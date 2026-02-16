"""
v3.1.1 핵심 기능 통합 테스트 (FastAPI 없이)

MCP 서버 + Phase 노드 + State 통합 테스트
"""

import sys
import os
from pathlib import Path

_project_root = str(Path(__file__).parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import asyncio
from datetime import datetime
from graph import build_phased_supervisor_graph
from state.phased_state import initialize_phased_supervisor_state
from services.mcp_server import get_mcp_server


async def test_full_workflow():
    """전체 워크플로우 테스트"""
    
    print("\n" + "="*80)
    print("v3.1.1 완전 통합 테스트: MCP + Phase + State")
    print("="*80)
    
    # ─────── Setup ───────
    print("\n[Setup] 리소스 초기화")
    print("-" * 80)
    
    mcp = get_mcp_server()
    
    # 제안서 ID
    proposal_id = f"prop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 회사 프로필
    company_profile = {
        "name": "테크노베이션파트너스",
        "capabilities": ["클라우드 아키텍처", "AI/ML 솔루션", "DevOps 자동화"],
        "experience_years": 15,
    }
    
    # State 초기화
    state = initialize_phased_supervisor_state(
        rfp_document_ref=proposal_id,
        company_profile=company_profile,
        express_mode=False,
    )
    
    # RFP 정보 입력
    state["proposal_state"] = {
        "rfp_title": "클라우드 마이그레이션 제안 요청서",
        "client_name": "삼성전자",
        "rfp_content": "레거시 온프레미스 시스템을 AWS 클라우드로 마이그레이션합니다.",
        "company_profile": company_profile,
    }
    
    print(f"✓ Proposal ID: {proposal_id}")
    print(f"✓ RFP: {state['proposal_state']['rfp_title']}")
    print(f"✓ Client: {state['proposal_state']['client_name']}")
    print(f"✓ Express Mode: False")
    
    # ─────── Test 1: Graph 빌드 ───────
    print("\n[TEST 1] LangGraph 빌드")
    print("-" * 80)
    
    try:
        graph = build_phased_supervisor_graph()
        print(f"✓ Graph 빌드 성공")
        print(f"✓ Graph 노드 수: {len(graph.nodes)}")
    except Exception as e:
        print(f"✗ Graph 빌드 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ─────── Test 2: MCP 검색 ───────
    print("\n[TEST 2] MCP 시스템 검증")
    print("-" * 80)
    
    try:
        # ProposalDB 검색
        similar = await mcp.search_similar_proposals("클라우드")
        print(f"✓ ProposalDB: {len(similar)}건 검색됨")
        
        # PersonnelDB 검색
        team = await mcp.get_team_for_project(["AWS", "Python"], 5)
        print(f"✓ PersonnelDB: {len(team)}명 배정됨")
        
        # RAGServer 검색
        refs = await mcp.search_references("클라우드 아키텍처", top_k=3)
        print(f"✓ RAGServer: {len(refs)}건 검색됨")
        
    except Exception as e:
        print(f"✗ MCP 검색 실패: {e}")
        return False
    
    # ─────── Test 3: 상태 검증 ───────
    print("\n[TEST 3] State 검증")
    print("-" * 80)
    
    try:
        # 필수 필드 확인
        assert "current_phase" in state, "current_phase 필드 누락"
        assert "proposal_state" in state, "proposal_state 필드 누락"
        assert "phase_working_state" in state, "phase_working_state 필드 누락"
        assert "messages" in state, "messages 필드 누락"
        assert "hitl_decisions" in state, "hitl_decisions 필드 누락"
        
        print(f"✓ State 필드 검증: 모두 정상")
        print(f"✓ current_phase: {state['current_phase']}")
        print(f"✓ RFP Title: {state['proposal_state']['rfp_title']}")
        
    except AssertionError as e:
        print(f"✗ State 검증 실패: {e}")
        return False
    
    # ─────── Test 4: 시뮬레이션 (Mock 데이터) ───────
    print("\n[TEST 4] 제안서 생성 시뮬레이션")
    print("-" * 80)
    
    try:
        phase_sequence = [
            ("phase_1_research", "🔍 RFP 분석"),
            ("phase_2_analysis", "📊 경쟁 분석"),
            ("phase_3_plan", "⚔️ 전략 수립"),
            ("phase_4_implement", "✍️ 섹션 작성"),
            ("phase_5_finalize", "🎯 최종 완성"),
        ]
        
        for i, (phase_name, desc) in enumerate(phase_sequence, 1):
            state["current_phase"] = phase_name
            
            # MCP 데이터 시뮬레이션
            if i == 1:
                similar = await mcp.search_similar_proposals("클라우드")
                state["phase_working_state"]["similar_proposals"] = similar[:3]
            elif i == 3:
                team = await mcp.get_team_for_project(["AWS"], 5)
                state["phase_working_state"]["allocated_personnel"] = team
            elif i == 5:
                # 최종 문서 저장
                doc_id = f"prop_final_{proposal_id}"
                filepath = await mcp.save_document(
                    doc_id,
                    "제안서_최종본.docx",
                    b"[DOCX Final Document]",
                    {"quality_score": 0.85, "pages": 120}
                )
                state["phase_working_state"]["document_store_path"] = filepath
            
            print(f"  {i}. {desc}")
        
        print(f"✓ 모든 Phase 시뮬레이션 완료")
        
    except Exception as e:
        print(f"✗ 시뮬레이션 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ─────── Test 5: DocumentStore 검증 ───────
    print("\n[TEST 5] DocumentStore 검증")
    print("-" * 80)
    
    try:
        docs = await mcp.list_all_documents()
        print(f"✓ 저장된 문서: {len(docs)}개")
        
        for doc in docs:
            print(f"  - {doc['filename']}")
        
    except Exception as e:
        print(f"✗ DocumentStore 검증 실패: {e}")
        return False
    
    # ─────── Summary ───────
    print("\n" + "="*80)
    print("✅ 완전 통합 테스트 완료")
    print("="*80)
    print(f"""
테스트 결과:
  ✓ LangGraph v3.1.1 구축 성공
  ✓ MCP 서버 4개 서비스 정상 작동
  ✓ State 스키마 검증 완료
  ✓ Phase 시뮬레이션 통과
  ✓ DocumentStore 저장 및 조회 정상

시스템 상태:
  - Proposal ID: {proposal_id}
  - RFP: {state['proposal_state']['rfp_title']}
  - Client: {state['proposal_state']['client_name']}
  - Phases Completed: 5/5
  - Quality Score: 0.85 (Mock)
  - Total Documents: {len(docs)}

다음 단계:
  1. ✅ MCP 서버 통합 완료
  2. ✅ Phase 노드 구현 완료
  3. ⏳ FastAPI 웹 서버 배포 준비
  4. ⏳ Docker 컨테이너화
  5. ⏳ 프로덕션 배포
""")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_full_workflow())
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 테스트 오류: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
