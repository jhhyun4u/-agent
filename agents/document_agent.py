"""
문서 출력 에이전트 (Sub-agent 5/5)

역할:
- 요약문 생성
- 최종 편집
- DOCX/PPTX 문서 생성

노드 구성:
1. generate_executive_summary - 요약문 생성 (LLM)
2. final_edit - 최종 편집 (LLM)
3. export_documents - DOCX/PPTX 생성 (Tool)
"""

from pathlib import Path
from datetime import datetime
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from state.agent_states import DocumentState
from config.claude_optimizer import ModelTier
from app.models.schemas import ProposalContent
from app.services.docx_builder import build_docx
from app.services.pptx_builder import build_pptx


async def generate_executive_summary_node(state: DocumentState) -> dict:
    """요약문 생성 - LLM 사용"""
    sections = state.get("sections", {})
    metadata = state.get("metadata", {})

    llm = ChatAnthropic(model=ModelTier.SONNET.value, temperature=0.5)

    # 섹션 요약 수집
    section_summaries = []
    for section_name, section_data in list(sections.items())[:3]:
        content = section_data.get("content", "")[:1000]
        section_summaries.append(f"**{section_name}**: {content[:200]}...")

    prompt = f"""다음 제안서의 요약문을 작성하세요.

# 프로젝트 정보
사업명: {metadata.get('project_name', '')}
발주처: {metadata.get('client_name', '')}

# 주요 섹션
{chr(10).join(section_summaries)}

# 요구사항
- 1-2페이지 분량 (800-1200자)
- 핵심 메시지와 차별화 포인트 강조
- 경영진이 빠르게 이해할 수 있도록 작성

마크다운 형식으로 작성하세요."""

    response = await llm.ainvoke([
        SystemMessage(content="당신은 제안서 작성 전문가입니다."),
        HumanMessage(content=prompt)
    ])

    executive_summary = response.content

    return {"executive_summary": executive_summary}


def final_edit_node(state: DocumentState) -> dict:
    """최종 편집 - 규칙 기반"""
    sections = state.get("sections", {})

    # 간단한 편집: 형식 통일
    final_edited = {}

    for section_name, section_data in sections.items():
        content = section_data.get("content", "")

        # 기본 편집
        edited_content = content.strip()

        # 이중 공백 제거
        import re
        edited_content = re.sub(r'\n\n\n+', '\n\n', edited_content)

        final_edited[section_name] = {
            **section_data,
            "content": edited_content,
            "edited": True
        }

    return {"final_edited": final_edited}


def export_documents_node(state: DocumentState) -> dict:
    """DOCX/PPTX 문서 생성 - Tool 사용"""
    final_sections = state.get("final_edited", {})
    metadata = state.get("metadata", {})
    executive_summary = state.get("executive_summary", "")

    # ProposalContent 객체 생성
    content = ProposalContent(
        project_overview=executive_summary,
        understanding=final_sections.get("사업 이해도", {}).get("content", "사업 이해도 내용"),
        approach=final_sections.get("접근 방법론", {}).get("content", "접근 방법론 내용"),
        methodology=final_sections.get("수행 방법론", {}).get("content", "수행 방법론 내용"),
        schedule=final_sections.get("추진 일정", {}).get("content", "추진 일정 내용"),
        team_composition=final_sections.get("인력 구성", {}).get("content", "인력 구성 내용"),
        expected_outcomes=final_sections.get("기대 효과", {}).get("content", "기대 효과 내용"),
        budget_plan=final_sections.get("예산 계획", {}).get("content", "")
    )

    # 출력 디렉토리
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = metadata.get("project_name", "제안서")

    # DOCX 생성
    docx_path = output_dir / f"proposal_{timestamp}.docx"
    try:
        docx_result = build_docx(content, project_name, docx_path)
        docx_success = True
    except Exception as e:
        print(f"DOCX 생성 실패: {e}")
        docx_result = None
        docx_success = False

    # PPTX 생성
    pptx_path = output_dir / f"proposal_{timestamp}.pptx"
    try:
        pptx_result = build_pptx(content, project_name, pptx_path)
        pptx_success = True
    except Exception as e:
        print(f"PPTX 생성 실패: {e}")
        pptx_result = None
        pptx_success = False

    export_paths = {
        "docx": str(docx_result) if docx_success else None,
        "pptx": str(pptx_result) if pptx_success else None,
    }

    return {"export_paths": export_paths}


def finalize_document_node(state: DocumentState) -> dict:
    """최종 문서 결과 생성"""
    document_result = {
        "executive_summary": state.get("executive_summary", ""),
        "export_paths": state.get("export_paths", {}),
        "status": "completed"
    }

    return {"document_result": document_result}


def build_document_graph():
    """문서 출력 Sub-agent 그래프 구축"""

    builder = StateGraph(DocumentState)

    # 노드 추가
    builder.add_node("generate_summary", generate_executive_summary_node)
    builder.add_node("final_edit", final_edit_node)
    builder.add_node("export_documents", export_documents_node)
    builder.add_node("finalize", finalize_document_node)

    # 엣지 정의
    builder.add_edge(START, "generate_summary")
    builder.add_edge("generate_summary", "final_edit")
    builder.add_edge("final_edit", "export_documents")
    builder.add_edge("export_documents", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()
