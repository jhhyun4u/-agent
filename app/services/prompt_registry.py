"""
프롬프트 레지스트리 서비스 — 버전 관리 + A/B 라우팅.

기존 Python 상수를 래핑하되 대체하지 않음 (레지스트리 DB 장애 시 폴백).
프롬프트 ID: {파일명}.{상수명} (예: section_prompts.UNDERSTAND)
"""

import hashlib
import importlib
import inspect
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 프롬프트 소스 매핑: (모듈 경로, 상수명 리스트)
PROMPT_SOURCES: dict[str, list[str]] = {
    "app.prompts.section_prompts": [
        "EVALUATOR_PERSPECTIVE_BLOCK",
        "SECTION_PROMPT_UNDERSTAND",
        "SECTION_PROMPT_STRATEGY",
        "SECTION_PROMPT_METHODOLOGY",
        "SECTION_PROMPT_TECHNICAL",
        "SECTION_PROMPT_MANAGEMENT",
        "SECTION_PROMPT_PERSONNEL",
        "SECTION_PROMPT_TRACK_RECORD",
        "SECTION_PROMPT_SECURITY",
        "SECTION_PROMPT_MAINTENANCE",
        "SECTION_PROMPT_ADDED_VALUE",
        "SECTION_PROMPT_CASE_B",
    ],
    "app.prompts.strategy": [
        "STRATEGY_GENERATE_PROMPT",
        "COMPETITIVE_ANALYSIS_FRAMEWORK",
        "STRATEGY_RESEARCH_FRAMEWORK",
    ],
    "app.prompts.plan": [
        "PLAN_TEAM_PROMPT",
        "PLAN_ASSIGN_PROMPT",
        "PLAN_SCHEDULE_PROMPT",
        "PLAN_STORY_PROMPT",
        "PLAN_PRICE_PROMPT",
        "BUDGET_DETAIL_FRAMEWORK",
    ],
    "app.prompts.proposal_prompts": [
        "PROPOSAL_CASE_A_PROMPT",
        "PROPOSAL_CASE_B_PROMPT",
        "SELF_REVIEW_PROMPT",
        "PRESENTATION_STRATEGY_PROMPT",
        "PPT_SLIDE_PROMPT",
    ],
    "app.prompts.ppt_pipeline": [
        "PPT_TOC_SYSTEM",
        "PPT_TOC_USER",
        "PPT_VISUAL_BRIEF_SYSTEM",
        "PPT_VISUAL_BRIEF_USER",
        "PPT_STORYBOARD_SYSTEM",
        "PPT_STORYBOARD_USER",
    ],
    "app.prompts.trustworthiness": [
        "SOURCE_TAG_FORMAT",
    ],
}

# 공유 블록 → 포함하는 프롬프트 매핑 (변경 시 자동 버전업)
SHARED_BLOCKS = {
    "section_prompts.EVALUATOR_PERSPECTIVE_BLOCK": [
        "section_prompts.UNDERSTAND",
        "section_prompts.STRATEGY",
        "section_prompts.METHODOLOGY",
        "section_prompts.TECHNICAL",
        "section_prompts.MANAGEMENT",
        "section_prompts.PERSONNEL",
        "section_prompts.TRACK_RECORD",
        "section_prompts.SECURITY",
        "section_prompts.MAINTENANCE",
        "section_prompts.ADDED_VALUE",
        "section_prompts.CASE_B",
    ],
}


def _content_hash(text: str) -> str:
    """SHA-256 해시."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _module_to_file(module_path: str) -> str:
    """모듈 경로 → 파일 경로."""
    return module_path.replace(".", "/") + ".py"


def _make_prompt_id(module_path: str, const_name: str) -> str:
    """모듈.상수명 → prompt_id."""
    file_part = module_path.rsplit(".", 1)[-1]  # 'section_prompts'
    # 상수명에서 접두사 제거: SECTION_PROMPT_UNDERSTAND → UNDERSTAND
    short_name = const_name
    for prefix in ("SECTION_PROMPT_", "PLAN_", "PPT_", "STRATEGY_"):
        if const_name.startswith(prefix) and const_name != prefix.rstrip("_"):
            short_name = const_name[len(prefix):]
            break
    return f"{file_part}.{short_name}"


def _estimate_tokens(text: str) -> int:
    """간이 토큰 수 추정 (한글+영문 혼합: ~1.5 chars/token)."""
    return max(1, len(text) // 2)


async def sync_all_prompts() -> dict:
    """기동 시 모든 프롬프트 파일 스캔 → 해시 비교 → 변경분 자동 버전업.

    Returns: {"synced": int, "updated": int, "errors": list}
    """
    from app.utils.supabase_client import get_async_client

    stats = {"synced": 0, "updated": 0, "errors": []}

    try:
        client = await get_async_client()
    except Exception as e:
        logger.warning(f"프롬프트 레지스트리 DB 연결 실패 (무시): {e}")
        return stats

    for module_path, const_names in PROMPT_SOURCES.items():
        try:
            mod = importlib.import_module(module_path)
        except ImportError as e:
            stats["errors"].append(f"{module_path}: {e}")
            continue

        source_file = _module_to_file(module_path)

        for const_name in const_names:
            prompt_text = getattr(mod, const_name, None)
            if not prompt_text or not isinstance(prompt_text, str):
                continue

            prompt_id = _make_prompt_id(module_path, const_name)
            content_hash = _content_hash(prompt_text)

            try:
                # 현재 active 버전 조회
                existing = await (
                    client.table("prompt_registry")
                    .select("version, content_hash")
                    .eq("prompt_id", prompt_id)
                    .eq("status", "active")
                    .order("version", desc=True)
                    .limit(1)
                    .execute()
                )

                if existing.data:
                    row = existing.data[0]
                    if row["content_hash"] == content_hash:
                        stats["synced"] += 1
                        continue

                    # 해시 다름 → 새 버전
                    new_version = row["version"] + 1
                    # 기존 active → retired
                    await (
                        client.table("prompt_registry")
                        .update({"status": "retired"})
                        .eq("prompt_id", prompt_id)
                        .eq("status", "active")
                        .execute()
                    )
                else:
                    new_version = 1

                # 새 버전 등록
                await client.table("prompt_registry").insert({
                    "prompt_id": prompt_id,
                    "version": new_version,
                    "source_file": source_file,
                    "content_hash": content_hash,
                    "content_text": prompt_text,
                    "metadata": {
                        "const_name": const_name,
                        "token_estimate": _estimate_tokens(prompt_text),
                        "variables": _extract_variables(prompt_text),
                    },
                    "status": "active",
                    "parent_version": new_version - 1 if new_version > 1 else None,
                    "change_reason": "코드 동기화" if new_version > 1 else "초기 등록",
                    "created_by": "system",
                }).execute()

                stats["updated" if new_version > 1 else "synced"] += 1

            except Exception as e:
                stats["errors"].append(f"{prompt_id}: {e}")

    logger.info(
        f"프롬프트 레지스트리 동기화 완료: "
        f"synced={stats['synced']}, updated={stats['updated']}, errors={len(stats['errors'])}"
    )
    return stats


def _extract_variables(text: str) -> list[str]:
    """프롬프트 텍스트에서 {변수명} 패턴 추출 ({{이스케이프}} 제외)."""
    import re
    # {{ }} 를 먼저 제거한 뒤 {var} 패턴 추출
    cleaned = re.sub(r"\{\{.*?\}\}", "", text)
    return sorted(set(re.findall(r"\{(\w+)\}", cleaned)))


async def get_active_prompt(prompt_id: str) -> tuple[str, int, str]:
    """활성 프롬프트 반환 → (text, version, hash). DB 실패 시 Python 상수 폴백."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()

        result = await (
            client.table("prompt_registry")
            .select("content_text, version, content_hash")
            .eq("prompt_id", prompt_id)
            .eq("status", "active")
            .order("version", desc=True)
            .limit(1)
            .execute()
        )

        if result.data:
            row = result.data[0]
            return row["content_text"], row["version"], row["content_hash"]
    except Exception as e:
        logger.debug(f"프롬프트 레지스트리 조회 실패, 폴백: {e}")

    # 폴백: Python 상수에서 직접 가져오기
    return _fallback_from_python(prompt_id)


async def get_prompt_for_experiment(
    prompt_id: str, proposal_id: str
) -> tuple[str, int, str]:
    """A/B 실험 라우팅 포함 프롬프트 반환.

    진행 중 실험이 있으면 hash(proposal_id + experiment_id) % 100으로 라우팅.
    """
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()

        # 진행 중 실험 조회
        experiments = await (
            client.table("prompt_ab_experiments")
            .select("id, baseline_version, candidate_version, traffic_pct")
            .eq("prompt_id", prompt_id)
            .eq("status", "running")
            .limit(1)
            .execute()
        )

        if experiments.data:
            exp = experiments.data[0]
            # 결정론적 라우팅
            route_hash = int(
                hashlib.md5(f"{proposal_id}{exp['id']}".encode()).hexdigest(), 16
            )
            use_candidate = (route_hash % 100) < exp["traffic_pct"]
            target_version = exp["candidate_version"] if use_candidate else exp["baseline_version"]

            result = await (
                client.table("prompt_registry")
                .select("content_text, version, content_hash")
                .eq("prompt_id", prompt_id)
                .eq("version", target_version)
                .limit(1)
                .execute()
            )

            if result.data:
                row = result.data[0]
                return row["content_text"], row["version"], row["content_hash"]
    except Exception as e:
        logger.debug(f"A/B 라우팅 실패, 기본 프롬프트 사용: {e}")

    return await get_active_prompt(prompt_id)


async def register_candidate(
    prompt_id: str,
    text: str,
    reason: str,
    created_by: str = "evolution_engine",
) -> Optional[int]:
    """후보 프롬프트 등록. 반환: 새 버전 번호."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()

        # 최신 버전 조회
        latest = await (
            client.table("prompt_registry")
            .select("version, source_file")
            .eq("prompt_id", prompt_id)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )

        if not latest.data:
            logger.warning(f"프롬프트 '{prompt_id}' 미등록")
            return None

        new_version = latest.data[0]["version"] + 1
        source_file = latest.data[0]["source_file"]

        await client.table("prompt_registry").insert({
            "prompt_id": prompt_id,
            "version": new_version,
            "source_file": source_file,
            "content_hash": _content_hash(text),
            "content_text": text,
            "metadata": {
                "token_estimate": _estimate_tokens(text),
                "variables": _extract_variables(text),
            },
            "status": "candidate",
            "parent_version": new_version - 1,
            "change_reason": reason,
            "created_by": created_by,
        }).execute()

        return new_version
    except Exception as e:
        logger.error(f"후보 등록 실패: {e}")
        return None


def _fallback_from_python(prompt_id: str) -> tuple[str, int, str]:
    """prompt_id → Python 상수에서 직접 조회 (DB 폴백)."""
    parts = prompt_id.split(".", 1)
    if len(parts) != 2:
        return "", 0, ""

    file_part, short_name = parts

    # prompt_id → (모듈, 상수명) 역매핑
    for module_path, const_names in PROMPT_SOURCES.items():
        if module_path.endswith(f".{file_part}"):
            for const_name in const_names:
                candidate_id = _make_prompt_id(module_path, const_name)
                if candidate_id == prompt_id:
                    try:
                        mod = importlib.import_module(module_path)
                        text = getattr(mod, const_name, "")
                        if text:
                            return text, 0, _content_hash(text)
                    except Exception:
                        pass

    return "", 0, ""
