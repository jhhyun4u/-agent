# 설계 문서: 용역 제안서 자동 생성 에이전트 v1

| 항목 | 내용 |
|------|------|
| 문서 버전 | v3.4 |
| 작성일 | 2026-03-10 |
| 상태 | 초안 |
| 기반 요구사항 | docs/01-plan/features/proposal-agent-v1.requirements.md (v4.9) |
| 핵심 기술 | LangGraph + FastAPI + **Supabase (PostgreSQL + pgvector)** + Next.js + Azure AD + Teams |
| 변경 이력 | v1.0 → v1.1: 포지셔닝 전략, TypedDict, STEP 0, SSE, Send API |
| | v1.1 → v1.2: 부분 재작업, 포지셔닝 중간 변경, 케이스 B, Compliance Matrix, 간이 모드, 빠른 승인, 선검토 등 12건 리뷰 반영 |
| | v1.2 → v1.3: STEP 0을 RFP 공고 검색/추천으로, Go/No-Go를 STEP 1 이후로 이동 |
| | v1.3 → v1.4: STEP 0 pick-up 후 RFP 문서 획득(하이브리드), GoNoGoPanel, 초기 검색 조건, Lite+검색 지원, STEP 1 서브스텝 UI |
| | **v1.4 → v2.0**: 전사 시스템 전환 — 조직·역할·권한, 결재선, 성과 추적, Teams 연동, Supabase PostgreSQL, Azure AD SSO, RLS |
| | **v2.0 → v3.0**: 요구사항 v4.9 반영 + 갭 분석 HIGH 7건 보완 — KB Part B~F (콘텐츠 라이브러리·발주기관·경쟁사·교훈·통합 검색), AI 토큰 효율화 (Prompt Caching·컨텍스트 예산·피드백 윈도우), AI 실행 상태 모니터링 (진행률·Heartbeat·SSE 이벤트), 사용자 라이프사이클 (퇴사·이동·위임), 크로스팀·컨소시엄, 동시 편집 충돌 방지 (섹션 잠금), 회사 템플릿 관리, 입력 검증·파일 보안, KB 내보내기, 주기적 자동 모니터링, 프로젝트 상태 머신 확장 |
| | **v3.0 → v3.1**: 아키텍처 패턴 비교 분석 후 Pattern A(모놀리식 StateGraph + Send() 병렬처리) 유지 확정. 갭 분석 MEDIUM 12건 설계 보완 — 콘텐츠 시딩(OB-05a), 콘텐츠 라이프사이클(CL-10/11), 경쟁 빈도 집계(CMP-06), 포지셔닝 정확도(LRN-08), 검색 이력(KBS-07), 비용 관리(COST-05~07), 운영 복원력(OPS-04~08), 데이터 보존(RET-01~05), 프론트엔드 비기능(NFR-18~20), TRS 보완(TRS-06/12) |
| | **v3.1 → v3.2**: ProposalForge 13개 에이전트 프롬프트 설계서 통합 — Pattern A 구조 내 노드 레벨 프롬프트로 흡수. 신규 노드 2개 (`research_gather`, `presentation_strategy`), 기존 프롬프트 보강 6개 (`go_no_go` 발주기관 인텔리전스 5단계, `strategy_generate` 경쟁 SWOT+시나리오, `plan_price` 원가기준·노임단가·입찰시뮬레이션, `self_review` 3인 페르소나 시뮬레이션, `proposal_section` 자체검증 체크리스트, `ppt.py` 신규 프롬프트 생성). 토큰 예산 ~80K → ~114K/프로젝트 (+34K) |
| | **v3.2 → v3.3**: ProposalForge v3.0 비교 검토 미반영 갭 보완 — DB 스키마 3건 (`labor_rates` 노임단가, `market_price_data` 낙찰가 벤치마크, `artifacts` 버전 관리 컬럼), 품질 게이트 원인별 피드백 라우팅 5방향 확장 (`self_review` → research/strategy/sections/force_review/pass), 전략-예산 상호조정 루프 (`review_plan` → `strategy_generate` 역류 분기), `plan_price` 실데이터 조회 로직, Fallback 전략 체계화 (§22-4), 의도적 스킵 항목 기록 (§30) |
| | **v3.3 → v3.4**: ProposalForge 프론트엔드 화면 흐름 설계서 비교 검토 반영 — 인브라우저 제안서 편집기 (`ProposalEditor`, Tiptap 3컬럼), 모의평가 결과 시각화 (`EvaluationView`, Recharts 레이더/점수 카드), 리뷰 패널 구조화 (AI 이슈 플래그 + 섹션별 인라인 피드백), 워크플로우 수평 Phase 그래프, 분석 대시보드 (`AnalyticsPage`), 원가기준/낙찰가 관리 UI, UI 인프라 (shadcn/ui + Tiptap + Recharts). §12 API 엔드포인트 보완 — ProposalForge API 비교 검토, v3.4 프론트엔드 필수 API 갭 해소 (섹션 AI 재생성, AI 어시스턴트, 모의평가 조회, 노임단가/낙찰가 CRUD, 분석 대시보드 집계 4건), 표준 에러 코드 체계 (M1), 버전 Diff 조회 (M2), HWP 내보내기 (M3), `routes_analytics.py` 추가 |

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

## 3. LangGraph State 스키마

> **v1.3 변경**: STEP 0을 RFP 공고 검색/추천으로 변경. Go/No-Go를 STEP 1 RFP 분석 이후로 이동. `RfpRecommendation` 모델 추가, `search_results` 필드 추가.
> **v1.4 변경**: `BidDetail` 모델 추가 (G2B 공고 상세), `search_query` / `bid_detail` 필드 추가. STEP 0 pick-up 후 하이브리드 RFP 획득 지원.
> **v2.0 변경**: 결재선(`ApprovalChainEntry`), 사용자 컨텍스트(`user_id`, `team_id`) 추가. `ApprovalStatus`에 결재선 이력 포함.
> **v3.0 변경**: KB 참조 필드(`kb_references`, `client_intel_ref`, `competitor_refs`), AI 상태 추적(`ai_task_id`), 토큰 사용 추적(`token_usage`), 피드백 윈도우(`feedback_window_size`) 추가.

```python
# app/graph/state.py
from typing import Annotated, TypedDict, Optional, Literal
from pydantic import BaseModel

# ── 서브 모델 ──

class ApprovalChainEntry(BaseModel):
    """결재선 단일 항목 — 예산 기준에 따라 1~3단계."""
    role: Literal["lead", "director", "executive"]
    user_id: str
    user_name: str
    status: Literal["pending", "approved", "rejected"] = "pending"
    decided_at: str = ""
    feedback: str = ""

class ApprovalStatus(BaseModel):
    status: str           # "pending" | "approved" | "rejected"
    approved_by: str = ""
    approved_at: str = ""
    feedback: str = ""
    # ★ v2.0: 결재선 (Go/No-Go, 제안서 최종 승인 시 사용)
    chain: list[ApprovalChainEntry] = []   # 비어 있으면 팀장 단독 승인

class RfpRecommendation(BaseModel):
    """STEP 0: 공고 검색 추천 결과 항목 (최대 5건)."""
    bid_no: str
    project_name: str
    client: str
    budget: str
    deadline: str
    # ── 공고 요약 정보 (관심과제 선정 판단 근거) ──
    project_summary: str            # 사업 개요 요약 (2~3문장)
    key_requirements: list[str]     # 주요 요구사항 (3~5개)
    eval_method: str                # 평가 방식 요약 (기술:가격 비율, 적격심사 등)
    competition_level: str          # 경쟁 강도 예측 (높음/보통/낮음 + 근거)
    # ── AI 적합도 평가 ──
    fit_score: int                  # 적합도 점수 (100점 만점)
    fit_rationale: str              # 적합도 판단 근거
    expected_positioning: Literal["defensive", "offensive", "adjacent"]
    brief_analysis: str             # 종합 한줄 분석

class BidDetail(BaseModel):
    """STEP 0→1 전환: G2B 공고 상세 정보 (자동 수집)."""
    bid_no: str
    project_name: str
    client: str
    budget: str
    deadline: str
    description: str               # 공고 상세 설명
    requirements_summary: str      # 주요 요구사항 요약
    attachments: list[dict]        # G2B 첨부파일 목록 [{ name, url, type }]
    rfp_auto_text: str = ""        # G2B에서 자동 추출한 RFP 텍스트 (첨부 PDF 등)

class GoNoGoResult(BaseModel):
    """STEP 1-②: RFP 분석 이후 Go/No-Go 의사결정 결과."""
    rfp_analysis_ref: str = ""      # RFP분석서 참조 (분석 완료 후 생성)
    positioning: Literal["defensive", "offensive", "adjacent"]
    positioning_rationale: str
    feasibility_score: int
    score_breakdown: dict
    pros: list[str]
    risks: list[str]
    recommendation: Literal["go", "no-go"]
    decision: str = "pending"

class RFPAnalysis(BaseModel):
    project_name: str
    client: str
    deadline: str
    case_type: Literal["A", "B"]
    eval_items: list[dict]
    tech_price_ratio: dict
    hot_buttons: list[str]
    mandatory_reqs: list[str]
    format_template: dict           # { exists: bool, structure: dict|null }
    volume_spec: dict
    special_conditions: list[str]

class StrategyAlternative(BaseModel):
    """전략 대안 — 최소 2가지, Human이 하나를 선택하거나 조합."""
    alt_id: str                     # "A", "B", ...
    ghost_theme: str
    win_theme: str
    action_forcing_event: str
    key_messages: list[str]
    price_strategy: dict
    risk_assessment: dict

class Strategy(BaseModel):
    positioning: Literal["defensive", "offensive", "adjacent"]
    positioning_rationale: str
    alternatives: list[StrategyAlternative]
    selected_alt_id: str = ""       # Human이 선택한 대안 ID
    # 아래는 선택된 대안에서 복사 + Human 수정 반영
    ghost_theme: str = ""
    win_theme: str = ""
    action_forcing_event: str = ""
    key_messages: list[str] = []
    focus_areas: list[dict] = []
    price_strategy: dict = {}
    competitor_analysis: dict = {}
    risks: list[dict] = []

class ComplianceItem(BaseModel):
    req_id: str
    content: str
    source_step: str                # 어느 단계에서 추가되었는지
    status: Literal["미확인", "충족", "미충족", "해당없음"] = "미확인"
    proposal_section: str = ""      # 대응하는 제안서 섹션

class ProposalSection(BaseModel):
    section_id: str
    title: str
    content: str
    version: int
    case_type: Literal["A", "B"]    # 케이스 A: 자유양식, B: 서식 채우기
    template_structure: Optional[dict] = None  # 케이스 B: 원본 서식 구조
    self_review_score: Optional[dict] = None

class ProposalPlan(BaseModel):
    team: list[dict]
    deliverables: list[dict]
    schedule: dict
    storylines: dict
    bid_price: dict

class PPTSlide(BaseModel):
    slide_id: str
    title: str
    content: str
    notes: str
    version: int


# ── Annotated Reducers ──

def _merge_dict(existing: dict, new: dict) -> dict:
    return {**existing, **new}

def _append_list(existing: list, new: list) -> list:
    return existing + new

def _replace(existing, new):
    return new


# ── 핵심 State 정의 ──

class ProposalState(TypedDict):
    # 프로젝트 메타
    project_id: str
    project_name: str

    # ★ v2.0: 소유·조직 컨텍스트
    team_id: str                    # 소속 팀 ID (프로젝트 생성 시 자동 귀속)
    division_id: str                # 소속 본부 ID
    created_by: str                 # 생성자 user_id
    participants: list[str]         # 참여 팀원 user_id 목록

    # ★ 실행 모드 (간이 / 정규)
    mode: Literal["lite", "full"]   # lite: 역량DB 없이 시작 가능

    # ★ 입찰 포지셔닝 (STEP 1-② Go/No-Go에서 확정, STEP 2에서도 변경 가능)
    positioning: Literal["defensive", "offensive", "adjacent"]

    # 단계별 산출물
    search_query: dict                       # STEP 0: 초기 검색 조건 { keywords, budget_min, region, ... }
    search_results: Annotated[list[RfpRecommendation], _replace]  # STEP 0: 공고 검색 추천 결과
    picked_bid_no: str                       # STEP 0: 사용자가 pick-up한 공고번호
    bid_detail: Optional[BidDetail]          # STEP 0→1: G2B 공고 상세 (자동 수집)
    go_no_go: Optional[GoNoGoResult]         # STEP 1-②: Go/No-Go 결과
    rfp_raw: str
    rfp_analysis: Optional[RFPAnalysis]
    strategy: Optional[Strategy]
    plan: Optional[ProposalPlan]
    proposal_sections: Annotated[list[ProposalSection], _replace]
    ppt_slides: Annotated[list[PPTSlide], _replace]

    # Compliance Matrix (전 단계에 걸쳐 진화)
    compliance_matrix: Annotated[list[ComplianceItem], _replace]

    # 단계별 승인 상태
    approval: Annotated[dict[str, ApprovalStatus], _merge_dict]

    # 현재 실행 중인 단계
    current_step: str

    # 피드백 이력
    feedback_history: Annotated[list[dict], _append_list]

    # ★ 부분 재작업 대상 (빈 리스트 = 전체 실행)
    rework_targets: list[str]

    # 동적 섹션 목록
    dynamic_sections: list[str]

    # 병렬 작업 중간 결과
    parallel_results: Annotated[dict, _merge_dict]

    # ★ v3.0: KB 참조 정보
    kb_references: Annotated[list[dict], _append_list]
    # 형식: [{ "source": "content_library"|"client_intel"|"competitor"|"lesson",
    #          "id": str, "title": str, "relevance_score": float, "used_in_step": str }]
    client_intel_ref: Optional[dict]       # 발주기관 DB 매칭 결과 (Go/No-Go에서 참조)
    competitor_refs: list[dict]            # 경쟁사 DB 매칭 결과 (전략 수립에서 참조)

    # ★ v3.0: AI 상태 추적
    ai_task_id: str                        # 현재 AI 작업 ID (ai_status_manager 연동)

    # ★ v3.0: 토큰 사용 추적
    token_usage: Annotated[dict, _merge_dict]
    # 형식: { "step_name": { "input_tokens": int, "output_tokens": int, "cached_tokens": int } }

    # ★ v3.0: 피드백 윈도우 (최근 N회만 프롬프트에 포함)
    feedback_window_size: int              # 기본값 3 (token_manager에서 관리)

    # ★ v3.2: ProposalForge 통합 — 신규 필드
    research_brief: Optional[dict]           # research_gather 노드 출력 (7차원 리서치 결과)
    presentation_strategy: Optional[dict]    # presentation_strategy 노드 출력 (발표전략)
    budget_detail: Optional[dict]            # plan_price 확장 출력 (상세 원가 — 노임단가·직접경비·간접경비·기술료)
    evaluation_simulation: Optional[dict]    # self_review 확장 출력 (3인 페르소나 시뮬레이션 + 예상 질문·모범답변)
```

---

## 4. LangGraph 그래프 정의

> **v1.3~v1.4 핵심 변경**:
> - STEP 0: RFP 공고 검색/추천 → 관심과제 선정 (interrupt) → **rfp_fetch** (G2B 상세 수집 + RFP 업로드) → STEP 1 진입. 관심과제 없으면 END
> - STEP 1: RFP 분석 → 분석 확인(interrupt) → Go/No-Go + 포지셔닝 확정(interrupt) → STEP 2
> - 부분 재작업: fan-out 함수가 `rework_targets` 확인 → 해당 항목만 Send
> - 포지셔닝 중간 변경: STEP 2 review에서도 `positioning_override` 허용
> - 자가진단 자동 개선 루프: `self_review` → 80점 미만 시 자동 재작성 → 재진단 (최대 2회)

```python
# app/graph/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver  # ★ v2.0: SQLite → PostgreSQL
from langgraph.types import Send

from app.graph.state import ProposalState

def build_graph(checkpointer):
    g = StateGraph(ProposalState)

    # ── 노드 등록 (생략: import 구문) ──

    # STEP 0: 공고 검색/추천
    g.add_node("rfp_search",                rfp_search)
    g.add_node("review_search",             review_node("search"))  # pick-up 선택
    g.add_node("rfp_fetch",                 rfp_fetch)              # G2B 상세 수집 + RFP 업로드 게이트

    # STEP 1-①: RFP 분석
    g.add_node("rfp_analyze",               rfp_analyze)
    g.add_node("review_rfp",                review_node("rfp"))

    # ★ v3.2: STEP 1-①→②: RFP-적응형 사전조사 (review 없이 자동 통과)
    g.add_node("research_gather",           research_gather)

    # STEP 1-②: Go/No-Go + 포지셔닝 확정
    g.add_node("go_no_go",                  go_no_go)
    g.add_node("review_gng",                review_node("go_no_go"))

    # STEP 2
    g.add_node("strategy_generate",         strategy_generate)
    g.add_node("review_strategy",            review_node("strategy"))

    # STEP 3 (병렬, 선택적 재실행)
    g.add_node("plan_fan_out_gate",          _passthrough)
    g.add_node("plan_team",                  plan_team)
    g.add_node("plan_assign",                plan_assign)
    g.add_node("plan_schedule",              plan_schedule)
    g.add_node("plan_story",                 plan_story)
    g.add_node("plan_price",                 plan_price)
    g.add_node("plan_merge",                 plan_merge)
    g.add_node("review_plan",                review_node("plan"))

    # STEP 4 (동적 섹션, 케이스 A/B, 선택적 재실행)
    g.add_node("proposal_fan_out_gate",      _passthrough)
    g.add_node("proposal_section",           proposal_section)
    g.add_node("proposal_merge",             proposal_merge)
    g.add_node("self_review",                self_review_with_auto_improve)
    g.add_node("review_proposal",            review_node("proposal"))

    # ★ v3.2: STEP 4→5: 발표전략 수립 (서류심사 시 건너뛰기)
    g.add_node("presentation_strategy",     presentation_strategy)

    # STEP 5
    g.add_node("ppt_fan_out_gate",           _passthrough)
    g.add_node("ppt_slide",                  ppt_slide)
    g.add_node("ppt_merge",                  ppt_merge)
    g.add_node("review_ppt",                 review_node("ppt"))


    # ── 엣지 정의 ──

    # ★ B-1 + U-1: START → 3가지 진입 경로 분기
    g.add_conditional_edges(START, route_start, {
        "search":        "rfp_search",    # 일반: STEP 0 공고 검색부터
        "direct_fetch":  "rfp_fetch",     # from-search: 공고번호 → rfp_fetch부터
        "direct_rfp":    "rfp_analyze",   # from-rfp: STEP 1 RFP 분석부터
    })

    # STEP 0: 공고 검색 → 관심과제 선정 → RFP 획득
    g.add_edge("rfp_search",       "review_search")
    g.add_conditional_edges("review_search", route_after_search_review, {
        "picked_up":    "rfp_fetch",    # 관심과제 선정 → G2B 상세 수집 + RFP 업로드
        "re_search":    "rfp_search",   # 검색 조건 변경 → 재검색
        "no_interest":  END,            # 관심과제 없음 → 워크플로 종료
    })
    g.add_edge("rfp_fetch",        "rfp_analyze")  # RFP 획득 완료 → STEP 1 진입

    # STEP 1-①: RFP 분석 → 분석 확인
    g.add_edge("rfp_analyze",       "review_rfp")
    g.add_conditional_edges("review_rfp", route_after_rfp_review, {
        "approved":  "research_gather",  # ★ v3.2: 분석 확인 → 리서치 조사 (기존: go_no_go 직행)
        "rejected":  "rfp_analyze",      # 재분석
    })

    # ★ v3.2: 리서치 → Go/No-Go (별도 review 없이 자동 통과)
    g.add_edge("research_gather",  "go_no_go")

    # STEP 1-②: Go/No-Go + 포지셔닝 확정
    g.add_edge("go_no_go",         "review_gng")
    g.add_conditional_edges("review_gng", route_after_gng_review, {
        "go":       "strategy_generate",  # Go → STEP 2
        "no_go":    END,
        "rejected": "go_no_go",
    })

    # STEP 2 (★ 포지셔닝 변경 가능)
    g.add_edge("strategy_generate",  "review_strategy")
    g.add_conditional_edges("review_strategy", route_after_strategy_review, {
        "approved":           "plan_fan_out_gate",
        "rejected":           "strategy_generate",
        "positioning_changed": "strategy_generate",  # 포지셔닝 변경 → 재생성
    })

    # STEP 3: 선택적 병렬 (★ 부분 재작업)
    g.add_conditional_edges("plan_fan_out_gate", plan_selective_fan_out)
    for node in ["plan_team","plan_assign","plan_schedule","plan_story","plan_price"]:
        g.add_edge(node, "plan_merge")
    g.add_edge("plan_merge",         "review_plan")
    # ★ v3.3: 전략-예산 상호조정 루프 (ProposalForge strategy_budget_sync 반영)
    g.add_conditional_edges("review_plan", route_after_plan_review, {
        "approved":             "proposal_fan_out_gate",
        "rework":               "plan_fan_out_gate",       # 부분 재작업
        "rework_with_strategy": "strategy_generate",       # ★ 신규: 예산-전략 부정합 → 전략부터 재수립
    })

    # STEP 4: 동적 섹션 + 선택적 재작업
    g.add_conditional_edges("proposal_fan_out_gate", proposal_selective_fan_out)
    g.add_edge("proposal_section",   "proposal_merge")
    g.add_edge("proposal_merge",     "self_review")
    # ★ v3.3: 원인별 피드백 라우팅 확장 (ProposalForge quality_gate_router 반영)
    g.add_conditional_edges("self_review", route_after_self_review, {
        "pass":            "review_proposal",         # 80점 이상
        "retry_research":  "research_gather",         # ★ 신규: 근거 부족 → 리서치 보강
        "retry_strategy":  "strategy_generate",       # ★ 신규: 전략 약함 → 전략 재수립
        "retry_sections":  "proposal_fan_out_gate",   # 섹션 재작성 (기존 auto_retry 대체)
        "force_review":    "review_proposal",         # 자동 개선 횟수 초과 → Human 판단
    })
    g.add_conditional_edges("review_proposal", route_after_proposal_review, {
        "approved":  "presentation_strategy",    # ★ v3.2: 발표전략 경유 (기존: ppt_fan_out_gate 직행)
        "rework":    "proposal_fan_out_gate",
    })

    # ★ v3.2: 발표전략 → PPT (서류심사 시 건너뛰기)
    g.add_conditional_edges("presentation_strategy", route_after_presentation_strategy, {
        "proceed":       "ppt_fan_out_gate",     # 발표전략 수립 완료 → PPT 생성
        "document_only": "ppt_fan_out_gate",     # 서류심사 → 발표전략 건너뛰기, PPT는 생성
    })

    # STEP 5
    g.add_conditional_edges("ppt_fan_out_gate", ppt_fan_out)
    g.add_edge("ppt_slide",          "ppt_merge")
    g.add_edge("ppt_merge",          "review_ppt")
    g.add_conditional_edges("review_ppt", route_after_ppt_review, {
        "approved":  END,
        "rework":    "ppt_fan_out_gate",
    })

    return g.compile(checkpointer=checkpointer)


def _passthrough(state: ProposalState) -> dict:
    return {}
```

### 4-1. 선택적 Fan-out (부분 재작업) — D-1 해결

```python
# app/graph/graph.py (계속)

ALL_PLAN_NODES = ["plan_team", "plan_assign", "plan_schedule", "plan_story", "plan_price"]

def plan_selective_fan_out(state: ProposalState) -> list[Send]:
    """
    ★ 부분 재작업: rework_targets가 비어 있으면 전체 실행,
    특정 항목이 지정되면 해당 항목만 재실행.
    """
    targets = state.get("rework_targets", [])
    if not targets:
        # 최초 실행 또는 전체 재실행
        nodes_to_run = ALL_PLAN_NODES
    else:
        # 부분 재작업: 지정된 항목만
        nodes_to_run = [n for n in ALL_PLAN_NODES if n in targets]

    return [Send(node, state) for node in nodes_to_run]


def proposal_selective_fan_out(state: ProposalState) -> list[Send]:
    """
    ★ 동적 섹션 + 부분 재작업 + 케이스 A/B 분기.
    """
    targets = state.get("rework_targets", [])
    sections = state.get("dynamic_sections", [])
    case_type = state.get("rfp_analysis", {}).get("case_type", "A") if state.get("rfp_analysis") else "A"

    if targets:
        sections_to_run = [s for s in sections if s in targets]
    else:
        sections_to_run = sections

    return [
        Send("proposal_section", {
            **state,
            "_current_section_id": section_id,
            "_case_type": case_type,
        })
        for section_id in sections_to_run
    ]
```

### 4-2. plan_merge — 부분 재작업 시 기존 결과 보존

```python
# app/graph/nodes/merge_nodes.py

def plan_merge(state: ProposalState) -> dict:
    """
    병렬 완료 결과 병합.
    부분 재작업 시: 새로 실행된 항목만 갱신, 나머지는 기존 값 유지.
    """
    new_results = state.get("parallel_results", {})
    existing_plan = state.get("plan")

    if existing_plan and state.get("rework_targets"):
        # 부분 재작업: 기존 plan에서 새 결과만 덮어씌움
        merged = existing_plan.model_dump()
        for key, value in new_results.items():
            merged[key] = value
        return {"plan": ProposalPlan(**merged), "rework_targets": []}
    else:
        # 최초 실행: 전체 조합
        return {"plan": ProposalPlan(**new_results), "rework_targets": []}
```

---

## 5. 리뷰 노드 (단계별 관점 차별화) — D-2, D-8, U-2 해결

> **v1.3~v1.4 변경**:
> - STEP 0: 공고 검색 리뷰 → pick-up 선택 (승인 게이트 아닌 선택 행위)
> - STEP 0→1: `rfp_fetch`는 review_node가 아닌 자체 interrupt() 사용 (파일 업로드 게이트)
> - STEP 1: RFP 분석 확인 → Go/No-Go 의사결정 (2단계 게이트)
> - 모든 단계에서 **빠른 승인** 지원 (피드백 생략)
> - 전략 단계에서 **포지셔닝 변경** 가능 + 영향 범위 안내
> - 단계별 **리뷰 관점(Shipley)** 차별화
> - 부분 재작업 시 **rework_targets** 지정

```python
# app/graph/nodes/review_node.py
from langgraph.types import interrupt
from app.graph.state import ProposalState, ApprovalStatus

# Shipley Color Team 관점 매핑
REVIEW_PERSPECTIVES = {
    "search": {
        "perspective": "영업 담당자 관점",
        "focus": "관심과제로 선정할 만한가? 우리 역량에 맞는가? 기한은 충분한가? 경쟁 환경은?",
    },
    "go_no_go": {
        "perspective": "의사결정자 관점",
        "focus": "RFP 분석 결과를 보고, 이 입찰에 참여할 만한 가치가 있는가? 자원 투입 대비 수주 가능성은?",
    },
    "rfp": {
        "perspective": "Blue Team (분석 검증) 관점",
        "focus": "RFP 해석이 정확한가? 누락된 요건은 없는가? 배점표 분석이 맞는가?",
    },
    "strategy": {
        "perspective": "Blue Team (전략 검증) 관점",
        "focus": "이 전략으로 이길 수 있는가? 포지셔닝이 맞는가? Win Theme이 평가위원을 설득할 수 있는가?",
    },
    "plan": {
        "perspective": "Pink Team (실행 검증) 관점",
        "focus": "이 계획대로 실행 가능한가? 일정은 현실적인가? 팀 구성에 빈틈은?",
    },
    "proposal": {
        "perspective": "Red Team (경쟁 관점) 관점",
        "focus": "경쟁사 대비 우위가 명확한가? 평가위원이 쉽게 점수를 줄 수 있는 구조인가?",
    },
    "ppt": {
        "perspective": "Gold Team (최종 품질) 관점",
        "focus": "형식·규격 완벽 준수? 메시지 일관성? 발표 시 핵심이 3초 안에 전달되는가?",
    },
}


def review_node(step_name: str):
    """모든 단계에서 공통 리뷰 게이트. 단계별 관점 차별화 + 빠른 승인 지원."""

    def _review(state: ProposalState) -> dict:
        artifact = _get_artifact(state, step_name)
        perspective = REVIEW_PERSPECTIVES.get(step_name, {})

        # ── interrupt: 프론트엔드 resume 대기 ──
        human_input = interrupt({
            "step": step_name,
            "artifact": artifact,
            "positioning": state.get("positioning", ""),
            "review_perspective": perspective,
            "message": f"[{perspective.get('perspective','')}] {step_name} 산출물을 검토하세요.",
            "review_focus": perspective.get("focus", ""),
            "feedback_history": [
                f for f in state.get("feedback_history", [])
                if f["step"] == step_name
            ],
        })

        # ── STEP 0: 공고 pick-up 특수 처리 ──
        if step_name == "search":
            return _handle_search_review(state, human_input)

        # ── STEP 1-②: Go/No-Go 특수 처리 ──
        if step_name == "go_no_go":
            return _handle_gng_review(state, human_input)

        # ── 전략 리뷰: 포지셔닝 변경 가능 (D-2) ──
        if step_name == "strategy":
            return _handle_strategy_review(state, human_input)

        # ── 빠른 승인 (U-2) ──
        if human_input.get("quick_approve"):
            approval = ApprovalStatus(
                status="approved",
                approved_by=human_input.get("approved_by", "user"),
                approved_at=human_input.get("approved_at", ""),
            )
            # ★ v2.0: 결재선 단계 확인 (Go/No-Go, 제안서 최종만 해당)
            if step_name in ("go_no_go", "proposal"):
                chain_result = _check_approval_chain(state, step_name, human_input)
                if chain_result:  # 결재선 미완료 → 다음 승인자 대기
                    return chain_result
                approval.chain = state.get("approval", {}).get(step_name, ApprovalStatus()).chain
            return {
                "approval": {step_name: approval},
                "current_step": f"{step_name}_approved",
                "rework_targets": [],
            }

        # ── 승인 ──
        if human_input.get("approved"):
            approval = ApprovalStatus(
                status="approved",
                approved_by=human_input.get("approved_by", "user"),
                approved_at=human_input.get("approved_at", ""),
            )
            # ★ v2.0: 결재선 단계 확인
            if step_name in ("go_no_go", "proposal"):
                chain_result = _check_approval_chain(state, step_name, human_input)
                if chain_result:
                    return chain_result
                approval.chain = state.get("approval", {}).get(step_name, ApprovalStatus()).chain
            return {
                "approval": {step_name: approval},
                "current_step": f"{step_name}_approved",
                "rework_targets": [],
            }

        # ── 거부 + 부분 재작업 지정 (D-1) ──
        feedback_entry = {
            "step": step_name,
            "feedback": human_input["feedback"],
            "comments": human_input.get("comments", {}),
            "rework_targets": human_input.get("rework_targets", []),
            "timestamp": human_input.get("timestamp", ""),
        }
        return {
            "approval": {step_name: ApprovalStatus(
                status="rejected",
                feedback=human_input["feedback"],
            )},
            "feedback_history": [feedback_entry],
            "current_step": f"{step_name}_rejected",
            "rework_targets": human_input.get("rework_targets", []),
        }

    return _review


def _handle_search_review(state, human_input):
    """STEP 0: 관심과제 선정 처리. 승인 게이트 아닌 선택/종료 행위."""

    # ── 관심과제 선정 (pick-up) → STEP 1 진입 ──
    picked_bid = human_input.get("picked_bid_no")
    if picked_bid:
        return {
            "picked_bid_no": picked_bid,
            "current_step": "search_picked_up",
        }

    # ── 관심과제 없음 → 워크플로 종료 ──
    if human_input.get("no_interest"):
        return {
            "current_step": "search_no_interest",
            "feedback_history": [{
                "step": "search",
                "feedback": human_input.get("reason", "관심과제 없음"),
                "timestamp": human_input.get("timestamp", ""),
            }],
        }

    # ── 재검색 (검색 조건 변경) ──
    return {
        "current_step": "search_re_search",
        "feedback_history": [{
            "step": "search",
            "search_query": human_input.get("search_query", {}),  # ★ A-3: dict로 보존
            "feedback": f"재검색: {human_input.get('search_query', {})}",
            "timestamp": human_input.get("timestamp", ""),
        }],
    }


def _handle_gng_review(state, human_input):
    decision = human_input.get("decision", "go")  # "go" | "no_go" | "rejected"

    if decision == "go":
        result = {
            "approval": {"go_no_go": ApprovalStatus(
                status="approved",
                approved_by=human_input.get("approved_by", "user"),
                approved_at=human_input.get("approved_at", ""),
                feedback=human_input.get("feedback", ""),
            )},
            "current_step": "go_no_go_go",
        }
        # 포지셔닝 확정 (AI 추천 수용 또는 직접 변경)
        override = human_input.get("positioning_override")
        if override and override != state.get("positioning"):
            result["positioning"] = override
        return result

    elif decision == "no_go":
        return {
            "approval": {"go_no_go": ApprovalStatus(
                status="rejected",
                approved_by=human_input.get("approved_by", "user"),
                approved_at=human_input.get("approved_at", ""),
                feedback=human_input.get("feedback", ""),
            )},
            "current_step": "go_no_go_no_go",  # ★ route_after_gng_review에서 확인
            "feedback_history": [{
                "step": "go_no_go",
                "feedback": human_input.get("feedback", "No-Go 결정"),
                "no_go_reason": human_input.get("no_go_reason", ""),
                "timestamp": human_input.get("timestamp", ""),
            }],
        }

    else:
        # 재검토 요청 (Go/No-Go 평가서 재생성)
        return {
            "approval": {"go_no_go": ApprovalStatus(
                status="rejected",
                feedback=human_input.get("feedback", ""),
            )},
            "feedback_history": [{
                "step": "go_no_go",
                "feedback": human_input.get("feedback", ""),
                "timestamp": human_input.get("timestamp", ""),
            }],
            "current_step": "go_no_go_rejected",
        }


def _handle_strategy_review(state, human_input):
    """전략 리뷰: 포지셔닝 변경 가능, 전략 대안 선택 처리."""

    # ★ 포지셔닝 변경 (D-2)
    positioning_changed = False
    override = human_input.get("positioning_override")
    if override and override != state.get("positioning"):
        positioning_changed = True

    # 전략 대안 선택 (D-6)
    selected_alt = human_input.get("selected_alt_id", "")

    if human_input.get("approved") or human_input.get("quick_approve"):
        result = {
            "approval": {"strategy": ApprovalStatus(
                status="approved",
                approved_by=human_input.get("approved_by", "user"),
                approved_at=human_input.get("approved_at", ""),
            )},
            "current_step": "strategy_approved",
        }
        if selected_alt:
            result["strategy"] = _apply_selected_alternative(state["strategy"], selected_alt)
        return result

    elif positioning_changed:
        # 포지셔닝 변경 → 전략 재생성 (기존 STEP 3~5 승인 초기화)
        return {
            "positioning": override,
            "approval": {
                "strategy": ApprovalStatus(status="rejected", feedback="포지셔닝 변경"),
                "plan":     ApprovalStatus(status="pending"),
                "proposal": ApprovalStatus(status="pending"),
                "ppt":      ApprovalStatus(status="pending"),
            },
            "feedback_history": [{
                "step": "strategy",
                "feedback": f"포지셔닝 변경: {state.get('positioning')} → {override}",
                "timestamp": human_input.get("timestamp", ""),
            }],
            "current_step": "strategy_positioning_changed",
        }

    else:
        # 일반 거부
        return {
            "approval": {"strategy": ApprovalStatus(
                status="rejected",
                feedback=human_input.get("feedback", ""),
            )},
            "feedback_history": [{
                "step": "strategy",
                "feedback": human_input.get("feedback", ""),
                "comments": human_input.get("comments", {}),
                "timestamp": human_input.get("timestamp", ""),
            }],
            "current_step": "strategy_rejected",
        }


def _apply_selected_alternative(strategy, alt_id):
    """선택된 대안의 값을 Strategy 최상위 필드로 복사."""
    for alt in strategy.alternatives:
        if alt.alt_id == alt_id:
            strategy.selected_alt_id = alt_id
            strategy.ghost_theme = alt.ghost_theme
            strategy.win_theme = alt.win_theme
            strategy.action_forcing_event = alt.action_forcing_event
            strategy.key_messages = alt.key_messages
            strategy.price_strategy = alt.price_strategy
            return strategy
    return strategy


def _get_artifact(state, step_name):
    mapping = {
        "search":    state.get("search_results"),
        "rfp_fetch": state.get("bid_detail"),
        "go_no_go":  state.get("go_no_go"),
        "rfp":       state.get("rfp_analysis"),
        "strategy": state.get("strategy"),
        "plan":     state.get("plan"),
        "proposal": state.get("proposal_sections"),
        "ppt":      state.get("ppt_slides"),
    }
    return mapping.get(step_name)


# ── ★ v2.0: 결재선 승인 체크 ──

def _check_approval_chain(state, step_name, human_input):
    """
    결재선 기반 다단계 승인 처리 (Go/No-Go, 제안서 최종 승인에 적용).

    결재선 규칙 (요구사항 §2-4):
    - 예산 3억 미만: 팀장 단독 승인
    - 예산 3억~5억: 팀장 → 본부장 승인 필수
    - 예산 5억 이상: 팀장 → 본부장 → 경영진 승인 필수

    결재선이 미완료인 경우 interrupt 상태를 유지하여 다음 승인자를 대기.
    """
    budget = _extract_budget(state)
    approver_role = human_input.get("approver_role", "lead")

    existing_approval = state.get("approval", {}).get(step_name, ApprovalStatus())
    chain = list(existing_approval.chain) if existing_approval.chain else []

    # 현재 승인자 기록
    chain.append(ApprovalChainEntry(
        role=approver_role,
        user_id=human_input.get("approved_by", ""),
        user_name=human_input.get("approver_name", ""),
        status="approved",
        decided_at=human_input.get("approved_at", ""),
    ))

    # 결재선 완료 여부 판단
    required_roles = _get_required_roles(budget)
    approved_roles = {e.role for e in chain if e.status == "approved"}

    if not required_roles.issubset(approved_roles):
        # 결재선 미완료 → 다음 승인자 대기 (interrupt 상태 유지)
        next_role = next(r for r in ["lead", "director", "executive"]
                        if r in required_roles and r not in approved_roles)
        return {
            "approval": {step_name: ApprovalStatus(
                status="pending",
                chain=chain,
                feedback=f"결재 진행 중 — {next_role} 승인 대기",
            )},
            "current_step": f"{step_name}_chain_pending",
        }

    # 결재선 완료 → None 반환 (호출자가 최종 승인 처리)
    return None


def _get_required_roles(budget: int) -> set[str]:
    """예산 기준 필요 결재 역할."""
    if budget >= 500_000_000:
        return {"lead", "director", "executive"}
    elif budget >= 300_000_000:
        return {"lead", "director"}
    return {"lead"}


def _extract_budget(state) -> int:
    """State에서 예산 금액 추출 (bid_detail 또는 rfp_analysis에서)."""
    bid = state.get("bid_detail")
    if bid and hasattr(bid, "budget"):
        try:
            return int(bid.budget.replace(",", "").replace("원", "").replace("억", "0000_0000"))
        except (ValueError, AttributeError):
            pass
    return 0
```

---

## 6. STEP 0: RFP 공고 검색 노드

```python
# app/graph/nodes/rfp_search.py

MAX_RECOMMENDATIONS = 5  # 관심과제 후보 최대 5건

async def rfp_search(state: ProposalState) -> dict:
    """
    STEP 0: G2B 공고 검색 + AI 적합도 평가 + 추천 리스트 생성 (최대 5건).
    각 공고에 대해 요약정보(사업개요, 주요 요구사항, 평가방식, 경쟁강도)를 제공하여
    사용자가 관심과제를 선정할 수 있도록 한다.
    """
    # ★ A-3 + U-4: 검색 조건 결정 (초기 search_query > 재검색 피드백 > project_name)
    query_params = state.get("search_query", {})  # 초기 검색 조건 (프로젝트 생성 시 전달)

    # 재검색인 경우: feedback_history에서 최신 검색 조건 추출
    feedback_history = state.get("feedback_history", [])
    if feedback_history:
        last = feedback_history[-1]
        if last.get("step") == "search":
            raw_query = last.get("search_query", {})
            if isinstance(raw_query, dict):
                query_params = {**query_params, **raw_query}  # 기존 조건에 덮어씌움
            else:
                query_params["keywords"] = str(raw_query)

    search_keywords = query_params.get("keywords", "") or state.get("project_name", "")
    mode = state.get("mode", "full")

    # G2B 공고 검색
    raw_results = await g2b_client.search_bids(
        keywords=search_keywords,
        budget_min=query_params.get("budget_min"),
        region=query_params.get("region"),
    )

    if mode == "full":
        # 역량 DB + ★ v3.0: 발주기관·경쟁사 DB 기반 적합도 평가
        capabilities = await capability_store.get_all()
        # ★ v3.0: 검색 결과 발주기관에 대한 기존 입찰 이력 조회
        client_names = [r.get("client", "") for r in raw_results]
        client_histories = await client_intelligence.get_bid_histories_by_names(client_names)
        recommendations = await claude_generate(
            RFP_SEARCH_PROMPT.format(
                bids=raw_results,
                capabilities=capabilities,
                client_histories=client_histories,  # ★ v3.0: 발주기관 입찰 이력
                max_results=MAX_RECOMMENDATIONS,
                # 프롬프트 지시: 각 공고에 대해
                # - project_summary: 사업 개요 2~3문장
                # - key_requirements: 주요 요구사항 3~5개
                # - eval_method: 평가 방식 (기술:가격 비율 등)
                # - competition_level: 경쟁 강도 예측 (★ 발주기관 입찰 이력 참고)
                # - fit_score/rationale: 자사 역량 대비 적합도
            ),
        )
    else:
        # lite 모드: 역량 DB 없이 공고 요약만
        recommendations = await claude_generate(
            RFP_SEARCH_LITE_PROMPT.format(
                bids=raw_results,
                max_results=MAX_RECOMMENDATIONS,
            ),
        )

    # 적합도순 정렬, 최대 5건
    sorted_recs = sorted(recommendations, key=lambda r: r.get("fit_score", 0), reverse=True)
    return {
        "search_results": [RfpRecommendation(**r) for r in sorted_recs[:MAX_RECOMMENDATIONS]],
        "current_step": "search_complete",
    }
```

### 6-1. rfp_fetch: G2B 상세 수집 + RFP 업로드 게이트 — U-1 해결

> **하이브리드 방식**: G2B에서 공고 상세·첨부파일을 자동 수집하고, 사용자에게 RFP 원본 파일 업로드 기회를 제공한다.
> G2B 자동 추출 텍스트만으로도 진행 가능하지만, 사용자가 별도 RFP PDF를 업로드하면 더 정확한 분석이 된다.

```python
# app/graph/nodes/rfp_fetch.py
from langgraph.types import interrupt

async def rfp_fetch(state: ProposalState) -> dict:
    """
    STEP 0 → STEP 1 전환 노드:
    1) G2B API로 공고 상세 + 첨부파일 자동 수집
    2) 첨부파일 중 RFP PDF가 있으면 자동 파싱
    3) interrupt()로 사용자에게 추가 RFP 파일 업로드 기회 제공
    4) rfp_raw 확보 → rfp_analyze 진입 가능
    """
    bid_no = state.get("picked_bid_no", "")

    # ── 1) G2B 공고 상세 자동 수집 ──
    detail = await g2b_client.get_bid_detail(bid_no)
    bid_detail = BidDetail(
        bid_no=bid_no,
        project_name=detail["project_name"],
        client=detail["client"],
        budget=detail["budget"],
        deadline=detail["deadline"],
        description=detail.get("description", ""),
        requirements_summary=detail.get("requirements_summary", ""),
        attachments=detail.get("attachments", []),
    )

    # ── 2) G2B 첨부파일에서 RFP 자동 추출 시도 ──
    auto_rfp_text = ""
    for att in bid_detail.attachments:
        if att.get("type") in ("pdf", "hwp", "hwpx"):
            try:
                file_bytes = await g2b_client.download_attachment(att["url"])
                auto_rfp_text = await parse_rfp_bytes(file_bytes, att["type"])
                break  # 첫 번째 성공한 파일 사용
            except Exception:
                continue

    bid_detail.rfp_auto_text = auto_rfp_text

    # ── 3) interrupt: 사용자에게 RFP 파일 업로드 기회 ──
    human_input = interrupt({
        "step": "rfp_fetch",
        "bid_detail": bid_detail.model_dump(),
        "has_auto_rfp": bool(auto_rfp_text),
        "message": "공고 상세를 수집했습니다. RFP 원본 파일이 있으면 업로드하세요.",
        "hint": "G2B 첨부파일에서 RFP를 자동 추출했습니다." if auto_rfp_text
                else "G2B 첨부파일에서 RFP를 찾지 못했습니다. 직접 업로드해 주세요.",
    })

    # ── 4) 사용자 응답 처리 ──
    if human_input.get("rfp_file_text"):
        # 사용자가 RFP 파일 업로드 → 파싱된 텍스트 사용
        rfp_raw = human_input["rfp_file_text"]
    elif auto_rfp_text:
        # 사용자 스킵 + G2B 자동 추출 성공 → 자동 텍스트 사용
        rfp_raw = auto_rfp_text
    else:
        # G2B 추출 실패 + 사용자 스킵 → 공고 상세 설명만으로 진행
        rfp_raw = f"[공고 상세 기반]\n{bid_detail.description}\n\n{bid_detail.requirements_summary}"

    return {
        "bid_detail": bid_detail,
        "rfp_raw": rfp_raw,
        "project_name": bid_detail.project_name,  # 프로젝트 기본정보 자동 채움
        "current_step": "rfp_fetch_complete",
    }
```

---

## 7. STEP 1-②: Go/No-Go 노드 — B-2 추가

> **RFP 분석 완료 후**, 분석 결과 + 자사 역량 DB를 기반으로 포지셔닝 판정 및 수주 가능성을 평가한다.
> **★ v3.2**: `research_gather` 리서치 결과를 추가 컨텍스트로 주입. 발주기관 인텔리전스 5단계 분석 프레임워크 추가 (ProposalForge #3). 토큰 예산 15,000 → 18,000.

```python
# app/graph/nodes/go_no_go.py

async def go_no_go(state: ProposalState) -> dict:
    """
    STEP 1-②: RFP 분석 결과를 기반으로 Go/No-Go 평가.
    - Full 모드: 역량 DB + RFP 분석 + 리서치 브리프 → AI 포지셔닝 추천 + 수주 가능성 점수
    - Lite 모드: RFP 분석만으로 간이 평가 (포지셔닝은 사용자 직접 선택)
    ★ v3.2: research_brief 주입 + 발주기관 인텔리전스 5단계 프레임워크
    """
    rfp = state.get("rfp_analysis")
    mode = state.get("mode", "full")
    research_brief = state.get("research_brief", {})  # ★ v3.2

    if mode == "full":
        capabilities = await capability_store.get_all()
        # ★ v3.0: KB 참조 — 발주기관 DB + 경쟁사 DB 조회
        client_name = rfp.client if rfp else ""
        client_intel = await client_intelligence.get_by_name(client_name)
        competitors = await competitor_intelligence.search_by_domain(
            rfp.hot_buttons if rfp else []
        )
        result = await claude_generate(
            GO_NO_GO_FULL_PROMPT.format(
                rfp_analysis=rfp,
                capabilities=capabilities,
                hot_buttons=rfp.hot_buttons,
                eval_items=rfp.eval_items,
                tech_price_ratio=rfp.tech_price_ratio,
                client_intel=client_intel,       # ★ v3.0: 발주기관 성향·이력
                competitors=competitors,          # ★ v3.0: 경쟁사 강약점
                research_brief=research_brief,    # ★ v3.2: 7차원 리서치 결과
            ),
        )
    else:
        # Lite 모드: 역량 DB 없이 RFP 분석만으로 간이 판단
        result = await claude_generate(
            GO_NO_GO_LITE_PROMPT.format(
                rfp_analysis=rfp,
            ),
        )
        # Lite 모드에서는 수주 가능성 점수 생략
        result["feasibility_score"] = 0
        result["score_breakdown"] = {}

    gng = GoNoGoResult(
        rfp_analysis_ref=f"rfp_{state.get('project_id', '')}",
        positioning=result["positioning"],
        positioning_rationale=result["positioning_rationale"],
        feasibility_score=result.get("feasibility_score", 0),
        score_breakdown=result.get("score_breakdown", {}),
        pros=result["pros"],
        risks=result["risks"],
        recommendation=result["recommendation"],
    )

    return {
        "go_no_go": gng,
        "positioning": gng.positioning,  # 잠정 포지셔닝 (Human이 변경 가능)
        "current_step": "go_no_go_complete",
        # ★ v3.0: KB 참조 기록
        "client_intel_ref": client_intel.to_dict() if client_intel else None,
        "competitor_refs": [c.to_dict() for c in competitors] if competitors else [],
        "kb_references": [
            {"source": "client_intel", "id": client_intel.id, "title": client_name,
             "relevance_score": 1.0, "used_in_step": "go_no_go"}
        ] if client_intel else [],
    }
```

---

## 8. 자가진단 자동 개선 루프 — D-10 해결

```python
# app/graph/nodes/self_review.py

MAX_AUTO_IMPROVE = 2  # 자동 개선 최대 횟수

async def self_review_with_auto_improve(state: ProposalState) -> dict:
    """
    AI 자가진단 + 자동 개선 루프.
    80점 미만 → 자동으로 부족 섹션 재작성 (최대 2회) → 재진단.
    """
    sections = state.get("proposal_sections", [])
    compliance = state.get("compliance_matrix", [])
    strategy = state.get("strategy")
    auto_improve_count = state.get("parallel_results", {}).get("_auto_improve_count", 0)

    # Compliance Matrix 완성 (D-4: STEP 4에서 완성)
    updated_compliance = await check_compliance(sections, compliance)

    # ★ v3.0: 4축 평가 (기존 3축 + 근거 신뢰성)
    score = await evaluate_proposal(sections, updated_compliance, strategy)
    trustworthiness = await evaluate_trustworthiness(sections, strategy)  # §16-3-3
    score["trustworthiness"] = trustworthiness
    # 총점 재계산 (4축 가중 합산: 각 25점, 합계 100점)
    score["total"] = (
        score.get("compliance_score", 0) +
        score.get("strategy_score", 0) +
        score.get("quality_score", 0) +
        trustworthiness["trustworthiness_score"]
    )

    result = {
        "compliance_matrix": updated_compliance,
        "parallel_results": {
            "_self_review_score": score,
            "_auto_improve_count": auto_improve_count,
        },
    }

    # ★ v3.3: 원인별 재시도 횟수 추적 (무한 루프 방지 — §22-4-3)
    retry_research_count = state.get("parallel_results", {}).get("_retry_research_count", 0)
    retry_strategy_count = state.get("parallel_results", {}).get("_retry_strategy_count", 0)

    if score["total"] >= 80:
        result["current_step"] = "self_review_pass"
    elif auto_improve_count < MAX_AUTO_IMPROVE:
        # ★ v3.3: 축별 약점 분석으로 원인별 라우팅 결정
        trustworthiness_score = trustworthiness.get("trustworthiness_score", 25)
        strategy_score = score.get("strategy_score", 25)

        if trustworthiness_score < 12 and retry_research_count < 1:
            # 근거 부족 → 리서치 보강 (최대 1회)
            result["parallel_results"]["_retry_research_count"] = retry_research_count + 1
            result["parallel_results"]["_auto_improve_count"] = auto_improve_count + 1
            result["current_step"] = "self_review_retry_research"
        elif strategy_score < 15 and retry_strategy_count < 1:
            # 전략 약함 → 전략 재수립 (최대 1회)
            result["parallel_results"]["_retry_strategy_count"] = retry_strategy_count + 1
            result["parallel_results"]["_auto_improve_count"] = auto_improve_count + 1
            result["current_step"] = "self_review_retry_strategy"
        else:
            # 그 외 → 섹션 재작성
            weak_sections = [s for s in score["section_scores"] if s["score"] < 70]
            result["rework_targets"] = [s["section_id"] for s in weak_sections]
            result["parallel_results"]["_auto_improve_count"] = auto_improve_count + 1
            result["current_step"] = "self_review_retry_sections"
    else:
        result["current_step"] = "self_review_force_review"

    return result


def route_after_self_review(state: ProposalState) -> str:
    """
    ★ v3.3: 원인별 피드백 라우팅 (ProposalForge quality_gate_router 반영).
    기존 3방향(pass/auto_retry/force_review) → 5방향 확장.
    self_review_with_auto_improve에서 설정한 current_step 값에 따라 분기.
    """
    step = state.get("current_step", "")
    if "pass" in step:
        return "pass"
    elif "force_review" in step:
        return "force_review"
    elif "retry_research" in step:
        return "retry_research"
    elif "retry_strategy" in step:
        return "retry_strategy"
    return "retry_sections"
```

---

## 9. 케이스 B (서식 있음) 처리 — D-3 해결

```python
# app/graph/nodes/proposal_nodes.py

async def proposal_section(state: ProposalState) -> dict:
    """
    섹션 생성 노드. 케이스 A/B에 따라 접근 방식이 다름.
    """
    section_id = state.get("_current_section_id", "")
    case_type = state.get("_case_type", "A")
    strategy = state.get("strategy")
    positioning = state.get("positioning")
    rfp = state.get("rfp_analysis")

    if case_type == "B":
        # ★ 케이스 B: 서식 구조 보존, 내용만 채우기
        template_structure = rfp.get("format_template", {}).get("structure", {})
        section_template = template_structure.get(section_id, {})

        content = await claude_generate(
            PROPOSAL_CASE_B_PROMPT.format(
                section_id=section_id,
                template_structure=section_template,  # 원본 서식 구조
                strategy=strategy,
                positioning=positioning,
                positioning_guide=POSITIONING_STRATEGY_MATRIX[positioning],
                rfp_analysis=rfp,
            ),
        )
        return {
            "proposal_sections": [ProposalSection(
                section_id=section_id,
                title=section_template.get("title", section_id),
                content=content,
                version=1,
                case_type="B",
                template_structure=section_template,
            )],
        }
    else:
        # 케이스 A: 자유 양식
        content = await claude_generate(
            PROPOSAL_CASE_A_PROMPT.format(
                section_id=section_id,
                strategy=strategy,
                positioning=positioning,
                positioning_guide=POSITIONING_STRATEGY_MATRIX[positioning],
                rfp_analysis=rfp,
            ),
        )
        return {
            "proposal_sections": [ProposalSection(
                section_id=section_id,
                title=section_id,
                content=content,
                version=1,
                case_type="A",
            )],
        }
```

### 9-1. DOCX 빌더 케이스 분기

```python
# app/services/docx_builder.py

async def build_docx(sections: list[ProposalSection], rfp: RFPAnalysis) -> bytes:
    if rfp.case_type == "B":
        # 케이스 B: RFP 서식 템플릿을 기반으로 DOCX 생성
        # 원본 서식의 제목·번호·구조를 그대로 재현하고 content만 삽입
        return _build_from_template(sections, rfp.format_template["structure"])
    else:
        # 케이스 A: 자유 양식 DOCX 생성
        return _build_freeform(sections)
```

---

## 10. Compliance Matrix 생애주기 — D-4 해결

```python
# app/services/compliance_tracker.py

class ComplianceTracker:
    """Compliance Matrix 전 단계 생애주기 관리."""

    @staticmethod
    async def create_initial(rfp_analysis: RFPAnalysis) -> list[ComplianceItem]:
        """STEP 1: RFP 필수 요건에서 초안 생성."""
        items = []
        for i, req in enumerate(rfp_analysis.mandatory_reqs):
            items.append(ComplianceItem(
                req_id=f"REQ-{i+1:03d}",
                content=req,
                source_step="rfp",
                status="미확인",
            ))
        # 평가항목에서 추가 요건 추출
        for item in rfp_analysis.eval_items:
            items.append(ComplianceItem(
                req_id=f"EVAL-{item['항목명'][:10]}",
                content=f"평가항목: {item['항목명']} ({item['배점']}점)",
                source_step="rfp",
                status="미확인",
            ))
        return items

    @staticmethod
    async def update_from_strategy(
        matrix: list[ComplianceItem], strategy: Strategy
    ) -> list[ComplianceItem]:
        """STEP 2: 전략 관점 항목 추가 (Win Theme 반영 체크 등)."""
        matrix.append(ComplianceItem(
            req_id="STR-WIN",
            content=f"Win Theme 반영 확인: {strategy.win_theme}",
            source_step="strategy",
            status="미확인",
        ))
        matrix.append(ComplianceItem(
            req_id="STR-AFE",
            content=f"Action Forcing Event 반영: {strategy.action_forcing_event}",
            source_step="strategy",
            status="미확인",
        ))
        for i, msg in enumerate(strategy.key_messages):
            matrix.append(ComplianceItem(
                req_id=f"STR-MSG-{i+1}",
                content=f"핵심 메시지 {i+1} 반영: {msg}",
                source_step="strategy",
                status="미확인",
            ))
        return matrix

    @staticmethod
    async def check_compliance(
        sections: list[ProposalSection], matrix: list[ComplianceItem]
    ) -> list[ComplianceItem]:
        """STEP 4 자가진단: 각 항목의 충족 여부를 AI로 체크."""
        all_content = "\n".join(s.content for s in sections)
        for item in matrix:
            # Claude에게 각 항목의 충족 여부 판정 요청
            result = await claude_generate(
                COMPLIANCE_CHECK_PROMPT.format(
                    requirement=item.content,
                    proposal_content=all_content,
                ),
            )
            item.status = result["status"]  # 충족|미충족|해당없음
            item.proposal_section = result.get("matching_section", "")
        return matrix
```

---

## 11. Conditional Edge 라우팅

```python
# app/graph/edges.py

def route_start(state: ProposalState) -> str:
    """★ B-1 + U-1 + U-6: 3가지 진입 경로 분기.
    - rfp_raw 존재 → STEP 1 직접 진입 (from-rfp)
    - picked_bid_no 존재 → rfp_fetch (from-search)
    - 그 외 → STEP 0 검색 (lite/full 모두)
    """
    if state.get("rfp_raw"):
        return "direct_rfp"
    if state.get("picked_bid_no"):
        return "direct_fetch"
    return "search"

def route_after_search_review(state: ProposalState) -> str:
    """STEP 0: 관심과제 선정 / 재검색 / 종료."""
    step = state.get("current_step", "")
    if step == "search_picked_up":
        return "picked_up"
    if step == "search_no_interest":
        return "no_interest"
    return "re_search"

def route_after_gng_review(state: ProposalState) -> str:
    """★ A-1 수정: current_step 기반 라우팅 (feedback 문자열 비교 제거)."""
    step = state.get("current_step", "")
    if step == "go_no_go_go":
        return "go"
    elif step == "go_no_go_no_go":
        return "no_go"
    return "rejected"  # go_no_go_rejected → 재생성

def route_after_rfp_review(state: ProposalState) -> str:
    """STEP 1-①: RFP 분석 확인 → 리서치 조사 진행 또는 재분석. ★ v3.2: research_gather 경유."""
    return "approved" if state["approval"]["rfp"].status == "approved" else "rejected"

def route_after_strategy_review(state: ProposalState) -> str:
    """★ 포지셔닝 변경 라우팅 추가."""
    if state.get("current_step") == "strategy_positioning_changed":
        return "positioning_changed"
    return "approved" if state["approval"]["strategy"].status == "approved" else "rejected"

def route_after_plan_review(state: ProposalState) -> str:
    """★ v3.3: 전략-예산 상호조정 분기 추가 (ProposalForge strategy_budget_sync 반영)."""
    if state["approval"]["plan"].status == "approved":
        return "approved"
    # 피드백에 '전략 재수립' 키워드가 포함되면 strategy_generate로 루프백
    feedback = state.get("feedback_history", [])
    latest = feedback[-1] if feedback else {}
    rework_targets = latest.get("rework_targets", [])
    if "strategy_generate" in rework_targets:
        return "rework_with_strategy"
    return "rework"

def route_after_proposal_review(state: ProposalState) -> str:
    """★ v3.2: approved → presentation_strategy 경유 (기존: ppt_fan_out_gate 직행)."""
    return "approved" if state["approval"]["proposal"].status == "approved" else "rework"

def route_after_presentation_strategy(state: ProposalState) -> str:
    """★ v3.2: 발표전략 조건부 실행. 서류심사(document_only)이면 건너뛰기."""
    eval_method = state.get("rfp_analysis", {})
    if hasattr(eval_method, "eval_method"):
        eval_method = eval_method.eval_method
    else:
        eval_method = eval_method.get("eval_method", "") if isinstance(eval_method, dict) else ""
    if "document_only" in str(eval_method).lower():
        return "document_only"
    return "proceed"

def route_after_ppt_review(state: ProposalState) -> str:
    return "approved" if state["approval"]["ppt"].status == "approved" else "rework"
```

---

## 12. API 엔드포인트 설계

### 12-0. ★ 표준 에러 코드 체계 (v3.4)

> **배경**: ProposalForge의 구조화된 에러 코드 체계(`AUTH_001`, `PROJ_001` 등)를 참고하여 도입.
> ProposalEditor 자동저장(3초 debounce)이 빈번한 API 호출을 유발하므로,
> 에러 종류별 프론트엔드 핸들링(재시도/토큰갱신/인라인에러)을 명확히 구분하는 것이 핵심 목적.

#### 에러 응답 표준 형식

```json
{
  "error_code": "SECT_001",
  "message": "섹션이 다른 사용자에 의해 잠겨 있습니다.",
  "detail": {
    "locked_by": "홍길동",
    "locked_at": "2026-03-10T14:30:00Z",
    "expires_at": "2026-03-10T15:00:00Z"
  }
}
```

#### 에러 코드 프리픽스

| 프리픽스 | 도메인 | 예시 |
|----------|--------|------|
| `AUTH_` | 인증·인가 | 토큰 만료, 권한 부족 |
| `PROP_` | 프로젝트·워크플로 | 상태 전이 오류, 중복 생성 |
| `WF_` | 워크플로 실행 | resume 실패, 노드 오류 |
| `SECT_` | 섹션·편집 | 잠금 충돌, 버전 충돌 |
| `KB_` | Knowledge Base | 검색 오류, 임포트 실패 |
| `AI_` | AI 서비스 | Claude API 오류, 토큰 초과 |
| `FILE_` | 파일 처리 | 업로드 실패, 포맷 오류 |
| `ADMIN_` | 관리자 기능 | 조직 구조 오류, 템플릿 오류 |

#### 주요 에러 코드 테이블

| 에러 코드 | HTTP | 설명 | 프론트엔드 핸들링 |
|-----------|------|------|-------------------|
| `AUTH_001` | 401 | JWT 토큰 만료 | 자동 토큰 갱신 후 재시도 |
| `AUTH_002` | 403 | 역할 권한 부족 | 에러 토스트 + 접근 차단 |
| `AUTH_003` | 403 | 프로젝트 접근 권한 없음 | 에러 페이지 리다이렉트 |
| `PROP_001` | 409 | 프로젝트 상태 전이 불가 | 상태 새로고침 안내 |
| `PROP_002` | 404 | 프로젝트 없음 | 404 페이지 |
| `WF_001` | 409 | 워크플로 이미 실행 중 | 현재 상태 안내 |
| `WF_002` | 422 | resume 페이로드 검증 실패 | 인라인 폼 에러 |
| `SECT_001` | 423 | 섹션 잠금 충돌 | 잠금 소유자·만료 시간 표시 |
| `SECT_002` | 409 | 섹션 버전 충돌 (동시 편집) | 최신 버전 로드 안내 |
| `KB_001` | 422 | KB 임포트 데이터 검증 실패 | 오류 행 번호 표시 |
| `AI_001` | 503 | Claude API 일시 오류 | 자동 재시도 (3회, 지수 백오프) |
| `AI_002` | 422 | AI 요청 토큰 예산 초과 | 입력 축소 안내 |
| `AI_003` | 504 | AI 응답 타임아웃 | 재시도 버튼 표시 |
| `FILE_001` | 413 | 파일 크기 초과 (50MB) | 파일 크기 제한 안내 |
| `FILE_002` | 415 | 지원하지 않는 파일 형식 | 허용 형식 목록 안내 |

> **구현 패턴**: `app/api/deps.py`에 `TenopAPIError(Exception)` 기반 클래스 정의.
> FastAPI exception handler에서 표준 형식으로 직렬화. 기존 `HTTPException`을 점진적으로 교체.
> §22-4 Fallback 전략의 에러 분류(Claude API retry, external data skip, quality gate limits, timeouts)와 일관성 유지.

---

### 12-1. 워크플로 제어

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/proposals` | 프로젝트 생성 (mode, search_query 포함) |
| POST | `/api/proposals/from-rfp` | RFP 업로드로 프로젝트 생성 (STEP 0 건너뛰고 STEP 1 직접 진입) |
| POST | `/api/proposals/from-search` | ★ 워크플로 밖에서 공고번호로 직접 프로젝트 생성 (rfp_fetch부터 시작) |
| GET  | `/api/proposals` | 프로젝트 목록 (포지셔닝·단계·마감일 포함, U-10) |
| GET  | `/api/proposals/{id}` | 프로젝트 상세 |
| POST | `/api/proposals/{id}/start` | 워크플로 시작 |
| GET  | `/api/proposals/{id}/state` | 현재 그래프 상태 |
| POST | `/api/proposals/{id}/resume` | Human 리뷰 결과 입력 → 그래프 재개 |
| POST | `/api/proposals/{id}/goto/{step}` | Time-travel |
| GET  | `/api/proposals/{id}/impact/{step}` | ★ 이전 단계 이동 시 영향 범위 조회 (U-5) |
| GET  | `/api/proposals/{id}/history` | 체크포인트 이력 |
| GET  | `/api/proposals/{id}/stream` | SSE 스트리밍 |
| POST | `/api/proposals/{id}/reopen` | ★ No-Go → Go 재전환 (D-9) |

### 12-1-1. 프로젝트 생성 API 요청 바디 (U-9)

```json
// POST /api/proposals — STEP 0(공고 검색)부터 시작
{
  "name": "AI 플랫폼 관련",
  "mode": "full",
  "search_query": {
    "keywords": "AI 플랫폼",
    "budget_min": 100000000,
    "region": "서울"
  }
}

// POST /api/proposals/from-rfp — STEP 0 건너뛰고 STEP 1 직접 시작
{
  "mode": "lite",
  "rfp_file": "<UploadFile>"
}

// POST /api/proposals/from-search — 워크플로 밖에서 공고번호 직접 지정 (rfp_fetch부터)
// ★ STEP 0(검색)을 건너뛰고, 이미 알고 있는 공고번호로 rfp_fetch → STEP 1 진입
{
  "bid_no": "20260309-001",
  "mode": "full"
}
```

> **3가지 진입 경로 정리**:
> | 경로 | API | 시작 노드 | 시나리오 |
> |------|-----|-----------|----------|
> | 공고 검색 | `POST /api/proposals` | `rfp_search` | 일반: 공고 탐색부터 시작 |
> | 공고번호 직접 | `POST /api/proposals/from-search` | `rfp_fetch` | 이미 공고를 알고 있음 |
> | RFP 업로드 | `POST /api/proposals/from-rfp` | `rfp_analyze` | RFP 문서를 가지고 있음 |

### 12-2. resume API 요청 바디

```json
// 빠른 승인 (U-2)
{
  "quick_approve": true,
  "approved_by": "홍길동"
}

// STEP 0: 공고 Pick-up
{
  "picked_bid_no": "20260309-001"
}

// STEP 0: 관심과제 없음 (워크플로 종료)
{
  "no_interest": true,
  "reason": "적합한 공고 없음. 예산 규모 및 기한이 맞지 않음."
}

// STEP 0: 재검색 (검색 조건 변경)
{
  "search_query": { "keywords": "AI 플랫폼", "budget_min": 100000000, "region": "서울" }
}

// STEP 0→1: RFP 파일 업로드 (rfp_fetch 게이트)
{
  "rfp_file_text": "... 파싱된 RFP 텍스트 ..."
}

// STEP 0→1: RFP 파일 없이 진행 (G2B 자동 추출분으로 진행)
{
  "skip_upload": true
}

// STEP 1-②: Go → 포지셔닝 확정
{
  "decision": "go",
  "positioning_override": "offensive",
  "approved_by": "김팀장"
}

// STEP 1-②: No-Go (프로젝트 종료)
{
  "decision": "no_go",
  "no_go_reason": "기술 요건 대비 수행실적 부족. 경쟁 우위 확보 어려움.",
  "feedback": "다음 유사 공고 시 재검토",
  "approved_by": "김팀장"
}

// STEP 1-②: Go/No-Go 재검토 요청 (go_no_go 노드 재실행)
{
  "decision": "rejected",
  "feedback": "수행실적 중 유사 프로젝트 누락 확인. 재평가 필요."
}

// STEP 2: 전략 승인 + 대안 선택 (D-6)
{
  "approved": true,
  "selected_alt_id": "A",
  "approved_by": "홍길동"
}

// STEP 2: 포지셔닝 변경 (D-2)
{
  "approved": false,
  "positioning_override": "adjacent",
  "feedback": "분석 결과 인접형이 더 적절. 유사 실적이 있으므로."
}

// STEP 3: 부분 재작업 (D-1)
{
  "approved": false,
  "feedback": "입찰가격 전략 수정 필요. 나머지는 양호.",
  "rework_targets": ["plan_price"],
  "comments": {
    "plan_price": "경쟁사 예상 가격 대비 15% 높음. 재검토 필요."
  }
}

// STEP 4: 부분 재작업 (D-1)
{
  "approved": false,
  "feedback": "수행방안 섹션 보강 필요.",
  "rework_targets": ["approach"],
  "comments": {
    "approach": "기술 아키텍처 다이어그램이 빠져 있음"
  }
}
```

### 12-3. 영향 범위 조회 API (U-5)

```json
// GET /api/proposals/{id}/impact/strategy
// → STEP 2를 재작업하면 영향받는 범위
{
  "target_step": "strategy",
  "affected_steps": [
    { "step": "plan",     "status": "approved", "will_reset": true },
    { "step": "proposal", "status": "approved", "will_reset": true },
    { "step": "ppt",      "status": "pending",  "will_reset": false }
  ],
  "warning": "STEP 3(제안계획)과 STEP 4(정성제안서)의 승인이 초기화됩니다. 재작업이 필요합니다."
}
```

### 12-4. 산출물 / G2B / 역량 DB

| Method | Path | 설명 |
|--------|------|------|
| GET  | `/api/proposals/{id}/artifacts/{step}` | 산출물 조회 |
| GET  | `/api/proposals/{id}/artifacts/{step}/versions` | 버전 이력 |
| GET  | `/api/proposals/{id}/download/docx` | DOCX 다운로드 (**중간 버전 포함**, U-9) |
| GET  | `/api/proposals/{id}/download/pptx` | PPTX 다운로드 |
| GET  | `/api/proposals/{id}/compliance` | Compliance Matrix 현재 상태 |
| GET  | `/api/g2b/search` | 공고 검색 |
| GET  | `/api/g2b/bid/{bid_no}` | 낙찰정보 |
| GET  | `/api/g2b/stats` | 유사 공고 낙찰 통계 |
| GET  | `/api/capabilities` | 역량 목록 |
| POST | `/api/capabilities` | 역량 등록 |
| PUT  | `/api/capabilities/{id}` | 역량 수정 |
| DELETE | `/api/capabilities/{id}` | 역량 삭제 |
| GET  | `/api/capabilities/search` | 키워드 검색 |
| POST | `/api/proposals/{id}/artifacts/{step}/sections/{section_id}/regenerate` | ★ v3.4: 개별 섹션 AI 재생성 (H1) |
| POST | `/api/proposals/{id}/ai-assist` | ★ v3.4: AI 어시스턴트 인라인 제안 (H2) |
| GET  | `/api/proposals/{id}/evaluation` | ★ v3.4: 모의평가 결과 조회 (H3) |
| GET  | `/api/proposals/{id}/artifacts/{step}/diff?v1=N&v2=M` | ★ v3.4: 버전 간 Diff 조회 (M2) |
| GET  | `/api/proposals/{id}/download/hwp` | ★ v3.4: HWP 내보내기 (M3) |

#### 12-4-1. ★ 섹션 AI 재생성 API (v3.4, H1)

> **용도**: §13-10 ProposalEditor의 "AI에게 질문하기" 기능. 기존 `/resume`은 전체 단계 재작업만 가능하므로, 개별 섹션 단위 AI 재생성 엔드포인트 필요.

```python
# POST /api/proposals/{id}/artifacts/{step}/sections/{section_id}/regenerate
# 권한: 프로젝트 참여자 (member, lead)
# 섹션 잠금 보유자만 호출 가능 (SECT_001 에러)
```

```json
// Request
{
  "instruction": "경쟁사 대비 기술적 차별점을 더 구체적으로 서술해주세요.",
  "context": {
    "reference_sections": ["approach", "team"],
    "kb_search_query": "AI 플랫폼 차별화 전략"
  }
}

// Response — 200 OK
{
  "section_id": "technical_approach",
  "content": "...(재생성된 섹션 내용)...",
  "change_source": "ai_revised",
  "tokens_used": 3200,
  "kb_references": [
    {"type": "content_library", "id": "uuid-1", "title": "AI 플랫폼 제안 사례"}
  ]
}
```

#### 12-4-2. ★ AI 어시스턴트 인라인 제안 API (v3.4, H2)

> **용도**: §13-10 EditorAiPanel의 "선택 텍스트 개선 요청". H1(전체 섹션 재생성)과 달리 선택한 텍스트 조각에 대한 경량 호출.

```python
# POST /api/proposals/{id}/ai-assist
# 권한: 프로젝트 참여자 (member, lead)
```

```json
// Request
{
  "section_id": "technical_approach",
  "selected_text": "본 과업은 AI 기술을 활용하여 업무 효율을 높입니다.",
  "instruction": "더 구체적인 수치와 기술 명칭을 포함해 개선",
  "tone": "formal"
}

// Response — 200 OK
{
  "original_text": "본 과업은 AI 기술을 활용하여 업무 효율을 높입니다.",
  "suggested_text": "본 과업은 자연어처리(NLP) 기반 문서 자동 분류 및 RAG(Retrieval-Augmented Generation) 기술을 적용하여, 기존 수작업 대비 문서 처리 시간을 약 60% 단축합니다.",
  "tokens_used": 850,
  "change_type": "enhancement"
}
```

#### 12-4-3. ★ 모의평가 결과 조회 API (v3.4, H3)

> **용도**: §13-11 EvaluationView가 `evaluation_simulation` 데이터(3인 점수, 취약점, Q&A) 필요. 현재 graph state에만 존재하며 REST 엔드포인트 없음.

```python
# GET /api/proposals/{id}/evaluation
# 권한: 프로젝트 참여자 + 팀장/본부장 (결재선 포함)
```

```json
// Response — 200 OK
{
  "proposal_id": "uuid-123",
  "evaluation_at": "2026-03-10T15:00:00Z",
  "evaluators": [
    {
      "persona": "기술 전문가",
      "scores": {
        "technical_approach": 85,
        "project_management": 78,
        "team_composition": 90,
        "price_competitiveness": 72,
        "past_performance": 88
      },
      "total_score": 82.6,
      "comments": "기술적 접근은 우수하나 가격 경쟁력 보완 필요"
    },
    {
      "persona": "발주기관 담당자",
      "scores": { "...": "..." },
      "total_score": 79.2,
      "comments": "RFP 요구사항 대비 충족도 양호"
    },
    {
      "persona": "경쟁사 평가자",
      "scores": { "...": "..." },
      "total_score": 76.8,
      "comments": "차별화 포인트 부족"
    }
  ],
  "average_score": 79.5,
  "weaknesses_top3": [
    {"area": "price_competitiveness", "detail": "경쟁사 예상 가격 대비 12% 높음", "suggestion": "간접비 항목 재검토"},
    {"area": "differentiation", "detail": "기술적 차별화 포인트 불명확", "suggestion": "AI/ML 특화 역량 강조"},
    {"area": "risk_management", "detail": "리스크 대응 계획 미흡", "suggestion": "유사 프로젝트 교훈 반영"}
  ],
  "expected_qa": [
    {"question": "AI 모델 학습 데이터의 보안 관리 방안은?", "suggested_answer": "..."},
    {"question": "기존 시스템과의 연동 테스트 계획은?", "suggested_answer": "..."}
  ]
}
```

#### 12-4-4. ★ 버전 간 Diff 조회 API (v3.4, M2)

> **용도**: DB에 `diff_from_previous` JSONB 있지만, 임의 버전 간 비교를 위한 엔드포인트. 인접 버전 외 v1↔v3 등 교차 비교 지원.

```python
# GET /api/proposals/{id}/artifacts/{step}/diff?v1=2&v2=5
# 권한: 프로젝트 참여자
```

```json
// Response — 200 OK
{
  "step": "proposal",
  "version_from": 2,
  "version_to": 5,
  "sections_changed": [
    {
      "section_id": "technical_approach",
      "change_type": "modified",
      "additions": 12,
      "deletions": 5,
      "diff_html": "<ins>추가된 내용</ins><del>삭제된 내용</del>"
    }
  ],
  "summary": "3개 섹션 수정, 1개 섹션 추가"
}
```

#### 12-4-5. ★ HWP 내보내기 (v3.4, M3)

> **용도**: 한국 공공조달 제안서의 HWP 포맷 지원. 별도 설계문서(`hwp-output.design.md`) 참조. §12-4 인덱스에 추가.

```python
# GET /api/proposals/{id}/download/hwp
# 권한: 프로젝트 참여자
# 응답: application/octet-stream (HWP 바이너리)
# 파라미터: ?template_id=uuid (선택, 회사 HWP 템플릿 적용)
```

---

### 12-6. ★ 인증 API (v2.0)

| Method | Path | 설명 |
|--------|------|------|
| GET  | `/api/auth/login` | Azure AD SSO 로그인 리다이렉트 |
| GET  | `/api/auth/callback` | Azure AD OAuth 콜백 → Supabase 세션 생성 |
| POST | `/api/auth/refresh` | JWT 토큰 갱신 |
| POST | `/api/auth/logout` | 세션 종료 |
| GET  | `/api/auth/me` | 현재 사용자 정보 (역할·소속 포함) |

### 12-7. ★ 사용자·조직 관리 API (v2.0)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET  | `/api/users` | 사용자 목록 | admin |
| GET  | `/api/users/{id}` | 사용자 상세 | admin, self |
| PUT  | `/api/users/{id}/role` | 역할 변경 | admin |
| GET  | `/api/organizations` | 조직 구조 (본부·팀) | admin |
| POST | `/api/organizations/divisions` | 본부 생성 | admin |
| POST | `/api/organizations/teams` | 팀 생성 | admin |
| PUT  | `/api/organizations/teams/{id}` | 팀 수정 (소속 변경 등) | admin |
| GET  | `/api/teams/{id}/members` | 팀원 목록 | lead, admin |
| POST | `/api/proposals/{id}/participants` | 프로젝트 참여자 배정 | lead |
| DELETE | `/api/proposals/{id}/participants/{user_id}` | 참여자 제외 | lead |

### 12-8. ★ 대시보드 API (v2.0)

| Method | Path | 설명 | 대상 역할 |
|--------|------|------|-----------|
| GET  | `/api/dashboard/my-projects` | 내 참여 프로젝트 현황 | member |
| GET  | `/api/dashboard/team` | 팀 제안 파이프라인 (STEP별 분포) | lead |
| GET  | `/api/dashboard/team/performance` | 팀 성과 요약 (수주율·건수) | lead |
| GET  | `/api/dashboard/division` | 본부 제안 현황 (팀별 비교) | director |
| GET  | `/api/dashboard/division/approvals` | 결재 대기 건 목록 | director |
| GET  | `/api/dashboard/company` | 전사 제안 현황 | executive |
| GET  | `/api/dashboard/company/kpi` | 전사 KPI (수주율 추이·분야 분석) | executive |
| GET  | `/api/dashboard/admin/stats` | 시스템 통계 (사용자·프로젝트 수) | admin |

### 12-9. ★ 성과 추적 API (v2.0)

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/proposals/{id}/result` | 제안 결과 등록 (수주/패찰/유찰) — 팀장 |
| GET  | `/api/performance/individual/{user_id}` | 개인 성과 (참여·완료·수주 건수) |
| GET  | `/api/performance/team/{team_id}` | 팀 성과 (수주율·건수·평균 소요일) |
| GET  | `/api/performance/division/{div_id}` | 본부 성과 (수주율·누적 수주액) |
| GET  | `/api/performance/company` | 전사 성과 (포지셔닝별 수주율) |
| GET  | `/api/performance/trends` | 기간별 추이 (월/분기/연, 필터 가능) |

### 12-10. ★ 알림 API (v2.0)

| Method | Path | 설명 |
|--------|------|------|
| GET  | `/api/notifications` | 내 알림 목록 (읽음/안읽음) |
| PUT  | `/api/notifications/{id}/read` | 알림 읽음 처리 |
| PUT  | `/api/notifications/read-all` | 전체 읽음 처리 |
| GET  | `/api/notifications/settings` | 알림 설정 조회 |
| PUT  | `/api/notifications/settings` | 알림 설정 변경 (ON/OFF, 채널) |

### 12-11. ★ 감사 로그 API (v2.0)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET  | `/api/audit-logs` | 감사 로그 조회 (기간·사용자·행위 필터) | admin |

### 12-12. ★ v3.0 추가 API (교차 참조)

> 아래 API들은 각 설계 섹션에서 상세히 정의됨. 요약 인덱스만 제공.

| 영역 | API 그룹 | 상세 섹션 |
|------|----------|-----------|
| KB 콘텐츠 라이브러리 | `GET/POST/PUT/DELETE /api/kb/content/*` | §20-4 |
| KB 발주기관 DB | `GET/POST/PUT /api/kb/clients/*` | §20-4 |
| KB 경쟁사 DB | `GET/POST/PUT /api/kb/competitors/*` | §20-4 |
| KB 교훈 아카이브 | `GET/POST /api/kb/lessons/*` | §20-4 |
| KB 통합 검색 | `GET /api/kb/search` | §20-4 |
| KB 내보내기 | `GET /api/kb/export/{part}` | §20-4 |
| AI 실행 상태 | `GET/POST/DELETE /api/ai-status/*` | §22 |
| 동시 편집 잠금 | `POST/DELETE/GET /api/proposals/{id}/sections/*/lock` | §24 |
| 회사 템플릿 | `GET/POST/PUT/DELETE /api/templates/*` | §26 |
| 사용자 관리 (v3.0 확장) | `POST /api/users/bulk`, `PUT /api/users/{id}/deactivate`, `POST /api/users/{id}/delegate` | §23 |
| KB 원가기준 (노임단가) ★ v3.4 | `GET/POST/PUT/DELETE /api/kb/labor-rates`, `POST /api/kb/labor-rates/import` | §13-13, §15-5h |
| KB 낙찰가 벤치마크 ★ v3.4 | `GET/POST/PUT/DELETE /api/kb/market-prices` | §13-13, §15-5i |

### 12-5. SSE 클라이언트 자동 재연결 (U-6)

```typescript
// frontend/lib/sse.ts
export function createSSEClient(proposalId: string) {
  let retryCount = 0;
  const MAX_RETRIES = 5;

  function connect() {
    const es = new EventSource(`/api/proposals/${proposalId}/stream`);

    es.onmessage = (event) => {
      retryCount = 0;  // 성공 시 리셋
      const data = JSON.parse(event.data);
      // 프론트엔드 상태 업데이트
      handleStreamEvent(data);
    };

    es.onerror = () => {
      es.close();
      if (retryCount < MAX_RETRIES) {
        retryCount++;
        // 지수 백오프 재연결
        setTimeout(connect, Math.min(1000 * 2 ** retryCount, 30000));
      } else {
        // 재연결 실패 → GET /state 로 현재 상태 복원
        fetchCurrentState(proposalId);
      }
    };

    return es;
  }

  return connect();
}
```

### 12-13. ★ 분석 대시보드 API (v3.4)

> **용도**: §13-12 AnalyticsPage의 4개 차트 데이터 소스. 기존 §12-8(대시보드)/§12-9(성과 추적)는 역할별 원시 데이터 제공이며, 차트에 필요한 집계(aggregation) API가 없음.

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/analytics/failure-reasons?period=2026Q1` | 실패 원인 분포 (파이 차트) |
| GET | `/api/analytics/positioning-win-rate?period=2026Q1` | 포지셔닝별 수주율 (바 차트) |
| GET | `/api/analytics/monthly-trends?from=2025-10&to=2026-03` | 월별 수주율 추이 (라인 차트) |
| GET | `/api/analytics/client-win-rate?period=2026Q1` | 기관별 수주 현황 (바 차트) |

> **권한**: lead, director, executive, admin. member는 자신이 참여한 프로젝트 범위 내에서만 조회 가능.
> **기간 파라미터**: `period` = `2026Q1`, `2026H1`, `2025` 형식. `from`/`to` = `YYYY-MM` 형식.
> **스코프**: `?scope=team|division|company` (기본값: 사용자 역할에 따라 자동 결정)

#### Response 예시

```json
// GET /api/analytics/failure-reasons?period=2026Q1
{
  "period": "2026Q1",
  "scope": "company",
  "total_failed": 12,
  "reasons": [
    {"reason": "가격 경쟁력 부족", "count": 5, "percentage": 41.7},
    {"reason": "기술 제안 미흡", "count": 3, "percentage": 25.0},
    {"reason": "수행실적 부족", "count": 2, "percentage": 16.7},
    {"reason": "컨소시엄 구성 약점", "count": 1, "percentage": 8.3},
    {"reason": "기타/불명", "count": 1, "percentage": 8.3}
  ]
}

// GET /api/analytics/positioning-win-rate?period=2026Q1
{
  "period": "2026Q1",
  "scope": "company",
  "positionings": [
    {"positioning": "offensive", "total": 8, "won": 5, "win_rate": 62.5},
    {"positioning": "defensive", "total": 6, "won": 2, "win_rate": 33.3},
    {"positioning": "adjacent", "total": 4, "won": 3, "win_rate": 75.0},
    {"positioning": "exploratory", "total": 2, "won": 0, "win_rate": 0.0}
  ]
}
```

---

## 13. 프론트엔드 핵심 컴포넌트

### 13-1. 프로젝트 목록 (U-10)

```
┌────────────────────────────────────────────────────────────────┐
│  📋 제안 프로젝트 목록          [ 🔍 공고 검색 ] [ + 직접 등록 ] │
├──────────────────┬─────────┬────────┬───────────┬─────────────┤
│  프로젝트명       │ 포지셔닝 │ 단계   │ 마감일     │ 상태        │
├──────────────────┼─────────┼────────┼───────────┼─────────────┤
│  AI 플랫폼 구축   │ ⚔️ 공격  │ STEP 3 │ 03-20     │ ⏳ 검토 대기 │
│  시스템 운영 2차   │ 🛡️ 수성  │ STEP 4 │ 03-15     │ 🔄 재작업중  │
│  데이터 분석 체계  │ 🔄 인접  │ STEP 1 │ 04-01     │ ✋ Go 결정   │
│  클라우드 전환     │ —       │ —      │ 03-25     │ ❌ No-Go     │
│  스마트시티 용역   │ —       │ STEP 0 │ 03-30     │ 🚫 관심없음  │
└──────────────────┴─────────┴────────┴───────────┴─────────────┘
```

### 13-1-1. 워크플로 진행 상태 — PhaseGraph (U-5) ★ v3.4 개정

> **v3.4 변경**: 기존 수직 타임라인/수평 프로그레스바 → **수평 Phase 그래프**로 교체.
> §13-7 `ParallelProgress`와 결합하여 병렬 fan-out 노드를 시각적으로 표현한다.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   STEP 0        STEP 1              STEP 2     STEP 3        STEP 4    STEP 5│
│                                                                              │
│   ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐   ┌──┐ ┌──┐  ┌──────┐     ┌──┐  ┌──┐ ┌──┐│
│   │검│→│업│→│분│→│조│→│Go│→│전│→│계│→│팀│가│일│→│제│→│발│→│PP││
│   │색│  │로│  │석│  │사│  │No│  │략│ │획│ │  격  정│  │안│  │표│  │T ││
│   │  │  │드│  │  │  │  │  │Go│  │  │ │  │ │스토리  │  │서│  │전│  │  ││
│   └✅┘  └✅┘  └✅┘  └✅┘  └●─┘   └○┘ └○┘ └──────┘  └○┘  └○┘ └○┘│
│                          ↑         🔍                               │
│                       [검토중]   체크포인트                            │
│                                                                              │
│   ● = 현재  ✅ = 완료  🔍 = 체크포인트(승인 대기)  ○ = 미시작            │
│   ═══ 병렬 fan-out (STEP 3: 팀/담당/일정/스토리/가격 동시 실행)          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

> **구현 명세**:
> - 컴포넌트: `PhaseGraph.tsx` (기존 `WorkflowProgress.tsx` 대체)
> - 노드 타입: `completed` | `active` | `review_pending` | `pending`
> - 체크포인트 배지: review 게이트 위치에 `approved` | `pending` | `rejected` 상태 표시
> - 병렬 분기 표시: STEP 3 (plan_*×5), STEP 4 (proposal_*×N), STEP 5 (ppt_*×N)를 묶어 표시
> - 반응형: 모바일에서는 접히는 세로 타임라인으로 폴백

### 13-2. 공고 검색·추천 패널 — RfpSearchPanel (STEP 0)

> **최대 5건** 추천. 각 공고의 요약정보(사업개요, 주요 요구사항, 평가방식, 경쟁강도)를
> 제공하여 사용자가 **1개 관심과제를 선정**하거나, 관심과제 없음으로 종료할 수 있다.

```
┌──────────────────────────────────────────────────────────────────────┐
│  🔍 RFP 공고 검색·추천 (최대 5건)                          [ × 닫기 ] │
├──────────────────────────────────────────────────────────────────────┤
│  검색 조건                                                           │
│  키워드: [ AI 플랫폼 구축          ]  예산: [ 1억 이상 ▼ ]            │
│  지역: [ 전체 ▼ ]  마감: [ 30일 이내 ▼ ]   [ 🔍 검색 ]              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📋 AI 추천 결과 (적합도순, 3/5건)     💡 1개 과제를 선택하세요       │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ ○ ⭐ 92점  AI 플랫폼 구축 용역         한국정보화진흥원        │  │
│  │   예산: 5.2억 | 마감: 2026-03-25 | 예상 포지셔닝: ⚔️ 공격형   │  │
│  │                                                                │  │
│  │   📌 사업개요: AI 기반 공공서비스 통합 플랫폼을 구축하여       │  │
│  │      민원처리 자동화 및 데이터 분석 체계를 수립하는 사업        │  │
│  │   📋 주요 요구사항:                                            │  │
│  │      • AI/ML 모델 개발 및 학습 파이프라인 구축                 │  │
│  │      • 기존 레거시 시스템 연계 API 개발                        │  │
│  │      • 사용자 교육 및 운영 매뉴얼 납품                         │  │
│  │   📊 평가방식: 기술 60 : 가격 40 (협상에 의한 계약)            │  │
│  │   🏁 경쟁강도: 보통 — 전문성 요구 높아 참여업체 제한적         │  │
│  │   💡 적합도: "자사 AI 플랫폼 실적 3건, 핵심 인력 보유"         │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │ ○ 78점  공공 데이터 분석 체계 구축     행정안전부              │  │
│  │   예산: 3.1억 | 마감: 2026-04-01 | 예상 포지셔닝: 🔄 인접형   │  │
│  │                                                                │  │
│  │   📌 사업개요: 공공기관 보유 데이터를 표준화하고 분석 체계를   │  │
│  │      구축하여 정책 의사결정을 지원하는 사업                     │  │
│  │   📋 주요 요구사항:                                            │  │
│  │      • 데이터 표준화 및 품질관리 체계 수립                     │  │
│  │      • 분석 대시보드 및 시각화 도구 개발                       │  │
│  │      • 데이터 거버넌스 정책 수립                                │  │
│  │   📊 평가방식: 기술 70 : 가격 30 (기술 중심)                   │  │
│  │   🏁 경쟁강도: 높음 — 유사 사업 경험 업체 다수                 │  │
│  │   💡 적합도: "데이터 분석 유사 실적 있으나 공공분야 첫 진입"   │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │ ○ 65점  시스템 운영 유지보수 3차       교육부                  │  │
│  │   예산: 2.0억 | 마감: 2026-03-20 | 예상 포지셔닝: 🛡️ 수성형   │  │
│  │   ... (접힌 상태, 클릭하면 요약 펼침)                          │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│       [ 🚫 관심과제 없음 (종료) ]         [ ✅ 선정하여 STEP 1 진행 ] │
└──────────────────────────────────────────────────────────────────────┘
```

> **UX 동작**: 라디오(○) 1개 선택 → [✅ 선정하여 STEP 1 진행] 활성화.
> 하위 3건은 접힌 상태로 표시, 클릭 시 요약정보 펼침.
> 적합도 낮은 순서대로 접힘 기본 적용.

### 13-3. RFP 파일 업로드 게이트 — rfp_fetch (STEP 0→1 전환)

```
┌──────────────────────────────────────────────────────────────────────┐
│  📋 공고 상세 — AI 플랫폼 구축 용역                       [ × 닫기 ] │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  공고번호: 20260309-001          발주기관: 한국정보화진흥원           │
│  예산: 5.2억                     마감: 2026-03-25                    │
│                                                                      │
│  ▼ 공고 상세 설명                                                    │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ 본 사업은 AI 기반 공공서비스 플랫폼을 구축하여 ...              │  │
│  │ (G2B에서 자동 수집된 내용)                                      │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  📎 G2B 첨부파일                                                     │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ ✅ 제안요청서.pdf (자동 추출 완료, 32p)                         │  │
│  │    제안요청서_별첨.hwp                                          │  │
│  │    과업지시서.pdf                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  📄 RFP 원본 파일 (선택)                                             │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  G2B에서 RFP를 자동 추출했습니다.                               │  │
│  │  더 정확한 분석을 위해 별도 RFP 파일을 업로드할 수 있습니다.    │  │
│  │                                                                  │  │
│  │  [ 📤 RFP 파일 업로드 (PDF/HWP) ]                               │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│       [ ← 다른 공고 선택 ]      [ ▶ G2B 추출분으로 진행 ]           │
│                                  [ ▶ 업로드 파일로 진행 ]            │
└──────────────────────────────────────────────────────────────────────┘
```

### 13-4. Go/No-Go 의사결정 패널 — GoNoGoPanel (STEP 1-②)

```
┌──────────────────────────────────────────────────────────────────────┐
│  [STEP 1-②] Go/No-Go 의사결정                          [ × 닫기 ]  │
│  🔍 리뷰 관점: 의사결정자 — "이 입찰에 자원을 투입할 가치가 있는가?" │
├──────────────────────────────┬───────────────────────────────────────┤
│                              │                                       │
│  📊 AI 수주 가능성 평가       │  🏷️ 포지셔닝 추천                     │
│                              │                                       │
│  종합 점수:  ████████░░ 78점  │  AI 추천: ⚔️ 공격형 (Offensive)       │
│                              │  "자사 유사 실적 3건 + 기술 우위"     │
│  ┌────────────────────────┐ │                                       │
│  │ 기술 적합도:    85점    │ │  포지셔닝 변경:                       │
│  │ 수행실적 부합:  72점    │ │  ○ 🛡️ 수성형  ● ⚔️ 공격형  ○ 🔄 인접형│
│  │ 가격 경쟁력:   70점    │ │                                       │
│  │ 경쟁 환경:     82점    │ │                                       │
│  └────────────────────────┘ │                                       │
│                              │                                       │
│  ✅ 강점 (Pros)              │  ⚠️ 리스크 (Risks)                    │
│  • AI 플랫폼 구축 실적 3건   │  • 예산 대비 요구 범위 넓음           │
│  • 핵심 기술인력 보유        │  • 경쟁사 A社 기존 수행업체           │
│  • 평가항목 기술배점 60%     │  • 마감까지 15일 촉박                │
│                              │                                       │
│  AI 추천: ✅ Go              │                                       │
│                              ├───────────────────────────────────────┤
│                              │  💬 의사결정 사유 (선택)               │
│                              │  ┌─────────────────────────────────┐ │
│                              │  │                                 │ │
│                              │  └─────────────────────────────────┘ │
│                              │                                       │
│                              │  ──────────────────────────────────── │
│                              │  [ ❌ No-Go ] [ 🔄 재검토 ] [ ✅ Go ] │
└──────────────────────────────┴───────────────────────────────────────┘
```

### 13-5. 리뷰 패널 — 빠른 승인 + 부분 재작업 (D-1, U-2) ★ v3.4 보강

> **v3.4 변경**: ProposalForge 탭 기반 멀티 산출물 리뷰 구조 반영.
> - ★ AI 이슈 플래그: 자가진단 점수 기반 약점 자동 하이라이트 (⚠️ 배지)
> - ★ 섹션별 인라인 피드백: 전체 코멘트 박스 → 항목별 개별 코멘트
> - 기존 빠른 승인/부분 재작업 체크박스는 유지

```
┌──────────────────────────────────────────────────────────────────────┐
│  [STEP 3] 제안계획서 검토                             [ × 닫기 ]     │
│  🔍 리뷰 관점: Pink Team (실행 검증)                                  │
│  "이 계획대로 실행 가능한가? 일정은 현실적인가?"                      │
│  🏷️ 포지셔닝: 🛡️ 수성형                                              │
├─────────────────────────────┬────────────────────────────────────────┤
│  📄 산출물 (탭)              │  💬 섹션별 피드백         ★ v3.4       │
│                             │                                        │
│  [팀구성✅][담당자✅][일정✅] │  ▼ 입찰가격 피드백                      │
│  [스토리라인✅][가격⚠️]      │  ┌────────────────────────────────┐    │
│                             │  │  이 섹션에 대한 코멘트          │    │
│  ▼ 입찰가격 (선택됨)        │  │  입찰가격만 재검토 필요         │    │
│  ┌─────────────────────┐   │  └────────────────────────────────┘    │
│  │ 추천가: 3.2억        │   │                                        │
│  │ 최저가: 2.8억        │   │  ▼ 스토리라인 피드백 (선택적)           │
│  │ 근거: ...            │   │  ┌────────────────────────────────┐    │
│  └─────────────────────┘   │  │                                │    │
│                             │  └────────────────────────────────┘    │
│  ⚠️ AI 이슈 플래그  ★ v3.4  │                                        │
│  ┌─────────────────────┐   │  ☑️ 재작업 항목 선택                    │
│  │ ⚠ 가격: 최저가와의  │   │  □ plan_team     □ plan_assign          │
│  │   차이 15% 초과      │   │  □ plan_schedule □ plan_story           │
│  │ ⚠ 일정: 납품 마감   │   │  ☑ plan_price ← 이것만 재작업           │
│  │   여유 3일 미만      │   │                                        │
│  └─────────────────────┘   │  ────────────────────────────────────── │
│                             │  [⚡빠른 승인] [재작업 요청] [✅ 승인]  │
└─────────────────────────────┴────────────────────────────────────────┘
```

> **AI 이슈 플래그 데이터 소스**:
> - `self_review` 노드의 `evaluation_simulation` 결과에서 약점 항목 추출
> - 4축 점수 (compliance/strategy/quality/trustworthiness) 중 70점 미만 항목 자동 하이라이트
> - 이슈 플래그 클릭 시 해당 산출물 탭으로 스크롤 + 관련 섹션 강조

### 13-6. 포지셔닝 변경 영향 미리보기 (D-2, U-8)

```
┌──────────────────────────────────────────────────────────────┐
│  ⚠️ 포지셔닝 변경 영향 미리보기                                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  현재: 🛡️ 수성형 (Defensive) → 변경: 🔄 인접형 (Adjacent)    │
│                                                              │
│  변경 시 영향:                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Ghost Theme: "교체 리스크" → "타 기관 성공 사례 적용"  │    │
│  │ Win Theme:   "실적 강조" → "유사 실적 전이 논리"       │    │
│  │ 가격 전략:   프리미엄 → 중간 수준                      │    │
│  │ 인력 구성:   현 수행 인력 → 유사 경험자 강조           │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ⚠️ STEP 2(제안전략)부터 재생성됩니다.                        │
│     STEP 3~5 기존 승인은 초기화됩니다.                        │
│                                                              │
│           [ 취소 ]          [ 포지셔닝 변경 확정 ]            │
└──────────────────────────────────────────────────────────────┘
```

### 13-7. 병렬 작업 진행 + 선검토 (U-4) ★ v3.4 보강

> **v3.4 변경**: PhaseGraph (§13-1-1)의 병렬 분기 표시와 연동.
> 프로젝트 상세 페이지에서 병렬 fan-out 구간 진입 시 자동 확장 표시.

```
┌──────────────────────────────────────────────────────┐
│  STEP 3 병렬 작업 진행 상황                            │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ████████████ 팀구성     ✅ 완료  [ 👁️ 미리보기 ]    │
│  ████████████ 담당자     ✅ 완료  [ 👁️ 미리보기 ]    │
│  ██████████░░ 일정       ⏳ 진행 중                   │
│  ████████████ 스토리라인  ✅ 완료  [ 👁️ 미리보기 ]   │
│  ████████████ 입찰가격   ✅ 완료  [ 👁️ 미리보기 ]    │
│                                                      │
│  4/5 완료 — 완료 항목은 미리보기로 사전 검토 가능     │
│                                                      │
│  ★ AI 상태                                           │
│  ┌────────────────────────────────────────────┐      │
│  │ 🤖 Claude: 일정 생성 중 (토큰: 2,340/4,000)│      │
│  │ ⏱️ 경과: 12초 | 예상 완료: ~8초             │      │
│  └────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────┘
```

> **구현 명세**:
> - `ParallelProgress.tsx` + `AiStatusPanel.tsx` 결합 표시
> - SSE 이벤트 (`phase_progress`, `node_heartbeat`)로 실시간 갱신
> - 미리보기 클릭 시 `ArtifactViewer` 모달 열림 (읽기 전용)

### 13-8. ★ 역할별 대시보드 (v2.0)

#### 13-8-1. 팀장 대시보드 — 팀 파이프라인

```
┌──────────────────────────────────────────────────────────────────────┐
│  📋 AI사업팀 제안 파이프라인                        김팀장 (Lead)     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📊 팀 성과 요약                                                     │
│  ┌──────────┬──────────┬──────────┬──────────┐                      │
│  │ 진행 중   │ 완료      │ 수주     │ 수주율    │                      │
│  │  5건      │  12건     │  8건     │  66.7%   │                      │
│  └──────────┴──────────┴──────────┴──────────┘                      │
│                                                                      │
│  📌 STEP별 프로젝트 분포                                              │
│  STEP 0 (검색)  ██ 2                                                 │
│  STEP 1 (분석)  ███ 3                                                │
│  STEP 2 (전략)  █ 1                                                  │
│  STEP 3 (계획)  █ 1                                                  │
│  STEP 4 (제안)  ██ 2                                                 │
│  STEP 5 (PPT)  █ 1                                                   │
│                                                                      │
│  ⚠️ 결재 대기                                                        │
│  ┌──────────────────────────────────────────────┐                    │
│  │ • AI 플랫폼 구축 — STEP 1-② Go/No-Go 결정 필요                │    │
│  │ • 데이터 분석 체계 — STEP 2 전략 승인 대기                     │    │
│  └──────────────────────────────────────────────┘                    │
│                                                                      │
│  ⏰ 마감 임박 (D-7 이내)                                             │
│  ┌──────────────────────────────────────────────┐                    │
│  │ • 시스템 운영 2차 — D-3 (03-12) — STEP 4 진행 중              │    │
│  └──────────────────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────────────────┘
```

#### 13-8-2. 경영진 대시보드 — 전사 KPI

```
┌──────────────────────────────────────────────────────────────────────┐
│  📊 전사 제안 현황                             이대표 (Executive)     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────┐          │
│  │  2026 1Q 전사 KPI                                       │          │
│  │  ┌──────────┬──────────┬──────────┬──────────────────┐ │          │
│  │  │ 제안 건수 │ 수주 건수 │ 수주율    │ 누적 수주액      │ │          │
│  │  │  28건     │  18건    │  64.3%   │  142억           │ │          │
│  │  └──────────┴──────────┴──────────┴──────────────────┘ │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                      │
│  📈 월별 수주율 추이                                                 │
│  100%│                                                               │
│   80%│        ●──●                                                   │
│   60%│  ●──●       ──●                                              │
│   40%│                                                               │
│      └──┬──┬──┬──┬──┬──                                            │
│        10  11  12  1   2   3                                         │
│                                                                      │
│  📋 본부별 비교                                                      │
│  ┌─────────────────┬─────────┬────────┬──────────┐                  │
│  │ 본부              │ 진행 건 │ 수주율  │ 평균 소요 │                  │
│  ├─────────────────┼─────────┼────────┼──────────┤                  │
│  │ ICT사업본부      │  15건   │ 71.4%  │  18일    │                  │
│  │ 공공사업본부      │  13건   │ 55.6%  │  22일    │                  │
│  └─────────────────┴─────────┴────────┴──────────┘                  │
│                                                                      │
│  📊 포지셔닝별 수주율                                                │
│  🛡️ 수성형: 85.7% (7/6)  ⚔️ 공격형: 50.0% (8/4)  🔄 인접형: 60.0% (5/3)│
└──────────────────────────────────────────────────────────────────────┘
```

#### 13-8-3. 결재선 현황 표시 — ApprovalChainStatus

```
┌────────────────────────────────────────────────────────────┐
│  🔐 결재선 (예산 5.2억 → 팀장 → 본부장 → 경영진)           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ✅ 김팀장 (Lead)        2026-03-09 14:30  "Go 결정"       │
│  → ⏳ 박본부장 (Director) 승인 대기                         │
│  → ○ 이대표 (Executive)  —                                 │
│                                                            │
│  💬 Teams 알림: 박본부장에게 승인 요청 발송됨               │
└────────────────────────────────────────────────────────────┘
```

### 13-9. 워크플로 내 역량 DB 인라인 편집 (U-7)

```
┌──────────────────────────────────────────────────┐
│  💡 이 실적을 제안서에 포함하고 싶은데             │
│     역량 DB에 등록되어 있지 않습니다.              │
│                                                  │
│  [ + 역량 DB에 바로 등록 ]                        │
│                                                  │
│  ┌─────────────────────────────────────────┐     │
│  │ 유형: ○ 수행실적  ○ 기술역량  ○ 인력    │     │
│  │ 제목: [                              ]  │     │
│  │ 상세: [                              ]  │     │
│  │ 키워드: [                            ]  │     │
│  │        [ 취소 ]    [ 등록 + 제안서 반영 ]│     │
│  └─────────────────────────────────────────┘     │
└──────────────────────────────────────────────────┘
```

### 13-10. ★ 인브라우저 제안서 편집기 — ProposalEditor (v3.4)

> **배경**: 기존 "생성→다운로드" 모델에서 "생성→리뷰→협업 편집" 모델로 전환.
> TENOPA의 가장 큰 UX 격차를 해소하는 핵심 컴포넌트.
> 라우트: `/projects/[id]/edit`

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  📝 제안서 편집 — AI 플랫폼 구축 용역               [저장] [DOCX 내보내기]  │
├───────────────┬────────────────────────────────────┬─────────────────────────┤
│               │                                    │                         │
│  📋 목차       │  Tiptap 에디터 (중앙)              │  🤖 AI 어시스턴트       │
│               │                                    │                         │
│  1. 사업이해   │  ## 1. 사업의 이해                 │  📊 요건 충족률          │
│  2. 추진전략 ◀│                                    │  ████████░░ 82%         │
│  3. 수행방안   │  본 사업은 AI 기반 공공서비스       │                         │
│  4. 조직구성   │  통합 플랫폼을 구축하여 민원처리   │  📋 Win Strategy 반영   │
│  5. 일정계획   │  자동화 및 데이터 분석 체계를       │  ✅ Ghost Theme 반영     │
│  6. 가격제안   │  수립하는 사업입니다.               │  ✅ Win Theme 반영       │
│               │                                    │  ⚠️ 차별화 포인트 부족   │
│  ─────────── │  [AI 제안 코멘트가 인라인으로       │                         │
│               │   노란 하이라이트로 표시됨]         │  🔍 출처 참조            │
│  📊 Compliance│                                    │  • KB-C023: 유사 실적   │
│  Matrix       │  💡 "이 부분에 자사의 AI 파이프라인│  • KB-I012: 기관 선호도 │
│               │     실적을 추가하면 차별화됩니다"   │                         │
│  ✅ 1.1 요건  │                                    │  📝 변경 이력           │
│  ✅ 1.2 요건  │                                    │  • 14:30 섹션 2 수정    │
│  ⚠️ 1.3 요건 │                                    │  • 14:15 AI 코멘트 반영  │
│  ✅ 2.1 요건  │                                    │  • 13:50 초안 생성       │
│               │                                    │                         │
│  ─────────── │                                    │  ─────────────────────  │
│  🔒 섹션 잠금 │  [편집 도구바: B I U 링크 표 이미지]│  [💡 AI에게 질문하기]   │
│  김팀장: §3   │                                    │  ┌───────────────────┐ │
│               │                                    │  │                   │ │
│               │                                    │  └───────────────────┘ │
├───────────────┴────────────────────────────────────┴─────────────────────────┤
│  마지막 저장: 14:35 | 현재 편집자: 이대리 | 🔒 §3 잠금: 김팀장              │
└──────────────────────────────────────────────────────────────────────────────┘
```

> **구현 명세**:
> - **에디터**: `@tiptap/react` + `@tiptap/starter-kit` + `@tiptap/extension-highlight` (AI 코멘트)
> - **좌측 패널** (`EditorTocPanel.tsx`):
>   - 목차: 제안서 섹션 트리 (클릭 시 에디터 스크롤)
>   - Compliance Matrix: `compliance_matrix` 데이터 (§10) 실시간 연동
>   - 섹션 잠금 현황: `SectionLockIndicator` (§24) 연동
> - **중앙 에디터**:
>   - Tiptap 에디터 — 섹션별 편집, 인라인 AI 코멘트 (노란 하이라이트)
>   - AI 코멘트 출처: `self_review` 노드의 피드백 + KB 참조 (`SourceMarker` 연동)
>   - 향후 공동 편집: `@tiptap/extension-collaboration` + Yjs (v2 이후)
> - **우측 패널** (`EditorAiPanel.tsx`):
>   - 요건 충족률 게이지: compliance_matrix 기반 자동 계산
>   - Win Strategy 반영도 체크리스트: strategy 노드 출력의 ghost/win theme 매칭
>   - KB 출처 참조 링크: `SourceMarker` 연동
>   - 변경 이력: `artifacts.change_source` (§15-4) 연동
>   - AI 질문: 선택 텍스트에 대해 AI에게 개선 요청 (Claude API 호출)
> - **데이터 소스**: `artifacts` 테이블 (STEP 4 proposal 결과), `compliance_matrix`, `evaluation_simulation`
> - **저장**: 자동 저장 (debounce 3초) + 수동 저장 버튼. `artifacts.change_source = 'human_edit'`
> - **DOCX 내보내기**: 편집 결과를 `docx_builder.py`에 전달하여 최종 DOCX 생성

### 13-11. ★ 모의평가 결과 시각화 — EvaluationView (v3.4)

> **배경**: v3.2에서 `self_review` 3인 페르소나 시뮬레이션 + `evaluation_simulation` 상태 필드를
> 설계했으나, 이 데이터를 표시할 전용 UI가 없었음. ProposalForge의 평가 시각화 참조.
> 라우트: `/projects/[id]/evaluation`

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  📊 모의평가 결과 — AI 플랫폼 구축 용역                        [ × 닫기 ]   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  종합 점수: 82.5 / 100                                                      │
│                                                                              │
│  ┌─────────────────────────────────┬─────────────────────────────────────┐  │
│  │  👤 평가위원 A (기술 전문가)     │         📊 4축 레이더 차트           │  │
│  │  종합: 85점                      │                                     │  │
│  │  ┌────────────────────────┐    │         Compliance (88)              │  │
│  │  │ 적합성:  88점           │    │              ▲                       │  │
│  │  │ 전략성:  82점           │    │         ╱    │    ╲                  │  │
│  │  │ 품질:    86점           │    │       ╱      │      ╲               │  │
│  │  │ 신뢰성:  84점           │    │  Strategy ───┼─── Quality           │  │
│  │  └────────────────────────┘    │   (79)   ╲   │   ╱  (83)            │  │
│  │                                 │            ╲  │  ╱                   │  │
│  │  👤 평가위원 B (사업관리)        │              ▼                       │  │
│  │  종합: 78점                      │       Trustworthiness (80)          │  │
│  │  ┌────────────────────────┐    │                                     │  │
│  │  │ 적합성:  80점           │    │   ── 현재 점수                      │  │
│  │  │ 전략성:  72점           │    │   -- 목표 점수 (85)                 │  │
│  │  │ 품질:    82점           │    │                                     │  │
│  │  │ 신뢰성:  78점           │    │                                     │  │
│  │  └────────────────────────┘    │                                     │  │
│  │                                 │                                     │  │
│  │  👤 평가위원 C (발주기관 관점)   │                                     │  │
│  │  종합: 84점                      │                                     │  │
│  │  ┌────────────────────────┐    │                                     │  │
│  │  │ 적합성:  86점           │    │                                     │  │
│  │  │ 전략성:  83점           │    │                                     │  │
│  │  │ 품질:    81점           │    │                                     │  │
│  │  │ 신뢰성:  86점           │    │                                     │  │
│  │  └────────────────────────┘    │                                     │  │
│  └─────────────────────────────────┴─────────────────────────────────────┘  │
│                                                                              │
│  ⚠️ 취약점 TOP 3                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ 1. 전략성 평균 79점 — "차별화 포인트가 명확하지 않음"                 │  │
│  │    📍 관련 섹션: §2 추진전략  [ 편집기에서 열기 ]                     │  │
│  │ 2. 신뢰성 평균 83점 — "유사 프로젝트 성과 데이터 부족"               │  │
│  │    📍 관련 섹션: §4 수행실적  [ 편집기에서 열기 ]                     │  │
│  │ 3. 품질 평균 83점 — "테스트 계획의 구체성 보완 필요"                  │  │
│  │    📍 관련 섹션: §3 수행방안  [ 편집기에서 열기 ]                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ❓ 예상 Q&A (발표전략 노드 출력)                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ ▶ Q1. AI 모델 학습 데이터 보안 방안은?                                │  │
│  │   모범답변: "데이터 익명화 3단계 프로세스를 적용하며..."              │  │
│  │ ▶ Q2. 기존 레거시 시스템 연계 시 다운타임 최소화 방안은?             │  │
│  │   모범답변: "블루-그린 배포 전략으로 무중단 전환..."                   │  │
│  │ ▶ Q3. 유지보수 인력 전환 계획은?                                      │  │
│  │   모범답변: "3개월 단계별 기술 이전 프로그램..."                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  [ ← 프로젝트 상세 ]   [ 📝 편집기에서 개선하기 ]   [ 📥 PDF 내보내기 ]     │
└──────────────────────────────────────────────────────────────────────────────┘
```

> **구현 명세**:
> - 점수 카드: `evaluation_simulation.evaluators[].scores` 데이터 렌더링
> - 레이더 차트: `EvaluationRadarChart.tsx` — Recharts `<RadarChart>` 사용
>   - 4축: compliance / strategy / quality / trustworthiness (§29의 100점 체계)
>   - 현재 점수 + 목표 점수(85점) 이중 레이어
> - 취약점 TOP 3: `evaluation_simulation.weaknesses[]` 배열에서 추출
>   - "편집기에서 열기" → `/projects/[id]/edit#section-N` 링크
> - 예상 Q&A: `presentation_strategy` 노드 출력의 `expected_qa[]` 렌더링 (아코디언)
> - 데이터 갱신: `self_review` 재실행 시 자동 갱신 (SSE `evaluation_updated` 이벤트)

### 13-12. ★ 분석 대시보드 — AnalyticsPage (v3.4)

> **배경**: 기존 대시보드에 기본 KPI만 제공. 실패 원인 분석, 포지셔닝별 수주율 분석 등
> 데이터 기반 인사이트가 부족. ProposalForge의 분석 기능 중 선별 채택.
> 라우트: `/analytics`

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  📊 제안 분석 대시보드                                     기간: [2026 1Q ▼] │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────┬───────────────────────────────────────┐  │
│  │  📉 실패 원인 분석             │  📊 포지셔닝별 수주율                  │  │
│  │                               │                                       │  │
│  │     ┌───┐                     │  🛡️ 수성형  ████████████ 85.7% (6/7) │  │
│  │     │   │ 가격 경쟁력 40%      │  ⚔️ 공격형  ██████░░░░░ 50.0% (4/8) │  │
│  │     ├───┤                     │  🔄 인접형  ████████░░░ 60.0% (3/5) │  │
│  │     │   │ 실적 부족  25%       │                                       │  │
│  │     ├───┤                     │  💡 인사이트:                          │  │
│  │     │   │ 전략 미흡  20%       │  "공격형 수주율 개선 필요.             │  │
│  │     ├───┤                     │   차별화 전략 강화 권장"               │  │
│  │     │   │ 기타      15%       │                                       │  │
│  │     └───┘                     │                                       │  │
│  └───────────────────────────────┴───────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────┬───────────────────────────────────────┐  │
│  │  📈 월별 수주율 추이 (라인)    │  📋 기관별 수주 현황 (바)              │  │
│  │                               │                                       │  │
│  │  80%│     ●──●               │  정보화진흥원  ████████ 75%            │  │
│  │  60%│ ●──●     ──●           │  행정안전부    ██████░░ 60%            │  │
│  │  40%│                         │  교육부        ████░░░░ 40%            │  │
│  │     └──┬──┬──┬──┬──┬──       │  과기부        ██████████ 100%        │  │
│  │       10  11  12  1   2   3   │                                       │  │
│  └───────────────────────────────┴───────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

> **구현 명세**:
> - **실패 원인 분석**: `proposals.result_reason` 필드 집계 → Recharts `<PieChart>`
> - **포지셔닝별 수주율**: `proposals.positioning` + `result` 집계 → Recharts `<BarChart>`
>   - §28-5 `LRN-08` 포지셔닝 정확도 데이터 활용
> - **월별 수주율 추이**: 기존 HTML 테이블 → Recharts `<LineChart>` 교체
> - **기관별 수주 현황**: 기존 CSS div bars → Recharts `<BarChart>` 교체
> - **접근 권한**: lead 이상 (팀장/본부장/경영진/관리자)
> - ❌ **스킵**: 가격 산점도 (낙찰가 데이터 부족), AI 성공 패턴 인사이트 (v1 over-engineering)

### 13-13. ★ 원가기준/낙찰가 관리 UI (v3.4)

> **배경**: v3.3에서 `labor_rates`, `market_price_data` 테이블을 추가했으나 관리 UI 없음.
> KB 페이지(`/kb/`)의 기존 탭 구조를 활용하여 2개 라우트 추가.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  📚 Knowledge Base                                                           │
│  [콘텐츠][발주기관][경쟁사][교훈][통합검색][원가기준 ★][낙찰가 벤치마크 ★]  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  📋 원가기준 (노임단가) — labor_rates                    [ + 등록 ] [ 📥 ]  │
│  ┌───────────┬──────┬──────────┬────────┬────────┬──────────────────┐      │
│  │ 기관        │ 연도  │ 등급      │ 단가    │ 출처    │ 갱신일            │      │
│  ├───────────┼──────┼──────────┼────────┼────────┼──────────────────┤      │
│  │ 한국SW산업  │ 2026 │ 특급기술사│ 450만  │ 공시   │ 2026-01-15       │      │
│  │ 한국SW산업  │ 2026 │ 고급기술사│ 380만  │ 공시   │ 2026-01-15       │      │
│  │ 기재부      │ 2026 │ 고급기사  │ 350만  │ 예정가  │ 2026-02-01       │      │
│  └───────────┴──────┴──────────┴────────┴────────┴──────────────────┘      │
│                                                                              │
│  필터: 기관 [ 전체 ▼ ]  연도 [ 2026 ▼ ]  등급 [ 전체 ▼ ]                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

> **구현 명세**:
> - `LaborRatesTable.tsx`: `labor_rates` CRUD (기관/연도/등급/단가/출처)
>   - API: `routes_kb.py` 확장 → `GET/POST/PUT/DELETE /api/kb/labor-rates`
>   - 필터: 기관, 연도, 등급
>   - CSV 가져오기/내보내기 지원
> - `MarketPricesTable.tsx`: `market_price_data` CRUD (도메인/예산범위/낙찰률/출처)
>   - API: `routes_kb.py` 확장 → `GET/POST/PUT/DELETE /api/kb/market-prices`
>   - 필터: 도메인, 예산 범위, 연도
> - **접근 권한**: lead 이상 (CRUD), member는 읽기 전용

---

## 14. 간이 모드 (Lite Mode) — U-1 해결

> **역량 DB 없이도 즉시 시작 가능.** 이 경우 AI가 역량 DB 자동 검색을 건너뛰고 사용자 수동 입력에 의존.

```python
# 간이 모드 프로젝트 생성
# POST /api/proposals
{
  "name": "AI 플랫폼 구축",
  "client": "과학기술부",
  "mode": "lite",         # ← lite 모드
  "rfp_file": <UploadFile> # ★ RFP 파일로 기본 정보 자동 추출 (U-3)
}
```

### 14-1. 모드별 동작 차이

| 항목 | Lite (간이) | Full (정규) |
|------|------------|------------|
| 역량 DB 필수 | 아니오 | 예 |
| STEP 0 공고 검색 | 가능 (키워드 검색만, 적합도 점수 간소화) | AI 공고 검색·추천 + 역량 기반 적합도 |
| STEP 1-② 포지셔닝 | 사용자 직접 선택 (AI 추천 없이) | AI 자동 판정 + 사용자 확정 |
| STEP 1-② 수주 가능성 점수 | 생략 | 산출 |
| STEP 2 Win Theme 생성 | 사용자 입력 역량 기반 | 역량 DB 자동 검색 기반 |
| STEP 4 실적 자동 인용 | 불가 (수동 입력) | 자동 |

### 14-2. RFP 업로드로 기본 정보 자동 추출 (U-3)

```python
# POST /api/proposals/from-rfp
async def create_from_rfp(rfp_file: UploadFile, mode: str = "lite"):
    """
    RFP 파일을 업로드하면:
    1. 파싱하여 사업명·발주기관·기한 자동 추출
    2. 프로젝트 생성
    3. rfp_raw에 파싱된 텍스트 저장
    → STEP 0 건너뛰고 STEP 1(RFP 분석)부터 직접 시작
    """
    text = await parse_rfp_file(rfp_file)
    basic_info = await extract_basic_info(text)  # Claude로 기본 정보 추출

    project = create_project(
        name=basic_info["project_name"],
        client=basic_info["client"],
        deadline=basic_info["deadline"],
        mode=mode,
    )

    # 그래프 초기 상태에 rfp_raw 포함 → STEP 1에서 재파싱 불필요
    await start_graph(project.id, initial_state={
        "rfp_raw": text,
        "project_name": basic_info["project_name"],
        "mode": mode,
    })

    return project
```

### 14-3. 공고번호 직접 지정 — from-search (U-2)

```python
# POST /api/proposals/from-search
async def create_from_search(bid_no: str, mode: str = "full"):
    """
    워크플로 밖에서 이미 알고 있는 공고번호로 프로젝트 생성.
    STEP 0(검색)을 건너뛰고 rfp_fetch(G2B 상세 수집 + RFP 업로드)부터 시작.
    """
    project = create_project(name=f"공고 {bid_no}", mode=mode)

    await start_graph(project.id, initial_state={
        "picked_bid_no": bid_no,  # → route_start에서 "direct_fetch" 분기
        "mode": mode,
    })

    return project
```

---

## 15. PostgreSQL 스키마 (Supabase) — v2.0

> **v2.0 변경**: SQLite → Supabase PostgreSQL 전환. 조직·사용자·역할 테이블 추가, RLS 정책 적용.
> LangGraph checkpointer는 `PostgresSaver`가 자체 테이블을 생성하므로 여기서는 앱 데이터만 정의.

### 15-1. 조직·사용자 테이블

```sql
-- ── 조직 구조 ──

CREATE TABLE organizations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,              -- 회사명
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE divisions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID REFERENCES organizations(id) NOT NULL,
    name        TEXT NOT NULL,              -- 본부명 (예: ICT사업본부)
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE teams (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    division_id UUID REFERENCES divisions(id) NOT NULL,
    name        TEXT NOT NULL,              -- 팀명 (예: AI사업팀)
    teams_webhook_url TEXT,                 -- ★ 팀별 Teams Incoming Webhook URL
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE users (
    id          UUID PRIMARY KEY REFERENCES auth.users(id),  -- Supabase Auth 연동
    email       TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'member',  -- member | lead | director | executive | admin
    team_id     UUID REFERENCES teams(id),
    division_id UUID REFERENCES divisions(id),   -- 본부장·경영진은 team 없이 division만
    org_id      UUID REFERENCES organizations(id) NOT NULL,
    azure_ad_oid TEXT UNIQUE,                    -- Azure AD Object ID (SSO 매핑)
    notification_settings JSONB DEFAULT '{"teams": true, "in_app": true}'::jsonb,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- ★ 프로젝트 참여자 (다대다)
CREATE TABLE project_participants (
    proposal_id UUID REFERENCES proposals(id) ON DELETE CASCADE,
    user_id     UUID REFERENCES users(id),
    role_in_project TEXT DEFAULT 'member',  -- member | section_lead
    assigned_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (proposal_id, user_id)
);
```

### 15-2. 자사 역량 DB

```sql
CREATE TABLE capabilities (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID REFERENCES organizations(id) NOT NULL,  -- 회사 소속
    type        TEXT NOT NULL,              -- track_record | tech | personnel
    title       TEXT NOT NULL,
    detail      TEXT NOT NULL,
    keywords    TEXT[],                     -- ★ PostgreSQL 배열
    created_by  UUID REFERENCES users(id),
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE capabilities ENABLE ROW LEVEL SECURITY;

-- 같은 회사 내 모든 사용자 조회 가능
CREATE POLICY "org_capabilities" ON capabilities FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()));
-- 수정은 admin만
CREATE POLICY "admin_manage_capabilities" ON capabilities FOR ALL
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');
```

### 15-3. 제안 프로젝트 테이블

```sql
CREATE TABLE proposals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    client          TEXT,
    deadline        TIMESTAMPTZ,
    positioning     TEXT,                   -- defensive | offensive | adjacent
    mode            TEXT DEFAULT 'full',    -- lite | full
    picked_bid_no   TEXT,
    bid_detail      JSONB,                  -- BidDetail JSON
    search_query    JSONB,                  -- 초기 검색 조건
    sales_intel     TEXT,
    status          TEXT DEFAULT 'active',  -- active | no_go | completed | won | lost
    result          TEXT,                   -- ★ 수주 | 패찰 | 유찰 (팀장 입력)
    result_amount   BIGINT,                -- ★ 수주액 (원)
    result_reason   TEXT,                   -- ★ 패찰 사유
    result_at       TIMESTAMPTZ,
    thread_id       TEXT UNIQUE,
    -- ★ v2.0: 소유·조직
    team_id         UUID REFERENCES teams(id) NOT NULL,
    division_id     UUID REFERENCES divisions(id) NOT NULL,
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    created_by      UUID REFERENCES users(id) NOT NULL,
    budget_amount   BIGINT,                -- ★ 예산액 (원, 결재선 판단 기준)
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);
```

### 15-4. 산출물·피드백·승인·Compliance

```sql
CREATE TABLE artifacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    step            TEXT NOT NULL,
    version         INTEGER DEFAULT 1,
    content         TEXT NOT NULL,
    created_by      UUID REFERENCES users(id),
    -- ★ v3.3: 버전 관리 강화 (ProposalForge 비교 검토 반영)
    change_summary  TEXT,                -- 변경 요약 (AI 자동 생성 / 사람 피드백 / 품질게이트)
    change_source   VARCHAR(50),         -- 'ai_generated'|'human_edited'|'quality_gate'|'final'
    quality_score   DECIMAL(5,2),        -- 해당 버전의 자가진단 점수
    diff_from_previous JSONB,            -- 이전 버전 대비 변경 상세
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(proposal_id, step, version)
);

CREATE TABLE feedbacks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    step            TEXT NOT NULL,
    version         INTEGER,
    feedback        TEXT NOT NULL,
    comments        JSONB,                  -- 항목별 코멘트
    rework_targets  JSONB,                  -- 부분 재작업 대상
    author_id       UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE approvals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    step            TEXT NOT NULL,
    approved_by     UUID REFERENCES users(id),
    approver_role   TEXT,                   -- ★ lead | director | executive
    approved_at     TIMESTAMPTZ,
    decision        TEXT,                   -- approved | rejected
    positioning     TEXT,
    chain_status    JSONB,                  -- ★ 결재선 전체 이력 JSON
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE compliance_matrix (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    req_id          TEXT NOT NULL,
    content         TEXT NOT NULL,
    source_step     TEXT NOT NULL,
    status          TEXT DEFAULT '미확인',
    proposal_section TEXT,
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(proposal_id, req_id)
);
```

### 15-5. 검색·캐시·알림·감사

```sql
CREATE TABLE search_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    bid_no          TEXT NOT NULL,
    project_name    TEXT NOT NULL,
    client          TEXT,
    budget          TEXT,
    deadline        TEXT,
    project_summary TEXT,
    key_requirements JSONB,
    eval_method     TEXT,
    competition_level TEXT,
    fit_score       INTEGER,
    fit_rationale   TEXT,
    expected_positioning TEXT,
    brief_analysis  TEXT,
    picked          BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE g2b_cache (
    cache_key       TEXT PRIMARY KEY,
    response        JSONB NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ★ v2.0: 알림
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) NOT NULL,
    proposal_id     UUID REFERENCES proposals(id),
    type            TEXT NOT NULL,           -- approval_request | approval_result | deadline | result
    title           TEXT NOT NULL,
    body            TEXT,
    link            TEXT,                    -- 프로젝트 URL
    is_read         BOOLEAN DEFAULT false,
    teams_sent      BOOLEAN DEFAULT false,   -- Teams 발송 여부
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- ★ v2.0: 감사 로그
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    action          TEXT NOT NULL,           -- approve | reject | create | update | delete
    resource_type   TEXT NOT NULL,           -- proposal | capability | user | approval
    resource_id     UUID,
    detail          JSONB,                   -- 변경 상세
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX idx_proposals_team ON proposals(team_id);
CREATE INDEX idx_proposals_division ON proposals(division_id);
CREATE INDEX idx_proposals_status ON proposals(status);
```

### 15-5a. ★ v3.0: 프로젝트 상태 머신 확장

```sql
-- proposals 테이블 status 확장 (v2.0의 status 컬럼을 대체)
-- 유효값: draft | searching | analyzing | strategizing | submitted | presented | won | lost | no_go | on_hold | expired | abandoned | retrospect
-- + current_step 필드 추가 (PSM-01a)

ALTER TABLE proposals ADD COLUMN IF NOT EXISTS current_step TEXT;  -- STEP 2/3/4/5 (strategizing 내 활성 단계)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS previous_status TEXT;  -- on_hold 전환 시 이전 상태 보존
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS hold_reason TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS abandon_reason TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS presentation_at TIMESTAMPTZ;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS presentation_location TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS presenter TEXT;

-- status 유효값 제약
ALTER TABLE proposals DROP CONSTRAINT IF EXISTS proposals_status_check;
ALTER TABLE proposals ADD CONSTRAINT proposals_status_check
  CHECK (status IN ('draft','searching','analyzing','strategizing','submitted','presented','won','lost','no_go','on_hold','expired','abandoned','retrospect'));
```

### 15-5b. ★ v3.0: KB Part B — 콘텐츠 라이브러리

```sql
CREATE TABLE content_library (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    type            TEXT NOT NULL,           -- section_block | paragraph | standard_answer | diagram_desc | performance_desc | qa_record
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    -- 메타데이터
    source_project_id UUID REFERENCES proposals(id),  -- 출처 프로젝트
    author_id       UUID REFERENCES users(id),
    industry        TEXT,                    -- 산업분야 태그
    tech_area       TEXT,                    -- 기술영역 태그
    rfp_type        TEXT,                    -- RFP 유형 태그
    tags            TEXT[],                  -- 추가 태그
    -- 거버넌스
    status          TEXT DEFAULT 'draft',    -- draft | published | archived
    approved_by     UUID REFERENCES users(id),
    approved_at     TIMESTAMPTZ,
    version         INTEGER DEFAULT 1,
    parent_id       UUID REFERENCES content_library(id),  -- 버전 관리 (이전 버전 참조)
    -- 품질 점수
    quality_score   NUMERIC(5,2) DEFAULT 0,  -- 수주 기여도 + 재사용 횟수 + 최신성
    reuse_count     INTEGER DEFAULT 0,
    won_count       INTEGER DEFAULT 0,       -- 이 콘텐츠 포함 제안서 수주 횟수
    lost_count      INTEGER DEFAULT 0,
    -- 벡터
    embedding       vector(1536),            -- pgvector 시맨틱 검색용
    -- 타임스탬프
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_content_embedding ON content_library USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_content_status ON content_library(status);
CREATE INDEX idx_content_org ON content_library(org_id);

ALTER TABLE content_library ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_content_published" ON content_library FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()) AND status = 'published');
CREATE POLICY "author_content_draft" ON content_library FOR SELECT
  USING (author_id = auth.uid() AND status = 'draft');
```

### 15-5c. ★ v3.0: KB Part C — 발주기관 DB

```sql
CREATE TABLE client_intelligence (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    client_name     TEXT NOT NULL,            -- 기관명
    client_type     TEXT,                     -- 중앙부처 | 지자체 | 공공기관 | 기타
    scale           TEXT,                     -- 대규모 | 중규모 | 소규모
    parent_ministry TEXT,                     -- 관할 부처
    location        TEXT,                     -- 소재지
    relationship    TEXT DEFAULT 'neutral',   -- new | neutral | friendly | close
    relationship_history JSONB DEFAULT '[]',  -- 관계 수준 변경 이력
    eval_tendency   TEXT,                     -- 평가 성향 메모 (기술중시/가격중시/혁신선호)
    contact_info    JSONB,                    -- 내부 영업 담당자, 기관 측 접점 (개인정보 최소화)
    notes           TEXT,                     -- 자유 텍스트 메모
    embedding       vector(1536),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- 발주기관 ↔ 프로젝트 자동 연결 (과거 입찰 이력)
CREATE TABLE client_bid_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID REFERENCES client_intelligence(id) ON DELETE CASCADE,
    proposal_id     UUID REFERENCES proposals(id),
    positioning     TEXT,                     -- 이 기관에서의 포지셔닝
    result          TEXT,                     -- won | lost | no_go | expired
    bid_year        INTEGER,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_client_embedding ON client_intelligence USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
ALTER TABLE client_intelligence ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_clients" ON client_intelligence FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()));
```

### 15-5d. ★ v3.0: KB Part D — 경쟁사 DB

```sql
CREATE TABLE competitors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    company_name    TEXT NOT NULL,
    scale           TEXT,                     -- 대기업 | 중견 | 중소
    primary_area    TEXT,                     -- 주력 분야
    strengths       TEXT,                     -- 강점 요약
    weaknesses      TEXT,                     -- 약점 요약
    price_pattern   TEXT,                     -- aggressive | conservative | moderate
    avg_win_rate    NUMERIC(5,2),             -- 평균 낙찰률
    notes           TEXT,
    embedding       vector(1536),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- 경쟁사 ↔ 프로젝트 경쟁 이력
CREATE TABLE competitor_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_id   UUID REFERENCES competitors(id) ON DELETE CASCADE,
    proposal_id     UUID REFERENCES proposals(id),
    strategy_used   TEXT,                     -- 이 업체와 경쟁 시 사용한 전략
    our_result      TEXT,                     -- won | lost
    competitor_result TEXT,                   -- won | lost | unknown
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_competitor_embedding ON competitors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
ALTER TABLE competitors ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_competitors" ON competitors FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()));
```

### 15-5e. ★ v3.0: KB Part E — 교훈 아카이브

```sql
CREATE TABLE lessons_learned (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    proposal_id     UUID REFERENCES proposals(id),
    -- 회고 데이터
    strategy_summary TEXT,                    -- 사용된 전략 요약
    effective_points TEXT,                    -- 효과적이었던 점
    weak_points     TEXT,                     -- 부족했던 점
    improvements    TEXT,                     -- 다음 개선 포인트
    -- 패찰 시 구조화 기록
    failure_category TEXT,                    -- price | tech | track_record | strategy | format
    failure_detail  TEXT,
    -- 메타
    positioning     TEXT,                     -- 사용된 포지셔닝
    client_name     TEXT,
    industry        TEXT,
    result          TEXT,                     -- won | lost | no_go | expired | abandoned
    embedding       vector(1536),
    author_id       UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_lessons_embedding ON lessons_learned USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
ALTER TABLE lessons_learned ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_lessons" ON lessons_learned FOR SELECT
  USING (org_id = (SELECT org_id FROM users WHERE id = auth.uid()));
```

### 15-5f. ★ v3.0: 크로스팀 프로젝트 + 컨소시엄

```sql
-- 크로스팀: 참여 팀 (주관 팀은 proposals.team_id)
CREATE TABLE project_teams (
    proposal_id UUID REFERENCES proposals(id) ON DELETE CASCADE,
    team_id     UUID REFERENCES teams(id),
    role        TEXT DEFAULT 'participating',  -- lead | participating
    PRIMARY KEY (proposal_id, team_id)
);

-- 컨소시엄 구성
CREATE TABLE consortium_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    company_name    TEXT NOT NULL,             -- 참여사명
    role            TEXT NOT NULL,             -- lead(자사) | partner
    scope           TEXT,                      -- 담당 범위
    personnel_count INTEGER,                   -- 투입 인력 수
    share_amount    BIGINT,                    -- 분담 금액
    contact_name    TEXT,
    contact_email   TEXT,
    contact_phone   TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

### 15-5g. ★ v3.0: AI 실행 상태 + 동시 편집 잠금 + 회사 템플릿

```sql
-- AI 작업 실행 이력 (AGT-09)
CREATE TABLE ai_task_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    step            TEXT NOT NULL,
    sub_task        TEXT,                      -- 병렬 하위 작업명
    status          TEXT NOT NULL,             -- running | complete | error | paused | no_response
    started_at      TIMESTAMPTZ DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    duration_ms     INTEGER,
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    model           TEXT,
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_ai_task_proposal ON ai_task_logs(proposal_id, step);

-- 섹션 편집 잠금 (GATE-17/18)
CREATE TABLE section_locks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    section_id      TEXT NOT NULL,
    locked_by       UUID REFERENCES users(id),
    locked_at       TIMESTAMPTZ DEFAULT now(),
    expires_at      TIMESTAMPTZ NOT NULL,      -- locked_at + 5분 (자동 해제)
    UNIQUE(proposal_id, section_id)
);

-- 회사 템플릿 관리 (ART-07~10)
CREATE TABLE company_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,
    type            TEXT NOT NULL,             -- docx | pptx
    name            TEXT NOT NULL,
    description     TEXT,
    file_path       TEXT NOT NULL,             -- Supabase Storage 경로
    version         INTEGER DEFAULT 1,
    is_active       BOOLEAN DEFAULT true,
    uploaded_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- 발표 Q&A 기록 (PSM-07/08)
CREATE TABLE presentation_qa (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID REFERENCES proposals(id) ON DELETE CASCADE,
    question        TEXT NOT NULL,
    answer          TEXT NOT NULL,
    evaluator_reaction TEXT,                   -- positive | neutral | negative
    memo            TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- 사용자 라이프사이클 확장 (ULM)
ALTER TABLE users ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';  -- active | inactive | suspended
ALTER TABLE users ADD COLUMN IF NOT EXISTS deactivated_at TIMESTAMPTZ;

-- 임시 위임 (ULM-07)
CREATE TABLE approval_delegations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delegator_id    UUID REFERENCES users(id) NOT NULL,
    delegate_id     UUID REFERENCES users(id) NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    reason          TEXT,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

### 15-5h. ★ v3.3: 노임단가 테이블

```sql
-- 노임단가 참조 테이블 (plan_price 노드에서 조회)
-- ProposalForge 비교 검토 반영: 프롬프트의 "[단가]" 플레이스홀더를 실제 DB 조회로 대체
CREATE TABLE labor_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    standard_org VARCHAR(100) NOT NULL,  -- 'KOSA'(SW산업협회), 'KEA'(엔지니어링협회), 'MOEF'(기재부)
    year INTEGER NOT NULL,
    grade VARCHAR(50) NOT NULL,          -- '기술사', '특급', '고급', '중급', '초급'
    monthly_rate BIGINT NOT NULL,
    daily_rate BIGINT,
    effective_date DATE,
    source_url VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_labor_rates_lookup ON labor_rates(standard_org, year, grade);

-- RLS: 같은 조직 내 조회 (노임단가는 공개 데이터이지만 조직별 관리)
ALTER TABLE labor_rates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "all_users_read_labor_rates" ON labor_rates FOR SELECT USING (true);
CREATE POLICY "admin_manage_labor_rates" ON labor_rates FOR ALL
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');
```

### 15-5i. ★ v3.3: 시장 낙찰가 벤치마크 테이블

```sql
-- 시장 낙찰가 벤치마크 (plan_price 노드에서 유사 도메인·규모 필터링 조회)
-- ProposalForge 비교 검토 반영: 입찰가격 시뮬레이션의 "유사과업 낙찰가 분석" 데이터 소스
CREATE TABLE market_price_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),  -- 수집한 조직 (NULL이면 공용)
    project_title VARCHAR(500),
    client_org VARCHAR(200),
    domain VARCHAR(100) NOT NULL,        -- 'SI/SW개발', '정책연구', '성과분석', '컨설팅' 등
    budget BIGINT,                       -- 예정가격
    winning_price BIGINT,                -- 낙찰가
    bid_ratio DECIMAL(5,4),              -- 낙찰률 (winning_price/budget)
    num_bidders INTEGER,
    tech_price_ratio VARCHAR(20),        -- '90:10', '80:20' 등
    evaluation_method VARCHAR(100),      -- '협상에 의한 계약', '적격심사', '2단계 경쟁입찰' 등
    year INTEGER NOT NULL,
    source VARCHAR(200),                 -- 데이터 출처 (나라장터, 조달청 등)
    collected_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_market_price_domain_year ON market_price_data(domain, year);
CREATE INDEX idx_market_price_budget ON market_price_data(budget);

ALTER TABLE market_price_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY "all_users_read_market_price" ON market_price_data FOR SELECT USING (true);
CREATE POLICY "admin_manage_market_price" ON market_price_data FOR ALL
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');
```

### 15-6. RLS (Row Level Security) 정책

```sql
-- ★ Supabase RLS 활성화
ALTER TABLE proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedbacks ENABLE ROW LEVEL SECURITY;
ALTER TABLE approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- ── 프로젝트 접근 정책 ──

-- 팀원: 본인 참여 프로젝트만
CREATE POLICY "member_select_proposals" ON proposals FOR SELECT
  USING (
    id IN (SELECT proposal_id FROM project_participants WHERE user_id = auth.uid())
    OR created_by = auth.uid()
  );

-- 팀장: 소속 팀 전체
CREATE POLICY "lead_select_proposals" ON proposals FOR SELECT
  USING (
    team_id = (SELECT team_id FROM users WHERE id = auth.uid())
    AND (SELECT role FROM users WHERE id = auth.uid()) IN ('lead', 'admin')
  );

-- 본부장: 소속 본부 전체
CREATE POLICY "director_select_proposals" ON proposals FOR SELECT
  USING (
    division_id = (SELECT division_id FROM users WHERE id = auth.uid())
    AND (SELECT role FROM users WHERE id = auth.uid()) IN ('director', 'admin')
  );

-- 경영진: 전사
CREATE POLICY "executive_select_proposals" ON proposals FOR SELECT
  USING (
    (SELECT role FROM users WHERE id = auth.uid()) IN ('executive', 'admin')
  );

-- 알림: 본인 것만
CREATE POLICY "own_notifications" ON notifications FOR ALL
  USING (user_id = auth.uid());
```

### 15-7. 성과 추적 뷰 (Materialized View)

```sql
-- ★ 팀별 성과 집계 뷰
CREATE MATERIALIZED VIEW team_performance AS
SELECT
    p.team_id,
    t.name AS team_name,
    d.name AS division_name,
    COUNT(*) FILTER (WHERE p.status IN ('active', 'completed', 'won', 'lost')) AS total_proposals,
    COUNT(*) FILTER (WHERE p.status = 'active') AS active_proposals,
    COUNT(*) FILTER (WHERE p.result = '수주') AS won_count,
    COUNT(*) FILTER (WHERE p.result IN ('수주', '패찰')) AS decided_count,
    CASE
        WHEN COUNT(*) FILTER (WHERE p.result IN ('수주', '패찰')) > 0
        THEN ROUND(
            COUNT(*) FILTER (WHERE p.result = '수주')::numeric /
            COUNT(*) FILTER (WHERE p.result IN ('수주', '패찰'))::numeric * 100, 1
        )
        ELSE 0
    END AS win_rate,
    COALESCE(SUM(p.result_amount) FILTER (WHERE p.result = '수주'), 0) AS total_won_amount,
    AVG(EXTRACT(DAY FROM (p.result_at - p.created_at)))
        FILTER (WHERE p.result IS NOT NULL) AS avg_days_to_result
FROM proposals p
JOIN teams t ON p.team_id = t.id
JOIN divisions d ON p.division_id = d.id
GROUP BY p.team_id, t.name, d.name;

-- 갱신: REFRESH MATERIALIZED VIEW team_performance;
-- (제안 결과 등록 시 트리거 또는 cron으로 갱신)
```

---

## 16. 프롬프트 설계 원칙

### 16-1. 공통 컨텍스트 주입

> **★ v3.0 토큰 최적화 원칙** (§21 참조):
> - `COMMON_CONTEXT`는 **Prompt Caching 대상** — `cache_control: {"type": "ephemeral"}` 적용
> - 피드백 이력은 **최근 3회(feedback_window_size)만** 포함
> - KB 참조는 **Top-5, 각 500자 이내**로 요약 후 주입
> - STEP별 컨텍스트 예산 준수 (§21 token_manager.py STEP_BUDGETS 참조)

```python
COMMON_CONTEXT = """
## 현재 제안 컨텍스트
- 사업명: {project_name}
- 발주기관: {client}
- 🏷️ 포지셔닝: {positioning} ({positioning_label})
- 모드: {mode}

## 포지셔닝 전략 가이드
{positioning_guide}

## 핵심 전략
- Ghost Theme: {ghost_theme}
- Win Theme: {win_theme}
- Action Forcing Event: {action_forcing_event}
- 핵심 메시지: {key_messages}

## 이전 단계 피드백 (최근 {feedback_window_size}회)
{feedback_history}

## ★ v3.0: KB 참조 컨텍스트 (Top-5, 각 500자 이내)
{kb_context}

## ★ v3.0: 발주기관 인텔리전스
{client_intel_summary}

## 부분 재작업 지시 (있는 경우)
{rework_instruction}
"""
```

> **Prompt Caching 적용 방법**: `COMMON_CONTEXT` 블록을 `messages[0].content[0]`에 배치하고 `cache_control` 마킹.
> 동일 프로젝트 내 STEP 간 전환 시 90% 입력 토큰 비용 절감 (§21 상세).

### 16-2. 단계별 프롬프트 핵심

| 단계 | 핵심 지시 | Shipley 관점 | 포지셔닝 연동 | KB 참조 | 토큰 예산 |
|------|-----------|-------------|-------------|---------------|-----------------|
| 공고 검색 | 최대 5건 추천, 공고별 요약 + 적합도 | 영업 담당자 | 예상 분류 | 발주기관 입찰이력 | 4,000 |
| RFP 획득 | G2B 첨부파일 자동 추출 + 사용자 업로드 | — (자동+수동) | — | — | — |
| RFP 분석 | 배점 역설계, Compliance Matrix 초안, hidden_requirements | Blue Team | 케이스 A/B | 유사 RFP 콘텐츠 | 8,000 |
| **★ 리서치 조사** | **RFP-적응형 사전조사: 사업 범주별 조사 차원 동적 설계 → 차원별 핵심 발견 수집** | **Blue Team** | **—** | **외부 데이터** | **15,000** |
| Go/No-Go | 포지셔닝 정밀 판정 + 수주 가능성 + **발주기관 인텔 5단계** | 의사결정자 | 유형 확정 | 발주기관+경쟁사 DB+**리서치** | **18,000** |
| 제안전략 | Ghost/Win/AFE + **경쟁사 SWOT + 시나리오 + 연구질문** | Blue Team | **매트릭스 전체** | 경쟁사 강약점·교훈 | **25,000** |
| 스토리라인 | 4단계 구조, 포지셔닝별 강조점 | Pink Team | 수성/공격/인접 | 수주 성공 콘텐츠 | 6,000 |
| 제안서 | 발주처 언어, 수치화, 케이스 A/B + **자체검증 체크리스트** | Red Team | 실적/혁신/전이 | 콘텐츠 라이브러리 | 12,000/섹션 |
| 가격산정 | **원가기준 확인 + 노임단가 M/M + 직접경비 + 입찰시뮬레이션** | Red Team | 가격전략 | KB 단가 DB | **15,000** |
| 자가진단 | 4축 평가 + **3인 페르소나 시뮬레이션** + 80점 기준 | Red Team | 포지셔닝 일관성 | Compliance 규칙 | 8,000 |
| **★ 발표전략** | **킬링 메시지, 시간 배분, Q&A 전략 (서류심사 시 건너뛰기)** | **Gold Team** | **발표 시나리오** | **—** | **8,000** |
| PPT | 1슬라이드 1메시지, **3막 구조(Why→How→Us)**, 50자×5줄 | Gold Team | 메시지 시각화 | — | 4,000/슬라이드 |

> **★ v3.0 토큰 예산 원칙**: 각 STEP의 입력 토큰이 예산을 초과하면 `token_manager`가 컨텍스트를 자동 축소 (RFP 요약 전달, KB 참조 Top-3 축소, 피드백 최근 2회 등). 상세 로직은 §21 참조.

### 16-3. ★ v3.0 AI 산출물 신뢰성 규칙 (TRS-01~12 구현)

> 요구사항 §12-0의 신뢰성 정책을 시스템 프롬프트 + 후처리로 구현한다.

#### 16-3-1. 시스템 프롬프트 — 신뢰성 지시 블록

```python
# app/prompts/trustworthiness.py

TRUSTWORTHINESS_RULES = """
## AI 작성 규칙 — 반드시 준수

### 1. 할루시네이션 금지
- KB(역량 DB, 콘텐츠 라이브러리, 발주기관 DB, 경쟁사 DB)에 있는 데이터를 우선 사용하라.
- 자사 수행실적, 인력 정보, 구체적 금액/기간을 KB 없이 생성하지 마라.
  → KB에 없으면 "[KB 데이터 필요: {필요한 정보 설명}]" 플레이스홀더를 삽입하라.
- 확인할 수 없는 사실을 단정적으로 서술하지 마라.

### 2. 출처 태그 필수
- 모든 수치(금액, 비율, 건수, 기간)에 출처 태그를 부착하라:
  - [KB] — KB 데이터 기반
  - [RFP] — RFP 원문 인용 (페이지 번호 포함)
  - [G2B] — 나라장터 공고/낙찰 데이터
  - [추정] — AI 추론 (반드시 추론 근거를 괄호 안에 명시)
  - [일반지식] — KB/RFP/G2B에 없는 일반적 사실
- 인라인 출처 마커 형식: [역량DB-{id}], [콘텐츠-{id}], [RFP p.{n}]

### 3. 과장 표현 금지
- "업계 최초", "혁신적", "획기적", "독보적" 등 검증 불가능한 표현 사용 금지.
  → 대신 구체적 수치와 비교 근거를 제시하라.
  → 예: "혁신적 기술" ❌ → "처리시간 30% 단축 (기존 10초 → 7초) [KB-CAP-045]" ✅

### 4. 발주처 언어 사용
- RFP에서 사용한 용어를 그대로 사용하라.
- RFP에 없는 자체 용어를 도입할 경우 [비RFP 용어] 태그를 부착하라.

### 5. 외부 데이터 인용 기준
- 시장 동향, 기술 트렌드, 통계 인용 시 공신력 있는 출처만 허용:
  ✅ 정부 통계(통계청, 과기정통부), 공공기관 보고서, 학술 논문, 업계 공식 보고서(Gartner, IDC 등)
  ❌ 개인 블로그, 비공식 매체, 위키백과, 출처 불명 데이터
- 출처를 특정할 수 없는 일반 상식은 [일반지식] 태그 부착.

### 6. 불확실성 명시
- 경쟁사 예상 가격, 시장 점유율 등 확신도가 낮은 판단은
  확신도(높음/보통/낮음)와 판단 근거를 함께 제시하라.
"""

# ── 공통 컨텍스트에 신뢰성 규칙 주입 ──
# COMMON_CONTEXT 빌드 시 TRUSTWORTHINESS_RULES를 cache_control 블록에 포함
# (프로젝트 내 모든 STEP에서 동일하게 적용 → Prompt Caching 대상)
```

#### 16-3-2. 출처 태그 후처리 — source_tagger.py

```python
# app/services/source_tagger.py
import re
from dataclasses import dataclass

@dataclass
class SourceTag:
    """AI 산출물 내 출처 태그 파싱 결과."""
    tag_type: str      # "KB" | "RFP" | "G2B" | "추정" | "일반지식" | "플레이스홀더"
    reference_id: str   # 예: "CAP-045", "p.12", ""
    text_span: tuple[int, int]  # 원문 내 위치

# ── 출처 태그 패턴 ──
TAG_PATTERNS = {
    "KB":           r'\[KB(?:-([A-Z]+-\d+))?\]',
    "역량DB":       r'\[역량DB-([A-Z]+-\d+)\]',
    "콘텐츠":       r'\[콘텐츠-([A-Z]+-\d+)\]',
    "RFP":          r'\[RFP\s*p\.(\d+)\]',
    "G2B":          r'\[G2B(?:\s+([^\]]+))?\]',
    "추정":         r'\[추정(?:\s*\(([^)]+)\))?\]',
    "일반지식":     r'\[일반지식\]',
    "플레이스홀더": r'\[KB 데이터 필요:\s*([^\]]+)\]',
    "비RFP용어":    r'\[비RFP 용어\]',
    "과장표현":     r'\[과장 표현 주의\]',
}

def extract_source_tags(text: str) -> list[SourceTag]:
    """AI 산출물에서 모든 출처 태그를 추출."""
    tags = []
    for tag_type, pattern in TAG_PATTERNS.items():
        for match in re.finditer(pattern, text):
            tags.append(SourceTag(
                tag_type=tag_type,
                reference_id=match.group(1) or "" if match.lastindex else "",
                text_span=(match.start(), match.end()),
            ))
    return tags

def calculate_grounding_ratio(text: str) -> dict:
    """
    TRS-05: KB 참조 신뢰도 산출.
    - kb_ratio: KB/RFP/G2B 기반 문장 비율
    - general_ratio: 일반지식 기반 비율
    - untagged_ratio: 출처 태그 없는 비율 (검증 필요)
    """
    sentences = [s.strip() for s in re.split(r'[.。!?]\s*', text) if s.strip()]
    if not sentences:
        return {"kb_ratio": 0, "general_ratio": 0, "untagged_ratio": 1.0, "level": "일반지식 기반"}

    kb_count = sum(1 for s in sentences
                   if re.search(r'\[(KB|역량DB|콘텐츠|RFP|G2B)', s))
    general_count = sum(1 for s in sentences
                        if re.search(r'\[일반지식\]', s))
    total = len(sentences)
    untagged = total - kb_count - general_count

    kb_ratio = kb_count / total
    # TRS-05 3단계 판정
    if kb_ratio >= 0.7:
        level = "KB 기반"
    elif kb_ratio >= 0.3:
        level = "혼합"
    else:
        level = "일반지식 기반"

    return {
        "kb_ratio": round(kb_ratio, 2),
        "general_ratio": round(general_count / total, 2),
        "untagged_ratio": round(untagged / total, 2),
        "level": level,
    }

def find_ungrounded_claims(text: str) -> list[dict]:
    """
    TRS-07: 출처 없는 주장·수치 탐지 → 검증 필요 목록.
    - 수치가 포함된 문장 중 출처 태그가 없는 것
    - 수행실적/인력/금액 키워드가 포함된 문장 중 KB 태그가 없는 것
    """
    issues = []
    sentences = re.split(r'(?<=[.。!?])\s+', text)
    for i, sent in enumerate(sentences):
        has_number = bool(re.search(r'\d+[억만천건명년월일%]', sent))
        has_fact_keyword = bool(re.search(r'수행실적|인력|투입|프로젝트명|사업비|계약', sent))
        has_source_tag = bool(re.search(r'\[(KB|역량DB|콘텐츠|RFP|G2B|추정)', sent))

        if has_number and not has_source_tag:
            issues.append({
                "sentence_index": i,
                "sentence": sent[:100],
                "issue": "수치에 출처 태그 누락",
                "severity": "high",
            })
        elif has_fact_keyword and not has_source_tag:
            issues.append({
                "sentence_index": i,
                "sentence": sent[:100],
                "issue": "사실 주장에 KB 출처 누락",
                "severity": "high",
            })
    return issues
```

#### 16-3-3. 자가진단 4축 확장 — 근거 신뢰성 축 추가

```python
# app/graph/nodes/self_review.py 에 추가

async def evaluate_trustworthiness(sections: list, strategy) -> dict:
    """
    4축: 근거 신뢰성 평가 (25점 만점).
    TRS-07 + TRS-08 + TRS-10 + TRS-11 구현.
    """
    from app.services.source_tagger import (
        calculate_grounding_ratio,
        find_ungrounded_claims,
    )

    all_text = "\n".join(s.content for s in sections)
    grounding = calculate_grounding_ratio(all_text)
    ungrounded = find_ungrounded_claims(all_text)

    # ── 개별 점수 산출 ──
    # (1) 출처 태그 부착률 (10점)
    tag_score = max(0, 10 - len([u for u in ungrounded if u["severity"] == "high"]))

    # (2) KB 참조 비율 (5점)
    kb_score = round(grounding["kb_ratio"] * 5, 1)

    # (3) 과장 표현 감지 (5점)
    exaggeration_patterns = r'업계\s*최초|혁신적|획기적|독보적|세계\s*최고|압도적'
    exaggeration_count = len(re.findall(exaggeration_patterns, all_text))
    exaggeration_score = max(0, 5 - exaggeration_count)

    # (4) 섹션 간 수치 일관성 (5점) — TRS-08
    inconsistencies = _check_number_consistency(sections)
    consistency_score = max(0, 5 - len(inconsistencies))

    total = tag_score + kb_score + exaggeration_score + consistency_score

    return {
        "trustworthiness_score": round(total, 1),
        "max_score": 25,
        "details": {
            "source_tag_score": tag_score,
            "kb_ratio_score": kb_score,
            "exaggeration_score": exaggeration_score,
            "consistency_score": consistency_score,
        },
        "grounding_level": grounding["level"],
        "ungrounded_claims": ungrounded[:10],  # 상위 10건
        "exaggeration_count": exaggeration_count,
        "inconsistencies": inconsistencies,
        "warning": "출처 보강 필요" if total < 15 else None,
    }


def _check_number_consistency(sections: list) -> list[dict]:
    """
    TRS-08: 동일 수치가 여러 섹션에서 다르게 언급되는 경우 탐지.
    예: "투입인력 10명" vs "투입인력 12명" 불일치.
    """
    # 섹션별 수치+맥락 추출 → 동일 키워드 다른 수치 비교
    import re
    number_mentions = {}  # { "투입인력": [("10명", section_id), ("12명", section_id)] }
    pattern = r'(투입인력|사업비|예산|기간|처리시간|인원|건수)\s*[:：]?\s*(\d+[\d,.]*\s*[억만천건명년월일개%]+)'

    for s in sections:
        for match in re.finditer(pattern, s.content):
            key = match.group(1)
            value = match.group(2).strip()
            number_mentions.setdefault(key, []).append((value, s.section_id))

    inconsistencies = []
    for key, mentions in number_mentions.items():
        values = set(v for v, _ in mentions)
        if len(values) > 1:
            inconsistencies.append({
                "keyword": key,
                "values": [{"value": v, "section": sid} for v, sid in mentions],
                "issue": f"'{key}' 수치 불일치: {', '.join(values)}",
            })
    return inconsistencies
```

> **자가진단 점수 체계 변경 (v3.0)**:
> | 축 | 배점 | 항목 |
> |----|------|------|
> | 1. Compliance Matrix | 25점 | RFP 요건 충족, 분량·서식 준수 |
> | 2. 전략 반영도 | 25점 | Win Theme·Hot Button·AFE·스토리라인 |
> | 3. 품질 | 25점 | 수치 구체성·발주처 언어·논리 일관성·차별성 |
> | **4. 근거 신뢰성** | **25점** | 출처 태그 부착률·KB 참조 비율·과장 표현·수치 일관성 |
> | **합계** | **100점** | 통과 기준 80점, 근거 신뢰성 15점 미만 시 개별 경고 |

---

## 17. ★ 인증 흐름 (v2.0)

```
┌─────────┐     ┌──────────┐     ┌──────────────┐     ┌───────────┐
│ 사용자   │────→│ Next.js  │────→│ Supabase Auth│────→│ Azure AD  │
│ 브라우저 │     │ /login   │     │ (OAuth)      │     │ (Entra ID)│
└─────────┘     └──────────┘     └──────────────┘     └───────────┘
                                        │                    │
                                        │  ← OAuth callback  │
                                        │  (id_token + profile)
                                        ▼
                                 ┌──────────────┐
                                 │ Supabase      │
                                 │ - JWT 발급    │
                                 │ - users 조회  │
                                 │ - 역할 매핑   │
                                 └──────┬───────┘
                                        │ JWT
                                        ▼
                                 ┌──────────────┐
                                 │ FastAPI       │
                                 │ - JWT 검증    │
                                 │ - RLS 적용    │
                                 └──────────────┘
```

### 17-1. 인증 서비스

```python
# app/services/auth_service.py

from supabase import create_client
from fastapi import Depends, HTTPException, Request
from app.config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def get_current_user(request: Request) -> dict:
    """JWT에서 현재 사용자 정보 추출 + DB 역할 조회."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(401, "인증 필요")

    # Supabase JWT 검증
    user = supabase.auth.get_user(token)
    if not user:
        raise HTTPException(401, "유효하지 않은 토큰")

    # DB에서 역할·소속 조회
    profile = supabase.table("users").select("*").eq("id", user.user.id).single().execute()
    return profile.data


# ── ★ v3.0: AUTH-06 세션 만료와 AI 작업 분리 ──

async def get_current_user_or_none(request: Request) -> dict | None:
    """세션 만료 여부만 확인 (AI 작업 백그라운드 실행에 사용)."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None  # 세션 만료 — AI 작업은 계속 진행


# ── AUTH-06 아키텍처 원칙 ──
# 1. AI 작업은 세션과 독립적으로 실행:
#    - LangGraph StateGraph 실행은 서버 측 asyncio task로 동작
#    - ai_task_logs에 작업 결과를 영속화 (세션 무관)
#    - 사용자 세션이 만료되어도 진행 중인 AI 작업은 중단하지 않음
#
# 2. 재로그인 시 미확인 결과 자동 표시:
#    - 로그인 시 ai_task_logs에서 status='complete' AND viewed=false 조회
#    - SSE 연결 재수립 시 미확인 이벤트 일괄 전송
#    - 프론트엔드에서 "AI 작업 완료 알림" 배지 표시
#
# 3. AI 작업 결과 영속화 흐름:
#    AI 작업 완료 → ai_task_logs.status='complete' + result JSONB 저장
#    → notification 생성 (NOTI-11)
#    → 사용자 재접속 시 GET /api/proposals/{id}/ai-logs?viewed=false 로 조회


def require_role(*roles: str):
    """역할 기반 접근 제어 데코레이터."""
    async def check(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(403, f"권한 부족: {user['role']} not in {roles}")
        return user
    return check
```

### 17-2. 결재선 서비스

```python
# app/services/approval_chain.py

async def build_approval_chain(proposal_id: str, step: str) -> list[dict]:
    """
    프로젝트 예산 기준으로 결재선 구성.
    - 3억 미만: [팀장]
    - 3~5억: [팀장, 본부장]
    - 5억 이상: [팀장, 본부장, 경영진]
    """
    proposal = await get_proposal(proposal_id)
    budget = proposal.get("budget_amount", 0)
    team_id = proposal["team_id"]
    division_id = proposal["division_id"]

    chain = []
    # 팀장 (항상 필요)
    lead = await get_team_lead(team_id)
    chain.append({"role": "lead", "user_id": lead["id"], "user_name": lead["name"]})

    if budget >= 300_000_000:
        director = await get_division_director(division_id)
        chain.append({"role": "director", "user_id": director["id"], "user_name": director["name"]})

    if budget >= 500_000_000:
        executive = await get_executive()
        chain.append({"role": "executive", "user_id": executive["id"], "user_name": executive["name"]})

    return chain


async def check_can_approve(user: dict, proposal_id: str, step: str) -> bool:
    """현재 사용자가 이 단계를 승인할 권한이 있는지 확인."""
    chain = await build_approval_chain(proposal_id, step)
    # 결재선에 포함된 역할만 승인 가능
    user_role = user["role"]
    return any(c["role"] == user_role and c["user_id"] == user["id"] for c in chain)
```

---

## 18. ★ Teams 알림 연동 (v2.0)

```python
# app/services/notification_service.py

import httpx
from app.config import TEAMS_WEBHOOK_DEFAULT

async def send_teams_notification(
    team_id: str,
    title: str,
    body: str,
    link: str = "",
):
    """Teams Incoming Webhook으로 알림 발송."""
    # 팀별 Webhook URL 조회 (teams 테이블)
    team = await get_team(team_id)
    webhook_url = team.get("teams_webhook_url") or TEAMS_WEBHOOK_DEFAULT

    if not webhook_url:
        return  # Webhook 미설정 시 생략

    card = {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {"type": "TextBlock", "text": title, "weight": "bolder", "size": "medium"},
                    {"type": "TextBlock", "text": body, "wrap": True},
                ],
                "actions": [
                    {"type": "Action.OpenUrl", "title": "바로 가기", "url": link}
                ] if link else [],
            },
        }],
    }

    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=card)


async def notify_approval_request(proposal_id: str, step: str, approver_id: str):
    """승인 요청 알림 (Teams + 인앱)."""
    proposal = await get_proposal(proposal_id)
    approver = await get_user(approver_id)

    # 인앱 알림 생성
    await create_notification(
        user_id=approver_id,
        proposal_id=proposal_id,
        type="approval_request",
        title=f"[승인 요청] {proposal['name']}",
        body=f"{step} 단계 승인이 필요합니다.",
        link=f"/projects/{proposal_id}/review/{step}",
    )

    # Teams 알림
    await send_teams_notification(
        team_id=proposal["team_id"],
        title=f"🔔 승인 요청: {proposal['name']}",
        body=f"{approver['name']}님, {step} 단계 승인을 요청드립니다.",
        link=f"{APP_URL}/projects/{proposal_id}/review/{step}",
    )


async def notify_deadline_alert(proposal_id: str, days_left: int):
    """마감 임박 알림 (D-7, D-3, D-1)."""
    proposal = await get_proposal(proposal_id)
    participants = await get_participants(proposal_id)

    for user in participants:
        await create_notification(
            user_id=user["user_id"],
            proposal_id=proposal_id,
            type="deadline",
            title=f"⏰ 마감 D-{days_left}: {proposal['name']}",
            body=f"제출 마감까지 {days_left}일 남았습니다.",
            link=f"/projects/{proposal_id}",
        )

    await send_teams_notification(
        team_id=proposal["team_id"],
        title=f"⏰ 마감 D-{days_left}: {proposal['name']}",
        body=f"제출 마감까지 {days_left}일 남았습니다. 현재 단계: {proposal.get('status', '')}",
        link=f"{APP_URL}/projects/{proposal_id}",
    )
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

## 20. ★ Knowledge Base 설계 (v3.0)

> **요구사항 §4 (Part A~F + Export) 대응**. 모든 KB 데이터는 조직(org_id) 단위로 격리, pgvector 시맨틱 검색 지원.

### 20-1. 임베딩 서비스

```python
# app/services/embedding_service.py
from openai import AsyncOpenAI

EMBEDDING_MODEL = "text-embedding-3-small"  # 1536차원
EMBEDDING_DIMENSIONS = 1536

openai_client = AsyncOpenAI()

async def generate_embedding(text: str) -> list[float]:
    """텍스트 → 임베딩 벡터 생성."""
    response = await openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text[:8000],  # 토큰 제한 방어
    )
    return response.data[0].embedding


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """배치 임베딩 생성 (최대 100건)."""
    response = await openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[t[:8000] for t in texts[:100]],
    )
    return [d.embedding for d in response.data]
```

### 20-2. 통합 KB 검색 서비스

```python
# app/services/knowledge_search.py

async def unified_search(
    query: str,
    org_id: str,
    filters: dict = None,  # { areas: ["content","client","competitor","lesson","capability"], period, industry, positioning }
    top_k: int = 5,
    max_body_length: int = 500,  # TKN-04: 본문 축약 상한
) -> dict:
    """
    통합 KB 검색 — 시맨틱(pgvector) + 키워드(tsvector) 하이브리드.
    결과를 영역별로 그룹화하여 반환.
    """
    query_embedding = await generate_embedding(query)

    results = {}
    areas = filters.get("areas", ["content","client","competitor","lesson","capability"]) if filters else None

    # 영역별 병렬 검색
    tasks = []
    if not areas or "content" in areas:
        tasks.append(_search_content(query, query_embedding, org_id, top_k, max_body_length))
    if not areas or "client" in areas:
        tasks.append(_search_clients(query, query_embedding, org_id, top_k))
    if not areas or "competitor" in areas:
        tasks.append(_search_competitors(query, query_embedding, org_id, top_k))
    if not areas or "lesson" in areas:
        tasks.append(_search_lessons(query, query_embedding, org_id, top_k))
    if not areas or "capability" in areas:
        tasks.append(_search_capabilities(query, org_id, top_k))

    all_results = await asyncio.gather(*tasks)
    # 영역별 그룹화 반환
    return {r["area"]: r["items"] for r in all_results}


async def _search_content(query, embedding, org_id, top_k, max_body):
    """콘텐츠 라이브러리 시맨틱 검색 (pgvector cosine similarity)."""
    rows = await db.execute("""
        SELECT id, title, LEFT(body, $4) as body_excerpt, quality_score,
               1 - (embedding <=> $1::vector) as similarity
        FROM content_library
        WHERE org_id = $2 AND status = 'published'
        ORDER BY embedding <=> $1::vector
        LIMIT $3
    """, embedding, org_id, top_k, max_body)
    return {"area": "content", "items": rows}
```

### 20-3. 콘텐츠 라이브러리 서비스

```python
# app/services/content_library.py

async def calculate_quality_score(content_id: str) -> float:
    """
    콘텐츠 품질 점수 산출 (CL-08):
    quality_score = (won_rate × 40) + (reuse_rate × 30) + (freshness × 30)
    - won_rate: 이 콘텐츠 포함 제안서 수주 비율
    - reuse_rate: 재사용 횟수 (정규화)
    - freshness: 최근 갱신일 기준 (6개월 내 = 100%, 이후 감쇠)
    """
    content = await get_content(content_id)
    total = content["won_count"] + content["lost_count"]
    won_rate = (content["won_count"] / total * 100) if total > 0 else 50
    reuse_rate = min(content["reuse_count"] / 10 * 100, 100)  # 10회 이상이면 100%
    days_since_update = (now() - content["updated_at"]).days
    freshness = max(0, 100 - (days_since_update - 180) * 0.5) if days_since_update > 180 else 100

    return won_rate * 0.4 + reuse_rate * 0.3 + freshness * 0.3


async def suggest_content_for_section(
    section_topic: str,
    org_id: str,
    top_k: int = 5,
) -> list[dict]:
    """STEP 4 섹션 작성 시 유사 콘텐츠 자동 추천 (DOC-14)."""
    results = await unified_search(
        query=section_topic,
        org_id=org_id,
        filters={"areas": ["content"]},
        top_k=top_k,
    )
    return sorted(results.get("content", []), key=lambda x: x["quality_score"], reverse=True)
```

### 20-4. 학습 피드백 루프 (프로젝트 완료 시 자동 KB 환류)

```python
# app/services/feedback_loop.py

async def process_project_completion(proposal_id: str, result: str):
    """
    프로젝트 완료 시 KB 자동 환류 (LRN-03~07):
    1. 발주기관 DB 업데이트 제안
    2. 경쟁사 DB 업데이트 제안
    3. 전략 아카이브 기록
    4. (수주 시) 콘텐츠 라이브러리 등록 후보 추천
    """
    proposal = await get_proposal(proposal_id)

    # 1. 발주기관 DB 자동 업데이트 제안
    if proposal.get("client"):
        client = await find_client_by_name(proposal["client"], proposal["org_id"])
        if client:
            await create_client_bid_history(client["id"], proposal_id, result)
            # 관계 수준 업데이트 제안 (수주→격상, 패찰→유지)
            suggested_relationship = "close" if result == "won" else client["relationship"]
            await create_notification(
                user_id=proposal["created_by"],
                type="kb_update_suggestion",
                title=f"발주기관 DB 업데이트 제안: {proposal['client']}",
                body=f"관계 수준: {client['relationship']} → {suggested_relationship} (제안)",
            )

    # 2. 콘텐츠 라이브러리 등록 후보 추천 (수주 시)
    if result == "won":
        sections = await get_proposal_sections(proposal_id)
        for section in sections:
            await create_notification(
                user_id=proposal["created_by"],
                type="content_suggestion",
                title=f"콘텐츠 등록 후보: {section['title']}",
                body=f"수주 제안서 '{proposal['name']}'의 섹션을 콘텐츠 라이브러리에 등록하시겠습니까?",
            )

    # 3. 교훈 아카이브 기록 준비 (회고 워크시트 작성 대기)
    await create_notification(
        user_id=proposal["created_by"],
        type="retrospect_reminder",
        title=f"회고 작성 요청: {proposal['name']}",
        body="프로젝트 결과가 등록되었습니다. 7일 이내에 회고 워크시트를 작성해 주세요.",
    )
```

### 20-5. KB 내보내기 API

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/api/kb/export/capabilities` | 역량 DB CSV/Excel 다운로드 | lead (소속 팀), admin (전체) |
| GET | `/api/kb/export/clients` | 발주기관 DB CSV/Excel 다운로드 | lead, admin |
| GET | `/api/kb/export/competitors` | 경쟁사 DB CSV/Excel 다운로드 | lead, admin |
| GET | `/api/kb/export/content` | 콘텐츠 라이브러리 메타 CSV + 본문 ZIP | lead, admin |
| GET | `/api/kb/export/lessons` | 교훈 아카이브 CSV/Excel 다운로드 | lead, admin |

### 20-6. KB API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/kb/search` | 통합 KB 검색 (시맨틱 + 키워드, 영역별 그룹화) |
| GET/POST/PUT/DELETE | `/api/content-library/*` | 콘텐츠 라이브러리 CRUD |
| POST | `/api/content-library/{id}/approve` | 콘텐츠 승인 (팀장) |
| GET/POST/PUT/DELETE | `/api/clients/*` | 발주기관 DB CRUD |
| GET/POST/PUT/DELETE | `/api/competitors/*` | 경쟁사 DB CRUD |
| GET/POST | `/api/lessons/*` | 교훈 아카이브 조회·작성 |
| POST | `/api/proposals/{id}/retrospect` | 회고 워크시트 작성 → retrospect 상태 전환 |

---

## 21. ★ AI 토큰 효율화 설계 (v3.0)

> **요구사항 §12-2 (TKN-01~09) 대응**. Claude API 비용의 대부분은 input 토큰에서 발생. 필요한 정보만 필요한 만큼 전달.

### 21-1. 토큰 매니저

```python
# app/services/token_manager.py
from anthropic import Anthropic

# STEP별 컨텍스트 토큰 예산 (TKN-01) — 설계 시 산정
STEP_TOKEN_BUDGETS = {
    "rfp_search":    8_000,   # STEP 0: 공고 목록 + 역량 요약
    "rfp_analyze":   30_000,  # STEP 1①: RFP 원문 (가장 큼)
    "go_no_go":      15_000,  # STEP 1②: RFP분석서 + 역량 + 발주기관 + 경쟁사
    "strategy":      20_000,  # STEP 2: RFP분석서 + 역량 + KB 검색 결과
    "plan_section":  12_000,  # STEP 3: 각 병렬 Agent
    "proposal_section": 15_000,  # STEP 4: 각 섹션 (공통 컨텍스트는 캐시)
    "self_review":   20_000,  # STEP 4: 전체 제안서 + Compliance
    "ppt_slide":     10_000,  # STEP 5: 각 슬라이드
}

# KB 검색 결과 상한 (TKN-04)
KB_TOP_K = 5
KB_MAX_BODY_LENGTH = 500  # 각 건 본문 축약 길이

# 피드백 윈도우 (TKN-03)
FEEDBACK_WINDOW_SIZE = 3  # 최근 N회분만 전체 포함


class TokenManager:
    """토큰 예산 관리 + Prompt Caching 제어."""

    @staticmethod
    def build_context(
        step: str,
        rfp_summary: dict,        # TKN-02: RFP분석서 (원문 아님)
        strategy: dict = None,
        plan: dict = None,
        feedback_history: list = None,
        kb_results: list = None,
        section_specific: dict = None,
    ) -> tuple[list[dict], dict]:
        """
        STEP별 컨텍스트 구성.
        반환: (messages, cache_control_config)

        TKN-02: RFP 원문 대신 RFP분석서(구조화 요약)를 전달
        TKN-03: 피드백 최근 3회분 + 이전은 요약
        TKN-04: KB 검색 결과 Top-K, 본문 축약
        TKN-05/06: 공통 컨텍스트는 cache_control로 캐시 대상 지정
        """
        budget = STEP_TOKEN_BUDGETS.get(step, 15_000)

        # ── 공통 컨텍스트 (Prompt Caching 대상) ──
        system_prompt = _build_system_prompt(step)
        common_context = _build_common_context(rfp_summary, strategy, plan)

        # ── 피드백 윈도우 (TKN-03) ──
        feedback_text = ""
        if feedback_history:
            recent = feedback_history[-FEEDBACK_WINDOW_SIZE:]
            older = feedback_history[:-FEEDBACK_WINDOW_SIZE]
            if older:
                feedback_text += f"[이전 피드백 요약] {_summarize_feedbacks(older)}\n\n"
            for fb in recent:
                feedback_text += f"[피드백 #{fb.get('version','')}] {fb.get('feedback','')}\n"

        # ── KB 검색 결과 (TKN-04) ──
        kb_text = ""
        if kb_results:
            for item in kb_results[:KB_TOP_K]:
                body = item.get("body_excerpt", item.get("body", ""))[:KB_MAX_BODY_LENGTH]
                kb_text += f"- [{item.get('area','')}] {item.get('title','')}: {body}\n"

        # ── 메시지 구성 ──
        messages = [
            {
                "role": "system",
                "content": system_prompt + "\n\n" + common_context,
                # TKN-06: 공통 컨텍스트에 Prompt Caching 적용
                "cache_control": {"type": "ephemeral"},
            },
        ]

        user_content = ""
        if feedback_text:
            user_content += f"## 피드백 이력\n{feedback_text}\n\n"
        if kb_text:
            user_content += f"## KB 참조 자료 (상위 {KB_TOP_K}건)\n{kb_text}\n\n"
        if section_specific:
            user_content += f"## 현재 작업\n{_format_section_context(section_specific)}\n"

        messages.append({"role": "user", "content": user_content})

        return messages

    @staticmethod
    def build_structured_output_schema(step: str) -> dict:
        """TKN-09: 산출물별 JSON Structured Output 스키마."""
        schemas = {
            "rfp_analyze": {
                "type": "json_schema",
                "json_schema": {
                    "name": "rfp_analysis",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "project_name": {"type": "string"},
                            "client": {"type": "string"},
                            "deadline": {"type": "string"},
                            "case_type": {"type": "string", "enum": ["A", "B"]},
                            "eval_items": {"type": "array"},
                            "tech_price_ratio": {"type": "object"},
                            "hot_buttons": {"type": "array"},
                            "mandatory_reqs": {"type": "array"},
                            "format_template": {"type": "object"},
                            "volume_spec": {"type": "object"},
                            "special_conditions": {"type": "array"},
                        },
                        "required": ["project_name", "client", "case_type", "eval_items", "hot_buttons"],
                    },
                },
            },
            # go_no_go, strategy, plan 등 각 STEP별 스키마 정의...
        }
        return schemas.get(step)
```

### 21-2. Compliance Matrix 규칙/AI 분리 (TKN-07)

```python
# app/services/compliance_tracker.py (v3.0 확장)

class ComplianceTracker:
    """v3.0: 규칙 기반 검증과 AI 판단 검증을 분리."""

    @staticmethod
    async def check_compliance_hybrid(
        sections: list[ProposalSection],
        matrix: list[ComplianceItem],
        rfp_analysis: RFPAnalysis,
    ) -> list[ComplianceItem]:
        """
        TKN-07: 규칙 기반 + AI 판단 하이브리드 검증.
        규칙 검증 가능한 항목은 코드로 자동 처리 (AI 호출 불필요).
        """
        for item in matrix:
            # ── 규칙 기반 자동 검증 (AI 미사용) ──
            if item.source_step == "rfp" and _is_rule_checkable(item):
                item.status = _rule_check(item, sections, rfp_analysis)
            # ── AI 판단 필요 항목만 AI 호출 ──
            else:
                pass  # 배치로 모아서 1회 AI 호출

        # AI 판단 필요 항목 배치 처리
        ai_items = [i for i in matrix if i.status == "미확인"]
        if ai_items:
            all_content = "\n".join(s.content for s in sections)
            results = await claude_generate(
                COMPLIANCE_BATCH_CHECK_PROMPT.format(
                    items=[{"req_id": i.req_id, "content": i.content} for i in ai_items],
                    proposal_content=all_content[:20000],  # 토큰 제한
                ),
            )
            for item, result in zip(ai_items, results):
                item.status = result["status"]
                item.proposal_section = result.get("matching_section", "")

        return matrix

    @staticmethod
    def _is_rule_checkable(item: ComplianceItem) -> bool:
        """규칙 기반 검증 가능 여부 판단."""
        # 분량·서식·필수 요건 포함 여부는 규칙으로 체크 가능
        return any(kw in item.content for kw in ["분량", "페이지", "서식", "용지", "글자"])

    @staticmethod
    def _rule_check(item, sections, rfp) -> str:
        """규칙 기반 자동 검증."""
        total_length = sum(len(s.content) for s in sections)
        if "분량" in item.content or "페이지" in item.content:
            max_pages = rfp.volume_spec.get("max_pages", 999)
            est_pages = total_length / 2000  # 대략 페이지 추정
            return "충족" if est_pages <= max_pages else "미충족"
        return "미확인"
```

### 21-3. 섹션별 출력 토큰 상한 (TKN-08)

```python
# proposal_nodes.py 내 출력 토큰 계산

def calculate_section_max_tokens(rfp_analysis: RFPAnalysis, section_count: int) -> int:
    """
    TKN-08: RFP 분량 제한에서 섹션별 출력 토큰 상한 자동 계산.
    1페이지 ≈ 500 토큰 (한국어 기준)
    """
    max_pages = rfp_analysis.volume_spec.get("max_pages", 50)
    tokens_per_page = 500
    total_budget = max_pages * tokens_per_page
    # 섹션별 균등 배분 (배점 비중으로 가중 가능)
    return total_budget // max(section_count, 1)
```

---

## 22. ★ AI 실행 상태 모니터링 설계 (v3.0)

> **요구사항 §5-1 (AGT-01~11) 대응**. AI Coworker 작업 중 실시간 상태·진행률·Heartbeat를 SSE로 클라이언트에 전달.

### 22-1. AI 상태 매니저

```python
# app/services/ai_status_manager.py
import asyncio
from datetime import datetime, timedelta

HEARTBEAT_TIMEOUT = 60  # 초 — AGT-08

class AiStatusManager:
    """프로젝트별 AI 실행 상태 관리."""

    def __init__(self):
        self._states: dict[str, dict] = {}  # proposal_id → status dict

    async def start_task(self, proposal_id: str, step: str, sub_tasks: list[str] = None):
        """AI 작업 시작 등록."""
        self._states[proposal_id] = {
            "status": "running",         # idle | running | complete | error | paused | no_response | waiting_approval
            "step": step,
            "sub_tasks": {
                t: {"status": "pending", "started_at": None, "completed_at": None, "duration_ms": None}
                for t in (sub_tasks or [step])
            },
            "progress_pct": 0,
            "started_at": datetime.utcnow().isoformat(),
            "last_heartbeat": datetime.utcnow(),
            "error": None,
        }
        # DB에도 기록 (ai_task_logs)
        await self._log_task(proposal_id, step, "running")

    async def update_sub_task(self, proposal_id: str, sub_task: str, status: str):
        """하위 작업 상태 갱신 + 진행률 자동 계산."""
        state = self._states.get(proposal_id)
        if not state:
            return
        if sub_task in state["sub_tasks"]:
            state["sub_tasks"][sub_task]["status"] = status
            if status == "running":
                state["sub_tasks"][sub_task]["started_at"] = datetime.utcnow().isoformat()
            elif status in ("complete", "error"):
                state["sub_tasks"][sub_task]["completed_at"] = datetime.utcnow().isoformat()

        # 진행률 계산
        total = len(state["sub_tasks"])
        done = sum(1 for t in state["sub_tasks"].values() if t["status"] in ("complete",))
        state["progress_pct"] = int(done / total * 100) if total > 0 else 0

        # Heartbeat 갱신
        state["last_heartbeat"] = datetime.utcnow()

        # SSE 이벤트 발송
        await self._emit_sse(proposal_id, "ai_status", state)

    async def heartbeat(self, proposal_id: str):
        """Heartbeat 수신 — 60초 이상 무응답 시 no_response."""
        state = self._states.get(proposal_id)
        if state:
            state["last_heartbeat"] = datetime.utcnow()

    async def check_heartbeat(self, proposal_id: str) -> bool:
        """Heartbeat 타임아웃 체크 (AGT-08)."""
        state = self._states.get(proposal_id)
        if not state or state["status"] != "running":
            return True
        elapsed = (datetime.utcnow() - state["last_heartbeat"]).total_seconds()
        if elapsed > HEARTBEAT_TIMEOUT:
            state["status"] = "no_response"
            await self._emit_sse(proposal_id, "ai_status", state)
            # 담당자 + 팀장에게 알림 (NOTI-10)
            await notify_ai_no_response(proposal_id, state["step"])
            return False
        return True

    async def abort_task(self, proposal_id: str):
        """사용자 요청에 의한 AI 작업 중단 (AGT-06). 완료된 하위 작업 결과는 보존."""
        state = self._states.get(proposal_id)
        if state:
            state["status"] = "paused"
            await self._emit_sse(proposal_id, "ai_status", state)

    async def get_composite_status(self, proposal_id: str) -> dict:
        """AGT-11: 복합 상태 조회 (프로젝트 상태 + 현재 STEP + AI 상태)."""
        proposal = await get_proposal(proposal_id)
        ai_state = self._states.get(proposal_id, {"status": "idle"})
        return {
            "project_status": proposal["status"],
            "current_step": proposal.get("current_step", ""),
            "ai_status": ai_state["status"],
            "ai_progress_pct": ai_state.get("progress_pct", 0),
            "ai_sub_tasks": ai_state.get("sub_tasks", {}),
        }
```

### 22-2. SSE 이벤트 타입 확장

```python
# app/api/routes_workflow.py (v3.0 확장)

SSE_EVENT_TYPES = {
    "workflow_progress":  "워크플로 단계 전환",
    "artifact_ready":     "산출물 생성 완료",
    "approval_required":  "승인 대기 전환",
    "ai_status":          "★ AI 상태 변경 (running/complete/error/paused/no_response)",
    "ai_progress":        "★ AI 진행률 갱신 (%, 하위 작업별)",
    "ai_heartbeat":       "★ AI Heartbeat (alive 확인)",
    "section_lock":       "★ 섹션 편집 잠금/해제 알림",
    "notification":       "인앱 알림",
}

# 단일 SSE 연결 원칙 (NFR-07): 모든 이벤트를 event 타입으로 구분하여 1개 연결로 멀티플렉싱
async def sse_stream(proposal_id: str):
    """SSE 스트림 — 모든 이벤트 타입을 하나의 연결로 전달."""
    async for event in event_bus.subscribe(proposal_id):
        yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"
```

### 22-3. AI 상태 API

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/proposals/{id}/ai-status` | AI 실행 상태 조회 (AGT-11 복합 상태) |
| POST | `/api/proposals/{id}/ai-abort` | AI 작업 중단 (AGT-06) |
| POST | `/api/proposals/{id}/ai-retry` | AI 작업 재시도 (AGT-07) |
| GET | `/api/proposals/{id}/ai-logs` | AI 작업 이력 조회 (AGT-09) |

### 22-4. ★ v3.3: Fallback 전략 (ProposalForge 비교 검토 반영)

> 체계적 장애 대응 전략. 기존 §22 Heartbeat/no_response와 일관되게 설계.

#### 22-4-1. Claude API 장애

| 단계 | 조건 | 동작 |
|------|------|------|
| 1차 | API 오류 (5xx, timeout) | 지수 백오프 재시도 (1s → 2s → 4s, 최대 3회) |
| 2차 | 3회 재시도 실패 | `ai_task_logs.status = 'error'` 기록, SSE `ai_status: error` 발송 |
| 3차 | 사용자 안내 | 인앱 알림 + Teams 알림: "AI 작업 실패 — 수동 진행 또는 재시도 가능" |

> **다중 LLM Fallback (Claude → GPT 등)은 의도적으로 스킵**. 프롬프트 호환성 관리 비용이 크고, 재시도 + 에러 알림으로 충분. (ProposalForge 비교 검토 §4-2)

```python
# app/services/claude_client.py — Fallback 재시도 로직

import asyncio
from anthropic import APIError, APITimeoutError

MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds

async def call_claude_with_retry(prompt: str, **kwargs) -> dict:
    """지수 백오프 재시도 + 실패 시 에러 기록."""
    for attempt in range(MAX_RETRIES):
        try:
            return await claude_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
        except (APIError, APITimeoutError) as e:
            if attempt == MAX_RETRIES - 1:
                # 최종 실패: 에러 로깅 + 알림
                await log_ai_error(e, prompt_summary=prompt[:200])
                raise
            delay = BASE_DELAY * (2 ** attempt)
            await asyncio.sleep(delay)
```

#### 22-4-2. 외부 데이터 소스 장애 (MCP/G2B/나라장터)

| 소스 | 장애 시 동작 |
|------|-------------|
| G2B 공고 검색 | 캐시(`g2b_cache`) 조회 → 없으면 `[G2B 접속 불가]` 태그 + 수동 RFP 업로드 안내 |
| 노임단가 DB (`labor_rates`) | 최근 연도 데이터 fallback → 없으면 `[노임단가 미확인]` 플레이스홀더 유지 |
| 시장 낙찰가 (`market_price_data`) | 해당 데이터 스킵 + `[벤치마크 데이터 부족]` 태그 → 수동 입력 안내 |
| KB 검색 (pgvector) | 검색 결과 0건 시 `[참조 데이터 없음]` 태그 → 프롬프트에서 일반 지식 기반 생성 |

#### 22-4-3. 품질 게이트 반복 실패

| 조건 | 동작 |
|------|------|
| `self_review` 2회 연속 80점 미만 | `force_review` → Human 판단 (기존 §8 `MAX_AUTO_IMPROVE=2`와 일관) |
| `retry_research` 후에도 trustworthiness < 12 | `force_review` → Human 판단 (무한 루프 방지) |
| `retry_strategy` 후에도 strategy_score < 15 | `force_review` → Human 판단 (무한 루프 방지) |

> **무한 루프 방지 원칙**: 모든 피드백 루프는 최대 재시도 횟수를 가짐. `_auto_improve_count` (§8)와 동일 메커니즘으로 `_retry_research_count`, `_retry_strategy_count`를 추적 (각 최대 1회).

#### 22-4-4. 노드별 타임아웃

| 노드 유형 | 타임아웃 | 초과 시 |
|-----------|---------|---------|
| 단일 LLM 호출 노드 | 120s | `no_response` → Heartbeat 알림 (기존 §22-1) |
| 병렬 fan-out 노드 | 300s (전체) | 완료된 하위 작업 보존 + 미완료 작업 `error` 처리 |
| 외부 API 호출 | 30s | 해당 데이터 스킵 + 태그 (§22-4-2 참조) |

---

## 23. ★ 사용자 라이프사이클 + 크로스팀 + 컨소시엄 설계 (v3.0)

> **요구사항 §2-7 (ULM), §10-1 (TEAM-09~11), §10-2 (CST) 대응**.

### 23-1. 사용자 관리 API 확장

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| POST | `/api/users` | 사용자 등록 (이름·이메일·소속·역할) | admin |
| POST | `/api/users/bulk` | CSV 일괄 등록 (OB-03) | admin |
| PUT | `/api/users/{id}/team` | 소속 변경 (기존 프로젝트 접근 유지 여부 선택) | admin |
| PUT | `/api/users/{id}/deactivate` | 계정 비활성화 (soft delete) + 후임자 지정 안내 | admin |
| PUT | `/api/users/{id}/reactivate` | 계정 재활성화 | admin |
| POST | `/api/users/{id}/delegate` | 임시 위임 (ULM-07) | admin, lead |
| GET | `/api/users/{id}/projects` | 담당 프로젝트 목록 (퇴사·이동 시 후임 지정용) | admin |

### 23-2. 자기결재 방지 (§2-4)

```python
# app/services/approval_chain.py (v3.0 확장)

async def build_approval_chain(proposal_id: str, step: str) -> list[dict]:
    """
    결재선 구성 — 자기결재 방지 원칙 적용.
    프로젝트 생성자가 팀장인 경우, 차상위 결재자(본부장)로 상향.
    """
    proposal = await get_proposal(proposal_id)
    budget = proposal.get("budget_amount", 0)
    team_id = proposal["team_id"]
    created_by = proposal["created_by"]

    lead = await get_team_lead(team_id)
    chain = []

    # 자기결재 방지: 생성자 == 팀장이면 팀장 단계 건너뛰고 본부장부터
    if lead["id"] == created_by:
        director = await get_division_director(proposal["division_id"])
        chain.append({"role": "director", "user_id": director["id"], "user_name": director["name"]})
        if budget >= 500_000_000:
            executive = await get_executive()
            chain.append({"role": "executive", "user_id": executive["id"], "user_name": executive["name"]})
    else:
        chain.append({"role": "lead", "user_id": lead["id"], "user_name": lead["name"]})
        if budget >= 300_000_000:
            director = await get_division_director(proposal["division_id"])
            chain.append({"role": "director", "user_id": director["id"], "user_name": director["name"]})
        if budget >= 500_000_000:
            executive = await get_executive()
            chain.append({"role": "executive", "user_id": executive["id"], "user_name": executive["name"]})

    # 임시 위임 체크
    chain = await _apply_delegation(chain)
    return chain
```

### 23-3. 크로스팀 프로젝트

```python
# 프로젝트 생성 시 참여 팀 지정
# POST /api/proposals
{
    "name": "AI 플랫폼 구축",
    "mode": "full",
    "participating_teams": ["team-uuid-2", "team-uuid-3"],  # 참여 팀
    # ... 기타
}

# 크로스팀 대시보드 가시성 (TEAM-11):
# 참여 팀장의 대시보드 쿼리에 project_teams 조인 추가
# SELECT * FROM proposals p
# JOIN project_teams pt ON p.id = pt.proposal_id
# WHERE pt.team_id = {team_id}
```

### 23-4. 컨소시엄 관리

```python
# POST /api/proposals/{id}/consortium
{
    "company_name": "○○기술",
    "role": "partner",
    "scope": "데이터 분석 모듈 개발",
    "personnel_count": 3,
    "share_amount": 120000000,
    "contact_name": "김담당",
    "contact_email": "kim@example.com"
}
# CST-06: 참여사는 시스템 계정 없음 — 담당 섹션은 DOCX 업로드로 수집
```

---

## 24. ★ 동시 편집 충돌 방지 설계 (v3.0)

> **요구사항 GATE-17/18 대응**. 동일 섹션을 다른 사용자가 편집 중일 때 잠금 표시 + 읽기 전용 전환.

### 24-1. 섹션 잠금 서비스

```python
# app/services/section_lock.py

LOCK_DURATION_MINUTES = 5  # 자동 해제 타임아웃

class SectionLockService:
    """섹션별 편집 잠금 관리."""

    async def acquire_lock(self, proposal_id: str, section_id: str, user_id: str) -> dict:
        """섹션 잠금 획득. 이미 다른 사용자가 잠금 중이면 실패."""
        # 만료된 잠금 정리
        await self._cleanup_expired()

        existing = await db.fetchone(
            "SELECT * FROM section_locks WHERE proposal_id=$1 AND section_id=$2",
            proposal_id, section_id
        )
        if existing and existing["locked_by"] != user_id:
            locker = await get_user(existing["locked_by"])
            return {
                "acquired": False,
                "locked_by": locker["name"],
                "locked_at": existing["locked_at"],
                "expires_at": existing["expires_at"],
            }

        expires_at = datetime.utcnow() + timedelta(minutes=LOCK_DURATION_MINUTES)
        await db.execute("""
            INSERT INTO section_locks (proposal_id, section_id, locked_by, expires_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (proposal_id, section_id) DO UPDATE
            SET locked_by=$3, locked_at=now(), expires_at=$4
        """, proposal_id, section_id, user_id, expires_at)

        # SSE로 잠금 알림 발송
        await emit_sse(proposal_id, "section_lock", {
            "section_id": section_id, "locked_by": user_id, "action": "locked"
        })
        return {"acquired": True, "expires_at": expires_at.isoformat()}

    async def release_lock(self, proposal_id: str, section_id: str, user_id: str):
        """잠금 해제 (수동)."""
        await db.execute(
            "DELETE FROM section_locks WHERE proposal_id=$1 AND section_id=$2 AND locked_by=$3",
            proposal_id, section_id, user_id
        )
        await emit_sse(proposal_id, "section_lock", {
            "section_id": section_id, "action": "unlocked"
        })
```

### 24-2. 섹션 잠금 API

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/proposals/{id}/sections/{section_id}/lock` | 섹션 편집 잠금 획득 |
| DELETE | `/api/proposals/{id}/sections/{section_id}/lock` | 섹션 편집 잠금 해제 |
| GET | `/api/proposals/{id}/sections/locks` | 현재 잠금 목록 조회 |

---

## 25. ★ 입력 검증 및 파일 보안 설계 (v3.0)

> **요구사항 §12-5 (VAL-01~07), NFR-11 대응**.

### 25-1. 입력 검증 미들웨어

```python
# app/services/input_validator.py
import magic  # python-magic (MIME 타입 검증)

# VAL-01: RFP 파일 허용 확장자 + 크기
RFP_ALLOWED_EXTENSIONS = {".pdf", ".hwpx"}
RFP_MAX_SIZE_MB = 50

# VAL-02: 첨부 파일 허용 확장자
ATTACHMENT_ALLOWED_EXTENSIONS = {".pdf", ".hwpx", ".docx", ".pptx", ".xlsx", ".csv"}

# VAL-03: 단일 필드 텍스트
TEXT_SHORT_MAX_LENGTH = 200

# VAL-04: 장문 텍스트
TEXT_LONG_MAX_LENGTH = 10_000

# VAL-06: 숫자 범위
BUDGET_MIN = 1
BUDGET_MAX = 99_900_000_000  # 999억


async def validate_file_upload(file, allowed_extensions: set, max_size_mb: int = 50):
    """파일 업로드 검증 — 확장자 + 크기 + MIME 타입."""
    # 확장자 체크
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"허용되지 않는 파일 형식: {ext}. 허용: {allowed_extensions}")

    # 크기 체크
    content = await file.read()
    if len(content) > max_size_mb * 1024 * 1024:
        raise ValidationError(f"파일 크기 초과: {len(content)} bytes (최대 {max_size_mb}MB)")

    # MIME 타입 체크
    mime = magic.from_buffer(content, mime=True)
    expected_mimes = {
        ".pdf": "application/pdf",
        ".hwpx": "application/hwp+zip",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    if ext in expected_mimes and mime != expected_mimes[ext]:
        raise ValidationError(f"MIME 타입 불일치: {mime} (기대: {expected_mimes[ext]})")

    await file.seek(0)  # 파일 포인터 리셋
    return content


def sanitize_text(text: str, max_length: int = TEXT_LONG_MAX_LENGTH) -> str:
    """텍스트 입력 sanitization — XSS/HTML 태그 제거."""
    import bleach
    cleaned = bleach.clean(text, tags=[], strip=True)
    return cleaned[:max_length]
```

### 25-2. 주기적 자동 모니터링 (SRC-11)

```python
# app/services/scheduled_monitor.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def daily_g2b_monitor():
    """
    SRC-11: 일 1회 G2B 신규 공고 자동 검색.
    등록된 관심 분야·키워드 기반으로 검색 → 적합 공고 발견 시 Teams 알림.
    """
    # 모든 활성 팀의 관심 키워드 수집
    teams = await get_all_active_teams()
    for team in teams:
        keywords = team.get("monitor_keywords", [])
        if not keywords:
            continue

        for kw in keywords:
            results = await g2b_client.search_bids(keywords=kw)
            # 이미 알림한 공고 제외
            new_results = await filter_new_bids(results, team["id"])
            if new_results:
                lead = await get_team_lead(team["id"])
                await send_teams_notification(
                    team_id=team["id"],
                    title=f"🔔 신규 공고 발견 ({len(new_results)}건)",
                    body="\n".join(f"• {r['project_name']} ({r['budget']})" for r in new_results[:5]),
                    link=f"{APP_URL}/projects?search={kw}",
                )

# 매일 09:00 실행
scheduler.add_job(daily_g2b_monitor, "cron", hour=9, minute=0)
```

---

## 26. ★ 회사 템플릿 관리 설계 (v3.0)

> **요구사항 ART-07~10 대응**. DOCX·PPTX 회사 표준 템플릿을 등록·관리하고 산출물 출력 시 자동 적용.

### 26-1. 템플릿 관리 API

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/api/templates` | 템플릿 목록 조회 | all |
| POST | `/api/templates` | 템플릿 업로드 (DOCX/PPTX) | admin |
| PUT | `/api/templates/{id}` | 템플릿 수정 (신규 버전 생성) | admin |
| DELETE | `/api/templates/{id}` | 템플릿 비활성화 | admin |

### 26-2. DOCX/PPTX 빌더 템플릿 적용

```python
# app/services/docx_builder.py (v3.0 확장)

async def build_docx(sections, rfp, proposal_id=None) -> bytes:
    """제안서 DOCX 생성 — 회사 템플릿 자동 적용 (ART-08)."""
    # 활성 DOCX 템플릿 조회
    template = await get_active_template(org_id, type="docx")

    if template:
        # 템플릿 기반 생성: 표지·머리글·바닥글·스타일 적용
        doc = Document(template["file_path"])
        _apply_template_styles(doc, sections)
    else:
        # 기본 스타일로 생성
        doc = Document()

    if rfp.case_type == "B":
        _build_from_template(doc, sections, rfp.format_template["structure"])
    else:
        _build_freeform(doc, sections)

    return _save_to_bytes(doc)
```

---

## 27. ★ 갭 분석 HIGH 항목 보완 설계 (v3.0)

> **갭 분석 결과 HIGH 심각도 7건 중 AUTH-06은 §17-1에 반영 완료. 나머지 6건을 아래에서 설계.**

### 27-1. TRS-09: AI 생성 vs Human 편집 구분 기록

> **목적**: 최종 산출물에서 AI가 작성한 부분과 Human이 직접 수정한 부분을 구분 기록하여 감사 추적 및 품질 관리에 활용.

#### DB 스키마 확장

```sql
-- artifacts 테이블에 편집 주체 추적 컬럼 추가
ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS edit_source TEXT DEFAULT 'ai';
-- 유효값: 'ai' (AI 생성 원본), 'human' (사용자 직접 편집), 'ai_revised' (피드백 반영 AI 재생성)

-- 편집 이력 테이블 (섹션별 변경 추적)
CREATE TABLE artifact_edit_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id     UUID REFERENCES artifacts(id) NOT NULL,
    proposal_id     UUID REFERENCES proposals(id) NOT NULL,
    section_id      TEXT NOT NULL,
    edit_source     TEXT NOT NULL,           -- 'ai' | 'human' | 'ai_revised'
    editor_id       UUID REFERENCES users(id),  -- Human 편집 시 사용자 ID
    diff_summary    TEXT,                    -- 변경 요약 (추가/삭제/수정 줄 수)
    previous_hash   TEXT,                    -- 이전 버전 해시 (변경 감지용)
    current_hash    TEXT,                    -- 현재 버전 해시
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_artifact_edit_history ON artifact_edit_history(proposal_id, section_id);
```

#### API 확장

```python
# app/api/routes_artifact.py 확장

@router.put("/api/proposals/{id}/artifacts/{step}/sections/{section_id}")
async def update_section_content(
    id: str, step: str, section_id: str,
    body: SectionEditRequest,
    user: dict = Depends(get_current_user),
):
    """
    TRS-09: Human이 직접 섹션 내용을 편집할 때 호출.
    edit_source='human'으로 기록하여 AI 생성분과 구분.
    """
    existing = await get_artifact_section(id, step, section_id)
    previous_hash = hashlib.sha256(existing["content"].encode()).hexdigest()
    current_hash = hashlib.sha256(body.content.encode()).hexdigest()

    if previous_hash == current_hash:
        return {"message": "변경 없음"}

    # 편집 이력 기록
    await insert_edit_history(
        artifact_id=existing["artifact_id"],
        proposal_id=id,
        section_id=section_id,
        edit_source="human",
        editor_id=user["id"],
        diff_summary=_compute_diff_summary(existing["content"], body.content),
        previous_hash=previous_hash,
        current_hash=current_hash,
    )

    # 산출물 업데이트
    await update_artifact_content(id, step, section_id, body.content, edit_source="human")
    return {"message": "편집 저장 완료", "edit_source": "human"}
```

> **프론트엔드 연동**: ArtifactViewer에서 각 섹션 옆에 편집 주체 아이콘 표시 (🤖 AI / ✏️ Human / 🔄 AI 재작성).

### 27-2. PSM-05: expired 자동 전환

> **목적**: 제출 기한(deadline)이 지난 프로젝트를 자동으로 `expired` 상태로 전환.

```python
# app/services/scheduled_monitor.py 에 추가

async def check_expired_projects():
    """
    PSM-05: 제출 기한 초과 프로젝트 자동 expired 전환.
    daily_g2b_monitor와 같은 스케줄러에서 실행.

    대상: status IN ('draft','searching','analyzing','strategizing') AND deadline < now()
    제외: 이미 submitted/presented/won/lost/no_go/abandoned/retrospect 상태
    """
    from datetime import datetime, timezone

    expirable_statuses = ('draft', 'searching', 'analyzing', 'strategizing')
    now = datetime.now(timezone.utc)

    expired_projects = await supabase.table("proposals") \
        .select("id, project_name, team_id, status, deadline") \
        .in_("status", expirable_statuses) \
        .lt("deadline", now.isoformat()) \
        .execute()

    for project in expired_projects.data:
        # 상태 전환
        await supabase.table("proposals") \
            .update({
                "status": "expired",
                "previous_status": project["status"],
            }) \
            .eq("id", project["id"]) \
            .execute()

        # 감사 로그
        await insert_audit_log(
            action="auto_expire",
            resource_type="proposal",
            resource_id=project["id"],
            detail={"previous_status": project["status"], "deadline": project["deadline"]},
        )

        # 팀장 알림
        lead = await get_team_lead(project["team_id"])
        if lead:
            await create_notification(
                user_id=lead["id"],
                proposal_id=project["id"],
                type="project_expired",
                title=f"⏰ 프로젝트 기한 만료: {project['project_name']}",
                body=f"제출 기한({project['deadline']})이 지나 자동으로 만료 처리되었습니다. 회고 작성을 권장합니다.",
            )

# 매일 00:30 실행 (daily_g2b_monitor 09:00과 분리)
scheduler.add_job(check_expired_projects, "cron", hour=0, minute=30)
```

### 27-3. PSM-16: Q&A 기록 검색 가능 저장

> **목적**: 발표 후 Q&A 기록을 콘텐츠 라이브러리와 교훈 아카이브에 검색 가능하게 저장.

```python
# app/services/feedback_loop.py 에 추가

async def save_qa_to_kb(proposal_id: str, qa_records: list[dict]):
    """
    PSM-16: Q&A 기록을 KB에 검색 가능하게 저장.
    presentation_qa 테이블에 저장 후, 콘텐츠 라이브러리에도 등록.

    qa_records 형식: [{ "question": str, "answer": str, "category": str }]
    """
    proposal = await get_proposal(proposal_id)

    for qa in qa_records:
        # 1) presentation_qa 테이블 저장 (기존)
        qa_id = await insert_presentation_qa(proposal_id, qa)

        # 2) 콘텐츠 라이브러리에 qa_record 유형으로 등록
        content_body = f"Q: {qa['question']}\nA: {qa['answer']}"
        content_id = await insert_content_library(
            org_id=proposal["org_id"],
            type="qa_record",
            title=f"[Q&A] {qa['question'][:50]}",
            body=content_body,
            source_project_id=proposal_id,
            industry=proposal.get("industry"),
            tags=[qa.get("category", "general"), "qa", "presentation"],
        )

        # 3) 임베딩 생성 → 시맨틱 검색 가능
        embedding = await embedding_service.generate(content_body)
        await update_content_embedding(content_id, embedding)

    # 4) 교훈 아카이브에 Q&A 요약 기록
    if qa_records:
        qa_summary = "\n".join(
            f"• Q: {qa['question'][:80]} → A: {qa['answer'][:80]}"
            for qa in qa_records
        )
        await append_lesson_learned(
            proposal_id=proposal_id,
            category="qa_insight",
            detail=f"발표 Q&A ({len(qa_records)}건):\n{qa_summary}",
        )
```

#### presentation_qa 테이블 확장

```sql
-- 기존 presentation_qa에 임베딩 + 콘텐츠 연결 추가
ALTER TABLE presentation_qa ADD COLUMN IF NOT EXISTS embedding vector(1536);
ALTER TABLE presentation_qa ADD COLUMN IF NOT EXISTS content_library_id UUID REFERENCES content_library(id);

CREATE INDEX idx_presentation_qa_embedding ON presentation_qa USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);
```

### 27-4. POST-06: 발표 없이 서류 심사 시 presented 건너뛰기

> **목적**: 서류 심사만으로 결과가 결정되는 공고의 경우 submitted → won/lost 직접 전환.

#### 프로젝트 상태 머신 확장

```sql
-- proposals 테이블에 심사 방식 플래그 추가
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS eval_method TEXT DEFAULT 'presentation';
-- 유효값: 'presentation' (발표 심사), 'document_only' (서류 심사만)
```

#### 상태 전환 로직

```python
# app/api/routes_proposal.py 확장

@router.post("/api/proposals/{id}/result")
async def register_result(
    id: str,
    body: ResultRequest,  # { result: "won"|"lost"|"canceled", eval_method?: str, ... }
    user: dict = Depends(require_role("lead")),
):
    """
    POST-06: 제안 결과 등록.
    - eval_method='document_only': submitted → won/lost (presented 건너뛰기)
    - eval_method='presentation': submitted → presented → won/lost (기존 흐름)
    """
    proposal = await get_proposal(id)

    if body.eval_method == "document_only":
        # 서류 심사: submitted → 바로 won/lost
        if proposal["status"] not in ("submitted",):
            raise HTTPException(400, "서류 심사 결과는 submitted 상태에서만 등록 가능")
        new_status = body.result  # "won" | "lost" | "canceled"
    else:
        # 발표 심사: presented 상태에서 won/lost
        if proposal["status"] not in ("presented",):
            raise HTTPException(400, "발표 심사 결과는 presented 상태에서만 등록 가능")
        new_status = body.result

    await update_proposal_status(id, new_status)
    await insert_audit_log(
        action="result_registered",
        resource_type="proposal",
        resource_id=id,
        detail={"result": body.result, "eval_method": body.eval_method or "presentation"},
        user_id=user["id"],
    )

    # 수주/패찰 시 KB 환류 트리거
    if new_status in ("won", "lost"):
        await trigger_feedback_loop(id, new_status)

    return {"status": new_status}
```

#### 상태 머신 제약 갱신

```sql
-- submitted → won/lost 직접 전환 허용 (서류 심사 경로)
-- 기존: submitted → presented → won/lost
-- 추가: submitted → won/lost (eval_method='document_only')
COMMENT ON COLUMN proposals.eval_method IS
  'presentation: 발표 심사 (submitted→presented→won/lost), document_only: 서류 심사 (submitted→won/lost 직접)';
```

### 27-5. OPS-02: /health 헬스체크 엔드포인트

```python
# app/api/routes_health.py

from fastapi import APIRouter
from app.models.db import supabase
from app.services.g2b_client import g2b_client
from app.config import CLAUDE_API_KEY
import httpx

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    OPS-02: 애플리케이션 헬스체크.
    DB·외부 서비스 연결 상태를 포함하여 200/503 반환.
    """
    checks = {}

    # 1. Supabase PostgreSQL 연결
    try:
        result = supabase.table("users").select("id").limit(1).execute()
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)[:100]}

    # 2. Supabase Storage 연결
    try:
        supabase.storage.list_buckets()
        checks["storage"] = {"status": "ok"}
    except Exception as e:
        checks["storage"] = {"status": "error", "detail": str(e)[:100]}

    # 3. Claude API 연결 (간단한 ping)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01"},
                timeout=5,
            )
            checks["claude_api"] = {"status": "ok" if resp.status_code == 200 else "degraded"}
    except Exception as e:
        checks["claude_api"] = {"status": "error", "detail": str(e)[:100]}

    # 4. G2B API 연결
    try:
        await g2b_client.ping()
        checks["g2b_api"] = {"status": "ok"}
    except Exception:
        checks["g2b_api"] = {"status": "degraded", "detail": "G2B API 응답 없음 (비필수)"}

    # 종합 판정
    critical_ok = all(
        checks[k]["status"] == "ok"
        for k in ("database", "storage")  # 필수 서비스
    )

    return {
        "status": "healthy" if critical_ok else "unhealthy",
        "checks": checks,
        "version": "v3.0",
    }
    # 응답 코드: 200 (healthy) / 503 (unhealthy)
```

### 27-6. OPS-03: 구조화 로깅 설계

```python
# app/config.py 에 추가

import structlog

def configure_logging():
    """
    OPS-03: 구조화 로깅 (JSON 형식).
    모든 로그에 request_id, user_id, proposal_id 등 컨텍스트 자동 포함.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,      # 컨텍스트 변수 자동 병합
            structlog.processors.TimeStamper(fmt="iso"),   # ISO 타임스탬프
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),           # JSON 출력
        ],
        wrapper_class=structlog.make_filtering_bound_logger(10),  # DEBUG 이상
        logger_factory=structlog.PrintLoggerFactory(),
    )

# ── 로깅 미들웨어 ──
# app/main.py

from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import uuid

logger = structlog.get_logger()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """모든 요청에 request_id를 바인딩하고 요청/응답을 로깅."""

    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())[:8]
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        # 사용자 컨텍스트 (인증된 경우)
        user = getattr(request.state, "user", None)
        if user:
            structlog.contextvars.bind_contextvars(
                user_id=user.get("id"),
                team_id=user.get("team_id"),
            )

        logger.info("request_start")
        response = await call_next(request)
        logger.info("request_end", status_code=response.status_code)
        return response


# ── 로깅 표준 패턴 (각 서비스에서 사용) ──
# 예: app/services/claude_client.py
#
# logger = structlog.get_logger()
#
# async def claude_generate(prompt, ...):
#     logger.info("claude_api_call", step=step, input_tokens=len(prompt))
#     response = await client.messages.create(...)
#     logger.info("claude_api_response",
#         step=step,
#         input_tokens=response.usage.input_tokens,
#         output_tokens=response.usage.output_tokens,
#         cached_tokens=response.usage.cache_read_input_tokens,
#     )
#     return response
```

> **로깅 레벨 가이드**:
> | 레벨 | 용도 | 예시 |
> |------|------|------|
> | INFO | 정상 흐름 | API 요청/응답, AI 호출, 상태 전환 |
> | WARNING | 비정상이지만 계속 가능 | Heartbeat 지연, API 재시도, 세션 만료 |
> | ERROR | 실패 | Claude API 오류, DB 연결 실패, 파일 파싱 실패 |
> | DEBUG | 개발용 상세 | 프롬프트 내용, KB 검색 결과, 토큰 카운트 |

---

## 28. ★ 갭 분석 MEDIUM 항목 보완 설계 (v3.1)

> **아키텍처 결정 (v3.1)**: Pattern A(모놀리식 StateGraph) + LangGraph `Send()` 병렬처리 유지 확정.
> 근거: ① 구조화된 순차 프로세스(RFP→전략→작성→검증)에 적합, ② 토큰 비용 효율(~80K vs ~200K),
> ③ 단일 상태로 Compliance Matrix 추적 용이, ④ 소규모 팀 운영 부담 최소화.
>
> 갭 분석 MEDIUM 심각도 12건을 아래에서 설계 보완합니다.

### 28-1. OB-05a: 콘텐츠 라이브러리 초기 시딩 (DOCX 자동 추출)

> **목적**: 기존 제안서(DOCX 파일)에서 섹션별 콘텐츠를 자동 추출하여 콘텐츠 라이브러리에 시딩.

#### API 엔드포인트

```python
# app/api/routes_onboarding.py

@router.post("/api/onboarding/seed-content")
async def seed_content_from_docx(
    files: list[UploadFile] = File(...),
    user: dict = Depends(require_role("admin", "lead")),
):
    """
    OB-05a: DOCX 파일에서 섹션 자동 추출 → 콘텐츠 라이브러리 초기 시딩.
    - 최대 10개 파일, 파일당 50MB 이하
    - 제목 스타일(Heading 1~3) 기준으로 섹션 분리
    """
    results = []
    for file in files[:10]:
        validate_file(file, allowed_types=["docx"], max_size_mb=50)
        sections = await extract_sections_from_docx(file)
        seeded = []
        for section in sections:
            content_id = await insert_content_library(
                org_id=user["org_id"],
                type="proposal_section",
                title=section["heading"],
                body=section["body"],
                source_file=file.filename,
                tags=section.get("tags", []),
                status="draft",  # 관리자 검토 후 게시
            )
            # 임베딩 생성
            embedding = await embedding_service.generate(
                f"{section['heading']}\n{section['body'][:2000]}"
            )
            await update_content_embedding(content_id, embedding)
            seeded.append({"id": content_id, "title": section["heading"]})
        results.append({"file": file.filename, "sections_extracted": len(seeded), "items": seeded})
    return {"seeded_files": len(results), "details": results}
```

#### DOCX 섹션 추출 서비스

```python
# app/services/docx_extractor.py

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

async def extract_sections_from_docx(file: UploadFile) -> list[dict]:
    """
    DOCX 파일의 Heading 스타일을 기준으로 섹션 분리.
    - Heading 1~3: 새 섹션 시작
    - 본문 단락: 현재 섹션에 누적
    - 표: '[표: N행×M열]' 형태로 텍스트 변환 후 포함
    """
    doc = Document(await file.read())
    sections = []
    current_heading = None
    current_body = []

    for para in doc.paragraphs:
        style_name = para.style.name.lower()
        if style_name.startswith("heading"):
            # 이전 섹션 저장
            if current_heading and current_body:
                sections.append({
                    "heading": current_heading,
                    "body": "\n".join(current_body).strip(),
                    "tags": _infer_tags(current_heading),
                })
            current_heading = para.text.strip()
            current_body = []
        elif current_heading:
            if para.text.strip():
                current_body.append(para.text.strip())

    # 마지막 섹션
    if current_heading and current_body:
        sections.append({
            "heading": current_heading,
            "body": "\n".join(current_body).strip(),
            "tags": _infer_tags(current_heading),
        })

    return sections

def _infer_tags(heading: str) -> list[str]:
    """제목 키워드 기반 자동 태그 추론."""
    tag_keywords = {
        "사업이해": ["사업이해", "understanding"],
        "수행방법": ["수행방법", "methodology"],
        "수행체계": ["수행체계", "organization"],
        "일정": ["일정", "schedule"],
        "보안": ["보안", "security"],
        "인력": ["인력", "team"],
    }
    tags = []
    for tag, keywords in tag_keywords.items():
        if any(kw in heading for kw in keywords):
            tags.append(tag)
    return tags or ["general"]
```

### 28-2. CL-10: 오래된 콘텐츠 감지 (6개월 미갱신 알림)

> **목적**: 6개월 이상 미갱신된 콘텐츠를 감지하여 담당자에게 갱신 알림 발송.

```python
# app/services/scheduled_monitor.py 에 추가

async def detect_stale_content():
    """
    CL-10: 6개월 미갱신 콘텐츠 감지 → 팀장/작성자에게 알림.
    매주 월요일 09:00 실행.
    """
    from datetime import datetime, timezone, timedelta

    stale_threshold = datetime.now(timezone.utc) - timedelta(days=180)

    stale_items = await supabase.table("content_library") \
        .select("id, title, org_id, created_by, updated_at, type, tags") \
        .eq("status", "published") \
        .lt("updated_at", stale_threshold.isoformat()) \
        .execute()

    for item in stale_items.data:
        # 중복 알림 방지: 최근 30일 이내 동일 알림 확인
        recent_notification = await supabase.table("notifications") \
            .select("id") \
            .eq("type", "stale_content") \
            .eq("reference_id", item["id"]) \
            .gt("created_at", (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()) \
            .limit(1) \
            .execute()

        if recent_notification.data:
            continue

        # 작성자에게 알림
        await create_notification(
            user_id=item["created_by"],
            type="stale_content",
            reference_id=item["id"],
            title=f"📋 콘텐츠 갱신 필요: {item['title'][:40]}",
            body=f"마지막 수정일: {item['updated_at'][:10]}. 6개월 이상 경과되어 갱신을 권장합니다.",
        )

    logger.info("stale_content_check", stale_count=len(stale_items.data))

# 매주 월요일 09:00 실행
scheduler.add_job(detect_stale_content, "cron", day_of_week="mon", hour=9, minute=0)
```

### 28-3. CL-11: 콘텐츠 갭 분석

> **목적**: 최근 제안서에서 자주 요청되었으나 콘텐츠 라이브러리에 없는 영역을 자동 식별.

```python
# app/services/content_gap_analyzer.py

import structlog
from collections import Counter

logger = structlog.get_logger()

async def analyze_content_gaps(org_id: str) -> dict:
    """
    CL-11: 콘텐츠 갭 분석.
    최근 6개월 제안서에서 AI가 참조 시도했으나 KB에서 찾지 못한 영역 분석.

    데이터 소스:
    1. ai_task_logs에서 kb_miss_tags (KB 검색 실패 태그 기록)
    2. 자가진단 결과에서 grounding_ratio가 낮은 섹션
    3. 플레이스홀더 '[KB 데이터 필요:]' 빈도
    """
    from datetime import datetime, timezone, timedelta

    six_months_ago = (datetime.now(timezone.utc) - timedelta(days=180)).isoformat()

    # 1. KB miss 태그 수집
    miss_logs = await supabase.table("ai_task_logs") \
        .select("metadata") \
        .eq("org_id", org_id) \
        .gt("created_at", six_months_ago) \
        .not_.is_("metadata->>kb_miss_tags", "null") \
        .execute()

    miss_tags = []
    for log in miss_logs.data:
        tags = log.get("metadata", {}).get("kb_miss_tags", [])
        miss_tags.extend(tags)

    # 2. 플레이스홀더 빈도 분석
    placeholder_logs = await supabase.table("artifacts") \
        .select("content, section_id") \
        .eq("org_id", org_id) \
        .gt("created_at", six_months_ago) \
        .execute()

    placeholder_sections = []
    for artifact in placeholder_logs.data:
        if "[KB 데이터 필요:" in (artifact.get("content") or ""):
            placeholder_sections.append(artifact["section_id"])

    # 3. 갭 영역 집계 및 정렬
    gap_counter = Counter(miss_tags + placeholder_sections)
    top_gaps = gap_counter.most_common(20)

    # 4. 기존 콘텐츠와 대조하여 순수 갭만 추출
    existing_tags = await supabase.table("content_library") \
        .select("tags") \
        .eq("org_id", org_id) \
        .eq("status", "published") \
        .execute()

    existing_tag_set = set()
    for item in existing_tags.data:
        existing_tag_set.update(item.get("tags") or [])

    pure_gaps = [
        {"area": tag, "request_count": count, "has_content": tag in existing_tag_set}
        for tag, count in top_gaps
    ]

    logger.info("content_gap_analysis", org_id=org_id, gap_count=len(pure_gaps))

    return {
        "total_misses": len(miss_tags),
        "top_gaps": pure_gaps,
        "recommendation": [
            g["area"] for g in pure_gaps
            if not g["has_content"] and g["request_count"] >= 3
        ],
    }
```

#### API 엔드포인트

```python
# app/api/routes_kb.py 에 추가

@router.get("/api/kb/content-gaps")
async def get_content_gaps(user: dict = Depends(require_role("admin", "lead"))):
    """CL-11: 콘텐츠 갭 분석 결과 조회."""
    return await analyze_content_gaps(user["org_id"])
```

#### DB 스키마 확장

```sql
-- ai_task_logs에 KB miss 태그 기록 지원
-- metadata JSONB 필드에 kb_miss_tags: string[] 포함
-- (이미 JSONB이므로 스키마 변경 불필요, 노드에서 기록 로직만 추가)

-- 예: node 실행 시 KB 검색 실패 기록
-- metadata: { "kb_miss_tags": ["보안관제실적", "클라우드마이그레이션"], "search_query": "..." }
```

### 28-4. CMP-06: 경쟁 빈도 자동 집계

> **목적**: competitor_history에서 경쟁 빈도를 자동 집계하여 경쟁사 프로필에 반영.

```sql
-- PostgreSQL 뷰: 경쟁사별 경쟁 빈도 자동 집계
CREATE OR REPLACE VIEW competitor_frequency AS
SELECT
    c.id AS competitor_id,
    c.name AS competitor_name,
    c.org_id,
    COUNT(ch.id) AS total_encounters,
    COUNT(ch.id) FILTER (WHERE ch.result = 'won') AS won_against,
    COUNT(ch.id) FILTER (WHERE ch.result = 'lost') AS lost_against,
    ROUND(
        COUNT(ch.id) FILTER (WHERE ch.result = 'won')::NUMERIC /
        NULLIF(COUNT(ch.id), 0) * 100, 1
    ) AS win_rate_pct,
    MAX(ch.created_at) AS last_encounter,
    -- 최근 12개월 빈도
    COUNT(ch.id) FILTER (
        WHERE ch.created_at > NOW() - INTERVAL '12 months'
    ) AS encounters_last_12m,
    -- 자주 경쟁하는 분야 (최빈값)
    MODE() WITHIN GROUP (ORDER BY ch.industry) AS primary_industry
FROM competitors c
LEFT JOIN competitor_history ch ON c.id = ch.competitor_id
GROUP BY c.id, c.name, c.org_id;

-- RLS: 조직 기반 필터
ALTER VIEW competitor_frequency OWNER TO authenticated;
CREATE POLICY "org_filter" ON competitor_frequency
    FOR SELECT USING (org_id = auth.jwt()->>'org_id');

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_competitor_history_created
    ON competitor_history(competitor_id, created_at DESC);
```

#### API 엔드포인트

```python
# app/api/routes_kb.py 에 추가

@router.get("/api/kb/competitors/{id}/frequency")
async def get_competitor_frequency(
    id: str,
    user: dict = Depends(get_current_user),
):
    """CMP-06: 경쟁사 경쟁 빈도 조회."""
    result = await supabase.table("competitor_frequency") \
        .select("*") \
        .eq("competitor_id", id) \
        .single() \
        .execute()
    return result.data

@router.get("/api/kb/competitors/frequency-ranking")
async def get_competitor_frequency_ranking(
    user: dict = Depends(get_current_user),
    limit: int = Query(default=10, le=50),
):
    """CMP-06: 경쟁사 빈도 순위 (상위 N개)."""
    result = await supabase.table("competitor_frequency") \
        .select("*") \
        .eq("org_id", user["org_id"]) \
        .order("total_encounters", desc=True) \
        .limit(limit) \
        .execute()
    return result.data
```

### 28-5. LRN-08: 포지셔닝 판단 정확도 검증 통계

> **목적**: AI가 추천한 포지셔닝(aggressive/moderate/conservative) vs 실제 수주 결과를 비교하여 정확도 통계를 산출.

```sql
-- 포지셔닝 정확도 분석 뷰
CREATE OR REPLACE VIEW positioning_accuracy AS
SELECT
    p.org_id,
    p.ai_positioning AS recommended_positioning,
    p.final_positioning AS actual_positioning,
    p.status AS result,
    -- AI 추천과 실제 선택 일치 여부
    CASE WHEN p.ai_positioning = p.final_positioning THEN TRUE ELSE FALSE END AS ai_adopted,
    -- 결과별 집계 (수주/패찰)
    CASE WHEN p.status = 'won' THEN 1 ELSE 0 END AS is_won,
    CASE WHEN p.status = 'lost' THEN 1 ELSE 0 END AS is_lost,
    p.created_at
FROM proposals p
WHERE p.status IN ('won', 'lost')
  AND p.ai_positioning IS NOT NULL;

-- 요약 통계 뷰
CREATE OR REPLACE VIEW positioning_accuracy_summary AS
SELECT
    org_id,
    recommended_positioning,
    COUNT(*) AS total_cases,
    SUM(is_won) AS won_count,
    SUM(is_lost) AS lost_count,
    ROUND(SUM(is_won)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 1) AS win_rate_pct,
    -- AI 추천 채택률
    COUNT(*) FILTER (WHERE ai_adopted) AS adopted_count,
    ROUND(
        COUNT(*) FILTER (WHERE ai_adopted)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 1
    ) AS adoption_rate_pct,
    -- AI 추천 채택 시 수주율 vs 미채택 시 수주율
    ROUND(
        SUM(CASE WHEN ai_adopted AND is_won = 1 THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(COUNT(*) FILTER (WHERE ai_adopted), 0) * 100, 1
    ) AS adopted_win_rate_pct,
    ROUND(
        SUM(CASE WHEN NOT ai_adopted AND is_won = 1 THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(COUNT(*) FILTER (WHERE NOT ai_adopted), 0) * 100, 1
    ) AS non_adopted_win_rate_pct
FROM positioning_accuracy
GROUP BY org_id, recommended_positioning;
```

#### proposals 테이블 확장

```sql
-- AI 추천 포지셔닝 기록 컬럼 (기존 final_positioning과 별도)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS ai_positioning TEXT;
-- go_no_go 노드에서 AI가 추천한 포지셔닝을 여기에 저장
-- final_positioning은 Human 승인 후 확정된 포지셔닝
```

#### API 엔드포인트

```python
# app/api/routes_stats.py 에 추가

@router.get("/api/stats/positioning-accuracy")
async def get_positioning_accuracy(
    user: dict = Depends(require_role("admin", "lead")),
):
    """LRN-08: 포지셔닝 판단 정확도 통계."""
    result = await supabase.table("positioning_accuracy_summary") \
        .select("*") \
        .eq("org_id", user["org_id"]) \
        .execute()
    return {
        "summary": result.data,
        "insight": _generate_positioning_insight(result.data),
    }

def _generate_positioning_insight(data: list[dict]) -> str:
    """포지셔닝 정확도 인사이트 생성."""
    if not data:
        return "아직 충분한 데이터가 없습니다. 최소 10건의 수주/패찰 결과가 필요합니다."

    best = max(data, key=lambda x: x.get("win_rate_pct") or 0)
    return (
        f"가장 높은 수주율: {best['recommended_positioning']} "
        f"({best['win_rate_pct']}%, {best['total_cases']}건). "
        f"AI 추천 채택 시 수주율: {best.get('adopted_win_rate_pct', 'N/A')}%."
    )
```

### 28-6. KBS-07: 검색 이력 분석

> **목적**: KB 통합 검색 이력을 저장하고 자주 검색하는 패턴을 분석하여 콘텐츠 갭 발견 및 검색 개선에 활용.

#### DB 스키마

```sql
CREATE TABLE search_history (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID REFERENCES organizations(id) NOT NULL,
    user_id     UUID REFERENCES users(id) NOT NULL,
    query       TEXT NOT NULL,
    query_type  TEXT NOT NULL,             -- 'keyword' | 'semantic' | 'hybrid'
    filters     JSONB DEFAULT '{}',        -- 적용된 필터 (kb_types, tags, date_range 등)
    result_count INT DEFAULT 0,
    clicked_ids UUID[] DEFAULT '{}',       -- 사용자가 클릭한 결과 ID 목록
    source      TEXT DEFAULT 'manual',     -- 'manual' (사용자 검색) | 'ai_auto' (AI 자동 참조)
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_search_history_org ON search_history(org_id, created_at DESC);
CREATE INDEX idx_search_history_query ON search_history USING gin(to_tsvector('simple', query));

-- RLS
ALTER TABLE search_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_members" ON search_history
    FOR ALL USING (org_id = auth.jwt()->>'org_id');
```

#### 검색 패턴 분석 서비스

```python
# app/services/search_analytics.py

async def get_search_patterns(org_id: str, days: int = 90) -> dict:
    """
    KBS-07: 검색 패턴 분석.
    - 인기 검색어 Top 20
    - 결과 0건 검색어 (콘텐츠 갭 후보)
    - 시간대별 검색 빈도
    """
    from datetime import datetime, timezone, timedelta

    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    history = await supabase.table("search_history") \
        .select("query, result_count, source, created_at") \
        .eq("org_id", org_id) \
        .gt("created_at", since) \
        .execute()

    queries = [h["query"] for h in history.data]
    zero_result_queries = [h["query"] for h in history.data if h["result_count"] == 0]

    from collections import Counter
    return {
        "total_searches": len(history.data),
        "unique_queries": len(set(queries)),
        "top_queries": Counter(queries).most_common(20),
        "zero_result_queries": Counter(zero_result_queries).most_common(10),
        "ai_auto_ratio": sum(1 for h in history.data if h["source"] == "ai_auto") / max(len(history.data), 1),
    }
```

#### 통합 검색 함수에 이력 기록 추가

```python
# app/services/knowledge_search.py 수정 (기존 unified_search에 추가)

async def unified_search(query: str, user: dict, **filters) -> dict:
    """기존 통합 검색 + KBS-07 이력 기록."""
    results = await _do_search(query, user["org_id"], **filters)

    # 검색 이력 비동기 기록 (검색 성능에 영향 없도록)
    asyncio.create_task(
        insert_search_history(
            org_id=user["org_id"],
            user_id=user["id"],
            query=query,
            query_type=filters.get("search_type", "hybrid"),
            filters=filters,
            result_count=len(results.get("items", [])),
            source="manual",
        )
    )

    return results
```

### 28-7. COST-05~07: 월간 예산 상한 / 경고 / AI 정지

> **목적**: 조직별 월간 API 비용 예산을 설정하고, 임계값 초과 시 경고 및 AI 호출 자동 정지.

#### DB 스키마

```sql
-- 조직별 비용 예산 설정
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS monthly_budget_usd NUMERIC(10,2);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS budget_alert_threshold NUMERIC(3,2) DEFAULT 0.80;
-- budget_alert_threshold: 예산 대비 경고 비율 (기본 80%)

-- 월간 비용 집계 뷰
CREATE OR REPLACE VIEW monthly_cost_summary AS
SELECT
    org_id,
    DATE_TRUNC('month', created_at) AS month,
    SUM(input_tokens) AS total_input_tokens,
    SUM(output_tokens) AS total_output_tokens,
    SUM(cached_tokens) AS total_cached_tokens,
    SUM(cost_usd) AS total_cost_usd
FROM token_usage
GROUP BY org_id, DATE_TRUNC('month', created_at);
```

#### 비용 관리 서비스

```python
# app/services/budget_manager.py

import structlog
from decimal import Decimal

logger = structlog.get_logger()

class BudgetManager:
    """COST-05~07: 월간 API 비용 예산 관리."""

    async def check_budget(self, org_id: str) -> dict:
        """
        현재 월 비용을 예산과 비교.
        Returns: { "allowed": bool, "usage_pct": float, "status": str }
        """
        org = await get_organization(org_id)
        budget = org.get("monthly_budget_usd")

        if not budget:
            return {"allowed": True, "usage_pct": 0, "status": "no_budget_set"}

        current_cost = await self._get_current_month_cost(org_id)
        usage_pct = float(current_cost / Decimal(str(budget)) * 100) if budget > 0 else 0
        threshold = float(org.get("budget_alert_threshold", 0.80)) * 100

        status = "normal"
        if usage_pct >= 100:
            status = "exceeded"
        elif usage_pct >= threshold:
            status = "warning"

        return {
            "allowed": usage_pct < 100,
            "usage_pct": round(usage_pct, 1),
            "status": status,
            "current_cost_usd": float(current_cost),
            "budget_usd": float(budget),
        }

    async def enforce_budget(self, org_id: str) -> bool:
        """
        COST-07: AI 호출 전 예산 확인. 초과 시 False 반환.
        claude_client.py에서 매 호출 전 실행.
        """
        result = await self.check_budget(org_id)

        if result["status"] == "warning":
            # COST-06: 경고 알림 (중복 방지: 하루 1회)
            await self._send_budget_alert_if_needed(org_id, result)

        if result["status"] == "exceeded":
            # COST-07: AI 호출 정지
            logger.warning("budget_exceeded", org_id=org_id, **result)
            await self._send_budget_exceeded_alert(org_id, result)
            return False

        return True

    async def _get_current_month_cost(self, org_id: str) -> Decimal:
        from datetime import datetime, timezone
        first_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0)
        result = await supabase.table("token_usage") \
            .select("cost_usd") \
            .eq("org_id", org_id) \
            .gte("created_at", first_of_month.isoformat()) \
            .execute()
        return sum(Decimal(str(r["cost_usd"])) for r in result.data)

    async def _send_budget_alert_if_needed(self, org_id: str, result: dict):
        """하루 1회 중복 방지 경고."""
        from datetime import datetime, timezone, timedelta
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        existing = await supabase.table("notifications") \
            .select("id") \
            .eq("type", "budget_warning") \
            .eq("org_id", org_id) \
            .gte("created_at", today_start.isoformat()) \
            .limit(1) \
            .execute()
        if not existing.data:
            admins = await get_org_admins(org_id)
            for admin in admins:
                await create_notification(
                    user_id=admin["id"],
                    type="budget_warning",
                    title=f"⚠️ API 비용 예산 {result['usage_pct']}% 도달",
                    body=f"현재 ${result['current_cost_usd']:.2f} / 예산 ${result['budget_usd']:.2f}",
                    org_id=org_id,
                )

    async def _send_budget_exceeded_alert(self, org_id: str, result: dict):
        """예산 초과 긴급 알림."""
        admins = await get_org_admins(org_id)
        for admin in admins:
            await create_notification(
                user_id=admin["id"],
                type="budget_exceeded",
                title="🚨 API 비용 예산 초과 — AI 호출 정지됨",
                body=f"현재 ${result['current_cost_usd']:.2f} / 예산 ${result['budget_usd']:.2f}. 관리자 설정에서 예산을 조정하거나 다음 달까지 대기하세요.",
                org_id=org_id,
            )

budget_manager = BudgetManager()
```

#### claude_client.py 통합

```python
# app/services/claude_client.py 수정 (기존 generate 함수에 예산 체크 추가)

async def claude_generate(prompt: str, org_id: str, **kwargs):
    """Claude API 호출 (COST-05~07 예산 체크 포함)."""
    # 예산 확인
    if not await budget_manager.enforce_budget(org_id):
        raise BudgetExceededError(
            "월간 API 비용 예산을 초과했습니다. 관리자에게 문의하세요."
        )

    response = await client.messages.create(...)
    # ... (기존 로직)
```

### 28-8. OPS-04~08: Claude API 장애 대응 및 운영 복원력

> **목적**: Claude API 장애 시 재시도·폴백·그레이스풀 디그레이데이션 전략과 운영 메트릭 수집.

#### 재시도 및 Circuit Breaker

```python
# app/services/api_resilience.py

import structlog
import asyncio
from datetime import datetime, timezone, timedelta
from enum import Enum

logger = structlog.get_logger()

class CircuitState(Enum):
    CLOSED = "closed"       # 정상
    OPEN = "open"           # 차단 (장애)
    HALF_OPEN = "half_open" # 시험 재개

class ClaudeCircuitBreaker:
    """
    OPS-04~05: Claude API Circuit Breaker.
    연속 실패 시 호출 차단, 일정 시간 후 시험 재개.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,     # 초
        half_open_max_calls: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0

    async def call(self, func, *args, **kwargs):
        """Circuit Breaker를 통한 API 호출."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info("circuit_breaker_half_open")
            else:
                raise ServiceUnavailableError("Claude API 일시적 장애. 잠시 후 재시도하세요.")

        try:
            result = await self._retry_with_backoff(func, *args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    async def _retry_with_backoff(self, func, *args, max_retries=3, **kwargs):
        """OPS-04: 지수 백오프 재시도."""
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                if attempt == max_retries - 1:
                    raise
                wait = min(2 ** attempt * 1.0, 30)  # 1s, 2s, 4s... max 30s
                logger.warning("claude_api_retry",
                    attempt=attempt + 1,
                    wait_seconds=wait,
                    error=str(e)[:100],
                )
                await asyncio.sleep(wait)

    def _on_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
                logger.info("circuit_breaker_closed")

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error("circuit_breaker_open", failure_count=self.failure_count)

    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return True
        elapsed = (datetime.now(timezone.utc) - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

circuit_breaker = ClaudeCircuitBreaker()
```

#### Graceful Degradation (OPS-06)

```python
# app/services/degradation.py

DEGRADATION_RESPONSES = {
    "rfp_analyze": "⚠️ AI 분석이 일시적으로 불가합니다. RFP 문서는 업로드되었으며, AI 복구 후 자동으로 분석이 재개됩니다.",
    "strategy_generate": "⚠️ AI 전략 생성이 일시적으로 불가합니다. 수동으로 전략을 입력하거나, AI 복구를 기다려주세요.",
    "proposal_section": "⚠️ AI 섹션 생성이 일시적으로 불가합니다. 직접 작성 모드로 전환합니다.",
    "self_review": "⚠️ AI 자가진단이 일시적으로 불가합니다. 수동 검토를 진행해주세요.",
}

async def get_degradation_response(step: str) -> dict | None:
    """
    OPS-06: AI 장애 시 단계별 폴백 응답.
    None 반환 시 정상 처리, dict 반환 시 폴백 모드.
    """
    if circuit_breaker.state == CircuitState.OPEN:
        return {
            "status": "degraded",
            "message": DEGRADATION_RESPONSES.get(step, "⚠️ AI 기능이 일시적으로 불가합니다."),
            "manual_mode_available": True,
        }
    return None
```

#### 운영 메트릭 수집 (OPS-07~08)

```python
# app/services/metrics_collector.py

import structlog
from datetime import datetime, timezone

logger = structlog.get_logger()

class MetricsCollector:
    """OPS-07~08: 운영 메트릭 수집 및 에러 모니터링."""

    async def record_api_call(self, step: str, duration_ms: float, success: bool, tokens: dict):
        """API 호출 메트릭 기록."""
        await supabase.table("api_metrics").insert({
            "step": step,
            "duration_ms": duration_ms,
            "success": success,
            "input_tokens": tokens.get("input", 0),
            "output_tokens": tokens.get("output", 0),
            "cached_tokens": tokens.get("cached", 0),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

    async def record_error(self, step: str, error_type: str, detail: str):
        """에러 이벤트 기록."""
        await supabase.table("error_events").insert({
            "step": step,
            "error_type": error_type,
            "detail": detail[:500],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        logger.error("api_error", step=step, error_type=error_type)

metrics = MetricsCollector()
```

#### 메트릭 DB 스키마

```sql
CREATE TABLE api_metrics (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    step        TEXT NOT NULL,
    duration_ms NUMERIC(10,2),
    success     BOOLEAN NOT NULL DEFAULT TRUE,
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    cached_tokens INT DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE error_events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    step        TEXT NOT NULL,
    error_type  TEXT NOT NULL,
    detail      TEXT,
    resolved    BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_api_metrics_step ON api_metrics(step, created_at DESC);
CREATE INDEX idx_error_events_unresolved ON error_events(resolved, created_at DESC) WHERE NOT resolved;
```

#### 메트릭 대시보드 API

```python
# app/api/routes_stats.py 에 추가

@router.get("/api/stats/api-health")
async def get_api_health_stats(
    user: dict = Depends(require_role("admin")),
    hours: int = Query(default=24, le=168),
):
    """OPS-07: API 상태 메트릭 대시보드."""
    from datetime import datetime, timezone, timedelta
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    metrics_data = await supabase.table("api_metrics") \
        .select("step, duration_ms, success") \
        .gte("created_at", since) \
        .execute()

    errors = await supabase.table("error_events") \
        .select("step, error_type, created_at") \
        .gte("created_at", since) \
        .execute()

    return {
        "period_hours": hours,
        "total_calls": len(metrics_data.data),
        "success_rate": sum(1 for m in metrics_data.data if m["success"]) / max(len(metrics_data.data), 1) * 100,
        "avg_duration_ms": sum(m["duration_ms"] for m in metrics_data.data) / max(len(metrics_data.data), 1),
        "error_count": len(errors.data),
        "circuit_breaker_state": circuit_breaker.state.value,
    }
```

### 28-9. RET-01~05: 데이터 보존 및 삭제 정책

> **목적**: 데이터 유형별 보존 기간 정의, 자동 아카이브, soft delete, 물리 삭제 스케줄.

#### 보존 정책 정의

```python
# app/config.py 에 추가

DATA_RETENTION_POLICIES = {
    # RET-01: 제안 프로젝트 데이터
    "proposals": {
        "active_retention_years": 5,       # 활성 보존 5년
        "archive_after_years": 3,          # 3년 후 아카이브
        "hard_delete_after_years": 7,      # 7년 후 물리 삭제
    },
    # RET-02: 산출물 (제안서, PPT 등)
    "artifacts": {
        "active_retention_years": 5,
        "archive_after_years": 3,
        "hard_delete_after_years": 7,
    },
    # RET-03: 감사 로그
    "audit_logs": {
        "active_retention_years": 5,
        "archive_after_years": 5,
        "hard_delete_after_years": 10,     # 법적 보존 기간 고려
    },
    # RET-04: AI 작업 로그 / 토큰 사용 로그
    "ai_task_logs": {
        "active_retention_years": 3,
        "archive_after_years": 1,
        "hard_delete_after_years": 5,
    },
    "token_usage": {
        "active_retention_years": 3,
        "archive_after_years": 1,
        "hard_delete_after_years": 5,
    },
    # RET-05: 알림
    "notifications": {
        "active_retention_years": 1,
        "archive_after_years": 0.5,        # 6개월 후 아카이브
        "hard_delete_after_years": 2,
    },
}
```

#### 자동 아카이브 / 삭제 스케줄러

```python
# app/services/data_retention.py

import structlog
from datetime import datetime, timezone, timedelta
from app.config import DATA_RETENTION_POLICIES

logger = structlog.get_logger()

async def run_retention_policies():
    """
    RET-01~05: 데이터 보존 정책 실행.
    매월 1일 02:00 실행.

    단계:
    1. archive_after 경과 데이터 → archived=true 마킹 (soft archive)
    2. hard_delete_after 경과 + archived 데이터 → 물리 삭제
    3. Supabase Storage의 연관 파일도 함께 처리
    """
    for table_name, policy in DATA_RETENTION_POLICIES.items():
        archive_threshold = datetime.now(timezone.utc) - timedelta(
            days=policy["archive_after_years"] * 365
        )
        delete_threshold = datetime.now(timezone.utc) - timedelta(
            days=policy["hard_delete_after_years"] * 365
        )

        # 1. 아카이브 (soft)
        archive_result = await supabase.table(table_name) \
            .update({"archived": True}) \
            .eq("archived", False) \
            .lt("created_at", archive_threshold.isoformat()) \
            .execute()

        archived_count = len(archive_result.data) if archive_result.data else 0

        # 2. 물리 삭제 (아카이브 후 보존 기간 초과)
        delete_result = await supabase.table(table_name) \
            .delete() \
            .eq("archived", True) \
            .lt("created_at", delete_threshold.isoformat()) \
            .execute()

        deleted_count = len(delete_result.data) if delete_result.data else 0

        if archived_count > 0 or deleted_count > 0:
            logger.info("retention_policy_executed",
                table=table_name,
                archived=archived_count,
                deleted=deleted_count,
            )

            await insert_audit_log(
                action="retention_policy",
                resource_type=table_name,
                detail={
                    "archived": archived_count,
                    "deleted": deleted_count,
                    "archive_threshold": archive_threshold.isoformat(),
                    "delete_threshold": delete_threshold.isoformat(),
                },
            )

# 매월 1일 02:00 실행
scheduler.add_job(run_retention_policies, "cron", day=1, hour=2, minute=0)
```

#### DB 스키마 확장

```sql
-- 아카이브 지원 컬럼 추가 (대상 테이블별)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;
ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;
ALTER TABLE ai_task_logs ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;
ALTER TABLE token_usage ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;

-- 아카이브 데이터 파티셔닝 인덱스
CREATE INDEX idx_proposals_archived ON proposals(archived, created_at) WHERE archived = TRUE;
CREATE INDEX idx_audit_logs_archived ON audit_logs(archived, created_at) WHERE archived = TRUE;
```

### 28-10. NFR-18~20: 브라우저 호환성 / WCAG 접근성 / 반응형 설계

> **목적**: 프론트엔드 비기능 요구사항 — 지원 브라우저, 접근성 표준, 반응형 설계 가이드라인.

#### NFR-18: 브라우저 호환성

```
지원 브라우저 (데스크톱 우선):
- Chrome 120+ (주 대상)
- Microsoft Edge 120+ (Chromium 기반)
- Firefox 120+ (호환성 테스트)
- Safari 17+ (macOS 사용자 대응)

비지원:
- Internet Explorer (전체)
- 모바일 브라우저 (Phase 2 대응 예정)

구현 가이드:
- Next.js browserslist 설정: "last 2 Chrome versions, last 2 Edge versions, last 2 Firefox versions, last 2 Safari versions"
- Polyfill: core-js (필요 시 next.config.js에서 자동 적용)
- CSS: CSS Grid + Flexbox (IE 호환 불필요)
- JS: ES2020+ 문법 사용 가능 (Optional Chaining, Nullish Coalescing 등)
```

#### NFR-19: WCAG 2.1 Level AA 접근성

```
접근성 요구사항 (WCAG 2.1 Level AA):

1. 시맨틱 HTML:
   - 모든 페이지에 <main>, <nav>, <header>, <footer> 랜드마크 사용
   - 제목 계층 구조 준수 (h1 → h2 → h3, 건너뛰기 금지)
   - 버튼/링크 구분: 네비게이션은 <a>, 동작은 <button>

2. 키보드 내비게이션:
   - 모든 인터랙티브 요소 Tab 접근 가능
   - 포커스 순서 논리적 (tabindex 남용 금지)
   - 모달/드롭다운: Escape 키로 닫기, 포커스 트랩
   - Skip to main content 링크 제공

3. ARIA:
   - 커스텀 컴포넌트에 적절한 role, aria-label, aria-describedby
   - 동적 콘텐츠 변경 시 aria-live="polite" (AI 진행 상태 등)
   - 로딩 상태: aria-busy="true"

4. 색상/대비:
   - 텍스트 대비 비율: 4.5:1 이상 (일반), 3:1 이상 (큰 텍스트)
   - 색상만으로 정보 전달 금지 (아이콘/텍스트 병행)
   - 상태 표시: 색상 + 아이콘 + 텍스트 레이블

5. 폼 접근성:
   - 모든 입력 필드에 연결된 <label>
   - 오류 메시지: aria-invalid + aria-describedby로 연결
   - 필수 필드: aria-required="true"

프론트엔드 도구:
- eslint-plugin-jsx-a11y (빌드 시 접근성 린트)
- @axe-core/react (개발 모드 런타임 감사)
```

#### NFR-20: 반응형 설계

```
반응형 브레이크포인트 (데스크톱 우선):

| 이름 | 범위 | 대상 |
|------|------|------|
| desktop-xl | ≥1440px | 대형 모니터 (기본 레이아웃) |
| desktop | 1024–1439px | 일반 데스크톱/노트북 |
| tablet | 768–1023px | 태블릿 / 좁은 브라우저 |
| mobile | <768px | 참고용 (Phase 2) |

레이아웃 전략:
- Sidebar (KB 패널, 프로젝트 목록): desktop-xl에서 고정, desktop에서 접이식, tablet에서 오버레이
- 워크플로 타임라인: 가로 스크롤 (desktop), 세로 스택 (tablet)
- 리뷰 패널 (diff 뷰): 나란히 비교 (desktop-xl), 위/아래 (desktop 이하)
- 대시보드 카드: 3열 (desktop-xl), 2열 (desktop), 1열 (tablet)

CSS 구현:
- Tailwind CSS 반응형 유틸리티: sm:, md:, lg:, xl:
- Container queries (컴포넌트 단위 반응형, @container)
- 최소 터치 영역: 44px × 44px (WCAG 2.5.5)
```

### 28-11. TRS-06: 인라인 출처 클릭 이동 프론트엔드 UI

> **목적**: AI 산출물의 인라인 출처 마커(예: `[역량DB-PRJ-023]`)를 클릭하면 해당 KB 항목으로 이동하는 프론트엔드 컴포넌트.

#### 출처 마커 파서 컴포넌트

```typescript
// frontend/components/SourceMarker.tsx

interface SourceMarkerProps {
  content: string;
  onSourceClick: (sourceRef: SourceReference) => void;
}

interface SourceReference {
  type: 'capability' | 'content' | 'client' | 'competitor' | 'lesson' | 'rfp' | 'g2b' | 'estimate';
  id: string;
  label: string;
}

/**
 * TRS-06: 인라인 출처 마커를 파싱하여 클릭 가능한 링크로 변환.
 *
 * 지원 마커 패턴:
 * - [역량DB-PRJ-023] → capabilities 테이블
 * - [콘텐츠-SEC-045] → content_library 테이블
 * - [발주처-CLI-012] → client_intel 테이블
 * - [경쟁사-CMP-007] → competitors 테이블
 * - [교훈-LSN-003] → lessons_learned 테이블
 * - [RFP-p12] → RFP 원문 페이지
 * - [G2B-공고번호] → G2B 공고 상세
 * - [추정] → 추정 데이터 (클릭 불가, 경고 스타일)
 */
const SOURCE_PATTERN = /\[(역량DB|콘텐츠|발주처|경쟁사|교훈|RFP|G2B|추정|일반지식)-([^\]]+)\]/g;

const SOURCE_TYPE_MAP: Record<string, SourceReference['type']> = {
  '역량DB': 'capability',
  '콘텐츠': 'content',
  '발주처': 'client',
  '경쟁사': 'competitor',
  '교훈': 'lesson',
  'RFP': 'rfp',
  'G2B': 'g2b',
  '추정': 'estimate',
};

export function SourceMarker({ content, onSourceClick }: SourceMarkerProps) {
  const parts = parseSourceMarkers(content);

  return (
    <span>
      {parts.map((part, i) =>
        part.isSource ? (
          <button
            key={i}
            className={`inline-source-marker ${part.ref!.type === 'estimate' ? 'source-warning' : 'source-link'}`}
            onClick={() => part.ref!.type !== 'estimate' && onSourceClick(part.ref!)}
            title={part.ref!.type === 'estimate' ? '추정 데이터 (KB 출처 없음)' : `${part.ref!.label} 원본 보기`}
            aria-label={`출처: ${part.ref!.label}`}
          >
            {part.text}
          </button>
        ) : (
          <span key={i}>{part.text}</span>
        )
      )}
    </span>
  );
}

function parseSourceMarkers(content: string) {
  const parts: Array<{ text: string; isSource: boolean; ref?: SourceReference }> = [];
  let lastIndex = 0;

  for (const match of content.matchAll(SOURCE_PATTERN)) {
    if (match.index! > lastIndex) {
      parts.push({ text: content.slice(lastIndex, match.index!), isSource: false });
    }
    const typeName = match[1];
    const id = match[2];
    parts.push({
      text: match[0],
      isSource: true,
      ref: {
        type: SOURCE_TYPE_MAP[typeName] || 'content',
        id,
        label: match[0],
      },
    });
    lastIndex = match.index! + match[0].length;
  }

  if (lastIndex < content.length) {
    parts.push({ text: content.slice(lastIndex), isSource: false });
  }

  return parts;
}
```

#### CSS 스타일

```css
/* frontend/styles/source-markers.css */

.inline-source-marker {
  display: inline;
  font-size: 0.85em;
  padding: 1px 4px;
  border-radius: 3px;
  cursor: pointer;
  font-family: inherit;
  border: none;
  background: none;
}

.source-link {
  color: #2563eb;
  background-color: #eff6ff;
  border-bottom: 1px dashed #2563eb;
}

.source-link:hover {
  background-color: #dbeafe;
  text-decoration: underline;
}

.source-warning {
  color: #d97706;
  background-color: #fffbeb;
  border-bottom: 1px dashed #d97706;
  cursor: default;
}
```

#### KB 항목 상세 패널 (사이드시트)

```typescript
// frontend/components/SourceDetailPanel.tsx

interface SourceDetailPanelProps {
  sourceRef: SourceReference | null;
  onClose: () => void;
}

/**
 * TRS-06: 출처 클릭 시 원본 데이터를 사이드 패널로 표시.
 * 종류별 API 호출하여 원본 데이터 로드.
 */
export function SourceDetailPanel({ sourceRef, onClose }: SourceDetailPanelProps) {
  const { data, isLoading } = useSourceDetail(sourceRef);

  if (!sourceRef) return null;

  const apiEndpoints: Record<string, string> = {
    capability: '/api/kb/capabilities',
    content: '/api/kb/content',
    client: '/api/kb/clients',
    competitor: '/api/kb/competitors',
    lesson: '/api/kb/lessons',
    rfp: '/api/proposals', // RFP 원문은 프로젝트 컨텍스트
    g2b: '/api/g2b/notices',
  };

  return (
    <aside className="source-detail-panel" role="complementary" aria-label="출처 상세">
      <header>
        <h3>출처 상세: {sourceRef.label}</h3>
        <button onClick={onClose} aria-label="닫기">✕</button>
      </header>
      {isLoading ? (
        <div aria-busy="true">로딩 중...</div>
      ) : (
        <div className="source-content">
          {/* 종류별 상세 렌더링 */}
          <SourceContent type={sourceRef.type} data={data} />
        </div>
      )}
    </aside>
  );
}
```

### 28-12. TRS-12: 불확실성 명시 후처리 검증 로직

> **목적**: AI 출력에서 확신도 표기(높음/보통/낮음)가 실제로 부착되었는지 후처리로 검증.

```python
# app/services/uncertainty_validator.py

import re
import structlog

logger = structlog.get_logger()

# 확신도 태그 패턴
CONFIDENCE_PATTERN = re.compile(
    r'\[(확신도[:\s]*(높음|보통|낮음))\]'
    r'|'
    r'\[confidence[:\s]*(high|medium|low)\]',
    re.IGNORECASE,
)

# 불확실성 표현 (확신도 태그가 필요한 문맥)
UNCERTAINTY_INDICATORS = [
    r'추정(됩니다|으로|치)',
    r'예상(됩니다|으로)',
    r'대략\s',
    r'약\s+\d+',
    r'~\d+',
    r'정확하지\s*않',
    r'확인\s*필요',
    r'검증\s*필요',
    r'\[추정\]',
    r'\[일반지식\]',
]
UNCERTAINTY_REGEX = re.compile('|'.join(UNCERTAINTY_INDICATORS))


def validate_uncertainty_markers(content: str, section_id: str = "") -> dict:
    """
    TRS-12: 불확실성 표기 검증.

    검사 항목:
    1. 추정/예상 표현이 있는 단락에 확신도 태그가 있는지
    2. [추정] 또는 [일반지식] 태그가 있으면 확신도 '낮음' 또는 '보통'인지
    3. 수치 데이터에 출처 태그 없이 확신도 태그도 없는 경우 경고
    """
    paragraphs = content.split('\n\n')
    issues = []
    stats = {
        "total_paragraphs": len(paragraphs),
        "uncertain_paragraphs": 0,
        "properly_tagged": 0,
        "missing_tags": 0,
    }

    for i, para in enumerate(paragraphs):
        has_uncertainty = bool(UNCERTAINTY_REGEX.search(para))
        has_confidence_tag = bool(CONFIDENCE_PATTERN.search(para))

        if has_uncertainty:
            stats["uncertain_paragraphs"] += 1

            if has_confidence_tag:
                stats["properly_tagged"] += 1

                # [추정]/[일반지식]이 있으면 확신도 '높음'은 부적절
                if ('[추정]' in para or '[일반지식]' in para):
                    confidence_match = CONFIDENCE_PATTERN.search(para)
                    if confidence_match:
                        level = (confidence_match.group(2) or confidence_match.group(3) or "").lower()
                        if level in ('높음', 'high'):
                            issues.append({
                                "paragraph_index": i,
                                "type": "confidence_mismatch",
                                "detail": "추정/일반지식 데이터에 확신도 '높음'은 부적절합니다.",
                                "suggestion": "확신도를 '보통' 또는 '낮음'으로 변경하세요.",
                            })
            else:
                stats["missing_tags"] += 1
                issues.append({
                    "paragraph_index": i,
                    "type": "missing_confidence",
                    "detail": f"불확실한 표현이 포함된 단락에 확신도 태그가 없습니다.",
                    "excerpt": para[:100],
                    "suggestion": "[확신도: 보통] 또는 [확신도: 낮음] 태그를 추가하세요.",
                })

    compliance_rate = (
        stats["properly_tagged"] / max(stats["uncertain_paragraphs"], 1) * 100
    )

    result = {
        "section_id": section_id,
        "stats": stats,
        "compliance_rate": round(compliance_rate, 1),
        "issues": issues,
        "passed": len(issues) == 0,
    }

    if issues:
        logger.warning("uncertainty_validation_issues",
            section_id=section_id,
            issue_count=len(issues),
            compliance_rate=compliance_rate,
        )

    return result
```

#### 자가진단 통합

```python
# app/graph/nodes/self_review.py 에 통합 (기존 4축 진단에 추가)

async def _run_trustworthiness_checks(state: ProposalState) -> dict:
    """
    기존 근거 신뢰성 검사 (16-3-3)에 TRS-12 불확실성 검증 추가.
    """
    from app.services.uncertainty_validator import validate_uncertainty_markers

    sections = state.get("proposal_sections", {})
    all_issues = []

    for section_id, content in sections.items():
        result = validate_uncertainty_markers(content, section_id)
        if not result["passed"]:
            all_issues.extend(result["issues"])

    return {
        "uncertainty_check": {
            "total_issues": len(all_issues),
            "issues": all_issues[:20],  # 상위 20건만
            "needs_rework": len(all_issues) > 5,  # 5건 초과 시 재작업 권고
        }
    }
```

---

> **v3.1 MEDIUM 보완 요약**: 12건 모두 설계 반영 완료.
> - 콘텐츠 라이프사이클: OB-05a (시딩), CL-10 (미갱신 알림), CL-11 (갭 분석)
> - KB 분석: CMP-06 (경쟁 빈도 뷰), LRN-08 (포지셔닝 정확도 뷰), KBS-07 (검색 이력)
> - 운영 안정성: COST-05~07 (예산 관리), OPS-04~08 (복원력+메트릭), RET-01~05 (데이터 보존)
> - 프론트엔드: NFR-18~20 (브라우저/접근성/반응형), TRS-06 (출처 클릭 UI), TRS-12 (불확실성 검증)

---

## 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2)

> **배경**: ProposalForge 13개 에이전트 상세 프롬프트 설계서를 Pattern A(모놀리식 StateGraph) 구조 내에서 흡수.
> ProposalForge는 Pattern B(오케스트레이터+전문에이전트) 기반이므로 아키텍처는 변경하지 않고, **프롬프트 내용**만 노드 레벨로 통합.
> 7개 리서치 서브에이전트 → 1개 `research_gather` 노드로 통합하되, **획일적 7차원 템플릿이 아닌 RFP-적응형**으로 설계 (사업 범주에 따라 조사 차원 자체를 동적 도출).

### 29-1. 그래프 플로우 변경 요약

**v3.1 → v3.2 엣지 변경**:
```
[변경 전] review_rfp → go_no_go → review_gng → ...
[변경 후] review_rfp → research_gather → go_no_go → review_gng → ...

[변경 전] ... → review_proposal → ppt_fan_out_gate → ...
[변경 후] ... → review_proposal → presentation_strategy → ppt_fan_out_gate → ...
```

- `research_gather`는 별도 Human review 없이 자동 통과 (리서치 결과는 Go/No-Go에서 함께 검토)
- `presentation_strategy`는 `eval_method == 'document_only'`이면 건너뛰기 (서류심사)

### 29-2. 신규 노드: `research_gather`

**위치**: `review_rfp` approved → `research_gather` → `go_no_go`
**역할**: RFP 분석 결과를 기반으로 **해당 사업에 맞는 조사 차원을 동적으로 설계**하고, Go/No-Go 의사결정과 제안전략 수립에 필요한 정보를 수집
**근거**: ProposalForge #5(리서치 디렉터) + #6(7개 서브에이전트) 통합
**토큰 예산**: 15,000 (입력) / 8,000 (출력)
**리뷰**: 없음 (go_no_go에서 함께 검토)

#### 핵심 설계 원칙: RFP-적응형 리서치

> **획일적 템플릿(시장동향·기술동향·규제동향 등)을 일률 적용하지 않는다.**
> RFP의 사업 범주와 내용에 따라 조사 차원 자체가 달라져야 한다.
>
> | RFP 사업 유형 | 필요한 조사 차원 (예시) |
> |---|---|
> | 성과조사분석 용역 | 대상 사업의 기집행 현황, 기존 성과지표 체계, 평가 방법론 비교, 유사 성과분석 사례, 이해관계자 맵 |
> | 정책연구 용역 | 정책 배경·입법 이력, 해외 정책 벤치마크, 선행연구 검토, 정책 수혜자 분석, 정량 데이터 가용성 |
> | SI/SW개발 사업 | 기술 스택 동향, 유사 시스템 구축 사례, 기술 인력 시장, 보안/인증 요건, 데이터 이관 복잡도 |
> | 컨설팅 용역 | 발주기관 조직 현황, 동종 기관 사례, 방법론 프레임워크 비교, 변화관리 이슈, 산업 벤치마크 |
>
> 프롬프트는 **2단계 구조**로 실행된다:
> 1. **조사 설계**: RFP 분석 결과를 보고 "이 사업에 필요한 조사 차원 3~7개"를 AI가 직접 도출
> 2. **조사 수행**: 도출된 차원별로 Go/No-Go + 전략 수립에 쓸 수 있는 핵심 발견을 수집

```python
# app/graph/nodes/research_gather.py

async def research_gather(state: ProposalState) -> dict:
    """
    ★ v3.2: RFP-적응형 사전조사.
    획일적 7차원이 아니라, RFP의 사업 범주·내용에 맞게 조사 차원을
    동적으로 설계한 뒤, 각 차원별 핵심 발견을 수집한다.
    Go/No-Go 의사결정과 제안전략 수립을 위한 정보 제공이 목적.
    """
    rfp = state.get("rfp_analysis")
    rfp_raw = state.get("rfp_raw", "")

    # RFP 원문이 긴 경우 핵심부만 전달 (토큰 예산 관리)
    rfp_excerpt = rfp_raw[:8000] if len(rfp_raw) > 8000 else rfp_raw

    result = await claude_generate(
        RESEARCH_GATHER_PROMPT.format(
            rfp_analysis=rfp,
            rfp_excerpt=rfp_excerpt,
            project_name=rfp.project_name if rfp else "",
            client=rfp.client if rfp else "",
            hot_buttons=rfp.hot_buttons if rfp else [],
            mandatory_reqs=rfp.mandatory_reqs if rfp else [],
            eval_items=rfp.eval_items if rfp else [],
            special_conditions=rfp.special_conditions if rfp else [],
        ),
    )

    return {
        "research_brief": result,
        "current_step": "research_gather_complete",
    }
```

```python
# app/prompts/research_gather.py

RESEARCH_GATHER_PROMPT = """
## 역할
당신은 정부 용역 제안을 위한 사전조사 전문가입니다.
RFP 분석 결과를 면밀히 검토한 뒤, **이 사업에 맞는 조사 차원을 직접 설계**하고 조사를 수행하세요.

## RFP 분석 결과
- 사업명: {project_name}
- 발주기관: {client}
- Hot Buttons (발주기관 핵심 관심사): {hot_buttons}
- 필수 요구사항: {mandatory_reqs}
- 평가항목: {eval_items}
- 특수조건: {special_conditions}

## RFP 원문 발췌
{rfp_excerpt}

---

## STEP 1: 조사 차원 설계

아래를 고려하여, **이 사업의 Go/No-Go 판단과 제안전략 수립에 실질적으로 필요한 조사 차원 3~7개**를 도출하세요.

### 차원 설계 기준
- RFP의 **사업 범주**를 먼저 판별하세요 (예: 성과조사분석, 정책연구, SI/SW개발, 컨설팅, 교육훈련, R&D, 기획·타당성조사 등)
- 사업 범주에 따라 필요한 조사가 근본적으로 다릅니다:
  - 성과조사분석 → 대상 사업 집행 현황, 성과지표 체계, 평가 방법론 비교 등
  - 정책연구 → 정책 입법 이력, 해외 벤치마크, 선행연구, 정책 수혜자 분석 등
  - SI/SW개발 → 기술 스택 동향, 유사 시스템 사례, 보안 요건, 데이터 이관 등
  - 컨설팅 → 조직 현황, 동종 기관 사례, 방법론 비교, 변화관리 등
- **모든 사업에 공통 적용하는 고정 템플릿을 사용하지 마세요**
- 각 차원은 다음 질문에 답할 수 있어야 합니다:
  "이 조사 결과가 Go/No-Go 판단이나 제안전략에 어떻게 쓰이는가?"

### 차원 도출 출력
각 차원에 대해:
- 차원명 (간결하게)
- 조사 목적: 이 차원의 조사 결과가 Go/No-Go 또는 전략 수립에 왜 필요한지
- 핵심 조사 질문 2~3개

## STEP 2: 차원별 조사 수행

STEP 1에서 도출한 각 차원에 대해 조사를 수행하세요.

### 각 차원별 조사 출력
- **핵심 발견 3~5개**: Go/No-Go 판단이나 전략 수립에 직접 영향을 줄 사실·데이터
- **시사점(So What?)**: 이 발견이 우리 입찰에 구체적으로 의미하는 바 (1~2문장)
- **전략 활용 방향**: Go/No-Go 판단 근거 또는 제안전략에 어떻게 반영할지

## 품질 규칙
- 모든 수치에 출처(기관명, 보고서명, 연도) 명기. 예: "대상 사업 예산 집행률 78% (기재부, 2025)"
- 확인 불가한 수치 생성 금지 → "[확인 필요]" 표기
- [추정] 태그로 추정과 사실 구분
- 출처를 특정할 수 없는 일반 상식은 [일반지식] 태그 부착
- **RFP와 무관한 일반론을 나열하지 마세요** — 모든 발견은 이 사업에 대한 구체적 시사점과 연결되어야 합니다

## 출력 형식 (JSON)
{{
  "project_category": "사업 범주 판별 결과 (예: 성과조사분석, 정책연구, SI/SW개발 등)",
  "category_rationale": "사업 범주 판별 근거 (1~2문장)",
  "research_dimensions": [
    {{
      "dimension_id": "D1",
      "dimension_name": "차원명",
      "purpose": "이 차원의 조사 목적 — Go/No-Go 또는 전략에 왜 필요한가",
      "key_questions": ["핵심 조사 질문 1", "..."],
      "findings": [
        {{
          "finding": "핵심 발견 내용",
          "source": "출처 (기관명, 문서명, 연도)",
          "confidence": "확인됨|추정|확인필요"
        }}
      ],
      "implication": "이 사업에 대한 시사점",
      "strategic_use": "go_no_go|strategy|both — 어디에 활용할 정보인지"
    }}
  ],
  "go_no_go_summary": "Go/No-Go 판단에 영향을 줄 핵심 요인 요약 (3~5문장)",
  "strategy_inputs": "제안전략 수립에 활용할 핵심 인사이트 요약 (3~5문장)"
}}
"""
```

### 29-3. 신규 노드: `presentation_strategy`

**위치**: `review_proposal` approved → `presentation_strategy` → `ppt_fan_out_gate`
**역할**: 발표전략 수립 (킬링 메시지, 시간 배분, Q&A 전략)
**근거**: ProposalForge #12(발표전략)
**토큰 예산**: 8,000
**조건부 실행**: `eval_method == 'document_only'`이면 건너뛰기 (POST-06 연동)

```python
# app/graph/nodes/presentation_strategy.py

async def presentation_strategy(state: ProposalState) -> dict:
    """
    ★ v3.2: 발표전략 수립.
    서류심사(document_only) 방식이면 건너뛰고 PPT 생성으로 직행.
    """
    rfp = state.get("rfp_analysis")
    eval_method = ""
    if rfp:
        eval_method = rfp.eval_method if hasattr(rfp, 'eval_method') else rfp.get("eval_method", "")

    # 서류심사이면 발표전략 생략
    if "document_only" in str(eval_method).lower():
        return {"current_step": "presentation_strategy_skip"}

    strategy = state.get("strategy")
    proposal_sections = state.get("proposal_sections", [])
    self_review_score = state.get("parallel_results", {}).get("_self_review_score", {})

    result = await claude_generate(
        PRESENTATION_STRATEGY_PROMPT.format(
            project_name=rfp.project_name if rfp else "",
            client=rfp.client if rfp else "",
            eval_items=rfp.eval_items if rfp else [],
            tech_price_ratio=rfp.tech_price_ratio if rfp else {},
            win_theme=strategy.win_theme if strategy else "",
            ghost_theme=strategy.ghost_theme if strategy else "",
            key_messages=strategy.key_messages if strategy else [],
            self_review_score=self_review_score,
        ),
    )

    return {
        "presentation_strategy": result,
        "current_step": "presentation_strategy_complete",
    }
```

```python
# app/prompts/presentation_strategy.py

PRESENTATION_STRATEGY_PROMPT = """
## 역할
당신은 정부 용역 발표 전략 수립 전문가입니다.
제안서 내용과 평가 기준을 기반으로 최적의 발표 전략을 수립하세요.

## 제안 컨텍스트
- 사업명: {project_name}
- 발주기관: {client}
- 평가항목: {eval_items}
- 기술:가격 비율: {tech_price_ratio}
- Win Theme: {win_theme}
- Ghost Theme: {ghost_theme}
- 핵심 메시지: {key_messages}
- 자가진단 점수: {self_review_score}

## 발표전략 수립 지시

### 1. 킬링 메시지 설계
- 평가위원이 기억할 핵심 메시지 1개 (15자 이내)
- 보조 메시지 2~3개
- 반복 전략: 도입-본론-결론에서 어떻게 반복할 것인가

### 2. 시간 배분 전략
- 전체 발표 시간 대비 각 파트 배분 (배점 비례 + 전략적 가중)
- 고배점 항목에 시간 집중 배분
- 도입(10%), 본론(70%), 결론(10%), 질의응답 대비(10%) 기본 구조

### 3. 발표 3막 구조
- Act 1 (Why): 왜 이 사업이 중요한가 + 우리의 이해도
- Act 2 (How): 어떻게 수행할 것인가 (차별화 방법론)
- Act 3 (Us): 왜 우리팀인가 (실적 + 팀 역량)

### 4. Q&A 전략
- 예상 질문 Top 10 (평가위원 관점)
- 각 질문에 대한 모범 답변 (30초 이내)
- 위험 질문 대응: 약점을 강점으로 전환하는 프레이밍

### 5. 시각 전략
- 핵심 슬라이드 5~7장 선정 + 각 슬라이드의 시각적 포인트
- 데모/시연이 필요한 구간 식별

## 출력 형식 (JSON)
{{
  "killing_message": {{
    "main": "...",
    "sub_messages": [...],
    "repetition_strategy": "..."
  }},
  "time_allocation": [
    {{ "section": "...", "duration_pct": 0, "rationale": "..." }}
  ],
  "three_act_structure": {{
    "act1_why": {{ "key_point": "...", "duration_pct": 0 }},
    "act2_how": {{ "key_point": "...", "duration_pct": 0 }},
    "act3_us": {{ "key_point": "...", "duration_pct": 0 }}
  }},
  "qa_strategy": {{
    "expected_questions": [
      {{ "question": "...", "answer": "...", "risk_level": "high|medium|low" }}
    ]
  }},
  "visual_strategy": {{
    "key_slides": [...],
    "demo_sections": [...]
  }}
}}
"""
```

### 29-4. 기존 프롬프트 보강 — `go_no_go` (발주기관 인텔리전스 5단계)

```python
# app/prompts/go_no_go.py 에 추가 (기존 GO_NO_GO_FULL_PROMPT 보강)

# ★ v3.2: 발주기관 인텔리전스 5단계 프레임워크 (ProposalForge #3)
CLIENT_INTELLIGENCE_FRAMEWORK = """
## 발주기관 인텔리전스 분석 (5단계)

아래 5단계에 따라 발주기관을 심층 분석하세요.
각 단계의 분석 결과가 Go/No-Go 판단의 핵심 근거가 됩니다.

### Step 1: 기관 프로파일링
- 기관 미션, 비전, 전략방향
- 최근 인사이동 (기관장, 부서장)
- 조직도상 해당 사업 담당 부서 파악

### Step 2: 과거 발주 패턴
- 최근 3년 유사 사업 발주 이력
- 낙찰률 (예정가 대비 낙찰가 비율)
- 선호 수행기관 유형 (대기업/중소/학교/연구기관)
- 반복 발주 여부 (동일·유사 사업 계속 발주 시 기존 수행기관 유리)

### Step 3: 평가 성향 추정
- 실적 중시 vs 방법론 중시 vs 가격 중시
- 외부 평가위원 구성 성향 (학계/산업계/연구기관 비율)
- 과거 선정 결과에서 드러나는 패턴

### Step 4: 정책 맥락
- 상위 정책과의 연결 (국가전략, 부처 계획)
- 현 정부 정책 방향과의 정합성
- 관련 법령·제도 변화

### Step 5: 리스크
- 조직개편 리스크 (해당 부서 축소·통합 가능성)
- 예산삭감 리스크 (예산안 변동)
- 국감 이슈 (감사원·국정감사 지적 사항)
- 정치적 민감도 (선거, 정권 교체 영향)

데이터 소스: client_intel_ref (KB 발주기관 DB), research_brief (리서치 조사 결과)
"""

# GO_NO_GO_FULL_PROMPT에 client_intelligence_framework, research_brief 삽입
# 토큰 예산: 15,000 → 18,000 (+3,000)
```

### 29-5. 기존 프롬프트 보강 — `strategy_generate` (경쟁 SWOT + 시나리오 + 연구질문)

```python
# app/prompts/strategy.py 에 추가 (기존 STRATEGY_PROMPT 보강)

# ★ v3.2: 경쟁분석 & Win Strategy (ProposalForge #4)
COMPETITIVE_ANALYSIS_FRAMEWORK = """
## 경쟁분석 프레임워크

### 경쟁사별 SWOT 매트릭스
각 경쟁사에 대해 SWOT 분석 + "그래서 어떻게" 대응전략을 제시:
| 경쟁사 | S(강점) → 대응 | W(약점) → 공략 | O(기회) → 활용 | T(위협) → 방어 |

### 차별화 포인트 구조
각 차별화 포인트를 다음 구조로 작성:
- **What**: 무엇이 다른가
- **Why**: 왜 발주기관에 중요한가
- **How**: 어떻게 증명할 것인가
- **Evidence**: 구체적 근거 (수행실적, 특허, 인력 자격 등)

### 경쟁 시나리오별 대응전략
- **Best Case**: 경쟁사 약점이 부각되는 시나리오 → 공격적 차별화
- **Base Case**: 동등 경쟁 시나리오 → 가격+품질 균형
- **Worst Case**: 경쟁사 강점이 부각되는 시나리오 → 방어적 대응

### Win Theme 구조
"우리는 [X역량/경험]이기 때문에 [Y성과]를 가장 잘 할 수 있다"
- 각 Win Theme에 supporting evidence 최소 2개
"""

# ★ v3.2: 전략수립 보강 (ProposalForge #7)
STRATEGY_RESEARCH_FRAMEWORK = """
## 연구수행 전략 프레임워크

### 핵심 연구질문(Research Questions) 도출
RFP의 핵심 과업에서 3~5개 연구질문을 도출하세요:
- RQ1: [연구질문] → [답을 위한 접근법]
- RQ2: ...

### 연구수행 프레임워크
전체 연구/수행 구조를 시각적으로 설명 (Phase → Task → Output):
- Phase 1: [명칭] — 핵심 활동, 산출물, 기간
- Phase 2: ...

### 방법론 선택 근거
각 방법론 선택에 대해 3가지 관점의 근거 제시:
1. **학술 타당성**: 해당 방법론의 이론적 기반, 선행연구 활용 사례
2. **실무 실현가능성**: 투입인력·기간·예산 내 실행 가능 여부
3. **차별성**: 경쟁사 대비 방법론적 우위 포인트
"""

# 토큰 예산: 20,000 → 25,000 (+5,000)
```

### 29-6. 기존 프롬프트 보강 — `plan_price` (원가기준·노임단가·입찰시뮬레이션)

```python
# app/prompts/plan.py 에 추가 (기존 PLAN_PRICE_PROMPT 보강)

# ★ v3.2: 예산산정 상세 (ProposalForge #8 — 최대 가치 항목)
BUDGET_DETAIL_FRAMEWORK = """
## 예산산정 상세 프레임워크

### 1. 원가 기준 확인
RFP에서 적용 원가 기준을 판별하세요:
- SW사업 대가산정 기준 (한국소프트웨어산업협회)
- 엔지니어링 사업 대가 기준 (한국엔지니어링협회)
- 학술연구용역비 산정 기준 (기획재정부)
- 기타 (RFP 명시 기준)

### 2. 인건비 산출
등급별 노임단가 × 투입 M/M:
| 등급 | 노임단가(월) | 투입 M/M | 소계 |
|------|-------------|---------|------|
| 기술사 | [단가] | [M/M] | [금액] |
| 특급기술자 | [단가] | [M/M] | [금액] |
| 고급기술자 | [단가] | [M/M] | [금액] |
| 중급기술자 | [단가] | [M/M] | [금액] |
| 초급기술자 | [단가] | [M/M] | [금액] |

### 3. 직접경비
항목별 산출 근거를 명시:
- 여비 (출장비): 출장 횟수 × 단가
- 회의비: 회의 횟수 × 단가
- 설문조사비: 대상 수 × 단가 (해당 시)
- 데이터 구매비: 필요 데이터 목록 × 단가
- 인쇄비: 보고서 부수 × 단가
- 기타: RFP 특수 요구사항

### 4. 간접경비(제경비)
기관 유형별 인건비 대비 비율:
- 영리법인: 110~120%
- 비영리법인: 40~60%
- 컨소시엄 시 기관별 차등 적용

### 5. 기술료(이윤)
(인건비 + 직접경비 + 간접경비) × 비율:
- 영리법인: 20% 이내
- 비영리법인: 해당 없음

### 6. 입찰가격 결정 시뮬레이션
계약 방식별 최적가 산출:
- **협상에 의한 계약**: 기술평가 70~90% + 가격평가 10~30% → 최적 제안가격 범위
- **적격심사**: 추정가격 대비 최적 사정률 산출
- **2단계 경쟁입찰**: 기술 통과 후 가격 경쟁 → 최저가 전략 vs 적정가 전략

## 출력 형식 (JSON)
{{
  "cost_standard": "적용 원가 기준",
  "labor_cost": {{
    "breakdown": [...],
    "total": 0
  }},
  "direct_expenses": {{
    "items": [...],
    "total": 0
  }},
  "overhead": {{
    "rate": 0,
    "total": 0
  }},
  "profit": {{
    "rate": 0,
    "total": 0
  }},
  "total_cost": 0,
  "bid_simulation": {{
    "method": "...",
    "optimal_price": 0,
    "price_range": {{ "min": 0, "max": 0 }},
    "rationale": "..."
  }}
}}
"""

# plan_price 노드 출력에 budget_detail 필드 추가
# 토큰 예산: 12,000 → 15,000 (+3,000)

# ★ v3.3: labor_rates, market_price_data DB 조회 로직 추가 (ProposalForge 비교 검토 반영)
# 프롬프트의 "[단가]" 플레이스홀더를 실제 DB 데이터로 대체

async def plan_price(state: ProposalState) -> dict:
    """
    STEP 3: 예산산정.
    ★ v3.3: labor_rates, market_price_data 테이블에서 실제 데이터 조회 후
    프롬프트에 주입하여 "[단가]" 플레이스홀더 제거.
    """
    rfp = state.get("rfp_analysis")
    strategy = state.get("strategy")

    # 1. 원가 기준 판별 → 해당 기관의 노임단가 조회
    cost_standard = _detect_cost_standard(rfp)  # 'KOSA' | 'KEA' | 'MOEF' | 'OTHER'
    current_year = datetime.now().year

    labor_rates = await db.fetch_all(
        """SELECT grade, monthly_rate, daily_rate
           FROM labor_rates
           WHERE standard_org = $1 AND year = $2
           ORDER BY monthly_rate DESC""",
        cost_standard, current_year
    )
    # Fallback: 올해 데이터 없으면 직전 연도 조회 (§22-4-2)
    if not labor_rates:
        labor_rates = await db.fetch_all(
            """SELECT grade, monthly_rate, daily_rate
               FROM labor_rates
               WHERE standard_org = $1 AND year = $2
               ORDER BY monthly_rate DESC""",
            cost_standard, current_year - 1
        )

    # 2. 유사 도메인·규모의 시장 낙찰가 벤치마크 조회
    domain = _classify_domain(rfp)  # 'SI/SW개발', '정책연구', '성과분석', '컨설팅' 등
    budget = rfp.budget if rfp else None
    budget_range = (int(budget * 0.5), int(budget * 2.0)) if budget else (0, 999_999_999_999)

    market_benchmarks = await db.fetch_all(
        """SELECT bid_ratio, num_bidders, evaluation_method, year
           FROM market_price_data
           WHERE domain = $1 AND budget BETWEEN $2 AND $3
           ORDER BY year DESC LIMIT 20""",
        domain, budget_range[0], budget_range[1]
    )

    # 3. 조회된 데이터를 프롬프트에 주입
    labor_rates_table = _format_labor_rates_table(labor_rates)  # Markdown 테이블 형식
    benchmark_summary = _format_benchmark_summary(market_benchmarks)  # 평균 낙찰률, 경쟁 강도 등

    result = await claude_generate(
        PLAN_PRICE_PROMPT.format(
            rfp_analysis=rfp,
            strategy=strategy,
            cost_standard=cost_standard,
            labor_rates_table=labor_rates_table,      # ★ 실제 노임단가 데이터
            benchmark_summary=benchmark_summary,       # ★ 시장 벤치마크 데이터
        ),
    )

    return {
        "parallel_results": {"bid_price": result},
        "budget_detail": result,
    }


def _detect_cost_standard(rfp) -> str:
    """RFP 내용에서 적용 원가 기준 자동 판별."""
    if not rfp:
        return "KOSA"
    text = str(rfp).lower()
    if "엔지니어링" in text or "기술용역" in text:
        return "KEA"
    if "학술" in text or "연구용역" in text or "기획재정부" in text:
        return "MOEF"
    return "KOSA"  # SW사업 대가산정 기준 (기본값)


def _classify_domain(rfp) -> str:
    """RFP 사업 유형을 도메인으로 분류."""
    if not rfp:
        return "기타"
    text = str(rfp).lower()
    if any(kw in text for kw in ["시스템", "개발", "구축", "sw", "소프트웨어"]):
        return "SI/SW개발"
    if any(kw in text for kw in ["정책", "연구", "학술"]):
        return "정책연구"
    if any(kw in text for kw in ["성과", "평가", "분석", "조사"]):
        return "성과분석"
    if any(kw in text for kw in ["컨설팅", "자문", "진단"]):
        return "컨설팅"
    return "기타"
```

### 29-7. 기존 프롬프트 보강 — `self_review` (3인 페르소나 시뮬레이션)

```python
# app/prompts/self_review.py 에 추가 (기존 SELF_REVIEW_PROMPT 보강)

# ★ v3.2: 평가 시뮬레이션 (ProposalForge #10 — 3인 페르소나)
EVALUATION_SIMULATION_FRAMEWORK = """
## 평가위원 시뮬레이션 (3인 페르소나)

기존 4축 100점 정량 평가에 추가하여, 3인의 가상 평가위원 관점에서 정성 평가를 수행하세요.

### 평가위원 A (산업계 전문가)
- 관점: 실현가능성, 현장 적용성, 실무 경험 기반 판단
- 핵심 질문: "이 방법론을 실제 현장에서 적용할 수 있는가?"
- 평가: 각 평가항목에 대해 강점/약점 1줄 코멘트 + 예상 질문 1개

### 평가위원 B (학계 전문가)
- 관점: 방법론 타당성, 논리 구조, 학술적 엄밀성
- 핵심 질문: "이론적 근거가 충분하고 연구 설계가 타당한가?"
- 평가: 각 평가항목에 대해 강점/약점 1줄 코멘트 + 예상 질문 1개

### 평가위원 C (연구기관 전문가)
- 관점: 기존 연구 대비 차별성, 정책 기여, 활용 가능성
- 핵심 질문: "기존 유사 연구와 차별화되고, 정책에 실제 기여하는가?"
- 평가: 각 평가항목에 대해 강점/약점 1줄 코멘트 + 예상 질문 1개

## 품질 게이트 (★ v3.2 개선)
기존: 전체 ≥ 80 → pass
변경: 전체 ≥ 80 AND 각 축 ≥ 17.5 (70% of 25) → pass
      전체 ≥ 80 BUT 축 < 17.5 → 해당 축 경고 + Human 판단 위임

## 출력에 추가되는 필드 (evaluation_simulation)
{{
  "persona_reviews": [
    {{
      "persona": "산업계",
      "strengths": [...],
      "weaknesses": [...],
      "expected_questions": [{{ "question": "...", "model_answer": "..." }}]
    }},
    ...
  ],
  "axis_warnings": [
    {{ "axis": "...", "score": 0, "warning": "..." }}
  ]
}}
"""

# self_review_with_auto_improve 함수에 통합:
# 1. 기존 4축 100점 평가 유지
# 2. 3인 페르소나 정성 코멘트 추가
# 3. 축별 최소 기준(17.5) 적용
# 4. evaluation_simulation state 필드로 출력
```

### 29-8. 기존 프롬프트 보강 — `proposal_section` (자체검증 체크리스트)

```python
# app/prompts/proposal_sections.py 에 추가

# ★ v3.2: 섹션별 자체검증 체크리스트 (ProposalForge #9)
SECTION_SELF_CHECK = """
## 섹션 자체검증 체크리스트
작성 완료 후 아래 항목을 자체 검증하고 결과를 JSON에 포함하세요:

1. □ RFP 필수과업 반영 여부: 해당 섹션이 매핑된 RFP 요구사항을 모두 다루었는가?
2. □ 평가항목 대응 충분성: 해당 평가항목의 배점에 비례한 분량과 깊이인가?
3. □ 핵심 키워드 포함 여부: RFP의 핵심 키워드가 섹션 내에 자연스럽게 포함되었는가?
4. □ 연속 텍스트 제한: 2페이지 이상 연속 텍스트가 없는가? (도표·그림·박스 삽입 필요)

출력에 추가:
"self_check": {{
  "rfp_coverage": true|false,
  "eval_item_depth": true|false,
  "keyword_inclusion": true|false,
  "text_break_ok": true|false,
  "issues": ["미충족 항목 설명"]
}}
"""
```

### 29-9. PPT 프롬프트 신규 생성

```python
# app/prompts/ppt.py (★ v3.2: 신규 작성 — ProposalForge #11)

PPT_SYSTEM_PROMPT = """
## 역할
당신은 정부 용역 발표 PPT 설계 전문가입니다.
제안서 내용과 발표전략을 기반으로 효과적인 슬라이드를 설계하세요.

## PPT 설계 원칙

### 1. 1슬라이드 1메시지
- 하나의 슬라이드에는 하나의 핵심 메시지만 전달
- 헤드라인이 곧 메시지 (질문형 X, 선언형 O)
- 예: "시스템 아키텍처" ❌ → "클라우드 네이티브로 30% 비용 절감" ✅

### 2. 시각 > 텍스트
- 텍스트: 50자 × 5줄 이내 (250자 제한)
- 키워드 중심, 문장형 서술 최소화
- 도표, 차트, 다이어그램, 아이콘 적극 활용
- 시각적 요소가 슬라이드 면적의 60% 이상 차지

### 3. 고배점 항목 집중
- 평가 배점 비례로 슬라이드 수 배분
- 핵심 차별화 포인트에 2~3배 슬라이드 할당
- 저배점/행정사항은 1장 요약으로 처리

### 4. 3막 구조 스토리라인
- **Why (도입)**: 사업 이해도 + 문제 인식 → 청중의 공감 확보
- **How (본론)**: 수행 방법론 + 차별화 → 논리적 설득
- **Us (결론)**: 팀 역량 + 약속 → 신뢰와 확신

### 5. 슬라이드 설계 단위
각 슬라이드에 대해 아래 정보를 생성:
"""

PPT_SLIDE_PROMPT = """
{ppt_system_prompt}

## 발표전략 컨텍스트
{presentation_strategy}

## 제안서 섹션 내용
{section_content}

## 해당 슬라이드 지시
- 섹션: {section_id}
- 슬라이드 번호: {slide_index}

## 출력 형식 (JSON)
{{
  "slide_id": "{section_id}_slide_{slide_index}",
  "headline": "핵심 메시지 (선언형, 20자 이내)",
  "visual_type": "chart|diagram|table|icon_grid|timeline|comparison|image",
  "key_points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
  "text_content": "본문 (250자 이내)",
  "speaker_note": "발표자 노트 (구어체, 30초~1분 분량)",
  "duration_seconds": 60,
  "visual_description": "시각 자료 상세 설명 (pptx_builder가 참조)"
}}
"""
```

### 29-10. 토큰 예산 갱신 요약

| 노드 | v3.1 예산 | v3.2 예산 | 변경 | 비고 |
|------|----------|----------|------|------|
| research_gather | — | 15,000 | 신규 | RFP-적응형 사전조사 |
| go_no_go | 6,000 | 18,000 | +12,000 | 발주기관 인텔 5단계 + research_brief |
| strategy_generate | 10,000 | 25,000 | +15,000 | SWOT + 시나리오 + 연구질문 |
| plan_price | (plan 6,000 중 일부) | 15,000 | +9,000 | 원가기준·노임단가·입찰시뮬레이션 |
| presentation_strategy | — | 8,000 | 신규 | 발표전략 (조건부) |
| PPT (sldie당) | 4,000 | 4,000 | 변경 없음 | 프롬프트 내용만 보강 |
| **추가 토큰 합계** | | | **~+34,000** | ~80K → ~114K/프로젝트 |

> **비용 영향**: Claude Sonnet 기준 프로젝트당 ~$0.10~0.50 추가. 허용 범위 내.
> `token_manager.py`의 `STEP_BUDGETS` 딕셔너리에 신규 노드 예산 추가 필요 (§21 참조).

### 29-11. ProposalForge 에이전트 → TENOPA 노드 매핑 참조표

| # | ProposalForge 에이전트 | 판정 | TENOPA 대응 | 비고 |
|---|---|---|---|---|
| 1 | Orchestrator | 스킵 | graph.py 엣지 라우팅 | LangGraph가 동일 역할 수행 |
| 2 | RFP 해석 | 소폭 보강 | rfp_analyze | hidden_requirements 필드 추가 |
| 3 | 발주기관 인텔리전스 | 프롬프트 보강 | go_no_go | 5단계 분석 프레임워크 (§29-4) |
| 4 | 경쟁분석 & Win Strategy | 프롬프트 보강 | strategy_generate | SWOT + 시나리오 (§29-5) |
| 5-6 | 리서치 디렉터 + 7서브 | 신규 노드 | research_gather | RFP-적응형 1개 노드 (§29-2) |
| 7 | 전략 수립 | 소폭 보강 | strategy_generate | 연구질문·방법론 (§29-5) |
| 8 | 예산 산정 | 대폭 보강 | plan_price | 원가기준·입찰시뮬 (§29-6) |
| 9 | 제안서 작성 | 소폭 보강 | proposal_section | 자체검증 체크리스트 (§29-8) |
| 10 | 평가 시뮬레이션 | self_review 보강 | self_review | 3인 페르소나 (§29-7) |
| 11 | PPT 생성 | 프롬프트 생성 | ppt.py | 신규 프롬프트 (§29-9) |
| 12 | 발표전략 | 신규 노드 | presentation_strategy | 발표전략 수립 (§29-3) |
| 13 | Verification | 소폭 보강 | self_review | 팩트체크 강화 (기존 source_tagger 활용) |

## 30. ★ ProposalForge v3.0 비교 검토 — 의도적 스킵 기록 (v3.3)

> **배경**: ProposalForge v3.0 전체 설계서와 TENOPA v3.2를 비교하여, 가치 있는 항목은 §15/§4/§8/§11/§22/§29에 반영하고, 아래 항목은 의도적으로 스킵. Pattern A(모놀리식 StateGraph) 유지 원칙에 따라 Pattern B 구조는 채택하지 않되, 프롬프트/로직/DB 스키마 중 가치 있는 내용만 흡수.

### 30-1. 의도적 스킵 항목

| # | ProposalForge 제안 | 판정 | 스킵 사유 | 대안 |
|---|---|---|---|---|
| 1 | 프롬프트 레지스트리 (`prompt_registry`) — DB 버전 관리, A/B 테스트 | 스킵 | `app/prompts/` Python 파일 + Git 버전 관리로 충분. A/B 테스트는 MVP 이후 | Git 커밋 메시지에 프롬프트 성능 변화 기록 |
| 2 | 다중 LLM Fallback (Claude → GPT → Gemini) | 스킵 | Claude API 단일 사용 확정. 프롬프트 호환성 관리 비용이 큼 | 지수 백오프 재시도 + 에러 알림 (§22-4-1) |
| 3 | MCP Server Layer (18+ Connectors) | 스킵 | `app/services/`에서 직접 통합. MCP 추상화 계층 불필요 | 기존 서비스 레이어 유지 |
| 4 | Celery + Redis 태스크 큐 | 스킵 | LangGraph `AsyncPostgresSaver` + FastAPI async가 동일 역할 | 기존 아키텍처 유지 |
| 5 | Pinecone + Elasticsearch | 스킵 | Supabase PostgreSQL + pgvector로 통합 처리 (§20) | 기존 벡터 검색 유지 |
| 6 | 자동 패턴 추출 엔진 (Organizational Learning Loop) | 향후 과제 | 데이터 축적 필요 (10+ 프로젝트). 현재는 수동 교훈 입력(§20 KB Part E)으로 충분 | 수동 교훈 → 향후 자동화 |
| 7 | RBAC 역할 세분화 (5등급) | 이미 충분 | TENOPA v2.0에서 팀원/팀장/본부장/경영진/관리자 5등급 + 결재선 이미 설계 (§17, §15) | — |

### 30-2. v3.3에서 반영된 항목 요약

| # | 항목 | 반영 위치 | 우선순위 |
|---|---|---|---|
| 1 | `labor_rates` 노임단가 테이블 | §15-5h | HIGH |
| 2 | `market_price_data` 낙찰가 벤치마크 테이블 | §15-5i | HIGH |
| 3 | `artifacts` 버전 관리 컬럼 추가 | §15-4 | MEDIUM |
| 4 | 품질 게이트 원인별 피드백 라우팅 (5방향) | §4, §8, §11 | HIGH |
| 5 | 전략-예산 상호조정 루프 | §4, §11 | MEDIUM |
| 6 | `plan_price` 실데이터 조회 로직 | §29-6 | HIGH |
| 7 | Fallback 전략 체계화 | §22-4 | MEDIUM |

### 30-3. 갭 분석 영향 예측

> v3.2 매칭률 96% → v3.3 목표 97%+
> - DB 스키마 완전성 향상: `plan_price` 프롬프트의 모든 `[단가]` 플레이스홀더가 실제 DB 조회로 대체 가능
> - 그래프 플로우 강건성 향상: 원인별 피드백 루프로 품질 게이트 통과율 개선
> - 운영 안정성 향상: 체계적 Fallback 전략으로 장애 시 graceful degradation 보장

---

## 31. ★ ProposalForge 프론트엔드 화면 흐름 비교 검토 반영 (v3.4)

> **배경**: ProposalForge의 프론트엔드 화면 흐름 설계서(30+ 라우트, 30+ 컴포넌트, 상세 와이어프레임)를
> TENOPA의 기존 설계(§13, 24개 컴포넌트)와 실제 구현(13개 라우트)을 비교하여,
> 차용할 가치가 있는 항목과 의도적 스킵 항목을 식별함.

### 31-1. 이미 TENOPA에 있는 것 (차용 불필요)

| ProposalForge 항목 | TENOPA 현황 | 판정 |
|---|---|---|
| 대시보드 KPI 카드 + 수주율 차트 | `dashboard/page.tsx` — 개인/팀/회사 KPI, 월별 추이, 기관별 수주율 | TENOPA가 더 상세 (3단 스코프 토글) |
| 프로젝트 목록/생성 | `proposals/page.tsx`, `proposals/new/page.tsx` — 드래그앤드롭, 서식 선택, 섹션 주입 | 이미 구현 완료 |
| 실시간 상태 추적 | `usePhaseStatus.ts` — Supabase Realtime + 폴링 | 전송 방식만 다름 (WebSocket vs Realtime) |
| 버전 관리 | 버전 드롭다운, 버전별 Diff 비교 탭, v3.3에서 artifacts 컬럼 강화 | 이미 구현+설계 완료 |
| 역할별 대시보드 | §13-8 — member/lead/director/executive/admin 5종 | **TENOPA가 우위** (PF는 단일 대시보드) |
| 알림 시스템 | §13 NotificationBell, Teams webhook, 인앱 알림 | Teams(MS365 환경)가 적합 |
| 팀 관리 | `admin/page.tsx` — 팀 CRUD, 멤버 초대, 역할 변경 | 이미 구현 완료 |
| KB/리소스 관리 | `resources/page.tsx` + §20 KB Part A~F (pgvector 시맨틱 검색) | **TENOPA가 우위** (벡터 검색) |
| 공고 추천 | `bids/page.tsx` — AI 매칭 점수, S/A/B/C/D 등급 | 이미 구현 완료 |

### 31-2. 차용 항목 및 반영 위치

| # | 항목 | 우선순위 | 반영 위치 | 핵심 내용 |
|---|---|---|---|---|
| 2-A | 인브라우저 제안서 편집기 | **HIGH** | §13-10 | Tiptap 3컬럼 (목차+에디터+AI 패널). "생성→편집→협업" 모델 |
| 2-B | 모의평가 결과 시각화 | **HIGH** | §13-11 | 3인 점수 카드, 레이더 차트, 취약점 TOP 3, 예상 Q&A |
| 2-C | 체크포인트 리뷰 구조화 | **MEDIUM** | §13-5 보강 | AI 이슈 플래그, 섹션별 인라인 피드백 |
| 2-D | 워크플로우 그래프 시각화 | **MEDIUM** | §13-1-1 보강 | 수평 Phase 그래프, 병렬 분기, 체크포인트 배지 |
| 2-E | 분석 대시보드 | **MEDIUM** | §13-12 | 실패 원인 파이, 포지셔닝별 수주율 (선별 채택) |
| 2-F | 원가기준/낙찰가 관리 UI | **MEDIUM** | §13-13 | KB 탭에 labor_rates + market_price_data CRUD 추가 |
| 2-G | shadcn/ui 도입 | **LOW-MEDIUM** | §31-3 | 일관된 컴포넌트 시스템. 기존 raw Tailwind 인라인 대체 |
| 2-H | Recharts 차트 도입 | **LOW-MEDIUM** | §31-3 | HTML 테이블/CSS 바 → 데이터 시각화 강화 |

### 31-3. UI 라이브러리 인프라 (신규)

> 기존 raw Tailwind CSS 인라인 스타일에서 체계적 컴포넌트 시스템으로 전환.
> 2-A~2-F 구현의 효율적 기반.

#### 31-3-1. shadcn/ui

| 항목 | 내용 |
|---|---|
| 목적 | 일관된 UI 컴포넌트 시스템 (Dialog, Tabs, Select, Badge, Toast 등) |
| 설치 | `npx shadcn-ui@latest init` → 개별 컴포넌트 추가 |
| 위치 | `frontend/components/ui/` (자동 생성) |
| 의존성 | `tailwindcss`, `tailwind-merge`, `clsx`, `class-variance-authority` |
| 테마 | 기존 다크 테마 호환 — `globals.css`에 CSS 변수 오버라이드 |
| 대상 컴포넌트 | `Button`, `Dialog`, `Tabs`, `Select`, `Switch`, `Badge`, `Toast`, `Accordion`, `DropdownMenu`, `Tooltip` |

#### 31-3-2. Tiptap 에디터

| 항목 | 내용 |
|---|---|
| 목적 | 인브라우저 제안서 편집기 (§13-10) |
| 패키지 | `@tiptap/react`, `@tiptap/starter-kit`, `@tiptap/extension-highlight`, `@tiptap/extension-placeholder`, `@tiptap/extension-table` |
| 향후 | `@tiptap/extension-collaboration` + Yjs (공동 편집, v2 이후) |
| 출력 | HTML → `docx_builder.py`에서 DOCX 변환 |

#### 31-3-3. Recharts

| 항목 | 내용 |
|---|---|
| 목적 | 데이터 시각화 (레이더/라인/바/파이 차트) |
| 패키지 | `recharts` |
| 사용처 | `EvaluationRadarChart` (레이더), `AnalyticsPage` (파이/라인/바), 경영진 대시보드 (라인/바) |
| 대체 | 기존 CSS div 기반 바 차트 → `<BarChart>`, HTML 테이블 → `<LineChart>` |

#### 31-3-4. 프론트엔드 의존성 요약

```json
{
  "dependencies": {
    "@tiptap/react": "^2.x",
    "@tiptap/starter-kit": "^2.x",
    "@tiptap/extension-highlight": "^2.x",
    "@tiptap/extension-placeholder": "^2.x",
    "@tiptap/extension-table": "^2.x",
    "recharts": "^2.x",
    "tailwind-merge": "^2.x",
    "clsx": "^2.x",
    "class-variance-authority": "^0.7.x"
  }
}
```

### 31-4. 의도적 스킵 (프론트엔드)

| # | ProposalForge 항목 | 스킵 사유 |
|---|---|---|
| 1 | 워크플로 단계별 개별 라우트 (`/rfp`, `/strategy`, `/budget` 등 8개) | TENOPA는 단일 프로젝트 페이지 + LangGraph interrupt 기반 리뷰. 8개 서브라우트는 UX 파편화 |
| 2 | 브라우저 PPT 미리보기 | 한국 정부 제안서는 HWP/PPTX 특수 서식. 브라우저 렌더링 불안정. 네이티브 앱에서 열기가 정확 |
| 3 | 프롬프트 관리 Admin 페이지 | `app/prompts/` Python 파일 + Git으로 관리. UI 에디터는 테스트/버전관리 우회 위험 |
| 4 | 발표전략 별도 페이지 | 하나의 산출물. 리뷰 패널 내 탭으로 표시하면 충분 |
| 5 | 4-Phase 구조 | TENOPA는 6단계(STEP 0~5)가 한국 공공조달 워크플로에 더 적합 |
| 6 | Slack 연동 | 대상 기업은 MS365/Teams 환경. Teams webhook이 적합 |
| 7 | 30+ 컴포넌트 분류 체계 | TENOPA 자체 §13 설계(24+10=34개) 기반으로 구현. shadcn/ui가 기반 제공 |
| 8 | 가격 산점도 차트 | 낙찰가 데이터 부족. 데이터 축적 후 재검토 |
| 9 | AI 성공 패턴 인사이트 | v1에서는 over-engineering. 10+ 프로젝트 축적 후 재검토 |

### 31-5. 구현 우선순위 및 의존 관계

```
Phase 1 (인프라):
  shadcn/ui 도입 ──→ 모든 Phase 2~3의 기반
  Recharts 도입  ──→ Phase 2의 차트 기반

Phase 2 (HIGH - 핵심 UX):
  ┌── ProposalEditor (§13-10) ←── Tiptap + shadcn/ui
  │     └── EditorTocPanel + EditorAiPanel
  └── EvaluationView (§13-11) ←── Recharts + shadcn/ui
        └── EvaluationRadarChart

Phase 3 (MEDIUM - 기존 설계 구현):
  ┌── ReviewPanel 보강 (§13-5)  ←── shadcn/ui (Tabs, Accordion)
  ├── PhaseGraph (§13-1-1)     ←── shadcn/ui (Badge, Tooltip)
  ├── AnalyticsPage (§13-12)   ←── Recharts
  └── LaborRates/MarketPrices (§13-13) ←── shadcn/ui (Table)
```

### 31-6. 설계 문서 변경 요약

| 변경 대상 | 변경 내용 | 유형 |
|---|---|---|
| §1 아키텍처 개요 | Frontend 영역에 v3.4 편집기/시각화/UI 인프라 명시 | 수정 |
| §2 디렉토리 구조 | 3개 라우트, 10개 컴포넌트, ui/ 디렉토리, lib/utils.ts 추가 | 수정 |
| §13-1-1 | 수평 프로그레스바 → PhaseGraph (수평 Phase 그래프) 전면 개정 | 수정 |
| §13-5 | AI 이슈 플래그 + 섹션별 인라인 피드백 보강 | 수정 |
| §13-7 | AI 상태 패널 결합 + 구현 명세 보강 | 수정 |
| §13-10 | ProposalEditor — 인브라우저 제안서 편집기 (신규) | 추가 |
| §13-11 | EvaluationView — 모의평가 결과 시각화 (신규) | 추가 |
| §13-12 | AnalyticsPage — 분석 대시보드 (신규) | 추가 |
| §13-13 | 원가기준/낙찰가 관리 UI (신규) | 추가 |
| §31 | 본 섹션 — 비교 검토 전문 + UI 인프라 + 스킵 기록 | 추가 |
| 변경 이력 | v3.3 → v3.4 항목 추가 | 수정 |

### 31-7. 검증 체크리스트

- [x] 각 차용 항목이 §13 기존 설계와 충돌하지 않음 확인
- [x] 차용 항목의 데이터 소스가 백엔드(§3 State, §15 DB)에 이미 존재 확인
  - `evaluation_simulation` → §3 State (v3.2)
  - `labor_rates`, `market_price_data` → §15-5h, §15-5i (v3.3)
  - `compliance_matrix` → §10 (v1.2)
  - `result_reason` → §15 proposals 테이블 (v2.0)
- [x] 스킵 항목이 요구사항(v4.9)에서 필수가 아님 확인
- [x] 신규 라우트가 기존 라우트 구조와 일관됨 확인
- [x] UI 라이브러리 의존성이 Next.js + React 18과 호환됨 확인

### 31-8. ★ ProposalForge API 엔드포인트 비교 검토 (v3.4)

> **배경**: ProposalForge의 API 엔드포인트 설계서(11개 섹션, 80+ 엔드포인트)를 TENOPA의 §12(12개 서브섹션, 60+ 엔드포인트)와 비교.
> 특히 v3.4에서 추가한 프론트엔드 컴포넌트(§13-10~13)에 필요한 API가 §12에 누락되어 있어, 갭 해소가 핵심 목표.

#### 31-8-1. 이미 TENOPA에 있는 것 (차용 불필요)

| PF 항목 | TENOPA 현황 | 판정 |
|---|---|---|
| 프로젝트 CRUD | §12-1: 3가지 진입 경로(검색/공고번호/RFP 업로드) | **TENOPA가 더 상세** |
| 체크포인트 approve/reject/feedback 분리 | §12-2: `/resume` 다형성 페이로드로 통합 | LangGraph interrupt()와 정합. **TENOPA 유지** |
| 섹션별 피드백 | §12-2: `rework_targets` + `comments` per section | 이미 지원 |
| DOCX/PPTX 내보내기 | §12-4: `/download/docx`, `/download/pptx` | 이미 있음 |
| WebSocket 스트리밍 | §12-5: SSE 선택 (단방향 충분, 단순함) | 아키텍처 결정 유지 |
| Auth (JWT + 역할) | §12-6: Azure AD SSO + Supabase Auth, 5역할 | MS365 환경에 적합 |
| 사용자/조직 관리 | §12-7: users, orgs, divisions, teams, participants | 이미 있음 |
| 대시보드 KPI | §12-8: 역할별 8개 엔드포인트 | **TENOPA가 더 상세** (5역할 스코프) |
| 성과 추적 | §12-9: individual/team/division/company + trends | 이미 있음 |
| 알림 | §12-10: CRUD + settings + Teams webhook | 이미 있음 |
| 감사 로그 | §12-11 | 이미 있음 |
| KB CRUD | §12-12 → §20-4 (pgvector 시맨틱 검색 포함) | 이미 있음 |
| 섹션 편집 + AI/Human 추적 | §27-1: `PUT /artifacts/{step}/sections/{section_id}` + `change_source` | v3.0에서 추가 |
| 섹션 잠금 | §24: `POST/DELETE/GET /sections/*/lock` | 이미 있음 |
| 버전 이력 | §12-4: `/artifacts/{step}/versions` + `diff_from_previous` JSONB | DB 레벨 지원 |

#### 31-8-2. 차용 항목 (본 v3.4에서 반영)

**HIGH — v3.4 프론트엔드 필수**

| # | 항목 | 추가 엔드포인트 | 반영 위치 | 근거 |
|---|---|---|---|---|
| H1 | 섹션 AI 재생성 | `POST .../sections/{section_id}/regenerate` | §12-4-1 | §13-10 "AI에게 질문하기" |
| H2 | AI 어시스턴트 인라인 제안 | `POST .../ai-assist` | §12-4-2 | §13-10 EditorAiPanel |
| H3 | 모의평가 결과 조회 | `GET .../evaluation` | §12-4-3 | §13-11 EvaluationView |
| H4 | 노임단가 CRUD | `GET/POST/PUT/DELETE /api/kb/labor-rates` + import | §12-12 확장 | §13-13, §15-5h |
| H5 | 낙찰가 벤치마크 CRUD | `GET/POST/PUT/DELETE /api/kb/market-prices` | §12-12 확장 | §13-13, §15-5i |
| H6 | 분석 대시보드 집계 | 4개 analytics API | §12-13 신규 | §13-12 AnalyticsPage |

**MEDIUM — 품질 개선**

| # | 항목 | 반영 위치 | 근거 |
|---|---|---|---|
| M1 | 표준 에러 코드 체계 | §12-0 신규 | ProposalEditor 자동저장에서 에러 구분 필수 |
| M2 | 버전 간 Diff 조회 | §12-4-4 | 임의 버전 교차 비교 지원 |
| M3 | HWP 내보내기 | §12-4-5 | 한국 공공조달 필수 포맷 |

**LOW — 향후 검토**

| # | 항목 | 이유 |
|---|---|---|
| L1 | Cursor 기반 페이지네이션 | v1 데이터량 소규모, 구현 시 점진 적용 |
| L2 | 에이전트 성능 분석 API | `ai_task_logs`로 ad-hoc 분석 가능 |

#### 31-8-3. 의도적 스킵

| PF 항목 | 스킵 사유 |
|---|---|
| `/api/v1/` 버전 프리픽스 | 내부 인트라넷 도구, 단일 프론트엔드 소비자. 라우팅 복잡성만 증가 |
| 체크포인트 분리 엔드포인트 (`/checkpoints/{cp_id}/approve\|reject`) | TENOPA `/resume` 다형성이 LangGraph `interrupt()/resume()`와 정확히 매핑 |
| WebSocket (`/ws/projects/{id}/stream`) | SSE 단방향으로 충분. 아키텍처 결정(§1) 유지 |
| 프롬프트 거버넌스 API (`/admin/prompts` CRUD, A/B 테스트) | §30-1에서 이미 스킵 확정. Git 기반 관리 |
| 발주기관별 원가 규정 API (`/client-rules/{client_id}`) | `client_intel` KB(§20)에서 관리. 별도 규칙 엔진은 over-engineering |
| ROI/비용 효율성 분석 (`/analytics/roi`, `/cost-efficiency`) | 재무 데이터 연동 범위 밖 |
| 성공/실패 패턴 ML (`/analytics/success-patterns`) | §31-4에서 이미 스킵. 10+ 프로젝트 데이터 축적 필요 |
| PDF 내보내기 | 한국 정부 제안서는 DOCX/HWP/PPTX. PDF는 부차적 |

#### 31-8-4. 핵심 시사점

1. **v3.4 프론트엔드에 API 갭 5건 해소**: §13-10~13에 필요한 H1~H6 엔드포인트를 §12-4, §12-12, §12-13에 추가하여 프론트엔드-백엔드 정합성 확보.
2. **표준 에러 코드 도입**: ProposalEditor 자동저장이 빈번한 API 호출을 유발하므로, 에러 종류별 핸들링(재시도/토큰갱신/인라인에러)을 §12-0에서 체계화. §22-4 Fallback 전략과 일관성 유지.
3. **TENOPA `/resume` 다형성 패턴 유지**: PF의 checkpoint 분리 엔드포인트는 다중 에이전트에 적합하지만, TENOPA의 모놀리식 StateGraph + interrupt() 패턴에서는 단일 `/resume`이 더 깔끔. 변경 불요.
