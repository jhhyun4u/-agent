# 아키텍처 개요 + 디렉토리 구조 + 구현 순서

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [02-state-schema.md](02-state-schema.md), [03-graph-definition.md](03-graph-definition.md)
> **원본 섹션**: §1, §2, §19

---

## 1. 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Frontend (Next.js · Vercel)                        │
│  역할별 대시보드 / 워크플로 / 리뷰 패널 / 산출물 뷰어 / 피드백     │
│  공고 검색·추천 / 포지셔닝 선택 / Go/No-Go / 성과 대시보드          │
│  ★ v3.0: KB 관리 (콘텐츠·발주기관·경쟁사·교훈·통합 검색)           │
│  ★ v3.0: AI 상태 패널 / 섹션 잠금 표시 / 회고 워크시트             │
│  ★ v3.4: 인브라우저 편집기(Tiptap) / 모의평가 시각화 / 분석 대시보드│
│  ★ v3.4: UI 인프라 (shadcn/ui + Recharts)                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP (REST API) + SSE (스트리밍)
                             │ JWT (Supabase Auth + Azure AD)
┌────────────────────────────▼────────────────────────────────────────┐
│                Backend (FastAPI · Railway/Render)                    │
│                                                                      │
│   ┌─── Auth Middleware (JWT 검증 + 역할 확인) ────────────────────┐  │
│   │                                                                │  │
│   │   ┌──────────────────────────────────────────────────────┐    │  │
│   │   │              LangGraph StateGraph                    │    │  │
│   │   │                                                      │    │  │
│   │   │  [rfp_search] → [review_search] → [rfp_fetch]       │    │  │
│   │   │    → [rfp_analyze] → [review_rfp]                    │    │  │
│   │   │    → [research_gather]  ★ v3.2: RFP-적응형 사전조사   │    │  │
│   │   │    → [go_no_go] → [review_gng]                       │    │  │
│   │   │    → [strategy_generate] → [review_strategy]         │    │  │
│   │   │    → [plan_*×5] → [plan_merge] → [review]           │    │  │
│   │   │    → [proposal_*×N] → [merge] → [self_review]       │    │  │
│   │   │      → [review_proposal]                              │    │  │
│   │   │    → [presentation_strategy] ★ v3.2: 발표전략 노드   │    │  │
│   │   │    → [ppt_*×N] → [merge] → [review_final]           │    │  │
│   │   │                                                      │    │  │
│   │   │  interrupt() ←→ FastAPI /resume (역할 검증 포함)     │    │  │
│   │   │  ★ v3.0: 각 노드에서 KB 참조 (knowledge_search)     │    │  │
│   │   │  ★ v3.0: token_manager 컨텍스트 예산 적용            │    │  │
│   │   └──────────────────────────────────────────────────────┘    │  │
│   │                                                                │  │
│   │   ┌──── Services Layer ──────────────────────────────────┐   │  │
│   │   │  Notification Service (Teams + 인앱)                   │   │  │
│   │   │  ★ v3.0: AI Status Manager (진행률·Heartbeat)         │   │  │
│   │   │  ★ v3.0: Token Manager (Prompt Caching·예산 관리)     │   │  │
│   │   │  ★ v3.0: Section Lock (동시 편집 충돌 방지)           │   │  │
│   │   │  ★ v3.0: Scheduled Monitor (G2B 자동 모니터링)        │   │  │
│   │   └───────────────────────────────────────────────────────┘   │  │
│   └────────────────────────────────────────────────────────────────┘  │
│                             │                                        │
│   ┌─────────────────────────▼──────────────────────────────────┐    │
│   │      Supabase (PostgreSQL + Auth + Storage + RLS)           │    │
│   │      ┌──────────────────┬──────────────────┐               │    │
│   │      │ App DB (RLS)     │ LangGraph        │               │    │
│   │      │ 조직·사용자·     │ PostgresSaver    │               │    │
│   │      │ 제안·산출물·     │ Checkpointer     │               │    │
│   │      │ 성과·알림        │                  │               │    │
│   │      ├──────────────────┘                  │               │    │
│   │      │ ★ v3.0: KB 테이블 (pgvector)        │               │    │
│   │      │ content_library · client_intel ·     │               │    │
│   │      │ competitors · lessons_learned        │               │    │
│   │      │ (embedding vector(1536) 컬럼)        │               │    │
│   │      └─────────────────────────────────────┘               │    │
│   └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                             │
      ┌──────────────┬───────┴───────┬──────────────┬──────────────┐
      ▼              ▼               ▼              ▼              ▼
   Claude API    G2B API       Azure AD       Teams Webhook   OpenAI API
  (Anthropic)   (나라장터)    (Entra ID)     (알림 발송)    ★ v3.0 Embedding
```

> **v2.0 변경**: SQLite → **Supabase PostgreSQL** 전환. LangGraph checkpointer도 `PostgresSaver` 사용.
> Supabase Auth가 Azure AD(Entra ID)를 OAuth provider로 연동하여 MS365 SSO 구현.
> 모든 테이블에 RLS 정책 적용으로 조직·역할 기반 데이터 격리 보장.
> **v3.0 변경**: Knowledge Base 테이블에 **pgvector** 확장으로 시맨틱 검색 지원. **OpenAI Embedding API** (text-embedding-3-small, 1536차원) 연동 추가. Services Layer에 AI 상태 관리·토큰 예산·섹션 잠금·자동 모니터링 서비스 추가.

---

## 2. 디렉토리 구조

```
app/
├── main.py                         # FastAPI 앱 진입점
├── config.py                       # 환경변수 설정
│
├── api/
│   ├── routes_auth.py              # ★ 인증 (Azure AD SSO 콜백, 세션 관리)
│   ├── routes_users.py             # ★ 사용자·조직·팀 CRUD + 역할 관리
│   ├── routes_proposal.py          # 제안 프로젝트 CRUD (팀 귀속, 참여자 배정)
│   ├── routes_workflow.py          # 워크플로 실행·재개·상태 조회 + SSE
│   ├── routes_artifact.py          # 산출물 조회·다운로드 (중간 버전 포함)
│   ├── routes_capability.py        # 자사 역량 DB CRUD
│   ├── routes_content.py           # ★ v3.0: 콘텐츠 라이브러리 CRUD + 시맨틱 검색
│   ├── routes_client_intel.py      # ★ v3.0: 발주기관 DB CRUD
│   ├── routes_competitor.py        # ★ v3.0: 경쟁사 DB CRUD
│   ├── routes_lessons.py           # ★ v3.0: 교훈 아카이브 + 회고 워크시트
│   ├── routes_kb_search.py         # ★ v3.0: 통합 KB 검색 (시맨틱 + 키워드)
│   ├── routes_kb_export.py         # ★ v3.0: KB 데이터 내보내기 (CSV/Excel)
│   ├── routes_g2b.py               # G2B 공고 검색·낙찰정보
│   ├── routes_dashboard.py         # ★ 역할별 대시보드 API (팀원/팀장/본부장/경영진)
│   ├── routes_notification.py      # ★ 알림 목록·설정 API
│   ├── routes_ai_status.py         # ★ v3.0: AI 실행 상태 조회·중단·재시도 API
│   ├── routes_template.py          # ★ v3.0: 회사 DOCX/PPTX 템플릿 관리 (admin)
│   ├── routes_analytics.py         # ★ v3.4: 분석 대시보드 집계 API (실패 원인·포지셔닝·월별·기관별)
│   └── deps.py                     # ★ 의존성 주입 (현재 사용자, 역할 검증, 결재선 확인, 입력 검증)
│
├── graph/
│   ├── state.py                    # ProposalState (TypedDict + Annotated)
│   ├── graph.py                    # LangGraph StateGraph 정의
│   ├── nodes/
│   │   ├── rfp_search.py           # STEP 0: G2B 공고 검색 + AI 추천
│   │   ├── rfp_fetch.py            # STEP 0→1 전환: G2B 상세 수집 + RFP 파일 업로드 게이트
│   │   ├── rfp_analyze.py          # STEP 1-①: RFP 분석 + Compliance Matrix 초안
│   │   ├── research_gather.py     # ★ v3.2: STEP 1-①→②: RFP-적응형 사전조사
│   │   ├── go_no_go.py             # STEP 1-②: Go/No-Go + 포지셔닝 (RFP 분석 이후)
│   │   ├── strategy_generate.py    # STEP 2: 포지셔닝 기반 제안전략
│   │   ├── plan_nodes.py           # STEP 3: 팀/담당/일정/스토리/가격 (선택적 재실행)
│   │   ├── proposal_nodes.py       # STEP 4: 섹션별 노드 (케이스 A/B 분기)
│   │   ├── self_review.py          # STEP 4: AI 자가진단 (자동 개선 루프)
│   │   ├── presentation_strategy.py  # ★ v3.2: STEP 4→5: 발표전략 수립 (조건부)
│   │   ├── ppt_nodes.py            # STEP 5: 슬라이드별 노드
│   │   ├── merge_nodes.py          # 병렬 결과 병합 (plan/proposal/ppt)
│   │   └── review_node.py          # 공통: Human 리뷰 게이트 (★ 결재선 기반 승인 포함)
│   └── edges.py                    # Conditional Edge 라우팅 함수
│
├── services/
│   ├── rfp_parser.py               # PDF/HWP/HWPX 파싱 (+ HWP fallback)
│   ├── g2b_client.py               # G2B API 클라이언트
│   ├── claude_client.py            # Anthropic API 래퍼
│   ├── capability_store.py         # 자사 역량 DB 접근 계층
│   ├── content_library.py          # ★ v3.0: 콘텐츠 라이브러리 서비스 (CRUD + 품질 점수)
│   ├── client_intelligence.py      # ★ v3.0: 발주기관 DB 서비스
│   ├── competitor_intelligence.py  # ★ v3.0: 경쟁사 DB 서비스
│   ├── knowledge_search.py         # ★ v3.0: 통합 KB 검색 (pgvector 시맨틱 + 키워드)
│   ├── embedding_service.py        # ★ v3.0: 임베딩 생성 (OpenAI text-embedding-3-small)
│   ├── token_manager.py            # ★ v3.0: 토큰 예산 관리 + Prompt Caching 제어
│   ├── ai_status_manager.py        # ★ v3.0: AI 실행 상태·Heartbeat·진행률 관리
│   ├── section_lock.py             # ★ v3.0: 동시 편집 섹션 잠금 관리
│   ├── input_validator.py          # ★ v3.0: 입력 검증 + 파일 보안 (VAL-01~07)
│   ├── compliance_tracker.py       # Compliance Matrix 생애주기 관리
│   ├── docx_builder.py             # DOCX 빌더 (케이스 A/B 분기 + 회사 템플릿)
│   ├── pptx_builder.py             # PPTX 빌더 (+ 회사 마스터 슬라이드)
│   ├── auth_service.py             # ★ Azure AD OAuth + Supabase Auth 연동
│   ├── approval_chain.py           # ★ 결재선 관리 (예산 기준 + 자기결재 방지)
│   ├── notification_service.py     # ★ Teams Webhook + 인앱 알림 발송 (AI 완료/오류/무응답 포함)
│   ├── scheduled_monitor.py        # ★ v3.0: 주기적 G2B 자동 모니터링 (SRC-11)
│   └── performance_tracker.py      # ★ 성과 추적 (수주율·건수·소요일 집계)
│
├── prompts/
│   ├── rfp_search.py               # 공고 검색·추천 프롬프트
│   ├── rfp_analysis.py             # RFP 분석 프롬프트
│   ├── go_no_go.py                 # Go/No-Go + 포지셔닝 프롬프트
│   ├── strategy.py                 # 포지셔닝 기반 제안전략 프롬프트
│   ├── plan.py                     # 제안계획 프롬프트
│   ├── proposal_sections.py        # 정성제안서 섹션별 프롬프트 (케이스 A/B)
│   ├── self_review.py              # AI 자가진단 프롬프트
│   ├── research_gather.py          # ★ v3.2: RFP-적응형 사전조사 프롬프트
│   ├── presentation_strategy.py    # ★ v3.2: 발표전략 프롬프트
│   └── ppt.py                      # PPT 프롬프트 (★ v3.2: 프롬프트 신규 작성)
│
└── models/
    ├── schemas.py                  # Pydantic 스키마 (API 요청/응답)
    └── db.py                       # ★ Supabase PostgreSQL 연결 (supabase-py)

frontend/
├── app/
│   ├── login/page.tsx              # ★ Azure AD SSO 로그인
│   ├── page.tsx                    # 역할별 대시보드 (리다이렉트)
│   ├── dashboard/
│   │   ├── member/page.tsx         # ★ 팀원 대시보드 (내 프로젝트)
│   │   ├── lead/page.tsx           # ★ 팀장 대시보드 (팀 파이프라인)
│   │   ├── director/page.tsx       # ★ 본부장 대시보드 (본부 현황 + 결재)
│   │   ├── executive/page.tsx      # ★ 경영진 대시보드 (전사 KPI)
│   │   └── admin/page.tsx          # ★ 관리자 (사용자·조직 관리)
│   ├── capability/page.tsx         # 역량 DB 관리 (독립 페이지)
│   ├── kb/
│   │   ├── content/page.tsx        # ★ v3.0: 콘텐츠 라이브러리 관리
│   │   ├── clients/page.tsx        # ★ v3.0: 발주기관 DB 관리
│   │   ├── competitors/page.tsx    # ★ v3.0: 경쟁사 DB 관리
│   │   ├── lessons/page.tsx        # ★ v3.0: 교훈 아카이브 조회
│   │   ├── search/page.tsx         # ★ v3.0: 통합 KB 검색
│   │   ├── labor-rates/page.tsx    # ★ v3.4: 원가기준(노임단가) CRUD
│   │   └── market-prices/page.tsx  # ★ v3.4: 낙찰가 벤치마크 CRUD
│   ├── admin/
│   │   ├── users/page.tsx          # ★ v3.0: 사용자 라이프사이클 관리
│   │   ├── onboarding/page.tsx     # ★ v3.0: 시스템 온보딩 체크리스트
│   │   └── templates/page.tsx      # ★ v3.0: 회사 DOCX/PPTX 템플릿 관리
│   ├── projects/[id]/
│   │   ├── page.tsx                # 워크플로 대시보드
│   │   ├── edit/page.tsx           # ★ v3.4: 인브라우저 제안서 편집기 (Tiptap 3컬럼)
│   │   ├── evaluation/page.tsx     # ★ v3.4: 모의평가 결과 시각화 (레이더 차트 + 점수 카드)
│   │   └── review/[step]/
│   │       └── page.tsx            # 리뷰 패널 (단계별)
│   ├── analytics/page.tsx          # ★ v3.4: 분석 대시보드 (실패 원인, 포지셔닝별 수주율)
├── components/
│   ├── WorkflowProgress.tsx        # 단계별 진행 상태 바 (STEP 0~5)
│   ├── RfpSearchPanel.tsx          # 공고 검색·추천 리스트 + 관심과제 선정
│   ├── GoNoGoPanel.tsx             # Go/No-Go + 포지셔닝 선택 UI (STEP 1-② 이후)
│   ├── PositioningBadge.tsx        # 포지셔닝 유형 배지
│   ├── PositioningChangeGuide.tsx  # 포지셔닝 변경 시 영향 미리보기
│   ├── ReviewPanel.tsx             # 리뷰 패널 (좌: 산출물, 우: 피드백)
│   ├── ApprovalChainStatus.tsx     # ★ 결재선 현황 표시 (팀장→본부장→경영진)
│   ├── QuickApproveButton.tsx      # 빠른 승인 버튼 (피드백 생략)
│   ├── ArtifactViewer.tsx          # 단계별 산출물 렌더러
│   ├── FeedbackForm.tsx            # 피드백·코멘트 입력
│   ├── ParallelProgress.tsx        # 병렬 작업 진행 + 완료 항목 선검토
│   ├── ImpactPreview.tsx           # 이전 단계 이동 시 영향 범위 표시
│   ├── InlineCapabilityEditor.tsx  # 워크플로 내 역량 DB 인라인 편집
│   ├── ComplianceMatrixView.tsx    # Compliance Matrix 시각화
│   ├── PerformanceChart.tsx        # ★ 성과 차트 (수주율, 건수, 추이)
│   ├── NotificationBell.tsx        # ★ 알림 벨 + 드롭다운
│   ├── TeamPipelineView.tsx        # ★ 팀 파이프라인 (STEP별 프로젝트 분포)
│   ├── AiStatusPanel.tsx           # ★ v3.0: AI Coworker 상태 패널 (진행률·Heartbeat)
│   ├── KbSearchBar.tsx             # ★ v3.0: 통합 KB 검색 바
│   ├── ContentLibraryView.tsx      # ★ v3.0: 콘텐츠 라이브러리 뷰어
│   ├── SectionLockIndicator.tsx    # ★ v3.0: 섹션 편집 잠금 표시
│   ├── KbConfidenceBadge.tsx       # ★ v3.0: KB 참조 신뢰도 배지 (KB기반/일반지식/혼합)
│   ├── RetrospectWorksheet.tsx     # ★ v3.0: 회고 워크시트 UI
│   ├── ProposalEditor.tsx         # ★ v3.4: 인브라우저 제안서 편집기 (Tiptap 3컬럼 레이아웃)
│   ├── EditorTocPanel.tsx         # ★ v3.4: 에디터 좌측 목차 + Compliance Matrix 패널
│   ├── EditorAiPanel.tsx          # ★ v3.4: 에디터 우측 AI 어시스턴트 패널
│   ├── EvaluationView.tsx         # ★ v3.4: 모의평가 결과 시각화 (점수 카드 + 레이더 차트)
│   ├── EvaluationRadarChart.tsx   # ★ v3.4: 4축 100점 레이더 차트 (Recharts)
│   ├── AnalyticsPage.tsx          # ★ v3.4: 분석 대시보드 (실패 원인 + 포지셔닝 수주율)
│   ├── PhaseGraph.tsx             # ★ v3.4: 수평 Phase 그래프 (병렬 분기 + 체크포인트 배지)
│   ├── LaborRatesTable.tsx        # ★ v3.4: 원가기준(노임단가) CRUD 테이블
│   └── MarketPricesTable.tsx      # ★ v3.4: 낙찰가 벤치마크 CRUD 테이블
├── components/ui/                  # ★ v3.4: shadcn/ui 컴포넌트 (자동 생성)
│   ├── button.tsx
│   ├── dialog.tsx
│   ├── tabs.tsx
│   ├── select.tsx
│   ├── badge.tsx
│   ├── toast.tsx
│   ├── switch.tsx
│   ├── accordion.tsx
│   └── ...                        # shadcn/ui CLI로 추가
└── lib/
    ├── api.ts                      # API 클라이언트 (★ JWT 자동 첨부)
    ├── auth.ts                     # ★ Supabase Auth 클라이언트 (Azure AD SSO)
    ├── sse.ts                      # SSE 이벤트 수신 (자동 재연결)
    └── utils.ts                    # ★ v3.4: shadcn/ui 유틸리티 (cn 함수)
```

---

## 19. 구현 순서 (Phase) — v2.0 개정

> **v2.0 변경**: Phase 0(인프라·인증)을 신설하고, 전사 기능을 Phase별로 분산 배치.

```
Phase 0 — ★ 인프라·인증 기반 (v2.0 신설)
  ├── Supabase 프로젝트 생성 + PostgreSQL 스키마 (§15 전체)
  ├── Supabase Auth + Azure AD(Entra ID) OAuth 연동
  ├── RLS 정책 적용 (organizations → divisions → teams → users)
  ├── FastAPI JWT 미들웨어 + 역할 기반 접근 제어 (deps.py)
  ├── Next.js Supabase Auth 클라이언트 + 로그인 페이지
  ├── 사용자·조직·팀 CRUD API (routes_users.py)
  └── 초기 데이터 시딩 (조직 구조, 테스트 사용자)

Phase 1 — 핵심 뼈대 + 결재선
  ├── LangGraph 그래프 (TypedDict, 선택적 fan-out, interrupt)
  ├── AsyncPostgresSaver (LangGraph Checkpointer)
  ├── FastAPI: /start, /state, /resume, /from-rfp, /from-search
  ├── rfp_search 노드 (G2B 공고 검색 + AI 추천 + route_start 분기)
  ├── rfp_fetch 노드 (G2B 상세 수집 + RFP 업로드 게이트, 하이브리드)
  ├── rfp_analyze 노드 (PDF + Compliance Matrix 초안)
  ├── go_no_go 노드 (포지셔닝 + lite/full 모드)
  ├── review_node (★ 결재선 + 빠른 승인 + 부분 재작업 + 포지셔닝 변경)
  ├── 자사 역량 DB CRUD API
  ├── Compliance Matrix 기본 생애주기
  └── ★ 프로젝트 생성 시 team_id 자동 귀속 + 참여자 배정 API

Phase 2 — 전략·계획 + 팀 협업
  ├── strategy_generate (포지셔닝 매트릭스 + 대안 2가지)
  ├── plan 5개 병렬 노드 (선택적 fan-out)
  ├── SSE 스트리밍 + 프론트엔드 자동 재연결
  ├── 프론트엔드: RfpSearchPanel + GoNoGoPanel + PositioningBadge
  ├── 프론트엔드: 리뷰 패널 (빠른 승인 + 부분 재작업 체크박스)
  ├── ★ 프론트엔드: ApprovalChainStatus (결재선 현황)
  └── ★ 프론트엔드: 팀원 대시보드 (내 프로젝트 현황)

Phase 3 — 제안서 작성 + 알림
  ├── proposal 동적 섹션 (케이스 A/B 분기)
  ├── self_review (자동 개선 루프 + Compliance 완성)
  ├── DOCX 빌더 (케이스 A/B)
  ├── 중간 버전 DOCX 다운로드 API
  ├── 프론트엔드: 병렬 선검토, Compliance Matrix 뷰
  ├── ★ Teams Webhook 알림 서비스 (승인 요청·결과·마감)
  └── ★ 인앱 알림 (NotificationBell + 알림 목록)

Phase 4 — PPT + G2B + 성과 추적
  ├── ppt 슬라이드 병렬 노드
  ├── PPTX 빌더
  ├── G2B 클라이언트 (공고 검색·낙찰정보)
  ├── HWP/HWPX 파싱 (+ fallback)
  ├── 프론트엔드: 포지셔닝 변경 영향 미리보기
  ├── ★ 제안 결과 등록 API (수주/패찰/유찰)
  ├── ★ 성과 추적 API + Materialized View
  └── ★ 팀장 대시보드 (팀 파이프라인 + 성과 요약)

Phase 5 — 전사 대시보드 + 고도화
  ├── Time-travel + 영향 범위 조회 API
  ├── 인라인 역량 DB 편집
  ├── 버전 비교
  ├── No-Go 재전환 (reopen)
  ├── ★ 본부장 대시보드 (본부 현황 + 결재 대기)
  ├── ★ 경영진 대시보드 (전사 KPI + 추이 차트)
  ├── ★ 관리자 페이지 (사용자·조직 관리 + 시스템 통계)
  ├── ★ 감사 로그 (audit_logs API + 조회 UI)
  └── ★ 성과 추이 차트 (월/분기/연, PerformanceChart)

Phase 6 — ★ v3.0: Knowledge Base + 토큰 효율화
  ├── pgvector 확장 활성화 + 임베딩 인덱스
  ├── 콘텐츠 라이브러리 CRUD + 시맨틱 검색 (content_library.py)
  ├── 발주기관 DB CRUD + G2B 자동 보강 (client_intelligence.py)
  ├── 경쟁사 DB CRUD (competitor_intelligence.py)
  ├── 교훈 아카이브 + 회고 워크시트 (routes_lessons.py)
  ├── 통합 KB 검색 (knowledge_search.py + routes_kb_search.py)
  ├── 임베딩 서비스 (embedding_service.py — OpenAI API)
  ├── 토큰 매니저 (token_manager.py — 컨텍스트 예산 + Prompt Caching)
  ├── Cold Start 대응 (KB 참조 신뢰도 표시)
  ├── KB 내보내기 API (CSV/Excel 다운로드)
  ├── 프론트엔드: KB 관리 페이지 (콘텐츠/발주기관/경쟁사/교훈/통합검색)
  └── 프론트엔드: KbConfidenceBadge + KbSearchBar

Phase 7 — ★ v3.0: AI 모니터링 + 동시 편집 + 사용자 관리
  ├── AI 실행 상태 관리 (ai_status_manager.py)
  ├── SSE 이벤트 타입 확장 (AI 상태·진행률·Heartbeat)
  ├── 프론트엔드: AiStatusPanel (진행률·상태·중단·재시도)
  ├── 섹션 잠금 서비스 (section_lock.py) + SectionLockIndicator
  ├── 회사 템플릿 관리 (routes_template.py)
  ├── 사용자 라이프사이클 관리 (퇴사·이동·위임)
  ├── 크로스팀 프로젝트 + 컨소시엄 관리
  ├── 입력 검증 미들웨어 (input_validator.py)
  ├── 주기적 자동 모니터링 (scheduled_monitor.py — APScheduler)
  ├── AI 완료/오류/무응답 알림 (NOTI-09~11)
  ├── 온보딩 체크리스트 + KB 충족도 대시보드
  └── 프론트엔드: 관리자 사용자 관리 + 온보딩 페이지
```

---
