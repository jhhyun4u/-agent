"""
Sub-agent 기본 구조 (v3.1.1)

각 Phase의 Sub-agent는 Claude를 호출하여 작업 수행.
구조화된 출력을 Pydantic으로 검증.
"""

import sys
import os
from pathlib import Path

_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import asyncio
import json
from typing import Any, Dict, Type, TypeVar, Generic, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import anthropic

# Pydantic 임포트
try:
    from pydantic import BaseModel, ValidationError
except ImportError:
    BaseModel = object
    ValidationError = ValueError

T = TypeVar('T', bound=BaseModel)


class SubAgentBase(ABC, Generic[T]):
    """Sub-agent 기본 클래스
    
    각 Phase의 Sub-agent는 이를 상속받아:
    - prompt 작성
    - parse_response()로 출력 파싱
    - model 선택 (Sonnet/Haiku)
    """
    
    def __init__(
        self,
        phase_name: str,
        output_model: Type[T],
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Args:
            phase_name: Phase 이름 (예: "phase_1_research")
            output_model: 출력 Pydantic 모델
            model: Claude 모델 (sonnet/haiku)
            temperature: 창의성 (0-1)
            max_tokens: 최대 토큰
        """
        self.phase_name = phase_name
        self.output_model = output_model
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = anthropic.Anthropic()
    
    @abstractmethod
    def build_prompt(self, context: Dict[str, Any]) -> str:
        """Phase별 프롬프트 작성 (서브클래스에서 구현)
        
        Args:
            context: 입력 데이터 (artifact, working_state 등)
            
        Returns:
            Claude에게 줄 프롬프트 문자열
        """
        pass
    
    async def invoke(self, context: Dict[str, Any]) -> T:
        """Claude를 호출하여 작업 수행
        
        Args:
            context: 입력 데이터
            
        Returns:
            Pydantic 모델로 파싱된 결과
            
        Raises:
            ValidationError: 출력이 모델과 맞지 않을 때
        """
        
        # 1. 프롬프트 작성
        prompt = self.build_prompt(context)
        
        print(f"\n[{self.phase_name}] Claude 호출...")
        print(f"  Model: {self.model}")
        print(f"  Tokens: {self.max_tokens}")
        
        # 2. Claude 호출
        response = await self._call_claude(prompt)
        
        # 3. 응답 파싱
        result = self.parse_response(response)
        
        print(f"  [OK] 응답 수신 (길이: {len(str(result))//100}kB)")
        
        return result
    
    async def _call_claude(self, prompt: str) -> str:
        """Claude API 호출 (비동기)"""
        
        loop = asyncio.get_event_loop()
        
        def _sync_call():
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )
            return message.content[0].text
        
        return await loop.run_in_executor(None, _sync_call)
    
    def parse_response(self, response: str) -> T:
        """Claude 응답을 Pydantic 모델로 파싱
        
        Args:
            response: Claude의 텍스트 응답
            
        Returns:
            파싱된 Pydantic 모델
            
        Raises:
            ValidationError: JSON 파싱 또는 검증 실패
        """
        
        # JSON 추출 (```json ... ``` 형식 지원)
        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.index("```") + 3
            end = response.index("```", start)
            json_str = response[start:end].strip()
        else:
            json_str = response
        
        # JSON 파싱
        data = json.loads(json_str)
        
        # Pydantic 검증
        return self.output_model.model_validate(data)


# ─────────────────────────────────────────
# Phase 1: RFP Analysis Sub-agent
# ─────────────────────────────────────────

class Phase1RFPResult(BaseModel):
    """Phase 1 출력 모델"""
    
    rfp_title: str
    client_name: str
    page_limit: int
    budget_range_min: Optional[int] = None
    budget_range_max: Optional[int] = None
    submission_deadline: str
    evaluation_method: str
    
    mandatory_requirements: list[str]
    optional_requirements: list[str]
    
    class Config:
        json_schema_extra = {"max_tokens": 8000}


class Phase1ResearchAgent(SubAgentBase[Phase1RFPResult]):
    """Phase 1: RFP 파싱 Sub-agent
    
    입력: RFP 원문
    출력: 구조화된 RFP 메타데이터
    """
    
    def build_prompt(self, context: Dict[str, Any]) -> str:
        rfp_content = context.get("rfp_content", "")
        
        return f"""
RFP(제안요청서) 문서를 분석하여 다음 정보를 추출하세요.

【RFP 원문】
{rfp_content}

【작업】
다음 정보를 정확히 추출하고 JSON 형식으로 반환하세요:

1. rfp_title: 프로젝트명/RFP 제목
2. client_name: 발주처명
3. page_limit: 제안서 분량 제한 (페이지 수)
4. budget_range_min/max: 예산 범위 (원, 없으면 null)
5. submission_deadline: 제출 마감일 (YYYY-MM-DD)
6. evaluation_method: 평가 방법 (예: 가격 + 기술 + 경험)
7. mandatory_requirements: 필수 요구사항 리스트 (최대 20개)
8. optional_requirements: 선택 요구사항 리스트 (최대 10개)

【출력 형식】
```json
{{
    "rfp_title": "...",
    "client_name": "...",
    "page_limit": 100,
    "budget_range_min": 100000000,
    "budget_range_max": 200000000,
    "submission_deadline": "2024-12-31",
    "evaluation_method": "...",
    "mandatory_requirements": ["요구사항 1", "요구사항 2", ...],
    "optional_requirements": ["선택사항 1", ...]
}}
```

JSON만 반환하세요. 설명은 제외합니다.
"""
    
    def __init__(self):
        super().__init__(
            phase_name="Phase 1: RFP Analysis",
            output_model=Phase1RFPResult,
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
        )


# ─────────────────────────────────────────
# Phase 2: Analysis Sub-agent
# ─────────────────────────────────────────

class Phase2AnalysisResult(BaseModel):
    """Phase 2 출력 모델"""
    
    qualification_status: str  # "충족" / "미충족" / "부분충족"
    qualification_gaps: Optional[list[str]] = None
    
    our_strengths: list[str]
    our_weaknesses: list[str]
    
    competitive_landscape: str
    market_position: str
    
    recommended_strategy: str
    risk_factors: list[str]
    
    class Config:
        json_schema_extra = {"max_tokens": 10000}


class Phase2AnalysisAgent(SubAgentBase[Phase2AnalysisResult]):
    """Phase 2: 분석 Sub-agent
    
    입력: Phase 1 Artifact (RFP 메타데이터) + 회사 정보
    출력: 자격 분석, 강점/약점, 경쟁 환경
    """
    
    def build_prompt(self, context: Dict[str, Any]) -> str:
        artifact_1 = context.get("phase_artifact_1", {})
        company_profile = context.get("company_profile", {})
        
        return f"""
RFP 분석 및 경쟁력 평가를 수행하세요.

【RFP 정보】
- 제목: {artifact_1.get('rfp_title', '')}
- 발주처: {artifact_1.get('client_name', '')}
- 분량: {artifact_1.get('page_limit', '')}p
- 마감: {artifact_1.get('submission_deadline', '')}
- 필수요건: {', '.join(artifact_1.get('mandatory_requirements', [])[:3])}

【우리 회사】
- 이름: {company_profile.get('name', '')}
- 업종: {company_profile.get('industry', '')}
- 주요역량: {company_profile.get('capabilities', '')}

【작업】
1. 자격요건 충족 여부 평가 (충족/미충족/부분충족)
2. 우리 회사의 강점 3-5개
3. 약점 또는 우려사항 2-4개
4. 경쟁사 환경 분석
5. 시장 위치 평가
6. 추천 전략
7. 위험 요인

【출력 형식】
```json
{{
    "qualification_status": "충족",
    "qualification_gaps": null,
    "our_strengths": ["강점 1", "강점 2", ...],
    "our_weaknesses": ["약점 1", "약점 2"],
    "competitive_landscape": "...",
    "market_position": "...",
    "recommended_strategy": "...",
    "risk_factors": ["위험 1", "위험 2"]
}}
```

JSON만 반환하세요.
"""
    
    def __init__(self):
        super().__init__(
            phase_name="Phase 2: Analysis",
            output_model=Phase2AnalysisResult,
            model="claude-3-5-sonnet-20241022",
            max_tokens=3000,
        )


# ─────────────────────────────────────────
# Phase 3: Strategy Sub-agent
# ─────────────────────────────────────────

class Phase3StrategyResult(BaseModel):
    """Phase 3 출력 모델"""
    
    core_message: str
    win_themes: list[str]
    differentiators: list[str]
    
    personnel_assignments: list[dict]  # [{"role": "PM", "name": "...", "grade": "..."}, ...]
    
    section_plans: list[dict]  # [{"name": "섹션명", "key_message": "...", "pages": 10}, ...]
    generation_order: list[list[str]]  # [[sec_01], [sec_02, sec_03], ...]
    
    class Config:
        json_schema_extra = {"max_tokens": 12000}


class Phase3StrategyAgent(SubAgentBase[Phase3StrategyResult]):
    """Phase 3: 전략 수립 Sub-agent
    
    입력: Phase 2 Artifact (분석 결과)
    출력: 핵심 메시지, 수주 테마, 인력 배정, 섹션 계획
    """
    
    def build_prompt(self, context: Dict[str, Any]) -> str:
        artifact_2 = context.get("phase_artifact_2", {})
        company_profile = context.get("company_profile", {})
        
        return f"""
제안서 전략을 수립하세요.

【분석 결과】
- 자격: {artifact_2.get('qualification_status', '')}
- 강점: {', '.join(artifact_2.get('our_strengths', [])[:2])}
- 전략: {artifact_2.get('recommended_strategy', '')}

【회사 정보】
- 이름: {company_profile.get('name', '')}
- 역량: {company_profile.get('capabilities', '')}

【작업】
1. 핵심 메시지 (한 문장, 명확함)
2. 수주 테마 3-5개
3. 차별화 포인트 3-4개
4. 핵심 인력 배정 (PM, 기술리드, 자문역 등)
5. 분량 배분 (9개 섹션, 총 100p)
6. 생성 순서 (병렬 가능한 섹션 그룹화)

【출력 형식】
```json
{{
    "core_message": "우리는 ...",
    "win_themes": ["테마1", "테마2", "테마3"],
    "differentiators": ["차별점1", "차별점2"],
    "personnel_assignments": [
        {{"role": "PM", "name": "김철수", "grade": "매니저"}},
        {{"role": "CTO", "name": "이영희", "grade": "리더"}}
    ],
    "section_plans": [
        {{"name": "1. 회사개요", "key_message": "...", "pages": 10}}
    ],
    "generation_order": [["1. 회사개요"], ["2. 솔루션", "3. 구현계획"]]
}}
```

JSON만 반환하세요.
"""
    
    def __init__(self):
        super().__init__(
            phase_name="Phase 3: Strategy",
            output_model=Phase3StrategyResult,
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
        )


# ─────────────────────────────────────────
# Phase 4: Implementation Sub-agent
# ─────────────────────────────────────────

class Phase4ImplementResult(BaseModel):
    """Phase 4 출력 모델"""
    
    sections: list[dict]  # [{"name": "1. 회사개요", "content": "...", "pages": 10}, ...]
    total_pages: float
    section_summaries: dict  # {"1": "회사개요 내용 요약", ...}
    
    required_claims: list[str]
    traceability_percent: float
    
    class Config:
        json_schema_extra = {"max_tokens": 15000}


class Phase4ImplementAgent(SubAgentBase[Phase4ImplementResult]):
    """Phase 4: 섹션 생성 Sub-agent
    
    입력: Phase 3 Artifact (전략)
    출력: 9개 섹션 초안 작성
    """
    
    def build_prompt(self, context: Dict[str, Any]) -> str:
        artifact_3 = context.get("phase_artifact_3", {})
        
        sections = artifact_3.get("section_plans", [])[:3]  # 처음 3개만 예시
        
        return f"""
RFP 제안서 섹션을 작성하세요.

【전략】
- 핵심 메시지: {artifact_3.get('core_message', '')}
- 수주 테마: {', '.join(artifact_3.get('win_themes', [])[:2])}

【작성할 섹션 (처음 3개)】
"""+ "\n".join([f"- {s.get('name', '')}: {s.get('key_message', '')} ({s.get('pages', 10)}p)" 
    for s in sections]) + f"""

【작업】
각 섹션에 대해:
1. 구성 요소와 내용 개요
2. 핵심 주장 (claims) 작성
3. 수주 테마와의 연결고리
4. 예상 페이지수

【출력 형식】
```json
{{
    "sections": [
        {{"name": "1. 회사개요", "content": "우리는...", "pages": 10}},
        {{"name": "2. 솔루션개요", "content": "제안...", "pages": 15}}
    ],
    "total_pages": 25.0,
    "section_summaries": {{"1": "회사 역사와 역량 설명", "2": "솔루션의 기술적 특징"}},
    "required_claims": ["주요 주장 1", "주요 주장 2"],
    "traceability_percent": 0.95
}}
```

JSON만 반환하세요.
"""
    
    def __init__(self):
        super().__init__(
            phase_name="Phase 4: Implementation",
            output_model=Phase4ImplementResult,
            model="claude-3-5-sonnet-20241022",
            max_tokens=5000,
        )


# ─────────────────────────────────────────
# Phase 5: Quality Review Sub-agent
# ─────────────────────────────────────────

class Phase5QualityResult(BaseModel):
    """Phase 5 출력 모델"""
    
    quality_score: float  # 0.0 ~ 1.0
    
    individual_scores: dict  # {"section_quality": 0.8, "claim_strength": 0.9, ...}
    critique: str
    
    major_issues: list[str]  # 심각한 문제
    minor_issues: list[str]  # 경미한 문제
    
    revision_recommendations: list[str]
    revised_sections: Optional[dict] = None  # 수정된 섹션
    
    class Config:
        json_schema_extra = {"max_tokens": 15000}


class Phase5QualityAgent(SubAgentBase[Phase5QualityResult]):
    """Phase 5: 품질 비평 Sub-agent
    
    입력: Phase 4 Artifact (섹션 초안)
    출력: 품질 점수, 문제점, 수정 권고
    """
    
    def build_prompt(self, context: Dict[str, Any]) -> str:
        artifact_4 = context.get("phase_artifact_4", {})
        sections = artifact_4.get("sections", [])[:2]
        
        return f"""
제안서 품질을 종합 평가하세요.

【작성된 섹션】
""" + "\n".join([f"- {s.get('name', '')}: {s.get('content', '')[:100]}..." 
    for s in sections]) + f"""

【평가 항목】
1. 각 섹션 품질 (0-1 스케일)
2. 요구사항 커버리지 확인
3. 논리적 일관성
4. 주장의 근거 정확성
5. 분량 적절성
6. 언어 표현 질

【출력 형식】
```json
{{
    "quality_score": 0.78,
    "individual_scores": {{
        "section_quality": 0.75,
        "claim_strength": 0.82,
        "logical_consistency": 0.80
    }},
    "critique": "전반적으로 양호하나 몇 가지 개선 필요...",
    "major_issues": ["XX 부분이 명확하지 않음", "YY 주장의 근거 필요"],
    "minor_issues": ["문법 오류 2개", "표 형식 통일"],
    "revision_recommendations": ["XX 섹션 추가 설명", "YY 데이터 최신화"],
    "revised_sections": null
}}
```

JSON만 반환하세요.
"""
    
    def __init__(self):
        super().__init__(
            phase_name="Phase 5: Quality Review",
            output_model=Phase5QualityResult,
            model="claude-3-5-sonnet-20241022",
            max_tokens=5000,
        )


if __name__ == "__main__":
    print("Sub-agent 모듈 로드 완료")
    print(f"- Phase1ResearchAgent: RFP 파싱")
    print(f"- Phase2AnalysisAgent: 분석")
    print(f"- Phase3StrategyAgent: 전략")
    print(f"- Phase4ImplementAgent: 섹션 생성")
    print(f"- Phase5QualityAgent: 품질 평가")
