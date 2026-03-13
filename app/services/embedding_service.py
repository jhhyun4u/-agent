"""
임베딩 서비스 (§20-1)

OpenAI text-embedding-3-small 기반 1536차원 벡터 생성.
KB 콘텐츠/발주기관/경쟁사/교훈의 시맨틱 검색에 사용.
"""

import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
MAX_INPUT_LENGTH = 8000

_openai_client = None


def _get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import AsyncOpenAI
        _openai_client = AsyncOpenAI(api_key=getattr(settings, "openai_api_key", None))
    return _openai_client


async def generate_embedding(text: str) -> list[float]:
    """텍스트 → 1536차원 임베딩 벡터."""
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIMENSIONS

    try:
        client = _get_openai()
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text[:MAX_INPUT_LENGTH],
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"임베딩 생성 실패: {e}")
        return [0.0] * EMBEDDING_DIMENSIONS


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """배치 임베딩 생성 (최대 100건)."""
    if not texts:
        return []

    try:
        client = _get_openai()
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[t[:MAX_INPUT_LENGTH] for t in texts[:100]],
        )
        return [d.embedding for d in response.data]
    except Exception as e:
        logger.error(f"배치 임베딩 생성 실패: {e}")
        return [[0.0] * EMBEDDING_DIMENSIONS for _ in texts[:100]]


def embedding_text_for_content(title: str, body: str, tags: list[str] | None = None) -> str:
    """콘텐츠 라이브러리용 임베딩 입력 텍스트 조합."""
    parts = [title, body[:4000]]
    if tags:
        parts.append(" ".join(tags))
    return " | ".join(parts)


def embedding_text_for_client(client_name: str, client_type: str = "", notes: str = "") -> str:
    """발주기관용 임베딩 입력 텍스트 조합."""
    return " | ".join(filter(None, [client_name, client_type, notes[:2000]]))


def embedding_text_for_competitor(company_name: str, primary_area: str = "", strengths: str = "") -> str:
    """경쟁사용 임베딩 입력 텍스트 조합."""
    return " | ".join(filter(None, [company_name, primary_area, strengths[:2000]]))


def embedding_text_for_lesson(
    strategy_summary: str = "",
    effective_points: str = "",
    weak_points: str = "",
    industry: str = "",
) -> str:
    """교훈용 임베딩 입력 텍스트 조합."""
    return " | ".join(filter(None, [strategy_summary, effective_points, weak_points, industry]))
