"""
Claude API 클라이언트 (§16 프롬프트 설계 원칙)

Anthropic API 래퍼:
- Prompt Caching 지원
- 토큰 사용량 추적
- 구조화 출력 (JSON 파싱)
- 재시도 로직 (지수 백오프)
"""

import json
import logging
from contextvars import ContextVar
from typing import Any

import anthropic
from anthropic.types import Message

from app.config import settings
from app.prompts.trustworthiness import TRUSTWORTHINESS_RULES

logger = logging.getLogger(__name__)

_client: anthropic.AsyncAnthropic | None = None

# ── ContextVar: 노드별 토큰 사용량 수집 ──
_current_call_usage: ContextVar[list[dict]] = ContextVar("_current_call_usage", default=[])


def reset_usage_context() -> list[dict]:
    """ContextVar를 새 리스트로 리셋. 데코레이터에서 노드 시작 시 호출."""
    fresh: list[dict] = []
    _current_call_usage.set(fresh)
    return fresh


def get_accumulated_usage() -> list[dict]:
    """현재 노드 실행 중 누적된 API 호출 기록 반환."""
    try:
        return _current_call_usage.get()
    except LookupError:
        return []

# 모든 Claude 호출에 적용되는 공통 시스템 프롬프트
# TRUSTWORTHINESS_RULES (§16-3-1)를 별도 모듈에서 임포트

COMMON_SYSTEM_RULES = f"""당신은 20년 경력의 한국 정부 용역 제안서 작성 전문가이자, 공공기관 제안 평가위원 출신입니다.
한국어로 작성하며, 공공기관 제안서 형식과 관행을 따릅니다.
구체적 근거(수치·사례·도표)를 반드시 포함하며, 추상적 미사여구는 사용하지 않습니다.

{TRUSTWORTHINESS_RULES}"""


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            max_retries=settings.max_retries,
        )
    return _client


async def claude_generate(
    prompt: str,
    system_prompt: str = "",
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.3,
    cache_system: bool = True,
    response_format: str = "json",
    step_name: str = "",
) -> dict[str, Any]:
    """Claude API 호출 — JSON 응답 파싱.

    Args:
        prompt: 사용자 메시지 (단계별 프롬프트)
        system_prompt: 시스템 프롬프트 (COMMON_CONTEXT + TRUSTWORTHINESS_RULES)
        model: 모델 override (기본: settings.claude_model)
        max_tokens: 최대 출력 토큰
        temperature: 생성 온도
        cache_system: 시스템 프롬프트 Prompt Caching 활성화
        response_format: "json" | "text"
        step_name: Pre-Flight Check용 노드 이름 (빈 문자열이면 검사 스킵)

    Returns:
        파싱된 JSON dict 또는 {"text": str}
    """
    # ── Pre-Flight Check ──
    from app.services.preflight_check import check_prompt
    preflight = check_prompt(prompt, step_name=step_name)
    if preflight.errors:
        logger.warning(
            "[PreFlight] step=%s ERRORS=%s (tokens=~%d, empty=%.0f%%)",
            step_name or "unknown", preflight.errors,
            preflight.estimated_tokens, preflight.empty_ratio * 100,
        )
    elif preflight.warnings:
        logger.info(
            "[PreFlight] step=%s warnings=%s (tokens=~%d)",
            step_name or "unknown", preflight.warnings, preflight.estimated_tokens,
        )

    client = _get_client()
    model = model or settings.claude_model
    max_tokens = max_tokens or settings.max_output_tokens

    # 시스템 프롬프트 구성 (Prompt Caching)
    # 공통 규칙 + 호출자 시스템 프롬프트 결합
    combined_system = COMMON_SYSTEM_RULES
    if system_prompt:
        combined_system = f"{COMMON_SYSTEM_RULES}\n\n{system_prompt}"

    system_content = []
    block = {"type": "text", "text": combined_system}  # type: ignore
    if cache_system and settings.enable_prompt_caching:
        block["cache_control"] = {"type": "ephemeral"}  # type: ignore
    system_content.append(block)

    # 메시지 구성
    messages = [{"role": "user", "content": prompt}]

    create_kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
        "system": system_content,
    }

    try:
        response = await client.messages.create(**create_kwargs)  # type: ignore

        # 토큰 사용량 로깅
        usage = response.usage
        if settings.log_token_usage:
            logger.info(
                f"Claude API: input={usage.input_tokens}, output={usage.output_tokens}, "
                f"cache_read={getattr(usage, 'cache_read_input_tokens', 0)}, "
                f"cache_create={getattr(usage, 'cache_creation_input_tokens', 0)}"
            )

        # ContextVar에 사용량 적재 (track_tokens 데코레이터에서 수집)
        try:
            _current_call_usage.get().append({
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0),
                "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0),
                "model": model,
            })
        except LookupError:
            pass

        # 응답 텍스트 추출
        text = response.content[0].text if response.content else ""

        # JSON 파싱
        if response_format == "json":
            return _parse_json_response(text)

        return {
            "text": text,
            "token_usage": {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cached_tokens": getattr(usage, "cache_read_input_tokens", 0),
            },
        }

    except anthropic.RateLimitError as e:
        logger.warning(f"Claude API Rate Limit: {e}")
        from app.exceptions import RateLimitError
        raise RateLimitError("Claude API 요청 한도 초과: 잠시 후 다시 시도하세요.")
    except anthropic.AuthenticationError as e:
        logger.error(f"Claude API 인증 오류: {e}")
        from app.exceptions import AIServiceError
        raise AIServiceError("Claude API 인증 오류: API 키를 확인하세요.")
    except anthropic.APIConnectionError as e:
        logger.error(f"Claude API 연결 실패: {e}")
        from app.exceptions import AIServiceError
        raise AIServiceError("Claude API 서버에 연결할 수 없습니다.")
    except anthropic.APITimeoutError as e:
        logger.error(f"Claude API 타임아웃: {e}")
        from app.exceptions import AITimeoutError
        raise AITimeoutError(step=step_name or "unknown")
    except anthropic.APIError as e:
        logger.error(f"Claude API 오류: {e}")
        from app.exceptions import AIServiceError
        raise AIServiceError(f"Claude API 오류: {e.message}")


async def claude_generate_streaming(
    prompt: str,
    system_prompt: str = "",
    model: str | None = None,
    max_tokens: int | None = None,
):
    """Claude API 스트리밍 호출 — SSE 이벤트 생성기."""
    client = _get_client()
    model = model or settings.claude_model
    max_tokens = max_tokens or settings.max_output_tokens

    combined_system = COMMON_SYSTEM_RULES
    if system_prompt:
        combined_system = f"{COMMON_SYSTEM_RULES}\n\n{system_prompt}"

    system_content = [{"type": "text", "text": combined_system}]

    stream_kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        "system": system_content,
    }

    try:
        async with client.messages.stream(**stream_kwargs) as stream:  # type: ignore
            async for text in stream.text_stream:
                yield text
    except anthropic.RateLimitError as e:
        logger.warning(f"Claude 스트리밍 Rate Limit: {e}")
        yield "\n[ERROR:RATE_LIMIT] Claude API 요청 한도 초과"
    except anthropic.APIConnectionError as e:
        logger.error(f"Claude 스트리밍 연결 실패: {e}")
        yield "\n[ERROR:CONNECTION] Claude API 서버 연결 실패"
    except anthropic.APITimeoutError as e:
        logger.error(f"Claude 스트리밍 타임아웃: {e}")
        yield "\n[ERROR:TIMEOUT] Claude API 응답 시간 초과"
    except anthropic.APIError as e:
        logger.error(f"Claude 스트리밍 API 오류: {e}")
        yield f"\n[ERROR:API] Claude API 오류: {e.message}"
    except Exception as e:
        logger.error(f"Claude 스트리밍 예외: {e}", exc_info=True)
        yield "\n[ERROR:UNKNOWN] 스트리밍 중 오류 발생"


def _parse_json_response(text: str) -> dict:
    """Claude 응답에서 JSON 추출 및 파싱.

    코드블록(```json ... ```) 또는 순수 JSON 모두 지원.
    """
    # 코드블록 제거
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # 첫 줄(```json)과 마지막 줄(```) 제거
        start = 1
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        cleaned = "\n".join(lines[start:end])

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # JSON 파싱 실패 시 텍스트 응답 반환
        logger.warning(f"JSON 파싱 실패, 텍스트 응답 반환: {cleaned[:200]}...")
        return {"text": text, "_parse_error": True}


class ClaudeClient:
    """Anthropic Claude API 래퍼 클래스 (master_projects_chat_service 호환)."""

    def __init__(self):
        self._client = _get_client()

    async def create_message(
        self,
        system: str,
        messages: list[dict],
        model: str = "claude-opus-4-6",
        max_tokens: int = 1500,
        **kwargs
    ) -> "Message":
        """Anthropic API를 호출하여 메시지 생성.

        Returns:
            Message 객체 (content[0].text 형식)
        """
        response = await self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            **kwargs
        )
        return response
