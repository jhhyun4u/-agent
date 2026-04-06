# 용역제안 Coworker

> 프로젝트 수주 성공률을 높이는 AI Coworker

RFP(제안요청서) 분석부터 전략 수립, 제안서 작성까지 — AI 동료와 함께하는 용역 제안 플랫폼입니다.

## 기능

- **RFP 업로드 분석**: PDF/DOCX 형식의 RFP 파일을 업로드하면 자동으로 핵심 정보를 추출합니다.
- **직접 입력**: 프로젝트명, 범위, 기간 등을 직접 입력하여 제안서를 생성할 수 있습니다.
- **DOCX 제안서 생성**: 섹션별로 구조화된 Word 제안서를 생성합니다.
- **PPTX 요약본 생성**: 프레젠테이션용 PPT 요약본을 함께 생성합니다.

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.11, FastAPI, LangGraph |
| Frontend | Next.js 15, React 19, TypeScript |
| AI | Anthropic Claude API |
| DB | Supabase (PostgreSQL + Auth + pgvector) |
| 인증 | Azure AD (Entra ID) SSO |
| 패키지 | uv (Python), npm (Node.js) |

## 로컬 개발

### 사전 요구사항
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 패키지 매니저
- Node.js 20+

### 백엔드

```bash
uv sync                                # 의존성 설치
cp .env.example .env                   # 환경변수 설정
uv run uvicorn app.main:app --reload   # 개발 서버 (http://localhost:8000)
```

### 프론트엔드

```bash
cd frontend
cp .env.local.example .env.local       # 환경변수 설정
npm install                            # 의존성 설치
npm run dev                            # 개발 서버 (http://localhost:3000)
```

### Docker Compose (통합 환경)

```bash
docker compose up -d                   # 백엔드 + PostgreSQL + 프론트엔드
docker compose logs -f backend         # 로그 확인
docker compose down                    # 종료
```

## 테스트

```bash
uv run pytest tests/unit/ -v           # 백엔드 유닛 테스트
cd frontend && npm run lint            # 프론트엔드 린트
cd frontend && npm run build           # TypeScript 빌드 검증
```

## 프로덕션 배포

### 아키텍처

```
[Vercel] ← Frontend (Next.js)
    ↓ API 호출
[Railway] ← Backend (FastAPI + Docker)
    ↓ DB 연결
[Supabase] ← PostgreSQL + Auth + Storage
```

### 1. Supabase 설정

1. [Supabase](https://supabase.com)에서 프로젝트 생성
2. SQL Editor에서 `database/schema_v3.4.sql` 실행
3. `database/migrations/` 내 SQL 파일을 순서대로 실행 (004 → 011)
4. 프로젝트 URL과 키 확보 (Settings → API)

자세한 설정은 `docs/SUPABASE_SETUP.md` 참조.

### 2. 백엔드 배포 (Railway)

1. [Railway](https://railway.app)에서 GitHub 저장소 연결
2. 환경변수 설정 (`.env.production.example` 참조):
   - `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
   - `FRONTEND_URL`, `CORS_ORIGINS` (프론트 URL)
   - `LOG_FORMAT=json`, `LOG_LEVEL=WARNING`
3. Railway가 `Dockerfile`을 자동 감지하여 빌드·배포
4. 배포 후 `https://<your-app>.railway.app/health` 확인

### 3. 프론트엔드 배포 (Vercel)

1. [Vercel](https://vercel.com)에서 GitHub 저장소 연결
2. Framework: Next.js, Root Directory: `frontend`
3. 환경변수 설정:
   - `NEXT_PUBLIC_API_URL` = Railway 백엔드 URL + `/api`
   - `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
4. 배포 후 도메인 확인

### 4. CI/CD

- **CI**: PR 또는 main push 시 자동 실행 (`.github/workflows/ci.yml`)
  - 백엔드: 구문 검사 + 유닛 테스트
  - 프론트엔드: ESLint + TypeScript 빌드
- **CD**: main 머지 시 Railway 자동 배포 (`.github/workflows/deploy.yml`)
  - GitHub Secrets에 `RAILWAY_TOKEN` 등록 필요

### 5. DB 마이그레이션

신규 마이그레이션 적용 시:
```bash
# Supabase SQL Editor에서 직접 실행
# database/migrations/ 내 해당 SQL 파일 내용 복사 → 실행
```

### 환경변수 체크리스트

| 변수 | 백엔드 | 프론트 | 필수 |
|------|:------:|:------:|:----:|
| ANTHROPIC_API_KEY | O | - | O |
| SUPABASE_URL | O | - | O |
| SUPABASE_KEY | O | - | O |
| SUPABASE_SERVICE_ROLE_KEY | O | - | O |
| FRONTEND_URL | O | - | O |
| CORS_ORIGINS | O | - | O |
| NEXT_PUBLIC_API_URL | - | O | O |
| NEXT_PUBLIC_SUPABASE_URL | - | O | O |
| NEXT_PUBLIC_SUPABASE_ANON_KEY | - | O | O |
| AZURE_AD_* | O | - | SSO 사용 시 |
| G2B_API_KEY | O | - | G2B 연동 시 |
| TEAMS_WEBHOOK_URL | O | - | 알림 사용 시 |
| LOG_FORMAT | O | - | 권장: json |
| LOG_LEVEL | O | - | 권장: WARNING |

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/proposals/from-rfp` | RFP 파일 업로드 기반 제안서 생성 |
| POST | `/api/proposals/from-input` | 직접 입력 기반 제안서 생성 |
| GET | `/api/proposals/{id}/download` | 생성된 문서 다운로드 |
| GET | `/health` | 헬스 체크 |
| GET | `/status` | 서버 상태 (버전, 활성 세션) |
