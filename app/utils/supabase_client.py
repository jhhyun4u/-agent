"""
Supabase 클라이언트 유틸리티

Supabase 데이터베이스 연결 및 기본 작업을 담당합니다.
"""

from typing import Optional, Dict, List, Any
from supabase import create_client, Client
from app.config import settings


class SupabaseClient:
    """Supabase 클라이언트 래퍼"""

    _instance: Optional["SupabaseClient"] = None
    _client: Optional[Client] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None and settings.supabase_url and settings.supabase_key:
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )

    @property
    def client(self) -> Client:
        """Supabase 클라이언트 반환"""
        if self._client is None:
            raise RuntimeError("Supabase client not initialized. Check SUPABASE_URL and SUPABASE_KEY in .env")
        return self._client

    async def get_proposals(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """제안서 목록 조회

        Args:
            filters: 필터 조건 (예: {"year": 2023, "status": "수주"})

        Returns:
            제안서 목록
        """
        try:
            query = self.client.table("proposals").select("*")

            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            response = query.execute()
            return response.data
        except Exception as e:
            print(f"[Supabase] 제안서 조회 실패: {e}")
            return []

    async def search_proposals(self, query: str) -> List[Dict[str, Any]]:
        """제안서 검색

        Args:
            query: 검색 키워드

        Returns:
            검색된 제안서 목록
        """
        try:
            # Supabase의 텍스트 검색 기능 사용
            response = (
                self.client.table("proposals")
                .select("*")
                .or_(f"title.ilike.%{query}%,client.ilike.%{query}%")
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"[Supabase] 제안서 검색 실패: {e}")
            return []

    async def add_proposal(self, proposal: Dict[str, Any]) -> Optional[str]:
        """제안서 추가

        Args:
            proposal: 제안서 데이터

        Returns:
            생성된 제안서 ID
        """
        try:
            response = self.client.table("proposals").insert(proposal).execute()
            if response.data:
                return response.data[0].get("id")
            return None
        except Exception as e:
            print(f"[Supabase] 제안서 추가 실패: {e}")
            return None

    async def get_personnel(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """인력 목록 조회

        Args:
            filters: 필터 조건 (예: {"available": True, "role": "PM"})

        Returns:
            인력 목록
        """
        try:
            query = self.client.table("personnel").select("*")

            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            response = query.execute()
            return response.data
        except Exception as e:
            print(f"[Supabase] 인력 조회 실패: {e}")
            return []

    async def search_personnel_by_skill(self, skill: str) -> List[Dict[str, Any]]:
        """기술로 인력 검색

        Args:
            skill: 기술명

        Returns:
            검색된 인력 목록
        """
        try:
            # PostgreSQL의 배열 검색 기능 사용
            response = (
                self.client.table("personnel")
                .select("*")
                .contains("expertise", [skill])
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"[Supabase] 인력 검색 실패: {e}")
            return []

    async def get_references(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """참고 자료 목록 조회

        Args:
            filters: 필터 조건

        Returns:
            참고 자료 목록
        """
        try:
            query = self.client.table("references").select("*")

            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            response = query.execute()
            return response.data
        except Exception as e:
            print(f"[Supabase] 참고 자료 조회 실패: {e}")
            return []

    async def search_references(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """참고 자료 검색

        Args:
            query: 검색 키워드
            top_k: 반환할 최대 개수

        Returns:
            검색된 참고 자료 목록
        """
        try:
            response = (
                self.client.table("references")
                .select("*")
                .or_(f"title.ilike.%{query}%,content.ilike.%{query}%")
                .limit(top_k)
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"[Supabase] 참고 자료 검색 실패: {e}")
            return []

    async def save_document(self, doc_data: Dict[str, Any]) -> Optional[str]:
        """문서 메타데이터 저장

        Args:
            doc_data: 문서 메타데이터

        Returns:
            생성된 문서 ID
        """
        try:
            response = self.client.table("documents").insert(doc_data).execute()
            if response.data:
                return response.data[0].get("id")
            return None
        except Exception as e:
            print(f"[Supabase] 문서 저장 실패: {e}")
            return None

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """문서 조회

        Args:
            doc_id: 문서 ID

        Returns:
            문서 데이터
        """
        try:
            response = (
                self.client.table("documents")
                .select("*")
                .eq("id", doc_id)
                .execute()
            )
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"[Supabase] 문서 조회 실패: {e}")
            return None


# 싱글톤 인스턴스
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Supabase 클라이언트 싱글톤 반환"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
