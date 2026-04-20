# Phase 5 Staging Deployment — 실시간 실행 명령어

**생성 시각:** 2026-04-20 19:00 UTC  
**상태:** 코드 배포 완료 ✅  
**다음:** 스테이징 환경에서 아래 명령 실행  

---

## 🔴 STEP 1: 스테이징 DB 백업 (5분)

**Supabase 대시보드 사용:**
```
1. https://supabase.com/dashboard 접속
2. 스테이징 프로젝트 선택
3. Database > Backups 메뉴
4. "Create backup" 클릭
5. 완료 대기 (2-5분)
```

**또는 Command Line:**
```bash
# 스테이징 서버에서 실행
pg_dump --format custom \
  -f staging_backup_$(date +%Y%m%d_%H%M%S).bak \
  "postgresql://[USER]:[PASSWORD]@[HOST]:[PORT]/[DATABASE]"

# 백업 확인
ls -lh staging_backup_*.bak
```

✅ **완료 후 다음 단계로**

---

## 🔴 STEP 2: 데이터베이스 마이그레이션 (2분)

**Supabase SQL 에디터 (권장):**
```
1. Supabase Dashboard > SQL Editor
2. "New Query" 클릭
3. 아래 SQL을 복사해서 붙여넣기
4. "Run" 클릭
```

**또는 Command Line:**
```bash
psql -h [HOST] -U [USER] -d [DATABASE] \
  -f database/migrations/006_scheduler_integration.sql
```

**실행할 SQL:**
```sql
-- Migration 006: Scheduler Integration Tables
-- Created: 2026-04-20
-- Purpose: Add tables for document migration scheduling and batch tracking

-- 1. Migration Schedules Table
CREATE TABLE IF NOT EXISTS migration_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    cron_expression VARCHAR(50) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    CONSTRAINT valid_cron CHECK (cron_expression ~ '^\d+ \d+ \d+ \d+ \d+$')
);

CREATE INDEX idx_migration_schedules_enabled ON migration_schedules(enabled);
CREATE INDEX idx_migration_schedules_created ON migration_schedules(created_at DESC);

-- 2. Migration Batches Table
CREATE TABLE IF NOT EXISTS migration_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES migration_schedules(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    total_documents INT NOT NULL DEFAULT 0,
    processed_documents INT NOT NULL DEFAULT 0,
    failed_documents INT NOT NULL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'success', 'partial', 'failed')),
    CONSTRAINT valid_counts CHECK (
        total_documents >= 0 AND
        processed_documents >= 0 AND
        failed_documents >= 0 AND
        processed_documents + failed_documents <= total_documents
    )
);

CREATE INDEX idx_migration_batches_schedule ON migration_batches(schedule_id);
CREATE INDEX idx_migration_batches_status ON migration_batches(status);
CREATE INDEX idx_migration_batches_created ON migration_batches(created_at DESC);

-- 3. Migration Logs Table
CREATE TABLE IF NOT EXISTS migration_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES migration_batches(id) ON DELETE CASCADE,
    source_document_id VARCHAR(100) NOT NULL,
    document_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    retry_count INT NOT NULL DEFAULT 0,
    processed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    CONSTRAINT valid_status CHECK (status IN ('success', 'failed', 'skipped'))
);

CREATE INDEX idx_migration_logs_batch ON migration_logs(batch_id);
CREATE INDEX idx_migration_logs_status ON migration_logs(status);
CREATE INDEX idx_migration_logs_document ON migration_logs(source_document_id);

-- Add comments for documentation
COMMENT ON TABLE migration_schedules IS 'Stores schedule configurations for automatic document migration';
COMMENT ON TABLE migration_batches IS 'Tracks batch execution results and status';
COMMENT ON TABLE migration_logs IS 'Records individual document processing results per batch';

-- Commit confirmation
SELECT NOW() as migration_completed;
```

**마이그레이션 완료 확인:**
```sql
-- 테이블 생성 확인
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'migration%'
ORDER BY table_name;

-- 결과 (3개 테이블):
-- migration_batches
-- migration_logs
-- migration_schedules

-- 인덱스 생성 확인
SELECT indexname 
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename LIKE 'migration%'
ORDER BY indexname;

-- 결과 (8개 인덱스):
-- idx_migration_batches_created
-- idx_migration_batches_schedule
-- idx_migration_batches_status
-- idx_migration_logs_batch
-- idx_migration_logs_document
-- idx_migration_logs_status
-- idx_migration_schedules_created
-- idx_migration_schedules_enabled
```

✅ **완료 후 다음 단계로**

---

## 🔴 STEP 3: 애플리케이션 코드 배포 (5분)

**Option A: 자동 배포 (CI/CD 설정된 경우)**
```
코드가 이미 main 브랜치에 푸시되었습니다.
CI/CD 파이프라인이 자동으로 스테이징 배포를 시작합니다.

상태 확인:
- Railway: railway logs --follow
- Render: render logs
- GitHub Actions: GitHub 리포지토리 > Actions 탭
```

**Option B: 수동 배포**
```bash
# 스테이징 서버에 SSH 접속
ssh [staging_server]

# 디렉토리로 이동
cd /app

# 코드 업데이트
git pull origin main

# 또는 rsync로 복사
rsync -av /local/path/app/ ./app/
rsync -av /local/path/database/ ./database/
rsync -av /local/path/tests/ ./tests/

# 의존성 설치
uv sync

# 애플리케이션 재시작
sudo systemctl restart api
# 또는
sudo supervisorctl restart api

# 상태 확인
sudo systemctl status api
```

✅ **완료 후 다음 단계로**

---

## 🔴 STEP 4: 스케줄러 초기화 검증 (2분)

**로그 확인:**
```bash
# 스테이징 서버의 로그 실시간 감시
tail -f /var/log/app.log | grep -E "스케줄러|Scheduler|Phase 5"

# 기대 메시지:
# "[Phase 5] 정기 문서 마이그레이션 스케줄러 초기화 완료"
```

**또는 접근 가능하면:**
```bash
# Railway 로그
railway logs --follow

# Render 로그
render logs

# SSH 로그
ssh [staging_server] "tail -f /var/log/app.log | grep -i scheduler"
```

**성공 표시:**
```
✅ 로그에 "스케줄러 초기화 완료" 메시지 나타남
✅ ERROR 로그 없음
✅ 애플리케이션 정상 실행 중
```

✅ **완료 후 다음 단계로**

---

## 🔴 STEP 5: 단위 테스트 실행 (10분)

```bash
# 스테이징 환경 또는 로컬에서 실행
cd /app  # 또는 프로젝트 경로

pytest tests/test_scheduler_integration.py -v --tb=short

# 기대 결과:
# ====== 24 passed, 1 warning in ~6s ======
```

**성공 기준:**
```
✅ 24 tests PASSED
✅ 0 tests FAILED
✅ Duration: 6-10 seconds
```

✅ **완료 후 다음 단계로**

---

## 🔴 STEP 6: API 엔드포인트 테스트 (10분)

**사전 설정:**
```bash
# 토큰 변수 설정 (필수)
export TOKEN="your_staging_bearer_token"
export API_URL="https://staging-api.yourdomain.com"
```

**6a. 스케줄 생성**
```bash
curl -X POST $API_URL/api/migration/schedules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Staging Test Schedule",
    "cron_expression": "0 8 * * *",
    "source_type": "intranet",
    "enabled": true
  }'

# 응답 예:
# HTTP 200
# {"id": "uuid-here", "name": "Staging Test Schedule", ...}

# 스케줄 ID 저장
export SCHEDULE_ID="paste_id_from_response"
```

**6b. 스케줄 목록 조회**
```bash
curl -X GET $API_URL/api/migration/schedules \
  -H "Authorization: Bearer $TOKEN"

# 응답: 스케줄 목록 배열
# [{"id": "...", "name": "Staging Test Schedule", ...}]
```

**6c. 마이그레이션 실행**
```bash
curl -X POST $API_URL/api/migration/trigger/$SCHEDULE_ID \
  -H "Authorization: Bearer $TOKEN"

# 응답:
# HTTP 200
# {"batch_id": "uuid-here"}

# 배치 ID 저장
export BATCH_ID="paste_batch_id_from_response"
```

**6d. 배치 상태 조회**
```bash
curl -X GET $API_URL/api/migration/batches/$BATCH_ID \
  -H "Authorization: Bearer $TOKEN"

# 응답: 배치 상세 정보
# {"id": "...", "status": "completed", "total_documents": 0, ...}
```

**6e. 배치 목록 조회**
```bash
curl -X GET $API_URL/api/migration/batches \
  -H "Authorization: Bearer $TOKEN"

# 응답: 배치 목록 배열
```

**성공 기준:**
```
✅ 모든 API 호출 HTTP 200 응답
✅ 응답에 예상 필드 포함
✅ 데이터가 올바른 형식
```

✅ **완료 후 다음 단계로**

---

## 🔴 STEP 7: 메트릭 모니터링 (30분)

**모니터링할 지표:**

```bash
# 1. 애플리케이션 로그 감시
tail -f /var/log/app.log | grep -E "error|ERROR|warning|CRITICAL"

# 2. 데이터베이스 레코드 확인
psql [staging_db] -c "SELECT COUNT(*) FROM migration_schedules;"
psql [staging_db] -c "SELECT COUNT(*) FROM migration_batches;"
psql [staging_db] -c "SELECT COUNT(*) FROM migration_logs;"

# 3. API 응답 시간 측정
for i in {1..5}; do
  echo "Request $i:"
  curl -w "Response time: %{time_total}s\n" -o /dev/null -s \
    $API_URL/api/migration/schedules \
    -H "Authorization: Bearer $TOKEN"
done

# 4. 에러율 계산
ERROR_COUNT=$(grep -c "ERROR" /var/log/app.log || echo 0)
echo "Error count: $ERROR_COUNT"

# 5. 스케줄러 상태
curl -s $API_URL/health | jq '.scheduler'
```

**기대 메트릭:**

| 지표 | 목표 | 방법 |
|------|------|------|
| 스케줄러 시작 | < 2s | 로그 확인 |
| API 응답 시간 | < 200ms | curl -w |
| 에러율 | < 0.1% | 로그 계산 |
| 배치 처리 | < 30s | DB 확인 |

**30분 모니터링:**
```
시간 0분:   API 테스트 완료 후 시작
시간 10분:  로그 및 메트릭 점검
시간 20분:  데이터베이스 레코드 확인
시간 30분:  최종 상태 확인 및 보고
```

✅ **모니터링 완료**

---

## ✅ 배포 완료 체크리스트

- [ ] STEP 1: DB 백업 완료
- [ ] STEP 2: 마이그레이션 SQL 실행 완료
- [ ] STEP 3: 테이블 생성 확인 (3개)
- [ ] STEP 4: 인덱스 생성 확인 (8개)
- [ ] STEP 5: 코드 배포 완료
- [ ] STEP 6: 스케줄러 초기화됨
- [ ] STEP 7: 24/24 테스트 통과
- [ ] STEP 8: 모든 API 엔드포인트 응답
- [ ] STEP 9: 30분 모니터링 완료

---

## ⚠️ 문제 발생 시 롤백

```bash
# 1. 애플리케이션 중지
sudo systemctl stop api

# 2. 데이터베이스 복원
pg_restore --format custom -d [database] staging_backup_*.bak

# 3. 코드 되돌리기
git revert [commit_hash]
git push origin main

# 4. 애플리케이션 재시작
sudo systemctl start api

# 5. 로그 확인
tail -f /var/log/app.log
```

---

## 📞 지원

**문제 발생 시:**
1. 로그 확인: `tail -f /var/log/app.log`
2. 체크리스트 참고: `PHASE5_DEPLOYMENT_CHECKLIST.md`
3. 상세 가이드: `docs/operations/phase5-staging-deployment-guide.md`
4. Slack: #tenopa-technical

---

**진행 상황 기록:**

| 단계 | 상태 | 시간 |
|------|------|------|
| 1. DB 백업 | ⏳ |  |
| 2. 마이그레이션 | ⏳ |  |
| 3. 코드 배포 | ⏳ |  |
| 4. 스케줄러 검증 | ⏳ |  |
| 5. 테스트 실행 | ⏳ |  |
| 6. API 테스트 | ⏳ |  |
| 7. 모니터링 | ⏳ |  |

**전체 예상 시간:** ~60분

---

**준비 완료. 위 단계들을 스테이징 환경에서 순서대로 실행하세요.**
