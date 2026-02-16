"""
5-Phase 노드 구현 (Mock 버전, v3.1.1)

각 Phase는 Sub-agent 호출 대신 Mock 데이터를 반환하여 그래프 구조 검증.
실제 구현은 이 노드 내부의 LLM 호출을 교체하면 됨.

노드 구조:
- Phase 실행 노드 (phase_1_research, phase_2_analysis, ...)
- 압축 노드 (compress_phase_1, compress_phase_2, ...)
"""

import sys
import os
from pathlib import Path

# Add project root to path
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import asyncio
from typing import Any, Dict
from datetime import datetime

from state.phased_state import PhasedSupervisorState
from state.phase_artifacts import (
    PhaseArtifact_1_Research,
    PhaseArtifact_2_Analysis,
    PhaseArtifact_3_Plan,
    PhaseArtifact_4_Implement,
)
from graph.mock_data import (
    MOCK_PHASE1_RESULT,
    MOCK_PHASE2_RESULT,
    MOCK_PHASE3_RESULT,
    MOCK_PHASE4_RESULT,
    MOCK_PHASE5_RESULT,
    create_mock_artifact_1,
    create_mock_artifact_2,
    create_mock_artifact_3,
    create_mock_artifact_4,
    create_mock_phase5_working_state,
)

# Sub-agent 임포트
try:
    from services.subagents import (
        Phase1ResearchAgent,
        Phase2AnalysisAgent,
        Phase3StrategyAgent,
        Phase4ImplementAgent,
        Phase5QualityAgent,
    )
    USE_LLM = True
except ImportError:
    print("Warning: Sub-agents not available, using mock data")
    USE_LLM = False

# MCP 서버 임포트
try:
    from services.mcp_server import get_mcp_server
    MCP_SERVER = get_mcp_server()
    USE_MCP = True
except ImportError:
    print("Warning: MCP Server not available")
    MCP_SERVER = None
    USE_MCP = False


# ═══ PHASE 1: RESEARCH NODE ═══

async def phase_1_research_node(state: PhasedSupervisorState) -> Dict[str, Any]:
    """
    Phase 1: Research (RFP 파싱)
    
    Sub-agent: RFP 문서 파싱 → 메타데이터 추출
    입력: RFP 원문
    출력: 구조화된 RFP 정보
    """

    print("🔍 Phase 1: Research (RFP 파싱)")

    # RFP 문서 내용 (proposal_state에서 가져오기)
    rfp_content = state.get("proposal_state", {}).get("rfp_content", "")
    
    if USE_LLM and rfp_content:
        # ── Sub-agent 호출 ──
        try:
            agent = Phase1ResearchAgent()
            result = await agent.invoke({
                "rfp_content": rfp_content,
            })
            
            working_state = {
                "parsed_rfp": result.model_dump(),
                "rfp_title": result.rfp_title,
                "client_name": result.client_name,
            }
            
            content_msg = f"[Phase 1 완료] RFP 파싱: {result.rfp_title} ({result.client_name})"
            
        except Exception as e:
            print(f"    Sub-agent error: {e}, falling back to mock data")
            working_state = {
                **state.get("phase_working_state", {}),
                **MOCK_PHASE1_RESULT,
            }
            content_msg = f"[Phase 1 완료] RFP 파싱: {MOCK_PHASE1_RESULT['parsed_rfp']['title']} (Mock)"
    else:
        # ── Mock 데이터 (Sub-agent 없을 때) ──
        working_state = {
            **state.get("phase_working_state", {}),
            **MOCK_PHASE1_RESULT,
        }
        content_msg = f"[Phase 1 완료] RFP 파싱: {MOCK_PHASE1_RESULT['parsed_rfp']['title']} (Mock)"

    # ── MCP: 유사한 과거 제안서 검색 ──
    similar_proposals = []
    if USE_MCP:
        try:
            rfp_title = working_state.get("rfp_title", "")
            similar_proposals = await MCP_SERVER.search_similar_proposals(rfp_title)
            if similar_proposals:
                working_state["similar_proposals"] = [
                    {"title": p["title"], "client": p["client"], "year": p["year"], "status": p["status"]}
                    for p in similar_proposals[:3]
                ]
                content_msg += f" (참고: 유사 제안서 {len(similar_proposals)}건 검색됨)"
        except Exception as e:
            print(f"    MCP search error: {e}")

    # ── Phase 1 완료 상태 업데이트 ──
    return {
        "current_phase": "phase_1_research",
        "phase_working_state": working_state,
        "agent_status": {
            **state.get("agent_status", {}),
            "phase_1": "completed",
        },
        "messages": [
            *state.get("messages", []),
            {
                "role": "system",
                "content": content_msg,
            },
        ],
    }


# ═══ PHASE 1 압축 NODE ═══

async def compress_phase_1_node(state: PhasedSupervisorState) -> Dict[str, Any]:
    """
    Phase 1 완료 → Artifact #1 생성 → phase_working_state 비움
    
    원칙 (C-2):
    - phase_working_state = {} 로 다음 Phase의 LLM 프롬프트에 이전 데이터 주입 안 함
    - 원본은 proposal_state에 보관
    - MCP가 필요하면 문서 참조로 접근
    """

    print("📦 Phase 1 압축: Artifact #1 생성")

    artifact_1 = create_mock_artifact_1()

    return {
        "phase_artifact_1": artifact_1,
        "phase_working_state": {},  # ★ 컨텍스트 격리 (C-2)
        "proposal_state": {
            **state.get("proposal_state", {}),
            "rfp_analysis": state["phase_working_state"].get("parsed_rfp", {}),
        },
        "messages": [
            *state.get("messages", []),
            {
                "role": "system",
                "content": "[Phase 1 압축] Artifact #1 생성 완료",
            },
        ],
    }


# ═══ PHASE 2: ANALYSIS NODE ═══

async def phase_2_analysis_node(state: PhasedSupervisorState) -> Dict[str, Any]:
    """
    Phase 2: Analysis (분석 및 평가)
    
    Sub-agent: RFP 분석 → 자격 평가, 경쟁 분석
    입력: Phase 1 Artifact (RFP 메타데이터)
    출력: 자격 여부, 강점/약점, 경쟁 환경 분석
    """

    print("🔍 Phase 2: Analysis (구조화 분석)")

    artifact_1 = state.get("phase_artifact_1", {})
    company_profile = state.get("proposal_state", {}).get("company_profile", {})

    if USE_LLM and artifact_1:
        # ── Sub-agent 호출 ──
        try:
            agent = Phase2AnalysisAgent()
            result = await agent.invoke({
                "phase_artifact_1": artifact_1,
                "company_profile": company_profile,
            })
            
            working_state = {
                "rfp_analysis": result.model_dump(),
                "qualification_status": result.qualification_status,
                "our_strengths": result.our_strengths,
                "our_weaknesses": result.our_weaknesses,
            }
            
            content_msg = f"[Phase 2 완료] 자격요건: {result.qualification_status}"
            
        except Exception as e:
            print(f"    Sub-agent error: {e}, falling back to mock data")
            working_state = {
                **state.get("phase_working_state", {}),
                **MOCK_PHASE2_RESULT,
            }
            content_msg = "[Phase 2 완료] 자격요건: 충족 (Mock)"
    else:
        # ── Mock 데이터 ──
        working_state = {
            **state.get("phase_working_state", {}),
            **MOCK_PHASE2_RESULT,
        }
        content_msg = "[Phase 2 완료] 자격요건: 충족 (Mock)"

    return {
        "current_phase": "phase_2_analysis",
        "phase_working_state": working_state,
        "agent_status": {
            **state.get("agent_status", {}),
            "phase_2": "completed",
        },
        "messages": [
            *state.get("messages", []),
            {
                "role": "system",
                "content": content_msg,
            },
        ],
    }


async def compress_phase_2_node(state: PhasedSupervisorState) -> Dict[str, Any]:
    """Phase 2 완료 → Artifact #2 생성"""

    print("📦 Phase 2 압축: Artifact #2 생성")

    artifact_2 = create_mock_artifact_2()

    return {
        "phase_artifact_2": artifact_2,
        "phase_working_state": {},  # ★ 컨텍스트 격리
        "proposal_state": {
            **state.get("proposal_state", {}),
            "rfp_analysis": state["phase_working_state"].get("rfp_analysis", {}),
            "competitive_analysis": state["phase_working_state"].get("competitive_analysis", {}),
        },
        "messages": [
            *state.get("messages", []),
            {
                "role": "system",
                "content": "[Phase 2 압축] Artifact #2 생성 완료",
            },
        ],
    }


# ═══ PHASE 3: PLAN NODE ═══

async def phase_3_plan_node(state: PhasedSupervisorState) -> Dict[str, Any]:
    """
    Phase 3: Plan (전략 수립)
    
    Sub-agent: 전략 수립 → 핵심 메시지, 수주 테마, 인력 배정, 섹션 계획
    입력: Phase 2 Artifact (분석 결과)
    출력: 전략 문서 및 실행 계획
    """

    print("⚔️ Phase 3: Plan (전략 수립)")

    artifact_2 = state.get("phase_artifact_2", {})
    company_profile = state.get("proposal_state", {}).get("company_profile", {})

    if USE_LLM and artifact_2:
        # ── Sub-agent 호출 ──
        try:
            agent = Phase3StrategyAgent()
            result = await agent.invoke({
                "phase_artifact_2": artifact_2,
                "company_profile": company_profile,
            })
            
            working_state = {
                "strategy": result.model_dump(),
                "core_message": result.core_message,
                "win_themes": result.win_themes,
                "personnel_assignments": result.personnel_assignments,
            }
            
            content_msg = f"[Phase 3 완료] 핵심 메시지: {result.core_message[:50]}..."
            
        except Exception as e:
            print(f"    Sub-agent error: {e}, falling back to mock data")
            working_state = {
                **state.get("phase_working_state", {}),
                **MOCK_PHASE3_RESULT,
            }
            content_msg = "[Phase 3 완료] 전략 수립 완료 (Mock)"
    else:
        # ── Mock 데이터 ──
        working_state = {
            **state.get("phase_working_state", {}),
            **MOCK_PHASE3_RESULT,
        }
        content_msg = "[Phase 3 완료] 전략 수립 완료 (Mock)"

    # ── MCP: 인력 배정 및 참고자료 검색 ──
    if USE_MCP:
        try:
            # 전략 기반 필요 기술 목록 추출
            win_themes = working_state.get("win_themes", [])
            required_skills = [theme.split()[0] for theme in win_themes[:3]] if win_themes else []
            
            # 인력 배정
            team = await MCP_SERVER.get_team_for_project(required_skills, 5)
            working_state["allocated_personnel"] = [
                {"name": m["name"], "role": m["role"], "expertise": m["expertise"]}
                for m in team
            ]
            
            # 참고자료 검색 (전략별로)
            references = []
            for theme in win_themes[:2]:
                refs = await MCP_SERVER.search_references(theme, top_k=2)
                references.extend(refs)
            
            if references:
                working_state["rag_references"] = [
                    {"title": r["title"], "topics": r["topics"]}
                    for r in references[:5]
                ]
            
            content_msg += f" (팀: {len(team)}명, 참고자료: {len(references)}건)"
        except Exception as e:
            print(f"    MCP lookup error: {e}")

    return {
        "current_phase": "phase_3_plan",
        "phase_working_state": working_state,
        "agent_status": {
            **state.get("agent_status", {}),
            "phase_3": "completed",
        },
        "messages": [
            *state.get("messages", []),
            {
                "role": "system",
                "content": content_msg,
            },
        ],
    }


async def compress_phase_3_node(state: PhasedSupervisorState) -> Dict[str, Any]:
    """Phase 3 완료 → Artifact #3 생성"""

    print("📦 Phase 3 압축: Artifact #3 생성")

    artifact_3 = create_mock_artifact_3()

    return {
        "phase_artifact_3": artifact_3,
        "phase_working_state": {},  # ★ 컨텍스트 격리
        "proposal_state": {
            **state.get("proposal_state", {}),
            "strategy": state["phase_working_state"].get("strategy", {}),
        },
        "messages": [
            *state.get("messages", []),
            {
                "role": "system",
                "content": "[Phase 3 압축] Artifact #3 생성 완료",
            },
        ],
    }


# ═══ PHASE 4: IMPLEMENT NODE ═══

async def phase_4_implement_node(state: PhasedSupervisorState) -> Dict[str, Any]:
    """
    Phase 4: Implement (섹션 생성)
    
    Sub-agent: 섹션 작성 → 제안서 초안 생성
    입력: Phase 3 Artifact (전략)
    출력: 9개 섹션 초안
    """

    print("✍️ Phase 4: Implement (섹션 생성)")

    artifact_3 = state.get("phase_artifact_3", {})

    if USE_LLM and artifact_3:
        # ── Sub-agent 호출 ──
        try:
            agent = Phase4ImplementAgent()
            result = await agent.invoke({
                "phase_artifact_3": artifact_3,
            })
            
            working_state = {
                "sections": result.sections,
                "total_pages": result.total_pages,
                "required_claims": result.required_claims,
                "traceability_percent": result.traceability_percent,
            }
            
            content_msg = f"[Phase 4 완료] {len(result.sections)}개 섹션 생성 ({result.total_pages:.0f}p)"
            
        except Exception as e:
            print(f"    Sub-agent error: {e}, falling back to mock data")
            working_state = {
                **state.get("phase_working_state", {}),
                **MOCK_PHASE4_RESULT,
            }
            content_msg = f"[Phase 4 완료] {len(MOCK_PHASE4_RESULT['sections'])}개 섹션 생성 (Mock)"
    else:
        # ── Mock 데이터 ──
        working_state = {
            **state.get("phase_working_state", {}),
            **MOCK_PHASE4_RESULT,
        }
        content_msg = f"[Phase 4 완료] {len(MOCK_PHASE4_RESULT['sections'])}개 섹션 생성 (Mock)"

    return {
        "current_phase": "phase_4_implement",
        "phase_working_state": working_state,
        "agent_status": {
            **state.get("agent_status", {}),
            "phase_4": "completed",
        },
        "messages": [
            *state.get("messages", []),
            {
                "role": "system",
                "content": content_msg,
            },
        ],
    }


async def compress_phase_4_node(state: PhasedSupervisorState) -> Dict[str, Any]:
    """Phase 4 완료 → Artifact #4 생성"""

    print("📦 Phase 4 압축: Artifact #4 생성")

    artifact_4 = create_mock_artifact_4()

    return {
        "phase_artifact_4": artifact_4,
        "phase_working_state": {},  # ★ 컨텍스트 격리
        "proposal_state": {
            **state.get("proposal_state", {}),
            "sections": state["phase_working_state"].get("sections", {}),
        },
        "messages": [
            *state.get("messages", []),
            {
                "role": "system",
                "content": "[Phase 4 압축] Artifact #4 생성 완료",
            },
        ],
    }


# ═══ PHASE 5: TEST NODES ═══

async def phase_5_critique_node(state: PhasedSupervisorState) -> Dict[str, Any]:
    """
    Phase 5a: Critique (품질 비평)
    
    Sub-agent: 섹션 평가 → 품질 점수, 문제점, 수정 권고
    입력: Phase 4 Artifact (섹션 초안)
    출력: 품질 평점 및 개선 권고
    """

    print("🔍 Phase 5a: Critique (품질 비평)")

    artifact_4 = state.get("phase_artifact_4", {})

    if USE_LLM and artifact_4:
        # ── Sub-agent 호출 ──
        try:
            agent = Phase5QualityAgent()
            result = await agent.invoke({
                "phase_artifact_4": artifact_4,
            })
            
            working_state = state.get("phase_working_state", {})
            working_state.update({
                "quality_score": result.quality_score,
                "critique_result": result.model_dump(),
                "revision_rounds": 0,
                "structural_issues": result.major_issues,
            })
            
            content_msg = f"[Phase 5a 완료] 품질 점수: {result.quality_score:.2f}"
            
        except Exception as e:
            print(f"    Sub-agent error: {e}, falling back to mock data")
            working_state = state.get("phase_working_state", {})
            working_state.update({
                "quality_score": MOCK_PHASE5_RESULT["quality_score"],
                "critique_result": MOCK_PHASE5_RESULT["critique_result"],
                "revision_rounds": 0,
                "structural_issues": [],
            })
            content_msg = f"[Phase 5a 완료] 품질 점수: {MOCK_PHASE5_RESULT['quality_score']:.2f} (Mock)"
    else:
        # ── Mock 데이터 ──
        working_state = state.get("phase_working_state", {})
        working_state.update({
            "quality_score": MOCK_PHASE5_RESULT["quality_score"],
            "critique_result": MOCK_PHASE5_RESULT["critique_result"],
            "revision_rounds": 0,
            "structural_issues": [],
        })
        content_msg = f"[Phase 5a 완료] 품질 점수: {MOCK_PHASE5_RESULT['quality_score']:.2f} (Mock)"

    return {
        "current_phase": "phase_5_critique",
        "phase_working_state": working_state,
        "agent_status": {
            **state.get("agent_status", {}),
            "phase_5_critique": "completed",
        },
        "messages": [
            *state.get("messages", []),
            {
                "role": "system",
                "content": "[Phase 5a 완료] 품질 점수: {:.2f}".format(
                    MOCK_PHASE5_RESULT["quality_score"]
                ),
            },
        ],
    }


async def phase_5_revise_node(state: PhasedSupervisorState) -> Dict[str, Any]:
    """
    Phase 5b: Revise (적응형 수정)
    
    Token #7: 심각도별 Sonnet/Haiku 선택으로 품질 개선
    """

    print("✏️ Phase 5b: Revise (섹션 수정)")

    # ── Mock: 수정 완료 (실제로는 LLM이 수정) ──
    working_state = state.get("phase_working_state", {})
    working_state["revision_rounds"] = working_state.get("revision_rounds", 0) + 1
    working_state["quality_score"] = min(
        working_state.get("quality_score", 0) + 0.05, 1.0
    )  # 약간 개선

    return {
        "phase_working_state": working_state,
        "agent_status": {
            **state.get("agent_status", {}),
            "phase_5_revise": "completed",
        },
        "messages": [
            *state.get("messages", []),
            {
                "role": "system",
                "content": "[Phase 5b 완료] 수정 라운드: {}".format(
                    working_state["revision_rounds"]
                ),
            },
        ],
    }


async def phase_5_finalize_node(state: PhasedSupervisorState) -> Dict[str, Any]:
    """
    Phase 5c: Finalize (최종 완성)
    
    M-3: Executive Summary를 여기서 생성 (수정 완료 후)
    MCP: DocumentStore에 최종 DOCX 저장
    """

    print("🎯 Phase 5c: Finalize (최종 편집 & 변환)")

    # ── Mock: 최종 변환 완료 ──
    working_state = state.get("phase_working_state", {})
    working_state["final_document_path"] = MOCK_PHASE5_RESULT["export_path"]
    working_state["executive_summary"] = "본 제안서는 마이크로서비스 기반 현대적 클라우드 아키텍처로 디지털 전환을 실현합니다."

    # ── MCP: DocumentStore에 최종 문서 저장 ──
    content_msg = f"[Phase 5 완료] 최종 문서: {MOCK_PHASE5_RESULT['export_path']}"
    
    if USE_MCP:
        try:
            # 제안서 정보
            rfp_title = state.get("proposal_state", {}).get("rfp_title", "Proposal")
            client_name = state.get("proposal_state", {}).get("client_name", "Client")
            
            # 최종 DOCX 바이너리 (실제로는 python-docx로 생성된 바이너리)
            doc_id = f"prop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            filename = f"{rfp_title.replace(' ', '_')}_{client_name}.docx"
            
            # Mock 바이너리 데이터 (실제로는 DOCX 바이너리)
            doc_content = b"[DOCX Binary Content - Python-docx generated]"
            
            # DocumentStore에 저장
            saved_path = await MCP_SERVER.save_document(
                doc_id=doc_id,
                filename=filename,
                content=doc_content,
                metadata={
                    "rfp_title": rfp_title,
                    "client": client_name,
                    "pages": working_state.get("total_pages", 0),
                    "quality_score": working_state.get("quality_score", 0),
                    "revision_rounds": working_state.get("revision_rounds", 0),
                }
            )
            
            working_state["document_store_path"] = saved_path
            content_msg += f" (저장됨: {filename})"
            
        except Exception as e:
            print(f"    MCP document save error: {e}")

    return {
        "current_phase": "phase_5_finalize",
        "phase_working_state": working_state,
        "agent_status": {
            **state.get("agent_status", {}),
            "phase_5_finalize": "completed",
        },
        "messages": [
            *state.get("messages", []),
            {
                "role": "system",
                "content": content_msg,
            },
        ],
    }


# ═══ 라우팅 함수 ═══

def decide_quality_action(state: PhasedSupervisorState) -> str:
    """
    Phase 5 품질 루프 라우팅 (C-3 Fix)
    
    - score >= 0.75 → pass (최종화)
    - score < 0.75 and rounds < 3 → revise (재수정)
    - rounds >= 3 or structural_issues → escalate (사람 판단)
    """

    ws = state.get("phase_working_state", {})
    score = ws.get("quality_score", 0)
    rounds = ws.get("revision_rounds", 0)
    issues = ws.get("structural_issues", [])

    if issues:
        return "escalate"  # 구조적 문제 → HITL Gate #5
    if score >= 0.75:
        return "pass"  # 최종화로 진행
    if rounds >= 3:
        return "escalate"  # 3회 수정 후에도 미달 → HITL Gate #5
    return "revise"  # 재수정


if __name__ == "__main__":
    # 테스트: 모든 노드 함수 검증

    async def test_phase_nodes():
        from state.phased_state import initialize_phased_supervisor_state

        print("🧪 Phase 노드 테스트\n")

        state = initialize_phased_supervisor_state()

        # Phase 1
        result = await phase_1_research_node(state)
        state.update(result)
        print(f"✅ Phase 1: {state['agent_status'].get('phase_1')}\n")

        # Compress 1
        result = await compress_phase_1_node(state)
        state.update(result)
        print(f"✅ Compress 1: artifact_1 생성\n")

        # Phase 2
        result = await phase_2_analysis_node(state)
        state.update(result)
        print(f"✅ Phase 2: {state['agent_status'].get('phase_2')}\n")

        # Compress 2
        result = await compress_phase_2_node(state)
        state.update(result)
        print(f"✅ Compress 2: artifact_2 생성\n")

        # Phase 3
        result = await phase_3_plan_node(state)
        state.update(result)
        print(f"✅ Phase 3: {state['agent_status'].get('phase_3')}\n")

        # Compress 3
        result = await compress_phase_3_node(state)
        state.update(result)
        print(f"✅ Compress 3: artifact_3 생성\n")

        # Phase 4
        result = await phase_4_implement_node(state)
        state.update(result)
        print(f"✅ Phase 4: {state['agent_status'].get('phase_4')}\n")

        # Compress 4
        result = await compress_phase_4_node(state)
        state.update(result)
        print(f"✅ Compress 4: artifact_4 생성\n")

        # Phase 5a
        result = await phase_5_critique_node(state)
        state.update(result)
        print(f"✅ Phase 5a: 품질 점수 {state['phase_working_state'].get('quality_score')}\n")

        # 라우팅 테스트
        action = decide_quality_action(state)
        print(f"✅ 품질 라우팅: {action}\n")

        print("✅ 모든 Phase 노드 정상 작동")

    asyncio.run(test_phase_nodes())
