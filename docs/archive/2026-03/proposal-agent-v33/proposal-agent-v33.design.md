# Design: 용역 제안서 자동 생성 에이전트 v3.3

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | proposal-agent-v33 |
| 작성일 | 2026-03-05 |
| 참조 Plan | proposal-agent-v311.plan.md |
| 목표 | 5-Phase 파이프라인에 실제 Claude API 연결, 서버 안정화 |

---

## 1. 아키텍처 개요

### 1.1 전체 흐름

```
클라이언트
    │
    ▼
POST /api/v3.1/proposals/generate
    │  (rfp_title, client_name, rfp_content)
    ▼
[SessionManager] — proposal_id 생성 & 상태 저장
    │
    ▼
POST /api/v3.1/proposals/{id}/execute
    │
    ├── Phase 1: Research  → RFP 파싱 + 이력 조회
    ├── Phase 2: Analysis  → Claude API (구조화 분석)
    ├── Phase 3: Plan      → Claude API (전략 수립) + HITL Gate #3
    ├── Phase 4: Implement → Claude API (섹션 생성, 병렬)
    └── Phase 5: Test      → Claude API (품질 검증) + HITL Gate #5
                │
                ▼
         DOCX + PPTX 파일 생성
                │
                ▼
GET /api/v3.1/proposals/{id}/result
```

### 1.2 컴포넌트 구조

```
app/
├── main.py                          # 진입점 (import 오류 수정 필요)
├── config.py                        # 설정 (기존 유지)
├── api/
│   ├── routes.py                    # 라우터 통합 (기존 유지)
│   └── routes_v31.py                # v3.1 API (Phase 실행 로직 추가)
├── services/
│   ├── phase_executor.py            # [신규] Phase 실행 엔진
│   ├── phase_prompts.py             # [신규] Phase별 프롬프트
│   ├── proposal_generator.py        # 기존 유지 (Phase 4에서 활용)
│   ├── rfp_parser.py                # 기존 유지 (Phase 1에서 활용)
│   ├── docx_builder.py              # 기존 유지 (Phase 5에서 활용)
│   ├── pptx_builder.py              # 기존 유지 (Phase 5에서 활용)
│   └── session_manager.py          # 기존 유지
├── models/
│   ├── schemas.py                   # 기존 유지
│   └── phase_schemas.py             # [신규] PhaseArtifact 스키마
└── utils/
    ├── supabase_client.py           # 기존 유지
    ├── claude_utils.py              # 기존 유지
    └── file_utils.py               # 기존 유지
```

---

## 2. main.py 안정화 설계

### 2.1 문제
현재 `main.py`가 존재하지 않는 모듈을 import:
```python
from graph import build_supervisor_graph        # 존재 X
from tools import create_default_registry       # 존재 X
from config.claude_optimizer import TokenUsageTracker  # 존재 X
```

### 2.2 해결 방향
`main.py`를 단순화하여 실제 존재하는 모듈만 import. 복잡한 LangGraph 의존성 제거.

```python
# 수정 후 main.py 구조
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router  # 실제 존재하는 라우터만

app = FastAPI(title="용역 제안서 자동 생성 에이전트", version="3.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
app.include_router(router, prefix="/api")
```

---

## 3. Phase 실행 엔진 설계 (신규: phase_executor.py)

### 3.1 PhaseArtifact 스키마

```python
# app/models/phase_schemas.py

class PhaseArtifact(BaseModel):
    """Phase 간 전달되는 압축 산출물 (토큰 최적화)"""
    phase_num: int                          # 1~5
    phase_name: str                         # research/analysis/plan/implement/test
    summary: str                            # 핵심 내용 요약 (3K 토큰 이하)
    structured_data: dict                   # 구조화 데이터
    token_count: int                        # 사용 토큰 수
    created_at: datetime

class Phase1Artifact(PhaseArtifact):
    """Phase 1 산출물: RFP 파싱 결과"""
    rfp_data: RFPData                       # 기존 RFPData 스키마 활용
    history_summary: str                    # Supabase 이력 요약

class Phase2Artifact(PhaseArtifact):
    """Phase 2 산출물: 분석 결과"""
    key_requirements: list[str]             # 핵심 요구사항
    evaluation_weights: dict                # 배점 구조
    hidden_intent: str                      # 숨은 의도 분석
    risk_factors: list[str]                 # 리스크 요인

class Phase3Artifact(PhaseArtifact):
    """Phase 3 산출물: 전략 계획"""
    win_strategy: str                       # 핵심 전략 메시지
    section_plan: list[dict]                # 섹션별 작성 계획
    page_allocation: dict                   # 섹션별 분량

class Phase4Artifact(PhaseArtifact):
    """Phase 4 산출물: 섹션 초안"""
    sections: dict[str, str]                # 섹션명 → 본문
    proposal_content: ProposalContent       # 기존 ProposalContent 활용

class Phase5Artifact(PhaseArtifact):
    """Phase 5 산출물: 최종 결과"""
    quality_score: float                    # 품질 점수 (0~100)
    docx_path: str
    pptx_path: str
    executive_summary: str
```

### 3.2 PhaseExecutor 클래스

```python
# app/services/phase_executor.py

class PhaseExecutor:
    """5-Phase 파이프라인 실행 엔진"""

    def __init__(self, proposal_id: str, session_manager, config):
        self.proposal_id = proposal_id
        self.session = session_manager
        self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self.model = config.claude_model

    async def execute_all(self, rfp_content: str, express_mode: bool = False) -> Phase5Artifact:
        """전체 Phase 순차 실행"""
        artifact1 = await self.phase1_research(rfp_content)
        artifact2 = await self.phase2_analysis(artifact1)
        artifact3 = await self.phase3_plan(artifact2)

        if not express_mode:
            # HITL Gate #3: 전략 확정 (사람 승인)
            await self._hitl_gate(3, artifact3)

        artifact4 = await self.phase4_implement(artifact3)
        artifact5 = await self.phase5_test(artifact4)

        if not express_mode:
            # HITL Gate #5: 최종 제출
            await self._hitl_gate(5, artifact5)

        return artifact5
```

### 3.3 Phase별 Claude API 호출 패턴

```python
# Phase 2 예시 (분석)
async def phase2_analysis(self, artifact1: Phase1Artifact) -> Phase2Artifact:
    self._update_status("phase_2_analysis")

    response = self.client.messages.create(
        model=self.model,
        max_tokens=4096,
        system=PHASE2_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": PHASE2_USER_PROMPT.format(
                rfp_summary=artifact1.summary,          # 원문 대신 요약 전달 (토큰 절약)
                key_data=artifact1.structured_data,
            )
        }],
    )

    result = self._parse_json(response.content[0].text)
    artifact2 = Phase2Artifact(
        phase_num=2,
        phase_name="analysis",
        summary=result["summary"],
        structured_data=result,
        token_count=response.usage.input_tokens + response.usage.output_tokens,
    )
    self._save_artifact(2, artifact2)
    return artifact2
```

---

## 4. Phase별 프롬프트 설계 (신규: phase_prompts.py)

### Phase 1 (Research) — Claude 미사용, 파싱만
```
입력: RFP 원문
처리: rfp_parser.py (기존 RFP_ANALYSIS_PROMPT 활용)
출력: Phase1Artifact (RFPData + 이력 요약)
```

### Phase 2 (Analysis) — Claude Sonnet
```
시스템: "RFP 전략 분석 전문가. 배점 구조와 숨은 의도를 파악한다."
입력: Phase1 요약 (3K 토큰 이하)
출력 JSON:
  - key_requirements: 핵심 요구사항 목록
  - evaluation_weights: 배점별 가중치
  - hidden_intent: 발주처 진짜 원하는 것
  - risk_factors: 주의할 리스크
최대 토큰: 4,096
```

### Phase 3 (Plan) — Claude Sonnet + Extended Thinking
```
시스템: "제안서 전략가. 승리하는 전략 메시지를 수립한다."
입력: Phase2 요약 (5K 토큰 이하)
출력 JSON:
  - win_strategy: 핵심 차별화 전략 (3문장)
  - section_plan: [{section, approach, page_limit}]
  - team_plan: 투입 인력 구성
최대 토큰: 8,192
extended_thinking: true (budgetTokens: 5,000)
```

### Phase 4 (Implement) — Claude Sonnet, 섹션별 순차 호출
```
시스템: "제안서 작성 전문가. 설득력 있는 제안서 본문을 작성한다."
입력: Phase3 섹션 계획 (한 섹션씩)
출력: ProposalContent 각 필드 채우기
      (기존 PROPOSAL_GENERATION_PROMPT 활용 + Phase3 전략 반영)
최대 토큰: 섹션당 2,048
```

### Phase 5 (Test) — Claude Haiku (품질 검증, 저비용)
```
시스템: "제안서 품질 심사관. 요구사항 충족률과 문체 일관성을 평가한다."
입력: Phase4 섹션 초안
출력 JSON:
  - quality_score: 0~100
  - issues: [심각도별 문제점]
  - fixed_sections: {섹션명: 수정본} (점수 80 미만시)
최대 토큰: 2,048
```

---

## 5. API 엔드포인트 수정 설계

### 5.1 routes_v31.py `/execute` 수정

```python
# 현재 (Mock)
for i, phase in enumerate(phase_names, start=1):
    state["current_phase"] = f"phase_{i}_{phase}"
session_manager.update_session(proposal_id, {"status": "completed"})

# 변경 후 (실제 실행)
executor = PhaseExecutor(proposal_id, session_manager, settings)
rfp_content = session["proposal_state"]["rfp_content"]
final_artifact = await executor.execute_all(rfp_content, auto_run)
session_manager.update_session(proposal_id, {
    "status": "completed",
    "phases_completed": 5,
    "quality_score": final_artifact.quality_score,
    "docx_path": final_artifact.docx_path,
    "pptx_path": final_artifact.pptx_path,
})
```

### 5.2 신규 엔드포인트: 문서 다운로드

```python
@router.get("/proposals/{proposal_id}/download/{file_type}")
async def download_document(proposal_id: str, file_type: Literal["docx", "pptx"]):
    """생성된 문서 다운로드"""
    session = session_manager.get_session(proposal_id)
    path = session.get(f"{file_type}_path")
    return FileResponse(path, filename=f"proposal_{proposal_id}.{file_type}")
```

---

## 6. 데이터 흐름 (토큰 예산)

```
Phase 1: RFP 원문 파싱 (Claude 미사용)
          → Artifact1: ~3K 토큰

Phase 2: Artifact1 요약 (3K) → Claude → Artifact2: ~5K 토큰
          컨텍스트 예산: ~15K 토큰 (200K의 7.5%)

Phase 3: Artifact2 요약 (5K) → Claude → Artifact3: ~8K 토큰
          컨텍스트 예산: ~20K 토큰 (200K의 10%)

Phase 4: Artifact3 계획 (8K) + 각 섹션 → Claude (섹션별)
          섹션당 컨텍스트: ~15K 토큰
          8개 섹션 × 15K = 총 120K (분산 처리)

Phase 5: Artifact4 초안 → Claude Haiku (저비용 검증)
          컨텍스트: ~30K 토큰
```

---

## 7. 구현 순서

```
[1] main.py 안정화
    → 불필요한 import 제거, 서버 기동 확인

[2] phase_schemas.py 작성
    → PhaseArtifact 5종 Pydantic 모델

[3] phase_prompts.py 작성
    → Phase 2~5 시스템/유저 프롬프트

[4] phase_executor.py 작성
    → PhaseExecutor 클래스 + Phase 1~5 메서드

[5] routes_v31.py /execute 수정
    → Mock → PhaseExecutor 실제 호출

[6] 다운로드 엔드포인트 추가

[7] 통합 테스트
    → 실제 RFP로 엔드-투-엔드 실행
```

---

## 8. 성공 기준 (Design 레벨)

| 항목 | 기준 |
|------|------|
| 서버 기동 | import 오류 0건 |
| Phase 1 | RFP 파싱 성공률 100% |
| Phase 2-3 | Claude API 호출 성공, JSON 파싱 성공 |
| Phase 4 | ProposalContent 8개 필드 모두 채워짐 |
| Phase 5 | quality_score 반환, DOCX+PPTX 파일 생성 |
| 토큰 | Phase당 60K 이하 유지 |

---

## 9. 다음 단계

```
현재 상태: Design 완료
다음 단계: /pdca do proposal-agent-v33
           (구현 시작 — main.py 수정부터)
```
