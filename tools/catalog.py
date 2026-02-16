"""
Skill/Tool 카탈로그 - 여러 에이전트가 공유하는 도구.

v3.0: Tool Registry 패턴으로 에이전트별 필요한 도구만 배정.

설계: Part IV - Skill/Tool 체계
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Literal


# ═══════════════════════════════════════════════════════════════════════════
# 계산/변환 Tools
# ═══════════════════════════════════════════════════════════════════════════

class TokenEstimateInput(BaseModel):
    text: str = Field(description="토큰 수를 추정할 텍스트")
    model: str = Field(default="claude-sonnet-4-5", description="대상 모델")


@tool("estimate_tokens", args_schema=TokenEstimateInput)
def estimate_tokens(text: str, model: str = "claude-sonnet-4-5") -> dict:
    """
    Claude 토큰 수를 추정합니다.
    
    한국어 토크나이저 특성:
    - 한글 1글자 ≈ 1.2토큰 (평균)
    - 영글 약 0.25토큰/글자 (대략)
    - 공백/기호: 약 0.5토큰
    
    ※ 정밀 계산은 Anthropic Token Counting API 권장.
    """
    korean_chars = sum(1 for c in text if '\uac00' <= c <= '\ud7a3')
    ascii_chars = sum(1 for c in text if c.isascii() and c.isalnum())
    other_chars = len(text) - korean_chars - ascii_chars

    tokens = int(korean_chars * 1.2 + ascii_chars * 0.25 + other_chars * 0.5)

    return {
        "estimated_tokens": tokens,
        "model": model,
        "character_count": len(text),
        "korean_ratio": round(korean_chars / max(len(text), 1), 2),
        "note": "추정치이므로 실제와 다를 수 있습니다.",
    }


class PageEstimateInput(BaseModel):
    text: str = Field(description="분량을 추정할 텍스트")
    chars_per_page: int = Field(default=1800, description="페이지당 글자 수 (한국어 기본 1800)")


@tool("estimate_pages", args_schema=PageEstimateInput)
def estimate_pages(text: str, chars_per_page: int = 1800) -> dict:
    """텍스트의 페이지 수를 추정합니다."""
    pages = len(text) / chars_per_page
    return {
        "estimated_pages": round(pages, 1),
        "character_count": len(text),
        "chars_per_page": chars_per_page,
    }


class ScoreAllocationInput(BaseModel):
    evaluation_criteria: list[dict] = Field(
        description="평가 항목 리스트 [{name, score}, ...]"
    )
    total_pages: int = Field(default=50, description="전체 목표 페이지 수")


@tool("calculate_score_allocation", args_schema=ScoreAllocationInput)
def calculate_score_allocation(
    evaluation_criteria: list[dict],
    total_pages: int = 50
) -> dict:
    """
    평가 배점에 따라 섹션별 목표 분량을 산출합니다.
    
    배점 비중이 높을수록:
    - 더 많은 페이지 할당
    - 깊이(depth)가 깊음
    - 우선순위(priority)가 높음
    """
    total_score = sum(c.get("score", 0) for c in evaluation_criteria)
    if total_score == 0:
        return {"error": "total_score가 0입니다."}

    allocations = []
    for c in evaluation_criteria:
        score = c.get("score", 0)
        weight = score / total_score
        target = max(2, round(weight * total_pages))

        # 깊이 및 우선순위 결정
        if weight > 0.2:
            depth = "deep"
            priority = "critical"
        elif weight > 0.15:
            depth = "standard"
            priority = "high"
        elif weight > 0.1:
            depth = "standard"
            priority = "normal"
        else:
            depth = "brief"
            priority = "normal"

        allocations.append({
            "category": c.get("name", ""),
            "score": score,
            "weight": round(weight, 3),
            "target_pages": target,
            "depth": depth,
            "priority": priority,
        })

    return {
        "allocations": allocations,
        "total_pages": total_pages,
        "total_score": total_score,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 검증 Tools
# ═══════════════════════════════════════════════════════════════════════════

class TraceabilityInput(BaseModel):
    rfp_requirements: list[dict] = Field(
        description="RFP 요구사항 목록 [{description, keywords}, ...]"
    )
    section_content: str = Field(description="섹션 본문 내용")


@tool("check_traceability", args_schema=TraceabilityInput)
def check_traceability(
    rfp_requirements: list[dict],
    section_content: str
) -> dict:
    """
    RFP 요구사항과 섹션 내용의 추적성을 검증합니다.
    
    각 RFP 요구사항이 섹션에서 충분히 다루어졌는지 확인.
    """
    matched = []
    unmatched = []

    for req in rfp_requirements:
        keywords = req.get("keywords", [req.get("description", "")])
        found = any(kw.lower() in section_content.lower() for kw in keywords if kw)

        if found:
            matched.append(req.get("description", ""))
        else:
            unmatched.append(req.get("description", ""))

    total = len(rfp_requirements)
    coverage = len(matched) / max(total, 1) if total > 0 else 0

    return {
        "total_requirements": total,
        "matched": len(matched),
        "unmatched": len(unmatched),
        "coverage_rate": round(coverage, 2),
        "missing_requirements": unmatched,
        "status": "✅ 완전히 추적 가능" if coverage >= 0.95
                  else "⚠️ 부분적 추적" if coverage >= 0.7
                  else "❌ 대부분 누락",
    }


class ConsistencyInput(BaseModel):
    sections: dict = Field(description="섹션 {section_id: content}")
    check_type: Literal["numbers", "terminology", "logic"] = Field(
        description="검증 유형"
    )


@tool("check_consistency", args_schema=ConsistencyInput)
def check_consistency(sections: dict, check_type: str) -> dict:
    """
    섹션 간 정합성을 검증합니다.
    
    - numbers: 인력 수, 예산, 기간 등의 일관성
    - terminology: 같은 개념의 용어 통일
    - logic: 전략 → 방법론 → 일정의 논리적 흐름
    """
    issues = []

    if check_type == "numbers":
        # 수치 추출 및 비교 (실제 구현에서는 정규식 사용)
        section_texts = "\n".join(sections.values()) if isinstance(sections, dict) else str(sections)
        # 예시: 인력 수 일관성 확인
        issues.append({
            "type": "note",
            "message": "수치 검증은 제한적입니다. 수동 검토 권장.",
        })

    elif check_type == "terminology":
        # 용어 통일성 검증
        issues.append({
            "type": "note",
            "message": "용어 검증은 제한적입니다. 수동 검토 권장.",
        })

    elif check_type == "logic":
        # 논리적 흐름 검증
        issues.append({
            "type": "note",
            "message": "논리적 흐름은 LLM 기반 비평에서 검증됩니다.",
        })

    return {
        "check_type": check_type,
        "issues_found": len([i for i in issues if i.get("type") == "issue"]),
        "issues": issues,
        "recommendation": "자세한 검증은 LLM 기반 품질 검토 단계에서 수행됩니다.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# 생성 Tools (시각 자료 등)
# ═══════════════════════════════════════════════════════════════════════════

class MermaidInput(BaseModel):
    diagram_type: str = Field(description="다이어그램 유형: flowchart, gantt, org_chart")
    description: str = Field(description="다이어그램에 대한 자연어 설명")


@tool("generate_mermaid", args_schema=MermaidInput)
def generate_mermaid(diagram_type: str, description: str) -> dict:
    """
    자연어 설명에서 Mermaid 다이어그램 코드를 생성합니다.
    
    실제 구현에서는 LLM을 호출하여 Mermaid 코드를 생성합니다.
    이 프로토타입에서는 템플릿 반환.
    """
    templates = {
        "flowchart": "graph TD\n  A[시작] --> B[처리]\n  B --> C[완료]",
        "gantt": "gantt\n  title 프로젝트 일정\n  section 본 업무\n  작업 1 :a1, 2024-01-01, 30d",
        "org_chart": "graph TD\n  CEO[CEO]\n  CEO --> PM[PM]\n  PM --> DEV[개발팀]",
    }

    return {
        "mermaid_code": templates.get(diagram_type, templates["flowchart"]),
        "diagram_type": diagram_type,
        "description": description,
        "note": "프로토타입 템플릿입니다. 실제 구현에서는 LLM으로 정제된 다이어그램을 생성합니다.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# Tool Registry
# ═══════════════════════════════════════════════════════════════════════════

class ToolRegistry:
    """
    중앙 Tool 레지스트리.
    각 Sub-agent는 필요한 Tool만 선택적으로 받아 사용합니다.
    
    설계: Part IV.12.2
    """

    def __init__(self):
        self._tools = {}
        self._mcp_tools = {}

    def register(self, tool_func, category: str = "utility"):
        """Tool 등록"""
        self._tools[tool_func.name] = {
            "tool": tool_func,
            "category": category,
            "description": tool_func.__doc__ or "",
        }

    def register_mcp_tools(self, tools: list, server_name: str):
        """MCP 서버의 Tool들을 일괄 등록"""
        for tool in tools:
            tool_key = f"{server_name}.{tool.get('name', 'unknown')}"
            self._mcp_tools[tool_key] = tool

    def get_tools_for_agent(self, agent_name: str) -> list:
        """특정 에이전트에 배정된 Tool 목록 반환"""

        AGENT_TOOL_MAP = {
            "rfp_analysis": [
                "estimate_tokens",
                "estimate_pages",
            ],
            "strategy": [
                "calculate_score_allocation",
            ],
            "section_generation": [
                "estimate_tokens",
                "estimate_pages",
                "check_traceability",
                "generate_mermaid",
            ],
            "quality": [
                "estimate_tokens",
                "estimate_pages",
                "check_traceability",
                "check_consistency",
            ],
            "document": [
                "estimate_pages",
                "generate_mermaid",
            ],
        }

        tool_names = AGENT_TOOL_MAP.get(agent_name, [])
        result = []

        for name in tool_names:
            if name in self._tools:
                result.append(self._tools[name]["tool"])

        return result

    def get_all_tools(self) -> dict:
        """모든 등록된 Tool 반환"""
        return self._tools

    def get_tool_info(self, tool_name: str) -> dict | None:
        """특정 Tool의 정보 반환"""
        return self._tools.get(tool_name)


def create_default_registry() -> ToolRegistry:
    """기본 Tool Registry 생성"""
    registry = ToolRegistry()

    # 계산 Tools
    registry.register(estimate_tokens, "calculation")
    registry.register(estimate_pages, "calculation")
    registry.register(calculate_score_allocation, "calculation")

    # 검증 Tools
    registry.register(check_traceability, "verification")
    registry.register(check_consistency, "verification")

    # 생성 Tools
    registry.register(generate_mermaid, "generation")

    return registry
