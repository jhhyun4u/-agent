# 용역제안 Coworker — 프로젝트 수주 성공률을 높이는 AI Coworker

## 프로젝트 개요
tenopa 내부 직원이 활용하는 **용역제안 AI 협업 플랫폼**. 용역과제 모니터링과 제안서 공동 작성을 수행하는 **AI Coworker**(에이전트)가 경험 많은 동료처럼 사람과 협업한다. 프로젝트를 거듭할수록 조직 지식(역량·콘텐츠·발주기관·경쟁사·교훈)이 축적되어 다음 제안의 품질이 올라가는 선순환 구조. 부서/팀 단위 운영, 역할 기반 접근 제어, 결재선, 성과 추적 지원.

## 기술 스택
- Python 3.11+ / FastAPI (Backend — Railway/Render)
- Next.js 15+ / React 19+ / TypeScript (Frontend — Vercel)
- LangGraph (StateGraph + interrupt + PostgresSaver)
- Anthropic Claude API (claude-sonnet-4-5-20250929)
- Supabase (PostgreSQL + Auth + RLS + Storage + pgvector)
- Azure AD (Entra ID) — MS365 SSO
- Teams Incoming Webhook — 알림
- UI: shadcn/ui + Tiptap + Recharts
- PyPDF2, python-docx, python-pptx, python-hwpx
- 패키지 관리: uv

## 주요 명령어
```bash
uv sync                              # 의존성 설치
uv run uvicorn app.main:app --reload  # 개발 서버 실행
uv run pytest                         # 테스트 실행
uv run python scripts/seed_data.py    # 시드 데이터 생성
```

## 백엔드 구조 (app/)

### API 라우트
- `app/api/deps.py` — 인증·인가 의존성 (get_current_user, require_role, require_project_access)
- `app/api/routes_auth.py` — 인증 (Azure AD SSO + Supabase Auth)
- `app/api/routes_users.py` — 사용자·조직·팀·참여자·위임 관리
- `app/api/routes_proposal.py` — 제안서 프로젝트 CRUD (3가지 진입 경로)
- `app/api/routes_workflow.py` — 워크플로 제어 (start, state, resume, stream, history, goto, impact)
- `app/api/routes_artifacts.py` — 산출물 조회 + DOCX/HWPX/PPTX 다운로드 + Compliance Matrix + 섹션 재생성 + AI 어시스트
- `app/api/routes_notification.py` — 알림 목록·읽음·설정
- `app/api/routes.py` — 기존 라우터 통합 (v3.1 파이프라인, 팀, G2B, 리소스 등)
- `app/api/routes_bids.py` — 입찰 관리
- `app/api/routes_bid_submission.py` — 투찰 관리 (투찰 기록/확인/상태/이력)

### LangGraph (app/graph/)
- `app/graph/state.py` — ProposalState TypedDict + 14 서브 모델 + Annotated reducers (§3)
- `app/graph/edges.py` — 라우팅 함수 15개: 8개 팩토리(_approval_router) + 7개 개별 (§11, v4.0)
- `app/graph/graph.py` — StateGraph v4.0 (40 노드, A/B 분기 워크플로). 인라인 함수 없이 gate_nodes에서 import
- `app/graph/nodes/gate_nodes.py` — 게이트·Fan-out·훅 (passthrough, fork, convergence, stream1_complete_hook 등)
- `app/graph/nodes/rfp_search.py` — STEP 0: G2B 공고 검색 + AI 적합도 평가 (그래프 외부, API 직접 호출)
- `app/graph/nodes/rfp_fetch.py` — STEP 0→1: G2B 상세 수집 + RFP 업로드 게이트 (그래프 외부)
- `app/graph/nodes/rfp_analyze.py` — STEP 1-①: RFP 분석 + Compliance Matrix
- `app/graph/nodes/research_gather.py` — v3.2: RFP 기반 동적 리서치
- `app/graph/nodes/go_no_go.py` — STEP 1-②: Go/No-Go + 포지셔닝 판정
- `app/graph/nodes/review_node.py` — 공통 리뷰 게이트 (Shipley Color Team) + plan 리뷰 (목차+스토리라인)
- `app/graph/nodes/merge_nodes.py` — plan 병합 (부분 재작업) + storylines→dynamic_sections 동기화
- `app/graph/nodes/strategy_generate.py` — STEP 2: 포지셔닝 기반 제안전략
- `app/graph/nodes/bid_plan.py` — STEP 2.5 (Path B-4B): 입찰가격계획 (PricingEngine + 시나리오)
- `app/graph/nodes/plan_nodes.py` — STEP 3A: 팀/담당/일정/스토리 (4개 병렬) + 가격(plan_price, 그래프 미등록)
- `app/graph/nodes/proposal_nodes.py` — STEP 4A: 순차 섹션 작성 + 자가진단
- `app/graph/nodes/ppt_nodes.py` — STEP 5A: 발표전략 + PPT toc/visual_brief/storyboard
- `app/graph/nodes/submission_nodes.py` — Path B: 제출서류 계획(3B) + 산출내역서(5B) + 제출확인(6B)
- `app/graph/nodes/evaluation_nodes.py` — 6A 모의평가 + 7 평가결과 + 8 Closing

### 서비스
- `app/services/claude_client.py` — Claude API 클라이언트 (JSON 파싱 + 스트리밍)
- `app/services/auth_service.py` — Azure AD 프로필 동기화, 사용자 관리
- `app/services/approval_chain.py` — 예산 기준 결재선 자동 구성 + 위임
- `app/services/audit_service.py` — 감사 로그
- `app/services/compliance_tracker.py` — Compliance Matrix 생애주기 (초안→전략→AI 체크)
- `app/services/docx_builder.py` — DOCX 빌더 (케이스 A/B + Markdown → DOCX)
- `app/services/bid_market_research.py` — 시장 조사 (유사과제 낙찰정보 확인 + G2B 크롤링 보강)
- `app/services/bid_handoff.py` — 투찰 핸드오프 (확정가 DB persist + artifact 저장 + 투찰 기록 + 이력 추적)
- `app/services/notification_service.py` — Teams Webhook + 인앱 알림 (승인/마감/AI 완료/입찰가확정/투찰완료)
- `app/services/kb_updater.py` — 성과 기반 KB 자동 업데이트 (수주→역량, 패찰→경쟁사, 교훈→임베딩)
- `app/services/hwpx_service.py` — HWPX 서비스 래퍼 (hwpxskill 기반: 빌드, 검증, 양식 분석, 쪽수 가드)
- `app/services/hwpx/` — hwpxskill 모듈 (build_hwpx, analyze_template, validate, page_guard + templates)
- `app/services/rfp_parser.py` — PDF/HWP/HWPX 파싱
- `app/services/session_manager.py` — 세션 관리
- `app/services/token_manager.py` — STEP별 토큰 예산 관리 + 컨텍스트 빌더 (§21)
- `app/services/ai_status_manager.py` — AI 작업 상태 추적 + 하트비트 + DB 로깅 (§22)
- `app/services/section_lock.py` — 섹션 동시 편집 잠금 (§24, 5분 자동 해제)
- `app/services/scheduled_monitor.py` — G2B 정기 모니터링 스케줄러 (§25-2, 평일 08~18시 매시 정각)
- `app/services/source_tagger.py` — 출처 태깅 + 근거 비율 분석 + 신뢰성 평가 (§16-3-2)

### 모델
- `app/models/schemas.py` — 제안서 관련 Pydantic 스키마
- `app/models/user_schemas.py` — 사용자·조직 Pydantic 스키마

### 핵심 파일
- `app/main.py` — FastAPI 앱 + TenopAPIError 핸들러
- `app/config.py` — 환경 설정 (Supabase, Azure AD, AI 등)
- `app/exceptions.py` — 표준 에러 코드 체계 (§12-0)
- `app/utils/supabase_client.py` — Supabase 비동기 클라이언트 (service_role + user JWT)

### 프롬프트 (app/prompts/)
- `app/prompts/strategy.py` — 포지셔닝 매트릭스 + SWOT + 시나리오 + Win Theme
- `app/prompts/plan.py` — 5개 plan 노드 프롬프트 (team/assign/schedule/story/price). plan_story는 목차 기획 + 스토리라인 설계
- `app/prompts/proposal_prompts.py` — 케이스 A/B + 자가진단 + PPT + 발표전략
- `app/prompts/section_prompts.py` — 10개 섹션 유형별 전문 프롬프트 + 케이스 B + 자동 분류 + 스토리라인 주입
- `app/prompts/trustworthiness.py` — 데이터 신뢰성 6대 규칙 + 출처 태그 형식 + 금지 표현 (§16-3-1)

### 추가 서비스 (Phase C~E / 레거시)
- `app/services/g2b_service.py` — G2B API 클라이언트 (공고 검색·낙찰정보·캐싱)
- `app/services/bid_recommender.py` — AI 입찰 추천·적격성 분석
- `app/services/pptx_builder.py` — PPTX 빌더 (그래프 연동, 경량)
- `app/services/presentation_generator.py` — 발표 자료 3단계 JSON 생성
- `app/services/presentation_pptx_builder.py` — 컨설팅급 PPTX 렌더링 (1,391줄)
- `app/services/hwpx_builder.py` — ⚠️ v3.1 레거시 HWPX 빌더 (python-hwpx API). v3.5에서는 hwpx_service.py 사용
- `app/services/knowledge_search.py` — 통합 KB 검색
- `app/services/phase_executor.py` — ⚠️ 레거시 v3.1 파이프라인 (LangGraph로 대체됨)
- `app/services/phase_prompts.py` — ⚠️ 레거시 v3.1 프롬프트
- `app/api/routes_v31.py` — ⚠️ 레거시 v3.1 API (/api/v3.1/*)
- `app/api/routes_analytics.py` — 분석 대시보드 집계 (Phase 4: win-rate, team-performance, competitor 추가)
- `app/api/routes_calendar.py` — RFP 일정 관리
- `app/api/routes_presentation.py` — 발표 자료 생성
- `app/api/routes_resources.py` — 섹션 라이브러리·아카이브
- `app/api/routes_stats.py` — 낙찰률 통계
- `app/api/routes_templates.py` — 공통서식 라이브러리

## DB 스키마
- `database/schema_v3.4.sql` — v3.4 통합 스키마 (§15 전체)
- `database/migrations/004_performance_views.sql` — Phase 4: proposal_results + Materialized View (mv_team_performance, mv_positioning_accuracy)
- `database/archive/` — 레거시 SQL (schema.sql, schema_v2.sql, supabase_schema.sql 등)

## 코드 컨벤션
- 한국어 docstring 및 주석
- Pydantic v2 스타일 사용
- async/await 패턴 (FastAPI)
- 에러: TenopAPIError 기반 표준 에러 코드 사용 (HTTPException 점진 교체)
- 인증: `app/api/deps.py`의 get_current_user / require_role 사용

## 설계 문서
- 요구사항: `docs/01-plan/features/proposal-agent-v1.requirements.md` (v4.9)
- 설계: `docs/02-design/features/proposal-agent-v1/_index.md` (v3.6, archived, modular 18 files)
- 갭 분석: `docs/03-analysis/features/proposal-agent-v1.analysis.md` (97%)
