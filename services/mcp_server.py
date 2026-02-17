"""
MCP (Model Context Protocol) 서버 통합

4가지 주요 서비스:
1. ProposalDB: 과거 제안서 저장소 (Supabase)
2. PersonnelDB: 인력 정보 관리 (Supabase)
3. RAGServer: 참고 자료 검색 (Supabase + Semantic)
4. DocumentStore: 생성된 문서 저장소 (Supabase Storage)
"""

import sys
import os
from pathlib import Path

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from abc import ABC, abstractmethod

try:
    from app.utils.supabase_client import get_supabase_client
    SUPABASE_AVAILABLE = True
except Exception as e:
    print(f"[Warning] Supabase 클라이언트 로드 실패: {e}")
    SUPABASE_AVAILABLE = False


# ═══════════════════════════════════════════
# 1. PROPOSAL DATABASE
# ═══════════════════════════════════════════

class ProposalDB:
    """과거 제안서 저장소 (Supabase 통합)"""

    def __init__(self, use_supabase: bool = True):
        self.use_supabase = use_supabase and SUPABASE_AVAILABLE
        self.supabase_client = get_supabase_client() if self.use_supabase else None

        # Supabase 클라이언트가 실제로 사용 가능한지 확인
        if self.supabase_client and not self.supabase_client.is_available():
            self.use_supabase = False
            self.supabase_client = None

        # 폴백용 메모리 데이터
        self.proposals = {
            "prop_001": {
                "id": "prop_001",
                "title": "클라우드 마이그레이션 프로젝트",
                "client": "삼성전자",
                "year": 2023,
                "pages": 150,
                "status": "수주",
                "key_messages": ["보안 강화", "비용 절감", "운영 효율화"],
                "sections": {
                    "1": {"title": "회사개요", "pages": 15},
                    "2": {"title": "솔루션개요", "pages": 25},
                    "3": {"title": "구현계획", "pages": 40},
                }
            },
            "prop_002": {
                "id": "prop_002",
                "title": "AI/ML 플랫폼 구축",
                "client": "현대모비스",
                "year": 2023,
                "pages": 120,
                "status": "수주",
                "key_messages": ["AI 자동화", "예측 분석", "실시간 처리"],
                "sections": {
                    "1": {"title": "회사개요", "pages": 12},
                    "2": {"title": "솔루션개요", "pages": 30},
                    "3": {"title": "구현계획", "pages": 35},
                }
            },
        }
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """키워드로 제안서 검색"""
        # Supabase 사용 시도
        if self.use_supabase and self.supabase_client:
            try:
                return await self.supabase_client.search_proposals(query)
            except Exception as e:
                print(f"[ProposalDB] Supabase 검색 실패, 메모리 폴백: {e}")

        # 메모리 폴백
        results = []
        for prop in self.proposals.values():
            if (query.lower() in prop["title"].lower() or
                query.lower() in prop["client"].lower() or
                any(query.lower() in msg.lower() for msg in prop.get("key_messages", []))):
                results.append(prop)
        return results
    
    def get_by_id(self, prop_id: str) -> Optional[Dict[str, Any]]:
        """ID로 제안서 조회"""
        return self.proposals.get(prop_id)
    
    def list_by_year(self, year: int) -> List[Dict[str, Any]]:
        """연도별 제안서 목록"""
        return [p for p in self.proposals.values() if p["year"] == year]
    
    async def add_proposal(self, proposal: Dict[str, Any]) -> str:
        """새 제안서 추가"""
        # Supabase 사용 시도
        if self.use_supabase and self.supabase_client:
            try:
                prop_id = await self.supabase_client.add_proposal(proposal)
                if prop_id:
                    return prop_id
            except Exception as e:
                print(f"[ProposalDB] Supabase 추가 실패, 메모리 폴백: {e}")

        # 메모리 폴백
        prop_id = f"prop_{len(self.proposals) + 1:03d}"
        proposal["id"] = prop_id
        self.proposals[prop_id] = proposal
        return prop_id


# ═══════════════════════════════════════════
# 2. PERSONNEL DATABASE
# ═══════════════════════════════════════════

class PersonnelDB:
    """인력 정보 관리 (Supabase 통합)"""

    def __init__(self, use_supabase: bool = True):
        self.use_supabase = use_supabase and SUPABASE_AVAILABLE
        self.supabase_client = get_supabase_client() if self.use_supabase else None

        # Supabase 클라이언트가 실제로 사용 가능한지 확인
        if self.supabase_client and not self.supabase_client.is_available():
            self.use_supabase = False
            self.supabase_client = None

        # 폴백용 메모리 데이터
        self.personnel = {
            "emp_001": {
                "id": "emp_001",
                "name": "김철수",
                "grade": "상무",
                "role": "PM",
                "expertise": ["Project Management", "Cloud Architecture"],
                "available": True,
                "projects": 2,
            },
            "emp_002": {
                "id": "emp_002",
                "name": "이영희",
                "grade": "이사",
                "role": "CTO",
                "expertise": ["AWS", "Azure", "Kubernetes"],
                "available": True,
                "projects": 1,
            },
            "emp_003": {
                "id": "emp_003",
                "name": "박민준",
                "grade": "차장",
                "role": "개발리더",
                "expertise": ["Python", "Java", "DevOps"],
                "available": False,
                "projects": 3,
            },
            "emp_004": {
                "id": "emp_004",
                "name": "최수진",
                "grade": "대리",
                "role": "QA",
                "expertise": ["Test Automation", "Performance Testing"],
                "available": True,
                "projects": 1,
            },
        }
    
    def search_by_role(self, role: str) -> List[Dict[str, Any]]:
        """역할로 인력 검색"""
        return [p for p in self.personnel.values() if p["role"] == role]
    
    async def search_by_expertise(self, skill: str) -> List[Dict[str, Any]]:
        """기술로 인력 검색"""
        # Supabase 사용 시도
        if self.use_supabase and self.supabase_client:
            try:
                return await self.supabase_client.search_personnel_by_skill(skill)
            except Exception as e:
                print(f"[PersonnelDB] Supabase 검색 실패, 메모리 폴백: {e}")

        # 메모리 폴백
        return [
            p for p in self.personnel.values()
            if any(skill.lower() in e.lower() for e in p.get("expertise", []))
        ]
    
    def get_available(self) -> List[Dict[str, Any]]:
        """이용 가능한 인력"""
        return [p for p in self.personnel.values() if p["available"]]
    
    def allocate(self, emp_id: str, project_id: str) -> bool:
        """인력 배정"""
        if emp_id in self.personnel:
            self.personnel[emp_id]["projects"] += 1
            self.personnel[emp_id]["available"] = self.personnel[emp_id]["projects"] < 3
            return True
        return False
    
    async def get_team_for_skills(self, required_skills: List[str], team_size: int = 5) -> List[Dict[str, Any]]:
        """필요 기술을 갖춘 팀 구성"""
        # Supabase 사용 시 모든 인력 가져오기
        if self.use_supabase and self.supabase_client:
            try:
                pool = await self.supabase_client.get_personnel({"available": True})
            except Exception as e:
                print(f"[PersonnelDB] Supabase 조회 실패, 메모리 폴백: {e}")
                pool = self.get_available()
        else:
            pool = self.get_available()

        # 기술별 매칭 점수로 정렬
        scored = []
        for person in pool:
            score = sum(1 for skill in required_skills
                       if any(skill.lower() in e.lower() for e in person.get("expertise", [])))
            if score > 0:
                scored.append((score, person))

        scored.sort(reverse=True)

        return [p for _, p in scored[:team_size]]


# ═══════════════════════════════════════════
# 3. RAG SERVER (Reference Retrieval)
# ═══════════════════════════════════════════

class RAGServer:
    """참고 자료 검색 (Supabase 통합)"""

    def __init__(self, use_supabase: bool = True):
        self.use_supabase = use_supabase and SUPABASE_AVAILABLE
        self.supabase_client = get_supabase_client() if self.use_supabase else None

        # Supabase 클라이언트가 실제로 사용 가능한지 확인
        if self.supabase_client and not self.supabase_client.is_available():
            self.use_supabase = False
            self.supabase_client = None

        # 폴백용 메모리 데이터
        self.references = {
            "ref_001": {
                "id": "ref_001",
                "title": "AWS 마이그레이션 Best Practices",
                "content": "클라우드 마이그레이션 시 보안 고려사항...",
                "topics": ["AWS", "Security", "Migration"],
            },
            "ref_002": {
                "id": "ref_002",
                "title": "Kubernetes 운영 가이드",
                "content": "컨테이너 오케스트레이션의 기본 개념...",
                "topics": ["Kubernetes", "DevOps", "Container"],
            },
            "ref_003": {
                "id": "ref_003",
                "title": "AI 시스템 아키텍처",
                "content": "머신러닝 시스템 설계의 핵심 원칙...",
                "topics": ["AI", "ML", "Architecture"],
            },
            "ref_004": {
                "id": "ref_004",
                "title": "해외 클라우드 규정",
                "content": "다국가 클라우드 서비스 준수사항...",
                "topics": ["Compliance", "Security", "Global"],
            },
        }
    
    async def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """쿼리 관련 참고 자료 검색"""
        # Supabase 사용 시도
        if self.use_supabase and self.supabase_client:
            try:
                return await self.supabase_client.search_references(query, top_k)
            except Exception as e:
                print(f"[RAGServer] Supabase 검색 실패, 메모리 폴백: {e}")

        # 메모리 폴백
        query_lower = query.lower()
        scored = []

        for ref in self.references.values():
            score = 0
            # 제목 매칭
            if query_lower in ref["title"].lower():
                score += 3
            # 컨텐츠 매칭
            if query_lower in ref["content"].lower():
                score += 1
            # 토픽 매칭
            for topic in ref["topics"]:
                if query_lower in topic.lower():
                    score += 2

            if score > 0:
                scored.append((score, ref))

        scored.sort(reverse=True)
        return [ref for _, ref in scored[:top_k]]
    
    def search_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """토픽별 자료 검색"""
        return [
            ref for ref in self.references.values()
            if any(topic.lower() == t.lower() for t in ref.get("topics", []))
        ]


# ═══════════════════════════════════════════
# 4. DOCUMENT STORE
# ═══════════════════════════════════════════

class DocumentStore:
    """생성된 문서 저장소 (Supabase Storage 통합)"""

    def __init__(self, base_path: Optional[Path] = None, use_supabase: bool = True):
        self.use_supabase = use_supabase and SUPABASE_AVAILABLE
        self.supabase_client = get_supabase_client() if self.use_supabase else None

        # Supabase 클라이언트가 실제로 사용 가능한지 확인
        if self.supabase_client and not self.supabase_client.is_available():
            self.use_supabase = False
            self.supabase_client = None

        self.base_path = base_path or Path("/tmp/proposal_documents")
        self.base_path.mkdir(parents=True, exist_ok=True)

        # 메모리 메타데이터 (Supabase 사용 시에도 로컬 캐시로 사용)
        self.documents = {}
    
    async def save(self, doc_id: str, filename: str, content: bytes, metadata: Dict[str, Any] = None) -> str:
        """문서 저장"""
        file_path = self.base_path / filename

        # 로컬 파일 시스템에 저장 (항상)
        file_path.write_bytes(content)

        # 메타데이터
        doc_meta = {
            "id": doc_id,
            "filename": filename,
            "path": str(file_path),
            "size": len(content),
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        # Supabase에 메타데이터 저장 시도
        if self.use_supabase and self.supabase_client:
            try:
                await self.supabase_client.save_document(doc_meta)
            except Exception as e:
                print(f"[DocumentStore] Supabase 저장 실패, 로컬만 유지: {e}")

        # 로컬 캐시에도 저장
        self.documents[doc_id] = doc_meta

        return str(file_path)
    
    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """문서 조회"""
        return self.documents.get(doc_id)
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """저장된 문서 목록"""
        return list(self.documents.values())
    
    def delete(self, doc_id: str) -> bool:
        """문서 삭제"""
        if doc_id in self.documents:
            doc = self.documents[doc_id]
            path = Path(doc["path"])
            if path.exists():
                path.unlink()
            del self.documents[doc_id]
            return True
        return False


# ═══════════════════════════════════════════
# MCP SERVER: 통합 인터페이스
# ═══════════════════════════════════════════

class MCPServer:
    """MCP 통합 서버 (Supabase 통합)

    모든 외부 서비스에 대한 단일 진입점
    """

    def __init__(self, use_supabase: bool = True):
        self.use_supabase = use_supabase and SUPABASE_AVAILABLE

        self.proposal_db = ProposalDB(use_supabase=self.use_supabase)
        self.personnel_db = PersonnelDB(use_supabase=self.use_supabase)
        self.rag_server = RAGServer(use_supabase=self.use_supabase)
        self.document_store = DocumentStore(use_supabase=self.use_supabase)

        print("[MCP Server] 초기화 완료")
        if self.use_supabase:
            print("  - 모드: Supabase 통합 (폴백: 메모리)")
        else:
            print("  - 모드: 메모리 전용")
        print("  - ProposalDB: 과거 제안서 2건 (메모리 폴백)")
        print("  - PersonnelDB: 인력 4명 (메모리 폴백)")
        print("  - RAGServer: 참고 자료 4건 (메모리 폴백)")
        print("  - DocumentStore: 준비 완료")
    
    # ─────── Proposal DB Methods ───────
    
    async def search_similar_proposals(self, query: str) -> List[Dict[str, Any]]:
        """유사 제안서 검색 (Phase 1에서 사용)"""
        return await self.proposal_db.search(query)
    
    # ─────── Personnel DB Methods ───────
    
    async def get_team_for_project(self, required_skills: List[str], team_size: int = 5) -> List[Dict[str, Any]]:
        """프로젝트용 팀 구성 (Phase 3에서 사용)"""
        return await self.personnel_db.get_team_for_skills(required_skills, team_size)
    
    async def search_personnel_by_skill(self, skill: str) -> List[Dict[str, Any]]:
        """기술별 인력 검색"""
        return await self.personnel_db.search_by_expertise(skill)
    
    # ─────── RAG Server Methods ───────
    
    async def search_references(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """참고 자료 검색 (Phase 3에서 RAG 사전 수집)"""
        return await self.rag_server.search(query, top_k)
    
    async def search_references_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """토픽별 참고 자료"""
        return self.rag_server.search_by_topic(topic)
    
    # ─────── Document Store Methods ───────
    
    async def save_document(self, doc_id: str, filename: str, content: bytes,
                           metadata: Dict[str, Any] = None) -> str:
        """최종 문서 저장 (Phase 5 후)"""
        return await self.document_store.save(doc_id, filename, content, metadata)
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """저장된 문서 조회"""
        return self.document_store.get(doc_id)
    
    async def list_all_documents(self) -> List[Dict[str, Any]]:
        """모든 저장된 문서 목록"""
        return self.document_store.list_documents()


# 글로벌 MCP 서버 인스턴스
_mcp_server = None

def get_mcp_server() -> MCPServer:
    """MCP 서버 싱글톤"""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
    return _mcp_server


if __name__ == "__main__":
    import asyncio
    
    async def test_mcp():
        mcp = get_mcp_server()
        
        print("\n" + "="*70)
        print("MCP Server Test")
        print("="*70)
        
        # 1. Proposal DB Test
        print("\n[1] ProposalDB Test")
        proposals = await mcp.search_similar_proposals("클라우드")
        print(f"    Found: {len(proposals)} proposals")
        for p in proposals:
            print(f"    - {p['title']} ({p['client']})")
        
        # 2. Personnel DB Test
        print("\n[2] PersonnelDB Test")
        team = await mcp.get_team_for_project(["AWS", "Python"], 3)
        print(f"    Team size: {len(team)}")
        for member in team:
            print(f"    - {member['name']} ({member['grade']}, {member['role']})")
        
        # 3. RAG Server Test
        print("\n[3] RAGServer Test")
        refs = await mcp.search_references("클라우드 보안")
        print(f"    Found: {len(refs)} references")
        for ref in refs:
            print(f"    - {ref['title']}")
        
        print("\n" + "="*70)
        print("MCP Server Ready for Integration")
        print("="*70)
    
    asyncio.run(test_mcp())
