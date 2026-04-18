# 모니터링 가이드 (Monitoring Guide)

## 개요

운영 환경에서의 안정성 확보를 위해 Prometheus(메트릭 수집), Grafana(대시보드), AlertManager(알림)를 사용합니다.
이 가이드는 모니터링 설정, 주요 지표 확인 방법, 알림 규칙을 다룹니다.

---

## 헬스체크 엔드포인트

### /health - 기본 헬스체크

애플리케이션 기본 상태를 즉시 확인합니다.

```bash
# 요청
curl -X GET https://api.tenopa.co.kr/health \
  -H "Content-Type: application/json"

# 응답 (200 OK)
{
  "status": "healthy",
  "version": "4.1.0",
  "environment": "production",
  "timestamp": "2026-04-25T10:30:00Z"
}
```

**응답 코드 해석:**
- `200 OK` - 정상 동작
- `503 Service Unavailable` - 서비스 불가능 (데이터베이스 연결 실패 등)

### /ready - 준비 상태 체크

서비스가 트래픽을 받을 준비가 되었는지 확인합니다. 쿠버네티스의 readiness probe에 사용됩니다.

```bash
# 요청
curl -X GET https://api.tenopa.co.kr/ready \
  -H "Content-Type: application/json"

# 응답 (200 OK)
{
  "ready": true,
  "checks": {
    "database": "ok",
    "redis": "ok",
    "anthropic_api": "ok"
  }
}
```

**상태 확인 항목:**
- `database`: PostgreSQL 연결
- `redis`: 캐시 연결 (있을 경우)
- `anthropic_api`: Claude API 연결

---

## Prometheus 메트릭 설정

### 메트릭 수집 엔드포인트

FastAPI 애플리케이션에서 Prometheus 형식의 메트릭을 제공합니다.

```bash
# Prometheus 메트릭 조회
curl https://api.tenopa.co.kr/metrics
```

### Prometheus 설정 파일 (prometheus.yml)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "tenopa-api-staging"
    static_configs:
      - targets: ["staging-api.tenopa.co.kr:443"]
    scheme: "https"
    scrape_interval: 30s

  - job_name: "tenopa-api-production"
    static_configs:
      - targets: ["api.tenopa.co.kr:443"]
    scheme: "https"
    scrape_interval: 15s
```

### 주요 메트릭 목록

| 메트릭 | 설명 | 단위 | 예시 |
|--------|------|------|------|
| `http_requests_total` | 전체 HTTP 요청 수 (경로, 메서드, 상태코드 별) | count | 45,230 |
| `http_request_duration_seconds` | HTTP 요청 응답 시간 (p50, p95, p99) | seconds | 0.12, 0.45, 1.23 |
| `http_requests_errors_total` | 에러 응답 수 (4xx, 5xx) | count | 312 |
| `db_query_duration_seconds` | 데이터베이스 쿼리 실행 시간 | seconds | 0.05 |
| `db_connections_active` | 활성 데이터베이스 연결 수 | count | 23/50 |
| `claude_api_calls_total` | Claude API 호출 총수 | count | 1,250 |
| `claude_api_errors_total` | Claude API 에러 수 | count | 3 |
| `proposal_workflow_duration_seconds` | 제안서 워크플로 실행 시간 | seconds | 45.3 |
| `cache_hits_total` | 캐시 히트 수 | count | 8,945 |
| `cache_misses_total` | 캐시 미스 수 | count | 1,250 |

---

## 모니터링할 KPI 및 임계값

### 1. 응답 시간 (Response Time)

**PromQL 쿼리:**
```
histogram_quantile(0.95, http_request_duration_seconds_bucket)
```

| 환경 | P50 | P95 | P99 | 경고 | 심각 |
|------|-----|-----|-----|------|------|
| Staging | < 300ms | < 1s | < 2s | > 1s | > 2s |
| Production | < 200ms | < 600ms | < 1.5s | > 1s | > 2s |

**주요 엔드포인트 별:**
- `/api/workflows/start` (제안 생성): < 2s
- `/api/workflows/stream` (워크플로 실행): < 5s (스트리밍)
- `/api/artifacts/download` (산출물 다운로드): < 3s

---

### 2. 에러율 (Error Rate)

**PromQL 쿼리:**
```
rate(http_requests_errors_total[5m]) / rate(http_requests_total[5m])
```

| 환경 | 경고 | 심각 |
|------|------|------|
| Staging | > 2% | > 5% |
| Production | > 1% | > 3% |

**에러 분류:**
- **4xx**: 클라이언트 오류 (일반적, 허용됨)
- **5xx**: 서버 오류 (즉시 조사 필요)

**PromQL - 5xx 에러율만 집계:**
```
rate(http_requests_errors_total{status_code=~"5.."}[5m])
```

---

### 3. 처리량 (Throughput)

**PromQL 쿼리:**
```
rate(http_requests_total[5m])
```

| 환경 | 정상범위 | 경고 |
|------|---------|------|
| Staging | 10-50 req/s | < 5 req/s (트래픽 부족) |
| Production | 50-200 req/s | < 20 req/s (트래픽 부족) |

---

### 4. 데이터베이스 성능

**활성 연결 수:**
```
db_connections_active / db_connections_max
```

| 임계값 | 상태 | 조치 |
|--------|------|------|
| < 50% | 정상 | 모니터링만 |
| 50-80% | 경고 | 슬로우 쿼리 조사 |
| > 80% | 심각 | 즉시 대응 (연결 풀 증가 또는 재시작) |

**슬로우 쿼리 감지:**
```sql
-- PostgreSQL: 1초 이상 소요 쿼리 확인
SELECT query, mean_time, calls 
FROM pg_stat_statements 
WHERE mean_time > 1000 
ORDER BY mean_time DESC 
LIMIT 10;
```

---

### 5. Claude API 성능

**API 호출 에러율:**
```
rate(claude_api_errors_total[5m]) / rate(claude_api_calls_total[5m])
```

| 임계값 | 상태 | 조치 |
|--------|------|------|
| < 1% | 정상 | 모니터링만 |
| 1-5% | 경고 | API 상태 확인, 재시도 로직 작동 |
| > 5% | 심각 | Anthropic Support 연락 |

---

## 알림 규칙 (Alert Rules)

### AlertManager 설정 (alertmanager.yml)

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

route:
  group_by: ['alertname', 'cluster']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  
  routes:
    # 심각 알림 - 즉시 발송
    - match:
        severity: critical
      receiver: 'critical-team'
      group_wait: 10s
      repeat_interval: 10m
    
    # 경고 알림 - 30초 후 발송
    - match:
        severity: warning
      receiver: 'ops-team'
      group_wait: 30s

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#ops-alerts'
        title: '알림: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'critical-team'
    slack_configs:
      - channel: '#critical-incidents'
    pagerduty_configs:
      - routing_key: 'YOUR_PAGERDUTY_KEY'
```

### 주요 알림 규칙

#### 1. 높은 에러율

```yaml
- alert: HighErrorRate
  expr: rate(http_requests_errors_total{status_code=~"5.."}[5m]) > 0.05
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "높은 5xx 에러율 감지"
    description: "5분 동안 5xx 에러율이 {{ $value | humanizePercentage }}로 높습니다."
```

#### 2. 느린 응답 시간

```yaml
- alert: SlowResponseTime
  expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 3
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "느린 응답 시간 감지"
    description: "P95 응답시간이 {{ $value | humanizeDuration }}입니다."
```

#### 3. 데이터베이스 연결 풀 부족

```yaml
- alert: HighDatabaseConnections
  expr: (db_connections_active / db_connections_max) > 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "데이터베이스 연결 풀 부족"
    description: "활성 연결이 최대의 {{ $value | humanizePercentage }}입니다."
```

#### 4. Claude API 호출 실패

```yaml
- alert: ClaudeAPIErrors
  expr: rate(claude_api_errors_total[5m]) > 0.05
  for: 10m
  labels:
    severity: critical
  annotations:
    summary: "Claude API 에러율 증가"
    description: "지난 5분간 Claude API 에러율이 {{ $value | humanizePercentage }}입니다."
```

#### 5. 서비스 다운

```yaml
- alert: ServiceDown
  expr: up{job="tenopa-api-production"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "서비스가 응답하지 않습니다"
    description: "{{ $labels.instance }} 서비스가 1분 이상 접근 불가능합니다."
```

---

## Grafana 대시보드 설정

### 대시보드 생성 (대시보드 ID: 1)

**이름:** `TenopA Proposer - Production Overview`

#### Panel 1: 요청 처리량 (RPS)

```promql
rate(http_requests_total[5m])
```

- **차트 타입**: Line Graph
- **Y축**: Requests/sec
- **범례**: 경로별 (`path` 라벨)

#### Panel 2: 응답 시간 (P95)

```promql
histogram_quantile(0.95, http_request_duration_seconds_bucket)
```

- **차트 타입**: Graph with Fill
- **Y축**: Seconds
- **스래시홀드**: 1s (경고), 2s (심각)

#### Panel 3: 에러율

```promql
(rate(http_requests_errors_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])) * 100
```

- **차트 타입**: Gauge
- **최소값**: 0, **최대값**: 10
- **색상 맵핑**: Green (< 1%), Yellow (1-5%), Red (> 5%)

#### Panel 4: 데이터베이스 연결 풀

```promql
db_connections_active / db_connections_max
```

- **차트 타입**: Gauge
- **최소값**: 0, **최대값**: 1
- **색상 맵핑**: Green (< 0.5), Yellow (0.5-0.8), Red (> 0.8)

#### Panel 5: Claude API 사용량

```promql
rate(claude_api_calls_total[5m])
```

- **차트 타입**: Bar Chart
- **Y축**: API Calls/sec
- **표시**: 시간대별 추이

#### Panel 6: 메모리 사용률

```promql
process_resident_memory_bytes / process_virtual_memory_max_bytes
```

- **차트 타입**: Gauge
- **최소값**: 0, **최대값**: 1
- **색상 맵핑**: Green (< 0.7), Yellow (0.7-0.85), Red (> 0.85)

---

## 모니터링 점검 체크리스트

### 매일 (09:00)

- [ ] Grafana 대시보드 접속 및 주요 메트릭 확인
- [ ] 어제의 에러 로그 검토 (Sentry)
- [ ] AlertManager에서 pending 알림 확인

### 주 1회 (월요일 10:00)

- [ ] 지난 주 성능 리포트 작성
  - 에러율, 응답 시간, 처리량 트렌드
  - 피크 시간대 분석
- [ ] Prometheus 스토리지 사용량 확인 (< 80%)

### 월 1회 (첫 주 금요일)

- [ ] 알림 규칙 재검토 (오탐 vs 미감지)
- [ ] 대시보드 레이아웃 최적화
- [ ] 메트릭 보존 정책 검토 (15일 유지)

---

## 트러블슈팅

### 메트릭이 수집되지 않음

```bash
# 1. Prometheus가 메트릭 엔드포인트에 접근 가능한지 확인
curl https://api.tenopa.co.kr/metrics -v

# 2. Prometheus 로그 확인
docker logs prometheus

# 3. Prometheus 설정 파일 검증
promtool check config /etc/prometheus/prometheus.yml

# 4. 수동으로 메트릭 푸시 (테스트)
curl -X POST http://localhost:9091/metrics/job/test
```

### 알림이 Slack에 도착하지 않음

```bash
# 1. AlertManager 로그 확인
docker logs alertmanager

# 2. Slack Webhook URL 검증
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"테스트 메시지"}' \
  https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# 3. AlertManager 설정 재로드
curl -X POST http://localhost:9093/-/reload
```

---

## 담당자

| 역할 | 담당자 | 연락처 |
|------|--------|---------|
| 모니터링 담당 | (지정 예정) | Slack: #ops |
| 인프라 팀장 | (지정 예정) | Slack: #infra |
| 긴급 대응 | 온콜 엔지니어 | PagerDuty |

---

## 문서 버전

- **버전**: 1.0
- **마지막 업데이트**: 2026-04-18
- **다음 검토**: 2026-05-18
