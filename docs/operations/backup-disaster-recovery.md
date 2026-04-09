# 백업 및 재해복구 (DR) 계획

**마지막 수정**: 2026-04-08  
**책임자**: DevOps 팀  
**검토 주기**: 분기별 (3개월)  

---

## 📋 목차

1. [개요](#개요)
2. [RTO/RPO 목표](#rtorpo-목표)
3. [백업 전략](#백업-전략)
4. [복구 절차](#복구-절차)
5. [테스트 계획](#테스트-계획)
6. [모니터링](#모니터링)
7. [체크리스트](#체크리스트)

---

## 개요

Tenopa Proposer 시스템의 **백업 및 재해복구 정책**을 정의하여 데이터 손실 및 서비스 중단을 최소화합니다.

### 주요 자산
| 자산 | 중요도 | 위치 | 보유 데이터 |
|------|--------|------|-----------|
| **Supabase PostgreSQL** | 🔴 Critical | us-east-1 | 제안서, 사용자, 프로젝트 |
| **Supabase Storage** | 🟡 High | us-east-1 | 업로드된 파일, 문서 |
| **Redis (캐시)** | 🟢 Low | Railway | 세션, 임시 데이터 |
| **Elasticsearch** | 🟡 High | 온프레미스/클라우드 | 로그 데이터 |
| **GitHub Repo** | 🔴 Critical | GitHub | 소스 코드 |

---

## RTO/RPO 목표

**RTO (Recovery Time Objective)**: 장애 발생 후 복구 완료 시간  
**RPO (Recovery Point Objective)**: 손실 가능한 최대 데이터 양

| 서비스 | RTO | RPO | SLA |
|--------|-----|-----|-----|
| **데이터베이스** | 1시간 | 15분 | 99.9% |
| **스토리지** | 2시간 | 1시간 | 99.5% |
| **API (백엔드)** | 30분 | N/A | 99.9% |
| **웹앱 (프론트엔드)** | 15분 | N/A | 99.5% |
| **로그 시스템** | 4시간 | 1일 | 95% |

---

## 백업 전략

### 1. Supabase PostgreSQL 백업

#### 자동 백업 (Supabase 관리)
```
빈도: 일일 (자동)
보관 기간: 7일
복구 시점 선택(PITR): 지난 7일 내 임의 시점
```

#### 수동 백업 (pg_dump)
```bash
#!/bin/bash
# 일일 수동 백업 스크립트
export PGPASSWORD="${SUPABASE_PASSWORD}"

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/db_${DATE}.sql.gz"

mkdir -p ${BACKUP_DIR}

# 데이터베이스 덤프
pg_dump \
  --host=${SUPABASE_HOST} \
  --port=5432 \
  --username=${SUPABASE_USER} \
  --dbname=${SUPABASE_DB} \
  --format=plain \
  | gzip > ${BACKUP_FILE}

# 보관 (30일)
find ${BACKUP_DIR} -name "db_*.sql.gz" -mtime +30 -delete

# S3에 업로드
aws s3 cp ${BACKUP_FILE} s3://backup-bucket/postgres/

echo "Backup completed: ${BACKUP_FILE}"
```

**스케줄**: 매일 02:00 UTC  
**보관 기간**: 30일 (로컬), 1년 (S3 Glacier)  
**검증**: 주간 복구 테스트

---

### 2. Supabase Storage 백업

#### 자동 스냅샷
```
빈도: 일일
보관 기간: 14일
버킷: tenopa-proposer/documents
```

#### S3 크로스 리전 복제
```bash
#!/bin/bash
# S3에 Storage 백업
BACKUP_DIR="/backups/storage"
DATE=$(date +%Y%m%d)

# Supabase Storage에서 다운로드
supabase storage download \
  --bucket=documents \
  --recursive \
  --output=${BACKUP_DIR}/storage_${DATE}

# AWS S3로 업로드 (지역 복제)
aws s3 sync ${BACKUP_DIR}/storage_${DATE} \
  s3://backup-bucket/storage/ \
  --region us-west-2 \
  --storage-class STANDARD_IA

echo "Storage backup completed"
```

**스케줄**: 매일 03:00 UTC  
**보관 기간**: 90일 (S3 Standard), 1년 (S3 Glacier)  
**검증**: 월간 복구 테스트

---

### 3. GitHub Repository 백업

#### Mirrored Repository
```bash
#!/bin/bash
# GitHub repo 미러 백업

MIRROR_DIR="/backups/github"
REPO="https://github.com/tenopa/proposer.git"

# 미러 생성 (처음 1회)
# git clone --mirror ${REPO} ${MIRROR_DIR}/proposer.git

# 정기 업데이트
cd ${MIRROR_DIR}/proposer.git
git fetch --all --prune

# S3에 압축 업로드
tar czf proposer_mirror_$(date +%Y%m%d).tar.gz proposer.git
aws s3 cp proposer_mirror_*.tar.gz s3://backup-bucket/github/

echo "GitHub mirror updated"
```

**스케줄**: 매일 04:00 UTC  
**보관 기간**: 1년  
**별도 저장소**: GitHub 및 Gitea (온프레미스)

---

### 4. 애플리케이션 설정 백업

```bash
#!/bin/bash
# 환경 변수, Docker Compose, 설정 파일 백업

BACKUP_DIR="/backups/configs"
DATE=$(date +%Y%m%d)

# 환경 변수 (암호화)
openssl enc -aes-256-cbc -salt -in .env.production \
  -out ${BACKUP_DIR}/.env.production_${DATE}.enc \
  -k "${ENCRYPTION_KEY}"

# Docker Compose
cp docker-compose*.yml ${BACKUP_DIR}/

# Nginx, Prometheus, Grafana 설정
tar czf configs_${DATE}.tar.gz \
  nginx.conf \
  monitoring/prometheus.yml \
  monitoring/grafana/ \
  monitoring/alertmanager.yml

aws s3 cp configs_${DATE}.tar.gz s3://backup-bucket/configs/

echo "Configs backup completed"
```

**스케줄**: 매주 일요일 05:00 UTC  
**보관 기간**: 3개월  
**암호화**: AES-256

---

## 복구 절차

### Scenario A: 데이터베이스 부분 손실

#### 상황
- 특정 테이블 손상 또는 삭제
- 사용자 조작 오류

#### 복구 스텝
```bash
# 1. Supabase 콘솔에서 PITR (Point-in-Time Recovery) 사용
# Settings → Backups → Restore from backup
# → 손상 전 시점 선택 (예: 2시간 전)

# 또는 CLI로 복구:
supabase db pull  # 백업에서 스키마 다운로드
psql -h ${SUPABASE_HOST} -U ${SUPABASE_USER} < backup.sql

# 2. 데이터 검증
SELECT COUNT(*) FROM table_name;

# 3. 서비스 상태 확인
curl http://api.tenopa.io/health
```

**예상 시간**: 15~30분  
**영향 범위**: 해당 테이블만 (다른 테이블은 영향 없음)  
**롤백**: PITR 시점 변경

---

### Scenario B: 전체 데이터베이스 손실

#### 상황
- Supabase 계정 해킹/삭제
- 재앙적 데이터 손상 (전체 스키마)

#### 복구 스텝
```bash
# 1. 별도 Supabase 프로젝트 생성
# Supabase 콘솔 → New Project → tenopa-proposer-restore

# 2. pg_dump에서 복구
BACKUP_FILE="/backups/postgres/db_20260408_020000.sql.gz"
zcat ${BACKUP_FILE} | psql \
  --host=${NEW_SUPABASE_HOST} \
  --username=${SUPABASE_USER} \
  --dbname=${SUPABASE_DB}

# 3. 환경 변수 업데이트
vi .env.production
# SUPABASE_URL 및 SUPABASE_KEY 변경

# 4. 애플리케이션 재배포
docker-compose -f docker-compose.yml restart api

# 5. 데이터 무결성 검사
npm run verify:database
```

**예상 시간**: 1~2시간  
**영향 범위**: 전체 시스템 (따라서 롤백 필요)  
**주의**: 마지막 백업 이후의 데이터 손실

---

### Scenario C: Storage 파일 손실

#### 상황
- 파일 삭제 (실수 또는 악의적)
- Storage 연결 끊김

#### 복구 스텝
```bash
# 1. S3에서 복구
aws s3 sync s3://backup-bucket/storage/storage_20260407 \
  /tmp/recovered_storage

# 2. Supabase Storage에 업로드
for file in /tmp/recovered_storage/*; do
  supabase storage upload \
    --bucket documents \
    --file ${file}
done

# 3. 데이터베이스 메타데이터 동기화
npm run sync:storage-metadata
```

**예상 시간**: 30분 ~ 2시간 (파일 크기 따라)  
**영향 범위**: Storage만 (DB는 영향 없음)

---

### Scenario D: 애플리케이션 서버 다운

#### 상황
- API 서버 하드웨어 장애
- Railway 무중단 배포 필요

#### 복구 스텝
```bash
# 1. 새 인스턴스 프로비저닝
# Railway 콘솔 → Deploy new instance

# 2. 코드 배포
git push origin main  # GitHub Actions 자동 배포

# 3. 헬스 체크
for i in {1..30}; do
  if curl -f http://api.tenopa.io/health; then
    echo "API restored"
    break
  fi
  sleep 10
done

# 4. 로드 밸런서 업데이트
# Nginx/HAProxy에서 새 인스턴스로 트래픽 전환
```

**예상 시간**: 5~15분  
**영향 범위**: 배포 중 잠시 응답 지연  
**Blue-Green 배포**: 무중단 복구

---

## 테스트 계획

### 월간 복구 테스트 (1차 목요일)
```bash
#!/bin/bash
# 모의 복구 테스트 스크립트

set -e
DATE=$(date +%Y%m%d)
TEST_DIR="/tmp/dr-test-${DATE}"

echo "=== 월간 DR 테스트 시작 ==="

# 1. 최신 백업 확인
echo "1. 백업 파일 검증..."
if [ ! -f "/backups/postgres/db_*.sql.gz" ]; then
  echo "❌ 백업 파일 없음"
  exit 1
fi
echo "✓ 백업 파일 존재"

# 2. 복구 데이터베이스 생성
echo "2. 테스트 DB 생성..."
psql -h ${SUPABASE_HOST} -U postgres -c "CREATE DATABASE test_restore;"

# 3. 백업에서 복구
echo "3. 백업 복구 중..."
BACKUP_FILE=$(ls -t /backups/postgres/db_*.sql.gz | head -1)
zcat ${BACKUP_FILE} | psql \
  -h ${SUPABASE_HOST} \
  -U ${SUPABASE_USER} \
  -d test_restore

# 4. 데이터 검증
echo "4. 데이터 무결성 검사..."
TABLES=$(psql -h ${SUPABASE_HOST} -U ${SUPABASE_USER} -d test_restore \
  -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")

if [ $TABLES -gt 0 ]; then
  echo "✓ $TABLES개 테이블 복구됨"
else
  echo "❌ 테이블 복구 실패"
  exit 1
fi

# 5. 정리
echo "5. 테스트 환경 정리..."
psql -h ${SUPABASE_HOST} -U postgres -c "DROP DATABASE test_restore;"

echo "=== DR 테스트 완료 ✓ ==="
echo "테스트 결과: 성공"
echo "복구 예상 시간: 1시간 이내"
```

**스케줄**: 매월 첫 목요일 14:00 UTC  
**담당자**: DevOps 리더  
**문서화**: 테스트 결과 기록

---

### 분기별 전체 복구 훈련
```
목표: RTO 달성 여부 검증
범위: 데이터베이스 + Storage + 애플리케이션
환경: Staging (프로덕션 아님)
기간: 2시간

1. 팀 구성 및 역할 할당
2. 모의 재난 시나리오 설정
3. 복구 절차 실행
4. 복구 시간 측정
5. 교훈 도출 및 절차 개선
```

---

## 모니터링

### 백업 상태 확인
```bash
# cron job 로그 확인
tail -f /var/log/cron  # Ubuntu: /var/log/syslog

# S3에 업로드된 백업 확인
aws s3 ls s3://backup-bucket/ --recursive --human-readable --summarize

# Supabase 자동 백업 확인
# Supabase 콘솔 → Settings → Database → Backups
```

### Prometheus 알림
```yaml
- alert: BackupFailed
  expr: increase(backup_failures_total[1d]) > 0
  annotations:
    summary: "Backup job failed in the last 24 hours"

- alert: NoRecentBackup
  expr: time() - backup_last_timestamp > 86400
  annotations:
    summary: "No backup in the last 24 hours"
```

---

## 체크리스트

### 정기 작업 (주간)
- [ ] 백업 로그 검토
- [ ] S3 백업 용량 확인
- [ ] 복구 테스트 결과 검토

### 정기 작업 (월간)
- [ ] 복구 테스트 실행
- [ ] RTO/RPO 달성 여부 검증
- [ ] 문서 업데이트

### 정기 작업 (분기별)
- [ ] 전체 복구 훈련 실행
- [ ] DR 계획 리뷰
- [ ] 팀 교육

### 정기 작업 (연간)
- [ ] DR 계획 개정
- [ ] RTO/RPO 재평가
- [ ] 제3자 감사

---

## 연락처

| 역할 | 이름 | 연락처 |
|------|------|--------|
| **DevOps Lead** | 현재호 | ops@tenopa.io |
| **DB 담당** | Backend Lead | backend@tenopa.io |
| **On-Call (24/7)** | Slack: #ops-oncall | |

---

## 참고 자료

- [Supabase 백업 문서](https://supabase.com/docs/guides/database/backups)
- [PostgreSQL pg_dump 매뉴얼](https://www.postgresql.org/docs/current/app-pgdump.html)
- [AWS S3 재해복구](https://aws.amazon.com/disaster-recovery/)
- [재해복구 계획 템플릿](https://en.wikipedia.org/wiki/Disaster_recovery_plan)

