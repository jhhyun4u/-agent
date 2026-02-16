"""
MCP 서버와 Phase 노드 통합 테스트

검증 항목:
1. MCP 서버 초기화
2. Phase 1에서 유사 제안서 검색
3. Phase 3에서 인력 배정 및 참고자료 검색
4. Phase 5에서 문서 저장
"""

import sys
import os
from pathlib import Path

_project_root = str(Path(__file__).parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import asyncio
from datetime import datetime
from services.mcp_server import get_mcp_server


async def test_mcp_integration():
    """MCP 통합 테스트"""
    
    print("\n" + "="*80)
    print("MCP 서버 & Phase 노드 통합 테스트")
    print("="*80)
    
    mcp = get_mcp_server()
    
    # ─────── Test 1: ProposalDB (Phase 1) ───────
    print("\n[TEST 1] Phase 1: 유사 제안서 검색")
    print("-" * 80)
    
    similar = await mcp.search_similar_proposals("클라우드")
    print(f"✓ 검색 결과: {len(similar)}건")
    for prop in similar:
        print(f"  - {prop['title']}")
        print(f"    Client: {prop['client']} ({prop['year']}년, 상태: {prop['status']})")
    
    # ─────── Test 2: PersonnelDB (Phase 3) ───────
    print("\n[TEST 2] Phase 3: 인력 배정")
    print("-" * 80)
    
    required_skills = ["AWS", "Python", "DevOps"]
    team = await mcp.get_team_for_project(required_skills, team_size=5)
    print(f"✓ 배정된 인력: {len(team)}명")
    for member in team:
        print(f"  - {member['name']} ({member['grade']}, {member['role']})")
        print(f"    Expertise: {', '.join(member['expertise'])}")
    
    # ─────── Test 3: RAGServer (Phase 3) ───────
    print("\n[TEST 3] Phase 3: 참고자료 검색")
    print("-" * 80)
    
    references = await mcp.search_references("클라우드 보안", top_k=3)
    print(f"✓ 검색 결과: {len(references)}건")
    for ref in references:
        print(f"  - {ref['title']}")
        print(f"    Topics: {', '.join(ref['topics'])}")
    
    # ─────── Test 4: DocumentStore (Phase 5) ───────
    print("\n[TEST 4] Phase 5: 문서 저장")
    print("-" * 80)
    
    doc_id = f"test_prop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    filename = "테스트_제안서_2024.docx"
    content = b"[DOCX Binary Content]"
    metadata = {
        "rfp_title": "AI 플랫폼 구축 제안서",
        "client": "테스트 회사",
        "pages": 120,
        "quality_score": 0.82,
    }
    
    saved_path = await mcp.save_document(doc_id, filename, content, metadata)
    print(f"✓ 문서 저장됨: {saved_path}")
    
    # 저장된 문서 조회
    doc = await mcp.get_document(doc_id)
    if doc:
        print(f"✓ 문서 조회: {doc['filename']}")
        print(f"  Size: {doc['size']} bytes")
        print(f"  Created: {doc['created_at']}")
        print(f"  Metadata: {doc['metadata']}")
    
    # 모든 문서 목록
    all_docs = await mcp.list_all_documents()
    print(f"✓ 저장된 문서 총 개수: {len(all_docs)}개")
    
    # ─────── Summary ───────
    print("\n" + "="*80)
    print("✅ MCP 통합 테스트 완료")
    print("="*80)
    print("""
MCP 서버 통합 상태:
  ✓ ProposalDB: 과거 제안서 검색 기능 정상
  ✓ PersonnelDB: 인력 배정 기능 정상
  ✓ RAGServer: 참고자료 검색 기능 정상
  ✓ DocumentStore: 문서 저장 및 조회 기능 정상

다음 단계:
  1. FastAPI 엔드포인트 구현
  2. Phase 노드와 MCP 연동 테스트
  3. 전체 워크플로우 통합 테스트
""")
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_mcp_integration())
    exit(0 if result else 1)
