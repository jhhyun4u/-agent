"""
G2B 공고 첨부파일 다운로드 + Supabase Storage 보관 + 텍스트 추출.

Storage 전략:
- Supabase Storage: bid-attachments/{bid_no}/{파일명} (영구 보관)
- 로컬: data/bid_attachments/{bid_no}/{파일명} (텍스트 추출용 임시 캐시)
- 텍스트: 추출 후 합산 반환 → content_text로 DB 저장 (호출자 책임)
"""

import logging
from pathlib import Path

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)

ATTACHMENT_DIR = Path("data/bid_attachments")
BUCKET = "bid-attachments"
SUPPORTED_EXTS = {"pdf", "hwp", "hwpx", "docx"}
MAX_FILES = 5
DOWNLOAD_TIMEOUT = settings.file_download_timeout_seconds

# 파일 분류 우선순위 (작을수록 먼저)
_TYPE_MAP = {
    "제안요청서": 0, "과업지시서": 1, "공고문": 2, "서식": 3, "기타": 4,
}


def classify_attachment(name: str) -> str:
    """첨부파일명에서 유형 분류."""
    lower = name.lower()
    if "제안요청" in lower or "rfp" in lower:
        return "제안요청서"
    if "과업지시" in lower or "과업내용" in lower:
        return "과업지시서"
    if "공고" in lower or "입찰" in lower:
        return "공고문"
    if "서식" in lower or "양식" in lower or "제출" in lower:
        return "서식"
    return "기타"


def _classify_priority(name: str) -> int:
    return _TYPE_MAP.get(classify_attachment(name), 4)


def parse_attachments_from_raw(raw_data: dict) -> list[dict]:
    """raw_data에서 첨부파일 목록 추출 (최대 10개)."""
    attachments = []
    for i in range(1, 11):
        url = raw_data.get(f"ntceSpecDocUrl{i}")
        name = raw_data.get(f"ntceSpecFileNm{i}", "")
        if url and name:
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            attachments.append({
                "url": url,
                "name": name,
                "ext": ext,
                "type": classify_attachment(name),
                "supported": ext in SUPPORTED_EXTS,
            })
    attachments.sort(key=lambda a: _classify_priority(a["name"]))
    return attachments


async def download_bid_attachments(bid_no: str, raw_data: dict) -> str:
    """
    공고 첨부파일 다운로드 → Supabase Storage 업로드 → 텍스트 추출.

    Returns:
        추출된 텍스트 (모든 파일 합산). 실패 시 빈 문자열.
    """
    all_attachments = parse_attachments_from_raw(raw_data)
    supported = [a for a in all_attachments if a["supported"]][:MAX_FILES]

    if not supported:
        return ""

    bid_dir = ATTACHMENT_DIR / bid_no
    bid_dir.mkdir(parents=True, exist_ok=True)

    extracted_parts: list[str] = []
    for att in supported:
        file_path = bid_dir / att["name"]

        # 로컬 캐시 확인 → 없으면 다운로드
        if not file_path.exists():
            try:
                await _download_file(att["url"], file_path)
                logger.info(f"[{bid_no}] 다운로드 완료: {att['name']}")
            except Exception as e:
                logger.warning(f"[{bid_no}] 다운로드 실패 {att['name']}: {e}")
                continue

        # Supabase Storage 업로드 (best-effort)
        await _upload_to_storage(bid_no, att["name"], file_path)

        # 텍스트 추출
        try:
            from app.services.rfp_parser import extract_text
            text = extract_text(file_path)
            if text and len(text.strip()) > 100:
                extracted_parts.append(text)
        except Exception as e:
            logger.warning(f"[{bid_no}] 텍스트 추출 실패 {att['name']}: {e}")

    combined = "\n\n---\n\n".join(extracted_parts)
    # PostgreSQL text 컬럼은 \u0000 (null byte) 저장 불가 → 제거
    return combined.replace("\x00", "")


async def _upload_to_storage(bid_no: str, filename: str, local_path: Path) -> str | None:
    """Supabase Storage에 업로드. 성공 시 storage_path 반환."""
    import re as _re
    import unicodedata as _ud
    # Supabase Storage는 한글 등 비ASCII 파일명을 거부 → ASCII 안전 경로 생성
    safe_name = _ud.normalize("NFC", filename)
    safe_name = _re.sub(r'[^\w.\-]', '_', safe_name)
    storage_path = f"{bid_no}/{safe_name}"
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()

        content_type_map = {
            ".pdf": "application/pdf",
            ".hwp": "application/x-hwp",
            ".hwpx": "application/hwp+zip",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        ext = local_path.suffix.lower()
        ct = content_type_map.get(ext, "application/octet-stream")

        await client.storage.from_(BUCKET).upload(
            path=storage_path,
            file=local_path.read_bytes(),
            file_options={"content-type": ct, "upsert": "true"},
        )
        logger.info(f"[{bid_no}] Storage 업로드: {storage_path}")
        return storage_path
    except Exception as e:
        logger.warning(f"[{bid_no}] Storage 업로드 실패 ({filename}): {e}")
        return None


async def get_attachment_download_url(bid_no: str, filename: str) -> str | None:
    """Supabase Storage 서명 URL (1시간)."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        signed = await client.storage.from_(BUCKET).create_signed_url(
            f"{bid_no}/{filename}", expires_in=settings.signed_url_expiry_seconds
        )
        return signed.get("signedURL") or signed.get("signedUrl") or signed.get("data", {}).get("signedUrl", "")
    except Exception as e:
        logger.warning(f"[{bid_no}] 서명 URL 실패 ({filename}): {e}")
        return None


async def copy_bid_attachments_to_proposal(bid_no: str, proposal_id: str, raw_data: dict) -> list[dict]:
    """공고 첨부파일을 proposal_files + project_archive에 복사 등록.

    Returns: 등록된 파일 레코드 목록.
    """
    from uuid import uuid4
    from app.utils.supabase_client import get_async_client

    all_attachments = parse_attachments_from_raw(raw_data)
    if not all_attachments:
        return []

    client = await get_async_client()
    registered = []

    for att in all_attachments:
        file_id = str(uuid4())
        # Storage 경로: proposal-files/{proposal_id}/rfp/{파일명}
        storage_path = f"{proposal_id}/rfp/{att['name']}"

        # bid-attachments에서 proposal-files로 복사 시도
        src_path = f"{bid_no}/{att['name']}"
        try:
            data = await client.storage.from_(BUCKET).download(src_path)
            await client.storage.from_(settings.storage_bucket_proposals).upload(
                path=storage_path,
                file=data,
                file_options={"content-type": "application/octet-stream", "upsert": "true"},
            )
        except Exception:
            # Storage에 없으면 원본 URL에서 직접 다운로드
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(att["url"], timeout=aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT)) as resp:
                        if resp.status == 200:
                            file_bytes = await resp.read()
                            await client.storage.from_(settings.storage_bucket_proposals).upload(
                                path=storage_path,
                                file=file_bytes,
                                file_options={"content-type": "application/octet-stream", "upsert": "true"},
                            )
                        else:
                            logger.warning(f"[{bid_no}→{proposal_id}] 첨부파일 다운로드 실패: {att['name']}")
                            continue
            except Exception as e:
                logger.warning(f"[{bid_no}→{proposal_id}] 첨부파일 복사 실패: {att['name']}: {e}")
                continue

        # proposal_files DB 등록
        try:
            await client.table("proposal_files").insert({
                "id": file_id,
                "proposal_id": proposal_id,
                "category": "rfp",
                "filename": att["name"],
                "storage_path": storage_path,
                "file_type": att["ext"],
                "description": att["type"],
            }).execute()
            registered.append({"file_id": file_id, "filename": att["name"], "type": att["type"]})
        except Exception as e:
            logger.warning(f"[{bid_no}→{proposal_id}] DB 등록 실패: {att['name']}: {e}")

    logger.info(f"[{bid_no}→{proposal_id}] 첨부파일 {len(registered)}건 proposal에 연결")
    return registered


async def _download_file(url: str, dest: Path):
    from app.services.rfp_parser import _validate_url
    _validate_url(url)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT)
        ) as resp:
            if resp.status != 200:
                raise ValueError(f"HTTP {resp.status}")
            content = await resp.read()
            dest.write_bytes(content)
