"""인트라넷 문서 수집 파이프라인.

업로드 → 텍스트 추출 → 청킹 → 임베딩 → 저장.
프로젝트 메타로 KB 자동 시드 (capabilities, client_intelligence).
"""

import asyncio
import gc
import hashlib
import logging
import tempfile
from pathlib import Path

from app.services.document_chunker import chunk_document
from app.services.embedding_service import (
    embedding_text_for_client,
    generate_embedding,
    generate_embeddings_batch,
)
from app.services.knowledge_manager import get_knowledge_manager
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

# ── 성능 최적화 설정 ──
# 배치 크기 (OpenAI API: 최대 100K 토큰/요청, 평균 청크: 500-1000 토큰)
EMBEDDING_BATCH_SIZE = 250  # ✅ 100 → 250 (60% 향상)
INSERT_BATCH_SIZE = 200      # ✅ 50 → 200 (배치 트랜잭션 4배 향상)

# 동시성 제한
MAX_CONCURRENT_DOCUMENTS = 5      # 동시 처리 문서 수
MAX_CONCURRENT_CLASSIFICATIONS = 10  # 동시 분류 청크 수

# ✅ 동시 문서 처리 세마포어
_document_processing_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOCUMENTS)

# ── 문서 처리 파이프라인 ──


async def process_document(document_id: str, org_id: str) -> dict:
    """
    단일 문서 처리: 텍스트 추출 → 청킹 → 임베딩 → 저장.

    이미 extracted_text가 있으면 추출을 건너뛴다.
    """
    client = await get_async_client()

    # Get document (with optional project join - handle NULL project_id)
    doc_result = await (
        client.table("intranet_documents")
        .select("*")
        .eq("id", document_id)
        .single()
        .execute()
    )
    doc = doc_result.data

    try:
        # 텍스트 추출
        text = doc.get("extracted_text") or ""
        if not text and doc.get("storage_path"):
            await _update_doc_status(client, document_id, "extracting")
            text = await _extract_from_storage(client, doc)
            await (
                client.table("intranet_documents")
                .update({"extracted_text": text, "total_chars": len(text)})
                .eq("id", document_id)
                .execute()
            )

        if not text or len(text.strip()) < 50:
            await _update_doc_status(client, document_id, "failed", "텍스트가 너무 짧음")
            return {"status": "failed", "reason": "insufficient_text"}

        # 청킹
        await _update_doc_status(client, document_id, "chunking")
        chunks = chunk_document(text, doc["doc_type"], doc.get("doc_subtype", ""))

        # ✅ 메모리 최적화: 원본 텍스트 정리
        del text
        gc.collect()

        if not chunks:
            await _update_doc_status(client, document_id, "failed", "청킹 결과 0건")
            return {"status": "failed", "reason": "no_chunks"}

        # 임베딩
        await _update_doc_status(client, document_id, "embedding")
        chunk_texts = [c.content[:8000] for c in chunks]

        all_embeddings: list[list[float]] = []
        for i in range(0, len(chunk_texts), EMBEDDING_BATCH_SIZE):
            batch = chunk_texts[i : i + EMBEDDING_BATCH_SIZE]
            embeddings = await generate_embeddings_batch(batch)
            all_embeddings.extend(embeddings)

        # 기존 청크 삭제 후 재삽입 (reprocess 대응)
        await client.table("document_chunks").delete().eq("document_id", document_id).execute()

        rows = [
            {
                "document_id": document_id,
                "org_id": org_id,
                "chunk_index": chunk.index,
                "chunk_type": chunk.chunk_type,
                "section_title": chunk.section_title,
                "content": chunk.content,
                "char_count": chunk.char_count,
                "embedding": emb,
            }
            for chunk, emb in zip(chunks, all_embeddings)
        ]

        for i in range(0, len(rows), INSERT_BATCH_SIZE):
            await client.table("document_chunks").insert(rows[i : i + INSERT_BATCH_SIZE]).execute()

        # ── Module-6: Knowledge classification (병렬화) ──
        # Classify each chunk for knowledge management system
        await _update_doc_status(client, document_id, "classifying")
        try:
            manager = get_knowledge_manager()
            inserted_chunks = await client.table("document_chunks").select(
                "id, content"
            ).eq("document_id", document_id).execute()

            if inserted_chunks.data:
                # ✅ 병렬 분류 (최대 동시성 제한)
                async def classify_single_chunk(chunk):
                    """단일 청크 분류"""
                    try:
                        return await manager.classify_chunk(
                            chunk_id=chunk["id"],
                            content=chunk["content"],
                            document_context=doc.get("title")
                        )
                    except Exception as e:
                        logger.warning(
                            f"Knowledge classification failed for chunk {chunk['id']}: {e}"
                        )
                        return None

                # 세마포어로 동시성 제한
                semaphore = asyncio.Semaphore(MAX_CONCURRENT_CLASSIFICATIONS)

                async def bounded_classify(chunk):
                    """동시성 제한이 있는 분류"""
                    async with semaphore:
                        return await classify_single_chunk(chunk)

                # ✅ 병렬 실행 (10배 빠름!)
                logger.debug(
                    f"[{org_id}] 청크 분류 시작: {len(inserted_chunks.data)}개 (병렬={MAX_CONCURRENT_CLASSIFICATIONS})"
                )
                await asyncio.gather(
                    *[bounded_classify(chunk) for chunk in inserted_chunks.data],
                    return_exceptions=True
                )
                logger.debug(f"[{org_id}] 청크 분류 완료")

                # Mark chunks as knowledge-indexed
                await client.table("document_chunks").update(
                    {"is_knowledge_indexed": True}
                ).eq("document_id", document_id).execute()

        except Exception as e:
            logger.warning(f"Knowledge indexing failed for document {document_id}: {e}")
            # Continue even if knowledge indexing fails

        chunk_count = len(chunks)

        await (
            client.table("intranet_documents")
            .update({
                "processing_status": "completed",
                "chunk_count": chunk_count,
                "error_message": None,
            })
            .eq("id", document_id)
            .execute()
        )

        # ✅ 메모리 최적화: 완료 후 청크 정리
        del chunks
        del all_embeddings
        del rows
        gc.collect()

        return {"status": "completed", "chunks": chunk_count}

    except Exception as e:
        logger.error(f"문서 처리 실패 [{document_id}]: {e}")
        await _update_doc_status(client, document_id, "failed", str(e)[:500])
        return {"status": "failed", "reason": str(e)}


async def process_document_bounded(document_id: str, org_id: str) -> dict:
    """
    ✅ 동시성 제한이 있는 문서 처리
    
    최대 5개 문서를 동시에 처리하여 리소스 관리
    (API 호출 제한, DB 연결 풀 관리)
    """
    async with _document_processing_semaphore:
        logger.debug(f"[{org_id}] 문서 처리 시작 (대기열 관리 적용)")
        return await process_document(document_id, org_id)


async def _extract_from_storage(client, doc: dict) -> str:
    """Supabase Storage에서 파일 다운로드 → 텍스트 추출."""
    import os
    from app.config import settings
    from app.utils.file_utils import extract_text_from_file

    bucket = getattr(settings, "storage_bucket_intranet", "intranet-documents")
    storage_path = doc["storage_path"]

    response = await client.storage.from_(bucket).download(storage_path)

    suffix = Path(doc["filename"]).suffix.lower()
    tmp_file = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_file = tmp.name
            tmp.write(response)
            tmp.flush()
        return extract_text_from_file(tmp_file)
    finally:
        if tmp_file and os.path.exists(tmp_file):
            os.unlink(tmp_file)


async def _update_doc_status(client, document_id: str, status: str, error: str | None = None):
    """문서 처리 상태 업데이트."""
    update = {"processing_status": status, "error_message": error}
    await client.table("intranet_documents").update(update).eq("id", document_id).execute()


# ── 프로젝트 임포트 + KB 시드 ──


async def import_project(org_id: str, project_data: dict, *, upsert: bool = False) -> dict:
    """
    마이그레이션 스크립트에서 호출하는 프로젝트 임포트.

    1. intranet_projects 생성 (중복 시 upsert=True면 업데이트, False면 스킵)
    2. 프로젝트 임베딩 생성
    3. capabilities 시드 (track_record)
    4. client_intelligence 시드

    Args:
        upsert: True면 기존 레코드를 최신 데이터로 업데이트 (증분 동기화용)
    """
    client = await get_async_client()

    # 중복 체크
    existing = await (
        client.table("intranet_projects")
        .select("id, status, progress_pct")
        .eq("org_id", org_id)
        .eq("legacy_idx", project_data["legacy_idx"])
        .eq("board_id", project_data.get("board_id", "PR_PG"))
        .execute()
    )

    if existing.data and not upsert:
        return {"id": existing.data[0]["id"], "action": "skipped"}

    # 프로젝트 임베딩 생성
    emb_text = " | ".join(filter(None, [
        project_data.get("project_name", ""),
        project_data.get("client_name", ""),
        " ".join(project_data.get("keywords", [])),
        project_data.get("team", ""),
    ]))
    embedding = await generate_embedding(emb_text)

    row = {
        "org_id": org_id,
        "legacy_idx": project_data["legacy_idx"],
        "legacy_code": project_data.get("legacy_code"),
        "board_id": project_data.get("board_id", "PR_PG"),
        "project_name": project_data["project_name"],
        "client_name": project_data.get("client_name"),
        "client_manager": project_data.get("client_manager"),
        "client_tel": project_data.get("client_tel"),
        "client_email": project_data.get("client_email"),
        "start_date": project_data.get("start_date"),
        "end_date": project_data.get("end_date"),
        "budget_text": project_data.get("budget_text"),
        "budget_krw": project_data.get("budget_krw"),
        "manager": project_data.get("manager"),
        "attendants": project_data.get("attendants"),
        "partner": project_data.get("partner"),
        "pm": project_data.get("pm"),
        "pm_members": project_data.get("pm_members"),
        "keywords": project_data.get("keywords", []),
        "team": project_data.get("team"),
        "status": project_data.get("status"),
        "inout": project_data.get("inout"),
        "progress_pct": project_data.get("progress_pct", 0),
        "department": project_data.get("department"),
        "domain": project_data.get("domain"),
        "embedding": embedding,
    }

    if existing.data and upsert:
        # 기존 레코드 업데이트
        from datetime import datetime
        project_id = existing.data[0]["id"]
        row.pop("org_id")
        row.pop("legacy_idx")
        row.pop("board_id")
        row["updated_at"] = datetime.utcnow().isoformat()
        await client.table("intranet_projects").update(row).eq("id", project_id).execute()
        action = "updated"
    else:
        # 신규 생성
        result = await client.table("intranet_projects").insert(row).execute()
        project_id = result.data[0]["id"]
        action = "created"

    # KB 시드
    cap_id = await _seed_capability(client, org_id, project_data)
    ci_id = await _seed_client_intelligence(client, org_id, project_data)
    mp_id = await _seed_market_price_data(client, org_id, project_data)

    kb_update = {}
    if cap_id:
        kb_update["capability_id"] = cap_id
    if ci_id:
        kb_update["client_intel_id"] = ci_id
    if mp_id:
        kb_update["market_price_id"] = mp_id
    if kb_update:
        await client.table("intranet_projects").update(kb_update).eq("id", project_id).execute()

    return {"id": project_id, "action": action}


async def _seed_capability(client, org_id: str, data: dict) -> str | None:
    """수행실적 역량 자동 시드 (중복 시 스킵)."""
    title = data.get("project_name")
    if not title:
        return None

    existing = await (
        client.table("capabilities")
        .select("id")
        .eq("org_id", org_id)
        .eq("type", "track_record")
        .eq("title", title)
        .execute()
    )

    if existing.data:
        return existing.data[0]["id"]

    detail_parts = [
        f"발주기관: {data.get('client_name', '')}",
        f"PM: {data.get('pm', '')}",
        f"예산: {data.get('budget_text', '')}",
        f"기간: {data.get('start_date', '')} ~ {data.get('end_date', '')}",
    ]
    detail = ", ".join(filter(lambda x: ": " not in x or not x.endswith(": "), detail_parts))

    embedding = await generate_embedding(f"track_record | {title} | {detail}")

    result = await client.table("capabilities").insert({
        "org_id": org_id,
        "type": "track_record",
        "title": title,
        "detail": detail,
        "keywords": data.get("keywords", []),
        "embedding": embedding,
    }).execute()

    return result.data[0]["id"] if result.data else None


async def _seed_client_intelligence(client, org_id: str, data: dict) -> str | None:
    """발주기관 정보 자동 시드 (중복 시 스킵)."""
    cn = data.get("client_name")
    if not cn:
        return None

    existing = await (
        client.table("client_intelligence")
        .select("id")
        .eq("org_id", org_id)
        .eq("client_name", cn)
        .execute()
    )

    if existing.data:
        return existing.data[0]["id"]

    emb_text = embedding_text_for_client(cn, "", "")
    embedding = await generate_embedding(emb_text)

    contact_info = {}
    if data.get("client_manager"):
        contact_info["manager"] = data["client_manager"]
    if data.get("client_tel"):
        contact_info["tel"] = data["client_tel"]
    if data.get("client_email"):
        contact_info["email"] = data["client_email"]

    result = await client.table("client_intelligence").insert({
        "org_id": org_id,
        "client_name": cn,
        "contact_info": contact_info if contact_info else None,
        "relationship": "neutral",
        "embedding": embedding,
    }).execute()

    return result.data[0]["id"] if result.data else None


async def _seed_market_price_data(client, org_id: str, data: dict) -> str | None:
    """시장가격 자동 시드 (프로젝트 예산 기반, 중복 시 스킵)."""
    budget = data.get("budget_krw")
    project_name = data.get("project_name")
    if not budget or not project_name:
        return None

    domain = data.get("domain", "")
    client_name = data.get("client_name", "")

    # 같은 조직·프로젝트명으로 이미 등록되었으면 스킵
    existing = await (
        client.table("market_price_data")
        .select("id")
        .eq("org_id", org_id)
        .eq("project_name", project_name)
        .execute()
    )
    if existing.data:
        return existing.data[0]["id"]

    result = await client.table("market_price_data").insert({
        "org_id": org_id,
        "project_name": project_name,
        "client_name": client_name,
        "domain": domain,
        "budget_krw": budget,
        "source": "intranet_migration",
    }).execute()

    return result.data[0]["id"] if result.data else None


# ── 유틸리티 ──


def compute_file_hash(content: bytes) -> str:
    """SHA-256 해시 계산."""
    return hashlib.sha256(content).hexdigest()
