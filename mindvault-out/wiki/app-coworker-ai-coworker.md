# 백엔드 구조 (app/) & 용역제안 Coworker — 프로젝트 수주 성공률을 높이는 AI Coworker
Cohesion: 0.25 | Nodes: 8

## Key Nodes
- **백엔드 구조 (app/)** (C:\project\tenopa proposer\CLAUDE.md) -- 5 connections
  - -> contains -> [[api]]
  - -> contains -> [[langgraph-appgraph]]
  - -> contains -> [[appprompts]]
  - -> contains -> [[phase-ce]]
  - <- contains <- [[coworker-ai-coworker]]
- **용역제안 Coworker — 프로젝트 수주 성공률을 높이는 AI Coworker** (C:\project\tenopa proposer\CLAUDE.md) -- 3 connections
  - -> has_code_example -> [[bash]]
  - -> contains -> [[app]]
  - -> contains -> [[db]]
- **bash** (C:\project\tenopa proposer\CLAUDE.md) -- 1 connections
  - <- has_code_example <- [[coworker-ai-coworker]]
- **API 라우트** (C:\project\tenopa proposer\CLAUDE.md) -- 1 connections
  - <- contains <- [[app]]
- **프롬프트 (app/prompts/)** (C:\project\tenopa proposer\CLAUDE.md) -- 1 connections
  - <- contains <- [[app]]
- **DB 스키마** (C:\project\tenopa proposer\CLAUDE.md) -- 1 connections
  - <- contains <- [[coworker-ai-coworker]]
- **LangGraph (app/graph/)** (C:\project\tenopa proposer\CLAUDE.md) -- 1 connections
  - <- contains <- [[app]]
- **추가 서비스 (Phase C~E / 레거시)** (C:\project\tenopa proposer\CLAUDE.md) -- 1 connections
  - <- contains <- [[app]]

## Internal Relationships
- 백엔드 구조 (app/) -> contains -> API 라우트 [EXTRACTED]
- 백엔드 구조 (app/) -> contains -> LangGraph (app/graph/) [EXTRACTED]
- 백엔드 구조 (app/) -> contains -> 프롬프트 (app/prompts/) [EXTRACTED]
- 백엔드 구조 (app/) -> contains -> 추가 서비스 (Phase C~E / 레거시) [EXTRACTED]
- 용역제안 Coworker — 프로젝트 수주 성공률을 높이는 AI Coworker -> has_code_example -> bash [EXTRACTED]
- 용역제안 Coworker — 프로젝트 수주 성공률을 높이는 AI Coworker -> contains -> 백엔드 구조 (app/) [EXTRACTED]
- 용역제안 Coworker — 프로젝트 수주 성공률을 높이는 AI Coworker -> contains -> DB 스키마 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 백엔드 구조 (app/), 용역제안 Coworker — 프로젝트 수주 성공률을 높이는 AI Coworker, bash를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 CLAUDE.md이다.

### Key Facts
- API 라우트 - `app/api/deps.py` — 인증·인가 의존성 (get_current_user, require_role, require_project_access) - `app/api/routes_auth.py` — 인증 (Azure AD SSO + Supabase Auth) - `app/api/routes_users.py` — 사용자·조직·팀·참여자·위임 관리 - `app/api/routes_proposal.py` — 제안서 프로젝트 CRUD (3가지 진입 경로) - `app/api/routes_workflow.py`…
- 프로젝트 개요 tenopa 내부 직원이 활용하는 **용역제안 AI 협업 플랫폼**. 용역과제 모니터링과 제안서 공동 작성을 수행하는 **AI Coworker**(에이전트)가 경험 많은 동료처럼 사람과 협업한다. 프로젝트를 거듭할수록 조직 지식(역량·콘텐츠·발주기관·경쟁사·교훈)이 축적되어 다음 제안의 품질이 올라가는 선순환 구조. 부서/팀 단위 운영, 역할 기반 접근 제어, 결재선, 성과 추적 지원.
- 주요 명령어 ```bash uv sync                              # 의존성 설치 uv run uvicorn app.main:app --reload  # 개발 서버 실행 uv run pytest                         # 테스트 실행 uv run python scripts/seed_data.py    # 시드 데이터 생성 ```
- LangGraph (app/graph/) - `app/graph/state.py` — ProposalState TypedDict + 16 서브 모델 + Annotated reducers (§3, v4.0: DiagnosisResult + GapReport 추가) - `app/graph/edges.py` — 라우팅 함수 16개: 8개 팩토리(_approval_router) + 8개 개별 (§11, v4.0: route_after_gap_analysis_review 추가) - `app/graph/graph.py` —…
- 추가 서비스 (Phase C~E / 레거시) - `app/services/g2b_service.py` — G2B API 클라이언트 (공고 검색·낙찰정보·캐싱) - `app/services/bid_recommender.py` — AI 입찰 추천·적격성 분석 - `app/services/pptx_builder.py` — PPTX 빌더 (그래프 연동, 경량) - `app/services/presentation_generator.py` — 발표 자료 3단계 JSON 생성 -…
