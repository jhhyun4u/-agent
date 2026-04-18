# Phase 2 Week 1: Production Monitoring Dashboard 구현 ✅ 완료

**날짜:** 2026-04-18  
**상태:** 완료 및 준비 완료  
**다음:** Week 2 - Data-Driven Optimization

---

## 📋 개요

Phase 1 Performance Optimization의 효과를 실시간으로 모니터링하기 위한 Prometheus + Grafana 기반 모니터링 대시보드 구현.

**Phase 1 성과:**
- KB Search: 2,248배 성능 향상 (5.924s → 2.63ms)
- Proposals List: 1,200배 성능 향상 (1.2s → <1ms)
- 메모리 사용: 2-5MB (매우 효율적)

**Phase 2 Week 1 목표:** 이러한 개선사항을 실시간으로 추적 및 모니터링

---

## 🔧 구현 사항

### 1️⃣ Prometheus Client 통합
```toml
# pyproject.toml 업데이트
dependencies = [
    ...
    "prometheus-client>=0.20.0",  # 추가됨
]
```

### 2️⃣ 메트릭 서비스 생성
**파일:** `app/services/metrics_service.py` (450+ 줄)

#### 캐시 메트릭
| 메트릭 | 설명 | 레이블 |
|--------|------|---------|
| `cache_hits_total` | 캐시 히트 총 횟수 | `cache_type` |
| `cache_misses_total` | 캐시 미스 총 횟수 | `cache_type` |
| `cache_evictions_total` | LRU 퇴출 총 횟수 | `cache_type` |
| `cache_expirations_total` | TTL 만료 총 횟수 | `cache_type` |
| `cache_size_bytes` | 캐시 메모리 사용량 | `cache_type` |
| `cache_items` | 캐시 항목 개수 | `cache_type` |
| `cache_hit_rate` | 캐시 히트율 (0.0-1.0) | `cache_type` |

#### API 메트릭
| 메트릭 | 설명 | 레이블 |
|--------|------|---------|
| `http_request_duration_seconds` | HTTP 요청 처리 시간 (히스토그램) | `method, endpoint, status` |
| `http_requests_total` | HTTP 요청 총 횟수 | `method, endpoint, status` |
| `http_requests_in_progress` | 현재 진행 중인 요청 | `method, endpoint` |

#### 데이터베이스 메트릭
| 메트릭 | 설명 | 레이블 |
|--------|------|---------|
| `db_query_duration_seconds` | DB 쿼리 처리 시간 | `query_type, table` |
| `db_queries_total` | DB 쿼리 총 횟수 | `query_type, table, status` |
| `db_connections_active` | 활성 DB 연결 수 | - |

#### AI API 메트릭
| 메트릭 | 설명 | 레이블 |
|--------|------|---------|
| `ai_request_duration_seconds` | Claude API 요청 시간 | `model, operation` |
| `ai_tokens_used_total` | 토큰 사용량 | `model, token_type` |
| `ai_errors_total` | API 에러 총 횟수 | `model, error_type` |

### 3️⃣ Memory Cache Service 메트릭 통합
**파일:** `app/services/memory_cache_service.py` (수정)

```python
# get() 메서드 - 캐시 히트/미스 추적
cache_hits.labels(cache_type=cache_name).inc()      # 히트 기록
cache_misses.labels(cache_type=cache_name).inc()    # 미스 기록
cache_expirations.labels(cache_type=cache_name).inc()  # 만료 기록

# set() 메서드 - LRU 퇴출 추적
cache_evictions.labels(cache_type=cache_name).inc()  # 퇴출 기록

# 캐시 통계 업데이트
_update_cache_metrics(cache_name, cache)  # 메모리 사용량, 항목 수, 히트율
```

### 4️⃣ FastAPI 메트릭 엔드포인트
**파일:** `app/main.py` (수정)

```python
@app.get("/metrics")
async def metrics():
    """Prometheus 메트릭 엔드포인트"""
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )
```

**접근:** `http://localhost:8000/metrics`

### 5️⃣ Prometheus 설정
**파일:** `monitoring/prometheus.yml` (기존 설정 유지)

```yaml
scrape_configs:
  - job_name: 'fastapi-backend'
    scrape_interval: 10s
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### 6️⃣ Prometheus 알림 규칙 추가
**파일:** `monitoring/prometheus-alerts.yml` (업데이트)

#### 캐시 성능 알림
```yaml
- alert: CacheHitRateLow
  expr: cache_hit_rate{cache_type=~"kb_search|proposals"} < 0.80
  for: 10m
  # 캐시 히트율 < 80% 경고

- alert: CacheEvictionsHigh
  expr: rate(cache_evictions_total[5m]) > 5
  for: 5m
  # 초당 5개 이상 LRU 퇴출 경고

- alert: CacheSizeWarning
  expr: cache_size_bytes{cache_type=~"kb_search|proposals"} > 104857600  # 100MB
  for: 10m
  # 캐시 크기 > 100MB 경고

- alert: KBSearchLatencyHigh
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{endpoint=~"/api/kb/search.*"}[5m])) > 0.5
  for: 5m
  # KB 검색 P95 지연 > 0.5초 경고

- alert: ProposalListLatencyHigh
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{endpoint=~"/api/proposals.*"}[5m])) > 0.3
  for: 5m
  # 제안 목록 P95 지연 > 0.3초 경고
```

### 7️⃣ Grafana 대시보드
**파일:** `monitoring/grafana/dashboards/cache-performance.json` (새로 생성)

#### 대시보드 구성 (5개 섹션)

**섹션 1: 캐시 히트율 (원형 차트)**
- KB Search 캐시 히트율
- Proposals 캐시 히트율

**섹션 2: 캐시 성능 게이지**
- KB Search 히트율 % (목표: ≥90%)
- Proposals 히트율 % (목표: ≥90%)
- KB Search 캐시 크기 (목표: <100MB)
- Proposals 캐시 크기 (목표: <100MB)

**섹션 3: 캐시 활동 추이**
- 캐시 히트 vs 미스 (5분 평균)
- 캐시 항목 개수 추이 (유형별)

**섹션 4: API 성능**
- HTTP 요청 지연 백분위수 (P50, P95, P99)
  - 목표: P95 < 100ms (캐시 적용 후)
  - 목표: P99 < 500ms
- HTTP 요청 비율 (상태별)
  - 2xx 성공, 4xx 클라이언트 에러, 5xx 서버 에러

**섹션 5: 데이터베이스 성능**
- DB 쿼리 비율 (성공 vs 에러)

#### 대시보드 주요 특징
- **갱신 간격:** 30초
- **시간 범위:** 최근 1시간 (기본)
- **색상:** Dark 테마
- **대화형:** 범위 선택, 드릴다운 가능
- **임계값:** 성능 저하 시 색상 변경 (녹색 → 황색 → 적색)

---

## 📈 성능 지표 해석

### 캐시 히트율
| 값 | 상태 | 설명 |
|-----|------|------|
| > 90% | ✅ 우수 | 최적 캐시 성능 |
| 80-90% | ⚠️ 주의 | 캐시 TTL 조정 필요 |
| < 80% | 🔴 경고 | 캐시 용량/TTL 점검 필요 |

### 응답 시간 (P95)
| 값 | 상태 | 설명 |
|-----|------|------|
| < 100ms | ✅ 우수 | Phase 1 개선 효과 달성 |
| 100-500ms | ⚠️ 주의 | 캐시 히트율 저하 확인 필요 |
| > 500ms | 🔴 경고 | DB 쿼리 성능 저하 |

### LRU 퇴출율
| 값 | 상태 | 설명 |
|-----|------|------|
| 0/분 | ✅ 우수 | 캐시 용량 충분 |
| 1-5/분 | ⚠️ 주의 | 캐시 사용률 높음 |
| > 5/분 | 🔴 경고 | 캐시 용량 부족, 확장 필요 |

---

## 🚀 사용 방법

### 1️⃣ 모니터링 스택 시작
```bash
# Docker Compose로 Prometheus + Grafana + 기타 도구 시작
docker-compose -f docker-compose.monitoring.yml up -d

# 확인
docker ps | grep -E "prometheus|grafana|alertmanager"
```

### 2️⃣ 메트릭 수집 확인
```bash
# Prometheus UI
http://localhost:9090

# 메트릭 쿼리 예시
http://localhost:9090/graph?expr=cache_hit_rate

# FastAPI 메트릭 엔드포인트
curl http://localhost:8000/metrics
```

### 3️⃣ Grafana 대시보드 접속
```
URL: http://localhost:3001
기본 계정: admin / ${GRAFANA_PASSWORD}
```

**대시보드 찾기:**
- 좌측 메뉴: "Dashboards" → "Performance" 폴더
- 대시보드명: "Cache Performance & API Monitoring (Phase 2 Week 1)"

### 4️⃣ 알림 수신
```bash
# Alertmanager UI
http://localhost:9093

# Teams 알림 설정 (기존 설정)
# monitoring/alertmanager.yml에서 Teams webhook 구성
```

---

## 📊 모니터링 시나리오

### 시나리오 1: 캐시 히트율 저하 감지
```
[대시보드 확인]
1. "KB Search Cache Hit Rate" 게이지 < 80%
2. "Cache Hits vs Misses" 그래프에서 미스 증가
3. "Cache Item Count" 안정적이면 TTL 조정
4. "Cache Item Count" 최대치면 용량 확장

[대응]
- TTL 연장: routes_kb.py에서 default_ttl_seconds 증가
- 용량 증가: memory_cache_service.py에서 max_size 증가
```

### 시나리오 2: API 응답 시간 증가
```
[대시보드 확인]
1. "HTTP Request Latency Percentiles" P95 > 100ms
2. "Cache Hits vs Misses" 미스 증가 확인
3. 캐시 히트율 정상 → DB 쿼리 성능 저하

[대응]
- DB 쿼리 프로파일링: DAY2_BOTTLENECK_ANALYSIS.md 참조
- 인덱스 확인: database/migrations/038_performance_indexes.sql
- 새로운 인덱스 추가 필요 시 gap analysis 진행
```

### 시나리오 3: 캐시 메모리 과다 사용
```
[대시보드 확인]
1. "Cache Size" 게이지 > 100MB
2. "LRU Evictions" 증가 추세
3. "Cache Hit Rate" 저하

[대응]
- 용량 조정: memory_cache_service.py에서 max_size 감소
- TTL 단축: default_ttl_seconds 감소
- 캐시 전략 재검토: TASK3_CACHE_IMPLEMENTATION_COMPLETE.md 참조
```

---

## 📁 생성/수정된 파일 목록

### 신규 파일
- `app/services/metrics_service.py` - Prometheus 메트릭 서비스
- `monitoring/grafana/dashboards/cache-performance.json` - Grafana 대시보드
- `monitoring/grafana/provisioning/dashboards/dashboards.yml` - Grafana provisioning

### 수정 파일
- `pyproject.toml` - prometheus-client 의존성 추가
- `app/services/memory_cache_service.py` - 메트릭 통합
- `app/main.py` - /metrics 엔드포인트 추가
- `monitoring/prometheus-alerts.yml` - 캐시 관련 알림 규칙 추가
- `docker-compose.monitoring.yml` - Grafana 대시보드 마운트 설정 추가

---

## ✅ 검증 항목

- [x] Prometheus 클라이언트 통합
- [x] 메트릭 서비스 구현 (캐시, API, DB, AI)
- [x] Memory Cache Service 메트릭 계측
- [x] FastAPI /metrics 엔드포인트
- [x] Prometheus 설정 (scrape_configs)
- [x] 알림 규칙 (캐시 성능, API 지연, 용량)
- [x] Grafana 대시보드 (12개 패널)
- [x] 대시보드 provisioning
- [x] 문서 및 사용 가이드

---

## 🎯 다음 단계 (Week 2: Data-Driven Optimization)

1. **실시간 데이터 분석**
   - 프로덕션 트래픽 패턴 분석
   - 캐시 히트율 실제 데이터 수집

2. **2차 최적화**
   - 자주 조회되는 쿼리 식별
   - 추가 인덱스 생성
   - 캐시 TTL 동적 조정

3. **성능 튜닝**
   - 고객별 맞춤 캐시 전략
   - 데이터베이스 파티셔닝 검토

---

## 📞 지원

**문제 해결:**
- Prometheus 메트릭 미수집: `docker logs prometheus`
- Grafana 대시보드 미표시: Prometheus 데이터소스 확인
- 알림 미수신: Alertmanager 및 Teams Webhook 확인

**추가 정보:**
- Prometheus 설정: monitoring/prometheus.yml
- 알림 규칙: monitoring/prometheus-alerts.yml
- Grafana 설정: monitoring/grafana/provisioning/

---

**준비 상태:** ✅ 프로덕션 배포 준비 완료  
**배포:** docker-compose -f docker-compose.monitoring.yml up -d  
**다음:** Week 2 - Data-Driven Optimization
