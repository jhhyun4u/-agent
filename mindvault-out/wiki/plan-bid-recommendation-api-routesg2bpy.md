# Plan: bid-recommendation & API 역할 분담 (기존 routes_g2b.py와 구분)
Cohesion: 0.14 | Nodes: 14

## Key Nodes
- **Plan: bid-recommendation** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\bid-recommendation\bid-recommendation.plan.md) -- 10 connections
  - -> contains -> [[f-01-bidfetcher]]
  - -> contains -> [[f-02]]
  - -> contains -> [[f-03-ai-bidrecommender-2]]
  - -> contains -> [[f-04-api-routesbids]]
  - -> contains -> [[f-05-ui-frontend]]
  - -> contains -> [[f-06-db]]
  - -> contains -> [[g2bservice]]
  - -> contains -> [[api]]
  - -> contains -> [[claude]]
  - -> contains -> [[api-routesg2bpy]]
- **API 역할 분담 (기존 routes_g2b.py와 구분)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\bid-recommendation\bid-recommendation.plan.md) -- 2 connections
  - -> has_code_example -> [[env]]
  - <- contains <- [[plan-bid-recommendation]]
- **F-03: AI 분석 엔진 (bid_recommender) — 2단계 구조** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\bid-recommendation\bid-recommendation.plan.md) -- 2 connections
  - -> has_code_example -> [[json]]
  - <- contains <- [[plan-bid-recommendation]]
- **F-06: DB 스키마 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\bid-recommendation\bid-recommendation.plan.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[plan-bid-recommendation]]
- **env** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\bid-recommendation\bid-recommendation.plan.md) -- 1 connections
  - <- has_code_example <- [[api-routesg2bpy]]
- **json** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\bid-recommendation\bid-recommendation.plan.md) -- 1 connections
  - <- has_code_example <- [[f-03-ai-bidrecommender-2]]
- **sql** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\bid-recommendation\bid-recommendation.plan.md) -- 1 connections
  - <- has_code_example <- [[f-06-db]]
- **나라장터 API 파라미터 전략** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\bid-recommendation\bid-recommendation.plan.md) -- 1 connections
  - <- contains <- [[plan-bid-recommendation]]
- **Claude 매칭 비용 최적화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\bid-recommendation\bid-recommendation.plan.md) -- 1 connections
  - <- contains <- [[plan-bid-recommendation]]
- **F-01: 나라장터 공고 수집 (bid_fetcher)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\bid-recommendation\bid-recommendation.plan.md) -- 1 connections
  - <- contains <- [[plan-bid-recommendation]]
- **F-02: 팀 프로필 + 검색 조건 관리** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\bid-recommendation\bid-recommendation.plan.md) -- 1 connections
  - <- contains <- [[plan-bid-recommendation]]
- **F-04: 추천 공고 API (routes_bids)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\bid-recommendation\bid-recommendation.plan.md) -- 1 connections
  - <- contains <- [[plan-bid-recommendation]]
- **F-05: 추천 공고 UI (frontend)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\bid-recommendation\bid-recommendation.plan.md) -- 1 connections
  - <- contains <- [[plan-bid-recommendation]]
- **기존 G2BService 재사용 전략** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\bid-recommendation\bid-recommendation.plan.md) -- 1 connections
  - <- contains <- [[plan-bid-recommendation]]

## Internal Relationships
- API 역할 분담 (기존 routes_g2b.py와 구분) -> has_code_example -> env [EXTRACTED]
- F-03: AI 분석 엔진 (bid_recommender) — 2단계 구조 -> has_code_example -> json [EXTRACTED]
- F-06: DB 스키마 추가 -> has_code_example -> sql [EXTRACTED]
- Plan: bid-recommendation -> contains -> F-01: 나라장터 공고 수집 (bid_fetcher) [EXTRACTED]
- Plan: bid-recommendation -> contains -> F-02: 팀 프로필 + 검색 조건 관리 [EXTRACTED]
- Plan: bid-recommendation -> contains -> F-03: AI 분석 엔진 (bid_recommender) — 2단계 구조 [EXTRACTED]
- Plan: bid-recommendation -> contains -> F-04: 추천 공고 API (routes_bids) [EXTRACTED]
- Plan: bid-recommendation -> contains -> F-05: 추천 공고 UI (frontend) [EXTRACTED]
- Plan: bid-recommendation -> contains -> F-06: DB 스키마 추가 [EXTRACTED]
- Plan: bid-recommendation -> contains -> 기존 G2BService 재사용 전략 [EXTRACTED]
- Plan: bid-recommendation -> contains -> 나라장터 API 파라미터 전략 [EXTRACTED]
- Plan: bid-recommendation -> contains -> Claude 매칭 비용 최적화 [EXTRACTED]
- Plan: bid-recommendation -> contains -> API 역할 분담 (기존 routes_g2b.py와 구분) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: bid-recommendation, API 역할 분담 (기존 routes_g2b.py와 구분), F-03: AI 분석 엔진 (bid_recommender) — 2단계 구조를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 bid-recommendation.plan.md이다.

### Key Facts
- 메타 정보 | 항목 | 내용 | |------|------| | Feature | bid-recommendation | | 작성일 | 2026-03-08 | | 목표 | 조달청 나라장터 공고를 수집하고, 팀/개인 역량과 매칭하여 최적 사업 공고를 추천 |
- 자격요건 판단 한계 및 대응 | 공고 유형 | 자격요건 접근성 | 처리 방식 | |-----------|---------------|----------| | 상세 API에 텍스트 있음 | 분석 가능 | 정상 판정 | | "첨부파일 참조" 문구만 있음 | 분석 불가 | `ambiguous` + "원문 확인 필요" | | 상세 API 응답 없음 | 분석 불가 | `ambiguous` + "상세 정보 미제공" |
- **목표:** Claude API로 ① 자격 판정 → ② 매칭 점수 순서로 분석. 자격 불충족 공고는 추천에서 제외
- **목표:** 공고 수집·추천 결과 영구 저장
- ```env DATA_GO_KR_API_KEY=...   # 공공데이터포털 API 인증키 ```
