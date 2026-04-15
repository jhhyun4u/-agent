# 사전규격 + 발주계획 통합 Plan & 3. 변경 범위
Cohesion: 0.12 | Nodes: 16

## Key Nodes
- **사전규격 + 발주계획 통합 Plan** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 8 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
- **3. 변경 범위** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 7 connections
  - -> contains -> [[3-1-g2b-api-orderplansttusservice]]
  - -> contains -> [[3-2]]
  - -> contains -> [[3-3]]
  - -> contains -> [[3-4]]
  - -> contains -> [[3-5-api]]
  - -> contains -> [[3-6]]
  - <- contains <- [[plan]]
- **4. 기술 고려사항** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 2 connections
  - -> contains -> [[g2b-api]]
  - <- contains <- [[plan]]
- **1. 배경 및 목적** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **2. 현황 분석** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **3-1. G2B API 추가: 발주계획 (`OrderPlanSttusService`)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3-2. 사전규격 전수 수집 메서드** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3-3. 스코어링 파이프라인 통합** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3-4. 스코어러 정규화 어댑터** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3-5. API 응답 확장** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3-6. 프론트엔드 표시** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **5. 수정 대상 파일** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **6. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **7. 검증 계획** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **8. 리스크** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **G2B API 제약** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pre-bid-integration.plan.md) -- 1 connections
  - <- contains <- [[4]]

## Internal Relationships
- 3. 변경 범위 -> contains -> 3-1. G2B API 추가: 발주계획 (`OrderPlanSttusService`) [EXTRACTED]
- 3. 변경 범위 -> contains -> 3-2. 사전규격 전수 수집 메서드 [EXTRACTED]
- 3. 변경 범위 -> contains -> 3-3. 스코어링 파이프라인 통합 [EXTRACTED]
- 3. 변경 범위 -> contains -> 3-4. 스코어러 정규화 어댑터 [EXTRACTED]
- 3. 변경 범위 -> contains -> 3-5. API 응답 확장 [EXTRACTED]
- 3. 변경 범위 -> contains -> 3-6. 프론트엔드 표시 [EXTRACTED]
- 4. 기술 고려사항 -> contains -> G2B API 제약 [EXTRACTED]
- 사전규격 + 발주계획 통합 Plan -> contains -> 1. 배경 및 목적 [EXTRACTED]
- 사전규격 + 발주계획 통합 Plan -> contains -> 2. 현황 분석 [EXTRACTED]
- 사전규격 + 발주계획 통합 Plan -> contains -> 3. 변경 범위 [EXTRACTED]
- 사전규격 + 발주계획 통합 Plan -> contains -> 4. 기술 고려사항 [EXTRACTED]
- 사전규격 + 발주계획 통합 Plan -> contains -> 5. 수정 대상 파일 [EXTRACTED]
- 사전규격 + 발주계획 통합 Plan -> contains -> 6. 구현 순서 [EXTRACTED]
- 사전규격 + 발주계획 통합 Plan -> contains -> 7. 검증 계획 [EXTRACTED]
- 사전규격 + 발주계획 통합 Plan -> contains -> 8. 리스크 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 사전규격 + 발주계획 통합 Plan, 3. 변경 범위, 4. 기술 고려사항를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 pre-bid-integration.plan.md이다.

### Key Facts
- | 항목 | 내용 | |------|------| | Feature | pre-bid-integration | | 버전 | v1.0 | | 작성일 | 2026-03-21 | | 상태 | Plan |
- 3-1. G2B API 추가: 발주계획 (`OrderPlanSttusService`) **파일**: `app/services/g2b_service.py`
- 현재 AI 추천(`/api/bids/scored`) 경로는 **입찰공고(getBidPblancListInfoServc)만** 수집한다. 나라장터 공고 생명주기는 `발주계획 → 사전규격 → 입찰공고` 순서로 진행되므로, 발주계획과 사전규격을 함께 수집하면 **2~4주 더 앞서** 기회를 포착할 수 있다.
- - `SERVICE_PREFIX`에 `"OrderPlanSttusService": "ao"` 추가 - `search_procurement_plans()` 메서드 신규 - 엔드포인트: `OrderPlanSttusService/getOrderPlanSttusListThng` (용역) - 파라미터: `numOfRows`, `pageNo`, `inqryBgnDt`, `inqryEndDt`, `type=json` - 에러 처리: API 미활용 신청 시 500 → graceful skip (사전규격 패턴 동일) -…
- - `fetch_all_pre_specs()` 메서드 신규 — `search_pre_bid_specifications()` 기반 페이지네이션 수집 - 기존 `search_pre_bid_specifications()`는 키워드 필터링 포함 → 전수 수집 시 키워드 없이 호출
