# 관리자 가이드 (Admin Guide)

**버전**: 1.0  
**대상**: 시스템 관리자, DevOps  
**마지막 수정**: 2026-04-08  

---

## 📋 목차

1. [시스템 관리](#시스템-관리)
2. [사용자 관리](#사용자-관리)
3. [보안 및 권한](#보안-및-권한)
4. [성능 모니터링](#성능-모니터링)
5. [백업 및 복구](#백업-및-복구)
6. [문제 진단](#문제-진단)

---

## 시스템 관리

### 대시보드 접근

**관리자 페이지**: `/admin/dashboard`

```
┌────────────────────────────────────────┐
│ 관리 대시보드                           │
├────────────────────────────────────────┤
│ 활성 사용자: 234명                     │
│ 프로젝트: 89개 (진행 중 34개)           │
│ API 요청: 45K/일                       │
│ 평균 응답시간: 234ms                   │
│                                        │
│ [시스템 상태] [알림] [로그] [설정]    │
│                                        │
└────────────────────────────────────────┘
```

### 시스템 상태 확인

**Uptime 확인**:
```bash
# 명령줄에서:
curl https://api.tenopa.io/health

# 응답:
{
  "status": "healthy",
  "version": "4.9.0",
  "timestamp": "2026-04-08T10:30:00Z",
  "database": "connected",
  "redis": "connected",
  "elasticsearch": "connected"
}
```

**헬스 체크 엔드포인트**:
- `/health` — 전체 상태
- `/health/db` — 데이터베이스만
- `/health/cache` — Redis 캐시만
- `/health/storage` — Supabase Storage

### 환경 변수 관리

**Railway 콘솔**:
1. Railway 대시보드 로그인
2. 프로젝트 선택 → Variables
3. 변수 추가/수정/삭제
4. "Trigger Deploy" → 자동 배포

**주요 환경 변수**:
```env
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyxxxxx
SUPABASE_PASSWORD=xxxxxx

# Azure AD
AZURE_AD_CLIENT_ID=xxxxx
AZURE_AD_CLIENT_SECRET=xxxxx
AZURE_AD_TENANT=xxxxx

# API
API_PORT=8000
API_LOG_LEVEL=INFO
MAX_WORKERS=4

# 외부 서비스
SLACK_WEBHOOK_URL=https://hooks.slack.com/xxxxx
PAGERDUTY_SERVICE_KEY=xxxxx
```

### 서비스 재시작

**Railway에서**:
```bash
# 1. 콘솔에서
Railway CLI 사용:
railway down    # 서비스 중지
railway up      # 서비스 시작

# 2. GitHub Actions
git push origin main  # 자동 배포 및 재시작
```

**Docker (온프레미스)**:
```bash
docker-compose restart api
docker-compose restart web
docker-compose restart postgres
```

---

## 사용자 관리

### 사용자 생성 및 활성화

**Azure AD 동기화**:
- 자동: 사용자가 처음 로그인할 때 자동 생성
- 수동: 관리 대시보드에서 직접 추가

**관리 대시보드 경로**: `/admin/users`

```
검색: ________________
필터: [활성] [비활성] [관리자] [리더]

사용자 목록:
┌──────────────────────────────────────────┐
│ 이름    | 이메일           | 부서  | 역할 │
├──────────────────────────────────────────┤
│ 홍길동  | hong@tenopa.io  | 영업 | 리더 │
│ 김영희  | kim@tenopa.io   | 기술 | 편집 │
│ ...                                      │
│ [+ 새 사용자 추가]                       │
└──────────────────────────────────────────┘
```

### 권한 설정

**역할 (Roles)**:
| 역할 | 권한 | 용도 |
|------|------|------|
| **Admin** | 모든 것 | 시스템 관리자 |
| **Manager** | 팀 관리, 제안 승인 | 부서장, PM |
| **Editor** | 제안 작성 & 편집 | 일반 사용자 |
| **Reviewer** | 읽기 & 검수 | 검수자 |
| **Guest** | 읽기만 | 임시 협력자 |

**권한 변경**:
1. 사용자 선택
2. "권한" 탭
3. 역할 선택 → 저장

### 사용자 비활성화

```
사용자 선택 → ⋮ (메뉴) → "비활성화"
```

**효과**:
- 로그인 불가
- 프로젝트 접근 불가
- 기존 데이터는 보존

---

## 보안 및 권한

### 액세스 제어 (RBAC)

**프로젝트 수준의 권한**:
```
프로젝트 설정 → 팀원
팀원 추가 → 역할 선택

[소유자]  → 모든 권한 + 삭제
[관리자]  → 편집 + 팀 관리
[편집자]  → 편집만
[검수자]  → 읽기 + 댓글
[읽기자]  → 읽기만
```

### 감사 로그 (Audit Log)

**접근**: `/admin/audit-logs`

```bash
# CLI에서 확인:
curl -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  https://api.tenopa.io/admin/audit-logs?limit=100

# 응답:
{
  "logs": [
    {
      "timestamp": "2026-04-08T10:30:00Z",
      "user": "hong@tenopa.io",
      "action": "create_project",
      "resource": "project_id_123",
      "status": "success"
    },
    ...
  ]
}
```

**주요 감시 항목**:
- 사용자 생성/삭제
- 권한 변경
- 제안서 제출
- 대량 다운로드
- 실패한 로그인 시도 (5회 이상)

### 비밀번호 정책

```
최소 길이: 12자
대문자: 최소 1개
숫자: 최소 1개
특수문자: 최소 1개 (!@#$%^&*)
만료: 90일 (다시 설정 강제)
```

**Azure AD로 로그인 시**: Azure AD의 정책 따름

---

## 성능 모니터링

### Grafana 대시보드

**접근**: `http://localhost:3001` (또는 클라우드 URL)

**주요 대시보드**:
1. **System Overview**: CPU, 메모리, 디스크, 네트워크
2. **API Performance**: 응답시간, 에러율, 처리량
3. **Database**: 연결 수, 쿼리 시간, 인덱스 효율
4. **Errors & Alerts**: 발생한 에러, 알림 상태

### 성능 기준 (SLA)

| 메트릭 | 목표 | 경고 | 심각 |
|--------|------|------|------|
| API 응답시간 (P95) | < 200ms | > 500ms | > 1s |
| 에러율 | < 0.1% | > 1% | > 5% |
| 데이터베이스 응답시간 | < 50ms | > 100ms | > 500ms |
| 캐시 히트율 | > 80% | < 70% | < 50% |
| CPU 사용률 | < 60% | > 80% | > 95% |
| 메모리 사용률 | < 70% | > 85% | > 95% |

### 성능 최적화 팁

**데이터베이스 쿼리 최적화**:
```bash
# 느린 쿼리 조회
SELECT query, calls, mean_time 
FROM pg_stat_statements 
WHERE mean_time > 100 
ORDER BY mean_time DESC 
LIMIT 10;

# 인덱스 재작성
REINDEX INDEX index_name;
VACUUM ANALYZE;
```

**캐시 효율성 개선**:
```bash
# Redis 메모리 사용 확인
redis-cli INFO memory

# 만료된 키 정리
redis-cli --scan --pattern "*" | xargs -L 100 redis-cli DEL

# 캐시 정책 확인
redis-cli CONFIG GET maxmemory-policy
```

---

## 백업 및 복구

### 자동 백업 확인

```bash
# Supabase에서:
1. 콘솔 로그인 → Settings → Database → Backups
2. 자동 백업 일정 확인 (매일 02:00 UTC)
3. PITR (Point-in-Time Recovery) 활성화 확인
```

### 수동 백업 실행

```bash
# PostgreSQL 백업
PGPASSWORD="${SUPABASE_PASSWORD}" pg_dump \
  --host=${SUPABASE_HOST} \
  --username=${SUPABASE_USER} \
  --dbname=${SUPABASE_DB} \
  | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# AWS S3에 업로드
aws s3 cp backup_*.sql.gz s3://backup-bucket/postgres/
```

### 복구 절차

**부분 복구 (특정 테이블)**:
```bash
# 테이블 덤프만 복구
pg_restore --table=table_name \
  --dbname=${SUPABASE_DB} \
  --host=${SUPABASE_HOST} \
  backup.sql
```

**전체 복구**:
```bash
# 새 데이터베이스 생성
psql -h ${SUPABASE_HOST} -U postgres \
  -c "CREATE DATABASE recovery_db;"

# 복구
zcat backup.sql.gz | psql \
  --host=${SUPABASE_HOST} \
  --username=${SUPABASE_USER} \
  --dbname=recovery_db
```

---

## 문제 진단

### 로그 확인

**백엔드 로그**:
```bash
# Elasticsearch에서:
GET logs-*/_search
{
  "query": {
    "range": {
      "@timestamp": {
        "gte": "now-1h"
      }
    }
  }
}

# 또는 Kibana에서:
1. 콘솔 접속 (http://localhost:5601)
2. Discover → index "logs-*" 선택
3. 필터 추가 (component:backend, severity:error 등)
```

**프론트엔드 에러 (브라우저)**:
```javascript
// 개발자 도구 → Console
// 모든 에러 로그 출력됨

// 또는 관리자 대시보드:
/admin/errors → 사용자별 에러 추적
```

### 일반적인 문제 해결

**문제**: API 응답 느림
```bash
# 1. 데이터베이스 상태 확인
SELECT datname, numbackends FROM pg_stat_database;

# 2. 느린 쿼리 식별
SELECT query, mean_time FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 5;

# 3. 인덱스 상태 확인
SELECT schemaname, tablename, indexname 
FROM pg_indexes WHERE schemaname='public';
```

**문제**: 메모리 누수
```bash
# Docker 컨테이너 메모리 모니터링
docker stats api

# 특정 프로세스 메모리 추적
ps aux | grep python | head -5
top -p <PID>
```

**문제**: 디스크 부족
```bash
# 디스크 사용량 확인
df -h

# 큰 파일 찾기
du -sh /* | sort -rh | head -10

# 오래된 로그 정리
find /var/log -name "*.log" -mtime +30 -delete
```

---

## 추가 리소스

### 외부 문서
- [Supabase Admin API](https://supabase.com/docs/reference/admin-api)
- [Railway CLI 가이드](https://docs.railway.app/cli)
- [Prometheus 쿼리 언어](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Elasticsearch 관리](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)

### 연락처
- **기술 지원**: ops-support@tenopa.io
- **긴급 (24/7)**: Slack #ops-oncall
- **보안 문제**: security@tenopa.io

