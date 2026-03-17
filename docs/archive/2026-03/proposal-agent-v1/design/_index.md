# 설계 문서: 용역 제안서 자동 생성 에이전트 v1

| 항목 | 내용 |
|------|------|
| 문서 버전 | v3.6 |
| 작성일 | 2026-03-16 |
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
| | **v3.4 → v3.5**: 워크플로 개선 — STEP 4 Send() 병렬 fan-out → 섹션별 순차 작성 + 리뷰 루프, 10개 섹션 유형별 전문 프롬프트, 스토리라인 파이프라인 (plan_story → plan_merge 동기화 → proposal_write_next 주입). **v3.5 모듈 분할** — 8,397줄 단일 파일 → 18개 모듈 파일, §32 내용을 각 대상 섹션에 머지 |
| | **v3.5 → v3.6**: Grant-Writer Best Practice 기반 프롬프트 개선 7항목 — EVALUATOR_PERSPECTIVE_BLOCK 스토리텔링 원칙, PLAN_STORY SMART 목표 프레임워크, ADDED_VALUE SMART 기준 표, PLAN_PRICE Budget Narrative, COMMON_SYSTEM_RULES 용어 정합성 원칙, MAINTENANCE 지속가능성, METHODOLOGY 적응적 관리, UNDERSTAND Needs Validation 강화 |

---

## 모듈 구조

| # | 파일 | 원본 섹션 | 설명 |
|---|------|----------|------|
| 01 | [01-architecture.md](01-architecture.md) | §1, §2, §19 | 아키텍처 개요, 디렉토리 구조, 구현 순서 |
| 02 | [02-state-schema.md](02-state-schema.md) | §3 + §32-3 | LangGraph State 스키마 |
| 03 | [03-graph-definition.md](03-graph-definition.md) | §4 + §32-2, §32-9 | 그래프 정의 + STEP 4 순차 작성 |
| 04 | [04-review-nodes.md](04-review-nodes.md) | §5 + §32-7 | 리뷰 노드 (Shipley Color Team) |
| 05 | [05-step0-rfp.md](05-step0-rfp.md) | §6, §7 | STEP 0 RFP 검색 + Go/No-Go |
| 06 | [06-proposal-workflow.md](06-proposal-workflow.md) | §8, §9, §10 + §32-5/6 | 자가진단 + 제안서 작성 + Compliance + 스토리라인 |
| 07 | [07-routing-edges.md](07-routing-edges.md) | §11 + §32-4 | Conditional Edge 라우팅 |
| 08 | [08-api-endpoints.md](08-api-endpoints.md) | §12 | API 엔드포인트 설계 |
| 09 | [09-frontend.md](09-frontend.md) | §13 | 프론트엔드 핵심 컴포넌트 |
| 10 | [10-lite-mode.md](10-lite-mode.md) | §14 | 간이 모드 (Lite Mode) |
| 11 | [11-database-schema.md](11-database-schema.md) | §15 | PostgreSQL 스키마 |
| 12 | [12-prompts.md](12-prompts.md) | §16, §29, §33 + §32-5-2/5-3/8 | 프롬프트 설계 |
| 13 | [13-auth-notifications.md](13-auth-notifications.md) | §17, §18 | 인증 + Teams 알림 |
| 14 | [14-services-v3.md](14-services-v3.md) | §20~§26 | v3.0 서비스 설계 |
| 15a | [15a-gap-high-archive.md](15a-gap-high-archive.md) | §27 | 갭 분석 HIGH 보완 |
| 15b | [15b-gap-medium-archive.md](15b-gap-medium-archive.md) | §28 | 갭 분석 MEDIUM 보완 |
| 16 | [16-proposalforge-reviews.md](16-proposalforge-reviews.md) | §30, §31 | ProposalForge 비교 검토 |

### 역할별 읽기 가이드

| 역할 | 주요 참조 파일 | 줄 수 | 절감률 |
|------|---------------|-------|--------|
| 그래프 노드 수정 | 02 + 03 + 07 | ~690 | **92%** |
| API 엔드포인트 추가 | 08 | ~565 | **93%** |
| 프론트엔드 작업 | 09 | ~600 | **93%** |
| 프롬프트 튜닝 | 12 | ~1,100 | **87%** |
| DB 스키마 변경 | 11 | ~650 | **92%** |
| 인증/알림 | 13 | ~230 | **97%** |
| 전체 리뷰 | 전체 파일 | ~7,665 | 9% |

### 탐색 팁

- 그래프 구조 변경: `03-graph-definition.md` → `07-routing-edges.md` → `04-review-nodes.md`
- 제안서 작성 흐름: `06-proposal-workflow.md` → `12-prompts.md`
- 신규 API 추가: `08-api-endpoints.md` → `01-architecture.md` (디렉토리 구조)
