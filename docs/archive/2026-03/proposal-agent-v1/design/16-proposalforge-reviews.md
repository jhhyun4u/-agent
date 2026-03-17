# ProposalForge 비교 검토

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [12-prompts.md](12-prompts.md), [09-frontend.md](09-frontend.md)
> **원본 섹션**: §30, §31

---

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

---
