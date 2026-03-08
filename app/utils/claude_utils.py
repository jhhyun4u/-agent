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
    Claude 응답에서 JSON 추출 (다단계 폴백)

    1) ```json ... ``` 코드 블록
    2) ``` ... ``` 코드 블록
    3) 첫 { 부터 마지막 } 까지 추출
    4) 잘린 JSON 복구 시도 (불완전한 값 제거)
    """
    original = response_text

    # 1. ```json 블록
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    # 2. ``` 블록
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()
    else:
        # 3. 첫 { ~ 마지막 } 추출
        start = response_text.find("{")
        end = response_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            response_text = response_text[start:end + 1]

    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        # 4. 잘린 JSON 복구: 마지막 완전한 키-값 이후를 닫음
        logger.warning(f"JSON 1차 파싱 실패, 복구 시도: {e}")
        recovered = _repair_truncated_json(response_text)
        if recovered is not None:
            return recovered
        logger.error(f"JSON 파싱 최종 실패: {e}")
        raise ClaudeAPIError(
            "Claude 응답을 JSON으로 파싱할 수 없습니다.",
            details={"response_text": original[:300], "error": str(e)}
        )


def _repair_truncated_json(text: str) -> Dict[str, Any] | None:
    """잘린 JSON을 마지막 완전한 키-값 쌍까지 잘라 복구"""
    # 마지막 완전한 값(문자열/숫자/배열 등) 이후의 쉼표 또는 공백에서 자름
    for cutoff in [",\n", ", \n", ",\r\n"]:
        idx = text.rfind(cutoff)
        if idx != -1:
            candidate = text[:idx] + "\n}"
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    # 마지막 } 없이 } 추가
    for suffix in ["}", "}}"]:
        try:
            return json.loads(text.rstrip().rstrip(",") + suffix)
        except json.JSONDecodeError:
            continue
    return None


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
