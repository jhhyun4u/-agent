# prompt-admin Design Document

> **Summary**: 프롬프트 카테고리 관리 + 인라인 편집 + 시뮬레이션 기반 개선 Admin UI
>
> **Project**: 용역제안 Coworker
> **Version**: v1.0
> **Date**: 2026-03-25
> **Status**: Draft
> **Planning Doc**: [prompt-admin.plan.md](../../01-plan/features/prompt-admin.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. 47개 프롬프트를 6개 카테고리로 분류하여 직관적으로 탐색
2. 코드 배포 없이 프롬프트를 편집하고 candidate로 안전하게 저장
3. 샘플/실제 데이터로 시뮬레이션하여 변경 효과를 사전 검증
4. 기존 백엔드 인프라(4 서비스 + 5 테이블 + 17 API) 최대 활용, 신규 코드 최소화

### 1.2 Design Principles

- **안전 우선**: active 프롬프트 직접 수정 불가, 항상 candidate → 시뮬레이션 → 승격 플로우
- **기존 인프라 재활용**: 신규 API 8개만 추가, DB 테이블 3개 신규 + 1개 확장
- **점진적 확장**: v1은 편집+시뮬레이션, v2에서 자동 A/B 실험 UI 강화

### 1.3 현재 구현 상태 (AS-IS)

| 계층 | 구현물 | 상태 |
|------|-------|------|
| DB | 5 테이블 (010_prompt_evolution.sql) | 완료 |
| 백엔드 서비스 | prompt_registry, prompt_tracker, prompt_evolution, human_edit_tracker | 완료 |
| API | 17개 엔드포인트 (routes_prompt_evolution.py) | 완료 |
| 프론트엔드 | 3 페이지 (대시보드, 상세, 실험) | **기본 구현** |
| 프론트엔드 API 클라이언트 | api.prompts.* (12개 메서드 + 10개 타입) | 완료 |

### 1.4 이번 설계 범위 (TO-BE)

| 구분 | 신규/개선 | 상세 |
|------|----------|------|
| DB | 신규 3 테이블 + 1 확장 | prompt_simulations, prompt_improvement_suggestions, simulation_token_usage + category 컬럼 |
| 백엔드 | 신규 2 서비스 + API 8개 | prompt_categories.py, prompt_simulator.py |
| 프론트 개선 | 기존 3 페이지 개선 | 카테고리 탭, 편집 기능, 시뮬레이션 통합 |
| 프론트 신규 | 2 페이지 + 5 컴포넌트 | 편집 페이지, 시뮬레이션 페이지 |

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js)                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────────┐  │
│  │ /admin/      │ │ /admin/      │ │ /admin/prompts/        │  │
│  │ prompts      │ │ prompts/[id] │ │ [id]/simulate          │  │
│  │ (카탈로그+   │ │ (상세+편집+  │ │ (시뮬레이션            │  │
│  │  대시보드)   │ │  AI제안)     │ │  샌드박스)             │  │
│  └──────┬───────┘ └──────┬───────┘ └──────────┬─────────────┘  │
│         │                │                     │                │
│  ┌──────┴────────────────┴─────────────────────┴─────────────┐  │
│  │  api.prompts.* (lib/api.ts) — 기존 12 + 신규 8 메서드    │  │
│  └───────────────────────────┬───────────────────────────────┘  │
└──────────────────────────────┼──────────────────────────────────┘
                               │ HTTP
┌──────────────────────────────┼──────────────────────────────────┐
│  Backend (FastAPI)           │                                   │
│  ┌───────────────────────────┴─────────────────────────────┐    │
│  │  routes_prompt_evolution.py — 기존 17 + 신규 8 엔드포인트│    │
│  └──────┬───────────────┬──────────────────┬───────────────┘    │
│         │               │                  │                    │
│  ┌──────┴──────┐ ┌──────┴──────┐ ┌────────┴───────────┐       │
│  │ prompt_     │ │ prompt_     │ │ prompt_             │       │
│  │ categories  │ │ simulator   │ │ evolution           │       │
│  │ (신규)      │ │ (신규)      │ │ (기존)              │       │
│  └─────────────┘ └──────┬──────┘ └─────────────────────┘       │
│                         │                                       │
│                  ┌──────┴──────┐                                │
│                  │ claude_     │                                 │
│                  │ client      │                                 │
│                  └──────┬──────┘                                │
│                         │ API                                   │
└─────────────────────────┼───────────────────────────────────────┘
                          │
                   ┌──────┴──────┐
                   │ Claude API  │
                   └─────────────┘
```

### 2.2 Data Flow

#### 프롬프트 편집 플로우

```
Admin UI (편집기)
  ↓ POST /api/prompts/{id}/create-candidate  [기존 API]
prompt_registry.register_candidate()
  ↓ status="candidate" 로 DB 저장
  ↓ (active 버전에 영향 없음)
Admin UI → [시뮬레이션 실행] 클릭
  ↓ POST /api/prompts/{id}/simulate  [신규 API]
prompt_simulator.run_simulation()
  ├── 1. 프롬프트 텍스트 + state 변수 조합
  ├── 2. Claude API 호출 (max_tokens 제한)
  ├── 3. (선택) 자가진단 품질 평가
  └── 4. 결과 + 메타데이터 반환 → prompt_simulations 테이블 저장
Admin UI → 결과 확인 → 만족 시:
  ↓ POST /api/prompts/experiments/create  [기존 API]
prompt_evolution.start_experiment()
  ↓ 실전 A/B 실험 시작
```

#### AI 개선 제안 플로우

```
Admin UI → [AI 개선 제안] 클릭
  ↓ POST /api/prompts/{id}/suggest-improvement  [기존 API]
prompt_evolution.suggest_improvements()
  ├── compute_effectiveness() → 성과 데이터
  ├── _get_frequent_edit_patterns() → 수정 패턴
  ├── _get_section_quality_patterns() → 품질 패턴
  ├── _get_review_feedback_for_prompt() → 리뷰 피드백
  └── Claude 메타프롬프트 → 3개 개선안
  ↓
Admin UI → 개선안 표시 + 각각에 [편집기 적용] [시뮬레이션] [후보 등록] 버튼
  ↓ POST /api/prompts/{id}/suggestions/{sid}/feedback  [신규 API]
prompt_improvement_suggestions 테이블 저장 (수용/거부 기록)
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| prompt_categories.py (신규) | prompt_registry.py | 카테고리 매핑 + PROMPT_SOURCES 참조 |
| prompt_simulator.py (신규) | claude_client.py, prompt_registry.py | AI 호출 + 프롬프트 조회 |
| 편집 페이지 (신규) | api.prompts.detail, createCandidate | 버전 조회 + 후보 저장 |
| 시뮬레이션 페이지 (신규) | prompt_simulator API | 시뮬레이션 실행 + 결과 표시 |

---

## 3. Data Model

### 3.1 신규 테이블

#### prompt_simulations — 시뮬레이션 이력

```sql
CREATE TABLE IF NOT EXISTS prompt_simulations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id       VARCHAR(100) NOT NULL,
    prompt_version  INTEGER,
    prompt_text     TEXT NOT NULL,
    data_source     VARCHAR(20) NOT NULL,     -- 'sample' | 'project' | 'custom'
    data_source_id  VARCHAR(200),
    input_variables JSONB DEFAULT '{}',
    output_text     TEXT,
    output_meta     JSONB DEFAULT '{}',       -- {tokens_in, tokens_out, duration_ms, model}
    quality_score   DECIMAL(5,2),
    quality_detail  JSONB,                    -- {compliance, strategy, quality, trustworthiness}
    compared_with   INTEGER,                  -- A/B 비교 시 상대 버전
    created_by      UUID,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_psim_prompt ON prompt_simulations(prompt_id);
CREATE INDEX idx_psim_created ON prompt_simulations(created_at DESC);
```

#### prompt_improvement_suggestions — AI 개선 제안 이력

```sql
CREATE TABLE IF NOT EXISTS prompt_improvement_suggestions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id       VARCHAR(100) NOT NULL,
    prompt_version  INTEGER NOT NULL,
    analysis        TEXT,
    suggestions     JSONB NOT NULL,           -- [{title, rationale, key_changes, prompt_text}]
    accepted_index  INTEGER,                  -- 수용된 제안 인덱스 (null=미수용)
    feedback        TEXT,
    created_by      UUID,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_pis_prompt ON prompt_improvement_suggestions(prompt_id);
```

#### simulation_token_usage — 일일 시뮬레이션 한도

```sql
CREATE TABLE IF NOT EXISTS simulation_token_usage (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    date            DATE DEFAULT CURRENT_DATE,
    simulations_count INTEGER DEFAULT 0,
    tokens_input    INTEGER DEFAULT 0,
    tokens_output   INTEGER DEFAULT 0,
    UNIQUE(user_id, date)
);
```

### 3.2 기존 테이블 확장

```sql
-- prompt_registry에 카테고리 컬럼 추가
ALTER TABLE prompt_registry ADD COLUMN IF NOT EXISTS category VARCHAR(30);
```

### 3.3 Entity Relationships

```
[prompt_registry] 1 ──── N [prompt_simulations]       (prompt_id)
[prompt_registry] 1 ──── N [prompt_improvement_suggestions] (prompt_id)
[prompt_registry] 1 ──── N [prompt_artifact_link]     (기존)
[prompt_registry] 1 ──── N [human_edit_tracking]      (기존)
[prompt_registry] 1 ──── N [prompt_ab_experiments]    (기존)
[auth.users]      1 ──── N [simulation_token_usage]   (user_id)
```

---

## 4. API Specification

### 4.1 신규 API (8개)

#### 4.1.1 `GET /api/prompts/categories`

카테고리별 프롬프트 목록 + 메타데이터 반환.

**Response (200):**
```json
{
  "categories": [
    {
      "id": "bid_analysis",
      "label": "공고 분석",
      "icon": "Search",
      "prompt_count": 9,
      "prompts": [
        {
          "prompt_id": "bid_review.PREPROCESSOR_SYSTEM",
          "label": "G2B 공고 전처리",
          "source_file": "app/prompts/bid_review.py",
          "const_name": "PREPROCESSOR_SYSTEM",
          "active_version": 1,
          "status": "active",
          "token_estimate": 800,
          "variables": ["bid_text"],
          "category": "bid_analysis",
          "node_usage": ["rfp_search"]
        }
      ]
    }
  ],
  "total_prompts": 47
}
```

#### 4.1.2 `GET /api/prompts/worst-performers?limit=5`

수정율 또는 품질 기준 워스트 N 프롬프트.

**Response (200):**
```json
{
  "worst_by_edit_ratio": [
    {
      "prompt_id": "section_prompts.TECHNICAL",
      "avg_edit_ratio": 0.62,
      "edit_count": 18,
      "avg_quality_score": 75.0,
      "category": "proposal_writing"
    }
  ],
  "worst_by_quality": [
    {
      "prompt_id": "section_prompts.MAINTENANCE",
      "avg_quality_score": 70.0,
      "avg_edit_ratio": 0.55,
      "edit_count": 12,
      "category": "proposal_writing"
    }
  ]
}
```

#### 4.1.3 `POST /api/prompts/{prompt_id}/simulate`

프롬프트 시뮬레이션 실행.

**Request:**
```json
{
  "prompt_text": "...(null이면 active 버전 사용)",
  "data_source": "sample",
  "data_source_id": "sample_mid_consulting",
  "custom_variables": null,
  "run_quality_check": true
}
```

**Response (200):**
```json
{
  "simulation_id": "uuid",
  "output_text": "...(AI 출력)",
  "tokens_input": 4200,
  "tokens_output": 1800,
  "duration_ms": 8500,
  "model": "claude-sonnet-4-5-20250929",
  "quality_score": 82.5,
  "quality_detail": {
    "compliance": 22,
    "strategy": 20,
    "quality": 21,
    "trustworthiness": 19.5
  },
  "variables_used": ["rfp_text", "strategy", "positioning_guide"],
  "variables_missing": [],
  "format_valid": true,
  "format_errors": [],
  "quota_remaining": 45
}
```

**Error:**
- `429 Too Many Requests`: 일일 시뮬레이션 한도 초과
- `400 Bad Request`: 유효하지 않은 data_source 또는 data_source_id

#### 4.1.4 `GET /api/prompts/{prompt_id}/simulations?limit=20`

시뮬레이션 이력 조회.

**Response (200):**
```json
{
  "simulations": [
    {
      "id": "uuid",
      "prompt_version": 2,
      "data_source": "sample",
      "data_source_id": "sample_mid_consulting",
      "quality_score": 82.5,
      "tokens_input": 4200,
      "tokens_output": 1800,
      "duration_ms": 8500,
      "compared_with": 1,
      "created_at": "2026-03-25T10:30:00Z"
    }
  ]
}
```

#### 4.1.5 `POST /api/prompts/{prompt_id}/simulate-compare`

A vs B 비교 시뮬레이션 (동일 입력, 두 프롬프트 버전).

**Request:**
```json
{
  "version_a": null,
  "text_a": null,
  "version_b": 3,
  "text_b": null,
  "data_source": "sample",
  "data_source_id": "sample_mid_consulting",
  "run_quality_check": true
}
```

**Response (200):**
```json
{
  "result_a": { "...SimulationResult" },
  "result_b": { "...SimulationResult" },
  "comparison": {
    "quality_diff": 5.5,
    "token_diff": -200,
    "duration_diff": -1200,
    "recommendation": "B가 품질 +5.5점, 토큰 -200 효율적"
  }
}
```

#### 4.1.6 `GET /api/prompts/{prompt_id}/suggestions`

AI 개선 제안 이력 조회.

**Response (200):**
```json
{
  "suggestions": [
    {
      "id": "uuid",
      "prompt_version": 1,
      "analysis": "현재 프롬프트 약점...",
      "suggestions": [{"title": "...", "rationale": "...", "key_changes": [], "prompt_text": "..."}],
      "accepted_index": 0,
      "feedback": "첫 번째 안 적용 후 품질 향상 확인",
      "created_at": "2026-03-20T14:00:00Z"
    }
  ]
}
```

#### 4.1.7 `POST /api/prompts/{prompt_id}/suggestions/{suggestion_id}/feedback`

AI 제안 수용/거부 피드백 기록.

**Request:**
```json
{
  "accepted_index": 0,
  "feedback": "첫 번째 안 채택, 두 번째는 토큰 과다"
}
```

**Response (200):**
```json
{ "updated": true }
```

#### 4.1.8 `GET /api/prompts/simulation-quota`

현재 사용자의 일일 시뮬레이션 잔여 한도.

**Response (200):**
```json
{
  "daily_limit": 50,
  "used_today": 5,
  "remaining": 45,
  "tokens_used_today": { "input": 21000, "output": 9000 }
}
```

### 4.2 기존 API (변경 없음, 재활용)

| # | 메서드 | 경로 | 용도 |
|---|--------|------|------|
| 1 | GET | `/api/prompts/dashboard` | 대시보드 집계 |
| 2 | GET | `/api/prompts/section-heatmap` | 섹션 히트맵 |
| 3 | GET | `/api/prompts/list` | 상태별 목록 |
| 4 | POST | `/api/prompts/edit-action` | 사람 수정 기록 |
| 5 | POST | `/api/prompts/experiments/create` | 실험 시작 |
| 6 | GET | `/api/prompts/experiments/list` | 실험 목록 |
| 7 | POST | `/api/prompts/experiments/{id}/evaluate` | 실험 평가 |
| 8 | POST | `/api/prompts/experiments/{id}/promote` | 승격 |
| 9 | POST | `/api/prompts/experiments/{id}/rollback` | 롤백 |
| 10 | GET | `/api/prompts/{id}/detail` | 상세 + 이력 |
| 11 | GET | `/api/prompts/{id}/effectiveness` | 성과 메트릭 |
| 12 | POST | `/api/prompts/{id}/suggest-improvement` | AI 개선 제안 |
| 13 | POST | `/api/prompts/{id}/create-candidate` | 후보 등록 |

---

## 5. Backend Services

### 5.1 prompt_categories.py (신규)

```python
"""프롬프트 카테고리 매핑 — 6개 카테고리 + 메타데이터."""

# 카테고리 정의
PROMPT_CATEGORIES: dict[str, dict] = {
    "bid_analysis": {
        "label": "공고 분석",
        "icon": "Search",
        "description": "G2B 공고 전처리, 적합도 평가, 통합 분석",
        "source_modules": ["app.prompts.bid_review"],
    },
    "strategy": {
        "label": "전략 수립",
        "icon": "Target",
        "description": "포지셔닝, SWOT, 경쟁 분석, Win Theme",
        "source_modules": ["app.prompts.strategy"],
    },
    "planning": {
        "label": "계획 수립",
        "icon": "Calendar",
        "description": "팀 구성, 일정, 스토리라인, 예산",
        "source_modules": ["app.prompts.plan"],
    },
    "proposal_writing": {
        "label": "제안서 작성",
        "icon": "FileText",
        "description": "10개 섹션 유형 + 케이스 A/B + 자가진단",
        "source_modules": ["app.prompts.section_prompts", "app.prompts.proposal_prompts"],
    },
    "presentation": {
        "label": "발표 자료",
        "icon": "Presentation",
        "description": "PPT 3단계 파이프라인 (TOC→비주얼→스토리보드)",
        "source_modules": ["app.prompts.ppt_pipeline"],
    },
    "quality_assurance": {
        "label": "품질 보증",
        "icon": "Shield",
        "description": "신뢰성 규칙, 출처 태그, 제출서류 추출",
        "source_modules": ["app.prompts.trustworthiness", "app.prompts.submission_docs"],
    },
}

# 프롬프트→카테고리 역매핑 (prompt_registry 동기화 시 사용)
PROMPT_TO_CATEGORY: dict[str, str] = {}  # sync_all_prompts에서 자동 생성

# 프롬프트→그래프 노드 매핑
PROMPT_NODE_USAGE: dict[str, list[str]] = {
    "bid_review.PREPROCESSOR_SYSTEM": ["rfp_search"],
    "bid_review.REVIEWER_SYSTEM": ["rfp_search"],
    "strategy.GENERATE_PROMPT": ["strategy_generate"],
    "plan.TEAM_PROMPT": ["plan_team"],
    "plan.STORY_PROMPT": ["plan_story"],
    "plan.PRICE_PROMPT": ["plan_price"],
    "section_prompts.UNDERSTAND": ["proposal_write_next"],
    "section_prompts.STRATEGY": ["proposal_write_next"],
    # ... (47개 전체 매핑)
    "proposal_prompts.SELF_REVIEW": ["self_review"],
    "ppt_pipeline.TOC_SYSTEM": ["ppt_toc"],
}


async def get_categories_with_prompts() -> dict:
    """카테고리별 프롬프트 목록 + DB 메타 조합."""
    from app.services.prompt_registry import PROMPT_SOURCES, _make_prompt_id, _estimate_tokens, _extract_variables
    import importlib

    categories = []
    total = 0

    for cat_id, cat_info in PROMPT_CATEGORIES.items():
        prompts = []
        for module_path in cat_info["source_modules"]:
            if module_path not in PROMPT_SOURCES:
                continue
            try:
                mod = importlib.import_module(module_path)
            except ImportError:
                continue

            for const_name in PROMPT_SOURCES[module_path]:
                text = getattr(mod, const_name, None)
                if not text or not isinstance(text, str):
                    continue

                prompt_id = _make_prompt_id(module_path, const_name)
                prompts.append({
                    "prompt_id": prompt_id,
                    "label": const_name.replace("_", " ").title(),
                    "source_file": module_path.replace(".", "/") + ".py",
                    "const_name": const_name,
                    "token_estimate": _estimate_tokens(text),
                    "variables": _extract_variables(text),
                    "category": cat_id,
                    "node_usage": PROMPT_NODE_USAGE.get(prompt_id, []),
                })

        total += len(prompts)
        categories.append({
            "id": cat_id,
            "label": cat_info["label"],
            "icon": cat_info["icon"],
            "description": cat_info["description"],
            "prompt_count": len(prompts),
            "prompts": prompts,
        })

    # DB에서 active 버전 + 상태 정보 병합
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        registry = await client.table("prompt_registry").select(
            "prompt_id, version, status"
        ).eq("status", "active").execute()

        version_map = {r["prompt_id"]: r["version"] for r in (registry.data or [])}
        for cat in categories:
            for p in cat["prompts"]:
                p["active_version"] = version_map.get(p["prompt_id"], 0)
                p["status"] = "active" if p["prompt_id"] in version_map else "unregistered"
    except Exception:
        pass

    return {"categories": categories, "total_prompts": total}


async def get_worst_performers(limit: int = 5) -> dict:
    """수정율/품질 기준 워스트 프롬프트."""
    from app.services.prompt_tracker import check_prompts_needing_attention

    attention = await check_prompts_needing_attention(edit_ratio_threshold=0.0, min_edits=1)

    # 수정율 기준 정렬
    worst_edit = sorted(attention, key=lambda x: x["avg_edit_ratio"], reverse=True)[:limit]

    # 품질 기준은 MV에서 조회
    worst_quality = []
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        result = await client.table("mv_prompt_effectiveness").select(
            "prompt_id, avg_quality_score, proposals_used"
        ).order("avg_quality_score").limit(limit).execute()
        worst_quality = result.data or []
    except Exception:
        pass

    return {
        "worst_by_edit_ratio": worst_edit,
        "worst_by_quality": worst_quality,
    }
```

### 5.2 prompt_simulator.py (신규)

```python
"""프롬프트 시뮬레이션 엔진 — 샌드박스 실행 + 품질 평가."""

import json
import logging
import time
from typing import Optional, Literal

from pydantic import BaseModel

logger = logging.getLogger(__name__)

DAILY_SIMULATION_LIMIT = 50
SIMULATION_MAX_TOKENS = 2000
QUALITY_CHECK_MAX_TOKENS = 500


class SimulationRequest(BaseModel):
    prompt_text: Optional[str] = None
    data_source: Literal["sample", "project", "custom"] = "sample"
    data_source_id: Optional[str] = None
    custom_variables: Optional[dict] = None
    run_quality_check: bool = True


class SimulationResult(BaseModel):
    simulation_id: Optional[str] = None
    output_text: str = ""
    tokens_input: int = 0
    tokens_output: int = 0
    duration_ms: int = 0
    model: str = ""
    quality_score: Optional[float] = None
    quality_detail: Optional[dict] = None
    variables_used: list[str] = []
    variables_missing: list[str] = []
    format_valid: bool = True
    format_errors: list[str] = []
    quota_remaining: int = 0


async def check_quota(user_id: str) -> tuple[bool, int]:
    """일일 한도 체크. Returns: (허용 여부, 잔여 횟수)."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()

        result = await client.table("simulation_token_usage").select(
            "simulations_count"
        ).eq("user_id", user_id).eq("date", "today()").limit(1).execute()

        used = result.data[0]["simulations_count"] if result.data else 0
        remaining = DAILY_SIMULATION_LIMIT - used
        return remaining > 0, max(0, remaining)
    except Exception:
        return True, DAILY_SIMULATION_LIMIT


async def run_simulation(
    prompt_id: str,
    req: SimulationRequest,
    user_id: str,
) -> SimulationResult:
    """시뮬레이션 메인 실행."""
    start = time.time()

    # 1. 프롬프트 텍스트 확보
    if req.prompt_text:
        prompt_text = req.prompt_text
        prompt_version = None
    else:
        from app.services.prompt_registry import get_active_prompt
        prompt_text, prompt_version, _ = await get_active_prompt(prompt_id)

    if not prompt_text:
        return SimulationResult(format_valid=False, format_errors=["프롬프트를 찾을 수 없습니다."])

    # 2. state 데이터 로드
    state_data = await _load_state_data(req.data_source, req.data_source_id, req.custom_variables)

    # 3. 변수 치환
    final_prompt, used, missing = _substitute_variables(prompt_text, state_data)

    # 4. Claude API 호출
    from app.services.claude_client import claude_generate
    output = await claude_generate(final_prompt, max_tokens=SIMULATION_MAX_TOKENS)
    output_text = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)

    duration_ms = int((time.time() - start) * 1000)

    # 5. 출력 형식 검증
    format_valid, format_errors = _validate_output_format(prompt_id, output_text)

    # 6. 품질 자가진단 (선택)
    quality_score = None
    quality_detail = None
    if req.run_quality_check:
        quality_score, quality_detail = await _run_quality_check(
            prompt_id, output_text, state_data
        )

    # 7. DB 저장 + 한도 업데이트
    sim_id = await _save_simulation(
        prompt_id, prompt_version, req, output_text,
        duration_ms, quality_score, quality_detail, user_id
    )
    await _update_quota(user_id, SIMULATION_MAX_TOKENS, len(output_text) // 2)

    _, remaining = await check_quota(user_id)

    return SimulationResult(
        simulation_id=sim_id,
        output_text=output_text,
        tokens_input=len(final_prompt) // 2,
        tokens_output=len(output_text) // 2,
        duration_ms=duration_ms,
        model="claude-sonnet-4-5-20250929",
        quality_score=quality_score,
        quality_detail=quality_detail,
        variables_used=used,
        variables_missing=missing,
        format_valid=format_valid,
        format_errors=format_errors,
        quota_remaining=remaining,
    )


async def run_comparison(
    prompt_id: str,
    version_a: Optional[int],
    text_a: Optional[str],
    version_b: Optional[int],
    text_b: Optional[str],
    data_source: str,
    data_source_id: Optional[str],
    run_quality_check: bool,
    user_id: str,
) -> dict:
    """A vs B 비교 시뮬레이션."""
    req_a = SimulationRequest(
        prompt_text=text_a, data_source=data_source,
        data_source_id=data_source_id, run_quality_check=run_quality_check
    )
    req_b = SimulationRequest(
        prompt_text=text_b, data_source=data_source,
        data_source_id=data_source_id, run_quality_check=run_quality_check
    )

    # version → text 변환
    if not text_a and version_a:
        from app.services.prompt_registry import get_active_prompt
        # version_a 조회 (TODO: get_prompt_by_version 추가)
        req_a.prompt_text = None  # active 사용
    if not text_b and version_b:
        req_b.prompt_text = None

    result_a = await run_simulation(prompt_id, req_a, user_id)
    result_b = await run_simulation(prompt_id, req_b, user_id)

    comparison = {
        "quality_diff": (result_b.quality_score or 0) - (result_a.quality_score or 0),
        "token_diff": result_b.tokens_output - result_a.tokens_output,
        "duration_diff": result_b.duration_ms - result_a.duration_ms,
    }

    # 요약 추천
    if comparison["quality_diff"] > 3:
        comparison["recommendation"] = f"B가 품질 +{comparison['quality_diff']:.1f}점 우수"
    elif comparison["quality_diff"] < -3:
        comparison["recommendation"] = f"A가 품질 +{abs(comparison['quality_diff']):.1f}점 우수"
    else:
        comparison["recommendation"] = "유의미한 차이 없음"

    return {
        "result_a": result_a.model_dump(),
        "result_b": result_b.model_dump(),
        "comparison": comparison,
    }


# ── Private helpers ──

async def _load_state_data(
    source: str, source_id: Optional[str], custom: Optional[dict]
) -> dict:
    """시뮬레이션용 state 데이터 로드."""
    if source == "custom" and custom:
        return custom

    if source == "sample":
        return _load_sample_data(source_id or "sample_mid_consulting")

    if source == "project" and source_id:
        return await _load_project_state(source_id)

    return _load_sample_data("sample_mid_consulting")


def _load_sample_data(sample_id: str) -> dict:
    """샘플 RFP 데이터 로드."""
    import os
    sample_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "sample_rfps", f"{sample_id}.json"
    )
    try:
        with open(sample_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"샘플 데이터 없음: {sample_path}, 기본값 사용")
        return _default_sample_state()


def _default_sample_state() -> dict:
    """기본 샘플 state (파일 없을 때 폴백)."""
    return {
        "rfp_text": "[샘플] 정보시스템 구축 용역 제안요청서. 사업 기간: 6개월, 예산: 3억원...",
        "rfp_analysis": {"project_name": "샘플 ISP", "budget": 300000000, "duration_months": 6},
        "go_no_go": {"verdict": "go", "confidence": 85},
        "strategy": {"win_theme": "고객 맞춤형 방법론", "positioning": "offensive"},
        "positioning_guide": "공격적 포지셔닝: 차별화된 기술력 강조",
        "prev_sections_context": "",
        "storyline_context": "",
    }


async def _load_project_state(project_id: str) -> dict:
    """기존 프로젝트의 LangGraph state 스냅샷 로드."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()

        result = await client.table("proposals").select(
            "title, rfp_text, rfp_analysis, strategy, plan"
        ).eq("id", project_id).limit(1).execute()

        if result.data:
            row = result.data[0]
            return {
                "rfp_text": row.get("rfp_text", ""),
                "rfp_analysis": row.get("rfp_analysis", {}),
                "strategy": row.get("strategy", {}),
                "positioning_guide": "",
                "prev_sections_context": "",
                "storyline_context": "",
            }
    except Exception as e:
        logger.warning(f"프로젝트 state 로드 실패: {e}")

    return _default_sample_state()


def _substitute_variables(prompt_text: str, state: dict) -> tuple[str, list[str], list[str]]:
    """프롬프트 텍스트의 {변수}를 state 데이터로 치환."""
    import re

    # {{ }} 이스케이프 보호
    escaped = re.sub(r"\{\{(.*?)\}\}", lambda m: f"__ESC__{m.group(1)}__ESC__", prompt_text)

    variables = re.findall(r"\{(\w+)\}", escaped)
    used = []
    missing = []

    result = escaped
    for var in set(variables):
        value = state.get(var)
        if value is not None:
            replacement = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
            result = result.replace(f"{{{var}}}", replacement)
            used.append(var)
        else:
            missing.append(var)
            result = result.replace(f"{{{var}}}", f"[미입력: {var}]")

    # 이스케이프 복원
    result = result.replace("__ESC__", "{").replace("__ESC__", "}")

    return result, sorted(set(used)), sorted(set(missing))


def _validate_output_format(prompt_id: str, output: str) -> tuple[bool, list[str]]:
    """출력 형식 기본 검증."""
    errors = []

    # JSON 출력 기대 프롬프트 검사
    json_prompts = {"strategy.GENERATE_PROMPT", "plan.TEAM_PROMPT", "plan.ASSIGN_PROMPT",
                    "plan.SCHEDULE_PROMPT", "plan.STORY_PROMPT", "plan.PRICE_PROMPT",
                    "proposal_prompts.SELF_REVIEW"}

    if prompt_id in json_prompts:
        try:
            json.loads(output)
        except json.JSONDecodeError:
            errors.append("JSON 형식이 아닙니다.")

    # 최소 길이 검사
    if len(output.strip()) < 50:
        errors.append("출력이 너무 짧습니다 (50자 미만).")

    return len(errors) == 0, errors


async def _run_quality_check(prompt_id: str, output: str, state: dict) -> tuple[Optional[float], Optional[dict]]:
    """간소화된 자가진단 (4축 평가)."""
    meta_prompt = f"""다음 AI 생성 결과물을 4개 축으로 평가하세요 (각 25점, 총 100점).

## 평가 대상
{output[:2000]}

## 원본 RFP 요약
{json.dumps(state.get("rfp_analysis", {}), ensure_ascii=False)[:500]}

## 평가 축
1. 적합성 (25점): RFP 요구사항 반영 정도
2. 전략 정합성 (25점): 전략/Win Theme과의 일관성
3. 품질 (25점): 구조, 깊이, 구체성
4. 신뢰성 (25점): 근거 제시, 과장 표현 없음

## 출력 (JSON만)
{{"compliance": N, "strategy": N, "quality": N, "trustworthiness": N, "total": N}}"""

    try:
        from app.services.claude_client import claude_generate
        result = await claude_generate(meta_prompt, max_tokens=QUALITY_CHECK_MAX_TOKENS)

        if isinstance(result, dict):
            total = result.get("total", sum(result.get(k, 0) for k in ["compliance", "strategy", "quality", "trustworthiness"]))
            return total, result
        return None, None
    except Exception as e:
        logger.debug(f"품질 평가 실패: {e}")
        return None, None


async def _save_simulation(
    prompt_id, prompt_version, req, output_text,
    duration_ms, quality_score, quality_detail, user_id
) -> Optional[str]:
    """시뮬레이션 결과 DB 저장."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()

        result = await client.table("prompt_simulations").insert({
            "prompt_id": prompt_id,
            "prompt_version": prompt_version,
            "prompt_text": req.prompt_text or "(active 버전)",
            "data_source": req.data_source,
            "data_source_id": req.data_source_id,
            "input_variables": req.custom_variables or {},
            "output_text": output_text,
            "output_meta": {"duration_ms": duration_ms, "model": "claude-sonnet-4-5-20250929"},
            "quality_score": quality_score,
            "quality_detail": quality_detail,
            "created_by": user_id,
        }).execute()

        return result.data[0]["id"] if result.data else None
    except Exception as e:
        logger.warning(f"시뮬레이션 저장 실패: {e}")
        return None


async def _update_quota(user_id: str, tokens_in: int, tokens_out: int):
    """일일 한도 업데이트 (upsert)."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()

        await client.rpc("upsert_simulation_quota", {
            "p_user_id": user_id,
            "p_tokens_in": tokens_in,
            "p_tokens_out": tokens_out,
        }).execute()
    except Exception as e:
        logger.debug(f"한도 업데이트 실패: {e}")
```

---

## 6. UI/UX Design

### 6.1 페이지 구조

```
/admin/prompts                         ← 기존 개선: 카테고리 탭 추가
/admin/prompts/[promptId]              ← 기존 개선: 편집 패널 + 시뮬레이션 연결
/admin/prompts/[promptId]/simulate     ← 신규: 시뮬레이션 샌드박스
/admin/prompts/experiments             ← 기존 유지
```

### 6.2 /admin/prompts 카탈로그 (기존 개선)

```
┌─────────────────────────────────────────────────────────────┐
│  ← 관리자          프롬프트 관리 대시보드       [A/B 실험]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [전체 47] [공고분석 9] [전략 4] [계획 6] [제안서 15]       │
│  [발표자료 8] [품질보증 5]                                   │
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 전체     │ │ 실험중   │ │ 주의필요 │ │ 성과데이터│       │
│  │   47     │ │   2      │ │   3      │ │   25     │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                             │
│  ┌──────────────────────────────────── 주의 필요 ──────┐    │
│  │ section_prompts.TECHNICAL  수정율: 62.0%  [상세 →]  │    │
│  │ section_prompts.MAINTENANCE 수정율: 55.0% [상세 →]  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌──────────────────────── 프롬프트 목록 ──────────────┐    │
│  │ ID          │ 카테고리 │ 버전 │ 사용 │ 승률 │ 수정율│    │
│  │ bid_review. │ 공고분석 │ v1   │  8   │ 63%  │ 25%  │    │
│  │ PREPROCESSOR│          │      │      │      │      │    │
│  │ strategy.   │ 전략수립 │ v2   │  12  │ 67%  │ 35%  │    │
│  │ GENERATE    │          │      │      │      │      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌──────────────────── 섹션 히트맵 ───────────────────┐    │
│  │ ██ UNDERSTAND  ██ STRATEGY  ░░ TECHNICAL           │    │
│  │ ██ METHODOLOGY ██ PERSONNEL ░░ MAINTENANCE         │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 /admin/prompts/[promptId] 상세+편집 (기존 개선)

```
┌─────────────────────────────────────────────────────────────┐
│  ← 프롬프트 목록    section_prompts.UNDERSTAND              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐             │
│  │사용12│ │승률67%│ │품질82│ │수정25%│ │토큰   │             │
│  │      │ │      │ │      │ │      │ │4200/  │             │
│  │      │ │      │ │      │ │      │ │1800   │             │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘             │
│                                                             │
│  [이력 탭] [편집 탭] [AI 제안 탭]                           │
│                                                             │
│  ═══ 편집 탭 ═══                                            │
│  ┌───────────────────────┬────────────────────────────┐    │
│  │  에디터               │  미리보기                    │    │
│  │                       │                             │    │
│  │  당신은 평가위원의    │  변수 슬롯:                  │    │
│  │  관점에서 ...         │  {rfp_text}: [샘플 로드 ▾]  │    │
│  │  {rfp_text}를         │  {strategy}: [JSON 편집]     │    │
│  │  분석하여 ...         │  {positioning_guide}: ...    │    │
│  │                       │                             │    │
│  │  ── 토큰: ~2,100 ──  │  ── 렌더링된 프롬프트 ──    │    │
│  └───────────────────────┴────────────────────────────┘    │
│                                                             │
│  변경 사유: [필수 입력란_____________________]               │
│  [후보 저장 (candidate)] [시뮬레이션 →] [버전 비교]         │
└─────────────────────────────────────────────────────────────┘
```

### 6.4 /admin/prompts/[promptId]/simulate 시뮬레이션 (신규)

```
┌─────────────────────────────────────────────────────────────┐
│  ← section_prompts.UNDERSTAND    시뮬레이션 샌드박스         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ── 입력 설정 ──                                            │
│  데이터 소스: (●) 샘플 RFP  ( ) 기존 프로젝트  ( ) 커스텀   │
│  샘플 선택:  [중규모 컨설팅 (3억, ISP) ▾]                   │
│  프롬프트:   (●) 편집 중 텍스트  ( ) Active v1              │
│  품질 평가:  [✓] 자가진단 포함                              │
│  비교 모드:  [ ] A vs B 비교                                │
│                                                             │
│  [▶ 시뮬레이션 실행]        잔여: 45/50회                   │
│                                                             │
│  ── 결과 ──                                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  AI 출력 (1,800 토큰, 8.5초)                        │    │
│  │                                                     │    │
│  │  ## 1. 사업 환경 및 현황 분석                       │    │
│  │  ### 1.1 AS-IS 현황                                 │    │
│  │  발주기관은 현재 노후화된 정보시스템으로 인해 ...    │    │
│  │  ...                                                │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ── 품질 평가 ──                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │적합성    │ │전략정합성│ │품질      │ │신뢰성    │       │
│  │  22/25   │ │  20/25   │ │  21/25   │ │  19/25   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  총점: 82.0/100   변수: 5/5 사용, 0 누락   형식: ✓ 정상    │
│                                                             │
│  [후보 등록] [A/B 실험 시작] [이력 보기]                    │
└─────────────────────────────────────────────────────────────┘
```

### 6.5 A vs B 비교 모드

```
┌─────────────────────────────────────────────────────────────┐
│  ── A vs B 비교 결과 ──                                     │
│                                                             │
│  ┌──────────────────────┬──────────────────────┐            │
│  │  A: Active v1        │  B: Candidate v2     │            │
│  │  품질: 77.5          │  품질: 83.0 (+5.5)   │            │
│  │  토큰: 1,800         │  토큰: 1,600 (-200)  │            │
│  │  시간: 8.5s          │  시간: 7.3s (-1.2s)  │            │
│  ├──────────────────────┼──────────────────────┤            │
│  │  ## 1. 사업 환경     │  ## 1. 사업 환경     │            │
│  │  ...기존 내용...     │  ...개선 내용...     │            │
│  │                      │  + 추가된 분석       │            │
│  │                      │  + 근거 강화         │            │
│  └──────────────────────┴──────────────────────┘            │
│                                                             │
│  추천: B가 품질 +5.5점, 토큰 -200 효율적                    │
│  [B를 후보 등록] [B로 A/B 실험 시작]                        │
└─────────────────────────────────────────────────────────────┘
```

### 6.6 Component List

| # | Component | Location | Responsibility |
|---|-----------|----------|----------------|
| 1 | `CategoryTabs` | `components/prompt/CategoryTabs.tsx` | 6개 카테고리 필터 탭 |
| 2 | `PromptEditor` | `components/prompt/PromptEditor.tsx` | textarea 편집기 + 변수 하이라이트 + 토큰 카운터 |
| 3 | `PreviewPanel` | `components/prompt/PreviewPanel.tsx` | 변수 슬롯 + 렌더링 미리보기 |
| 4 | `SimulationRunner` | `components/prompt/SimulationRunner.tsx` | 시뮬레이션 실행 UI + 결과 표시 + 품질 점수 |
| 5 | `CompareView` | `components/prompt/CompareView.tsx` | A vs B 나란히 비교 + diff 하이라이트 |

---

## 7. Error Handling

### 7.1 Error Codes

| Code | Message | Cause | Handling |
|------|---------|-------|----------|
| 400 | `INVALID_DATA_SOURCE` | 유효하지 않은 시뮬레이션 소스 | data_source 값 검증 |
| 403 | `ADMIN_REQUIRED` | admin 역할이 아닌 사용자 | require_role("admin") |
| 404 | `PROMPT_NOT_FOUND` | 존재하지 않는 prompt_id | Python 상수 + DB 양쪽 확인 |
| 429 | `SIMULATION_QUOTA_EXCEEDED` | 일일 한도 초과 | 잔여 횟수 표시, 다음 날 재시도 안내 |
| 500 | `SIMULATION_FAILED` | Claude API 호출 실패 | 재시도 안내, 에러 로그 |

### 7.2 Error Response Format

```json
{
  "detail": {
    "code": "SIMULATION_QUOTA_EXCEEDED",
    "message": "일일 시뮬레이션 한도(50회)를 초과했습니다.",
    "remaining": 0,
    "reset_at": "2026-03-26T00:00:00+09:00"
  }
}
```

---

## 8. Security Considerations

- [x] admin 역할만 프롬프트 편집/시뮬레이션 가능 (`require_role("admin")`)
- [x] active 프롬프트 직접 수정 불가 (항상 candidate → 승격 플로우)
- [x] 시뮬레이션 일일 한도 (50회/admin) — API 비용 제어
- [x] 모든 변경 audit_log 기록 (created_by + created_at)
- [x] 프롬프트 삭제 불가, retired 마킹만 허용

---

## 9. Sample RFP Data

### 9.1 data/sample_rfps/ 디렉토리 구조

```
data/
└── sample_rfps/
    ├── sample_small_si.json        # 소규모 SI (5천만)
    ├── sample_mid_consulting.json  # 중규모 컨설팅 (3억)
    └── sample_large_isp.json       # 대규모 ISP (15억)
```

### 9.2 샘플 데이터 스키마

각 파일은 `ProposalState`의 주요 필드를 포함:

```json
{
  "rfp_text": "...(RFP 원문 요약, 2000자 이내)",
  "rfp_analysis": {
    "project_name": "정보시스템 구축",
    "budget": 300000000,
    "duration_months": 6,
    "eval_method": "기술+가격 분리평가",
    "eval_weights": {"기술": 90, "가격": 10},
    "key_requirements": ["요구사항1", "요구사항2"],
    "compliance_items": ["항목1", "항목2"]
  },
  "go_no_go": {
    "verdict": "go",
    "confidence": 85,
    "positioning": "offensive"
  },
  "strategy": {
    "win_theme": "고객 맞춤형 방법론과 검증된 수행 역량",
    "ghost_theme": "경쟁사 표준화 접근법의 한계",
    "positioning": "offensive",
    "differentiation": ["차별점1", "차별점2"]
  },
  "positioning_guide": "공격적 포지셔닝: 차별화된 기술력과 도메인 전문성 강조",
  "plan": {
    "team": {"roles": [...]},
    "schedule": {"phases": [...]},
    "budget": {"total": 300000000}
  },
  "dynamic_sections": [
    {"id": "sec-1", "title": "사업 이해 및 환경 분석", "type": "understand"},
    {"id": "sec-2", "title": "추진 전략", "type": "strategy"}
  ],
  "storylines": {
    "sections": [
      {
        "section_id": "sec-1",
        "key_message": "발주기관 환경에 대한 깊은 이해",
        "narrative_arc": "현황→문제→비전",
        "supporting_points": ["포인트1"],
        "win_theme_connection": "고객 맞춤형"
      }
    ]
  },
  "prev_sections_context": "",
  "storyline_context": ""
}
```

---

## 10. DB Migration SQL

```sql
-- 012_prompt_admin.sql
-- 프롬프트 Admin 기능 — 시뮬레이션 + AI 제안 이력 + 카테고리

-- ═══ 1. prompt_registry 카테고리 확장 ═══
ALTER TABLE prompt_registry ADD COLUMN IF NOT EXISTS category VARCHAR(30);

UPDATE prompt_registry SET category = 'bid_analysis' WHERE prompt_id LIKE 'bid_review.%';
UPDATE prompt_registry SET category = 'strategy' WHERE prompt_id LIKE 'strategy.%';
UPDATE prompt_registry SET category = 'planning' WHERE prompt_id LIKE 'plan.%';
UPDATE prompt_registry SET category = 'proposal_writing'
  WHERE prompt_id LIKE 'section_prompts.%'
     OR prompt_id LIKE 'proposal_prompts.%';
UPDATE prompt_registry SET category = 'presentation'
  WHERE prompt_id LIKE 'ppt_pipeline.%';
UPDATE prompt_registry SET category = 'quality_assurance'
  WHERE prompt_id LIKE 'trustworthiness.%'
     OR prompt_id LIKE 'submission_docs.%';

CREATE INDEX IF NOT EXISTS idx_pr_category ON prompt_registry(category);

-- ═══ 2. 시뮬레이션 이력 ═══
CREATE TABLE IF NOT EXISTS prompt_simulations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id       VARCHAR(100) NOT NULL,
    prompt_version  INTEGER,
    prompt_text     TEXT NOT NULL,
    data_source     VARCHAR(20) NOT NULL CHECK (data_source IN ('sample', 'project', 'custom')),
    data_source_id  VARCHAR(200),
    input_variables JSONB DEFAULT '{}',
    output_text     TEXT,
    output_meta     JSONB DEFAULT '{}',
    quality_score   DECIMAL(5,2),
    quality_detail  JSONB,
    compared_with   INTEGER,
    created_by      UUID,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_psim_prompt ON prompt_simulations(prompt_id);
CREATE INDEX IF NOT EXISTS idx_psim_created ON prompt_simulations(created_at DESC);

-- ═══ 3. AI 개선 제안 이력 ═══
CREATE TABLE IF NOT EXISTS prompt_improvement_suggestions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id       VARCHAR(100) NOT NULL,
    prompt_version  INTEGER NOT NULL,
    analysis        TEXT,
    suggestions     JSONB NOT NULL,
    accepted_index  INTEGER,
    feedback        TEXT,
    created_by      UUID,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pis_prompt ON prompt_improvement_suggestions(prompt_id);

-- ═══ 4. 시뮬레이션 토큰 한도 ═══
CREATE TABLE IF NOT EXISTS simulation_token_usage (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    date            DATE DEFAULT CURRENT_DATE,
    simulations_count INTEGER DEFAULT 0,
    tokens_input    INTEGER DEFAULT 0,
    tokens_output   INTEGER DEFAULT 0,
    UNIQUE(user_id, date)
);

-- upsert 함수
CREATE OR REPLACE FUNCTION upsert_simulation_quota(
    p_user_id UUID,
    p_tokens_in INTEGER,
    p_tokens_out INTEGER
) RETURNS VOID AS $$
BEGIN
    INSERT INTO simulation_token_usage (user_id, simulations_count, tokens_input, tokens_output)
    VALUES (p_user_id, 1, p_tokens_in, p_tokens_out)
    ON CONFLICT (user_id, date)
    DO UPDATE SET
        simulations_count = simulation_token_usage.simulations_count + 1,
        tokens_input = simulation_token_usage.tokens_input + p_tokens_in,
        tokens_output = simulation_token_usage.tokens_output + p_tokens_out;
END;
$$ LANGUAGE plpgsql;
```

---

## 11. Frontend API Client Extensions

`frontend/lib/api.ts`에 추가할 타입과 메서드:

### 11.1 신규 타입

```typescript
// ── 프롬프트 Admin 신규 타입 ──

export interface PromptCategory {
  id: string;
  label: string;
  icon: string;
  description: string;
  prompt_count: number;
  prompts: PromptCategoryItem[];
}

export interface PromptCategoryItem {
  prompt_id: string;
  label: string;
  source_file: string;
  const_name: string;
  active_version: number;
  status: string;
  token_estimate: number;
  variables: string[];
  category: string;
  node_usage: string[];
}

export interface SimulationRequest {
  prompt_text?: string;
  data_source: "sample" | "project" | "custom";
  data_source_id?: string;
  custom_variables?: Record<string, unknown>;
  run_quality_check?: boolean;
}

export interface SimulationResult {
  simulation_id: string;
  output_text: string;
  tokens_input: number;
  tokens_output: number;
  duration_ms: number;
  model: string;
  quality_score: number | null;
  quality_detail: { compliance: number; strategy: number; quality: number; trustworthiness: number } | null;
  variables_used: string[];
  variables_missing: string[];
  format_valid: boolean;
  format_errors: string[];
  quota_remaining: number;
}

export interface CompareResult {
  result_a: SimulationResult;
  result_b: SimulationResult;
  comparison: {
    quality_diff: number;
    token_diff: number;
    duration_diff: number;
    recommendation: string;
  };
}

export interface SimulationQuota {
  daily_limit: number;
  used_today: number;
  remaining: number;
  tokens_used_today: { input: number; output: number };
}

export interface SuggestionHistory {
  id: string;
  prompt_version: number;
  analysis: string;
  suggestions: PromptSuggestion["suggestions"];
  accepted_index: number | null;
  feedback: string | null;
  created_at: string;
}
```

### 11.2 신규 API 메서드

```typescript
// api.prompts 객체에 추가
{
  // 기존 12개 유지 + 신규 8개
  categories() {
    return request<{ categories: PromptCategory[]; total_prompts: number }>("GET", "/prompts/categories");
  },
  worstPerformers(limit = 5) {
    return request<{ worst_by_edit_ratio: any[]; worst_by_quality: any[] }>(
      "GET", `/prompts/worst-performers?limit=${limit}`
    );
  },
  simulate(promptId: string, body: SimulationRequest) {
    return request<SimulationResult>(
      "POST", `/prompts/${encodeURIComponent(promptId)}/simulate`, body
    );
  },
  simulations(promptId: string, limit = 20) {
    return request<{ simulations: SimulationResult[] }>(
      "GET", `/prompts/${encodeURIComponent(promptId)}/simulations?limit=${limit}`
    );
  },
  simulateCompare(promptId: string, body: any) {
    return request<CompareResult>(
      "POST", `/prompts/${encodeURIComponent(promptId)}/simulate-compare`, body
    );
  },
  suggestionHistory(promptId: string) {
    return request<{ suggestions: SuggestionHistory[] }>(
      "GET", `/prompts/${encodeURIComponent(promptId)}/suggestions`
    );
  },
  suggestionFeedback(promptId: string, suggestionId: string, body: { accepted_index: number | null; feedback: string }) {
    return request<{ updated: boolean }>(
      "POST", `/prompts/${encodeURIComponent(promptId)}/suggestions/${suggestionId}/feedback`, body
    );
  },
  simulationQuota() {
    return request<SimulationQuota>("GET", "/prompts/simulation-quota");
  },
}
```

---

## 12. Implementation Order

### Phase A: DB + 카테고리 서비스 + 카탈로그 개선 (Day 1-2)

| # | 작업 | 파일 | 유형 |
|---|------|------|------|
| A-1 | DB 마이그레이션 실행 | `database/migrations/012_prompt_admin.sql` | 신규 |
| A-2 | prompt_categories.py 구현 | `app/services/prompt_categories.py` | 신규 |
| A-3 | API 2개 추가 (categories, worst-performers) | `app/api/routes_prompt_evolution.py` | 수정 |
| A-4 | 프론트: CategoryTabs 컴포넌트 | `frontend/components/prompt/CategoryTabs.tsx` | 신규 |
| A-5 | 프론트: 카탈로그 페이지 개선 (카테고리 탭 + 카테고리 컬럼) | `frontend/app/(app)/admin/prompts/page.tsx` | 수정 |
| A-6 | 프론트: api.ts 타입 + 메서드 추가 | `frontend/lib/api.ts` | 수정 |

### Phase B: 편집기 + AI 제안 개선 (Day 3-4)

| # | 작업 | 파일 | 유형 |
|---|------|------|------|
| B-1 | PromptEditor 컴포넌트 (변수 하이라이트 + 토큰 카운터) | `frontend/components/prompt/PromptEditor.tsx` | 신규 |
| B-2 | PreviewPanel 컴포넌트 (변수 치환 미리보기) | `frontend/components/prompt/PreviewPanel.tsx` | 신규 |
| B-3 | 상세 페이지에 편집 탭 추가 | `frontend/app/(app)/admin/prompts/[promptId]/page.tsx` | 수정 |
| B-4 | AI 제안 이력 API + 피드백 API | `app/api/routes_prompt_evolution.py` | 수정 |
| B-5 | prompt_evolution.py 제안 이력 DB 저장 로직 | `app/services/prompt_evolution.py` | 수정 |

### Phase C: 시뮬레이션 엔진 + UI (Day 5-6)

| # | 작업 | 파일 | 유형 |
|---|------|------|------|
| C-1 | prompt_simulator.py 구현 | `app/services/prompt_simulator.py` | 신규 |
| C-2 | 샘플 RFP 데이터 3종 | `data/sample_rfps/*.json` | 신규 |
| C-3 | 시뮬레이션 API 3개 + 한도 API | `app/api/routes_prompt_evolution.py` | 수정 |
| C-4 | SimulationRunner 컴포넌트 | `frontend/components/prompt/SimulationRunner.tsx` | 신규 |
| C-5 | CompareView 컴포넌트 | `frontend/components/prompt/CompareView.tsx` | 신규 |
| C-6 | 시뮬레이션 페이지 | `frontend/app/(app)/admin/prompts/[promptId]/simulate/page.tsx` | 신규 |

### Phase D: 통합 + QA (Day 7)

| # | 작업 | 파일 | 유형 |
|---|------|------|------|
| D-1 | AppSidebar에 Admin > 프롬프트 관리 메뉴 확인 | `frontend/components/AppSidebar.tsx` | 확인/수정 |
| D-2 | main.py에 라우터 등록 확인 | `app/main.py` | 확인 |
| D-3 | 전체 플로우 E2E 수동 검증 | 수동 QA | - |
| D-4 | TypeScript 빌드 에러 0건 확인 | `npm run build` | - |

---

## 13. File Summary

### 신규 파일 (8개)

| # | 파일 | 줄 (예상) |
|---|------|----------|
| 1 | `database/migrations/012_prompt_admin.sql` | ~60 |
| 2 | `app/services/prompt_categories.py` | ~120 |
| 3 | `app/services/prompt_simulator.py` | ~300 |
| 4 | `data/sample_rfps/sample_small_si.json` | ~80 |
| 5 | `data/sample_rfps/sample_mid_consulting.json` | ~80 |
| 6 | `data/sample_rfps/sample_large_isp.json` | ~80 |
| 7 | `frontend/components/prompt/CategoryTabs.tsx` | ~60 |
| 8 | `frontend/components/prompt/PromptEditor.tsx` | ~150 |
| 9 | `frontend/components/prompt/PreviewPanel.tsx` | ~100 |
| 10 | `frontend/components/prompt/SimulationRunner.tsx` | ~200 |
| 11 | `frontend/components/prompt/CompareView.tsx` | ~150 |
| 12 | `frontend/app/(app)/admin/prompts/[promptId]/simulate/page.tsx` | ~200 |

### 수정 파일 (5개)

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `app/api/routes_prompt_evolution.py` | +8 엔드포인트 (~200줄) |
| 2 | `app/services/prompt_evolution.py` | 제안 이력 DB 저장 로직 (~30줄) |
| 3 | `frontend/lib/api.ts` | +8 타입 + 8 메서드 (~120줄) |
| 4 | `frontend/app/(app)/admin/prompts/page.tsx` | 카테고리 탭 + 필터 (~50줄) |
| 5 | `frontend/app/(app)/admin/prompts/[promptId]/page.tsx` | 편집 탭 추가 (~100줄) |

### 총계: ~1,800줄 신규 + ~500줄 수정 = **~2,300줄**

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-03-25 | Initial draft | AI Coworker |
