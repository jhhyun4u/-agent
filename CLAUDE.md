# TENOPA Intranet — 용역제안 AI Coworker

## 프로젝트 개요
TENOPA 내부 직원이 활용하는 **용역제안 Knowledge Base 플랫폼**. 용역과제 모니터링과 제안서 공동 작성을 수행하는 **AI Coworker**(에이전트)가 사람과 협업한다. 프로젝트를 거듭할수록 조직 지식(역량·콘텐츠·발주기관·경쟁사·교훈)이 축적되어 다음 제안의 품질이 올라가는 선순환 구조. 부서/팀 단위 운영, 역할 기반 접근 제어, 결재선, 성과 추적 지원.

## 기술 스택
- Python 3.11+ / FastAPI (Backend — Railway/Render)
- Next.js (Frontend — Vercel)
- LangGraph (StateGraph + interrupt + PostgresSaver)
- Anthropic Claude API (claude-sonnet-4-5-20250929)
- Supabase (PostgreSQL + Auth + RLS + Storage)
- Azure AD (Entra ID) — MS365 SSO
- Teams Incoming Webhook — 알림
- PyPDF2, python-docx, python-pptx
- 패키지 관리: uv

## 주요 명령어
```bash
uv sync                              # 의존성 설치
uv run uvicorn app.main:app --reload  # 개발 서버 실행
uv run pytest                         # 테스트 실행
```

## 구조
- `app/api/routes_auth.py` — 인증 (Azure AD SSO)
- `app/api/routes_users.py` — 사용자·조직·팀 관리
- `app/api/routes_proposal.py` — 제안 프로젝트 CRUD
- `app/api/routes_workflow.py` — 워크플로 실행·재개 + SSE
- `app/api/routes_dashboard.py` — 역할별 대시보드
- `app/api/routes_notification.py` — 알림 관리
- `app/graph/` — LangGraph StateGraph (state, nodes, edges)
- `app/services/` — rfp_parser, claude_client, auth_service, approval_chain, notification_service, knowledge_search 등
- `app/models/schemas.py` — Pydantic 스키마
- `app/models/db.py` — Supabase PostgreSQL 연결
- `app/prompts/` — 단계별 프롬프트 템플릿

## 코드 컨벤션
- 한국어 docstring 및 주석
- Pydantic v2 스타일 사용
- async/await 패턴 (FastAPI)
