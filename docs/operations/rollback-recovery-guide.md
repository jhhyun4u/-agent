# 장애 대응 및 복구 가이드 (Rollback & Recovery Guide)

## 개요

프로덕션 환경에서 발생한 장애를 신속하게 감지하고, 롤백 또는 복구하는 절차를 정의합니다.
이 가이드는 장애 감지 → 근본 원인 파악 → 롤백/수정 → 사후 분석의 전체 사이클을 다룹니다.

---

## 장애 감지 절차

### 자동 감지 시스템

Prometheus Alert Rules에 의해 자동 감지되며, Slack #critical-incidents 채널에 즉시 알림됩니다.

| 감지 항목 | 조건 | 응답 시간 |
|-----------|------|---------|
| **서비스 다운** | `/health` 응답 없음 (1분) | 즉시 |
| **높은 에러율** | 5xx 에러 > 5% (5분) | 5분 |
| **느린 응답** | P95 > 2초 (10분) | 10분 |
| **DB 연결 부족** | 활성 연결 > 80% (5분) | 5분 |
| **메모리 누수** | 메모리 > 90% (10분) | 10분 |

### 수동 감지

사용자가 문제를 보고한 경우:

```bash
# 1. 문제 재현 및 확인
curl -X GET https://api.tenopa.co.kr/health -v
# 응답 확인: 200 OK vs 503 Service Unavailable

# 2. 로그 확인
# Railway/Render 대시보드에서 실시간 로그 확인
# Sentry (에러 추적) 확인: https://sentry.io/dashboard

# 3. 메트릭 확인
# Grafana 대시보드에서 에러율, 응답 시간, CPU 등 확인
```

### 장애 심각도 판단

| 심각도 | 현상 | 응답 단계 | SLA |
|--------|------|---------|-----|
| **Critical (심각)** | 서비스 완전 다운, 데이터 손실 위험 | 즉시 롤백 | 15분 |
| **High (높음)** | 부분 기능 장애, 에러율 > 5% | 5분 내 판단 | 1시간 |
| **Medium (중간)** | 성능 저하, 에러율 1-5% | 30분 내 판단 | 4시간 |
| **Low (낮음)** | 경미한 버그 | 업무 시간 내 처리 | 다음 배포 |

---

## 롤백 프로세스

### 롤백 의사결정 (5-10분 내)

```bash
# 1단계: 롤백 트리거 확인
# 다음 중 하나 이상 해당 시 즉시 롤백 진행:
# - 서비스 다운 (1분 이상)
# - 에러율 > 10%
# - 데이터 손실 가능성
# - 심각한 보안 이슈

# 2단계: 롤백 회의 (팀장 3명 이상)
# Slack: @devops_lead @backend_lead @frontend_lead
# "장애 감지: [증상] → 즉시 롤백 진행"

# 3단계: 롤백 대상 버전 확인
# 이전 배포가 안정적이었는지 확인
git log --oneline -10
# (이전 버전이 정상 운영 중이었는지 메트릭 확인)
```

### Railway 백엔드 롤백

```bash
# Option 1: Railway 대시보드 UI 사용 (권장)
# 1. Railway.app > Project > Deployments 접속
# 2. 이전 배포 찾기 (초록색 체크마크)
# 3. [···] > Rollback 클릭
# 4. "Confirm Rollback" 클릭
# 예상 시간: 3-5분

# Option 2: Railway CLI 사용
railway environment:switch production
railway deploy --environment production --to-commit <COMMIT_SHA>

# 롤백 완료 확인:
curl https://api.tenopa.co.kr/health
# 응답이 정상이면 성공
```

**Railway 롤백 확인 체크리스트:**
```
- [ ] 롤백 커밋 SHA 기록: ______________________
- [ ] 롤백 완료 시간: ______________________
- [ ] /health 응답 상태: OK / Failed
- [ ] 에러율 확인: ____%
- [ ] DB 연결 정상: Yes / No
```

### Vercel 프론트엔드 롤백

```bash
# Option 1: Vercel 대시보드 UI 사용 (권장)
# 1. Vercel Dashboard > Deployments
# 2. 이전 배포 찾기 (완료 상태)
# 3. [···] > Promote to Production 클릭
# 4. 확인: "Promote deployment to production?"
# 예상 시간: 1-2분

# Option 2: Vercel CLI 사용
vercel promote <DEPLOYMENT_URL>

# 롤백 완료 확인:
curl -I https://tenopa.co.kr
# HTTP 200 확인

# 캐시 초기화 (혹시 모르니):
curl -X POST https://api.vercel.com/v1/purge \
  -H "Authorization: Bearer $VERCEL_TOKEN"
```

**Vercel 롤백 확인 체크리스트:**
```
- [ ] 롤백 배포 ID 기록: ______________________
- [ ] 롤백 완료 시간: ______________________
- [ ] 웹사이트 접근 가능: Yes / No
- [ ] 주요 페이지 렌더링: Yes / No
- [ ] 콘솔 에러 없음: Yes / No
```

### 데이터베이스 롤백 (필요시)

```bash
# ⚠️ 극단적인 경우에만 진행. 데이터 손실 위험 높음!

# 1단계: 최근 스냅샷 확인
# Supabase > Backups 에서 최근 좋은 상태의 스냅샷 찾기

# 2단계: 스냅샷 복원
# Supabase 대시보드 > [프로젝트] > Backups
# 복원 대상 스냅샷 선택 > "Restore to project"
# 예상 시간: 10-30분

# 3단계: 데이터 검증
# 복원 후 주요 테이블 행 수 확인
psql $DATABASE_URL -c "
  SELECT 
    tablename,
    (SELECT COUNT(*) FROM 
      (SELECT 1 FROM information_schema.tables 
       WHERE table_name=tablename) AS t) as row_count
  FROM pg_tables WHERE schemaname='public'
  ORDER BY tablename;"

# 4단계: 애플리케이션 재시작
# Railway에서 서비스 재시작하여 연결 초기화
```

**⚠️ 주의사항:**
- 데이터베이스 롤백은 마지막 수단
- 스냅샷 이후 발생한 데이터 손실 (복구 불가)
- 먼저 애플리케이션만 롤백 시도

---

## 재배포 프로세스 (롤백 후 수정)

### 긴급 핫픽스 배포 (Critical 장애)

```bash
# 1단계: 원인 파악 및 수정 (30-60분)
# 프로덕션 이슈 브랜치 생성
git checkout -b hotfix/critical-issue-2026-04-25

# 2단계: 최소한의 코드 수정
# 예: 잘못된 환경 변수, 무한 루프 등
# → 수정 내용을 1개 파일, 5-10줄로 제한

# 3단계: 로컬 테스트 (필수!)
uv run pytest -k "test_critical_path" --tb=short
# 또는 최소 수동 테스트
uv run uvicorn app.main:app --reload
# http://localhost:8000/health 확인

# 4단계: 긴급 배포
git add app/services/...py
git commit -m "hotfix: [심각한 버그] 원인 설명 (Critical)"
git push origin hotfix/critical-issue-2026-04-25

# Railway가 자동 배포
# 배포 완료 후 메인 브랜치에 병합
git checkout main
git merge hotfix/critical-issue-2026-04-25
git push origin main

# 5단계: 배포 검증 (5-10분)
curl https://api.tenopa.co.kr/health
# Grafana 메트릭 정상화 확인
```

### 정상 배포 사이클 (High/Medium 장애)

```bash
# 1단계: 이슈 브랜치 생성
git checkout -b fix/issue-description

# 2단계: 코드 수정 + 테스트 작성
# 예: 보류 중인 쿼리, 대용량 응답 등

# 3단계: Pull Request 생성
# 제목: "fix: [설명]"
# 설명: 장애 현상, 근본 원인, 수정 내용
# 코드 리뷰 진행 (최소 1명)

# 4단계: Staging에서 검증
# PR을 staging 브랜치에 병합
git checkout staging-release-2026-04-20
git merge fix/issue-description
git push origin staging-release-2026-04-20

# Railway 자동 배포 후 1시간 모니터링

# 5단계: Production 배포
git checkout main
git merge fix/issue-description
git push origin main

# 6단계: 배포 후 모니터링 (2시간)
```

---

## 사후 분석 (Post-mortem) 템플릿

### 장애 사후 분석 회의 (장애 발생 후 24시간 내)

```markdown
# Post-mortem: [장애명]
**날짜**: 2026-04-25
**심각도**: [Critical / High / Medium]
**담당자**: [이름], [이름]

## 1. 개요
- **발생 시간**: 2026-04-25 14:30 UTC
- **감지 시간**: 2026-04-25 14:32 (2분)
- **롤백 시간**: 2026-04-25 14:38 (6분)
- **복구 시간**: 2026-04-25 15:15 (45분)
- **영향 범위**: 제안서 작성 기능, ~50명 사용자

## 2. 근본 원인 (Root Cause)
[5 Why 분석]
1. 백엔드 서버 메모리 누수 발생
2. → 새 배포의 LangGraph 상태 저장 로직에서 메모리 해제 누락
3. → → 특정 엣지 경로에서 상태 객체가 계속 누적
4. → → → 2시간 운영 후 메모리 > 95%
5. → → → → → 서비스 다운 (OOM Kill)

**근본 원인**: 상태 객체 메모리 누수 (PR #2425)

## 3. 영향도
- **사용자 영향**: 50명, 15개 진행 중 제안서 중단
- **데이터 손실**: 없음 (DB에 저장됨)
- **비용 영향**: ~$50 (추가 인프라)

## 4. 타임라인

| 시간 | 이벤트 | 담당자 |
|------|--------|--------|
| 14:30 | 배포 완료 (v4.1.1) | DevOps |
| 14:32 | Prometheus Alert 발생 (메모리 > 90%) | 모니터링 |
| 14:35 | Slack 알림 수신 + 팀 집결 | Ops |
| 14:38 | 롤백 결정 및 시작 | DevOps |
| 14:43 | 롤백 완료, 서비스 정상화 | DevOps |
| 15:15 | 핫픽스 배포 (PR #2429) | Backend |
| 15:30 | 메트릭 정상화 확인 | Ops |

## 5. 대응 조치
- ✅ 롤백 완료 (6분)
- ✅ 메모리 누수 원인 파악 (30분)
- ✅ 핫픽스 코드 작성 및 검토 (45분)
- ✅ 프로덕션 재배포 (15분)

## 6. 근본 원인 분석 및 개선

### 감지 실패 분석
- **문제**: 배포 직후 메모리 모니터링이 충분하지 않음
- **개선**: 배포 후 30분 메모리 추이를 명시적으로 확인하는 체크리스트 추가

### 코드 리뷰 개선
- **문제**: PR #2425에서 상태 객체 메모리 해제 누락을 감지하지 못함
- **개선**: 메모리 누수 위험 코드에 대한 자동 스캔 추가 (bandit 확장)

### 테스트 개선
- **문제**: 장시간 운영 테스트 (load test) 부족
- **개선**: CI/CD에 1시간 load test 추가

## 7. 액션 아이템

| 항목 | 담당자 | 기한 | 상태 |
|------|--------|------|------|
| LangGraph 메모리 누수 fix | 백엔드팀 | 2026-04-26 | 완료 |
| 배포 후 메모리 체크리스트 추가 | DevOps | 2026-04-27 | 진행 중 |
| Load test 자동화 추가 | 백엔드팀 | 2026-05-02 | 예정 |
| 메모리 프로파일링 도구 도입 | 인프라팀 | 2026-05-10 | 예정 |

## 8. 예방 방안
1. **배포 전 메모리 프로파일링** 필수
   - Staging에서 최소 30분 load test 실행
   - 메모리 증가율 < 1MB/분 기준

2. **자동 메모리 누수 감지**
   - Prometheus rule: `memory > 85%` → Alert (10분)
   - 대시보드에서 메모리 증가 추이 시각화

3. **코드 리뷰 강화**
   - 장시간 실행 객체의 메모리 해제 명시 확인
   - PR template에 "메모리 누수 확인" 항목 추가

## 결론
45분 내 복구했으나, 배포 전 테스트 강화로 예방 가능했습니다.
향후 모든 배포는 최소 30분의 load test를 필수 조건으로 합니다.
```

### Post-mortem 회의 준비

**회의 일정:**
```bash
# 장애 발생 후 24시간 내 개최
# 예: 장애 발생 2026-04-25 14:30 → 회의 2026-04-26 10:00

# 참석자:
# - DevOps Lead (의장)
# - 백엔드 팀장
# - QA 담당자
# - PM

# 준비물:
# 1. 배포 로그 (Railway/Vercel)
# 2. 메트릭 그래프 (Grafana)
# 3. 에러 로그 (Sentry)
# 4. 사용자 피드백 (Slack 정리)
```

**회의 산출물:**
- Post-mortem 문서 (위 템플릿)
- 액션 아이템 리스트 (JIRA/GitHub Issues)
- 팀 커뮤니케이션 (Slack 공유)

---

## 트러블슈팅

### 롤백이 작동하지 않는 경우

```bash
# 1. Railway 상태 확인
# Railway Status: https://status.railway.app

# 2. 롤백 목표 버전이 정상인지 재확인
# 메트릭 기록 검토 (이전 배포도 에러율 높았을 수 있음)

# 3. 수동 롤백 시도
git log --oneline -20
git revert HEAD
git push origin main

# 4. 최악의 경우: 알려진 좋은 버전으로 강제 배포
git reset --hard v4.0.5
git push -f origin main  # ⚠️ 매우 위험, 승인 필수
```

### 데이터베이스 연결 실패

```bash
# 1. 환경 변수 확인
echo $DATABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY

# 2. 연결 테스트
psql $DATABASE_URL -c "SELECT 1;"

# 3. Supabase 상태 확인
# https://status.supabase.com

# 4. 마이그레이션 상태 확인 (Supabase에서 recent migration 확인)
```

---

## 담당자 및 연락처

| 역할 | 담당자 | 연락처 | 응답시간 |
|------|--------|---------|---------|
| DevOps Lead (의장) | (지정 예정) | Slack: @devops_lead | 즉시 |
| 백엔드 팀장 | (지정 예정) | Slack: @backend_lead | 5분 |
| 인프라 담당 | (지정 예정) | Slack: @infra | 10분 |
| 긴급 대응팀 | 온콜 엔지니어 | PagerDuty | 즉시 |

**긴급 연락:**
- Slack: #critical-incidents (자동 알림)
- 전화: 긴급 담당자 비상 연락처

---

## 관련 문서

- `deployment-guide.md` - 배포 프로세스
- `monitoring-guide.md` - 모니터링 설정
- 긴급 대응 플레이북 (별도 문서)

---

## 문서 버전

- **버전**: 1.0
- **마지막 업데이트**: 2026-04-18
- **다음 검토**: 2026-05-18
