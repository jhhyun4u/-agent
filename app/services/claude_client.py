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
from typing import Any

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

_client: anthropic.AsyncAnthropic | None = None

# 모든 Claude 호출에 적용되는 공통 시스템 프롬프트
COMMON_SYSTEM_RULES = """당신은 전문 용역 제안서 작성 전문가입니다. 한국어로 작성하며 공공기관 제안서 형식과 관행을 따릅니다.

[데이터 신뢰성 원칙]
- 수치 데이터는 반드시 확인하여, 근거가 있는 자료만 활용해야 합니다.
- 출처가 불분명하거나 검증되지 않은 수치는 사용하지 마세요.
- 통계·수치를 인용할 때는 출처(기관명, 연도, 보고서명 등)를 명시하세요.
- 추정치를 사용할 경우 '추정', '약' 등을 표기하고 산출 근거를 밝히세요.

[용어 정합성 원칙]
- RFP에서 사용하는 핵심 용어·표현을 그대로 사용하세요. 동의어로 바꾸지 마세요.
- 발주기관의 비전·미션 문서에 나오는 키워드를 자연스럽게 활용하세요."""


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

    Returns:
        파싱된 JSON dict 또는 {"text": str}
    """
    client = _get_client()
    model = model or settings.claude_model
    max_tokens = max_tokens or settings.max_output_tokens

    # 시스템 프롬프트 구성 (Prompt Caching)
    # 공통 규칙 + 호출자 시스템 프롬프트 결합
    combined_system = COMMON_SYSTEM_RULES
    if system_prompt:
        combined_system = f"{COMMON_SYSTEM_RULES}\n\n{system_prompt}"

    system_content = []
    block = {"type": "text", "text": combined_system}
    if cache_system and settings.enable_prompt_caching:
        block["cache_control"] = {"type": "ephemeral"}
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
        response = await client.messages.create(**create_kwargs)

        # 토큰 사용량 로깅
        usage = response.usage
        if settings.log_token_usage:
            logger.info(
                f"Claude API: input={usage.input_tokens}, output={usage.output_tokens}, "
                f"cache_read={getattr(usage, 'cache_read_input_tokens', 0)}, "
                f"cache_create={getattr(usage, 'cache_creation_input_tokens', 0)}"
            )

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

    async with client.messages.stream(**stream_kwargs) as stream:
        async for text in stream.text_stream:
            yield text


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
