# Plan: 프롬프트 Admin — 카테고리 관리 + 편집 + 시뮬레이션 개선

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | prompt-admin |
| 작성일 | 2026-03-25 |
| 우선순위 | High |
| 의존성 | Phase C~E 백엔드 완료 (`prompt_registry`, `prompt_tracker`, `prompt_evolution`, `human_edit_tracker`) |
| 참조 | `app/services/prompt_registry.py`, `app/services/prompt_evolution.py`, `app/api/routes_prompt_evolution.py` |
| 현 상태 | 백엔드 인프라 완비 / **프론트엔드 Admin UI 없음** (§30 의도적 스킵이었으나, 이번에 구현) |

---

## 1. 핵심 문제

현재 프롬프트 관리 시스템은 **백엔드 서비스 4개 + DB 테이블 5개 + API 17개**가 이미 구축되어 있으나, 관리자가 이를 활용할 **시각적 인터페이스가 없다**. 현재 프롬프트 수정은 Python 소스 코드 직접 편집 → Git 커밋 → 서버 재시작으로만 가능하며, 축적된 성과 데이터(수주율, 수정율, 리뷰 피드백)를 시각적으로 확인하거나 A/B 실험을 관리할 수 없다.

| 문제 | 현재 상태 | 영향 |
|------|----------|------|
| 프롬프트 현황 파악 불가 | 47개 프롬프트가 9개 Python 파일에 분산 | 어떤 프롬프트가 성과 좋은지/나쁜지 알 수 없음 |
| 수정 사이클 느림 | 코드 편집 → 배포 → 확인 (최소 수십 분) | 프롬프트 개선 속도 저하 |
| 성과 데이터 사장 | DB에 축적되지만 조회 UI 없음 | 데이터 기반 개선 불가 |
| A/B 실험 관리 불가 | API만 존재, UI 없음 | 실험 시작/모니터링/판정 불가 |
| 시뮬레이션 불가 | 실제 제안서 생성해봐야 결과 확인 | 프롬프트 변경 리스크 큼 |

---

## 2. 프롬프트 카테고리 분류 체계

플랫폼에서 활용 중인 **47개 프롬프트**를 6개 카테고리로 분류한다.

### 카테고리 A: 공고 분석 (Bid Analysis) — 9개

| ID | 프롬프트 | 소스 파일 | 용도 | 토큰 |
|----|---------|----------|------|------|
| A-1 | `PREPROCESSOR_SYSTEM` | `bid_review.py` | G2B 공고 전처리 (기관/예산/범위/자격/평가 추출) | ~800 |
| A-2 | `PREPROCESSOR_USER` | `bid_review.py` | 원문→BidSummary JSON 변환 | ~400 |
| A-3 | `REVIEWER_SYSTEM` | `bid_review.py` | TENOPA 적합도 평가 (40개 긍정 키워드 + 부정 필터 + 4축 점수) | ~1,200 |
| A-4 | `REVIEWER_USER_SINGLE` | `bid_review.py` | 단건 적합도 점수(0-100) + 판정 | ~300 |
| A-5 | `REVIEWER_USER_BATCH` | `bid_review.py` | 다건 일괄 평가 | ~300 |
| A-6 | `UNIFIED_ANALYSIS_SYSTEM` | `bid_review.py` | 전처리+리뷰 통합 1-shot 분석 | ~1,500 |
| A-7 | `UNIFIED_ANALYSIS_USER` | `bid_review.py` | 통합 분석 사용자 프롬프트 | ~300 |
| A-8 | `VERDICT_TO_ACTION` | `bid_review.py` | 판정→액션 매핑 (dict) | ~50 |
| A-9 | `VERDICT_TO_PROBABILITY` | `bid_review.py` | 판정→확률 매핑 (dict) | ~50 |

### 카테고리 B: 전략 수립 (Strategy) — 4개

| ID | 프롬프트 | 소스 파일 | 용도 | 토큰 |
|----|---------|----------|------|------|
| B-1 | `STRATEGY_GENERATE_PROMPT` | `strategy.py` | RFP+GoNoGo→전략+Win Theme+대안 | ~2,500 |
| B-2 | `POSITIONING_STRATEGY_MATRIX` | `strategy.py` | 3방향 포지셔닝 가이드 (방어/공격/인접) | ~400 |
| B-3 | `COMPETITIVE_ANALYSIS_FRAMEWORK` | `strategy.py` | SWOT + 차별화 + 시나리오 | ~500 |
| B-4 | `STRATEGY_RESEARCH_FRAMEWORK` | `strategy.py` | 리서치 질문 + 방법론 근거 | ~400 |

### 카테고리 C: 계획 수립 (Planning) — 6개

| ID | 프롬프트 | 소스 파일 | 용도 | 토큰 |
|----|---------|----------|------|------|
| C-1 | `PLAN_TEAM_PROMPT` | `plan.py` | 팀 구성 + 역할 + 요구사항 | ~700 |
| C-2 | `PLAN_ASSIGN_PROMPT` | `plan.py` | 산출물 + 담당 + QA 체크포인트 | ~700 |
| C-3 | `PLAN_SCHEDULE_PROMPT` | `plan.py` | 일정 + 단계 + 마일스톤 + 크리티컬패스 | ~700 |
| C-4 | `PLAN_STORY_PROMPT` | `plan.py` | 목차 기획 + 스토리라인 설계 + SMART 목표 | ~1,500 |
| C-5 | `PLAN_PRICE_PROMPT` | `plan.py` | 예산 편성 + 입찰 시뮬레이션 + Budget Narrative | ~1,200 |
| C-6 | `BUDGET_DETAIL_FRAMEWORK` | `plan.py` | 원가 기준 + 노임단가 + 경비 + 이윤 | ~500 |

### 카테고리 D: 제안서 작성 (Proposal Writing) — 15개

| ID | 프롬프트 | 소스 파일 | 용도 | 토큰 |
|----|---------|----------|------|------|
| D-0 | `EVALUATOR_PERSPECTIVE_BLOCK` | `section_prompts.py` | **공유 블록**: 5대 평가 기준 + 스토리텔링 + 깊이 기준 (모든 섹션에 주입) | ~2,000 |
| D-1 | `SECTION_PROMPT_UNDERSTAND` | `section_prompts.py` | 과업 이해 (AS-IS/TO-BE, 핫버튼, 발주기관 맥락) | ~2,000 |
| D-2 | `SECTION_PROMPT_STRATEGY` | `section_prompts.py` | Win Theme + 프레임워크 + 차별화 + CSF + KPI | ~2,000 |
| D-3 | `SECTION_PROMPT_METHODOLOGY` | `section_prompts.py` | 단계별 접근법 + 커스터마이징 + 산출물 | ~2,000 |
| D-4 | `SECTION_PROMPT_TECHNICAL` | `section_prompts.py` | 아키텍처 + 설계 + 구현 + 데이터 흐름 | ~2,000 |
| D-5 | `SECTION_PROMPT_MANAGEMENT` | `section_prompts.py` | 리스크 관리 + 일정 + QA + 커뮤니케이션 | ~2,000 |
| D-6 | `SECTION_PROMPT_PERSONNEL` | `section_prompts.py` | 팀 구성 + 자격 + 배치 + 조직도 | ~2,000 |
| D-7 | `SECTION_PROMPT_TRACK_RECORD` | `section_prompts.py` | 수행 실적 + 사례 + 참조 + 자격 | ~2,000 |
| D-8 | `SECTION_PROMPT_SECURITY` | `section_prompts.py` | 보안 + 접근 제어 + 암호화 + 취약점 + 컴플라이언스 | ~2,000 |
| D-9 | `SECTION_PROMPT_MAINTENANCE` | `section_prompts.py` | SLA + 지원 + 지속가능성 + 재해 복구 | ~2,000 |
| D-10 | `SECTION_PROMPT_ADDED_VALUE` | `section_prompts.py` | 기대효과 + 혁신 + 미래 로드맵 | ~2,000 |
| D-11 | `SECTION_PROMPT_CASE_B` | `section_prompts.py` | 양식 제약 모드 (발주기관 템플릿 보존) | ~1,500 |
| D-12 | `PROPOSAL_CASE_A_PROMPT` | `proposal_prompts.py` | 자유형식 제안서 섹션 | ~1,600 |
| D-13 | `PROPOSAL_CASE_B_PROMPT` | `proposal_prompts.py` | 양식 제약 제안서 (발주처 양식 보존) | ~1,200 |
| D-14 | `SELF_REVIEW_PROMPT` | `proposal_prompts.py` | 4축 자가진단 (적합성/전략/품질/신뢰성) + 3-persona 시뮬레이션 | ~1,800 |

### 카테고리 E: 발표 자료 (Presentation) — 8개

| ID | 프롬프트 | 소스 파일 | 용도 | 토큰 |
|----|---------|----------|------|------|
| E-1 | `PRESENTATION_STRATEGY_PROMPT` | `proposal_prompts.py` | 시간 배분 + 구조 + Q&A 전략 + 비주얼 전략 | ~800 |
| E-2 | `PPT_SLIDE_PROMPT` | `proposal_prompts.py` | 섹션→PPT 슬라이드 변환 | ~600 |
| E-3 | `PPT_TOC_SYSTEM` | `ppt_pipeline.py` | PPT 목차 설계 (25-35 슬라이드, F-패턴, 14 레이아웃) | ~2,500 |
| E-4 | `PPT_TOC_USER` | `ppt_pipeline.py` | 평가가중치→목차 레이아웃 매핑 | ~1,000 |
| E-5 | `PPT_VISUAL_BRIEF_SYSTEM` | `ppt_pipeline.py` | 비주얼 전략 원칙 (Message→Logic→Structure→Design) | ~2,500 |
| E-6 | `PPT_VISUAL_BRIEF_USER` | `ppt_pipeline.py` | TOC+Win Theme→비주얼 브리프 | ~1,000 |
| E-7 | `PPT_STORYBOARD_SYSTEM` | `ppt_pipeline.py` | 스토리보드 규칙 (6×6, 발표 노트) | ~2,500 |
| E-8 | `PPT_STORYBOARD_USER` | `ppt_pipeline.py` | TOC+비주얼브리프+섹션→슬라이드 콘텐츠 | ~1,000 |

### 카테고리 F: 품질 보증 (Quality Assurance) — 5개

| ID | 프롬프트 | 소스 파일 | 용도 | 토큰 |
|----|---------|----------|------|------|
| F-1 | `SOURCE_TAG_FORMAT` | `trustworthiness.py` | 8종 출처 태그 ([KB], [역량DB], [RFP p.N] 등) | ~500 |
| F-2 | `TRUSTWORTHINESS_RULES` | `trustworthiness.py` | 6대 신뢰성 규칙 (환각 방지, 출처 태깅 등) | ~600 |
| F-3 | `TRUSTWORTHINESS_SCORING` | `trustworthiness.py` | 25점 평가 (출처 태그 준수, KB 활용, 금지 표현) | ~400 |
| F-4 | `FORBIDDEN_EXPRESSIONS` | `trustworthiness.py` | 10개 금지 표현 리스트 | ~100 |
| F-5 | `EXTRACT_SUBMISSION_DOCS_PROMPT` | `submission_docs.py` | RFP→제출서류 JSON 추출 | ~900 |

### 카테고리 요약

| 카테고리 | 코드 | 개수 | 토큰 합계 | 핵심 특성 |
|---------|------|------|----------|----------|
| 공고 분석 | A | 9 | ~5,400 | 입력 텍스트 의존, 정형 출력 |
| 전략 수립 | B | 4 | ~3,800 | 프레임워크 조합, 구조화 추론 |
| 계획 수립 | C | 6 | ~5,300 | 병렬 실행, DB 연동 (노임단가) |
| 제안서 작성 | D | 15 | ~26,100 | **최대 비중**, 유형별 전문화 + 공유 블록 |
| 발표 자료 | E | 8 | ~11,900 | 3단계 파이프라인, System/User 쌍 |
| 품질 보증 | F | 5 | ~2,500 | 크로스커팅 (다른 프롬프트에 주입) |
| **합계** | | **47** | **~55,000** | |

---

## 3. 개선 목표

### 3.1 기능 목표

| # | 기능 | 설명 | 우선순위 |
|---|------|------|---------|
| G-1 | 프롬프트 카탈로그 | 6개 카테고리 기반 전체 프롬프트 목록 + 메타데이터 조회 | **P0** |
| G-2 | 성과 대시보드 | 프롬프트별 수주율, 품질점수, 수정율, 사용횟수 시각화 | **P0** |
| G-3 | 인라인 편집기 | 프롬프트 텍스트 직접 편집 (변수 하이라이트, 구문 검증) | **P0** |
| G-4 | AI 개선 제안 | 축적된 성과 데이터 기반 Claude 메타분석 → 3개 개선안 | **P1** |
| G-5 | 시뮬레이션 샌드박스 | 수정된 프롬프트로 샘플 RFP 실행 → 결과 즉시 확인 | **P1** |
| G-6 | Diff 비교기 | 버전 간 텍스트 비교 (변경점 하이라이트) | **P1** |
| G-7 | A/B 실험 관리 | 실험 생성/모니터링/승격/롤백 UI | **P2** |
| G-8 | 섹션 히트맵 | 섹션 유형별 품질 점수 히트맵 | **P2** |
| G-9 | 변수 인스펙터 | 프롬프트 내 `{variable}` 목록 + 실제 주입값 미리보기 | **P2** |

### 3.2 비기능 목표

| # | 목표 | 기준 |
|---|------|------|
| N-1 | 시뮬레이션 응답 시간 | 프롬프트 1개 시뮬레이션 ≤ 30초 |
| N-2 | 권한 제어 | admin 역할만 프롬프트 편집/실험 가능 |
| N-3 | 변경 감사 | 모든 프롬프트 수정 이력 audit_log 기록 |
| N-4 | 안전장치 | 프롬프트 삭제 불가, 항상 버전 추가만 허용 (retired 마킹) |

---

## 4. 기능 상세 설계

### 4.1 프롬프트 카탈로그 (G-1)

```
/admin/prompts
├── 카테고리 탭: [공고 분석] [전략] [계획] [제안서 작성] [발표 자료] [품질 보증]
├── 각 프롬프트 카드:
│   ├── ID + 이름 + 소스 파일
│   ├── 상태 배지: active (초록) / candidate (노랑) / retired (회색)
│   ├── 메타: 토큰 수, 변수 개수, 버전 수, 마지막 수정일
│   ├── 성과 미니: 수주율 % / 품질점수 / 수정율
│   └── 액션: [상세] [편집] [시뮬레이션] [히스토리]
└── 검색/필터: 키워드, 상태, 카테고리
```

**카테고리 매핑 (백엔드)**:

```python
PROMPT_CATEGORIES = {
    "bid_analysis": {
        "label": "공고 분석",
        "icon": "Search",
        "prompts": ["bid_review.PREPROCESSOR_SYSTEM", "bid_review.PREPROCESSOR_USER", ...],
    },
    "strategy": {
        "label": "전략 수립",
        "icon": "Target",
        "prompts": ["strategy.GENERATE_PROMPT", ...],
    },
    "planning": {
        "label": "계획 수립",
        "icon": "Calendar",
        "prompts": ["plan.TEAM_PROMPT", ...],
    },
    "proposal_writing": {
        "label": "제안서 작성",
        "icon": "FileText",
        "prompts": ["section_prompts.EVALUATOR_PERSPECTIVE_BLOCK", ...],
    },
    "presentation": {
        "label": "발표 자료",
        "icon": "Presentation",
        "prompts": ["ppt_pipeline.TOC_SYSTEM", ...],
    },
    "quality_assurance": {
        "label": "품질 보증",
        "icon": "Shield",
        "prompts": ["trustworthiness.SOURCE_TAG_FORMAT", ...],
    },
}
```

### 4.2 성과 대시보드 (G-2)

```
/admin/prompts/dashboard
├── 요약 카드: 전체 프롬프트 47개 / 활성 실험 N건 / 주의 필요 N건
├── 카테고리별 성과 비교 (Recharts BarChart)
│   ├── X축: 카테고리
│   └── Y축: 평균 수주율 / 평균 품질점수 / 평균 수정율
├── 수정율 워스트 5 (가장 많이 수정되는 프롬프트)
├── 품질 트렌드 (LineChart: 최근 20건 품질점수 추이)
└── 진행 중 실험 목록
```

**기존 API 활용**:
- `GET /api/prompts/dashboard` → 이미 구현됨
- `GET /api/prompts/section-heatmap` → 이미 구현됨
- `GET /api/prompts/{id}/effectiveness` → 이미 구현됨

**신규 API**:
- `GET /api/prompts/categories` → 카테고리 매핑 + 프롬프트별 메타 반환
- `GET /api/prompts/worst-performers` → 수정율/품질 기준 워스트 N

### 4.3 프롬프트 편집기 (G-3)

```
/admin/prompts/{prompt_id}/edit
├── 2-패널 레이아웃
│   ├── 좌: 에디터 (Monaco/CodeMirror)
│   │   ├── 구문 하이라이트: {변수}는 파란색, {{이스케이프}}는 회색
│   │   ├── 인라인 변수 힌트: hover 시 변수 설명 + 타입
│   │   ├── 토큰 카운터 (실시간 추정)
│   │   └── 변경 감지: 원본 대비 diff 표시
│   └── 우: 미리보기/시뮬레이션 패널
│       ├── 변수 슬롯: 실제 또는 샘플 데이터로 변수 치환
│       └── 렌더링된 프롬프트 미리보기
├── 하단 툴바
│   ├── [저장 (candidate)] — 후보로 등록 (active에 영향 없음)
│   ├── [시뮬레이션 실행] — §4.5 샌드박스 호출
│   ├── [AI 개선 제안] — §4.4 호출
│   └── [버전 비교] — §4.6 Diff 뷰
└── 변경 사유 입력 (필수)
```

**편집 권한**: `require_role("admin")` 적용

**저장 플로우**:
1. 편집 → `POST /api/prompts/{id}/create-candidate` (이미 구현)
2. candidate 상태로 등록 → active에는 영향 없음
3. 시뮬레이션 통과 후 → A/B 실험 또는 직접 승격

### 4.4 AI 개선 제안 (G-4)

```
/admin/prompts/{prompt_id}/improve
├── 현재 프롬프트 요약
├── 성과 데이터 요약 (수주율, 품질, 수정율)
├── [AI 분석 실행] 버튼
│   └── Claude 메타분석 (~4K 토큰, 30초 이내)
├── 결과: 3개 개선안
│   ├── 개선안 1: 제목 + 근거 + 핵심 변경점 + 전문
│   ├── 개선안 2: ...
│   └── 개선안 3: ...
├── 각 개선안에 [이 안으로 편집] [시뮬레이션] [후보 등록] 버튼
└── 분석 이력: 이전 AI 제안 기록
```

**기존 API 활용**: `POST /api/prompts/{id}/suggest-improvement` (이미 구현)

**신규 기능**:
- AI 제안 이력 저장 (DB 테이블 `prompt_improvement_suggestions`)
- 제안 수용/거부 피드백 기록 → 향후 메타분석 정확도 개선

### 4.5 시뮬레이션 샌드박스 (G-5) ★ 핵심 신규 기능

**목적**: 프롬프트를 수정한 뒤 **실제 제안서를 생성하지 않고도** 결과를 미리 확인한다.

```
/admin/prompts/{prompt_id}/simulate
├── 입력 설정
│   ├── 시뮬레이션 데이터 소스 선택:
│   │   ├── [샘플 RFP] — 시스템 제공 3종 (소규모/중규모/대규모)
│   │   ├── [기존 프로젝트] — 과거 수주 프로젝트에서 state 스냅샷 로드
│   │   └── [커스텀 입력] — 직접 state 변수 입력
│   ├── 프롬프트 버전 선택: active / candidate / 편집 중 텍스트
│   └── 비교 모드: [단독 실행] / [A vs B 비교]
│
├── 실행 결과
│   ├── AI 출력 전문 (JSON 또는 Markdown)
│   ├── 메타데이터: 토큰 사용량, 응답 시간, 모델
│   ├── 자동 품질 평가 (SELF_REVIEW_PROMPT 활용한 자가진단 점수)
│   └── Compliance 체크 (변수 미사용 경고, 출력 형식 검증)
│
├── A vs B 비교 모드
│   ├── 좌: Active 버전 결과
│   ├── 우: Candidate/편집 중 버전 결과
│   ├── 하단: Diff 하이라이트 + 품질 점수 비교
│   └── [이 후보로 A/B 실험 시작] 버튼
│
└── 시뮬레이션 이력 (최근 20건, DB 저장)
```

**시뮬레이션 아키텍처**:

```
[프론트엔드]
    ↓ POST /api/prompts/{id}/simulate
[백엔드: prompt_simulator.py]
    ├── 1. 프롬프트 텍스트 + 변수 조합
    ├── 2. state 데이터 로드 (샘플/프로젝트/커스텀)
    ├── 3. 변수 치환 → 최종 프롬프트 구성
    ├── 4. Claude API 호출 (max_tokens 제한, 별도 예산)
    ├── 5. 출력 파싱 + 형식 검증
    ├── 6. (선택) 자가진단 프롬프트로 품질 점수 산출
    └── 7. 결과 + 메타데이터 반환
```

**시뮬레이션 데이터 소스**:

| 소스 | 설명 | 준비 방식 |
|------|------|----------|
| 샘플 RFP 3종 | 소규모 SI, 중규모 컨설팅, 대규모 ISP | `data/sample_rfps/` 에 JSON 스냅샷 저장 |
| 기존 프로젝트 | 과거 수주 프로젝트의 graph state | LangGraph checkpointer에서 state 로드 |
| 커스텀 입력 | 사용자가 변수 직접 입력 | UI 폼에서 JSON 편집 |

**비용 제어**:
- 시뮬레이션당 `max_tokens=2000` (본문 프롬프트) / `max_tokens=500` (자가진단)
- 일일 시뮬레이션 한도: 50회 (admin 당)
- 시뮬레이션 전용 예산 추적 (`simulation_token_usage` 테이블)

### 4.6 Diff 비교기 (G-6)

```
/admin/prompts/{prompt_id}/diff
├── 버전 A 선택 (드롭다운: v1, v2, ..., active)
├── 버전 B 선택
├── Side-by-side Diff 뷰
│   ├── 추가된 줄: 초록 배경
│   ├── 삭제된 줄: 빨강 배경
│   └── 변경된 단어: 인라인 하이라이트
├── 변경 요약: +N줄 / -N줄 / 토큰 변화량
└── 변경 사유 표시 (change_reason 필드)
```

**구현**: `diff-match-patch` 라이브러리 (프론트엔드)

### 4.7 A/B 실험 관리 (G-7)

```
/admin/prompts/experiments
├── 진행 중 실험 목록
│   ├── 실험명, 프롬프트, baseline vs candidate, 트래픽 비율, 샘플 수
│   └── [평가] [중단] 액션
├── 완료된 실험 목록
│   ├── 결과: 승격/롤백/중단
│   └── 복합 점수 비교
└── [새 실험 만들기] 버튼
    ├── 프롬프트 선택
    ├── candidate 버전 선택
    ├── 트래픽 비율 (10~50%)
    ├── 최소 샘플 수 (기본 5)
    └── 실험명
```

**기존 API 활용**: 실험 CRUD 5개 엔드포인트 모두 이미 구현됨

### 4.8 섹션 히트맵 (G-8)

```
/admin/prompts/heatmap
├── X축: 프롬프트 유형 (UNDERSTAND, STRATEGY, ...)
├── Y축: 프로젝트 (최근 20건)
├── 셀 색상: 품질점수 (빨강 ≤60 / 노랑 60-80 / 초록 ≥80)
├── 셀 클릭 → 해당 프롬프트 상세 이동
└── 필터: 기간, 카테고리
```

**기존 API 활용**: `GET /api/prompts/section-heatmap` (이미 구현)

---

## 5. 데이터 모델 변경

### 5.1 신규 테이블

```sql
-- 시뮬레이션 이력
CREATE TABLE prompt_simulations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    prompt_id TEXT NOT NULL,
    prompt_version INT,
    prompt_text TEXT NOT NULL,          -- 시뮬레이션에 사용된 실제 텍스트
    data_source TEXT NOT NULL,          -- 'sample' | 'project' | 'custom'
    data_source_id TEXT,                -- 샘플 RFP ID 또는 프로젝트 ID
    input_variables JSONB DEFAULT '{}', -- 치환된 변수 값
    output_text TEXT,                   -- AI 출력 전문
    output_meta JSONB DEFAULT '{}',     -- {tokens_in, tokens_out, duration_ms, model}
    quality_score REAL,                 -- 자가진단 점수 (0-100)
    quality_detail JSONB,              -- 축별 상세
    compared_with_version INT,          -- A/B 비교 시 상대 버전
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_ps_prompt ON prompt_simulations(prompt_id);
CREATE INDEX idx_ps_created ON prompt_simulations(created_at DESC);

-- AI 개선 제안 이력
CREATE TABLE prompt_improvement_suggestions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    prompt_id TEXT NOT NULL,
    prompt_version INT NOT NULL,
    analysis TEXT,                       -- 약점 분석
    suggestions JSONB NOT NULL,          -- [{title, rationale, key_changes, prompt_text}]
    accepted_index INT,                  -- 수용된 제안 인덱스 (null=미수용)
    feedback TEXT,                       -- 관리자 피드백
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_pis_prompt ON prompt_improvement_suggestions(prompt_id);

-- 시뮬레이션 토큰 사용량
CREATE TABLE simulation_token_usage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    date DATE DEFAULT CURRENT_DATE,
    simulations_count INT DEFAULT 0,
    tokens_input INT DEFAULT 0,
    tokens_output INT DEFAULT 0,
    UNIQUE(user_id, date)
);
```

### 5.2 기존 테이블 확장

```sql
-- prompt_registry에 카테고리 필드 추가
ALTER TABLE prompt_registry ADD COLUMN category TEXT;

-- 카테고리 값 일괄 업데이트 (마이그레이션에서 실행)
UPDATE prompt_registry SET category = 'bid_analysis' WHERE prompt_id LIKE 'bid_review.%';
UPDATE prompt_registry SET category = 'strategy' WHERE prompt_id LIKE 'strategy.%';
UPDATE prompt_registry SET category = 'planning' WHERE prompt_id LIKE 'plan.%';
UPDATE prompt_registry SET category = 'proposal_writing' WHERE prompt_id LIKE 'section_prompts.%' OR prompt_id LIKE 'proposal_prompts.%';
UPDATE prompt_registry SET category = 'presentation' WHERE prompt_id LIKE 'ppt_pipeline.%' OR prompt_id LIKE 'proposal_prompts.PRESENTATION%' OR prompt_id LIKE 'proposal_prompts.PPT%';
UPDATE prompt_registry SET category = 'quality_assurance' WHERE prompt_id LIKE 'trustworthiness.%' OR prompt_id LIKE 'submission_docs.%';
```

---

## 6. 신규 API 목록

| # | 메서드 | 경로 | 설명 |
|---|--------|------|------|
| 1 | GET | `/api/prompts/categories` | 카테고리 매핑 + 프롬프트별 메타 |
| 2 | GET | `/api/prompts/worst-performers` | 수정율/품질 기준 워스트 N |
| 3 | POST | `/api/prompts/{id}/simulate` | 시뮬레이션 실행 |
| 4 | GET | `/api/prompts/{id}/simulations` | 시뮬레이션 이력 조회 |
| 5 | POST | `/api/prompts/{id}/simulate-compare` | A vs B 비교 시뮬레이션 |
| 6 | GET | `/api/prompts/{id}/suggestions` | AI 개선 제안 이력 |
| 7 | POST | `/api/prompts/{id}/suggestions/{sid}/feedback` | 제안 수용/거부 피드백 |
| 8 | GET | `/api/prompts/simulation-quota` | 일일 시뮬레이션 잔여 한도 |

**기존 API 재활용** (변경 없음): 기존 17개 엔드포인트 전부 활용

---

## 7. 프론트엔드 신규 페이지/컴포넌트

### 7.1 페이지 (6개)

| # | 경로 | 설명 | 주요 컴포넌트 |
|---|------|------|-------------|
| 1 | `/admin/prompts` | 프롬프트 카탈로그 | CategoryTabs, PromptCard, SearchFilter |
| 2 | `/admin/prompts/dashboard` | 성과 대시보드 | SummaryCards, CategoryBarChart, WorstPerformers, TrendLine |
| 3 | `/admin/prompts/[id]` | 프롬프트 상세 + 편집 | PromptEditor, VariableInspector, PreviewPanel |
| 4 | `/admin/prompts/[id]/simulate` | 시뮬레이션 샌드박스 | DataSourceSelector, SimulationResult, CompareView |
| 5 | `/admin/prompts/experiments` | A/B 실험 관리 | ExperimentList, ExperimentDetail, NewExperimentForm |
| 6 | `/admin/prompts/heatmap` | 섹션 히트맵 | HeatmapGrid, QualityTooltip |

### 7.2 공용 컴포넌트 (8개)

| # | 컴포넌트 | 설명 |
|---|---------|------|
| 1 | `PromptEditor` | Monaco/CodeMirror 기반 편집기 + 변수 하이라이트 + 토큰 카운터 |
| 2 | `PromptDiffView` | Side-by-side diff (diff-match-patch) |
| 3 | `SimulationRunner` | 시뮬레이션 실행 + 결과 표시 + 품질 점수 |
| 4 | `PromptCard` | 프롬프트 요약 카드 (이름, 상태, 성과 미니) |
| 5 | `CategoryTabs` | 6개 카테고리 탭 |
| 6 | `VersionTimeline` | 버전 이력 타임라인 (active/candidate/retired 상태 표시) |
| 7 | `QualityBadge` | 품질 점수 배지 (색상 코딩: 빨/노/초) |
| 8 | `CompareView` | A vs B 결과 나란히 비교 |

---

## 8. 핵심 플로우

### 8.1 프롬프트 개선 사이클 (Human-Driven)

```
1. 대시보드에서 워스트 퍼포머 확인
   ↓
2. 프롬프트 상세 페이지 진입
   ↓
3. [AI 개선 제안] 클릭 → 3개 개선안 수신
   ↓
4. 개선안 선택 또는 직접 편집
   ↓
5. [시뮬레이션 실행] → 샘플 RFP로 결과 확인
   ↓
6. [A vs B 비교] → active 버전 결과와 나란히 비교
   ↓
7. 만족 → [후보 등록]
   ↓
8. [A/B 실험 시작] → 20% 트래픽으로 실전 검증
   ↓
9. min_samples 도달 → [실험 평가]
   ↓
10. 개선 확인 → [승격] / 악화 → [롤백]
```

### 8.2 프롬프트 개선 사이클 (AI-Driven, 자동)

```
1. weekly cron: prompt_tracker.periodic_maintenance()
   ↓
2. check_prompts_needing_attention() → 수정율 >50% 프롬프트 탐지
   ↓
3. suggest_improvements() → Claude 메타분석 → 3개 개선안
   ↓
4. 개선안 DB 저장 (prompt_improvement_suggestions)
   ↓
5. Teams 알림 → 관리자에게 리뷰 요청
   ↓
6. 관리자가 Admin UI에서 확인 → 시뮬레이션 → 판단
```

---

## 9. 시뮬레이션 엔진 상세

### 9.1 prompt_simulator.py (신규 서비스)

```python
class SimulationRequest:
    prompt_id: str
    prompt_text: str | None      # None이면 active 버전 사용
    data_source: Literal["sample", "project", "custom"]
    data_source_id: str | None   # 샘플 ID 또는 프로젝트 ID
    custom_variables: dict | None
    run_quality_check: bool = True

class SimulationResult:
    output_text: str
    tokens_input: int
    tokens_output: int
    duration_ms: int
    quality_score: float | None
    quality_detail: dict | None
    variables_used: list[str]
    variables_missing: list[str]
    format_valid: bool
    format_errors: list[str]
```

### 9.2 샘플 RFP 데이터

| ID | 이름 | 규모 | 특성 |
|----|------|------|------|
| `sample_small_si` | 소규모 SI | 5천만원 | 단순 개발, 3인 팀, 서류심사 |
| `sample_mid_consulting` | 중규모 컨설팅 | 3억원 | ISP/BPR, 10인 팀, 기술+가격 분리 |
| `sample_large_isp` | 대규모 ISP | 15억원 | 대형 SI, 30인 팀, 발표심사 포함 |

각 샘플은 `ProposalState`의 주요 필드(rfp_text, rfp_analysis, go_no_go, strategy, plan 등)를 모두 포함하는 JSON 스냅샷이다.

### 9.3 품질 자동 평가

시뮬레이션 출력에 대해 `SELF_REVIEW_PROMPT`의 간소화 버전으로 4축 평가를 수행한다:

| 축 | 평가 기준 | 배점 |
|----|----------|------|
| 적합성 | RFP 요구사항 반영도 | 25점 |
| 전략 정합성 | Win Theme과의 일관성 | 25점 |
| 품질 | 구조, 깊이, 구체성 | 25점 |
| 신뢰성 | 출처 태깅, 근거 비율, 금지 표현 | 25점 |

---

## 10. YAGNI 검토

### v1 포함 (이번 구현)

| 기능 | 근거 |
|------|------|
| 프롬프트 카탈로그 (G-1) | 47개 프롬프트 파악이 모든 작업의 전제 |
| 성과 대시보드 (G-2) | 축적된 데이터 활용의 최소 단위 |
| 인라인 편집기 (G-3) | 코드 수정 없이 프롬프트 개선하려면 필수 |
| AI 개선 제안 (G-4) | 기존 API 활용, 프론트엔드만 추가 |
| 시뮬레이션 샌드박스 (G-5) | 핵심 차별화 기능, 편집기와 함께 제공해야 의미 |
| Diff 비교기 (G-6) | 버전 관리의 기본 도구 |

### v2 이후 (보류)

| 기능 | 보류 사유 |
|------|----------|
| A/B 실험 관리 UI (G-7) | 실전 데이터 축적 후 의미 있음, API는 이미 준비됨 |
| 섹션 히트맵 (G-8) | 대시보드로 충분, 별도 페이지는 데이터 축적 후 |
| 변수 인스펙터 (G-9) | 편집기 내 기본 변수 하이라이트로 충분 |
| 프롬프트 자동 승격 | 사람 판단 필수, 자동화는 위험 |
| 멀티 모델 시뮬레이션 | Claude 단일 모델 정책 |

---

## 11. 구현 순서

### Phase A: 인프라 + 카탈로그 (2일)

| # | 작업 | 파일 |
|---|------|------|
| A-1 | DB 마이그레이션 (신규 3 테이블 + category 컬럼) | `database/migrations/012_prompt_admin.sql` |
| A-2 | 카테고리 매핑 상수 + API 2개 (categories, worst-performers) | `app/services/prompt_categories.py`, `routes_prompt_evolution.py` |
| A-3 | 프론트: 카탈로그 페이지 + CategoryTabs + PromptCard | `frontend/app/(app)/admin/prompts/page.tsx` |
| A-4 | 프론트: 프롬프트 상세 페이지 + VersionTimeline | `frontend/app/(app)/admin/prompts/[id]/page.tsx` |

### Phase B: 대시보드 + Diff (1일)

| # | 작업 | 파일 |
|---|------|------|
| B-1 | 프론트: 성과 대시보드 (기존 API 활용) | `frontend/app/(app)/admin/prompts/dashboard/page.tsx` |
| B-2 | 프론트: PromptDiffView 컴포넌트 | `frontend/components/prompt/PromptDiffView.tsx` |
| B-3 | 프론트: Recharts 차트 (카테고리별 성과, 트렌드) | `frontend/components/prompt/PerformanceCharts.tsx` |

### Phase C: 편집기 (2일)

| # | 작업 | 파일 |
|---|------|------|
| C-1 | 프론트: PromptEditor (변수 하이라이트 + 토큰 카운터) | `frontend/components/prompt/PromptEditor.tsx` |
| C-2 | 프론트: PreviewPanel (변수 치환 미리보기) | `frontend/components/prompt/PreviewPanel.tsx` |
| C-3 | 프론트: 편집 페이지 통합 (에디터 + 미리보기 + 저장) | `frontend/app/(app)/admin/prompts/[id]/edit/page.tsx` |
| C-4 | AI 제안 이력 저장 API + DB | `routes_prompt_evolution.py`, `prompt_evolution.py` |

### Phase D: 시뮬레이션 (2일)

| # | 작업 | 파일 |
|---|------|------|
| D-1 | 백엔드: prompt_simulator.py (시뮬레이션 엔진) | `app/services/prompt_simulator.py` |
| D-2 | 샘플 RFP 데이터 3종 | `data/sample_rfps/*.json` |
| D-3 | API 3개 (simulate, simulations, simulate-compare) | `routes_prompt_evolution.py` |
| D-4 | 프론트: 시뮬레이션 페이지 + DataSourceSelector + SimulationResult | `frontend/app/(app)/admin/prompts/[id]/simulate/page.tsx` |
| D-5 | 프론트: CompareView (A vs B 결과 비교) | `frontend/components/prompt/CompareView.tsx` |
| D-6 | 일일 한도 체크 + simulation_token_usage | `prompt_simulator.py` |

### Phase E: 통합 + QA (1일)

| # | 작업 | 파일 |
|---|------|------|
| E-1 | AppSidebar에 Admin > 프롬프트 관리 메뉴 추가 | `frontend/components/AppSidebar.tsx` |
| E-2 | admin 권한 가드 적용 | `frontend/middleware.ts` 또는 레이아웃 |
| E-3 | 전체 플로우 E2E 검증 (카탈로그→편집→시뮬레이션→후보 등록) | 수동 QA |
| E-4 | API 타입 + 프론트 타입 동기화 | `frontend/lib/api.ts` |

---

## 12. 성공 기준

| # | 기준 | 검증 방법 |
|---|------|----------|
| S-1 | 카탈로그에서 47개 프롬프트를 6개 카테고리로 조회 가능 | `/admin/prompts` 페이지 렌더링 확인 |
| S-2 | 대시보드에서 프롬프트별 성과 메트릭 시각화 | 차트 렌더링 + 데이터 정합성 |
| S-3 | 편집기에서 프롬프트 수정 후 candidate로 저장 | DB에 새 버전 생성 확인 |
| S-4 | AI 개선 제안 → 3개 개선안 표시 | API 응답 + UI 렌더링 |
| S-5 | 시뮬레이션 실행 → 30초 이내 결과 반환 | 응답 시간 측정 |
| S-6 | A vs B 비교 시뮬레이션 → 두 결과 나란히 표시 | CompareView 렌더링 |
| S-7 | Diff 뷰에서 버전 간 변경점 하이라이트 | 추가/삭제/수정 표시 확인 |
| S-8 | admin 역할 아닌 사용자 → 접근 차단 | 403 응답 확인 |

---

## 13. 리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 시뮬레이션 비용 과다 | Claude API 비용 증가 | 일일 50회 한도 + max_tokens 제한 + 캐싱 |
| 프롬프트 잘못 수정 → 제안서 품질 저하 | 수주율 하락 | candidate 상태 필수, active 직접 수정 금지, 시뮬레이션 + A/B 검증 |
| 샘플 RFP가 실제와 괴리 | 시뮬레이션 결과 신뢰도 저하 | 수주 성공 프로젝트의 state 스냅샷 활용 옵션 제공 |
| Monaco 에디터 번들 사이즈 | 프론트엔드 로딩 지연 | dynamic import + 코드 스플리팅 |

---

## 14. 다음 단계

```
/pdca design prompt-admin
```
