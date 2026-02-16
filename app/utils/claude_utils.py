"""Claude API 관련 유틸리티"""

import json
import logging
from typing import Any, Dict

import anthropic

from app.config import settings
from app.exceptions import ClaudeAPIError

logger = logging.getLogger(__name__)


def extract_json_from_response(response_text: str) -> Dict[str, Any]:
    """
    Claude 응답에서 JSON 추출

    Args:
        response_text: Claude 응답 텍스트

    Returns:
        파싱된 JSON 딕셔너리

    Raises:
        ClaudeAPIError: JSON 파싱 실패 시
    """
    try:
        # JSON 코드 블록 추출
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        return json.loads(response_text.strip())
    except (json.JSONDecodeError, IndexError) as e:
        logger.error(f"JSON 파싱 실패: {e}")
        raise ClaudeAPIError(
            "Claude 응답을 JSON으로 파싱할 수 없습니다.",
            details={"response_text": response_text[:200], "error": str(e)}
        )


def create_anthropic_client(async_client: bool = False) -> anthropic.Anthropic:
    """
    Anthropic 클라이언트 생성

    Args:
        async_client: True면 비동기 클라이언트 생성

    Returns:
        Anthropic 클라이언트 인스턴스

    Raises:
        ClaudeAPIError: API 키가 설정되지 않은 경우
    """
    if not settings.anthropic_api_key:
        raise ClaudeAPIError("Anthropic API 키가 설정되지 않았습니다.")

    if async_client:
        return anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)
