# prompt-admin v2.0 Design — 학습 기반 프롬프트 개선 시스템

> **Summary**: 프롬프트가 프로젝트를 거듭할수록 학습·개선되는 시스템. 데이터 기반 문제 진단 → AI 가설 → 시뮬레이션 → A/B 실험의 과학적 사이클을 하나의 워크플로로 통합.
>
> **Project**: 용역제안 Coworker
> **Version**: v2.0
> **Date**: 2026-03-25
> **Status**: Draft
> **Previous**: [prompt-admin v1.0](prompt-admin.design.md) — 카탈로그 + 편집 + 시뮬레이션

---

## 1. v1.0 문제점 분석 (사용자 관점)

### 1.1 근본 문제: "도구 나열" vs "목적 중심"

v1.0은 "프롬프트 목록 보기 / 편집하기 / 시뮬레이션 돌리기 / A/B 실험 관리"라는 **기능 나열** 구조.
사용자의 실제 목적인 **"제안서 품질을 높이기 위해 프롬프트를 개선한다"** 흐름이 UI에 없음.

### 1.2 구체적 문제

| # | 문제 | 영향 |
|---|------|------|
| P-1 | 개발자용 ID (`section.TECHNICAL`)만 표시 | 사용자가 "이것이 뭐하는 프롬프트인지" 모름 |
| P-2 | 수치 나열만 있고 해석 없음 | "수정율 62%가 좋은가 나쁜가?" 판단 불가 |
| P-3 | 편집→시뮬→실험이 3개 페이지로 파편화 | 워크플로 단절, 사용자가 다음 행동을 모름 |
| P-4 | 시간축 추이 없음 | 개선되고 있는지 알 수 없음 |
| P-5 | "왜 나쁜가" 분석 없음 | 수정율은 높지만 원인을 모르면 개선 불가 |
| P-6 | 수주/패찰과 연결 안됨 | "이긴 제안서"와 "진 제안서"의 차이를 모름 |

### 1.3 핵심 갭: 패턴 분석 레이어 부재

현재 데이터 흐름:
```
축적(✅) → 수치집계(✅) → 패턴분석(❌) → 가설(✅) → 시뮬(✅) → 실험(✅)
```
**2단계 패턴 분석**이 없어서 학습 사이클이 끊김.

---

## 2. Design Goals (v2.0)

1. **목적 중심 UI**: "개선 필요 프롬프트 TOP N"을 진입점으로, 문제파악→개선→검증 워크플로를 한 화면에서 안내
2. **자동 패턴 분석**: 사람 수정 패턴, 리뷰 피드백, 수주/패찰 차이를 자동 분류·요약
3. **학습 사이클 시각화**: 시간축 추이 차트로 프롬프트가 나아지고 있는지 확인
4. **맥락 제공**: 워크플로 맵에서 각 프롬프트가 어디에 사용되는지 시각화

---

## 3. Architecture

### 3.1 학습 사이클

```
[1. 데이터 축적] ← 자동 (기존 인프라)
    제안서 생성 → self_review 점수
    사람 수정 → human_edit_tracking (diff + action)
    리뷰 피드백 → feedbacks 테이블
    quality_warnings → Pre-Flight Check 결과
    수주/패찰 → proposal_results
              ↓
[2. 패턴 분석] ← 신규 서비스 (prompt_analyzer.py)
    수정 패턴 분류 (Claude 배치 분석)
    리뷰 피드백 키워드 추출
    수주/패찰 프롬프트 성능 비교
    시간축 추이 계산
              ↓
[3. 가설 생성] ← 기존 suggest_improvements() 강화
    패턴 분석 결과를 메타프롬프트에 주입
              ↓
[4. 시뮬레이션] ← 기존 prompt_simulator.py
              ↓
[5. A/B 실험] ← 기존 prompt_ab_experiments
              ↓
[6. 승격/롤백] ← 기존 promote/rollback API
              ↓
        [1로 돌아감]
```

### 3.2 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Next.js)                                          │
│  ┌──────────────┐  ┌─────────────────────┐  ┌────────────┐ │
│  │ /admin/      │  │ /admin/prompts/     │  │ /admin/    │ │
│  │ prompts      │  │ [id]/improve        │  │ prompts/   │ │
│  │ (학습 대시)  │  │ (개선 워크벤치)      │  │ catalog    │ │
│  └──────┬───────┘  └──────┬──────────────┘  └──────┬─────┘ │
│         │                 │                         │       │
│  ┌──────┴─────────────────┴─────────────────────────┴─────┐ │
│  │  api.prompts.* (기존 20 + 신규 4 메서드)               │ │
│  └────────────────────────┬───────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────┘
                            │ HTTP
┌───────────────────────────┼─────────────────────────────────┐
│  Backend (FastAPI)        │                                  │
│  ┌────────────────────────┴──────────────────────────────┐  │
│  │  routes_prompt_evolution.py (기존 25 + 신규 4 EP)      │  │
│  └──────┬──────────────┬────────────────┬────────────────┘  │
│         │              │                │                    │
│  ┌──────┴──────┐ ┌─────┴──────┐ ┌──────┴──────────┐       │
│  │ prompt_     │ │ prompt_    │ │ prompt_          │       │
│  │ analyzer    │ │ simulator  │ │ evolution        │       │
│  │ (신규)      │ │ (기존)     │ │ (기존+강화)      │       │
│  └─────────────┘ └────────────┘ └─────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Data Model

### 4.1 신규 테이블

#### prompt_analysis_snapshots — 주기적 패턴 분석 결과

```sql
CREATE TABLE IF NOT EXISTS prompt_analysis_snapshots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id       VARCHAR(100) NOT NULL,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    -- 수치 메트릭
    proposals_used  INTEGER DEFAULT 0,
    win_count       INTEGER DEFAULT 0,
    loss_count      INTEGER DEFAULT 0,
    win_rate        DECIMAL(5,2),
    avg_quality     DECIMAL(5,2),
    avg_edit_ratio  DECIMAL(5,4),
    edit_count      INTEGER DEFAULT 0,
    -- 패턴 분석 (AI 생성)
    edit_patterns   JSONB DEFAULT '[]',    -- [{pattern, count, examples}]
    feedback_summary JSONB DEFAULT '{}',   -- {keywords: [{word, count}], themes: [str]}
    win_loss_diff   JSONB DEFAULT '{}',    -- {win_avg_quality, loss_avg_quality, key_differences: [str]}
    hypothesis      TEXT,                  -- AI가 생성한 개선 가설
    -- 메타
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_pas_prompt ON prompt_analysis_snapshots(prompt_id, period_end DESC);
```

### 4.2 기존 테이블 활용 (변경 없음)

| 테이블 | 역할 | 이미 축적 중 |
|--------|------|:----------:|
| `prompt_artifact_link` | 프롬프트→제안서 연결 | ✅ |
| `human_edit_tracking` | 사람 수정 이력 (action, edit_ratio) | ✅ |
| `feedbacks` | 리뷰 게이트 피드백 텍스트 | ✅ |
| `proposal_results` | 수주/패찰 결과 | ✅ |
| `prompt_simulations` | 시뮬레이션 이력 (v1.0) | ✅ |
| `prompt_improvement_suggestions` | AI 제안 이력 (v1.0) | ✅ |
| `prompt_ab_experiments` | A/B 실험 (기존) | ✅ |

---

## 5. Backend Service — prompt_analyzer.py (신규)

```python
"""프롬프트 패턴 분석 엔진 — 학습 사이클 2단계."""

async def analyze_prompt(prompt_id: str, days: int = 90) -> dict:
    """프롬프트의 최근 N일 데이터를 분석하여 패턴 도출.

    Returns:
        {
            "metrics": {수치 메트릭},
            "edit_patterns": [{pattern, count, examples}],
            "feedback_summary": {keywords, themes},
            "win_loss_comparison": {win_avg, loss_avg, key_differences},
            "trend": [{period, quality, edit_ratio, win_rate}],
            "hypothesis": "AI 가설",
            "improvement_priority": "high|medium|low",
        }
    """

async def classify_edit_patterns(prompt_id: str, limit: int = 30) -> list[dict]:
    """human_edit_tracking의 수정 이력을 AI로 패턴 분류.

    기존 _get_frequent_edit_patterns()는 action(rewrite/refine)만 집계.
    이 함수는 수정 전/후 diff를 분석하여 "어떤 종류의 수정인가"를 분류.

    Returns:
        [
            {"pattern": "구체적 구현 방법 추가", "count": 12, "examples": ["..."]},
            {"pattern": "성능 수치 보강", "count": 8, "examples": ["..."]},
        ]
    """

async def compare_win_loss(prompt_id: str) -> dict:
    """수주/패찰 제안서에서 이 프롬프트의 성능 비교.

    Returns:
        {
            "win_avg_quality": 85.0,
            "loss_avg_quality": 68.0,
            "win_avg_evidence_count": 4.2,
            "loss_avg_evidence_count": 1.5,
            "key_differences": ["수주 시 표/다이어그램 밀도 3배 높음", ...]
        }
    """

async def compute_trend(prompt_id: str, months: int = 6) -> list[dict]:
    """월별 추이 데이터 계산.

    Returns:
        [
            {"period": "2026-01", "quality": 75.0, "edit_ratio": 0.62, "win_rate": 55.0, "version": 1},
            {"period": "2026-02", "quality": 79.0, "edit_ratio": 0.48, "win_rate": 60.0, "version": 1},
            {"period": "2026-03", "quality": 84.0, "edit_ratio": 0.35, "win_rate": 70.0, "version": 2},
        ]
    """

async def generate_improvement_priority(prompt_id: str) -> str:
    """개선 우선순위 판정.

    Rules:
    - HIGH: 수정율 > 50% AND (품질 < 75 OR 수주율 < 55%)
    - MEDIUM: 수정율 > 35% OR 품질 < 80
    - LOW: 기타
    """

async def run_batch_analysis(top_n: int = 10) -> list[dict]:
    """전체 프롬프트 중 개선 필요 TOP N 자동 선정 + 패턴 분석.
    주간 배치 또는 온디맨드 실행.
    """
```

---

## 6. API Specification (신규 4개)

### 6.1 `GET /api/prompts/learning-dashboard`

학습 대시보드 전체 데이터 (홈 화면용).

**Response:**
```json
{
    "overview": {
        "avg_win_rate": 67.0,
        "avg_quality": 81.0,
        "avg_edit_ratio": 0.38,
        "running_experiments": 2,
        "delta": {"win_rate": 3.0, "quality": 2.0, "edit_ratio": -0.05}
    },
    "top_needs_improvement": [
        {
            "prompt_id": "section_prompts.TECHNICAL",
            "label": "기술적 수행방안",
            "category": "proposal_writing",
            "priority": "high",
            "metrics": {"edit_ratio": 0.62, "quality": 75.0, "win_rate": 54.5},
            "top_pattern": {"pattern": "구체적 구현 방법 추가", "count": 12},
            "feedback_theme": "근거 부족"
        }
    ],
    "recent_learnings": [
        {
            "date": "2026-03-20",
            "prompt_id": "section_prompts.TECHNICAL",
            "event": "v1→v2 승격",
            "impact": "수정율 62% → 41%"
        }
    ],
    "trend": [
        {"period": "2026-01", "avg_quality": 75.0, "avg_edit_ratio": 0.45},
        {"period": "2026-02", "avg_quality": 78.0, "avg_edit_ratio": 0.40},
        {"period": "2026-03", "avg_quality": 81.0, "avg_edit_ratio": 0.38}
    ]
}
```

### 6.2 `GET /api/prompts/{prompt_id}/analysis`

개별 프롬프트 심층 분석 (개선 워크벤치용).

**Response:**
```json
{
    "prompt_id": "section_prompts.TECHNICAL",
    "label": "기술적 수행방안",
    "priority": "high",
    "metrics": {"edit_ratio": 0.62, "quality": 75.0, "win_rate": 54.5, "proposals_used": 11},
    "edit_patterns": [
        {"pattern": "구체적 구현 방법 추가", "count": 12, "pct": 66.7},
        {"pattern": "성능 수치 보강", "count": 8, "pct": 44.4},
        {"pattern": "기술 비교표 추가", "count": 5, "pct": 27.8}
    ],
    "feedback_summary": {
        "keywords": [{"word": "근거 부족", "count": 7}, {"word": "추상적", "count": 5}],
        "themes": ["구현 구체성 부족", "대안 기술 비교 없음"]
    },
    "win_loss_comparison": {
        "win_avg_quality": 85.0,
        "loss_avg_quality": 68.0,
        "key_differences": [
            "수주 시 근거 수 평균 4.2개 vs 패찰 시 1.5개",
            "수주 시 표/다이어그램 평균 1.8개 vs 패찰 시 0.3개"
        ]
    },
    "trend": [
        {"period": "2026-01", "quality": 73.0, "edit_ratio": 0.65, "version": 1},
        {"period": "2026-03", "quality": 75.0, "edit_ratio": 0.62, "version": 1}
    ],
    "hypothesis": "구현 방법 상세화 지시와 기술 비교표 의무화를 강화하면 수정율 40% 이하로 개선 가능"
}
```

### 6.3 `POST /api/prompts/{prompt_id}/run-analysis`

온디맨드 패턴 분석 실행 (분석 결과 갱신).

**Request:** `{"days": 90}`
**Response:** 6.2와 동일 구조 (새로 분석 후 snapshot 저장)

### 6.4 `GET /api/prompts/workflow-map`

워크플로 맵 데이터 (카탈로그용).

**Response:**
```json
{
    "nodes": [
        {"id": "rfp_search", "label": "공고 검색", "prompts": ["bid_review.PREPROCESSOR_SYSTEM", "bid_review.REVIEWER_SYSTEM"]},
        {"id": "strategy_generate", "label": "전략 수립", "prompts": ["strategy.GENERATE_PROMPT"]},
        {"id": "proposal_write", "label": "제안서 작성", "prompts": ["section_prompts.UNDERSTAND", "..."]}
    ],
    "edges": [
        {"from": "rfp_search", "to": "rfp_analyze"},
        {"from": "rfp_analyze", "to": "go_no_go"}
    ]
}
```

---

## 7. UI Design

### 7.1 페이지 구조 (3페이지)

```
/admin/prompts                    ← 학습 대시보드 (홈) — v1 카탈로그 교체
/admin/prompts/[id]/improve       ← 개선 워크벤치 (신규)
/admin/prompts/catalog            ← 카탈로그 (v1 이동, 보조 역할)
/admin/prompts/experiments        ← A/B 실험 (기존 유지)
```

### 7.2 학습 대시보드 (`/admin/prompts`)

```
┌─────────────────────────────────────────────────────────┐
│  프롬프트 학습 현황                       [카탈로그 →]   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ── 전체 건강 지표 ──                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ 평균 수주 │ │ 평균 품질 │ │ 평균 수정 │ │ 실험 중   │   │
│  │ 67%      │ │ 81점     │ │ 38%      │ │ 2건      │   │
│  │ +3% ↑    │ │ +2 ↑     │ │ -5% ↓   │ │          │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                           │
│  ── 개선 필요 TOP 3 ────────────────────────────────    │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 1. 기술적 수행방안                    우선순위: HIGH │
│  │    수정율 62% | 품질 75점 | 수주율 55%            │    │
│  │    패턴: "구체적 구현 방법 추가" 12건              │    │
│  │    → [개선 시작하기]                              │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ 2. 유지보수 (MAINTENANCE)              우선순위: MED │
│  │    수정율 55% | 품질 70점                          │    │
│  │    패턴: "SLA 수치 구체화" 6건                     │    │
│  │    → [개선 시작하기]                              │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ── 추이 차트 (최근 6개월) ──                            │
│  [수정율 추이] [품질 추이] [수주율 추이]                  │
│  (Recharts 라인차트: 월별 데이터 + 버전 변경 마커)        │
│                                                           │
│  ── 최근 학습 이력 ──                                    │
│  3/20 TECHNICAL v1→v2 승격 (수정율 62→41%)              │
│  3/15 METHODOLOGY 실험 완료 (B안 채택)                   │
└─────────────────────────────────────────────────────────┘
```

### 7.3 개선 워크벤치 (`/admin/prompts/[id]/improve`)

[개선 시작하기] 클릭 시 진입. **4스텝 워크플로**를 한 화면에서 순차 안내.

```
┌─────────────────────────────────────────────────────────┐
│  ← 대시보드    기술적 수행방안 프롬프트 개선              │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  [1.문제파악] → [2.개선안] → [3.시뮬레이션] → [4.실험]   │
│      ✅            🔄           ⏳             ⏳        │
│                                                           │
│  ═══ STEP 1: 문제 파악 ═══                               │
│                                                           │
│  ┌─ 핵심 수치 ─────────────────────────────────────┐    │
│  │ 수정율: 62% (HIGH) | 품질: 75점 | 수주율: 55%    │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─ 사람 수정 패턴 TOP 5 ──────────────────────────┐    │
│  │  1. 구체적 구현 방법 추가    ████████████  12건   │    │
│  │  2. 성능 수치 보강           ████████░░░   8건   │    │
│  │  3. 기술 비교표 추가         █████░░░░░░   5건   │    │
│  │  4. 아키텍처 다이어그램 추가 ███░░░░░░░░   3건   │    │
│  │  5. RFP 요구사항 매핑        ██░░░░░░░░░   2건   │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─ 수주 vs 패찰 비교 ────────────────────────────┐    │
│  │          수주 제안서    패찰 제안서    차이       │    │
│  │  품질:    85점          68점         +17점      │    │
│  │  근거 수: 4.2개         1.5개        +2.7개     │    │
│  │  표/도표: 1.8개         0.3개        +1.5개     │    │
│  │  → 핵심: 구체적 근거와 시각 자료 밀도           │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─ 리뷰 피드백 요약 ─────────────────────────────┐    │
│  │  "구현 방법이 너무 추상적" (3회)                  │    │
│  │  "대안 기술 비교가 없음" (2회)                    │    │
│  │  "성능 목표 수치가 없음" (2회)                    │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ═══ STEP 2: AI 개선안 ═══                               │
│                                                           │
│  ┌─ 가설 ──────────────────────────────────────────┐    │
│  │  "구현 방법 상세화 지시를 강화하면                 │    │
│  │   수정율이 62% → 40% 이하로 줄어들 것"           │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─ 개선안 3건 ────────────────────────────────────┐    │
│  │  A: 구현 상세화 + 성능 수치 필수화                │    │
│  │     [현재와 비교] [시뮬레이션 →]                  │    │
│  │  B: 기술 비교표 의무화 + 코드 예시 추가            │    │
│  │     [현재와 비교] [시뮬레이션 →]                  │    │
│  │  C: RFP 매핑 강화 + 아키텍처도 필수               │    │
│  │     [현재와 비교] [시뮬레이션 →]                  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ═══ STEP 3: 시뮬레이션 비교 ═══                         │
│                                                           │
│  (시뮬레이션 실행 후 결과 표시 — v1 SimulationRunner/     │
│   CompareView 컴포넌트 재활용)                            │
│                                                           │
│  ═══ STEP 4: A/B 실험 ═══                                │
│                                                           │
│  [이 개선안으로 A/B 실험 시작]                            │
│  (실험 진행 중이면 실시간 메트릭 표시)                     │
│  (실험 완료 시 [승격] [롤백] 버튼)                        │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 7.4 카탈로그 (`/admin/prompts/catalog`)

기존 v1 카탈로그를 이동. 워크플로 맵 추가.

```
┌─────────────────────────────────────────────────────────┐
│  ← 대시보드    프롬프트 카탈로그                          │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ── 워크플로 맵 ──                                       │
│  공고검색 → RFP분석 → Go/NoGo → 전략 → 계획 →          │
│  [A:9개]   [A:2개]  [A:3개]  [B:4개] [C:6개]           │
│                                                           │
│  → 제안서작성 → 자가진단 → 발표자료                      │
│    [D:15개]     [D:1개]   [E:8개]                        │
│                                                           │
│  (노드 클릭 → 해당 프롬프트 필터)                         │
│                                                           │
│  ── 카테고리 탭 + 테이블 (기존 v1 그대로) ──             │
│  [전체] [공고분석] [전략] [계획] [제안서] [발표] [품질]   │
│  ...                                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Frontend Components (신규/수정)

| # | Component | 유형 | 설명 |
|---|-----------|------|------|
| 1 | `LearningDashboard` | 신규 페이지 | 전체 건강 지표 + TOP N + 추이 차트 + 학습 이력 |
| 2 | `ImprovementWorkbench` | 신규 페이지 | 4스텝 워크플로 (문제파악→개선안→시뮬→실험) |
| 3 | `EditPatternChart` | 신규 컴포넌트 | 수정 패턴 수평 막대 차트 |
| 4 | `WinLossComparison` | 신규 컴포넌트 | 수주/패찰 비교 테이블 |
| 5 | `TrendChart` | 신규 컴포넌트 | 월별 추이 라인 차트 (Recharts) |
| 6 | `WorkflowMap` | 신규 컴포넌트 | 워크플로 노드 다이어그램 |
| 7 | `StepProgress` | 신규 컴포넌트 | 4스텝 진행 표시기 |
| 8 | `SimulationRunner` | 기존 재활용 | v1 컴포넌트 그대로 |
| 9 | `CompareView` | 기존 재활용 | v1 컴포넌트 그대로 |

---

## 9. Implementation Order

### Phase A: 백엔드 패턴 분석 (Day 1-2)

| # | 작업 | 파일 | 유형 |
|---|------|------|------|
| A-1 | DB 마이그레이션 | `database/migrations/013_prompt_analysis.sql` | 신규 |
| A-2 | prompt_analyzer.py | `app/services/prompt_analyzer.py` | 신규 |
| A-3 | API 4개 추가 | `app/api/routes_prompt_evolution.py` | 수정 |
| A-4 | api.ts 타입 + 메서드 추가 | `frontend/lib/api.ts` | 수정 |

### Phase B: 학습 대시보드 (Day 3-4)

| # | 작업 | 파일 | 유형 |
|---|------|------|------|
| B-1 | TrendChart 컴포넌트 | `frontend/components/prompt/TrendChart.tsx` | 신규 |
| B-2 | EditPatternChart 컴포넌트 | `frontend/components/prompt/EditPatternChart.tsx` | 신규 |
| B-3 | 학습 대시보드 페이지 | `frontend/app/(app)/admin/prompts/page.tsx` | 교체 |

### Phase C: 개선 워크벤치 (Day 5-6)

| # | 작업 | 파일 | 유형 |
|---|------|------|------|
| C-1 | WinLossComparison | `frontend/components/prompt/WinLossComparison.tsx` | 신규 |
| C-2 | StepProgress | `frontend/components/prompt/StepProgress.tsx` | 신규 |
| C-3 | 개선 워크벤치 페이지 | `frontend/app/(app)/admin/prompts/[promptId]/improve/page.tsx` | 신규 |

### Phase D: 카탈로그 이동 + 워크플로 맵 (Day 7)

| # | 작업 | 파일 | 유형 |
|---|------|------|------|
| D-1 | WorkflowMap 컴포넌트 | `frontend/components/prompt/WorkflowMap.tsx` | 신규 |
| D-2 | 카탈로그 페이지 이동 | `frontend/app/(app)/admin/prompts/catalog/page.tsx` | 이동 |
| D-3 | 통합 QA | 수동 | - |

---

## 10. File Summary

### 신규 파일 (8개)

| # | 파일 | 줄 (예상) |
|---|------|----------|
| 1 | `database/migrations/013_prompt_analysis.sql` | ~30 |
| 2 | `app/services/prompt_analyzer.py` | ~250 |
| 3 | `frontend/components/prompt/TrendChart.tsx` | ~80 |
| 4 | `frontend/components/prompt/EditPatternChart.tsx` | ~60 |
| 5 | `frontend/components/prompt/WinLossComparison.tsx` | ~80 |
| 6 | `frontend/components/prompt/StepProgress.tsx` | ~40 |
| 7 | `frontend/components/prompt/WorkflowMap.tsx` | ~100 |
| 8 | `frontend/app/(app)/admin/prompts/[promptId]/improve/page.tsx` | ~350 |

### 수정 파일 (4개)

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `app/api/routes_prompt_evolution.py` | +4 엔드포인트 (~80줄) |
| 2 | `frontend/lib/api.ts` | +4 타입 + 4 메서드 (~60줄) |
| 3 | `frontend/app/(app)/admin/prompts/page.tsx` | 학습 대시보드로 교체 (~300줄) |
| 4 | `frontend/app/(app)/admin/prompts/catalog/page.tsx` | 기존 카탈로그 이동 + WorkflowMap |

### 총계: ~1,430줄 신규 + ~440줄 수정 = **~1,870줄**

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-25 | 카테고리 관리 + 편집 + 시뮬레이션 |
| 2.0 | 2026-03-25 | 학습 기반 개선 — 패턴 분석 + 워크벤치 + 대시보드 재설계 |
