"""
대시보드 캐싱 관리자 (설계: 섹션 6)

Redis 기반 캐싱:
- get/set/delete 연산
- JSON 직렬화/역직렬화
- 캐시 무효화 (패턴 매칭)
- 에러 처리 (Redis 다운 시 fallback)
- Decorator 지원 (@cached)
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional, Callable
from functools import wraps

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis 기반 캐시 관리자"""

    def __init__(self):
        """캐시 관리자 초기화 (싱글톤)"""
        self._client: Optional[redis.Redis] = None
        self._available: bool = True

    async def _get_client(self) -> Optional[redis.Redis]:
        """Redis 클라이언트 획득 (lazy initialization)"""
        if self._client is None and self._available:
            try:
                self._client = await redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                )
                # 연결 테스트
                await self._client.ping()
                logger.info("✅ Redis 클라이언트 연결 성공")
            except Exception as e:
                logger.warning(f"⚠️ Redis 연결 실패 (캐싱 비활성화): {e}")
                self._available = False
                self._client = None

        return self._client

    async def get(self, key: str) -> Optional[dict]:
        """
        캐시에서 값 조회 (JSON 역직렬화)

        Args:
            key: 캐시 키

        Returns:
            캐시 데이터 또는 None
        """
        try:
            client = await self._get_client()
            if not client:
                return None

            value = await client.get(key)
            if value:
                return json.loads(value)
            return None

        except Exception as e:
            logger.error(f"❌ 캐시 GET 오류 ({key}): {e}")
            return None

    async def set(
        self,
        key: str,
        value: dict,
        ttl: int = 300
    ) -> bool:
        """
        캐시에 값 저장 (JSON 직렬화)

        Args:
            key: 캐시 키
            value: 저장할 데이터 (dict)
            ttl: TTL (초), 기본값 5분

        Returns:
            저장 성공 여부
        """
        try:
            client = await self._get_client()
            if not client:
                return False

            serialized = json.dumps(value, ensure_ascii=False, default=str)
            await client.setex(key, ttl, serialized)
            logger.debug(f"📝 캐시 SET: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"❌ 캐시 SET 오류 ({key}): {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        캐시에서 키 삭제

        Args:
            key: 캐시 키

        Returns:
            삭제 성공 여부
        """
        try:
            client = await self._get_client()
            if not client:
                return False

            deleted = await client.delete(key)
            if deleted:
                logger.debug(f"🗑️  캐시 DELETE: {key}")
            return deleted > 0

        except Exception as e:
            logger.error(f"❌ 캐시 DELETE 오류 ({key}): {e}")
            return False

    async def flush_pattern(self, pattern: str) -> int:
        """
        패턴에 일치하는 모든 캐시 키 삭제

        Args:
            pattern: 캐시 키 패턴 (e.g., "dashboard:metrics:team:*")

        Returns:
            삭제된 키 개수
        """
        try:
            client = await self._get_client()
            if not client:
                return 0

            # SCAN을 사용하여 패턴에 일치하는 키 찾기
            keys = await client.keys(pattern)
            if not keys:
                return 0

            # 배치로 삭제 (파이프라인 사용)
            async with client.pipeline() as pipe:
                for key in keys:
                    pipe.delete(key)
                results = await pipe.execute()

            deleted_count = sum(1 for r in results if r)
            logger.info(f"🗑️  캐시 패턴 DELETE: {pattern} ({deleted_count}개)")
            return deleted_count

        except Exception as e:
            logger.error(f"❌ 캐시 패턴 DELETE 오류 ({pattern}): {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        캐시 키 존재 여부 확인

        Args:
            key: 캐시 키

        Returns:
            존재 여부
        """
        try:
            client = await self._get_client()
            if not client:
                return False

            return await client.exists(key) > 0

        except Exception as e:
            logger.error(f"❌ 캐시 EXISTS 오류 ({key}): {e}")
            return False

    async def ttl(self, key: str) -> int:
        """
        캐시 키의 남은 TTL 조회

        Args:
            key: 캐시 키

        Returns:
            남은 TTL (초), 키 없음 시 -2, TTL 없음 시 -1
        """
        try:
            client = await self._get_client()
            if not client:
                return -2

            ttl_value = await client.ttl(key)
            return ttl_value

        except Exception as e:
            logger.error(f"❌ 캐시 TTL 오류 ({key}): {e}")
            return -2


# 싱글톤 인스턴스
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """캐시 관리자 싱글톤 획득"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(ttl: int = 300) -> Callable:
    """
    캐싱 데코레이터

    Args:
        ttl: 캐시 TTL (초)

    사용 예시:
        @cached(ttl=300)
        async def get_team_metrics(team_id: str) -> dict:
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 캐시 키 생성
            cache_key_parts = [func.__name__]
            if args:
                cache_key_parts.extend(str(arg) for arg in args)
            if kwargs:
                cache_key_parts.extend(f"{k}:{v}" for k, v in kwargs.items())
            cache_key = ":".join(cache_key_parts)

            # 캐시 조회
            cache_mgr = get_cache_manager()
            cached_value = await cache_mgr.get(cache_key)
            if cached_value is not None:
                logger.debug(f"💾 캐시 HIT: {cache_key}")
                return cached_value

            # 캐시 미스 → 함수 실행
            result = await func(*args, **kwargs)

            # 캐시 저장
            await cache_mgr.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# ════════════════════════════════════════════════════════════════════
# 캐시 무효화 헬퍼
# ════════════════════════════════════════════════════════════════════

async def invalidate_dashboard_caches(
    dashboard_type: Optional[str] = None,
    user_id: Optional[str] = None,
    team_id: Optional[str] = None,
    division_id: Optional[str] = None,
) -> int:
    """
    대시보드 캐시 무효화

    Args:
        dashboard_type: 대시보드 유형 (individual/team/department/executive)
        user_id: 사용자 ID
        team_id: 팀 ID
        division_id: 본부 ID

    Returns:
        무효화된 캐시 개수
    """
    cache_mgr = get_cache_manager()
    total_deleted = 0

    if dashboard_type == "individual" and user_id:
        pattern = f"dashboard:metrics:individual:{user_id}:*"
        total_deleted += await cache_mgr.flush_pattern(pattern)

    elif dashboard_type == "team" and team_id:
        pattern = f"dashboard:metrics:team:{team_id}:*"
        total_deleted += await cache_mgr.flush_pattern(pattern)
        pattern = f"dashboard:timeline:team:{team_id}:*"
        total_deleted += await cache_mgr.flush_pattern(pattern)

    elif dashboard_type == "department" and division_id:
        pattern = f"dashboard:metrics:department:{division_id}:*"
        total_deleted += await cache_mgr.flush_pattern(pattern)
        pattern = f"dashboard:timeline:department:{division_id}:*"
        total_deleted += await cache_mgr.flush_pattern(pattern)

    elif dashboard_type == "executive":
        pattern = "dashboard:metrics:executive:*"
        total_deleted += await cache_mgr.flush_pattern(pattern)
        pattern = "dashboard:timeline:executive:*"
        total_deleted += await cache_mgr.flush_pattern(pattern)

    else:
        # 모든 대시보드 캐시 무효화
        patterns = [
            "dashboard:metrics:*",
            "dashboard:timeline:*",
            "dashboard:details:*",
        ]
        for pattern in patterns:
            total_deleted += await cache_mgr.flush_pattern(pattern)

    return total_deleted
