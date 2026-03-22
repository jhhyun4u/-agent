"""
제출서류 관리 서비스 (Stream 3)

- AI 1회 호출로 RFP에서 제출서류 목록 추출
- org_document_templates 자동 병합
- CRUD + 파일 업로드 + 검증
- 유효기간 만료 경고
"""

import io
import json
import logging
import zipfile
from datetime import date, datetime, timezone

from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


# ── AI 추출 ──

async def extract_checklist_from_rfp(
    proposal_id: str,
    rfp_text: str,
    rfp_analysis: dict | None = None,
) -> list[dict]:
    """RFP에서 제출서류 목록 추출 + org_document_templates 자동 병합."""
    from app.services.claude_client import call_claude_json
    from app.prompts.submission_docs import EXTRACT_SUBMISSION_DOCS_PROMPT

    # AI 호출
    prompt = EXTRACT_SUBMISSION_DOCS_PROMPT.format(
        rfp_text=rfp_text[:15000],  # 토큰 절약
        rfp_analysis=json.dumps(rfp_analysis or {}, ensure_ascii=False, default=str)[:5000],
    )

    try:
        extracted = await call_claude_json(prompt, max_tokens=4000)
    except Exception as e:
        logger.error(f"제출서류 AI 추출 실패: {e}")
        extracted = []

    if not isinstance(extracted, list):
        extracted = []

    client = await get_async_client()

    # 기존 항목 삭제 (재추출 시)
    await (
        client.table("submission_documents")
        .delete()
        .eq("proposal_id", proposal_id)
        .eq("source", "rfp_extracted")
        .execute()
    )

    # org_id 조회
    prop = await (
        client.table("proposals")
        .select("org_id")
        .eq("id", proposal_id)
        .single()
        .execute()
    )
    org_id = prop.data.get("org_id") if prop.data else None

    # org_document_templates 조회
    templates = {}
    if org_id:
        tmpl_res = await (
            client.table("org_document_templates")
            .select("*")
            .eq("org_id", org_id)
            .eq("auto_include", True)
            .execute()
        )
        templates = {t["doc_type"]: t for t in (tmpl_res.data or [])}

    # 추출 결과 저장 + 템플릿 병합
    inserted = []
    matched_template_types = set()

    for i, doc in enumerate(extracted):
        doc_type = doc.get("doc_type", "")
        if not doc_type:
            continue

        row = {
            "proposal_id": proposal_id,
            "doc_type": doc_type,
            "doc_category": doc.get("doc_category", "other"),
            "required_format": doc.get("required_format", "자유"),
            "required_copies": doc.get("required_copies", 1),
            "source": "rfp_extracted",
            "status": "pending",
            "priority": doc.get("priority", "medium"),
            "notes": doc.get("notes"),
            "rfp_reference": doc.get("rfp_reference"),
            "sort_order": i,
        }

        # 템플릿 매칭: 이름이 유사하면 자동 연결
        tmpl = templates.get(doc_type)
        if tmpl:
            matched_template_types.add(doc_type)
            is_expired = _is_template_expired(tmpl)
            if is_expired:
                row["status"] = "expired"
                row["notes"] = (row.get("notes") or "") + " [유효기간 만료]"
            elif tmpl.get("file_path"):
                row["status"] = "uploaded"
                row["file_path"] = tmpl["file_path"]
                row["file_name"] = tmpl.get("file_name")
                row["file_size"] = tmpl.get("file_size")
                row["source"] = "template_matched"

        res = await client.table("submission_documents").insert(row).execute()
        if res.data:
            inserted.append(res.data[0])

    # 템플릿에는 있지만 RFP에 없는 서류 추가 (auto_include)
    for doc_type, tmpl in templates.items():
        if doc_type not in matched_template_types:
            is_expired = _is_template_expired(tmpl)
            row = {
                "proposal_id": proposal_id,
                "doc_type": doc_type,
                "doc_category": tmpl.get("doc_category", "qualification"),
                "required_format": tmpl.get("required_format", "사본"),
                "required_copies": 1,
                "source": "template_matched",
                "status": "expired" if is_expired else ("uploaded" if tmpl.get("file_path") else "pending"),
                "priority": "low",
                "notes": "[공통서류 자동포함]" + (" [유효기간 만료]" if is_expired else ""),
                "sort_order": len(inserted) + 100,
            }
            if tmpl.get("file_path") and not is_expired:
                row["file_path"] = tmpl["file_path"]
                row["file_name"] = tmpl.get("file_name")
                row["file_size"] = tmpl.get("file_size")

            res = await client.table("submission_documents").insert(row).execute()
            if res.data:
                inserted.append(res.data[0])

    # Stream 3 진행률 갱신
    from app.services.stream_orchestrator import update_stream_progress
    await update_stream_progress(
        proposal_id, "documents",
        status="in_progress",
        current_phase="checklist_extracted",
        progress_pct=20,
    )

    logger.info(f"제출서류 추출 완료: proposal={proposal_id}, {len(inserted)}건")
    return inserted


def _is_template_expired(tmpl: dict) -> bool:
    """템플릿 유효기간 만료 여부."""
    valid_until = tmpl.get("valid_until")
    if not valid_until:
        return False
    try:
        if isinstance(valid_until, str):
            exp_date = date.fromisoformat(valid_until)
        else:
            exp_date = valid_until
        return exp_date < date.today()
    except (ValueError, TypeError):
        return False


# ── CRUD ──

async def get_checklist(proposal_id: str) -> list[dict]:
    """제출서류 체크리스트 조회."""
    client = await get_async_client()
    res = await (
        client.table("submission_documents")
        .select("*")
        .eq("proposal_id", proposal_id)
        .order("sort_order")
        .execute()
    )
    return res.data or []


_ADD_DOC_ALLOWED_KEYS = frozenset({
    "doc_type", "doc_category", "required_format", "required_copies",
    "priority", "notes", "assignee_id", "deadline", "rfp_reference", "sort_order",
})


async def add_document(proposal_id: str, data: dict) -> dict:
    """수동 서류 추가 (허용 키 화이트리스트 적용)."""
    client = await get_async_client()
    safe_data = {k: v for k, v in data.items() if k in _ADD_DOC_ALLOWED_KEYS}
    row = {
        "proposal_id": proposal_id,
        "source": "manual",
        "status": "pending",
        **safe_data,
    }
    res = await client.table("submission_documents").insert(row).execute()
    return res.data[0] if res.data else {}


async def update_document_status(doc_id: str, data: dict, proposal_id: str | None = None) -> dict:
    """서류 상태/담당 변경 (proposal_id로 소유권 검증)."""
    client = await get_async_client()
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    q = client.table("submission_documents").update(data).eq("id", doc_id)
    if proposal_id:
        q = q.eq("proposal_id", proposal_id)
    res = await q.execute()
    result = res.data[0] if res.data else {}
    if result and "status" in data and proposal_id:
        await recalculate_documents_progress(proposal_id)
    return result


async def delete_document(doc_id: str, proposal_id: str | None = None) -> bool:
    """서류 삭제 (proposal_id로 소유권 검증)."""
    client = await get_async_client()
    q = client.table("submission_documents").delete().eq("id", doc_id)
    if proposal_id:
        q = q.eq("proposal_id", proposal_id)
    res = await q.execute()
    return bool(res.data)


async def assign_document(doc_id: str, assignee_id: str) -> dict:
    """담당자 배정."""
    return await update_document_status(doc_id, {
        "assignee_id": assignee_id,
        "status": "assigned",
    })


async def upload_document(doc_id: str, file_path: str, file_name: str, file_size: int, file_format: str, user_id: str, proposal_id: str | None = None) -> dict:
    """파일 업로드 기록 (proposal_id로 소유권 검증)."""
    client = await get_async_client()
    now = datetime.now(timezone.utc).isoformat()
    q = (
        client.table("submission_documents")
        .update({
            "file_path": file_path,
            "file_name": file_name,
            "file_size": file_size,
            "file_format": file_format,
            "uploaded_by": user_id,
            "uploaded_at": now,
            "status": "uploaded",
            "updated_at": now,
        })
        .eq("id", doc_id)
    )
    if proposal_id:
        q = q.eq("proposal_id", proposal_id)
    res = await q.execute()
    result = res.data[0] if res.data else {}
    if result and proposal_id:
        await recalculate_documents_progress(proposal_id)
    return result


async def verify_document(doc_id: str, user_id: str, proposal_id: str | None = None) -> dict:
    """검증 완료 (proposal_id로 소유권 검증)."""
    client = await get_async_client()
    now = datetime.now(timezone.utc).isoformat()
    q = (
        client.table("submission_documents")
        .update({
            "verified_by": user_id,
            "verified_at": now,
            "status": "verified",
            "updated_at": now,
        })
        .eq("id", doc_id)
    )
    if proposal_id:
        q = q.eq("proposal_id", proposal_id)
    res = await q.execute()
    result = res.data[0] if res.data else {}
    if result and proposal_id:
        await recalculate_documents_progress(proposal_id)
    return result


async def validate_document(doc_id: str) -> dict:
    """포맷/크기 검증."""
    client = await get_async_client()
    doc = await (
        client.table("submission_documents")
        .select("*")
        .eq("id", doc_id)
        .single()
        .execute()
    )
    if not doc.data:
        return {"valid": False, "errors": ["서류를 찾을 수 없습니다."]}

    d = doc.data
    errors = []
    if not d.get("file_path"):
        errors.append("파일이 업로드되지 않았습니다.")
    if d.get("required_format") and d.get("file_format"):
        fmt = d["required_format"]
        actual = (d["file_format"] or "").upper()
        if fmt != "자유" and fmt.upper() not in actual:
            errors.append(f"포맷 불일치: 요구={fmt}, 실제={actual}")

    return {"valid": len(errors) == 0, "errors": errors}


# ── 진행률 자동 계산 + 자동 완료 ──

async def recalculate_documents_progress(proposal_id: str) -> int:
    """서류 상태 기반 가중 진행률 계산 + 전체 verified 시 자동 완료."""
    from app.services.stream_orchestrator import update_stream_progress

    docs = await get_checklist(proposal_id)
    applicable = [d for d in docs if d["status"] != "not_applicable"]
    total = len(applicable)
    if total == 0:
        return 0

    verified = sum(1 for d in applicable if d["status"] == "verified")
    uploaded = sum(1 for d in applicable if d["status"] == "uploaded")
    assigned = sum(1 for d in applicable if d["status"] in ("assigned", "in_progress"))

    weighted = verified * 1.0 + uploaded * 0.7 + assigned * 0.3
    pct = int(min(weighted / total * 100, 100))

    is_complete = (verified == total and total > 0)
    phase = "all_verified" if is_complete else (
        "all_uploaded" if uploaded + verified == total else "in_progress"
    )

    await update_stream_progress(
        proposal_id, "documents",
        status="completed" if is_complete else "in_progress",
        progress_pct=pct,
        current_phase=phase,
    )
    return pct


# ── 원본 준비 확인 ──

async def confirm_original_document(
    doc_id: str, user_id: str, proposal_id: str | None = None,
) -> dict:
    """원본 서류 준비 완료 확인 (파일 업로드 없이 verified 처리)."""
    client = await get_async_client()

    # 서류 조회 + required_format 검증
    q = client.table("submission_documents").select("*").eq("id", doc_id)
    if proposal_id:
        q = q.eq("proposal_id", proposal_id)
    doc_res = await q.single().execute()
    if not doc_res.data:
        raise ValueError("서류를 찾을 수 없습니다.")

    doc = doc_res.data
    if doc.get("required_format") != "원본":
        raise ValueError("원본 서류만 이 방식으로 확인할 수 있습니다.")

    now = datetime.now(timezone.utc).isoformat()
    notes = (doc.get("notes") or "") + " [원본 준비 확인]"

    res = await (
        client.table("submission_documents")
        .update({
            "status": "verified",
            "verified_by": user_id,
            "verified_at": now,
            "notes": notes.strip(),
            "updated_at": now,
        })
        .eq("id", doc_id)
        .execute()
    )
    result = res.data[0] if res.data else {}

    if result and proposal_id:
        await recalculate_documents_progress(proposal_id)
    elif result and doc.get("proposal_id"):
        await recalculate_documents_progress(doc["proposal_id"])

    return result


# ── 사본 PDF 병합 다운로드 ──

async def build_copy_bundle(proposal_id: str) -> tuple[bytes, str]:
    """사본 서류 파일을 PDF 병합 (비PDF 혼재 시 ZIP fallback)."""
    docs = await get_checklist(proposal_id)
    copy_docs = [
        d for d in docs
        if d.get("file_path")
        and d.get("required_format") in ("사본", None)
        and d.get("source") == "template_matched"
    ]

    if not copy_docs:
        raise ValueError("다운로드할 사본 서류가 없습니다.")

    client = await get_async_client()
    files: list[tuple[str, bytes]] = []

    for doc in copy_docs:
        try:
            res = await client.storage.from_("proposal-files").download(doc["file_path"])
            fname = doc.get("file_name") or doc["file_path"].rsplit("/", 1)[-1]
            files.append((fname, res))
        except Exception as e:
            logger.warning(f"사본 파일 다운로드 실패: {doc['file_path']} — {e}")

    if not files:
        raise ValueError("다운로드 가능한 사본 파일이 없습니다.")

    # 모든 파일이 PDF면 병합, 아니면 ZIP
    all_pdf = all(fname.lower().endswith(".pdf") for fname, _ in files)

    if all_pdf and len(files) >= 1:
        try:
            from PyPDF2 import PdfMerger
            merger = PdfMerger()
            for fname, data in files:
                merger.append(io.BytesIO(data))
            output = io.BytesIO()
            merger.write(output)
            merger.close()
            return output.getvalue(), "application/pdf"
        except Exception as e:
            logger.warning(f"PDF 병합 실패, ZIP fallback: {e}")

    # ZIP fallback
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, data in files:
            zf.writestr(fname, data)
    return buf.getvalue(), "application/zip"


# ── 산출물 자동 연결 ──

async def link_stream1_artifacts(proposal_id: str) -> int:
    """Stream 1 완료 시 제안서/PPT 산출물을 체크리스트에 자동 연결."""
    client = await get_async_client()

    # doc_category=proposal인 서류 조회
    docs_res = await (
        client.table("submission_documents")
        .select("*")
        .eq("proposal_id", proposal_id)
        .eq("doc_category", "proposal")
        .execute()
    )
    target_docs = docs_res.data or []
    if not target_docs:
        return 0

    # 최신 산출물 조회 (proposal, ppt)
    artifacts = {}
    for step in ("proposal", "ppt"):
        art_res = await (
            client.table("artifacts")
            .select("file_path, file_name, file_size, file_format")
            .eq("proposal_id", proposal_id)
            .eq("step", step)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        if art_res.data and art_res.data[0].get("file_path"):
            artifacts[step] = art_res.data[0]

    if not artifacts:
        return 0

    now = datetime.now(timezone.utc).isoformat()
    linked = 0

    for doc in target_docs:
        if doc.get("status") in ("verified", "uploaded"):
            continue  # 이미 처리됨

        doc_type_lower = (doc.get("doc_type") or "").lower()
        matched_art = None

        if any(kw in doc_type_lower for kw in ("기술제안서", "제안서", "proposal")):
            matched_art = artifacts.get("proposal")
        elif any(kw in doc_type_lower for kw in ("발표자료", "발표", "ppt", "프레젠테이션")):
            matched_art = artifacts.get("ppt")

        if matched_art:
            notes = (doc.get("notes") or "") + " [산출물 자동연결]"
            await (
                client.table("submission_documents")
                .update({
                    "file_path": matched_art["file_path"],
                    "file_name": matched_art.get("file_name"),
                    "file_size": matched_art.get("file_size"),
                    "file_format": matched_art.get("file_format"),
                    "status": "uploaded",
                    "notes": notes.strip(),
                    "updated_at": now,
                })
                .eq("id", doc["id"])
                .execute()
            )
            linked += 1

    if linked > 0:
        await recalculate_documents_progress(proposal_id)

    logger.info(f"산출물 자동 연결: proposal={proposal_id}, {linked}건")
    return linked


# ── 사전 제출 점검 ──

async def check_documents_ready(proposal_id: str) -> dict:
    """사전 제출 점검 — 유효기간 만료 경고 포함."""
    docs = await get_checklist(proposal_id)
    total = 0
    completed = 0
    issues = []

    for d in docs:
        if d["status"] == "not_applicable":
            continue
        total += 1
        if d["status"] == "verified":
            completed += 1
        else:
            issue = None
            if d["status"] == "expired":
                issue = "유효기간 만료"
            elif d["status"] == "pending" and not d.get("assignee_id"):
                issue = "담당자 미배정"
            elif d["status"] == "rejected":
                issue = f"반려: {d.get('rejection_reason', '')}"
            elif d["status"] in ("pending", "assigned", "in_progress"):
                issue = "미완료"
            elif d["status"] == "uploaded":
                issue = "검증 대기"

            issues.append({
                "doc_id": d["id"],
                "doc_type": d["doc_type"],
                "status": d["status"],
                "issue": issue,
            })

    return {
        "ready": completed == total and total > 0,
        "total": total,
        "completed": completed,
        "issues": issues,
    }


# ── 조직 공통 서류 CRUD ──

async def get_org_templates(org_id: str) -> list[dict]:
    """조직 공통 서류 목록."""
    client = await get_async_client()
    res = await (
        client.table("org_document_templates")
        .select("*")
        .eq("org_id", org_id)
        .order("doc_type")
        .execute()
    )
    return res.data or []


async def upsert_org_template(org_id: str, data: dict, user_id: str) -> dict:
    """조직 공통 서류 등록/갱신."""
    client = await get_async_client()
    row = {
        "org_id": org_id,
        "uploaded_by": user_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        **data,
    }
    res = await (
        client.table("org_document_templates")
        .upsert(row, on_conflict="org_id,doc_type")
        .execute()
    )
    return res.data[0] if res.data else {}


async def delete_org_template(template_id: str) -> bool:
    """조직 공통 서류 삭제."""
    client = await get_async_client()
    res = await (
        client.table("org_document_templates")
        .delete()
        .eq("id", template_id)
        .execute()
    )
    return bool(res.data)
