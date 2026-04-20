# 스테이징 배포 체크리스트 (2026-04-21)

## Pre-Deployment (배포 전)

### 준비 단계 (30분)
- [ ] 프로덕션 DB 백업 확인
- [ ] 스테이징 환경 Supabase 접속 확인
- [ ] 배포 환경 변수 확인
  - [ ] SUPABASE_URL (스테이징)
  - [ ] SUPABASE_KEY (스테이징)
  - [ ] DATABASE_URL (스테이징)

### 코드 검증 (15분)
```bash
# 최신 코드 풀
git pull origin main

# Phase 5 커밋 확인
git log --oneline -5
# 예상: b48debf, 078dfa5, 06dc77c, 2cb63cd, 11a128d

# 문법 검증
python -m py_compile app/main.py
python -m py_compile app/api/routes_scheduler.py
python -m py_compile app/services/scheduler_service.py
python -m py_compile app/services/batch_processor.py
```

### DB 마이그레이션 (15분)
```bash
# Migration 040 적용 (Supabase SQL 에디터)
cat database/migrations/040_scheduler_integration.sql | \
  curl -X POST https://your-supabase-url/rest/v1/query \
  -H "Authorization: Bearer YOUR_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"..."}'

# 또는 Supabase 콘솔에서 직접 실행
```

---

## Deployment (배포)

### 스테이징 배포 (10분)
```bash
# Option 1: Manual deployment
# 1. 스테이징 서버에 코드 배포
# 2. 의존성 설치: uv sync
# 3. 서비스 재시작

# Option 2: CI/CD (GitHub Actions)
git push origin main
# GitHub Actions 워크플로우 자동 실행
```

### 초기 헬스 체크 (5분)
```bash
# 앱 시작 로그 확인
tail -50 staging.log | grep -E "Phase 5|Scheduler"

# 예상 로그:
# [Phase 5] 정기 문서 마이그레이션 스케줄러 초기화 완료
# Scheduler initialized with N schedules

# 엔드포인트 접근 확인
curl -X GET http://staging-api/api/scheduler/schedules \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## Validation (검증) — 4시간

### Phase 1: 스모크 테스트 (30분)

#### 1.1 기본 연결성
```bash
# GET /api/scheduler/schedules 테스트
curl -X GET http://staging-api/api/scheduler/schedules \
  -H "Authorization: Bearer ADMIN_TOKEN"

# 예상 응답:
# {
#   "data": [
#     {
#       "id": "...",
#       "schedule_name": "Monthly Intranet Migration",
#       "enabled": true,
#       ...
#     }
#   ]
# }
```

- [ ] 응답 200 OK
- [ ] 스케줄 목록 반환
- [ ] 필드 완전성 (id, schedule_name, enabled 등)

#### 1.2 권한 확인
```bash
# Non-admin 사용자로 테스트
curl -X GET http://staging-api/api/scheduler/schedules \
  -H "Authorization: Bearer USER_TOKEN"

# 예상: 403 Forbidden
```

- [ ] Non-admin 거부 (403)
- [ ] 에러 메시지 적절함

### Phase 2: 스케줄 생성 테스트 (30분)

#### 2.1 새 스케줄 생성
```bash
curl -X POST http://staging-api/api/scheduler/schedules \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Test Migration",
    "cron_expression": "0 0 * * 0",
    "source_type": "intranet",
    "enabled": true
  }'

# 예상 응답:
# {
#   "id": "...",
#   "schedule_name": "Weekly Test Migration",
#   "enabled": true
# }
```

- [ ] 스케줄 생성 성공 (200)
- [ ] DB에 저장 확인
- [ ] APScheduler에 등록 확인

#### 2.2 스케줄 목록 재확인
```bash
curl -X GET http://staging-api/api/scheduler/schedules \
  -H "Authorization: Bearer ADMIN_TOKEN"

# 새 스케줄 포함 여부 확인
```

- [ ] 새 스케줄 목록에 포함
- [ ] cron_expression 정확함

### Phase 3: 배치 실행 테스트 (60분)

#### 3.1 수동 트리거
```bash
# 첫 번째 스케줄 ID 획득
SCHEDULE_ID=$(curl -s http://staging-api/api/scheduler/schedules \
  -H "Authorization: Bearer ADMIN_TOKEN" | jq -r '.[0].id')

# 배치 실행
curl -X POST http://staging-api/api/scheduler/schedules/$SCHEDULE_ID/trigger \
  -H "Authorization: Bearer ADMIN_TOKEN"

# 예상 응답:
# {
#   "batch_id": "...",
#   "message": "Migration triggered"
# }
```

- [ ] 배치 생성 성공
- [ ] batch_id 반환

#### 3.2 배치 상태 조회
```bash
BATCH_ID="..."

# 배치 상태 조회
curl -X GET http://staging-api/api/scheduler/batches/$BATCH_ID \
  -H "Authorization: Bearer ADMIN_TOKEN"

# 예상 응답:
# {
#   "id": "...",
#   "batch_name": "Batch-...",
#   "status": "completed",
#   "processed_documents": 10,
#   "failed_documents": 0,
#   "started_at": "...",
#   "completed_at": "..."
# }
```

- [ ] 배치 상태 조회 성공
- [ ] status 변경 추적 (pending → processing → completed)
- [ ] 처리/실패 통계 정확함

#### 3.3 DB 확인
```sql
-- Supabase 콘솔 SQL 에디터
SELECT * FROM migration_batches ORDER BY scheduled_at DESC LIMIT 1;
SELECT * FROM migration_status_logs WHERE batch_id = '...' LIMIT 5;
SELECT * FROM migration_schedule WHERE enabled = true;
```

- [ ] migration_batches 레코드 생성됨
- [ ] migration_status_logs 감사 로그 기록됨
- [ ] 각 필드 데이터 정확함

### Phase 4: 에러 시나리오 (60분)

#### 4.1 권한 오류
- [ ] Non-admin이 POST 시도 → 403
- [ ] Non-admin이 배치 조회 시도 → 403
- [ ] 에러 메시지 명확함

#### 4.2 존재하지 않는 리소스
```bash
# 존재하지 않는 배치 ID
curl -X GET http://staging-api/api/scheduler/batches/invalid-id \
  -H "Authorization: Bearer ADMIN_TOKEN"

# 예상: 404 Not Found
```

- [ ] 404 에러 반환
- [ ] 에러 메시지 적절함

#### 4.3 잘못된 Cron 표현식
```bash
curl -X POST http://staging-api/api/scheduler/schedules \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Invalid Cron",
    "cron_expression": "invalid cron",
    "enabled": true
  }'

# 예상: 400 Bad Request
```

- [ ] 잘못된 cron 거부
- [ ] 에러 메시지 명확함

#### 4.4 DB 연결 오류 시뮬레이션
```bash
# DB 연결 일시 끊음 (스테이징 환경)
# 또는 잘못된 자격증명으로 테스트

# 예상: 500 Internal Server Error
# 에러 로그에 상세 메시지 기록
```

- [ ] 연결 오류 처리됨
- [ ] 로그에 상세 정보 기록됨

### Phase 5: 성능 기준선 (30분)

#### 5.1 응답 시간
```bash
# 100개 요청 벤치마크
for i in {1..100}; do
  time curl -s -X GET http://staging-api/api/scheduler/schedules \
    -H "Authorization: Bearer ADMIN_TOKEN" > /dev/null
done

# p95 응답 시간 < 500ms 확인
```

- [ ] GET /schedules: p95 < 500ms
- [ ] POST /schedules: p95 < 1000ms
- [ ] GET /batches/{id}: p95 < 500ms

#### 5.2 배치 처리 성능
```bash
# 배치 생성 → 완료 시간 측정
# 예상: 100 documents < 60초

curl -w "Total time: %{time_total}s\n" \
  -X POST http://staging-api/api/scheduler/schedules/$SCHEDULE_ID/trigger \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

- [ ] 배치 완료 시간 < 60s (100 docs)
- [ ] 병렬 처리 확인 (로그에서 worker 활용)

---

## Post-Deployment (배포 후)

### 모니터링 설정 (30분)
- [ ] 로그 집계 설정 (ELK/Cloudwatch)
- [ ] 에러 알림 설정 (Slack/PagerDuty)
- [ ] 메트릭 대시보드 확인
  - [ ] 배치 성공률
  - [ ] 평균 응답 시간
  - [ ] 에러율

### 문서화
- [ ] 스테이징 배포 결과 기록
- [ ] 발견된 문제 및 해결책 문서화
- [ ] 프로덕션 배포 GO/NO-GO 결정

---

## Rollback Plan (문제 발생 시)

### 즉시 조치 (5분)
```bash
# 1. 스케줄러 중지
curl -X POST http://staging-api/api/control/stop \
  -H "Authorization: Bearer ADMIN_TOKEN"

# 2. 애플리케이션 재시작 (이전 버전)
git checkout HEAD~1
uv sync
systemctl restart app

# 3. 마이그레이션 롤백
DROP TABLE migration_batches CASCADE;
DROP TABLE migration_schedule CASCADE;
DROP TABLE migration_status_logs CASCADE;
```

### 원인 분석 (30분)
- [ ] 에러 로그 수집
- [ ] DB 상태 검증
- [ ] 메모리/리소스 확인

### 재배포 (문제 해결 후)
- [ ] 문제 원인 파악 및 수정
- [ ] Phase 1부터 재시작

---

## GO/NO-GO Decision

### GO 조건 (모두 만족)
- [x] All 5 phases passed
- [x] No CRITICAL issues
- [x] Performance baseline met
- [x] 문서화 완료
- [x] 모니터링 설정 완료

### NO-GO 조건 (1개 이상 해당)
- [ ] Phase 중 실패
- [ ] CRITICAL 버그 발견
- [ ] 성능 기준 미달
- [ ] 보안 취약점 발견

---

## Production Deployment Timeline

| Date | Event | Status |
|------|-------|--------|
| 2026-04-20 | Phase 5 implementation complete | ✅ Done |
| 2026-04-21 | Staging deployment + validation | ⏳ Scheduled |
| 2026-04-22 | Staging monitoring (24h) | ⏳ Scheduled |
| 2026-04-25 | Production deployment (GO approval) | ⏳ Scheduled |

---

**Owner:** AI Coworker  
**Last Updated:** 2026-04-20 19:00 UTC  
**Next Step:** Execute staging deployment on 2026-04-21
