# Staging 강제 재배포 가이드

**목표:** Staging 서버에 최신 scheduler health endpoint 코드 배포  
**Root Cause:** Staging 서버가 outdated code 실행 중  
**Fix:** Latest staging branch (5f617f1) 배포

---

## 재배포 방법 선택

### **방법 A: Railway/Render 자동 배포 (권장)**

```bash
# Staging이 연결된 배포 플랫폼 확인
# Railway / Render / Heroku 등

# 1. staging 브랜치의 최신 커밋 확인
git log -1 --oneline staging
# Output: 5f617f1 docs: Phase 5 production deployment preparation

# 2. Staging 환경에 최신 코드 푸시
git push origin staging --force

# 3. 자동 배포 트리거
# → CI/CD pipeline automatically re-deploys from staging branch

# 4. 배포 상태 확인
# → Check deployment logs in Railway/Render dashboard
```

### **방법 B: 수동 SSH 배포**

```bash
# 1. Staging 서버에 SSH 접속
ssh deploy@staging-api.tenopa.co

# 2. 최신 코드 가져오기
cd /app
git fetch origin
git checkout staging
git pull origin staging

# 3. 의존성 업데이트
uv sync

# 4. 서비스 재시작
systemctl restart tenopa-api-staging

# 또는 Docker 사용 시:
docker pull tenopa-staging:latest
docker stop tenopa-staging
docker run -d --name tenopa-staging tenopa-staging:latest
```

### **방법 C: 컨테이너 이미지 재빌드**

```bash
# 1. Staging 이미지 빌드 (latest staging 코드로)
docker build -t tenopa-staging:latest --build-arg BRANCH=staging .

# 2. 컨테이너 중지 및 제거
docker stop tenopa-staging
docker rm tenopa-staging

# 3. 새 이미지로 실행
docker run -d \
  --name tenopa-staging \
  -p 8000:8000 \
  -e SUPABASE_URL=[...] \
  -e SUPABASE_KEY=[...] \
  tenopa-staging:latest

# 4. 상태 확인
curl http://localhost:8000/api/scheduler/health
```

---

## 배포 후 검증

### **1단계: 즉시 확인 (배포 후 1분)**

```bash
# Health endpoint 확인
curl -v https://staging-api.tenopa.co/api/scheduler/health

# Expected response:
# HTTP/1.1 200 OK
# {"status": "ok", "service": "scheduler"}
```

### **2단계: 기능 테스트 (배포 후 5분)**

```bash
# 로컬에서 staging API에 대해 실행
python -c "
import requests
import json

BASE_URL = 'https://staging-api.tenopa.co'
TOKEN = 'Bearer [your-token]'  # Replace with actual token

# Test 1: Health check
resp = requests.get(f'{BASE_URL}/api/scheduler/health')
print(f'Health: {resp.status_code} {resp.text}')

# Test 2: List schedules
resp = requests.get(
    f'{BASE_URL}/api/scheduler/schedules',
    headers={'Authorization': TOKEN}
)
print(f'Schedules: {resp.status_code}')

# Test 3: Create test schedule
resp = requests.post(
    f'{BASE_URL}/api/scheduler/schedules',
    headers={'Authorization': TOKEN},
    json={
        'name': 'test-schedule',
        'cron_expression': '0 12 * * *',
        'enabled': True
    }
)
print(f'Create: {resp.status_code}')
if resp.status_code == 200:
    print(f'Created schedule ID: {resp.json().get(\"id\")}')
"
```

### **3단계: 로그 확인 (배포 후 10분)**

```bash
# 배포 로그 확인
# Railway dashboard → Deployments → [latest]
# 또는
# SSH로 서버 접속해 로그 확인:
tail -100 /var/log/tenopa-api.log | grep -i scheduler

# 에러 로그 확인
tail -100 /var/log/tenopa-api.log | grep -i error

# 성공 표시:
# [INFO] Scheduler initialized with X schedules
# [INFO] GET /api/scheduler/health 200 OK
```

### **4단계: 모니터링 데이터 수집 (배포 후 1시간)**

```bash
# 1시간 동안 매 5분마다 health check
for i in {1..12}; do
    echo "Check $i at $(date)"
    curl -s https://staging-api.tenopa.co/api/scheduler/health
    echo ""
    sleep 300
done > staging_health_check_$(date +%Y%m%d_%H%M%S).log
```

---

## 재배포 체크리스트

### 배포 전 (Pre-Deployment)
- [ ] Staging 브랜치 최신 상태 확인
  ```bash
  git log -1 staging  # Should be 5f617f1 or later
  ```
- [ ] Routes_scheduler 엔드포인트 코드 확인
  ```bash
  grep -n "@router.get\(\"/health\"\)" app/api/routes_scheduler.py
  ```
- [ ] Main.py에 scheduler_router 등록 확인
  ```bash
  grep -n "scheduler_router" app/main.py
  ```
- [ ] 로컬 테스트 통과 확인
  ```bash
  pytest tests/test_scheduler_integration.py -v
  ```

### 배포 중 (During Deployment)
- [ ] Staging branch 최신 코드 푸시 또는 수동 배포
- [ ] 배포 로그 모니터링 (에러 확인)
- [ ] 서비스 재시작 완료 대기 (2-3분)

### 배포 후 (Post-Deployment)
- [ ] `/api/scheduler/health` endpoint 응답 확인 (200 OK)
- [ ] 기능 테스트 (schedule 생성, 조회)
- [ ] 로그에 에러 없음 확인
- [ ] 1시간 모니터링 데이터 수집
- [ ] PHASE5_MONITORING_STATUS.jsonl 업데이트

---

## 예상 영향

**영향 범위:** Staging 환경만  
**다운타임:** 2-5분 (서비스 재시작)  
**Rollback:** Git checkout previous commit → Restart  
**Risk Level:** LOW (코드 변경은 없고 배포만 함)

---

## 실패 시 대응

| 증상 | 원인 | 대응 |
|------|------|------|
| 여전히 404 | 배포되지 않음 | 배포 로그 확인, 수동 배포 재시도 |
| 502 Bad Gateway | 앱 크래시 | 로그 확인, 의존성 문제 해결 |
| 500 Internal Error | 런타임 에러 | 로그에서 상세 에러 메시지 확인 |
| 느린 응답 | 리소스 부족 | 메모리/CPU 확인, 캐시 정리 |

---

## 예상 소요 시간

| Phase | Duration |
|-------|----------|
| 배포 | 2-3 minutes |
| 서비스 시작 | 1-2 minutes |
| 헬스 체크 | < 1 minute |
| 기능 테스트 | 2-3 minutes |
| 1시간 모니터링 | 1 hour |
| **총합** | **~75 minutes** |

---

## 연락처

배포 중 문제 발생 시:
- On-Call Engineer: [Contact]
- DevOps Team: [Contact]
- #tenopa-staging (Slack)

---

**Generated:** 2026-04-22  
**Target Deployment:** Immediately (before production deployment on 2026-04-25)
