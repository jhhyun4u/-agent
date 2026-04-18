# 배포 가이드 (Deployment Guide)

## 개요

용역제안 AI 협업 플랫폼의 배포는 Staging → Production 2단계로 진행됩니다.
- **Staging 배포**: 2026-04-20 (기능 검증)
- **Production 배포**: 2026-04-25 (본격 운영)

각 환경은 독립적으로 구성되며, Railway/Render(백엔드)와 Vercel(프론트엔드) 인프라를 사용합니다.

---

## 배포 전 체크리스트

배포 2주일 전부터 다음을 확인하세요.

### 코드 준비
- [ ] 모든 테스트 통과 (단위, 통합, E2E): `uv run pytest --cov=src --cov-report=term-missing`
- [ ] 테스트 커버리지 80% 이상 달성
- [ ] Linting 및 포맷팅 통과: `uv run black . && uv run ruff check .`
- [ ] 타입 체크 통과: `uv run mypy app/`
- [ ] 보안 스캔 통과: `uv run bandit -r app/`
- [ ] 모든 기능 브랜치 main 병합 완료

### 환경 설정
- [ ] 배포 환경 변수 검증 (`.env.staging`, `.env.production`)
  - `ENVIRONMENT=staging` 또는 `ENVIRONMENT=production`
  - `ANTHROPIC_API_KEY`, `DATABASE_URL`, `SUPABASE_URL` 등 필수 키 확인
  - `AZURE_AD_CLIENT_ID`, `AZURE_AD_CLIENT_SECRET` 설정
- [ ] 데이터베이스 마이그레이션 스크립트 준비
- [ ] 백업 계획 수립 (DB 스냅샷 생성)

### 문서화
- [ ] 배포 노트 작성 (주요 변경사항, 알려진 문제)
- [ ] 롤백 절차 문서화
- [ ] 담당자 연락처 공지

---

## 단계별 배포 프로세스

### 1단계: Staging 배포 (2026-04-20)

#### 1-1. 백엔드 배포 (Railway)

```bash
# 1. 배포 브랜치 생성 및 확인
git checkout -b staging-release-2026-04-20
git log --oneline -5

# 2. 버전 업데이트 및 배포 노트 작성
# app/__init__.py에서 __version__ 업데이트
echo "4.1.0" > VERSION
git commit -am "chore: bump version to 4.1.0"

# 3. Staging 환경 변수 설정
# Railway 대시보드 > Project > Variables 에서 설정:
#   ENVIRONMENT=staging
#   ENABLE_HITL=true (수동 승인 활성화)
#   LOG_LEVEL=INFO

# 4. Railway에 푸시 (자동 배포)
git push origin staging-release-2026-04-20

# 5. Railway 빌드 로그 모니터링
# Railway Dashboard > Deployments 탭에서 상태 확인
# 예상 배포 시간: 3-5분
```

**배포 완료 확인:**
```bash
# Staging API 헬스체크
curl -X GET https://staging-api.tenopa.co.kr/health \
  -H "Content-Type: application/json"

# 응답 예시:
# {
#   "status": "healthy",
#   "version": "4.1.0",
#   "environment": "staging",
#   "timestamp": "2026-04-20T09:00:00Z"
# }
```

#### 1-2. 프론트엔드 배포 (Vercel)

```bash
# 1. 환경 변수 설정 (Vercel 대시보드)
# Project Settings > Environment Variables:
#   NEXT_PUBLIC_API_URL=https://staging-api.tenopa.co.kr
#   NEXT_PUBLIC_ENVIRONMENT=staging

# 2. Vercel에 푸시 (자동 배포)
git push origin staging-release-2026-04-20

# 3. Vercel 빌드 로그 모니터링
# Vercel Dashboard > Deployments 탭에서 상태 확인
# 예상 배포 시간: 2-3분

# 4. 프로덕션 배포 대기
# 프리뷰 URL에서 기능 테스트
# https://staging-tenopa.vercel.app
```

#### 1-3. 데이터베이스 마이그레이션

```bash
# 1. Staging 데이터베이스 마이그레이션
# Supabase 대시보드 > SQL Editor에서:
--  마이그레이션 스크립트 실행
\i database/migrations/004_performance_views.sql

# 2. 마이그레이션 로그 확인
SELECT * FROM pg_stat_statements LIMIT 10;

# 3. 데이터베이스 상태 확인
SELECT version();
```

#### 1-4. Staging 검증 (2-3시간)

| 항목 | 확인 내용 | 담당자 |
|------|---------|--------|
| API 응답 | 모든 엔드포인트 200 응답 | 백엔드 팀장 |
| UI 렌더링 | 페이지 로드 시간 < 2초 | 프론트엔드 팀장 |
| 사용자 인증 | Azure AD SSO 로그인 동작 | DevOps 담당자 |
| 워크플로 | 제안서 작성 전체 프로세스 완료 | PM |
| 알림 | Teams Webhook 메시지 전송 | 운영 담당자 |
| 로깅 | 구조화 로그 수집 확인 | 모니터링 담당자 |

---

### 2단계: Production 배포 (2026-04-25)

#### 2-1. 최종 체크

```bash
# 1. Staging 운영 5일간의 모니터링 데이터 검토
# Prometheus/Grafana 대시보드에서:
#   - 에러율: < 0.5%
#   - 응답시간 P95: < 3초
#   - CPU 사용율: < 70%

# 2. Staging에서 보고된 버그 확인
# Jira/GitHub Issues에서 critical/high 이슈 없음 확인

# 3. Production 환경 변수 재검증
# 특히 민감한 정보 (API 키, DB URL) 확인
env | grep -E "ANTHROPIC|DATABASE|SUPABASE|AZURE"
```

#### 2-2. Production 백엔드 배포

```bash
# 1. Production 배포 브랜치 생성
git checkout -b prod-release-2026-04-25
git merge staging-release-2026-04-20

# 2. Release 태그 생성
git tag -a v4.1.0 -m "Production release 2026-04-25"
git push origin prod-release-2026-04-25
git push origin v4.1.0

# 3. Railway Production 환경 설정
# Railway Dashboard > Project > Variables:
#   ENVIRONMENT=production
#   ENABLE_HITL=true
#   LOG_LEVEL=WARN (로깅 감소)
#   SENTRY_DSN=<설정 값> (에러 추적)

# 4. Railway에 푸시
git push origin prod-release-2026-04-25

# 5. 배포 모니터링 (10-15분)
# https://railway.app/project 에서 실시간 로그 확인
```

#### 2-3. Production 프론트엔드 배포

```bash
# 1. Vercel 환경 변수 업데이트
# Project Settings > Environment Variables (Production):
#   NEXT_PUBLIC_API_URL=https://api.tenopa.co.kr
#   NEXT_PUBLIC_ENVIRONMENT=production
#   NEXT_PUBLIC_GA_ID=<Google Analytics ID>

# 2. Vercel에 푸시
git push origin prod-release-2026-04-25

# 3. 배포 완료 확인 (2-3분)
# https://tenopa.co.kr 접속하여 홈페이지 확인
```

#### 2-4. Production 검증 (30분)

```bash
# 필수 검증 항목 (체크리스트)
- [ ] https://api.tenopa.co.kr/health → "healthy"
- [ ] https://tenopa.co.kr 로드 시간 < 3초
- [ ] Azure AD 로그인 동작 (demo@tenopa.co.kr)
- [ ] 제안서 생성 → 워크플로 시작 동작
- [ ] 알림 (Teams) 정상 수신
- [ ] 에러 로그 (Sentry) 모니터링 대시보드 활성화

# API 응답 시간 측정
curl -w "@curl-format.txt" -o /dev/null -s https://api.tenopa.co.kr/health
# 응답 시간 < 200ms 목표
```

---

## 배포 후 검증 항목

### 즉시 확인 (배포 후 30분)
1. **API 헬스체크**: `GET /health` → `200 OK`
2. **UI 접근성**: 웹사이트 로드 및 기본 페이지 렌더링
3. **인증**: 사용자 로그인 성공
4. **로깅**: Prometheus에서 메트릭 수집 확인

### 1시간 내 확인
1. **에러율**: Grafana 대시보드에서 5xx 에러 < 1%
2. **응답시간**: P95 응답시간 < 3초
3. **데이터 무결성**: 데이터베이스 레코드 확인
4. **알림**: Teams 채널에 배포 완료 메시지 발송

### 24시간 모니터링
1. **안정성**: 에러율 추이 확인
2. **성능**: CPU/메모리 사용율 추이
3. **사용자 피드백**: Slack/이메일에서 장애 보고 확인

---

## 트러블슈팅

### 배포 실패 시

**증상**: Railway/Vercel 빌드 실패

```bash
# 1. 로그 확인
# Railway: https://railway.app 에서 "Failed" 배포 선택
# Vercel: https://vercel.com/dashboard 에서 빌드 로그 확인

# 2. 로컬에서 재현
uv sync
uv run uvicorn app.main:app --reload

# 3. 주요 확인 항목
# - Python 버전 호환성 (3.11+)
# - 환경 변수 누락 여부
# - 의존성 버전 충돌

# 4. 문제 해결 후 다시 푸시
git push -f origin <branch-name>
```

### 데이터베이스 연결 실패

```bash
# 1. 연결 문제 확인
psql $DATABASE_URL -c "SELECT 1;"

# 2. 환경 변수 확인
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY

# 3. Supabase 상태 확인
# https://status.supabase.com
```

### 높은 응답시간

```bash
# 1. 쿼리 성능 분석
# Supabase > SQL Editor:
SELECT query, mean_time, calls 
FROM pg_stat_statements 
WHERE mean_time > 1000 
ORDER BY mean_time DESC 
LIMIT 10;

# 2. 캐시 및 인덱스 최적화
ANALYZE;
```

---

## 담당자 및 연락처

| 역할 | 담당자 | 연락처 | 시간대 |
|------|--------|---------|--------|
| DevOps Lead | (지정 예정) | Slack: #ops | 09:00-18:00 |
| 백엔드 팀장 | (지정 예정) | Slack: #backend | 09:00-18:00 |
| 프론트엔드 팀장 | (지정 예정) | Slack: #frontend | 09:00-18:00 |
| 긴급 대응 | (온콜 엔지니어) | 슬랙 @oncall | 24/7 |

---

## 롤백 절차

배포 후 심각한 버그 발견 시 즉시 이전 버전으로 롤백합니다.

```bash
# 1. 롤백 결정 (DevOps Lead + PM 승인)

# 2. Railway에서 이전 배포 선택
# Railway Dashboard > Deployments > [이전 배포] > Rollback

# 3. Vercel에서 이전 배포 선택
# Vercel Dashboard > Deployments > [이전 배포] > Promote to Production

# 4. 롤백 검증 (5분)
curl https://api.tenopa.co.kr/health

# 5. 로그 및 메트릭 확인
# Prometheus/Grafana 대시보드에서 복구 상황 확인

# 6. Post-mortem 회의 예약 (24시간 내)
```

---

## 주요 메트릭 및 알림

### Prometheus 수집 메트릭
- `http_requests_total`: 전체 요청 수
- `http_request_duration_seconds`: 요청 응답 시간
- `http_requests_errors_total`: 에러 응답 수

### 알림 기준값
| 메트릭 | 경고 | 심각 |
|--------|------|------|
| 에러율 | > 1% | > 5% |
| P95 응답시간 | > 3초 | > 5초 |
| CPU 사용율 | > 70% | > 90% |
| 메모리 사용율 | > 75% | > 95% |
| 데이터베이스 연결 | > 80 | > 95 |

---

## 문서 버전

- **버전**: 1.0
- **마지막 업데이트**: 2026-04-18
- **다음 검토**: 2026-05-18
