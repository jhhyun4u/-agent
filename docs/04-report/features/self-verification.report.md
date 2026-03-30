# PDCA Completion Report: 플랫폼 자가검증 시스템 (Self-Verification)

## 개요

| 항목 | 값 |
|------|-----|
| Feature | self-verification |
| PDCA 사이클 | Plan → Design → Do → Check → Report (전체) |
| 완료일 | 2026-03-26 |
| Match Rate | **99%** |
| 신규 파일 | 3개 |
| 기존 확장 | 5개 |
| 총 코드량 | ~500줄 (백엔드) |

## 무엇을 만들었나

플랫폼 전체를 **주기적으로 자가검증**하고, 이상 발견 시 **Teams 알림 + 자동 복구**하는 시스템.

```
APScheduler (FastAPI lifespan)
  ├── 매 5분:  인프라 (DB, Storage, 리소스)
  ├── 매 30분: 데이터 정합성 (5개 항목 + 자동 복구)
  └── 매 1시간: 외부 서비스 + API 스모크 테스트
         │
         ▼
  HealthCheckRunner (15개 체크)
         │
    ┌────┴────┐
    ▼         ▼
 HealthResult  AlertManager
 (pass/warn/   (Teams 알림
  fail/fixed)   + DB 로깅
                + 30분 중복 억제)
```

## 15개 검증 항목

### 인프라 (매 5분)

| ID | 검증 | 자동 복구 |
|----|------|:---------:|
| I-1 | DB 연결 (SELECT + 연결 풀 재생성) | ✅ |
| I-2 | Supabase Storage 버킷 접근 | - |
| I-3 | 메모리/CPU (psutil, 선택적) | - |

### 데이터 정합성 (매 30분)

| ID | 검증 | 자동 복구 |
|----|------|:---------:|
| D-1 | 마감 경과 공고 days_remaining 불일치 → 재계산 | ✅ |
| D-2 | 고아 추천 레코드 (공고 없는 bid_no) → 삭제 | ✅ |
| D-3 | Stale 세션 (running >2시간) → stale 전환 | ✅ |
| D-4 | MV 최신성 (>24시간) → REFRESH | ✅ |
| D-5 | 파일 캐시-DB 불일치 → DB 기준 동기화 | ✅ |

### 외부 서비스 (매 1시간)

| ID | 검증 | 자동 복구 |
|----|------|:---------:|
| E-1 | G2B API 응답 확인 | - |
| E-2 | Claude API 키 형식 확인 (호출 X, 비용 절약) | - |
| E-3 | Teams Webhook 접근 확인 (HEAD, 메시지 X) | - |

### API 스모크 (매 1시간)

| ID | 검증 | 자동 복구 |
|----|------|:---------:|
| A-1 | /health 내부 호출 | - |
| A-2 | 모니터 API 응답 구조 + 필수 필드 검증 | - |
| A-3 | 스코어링 함수 정상 작동 | - |
| A-4 | proposals 테이블 접근 | - |

## 변경 파일

| 파일 | 상태 | 내용 | 규모 |
|------|:----:|------|:----:|
| `app/services/health_checker.py` | 신규 | HealthResult + HealthCheckRunner + 15개 체크 | ~300줄 |
| `app/services/alert_manager.py` | 신규 | Teams 알림 + DB 로깅 + 중복 억제 | ~80줄 |
| `database/migrations/012_health_check_logs.sql` | 신규 | 이력 테이블 + 인덱스 3개 | ~20줄 |
| `app/config.py` | 확장 | 설정 6개 (임계치, 억제 시간) | +7줄 |
| `app/utils/supabase_client.py` | 확장 | `reset_client()` (스레드 안전) | +7줄 |
| `app/services/scheduled_monitor.py` | 확장 | 잡 3개 (5분/30분/1시간) | +40줄 |
| `app/main.py` | 확장 | `/health` 응답에 검증 요약 + failing 목록 | +20줄 |
| `app/api/routes_admin.py` | 확장 | `GET /admin/health/detail` + `POST /admin/health/run` | +50줄 |

## 알림 시스템

### Teams Adaptive Card 형식

```
🔴 [FAIL] D-1: 자가검증
days_remaining 불일치 15건 → 15건 재계산
자동 복구: ✅
상세: found=15, fixed=15
```

### 중복 억제

- 같은 `check_id` + `fail` → **30분 이내 재발 시 Teams 스킵** (DB 로깅만)
- `fixed` (복구 성공) → **항상 알림** (복구 확인)
- 억제 시간: `settings.health_suppress_minutes`로 설정 가능

## 관리자 API

| 엔드포인트 | 용도 |
|-----------|------|
| `GET /health` | 공개 — DB + 최근 검증 요약 (fail 건수, failing 목록) |
| `GET /api/admin/health/detail?category=data&hours=24` | 관리자 — 최근 이력 상세 (필터링) |
| `POST /api/admin/health/run?check_id=D-1` | 관리자 — 수동 즉시 실행 |

## 설정 (config.py)

| 설정 | 기본값 | 용도 |
|------|:------:|------|
| `health_check_enabled` | `True` | 전체 on/off |
| `health_suppress_minutes` | `30` | 중복 알림 억제 시간 |
| `health_resource_warn_pct` | `75` | I-3 리소스 경고 % |
| `health_resource_fail_pct` | `90` | I-3 리소스 위험 % |
| `health_mv_max_hours` | `24` | D-4 MV 허용 경과 시간 |
| `health_stale_session_hours` | `2` | D-3 Stale 판정 시간 |

## Gap Analysis 결과

| 설계 섹션 | Match |
|-----------|:-----:|
| DB Schema | 100% |
| HealthResult | 100% |
| Runner 엔진 | 98% |
| 인프라 I-1~3 | 99% |
| 데이터 D-1~5 | 97% |
| 외부 E-1~3 | 100% |
| API A-1~4 | 100% |
| AlertManager | 97% |
| 스케줄러 | 100% |
| API 엔드포인트 | 97% |
| reset_client | 100% |
| Config | 100% |
| **Overall** | **99%** |

7건 차이 모두 설계 대비 **개선** (설정 가능화, 스레드 안전, 쿼리 최적화). 누락/회귀 0건.

## 검증

| 항목 | 결과 |
|------|------|
| ruff check (신규 2파일) | 0 에러 |
| import 검증 | 성공 |
| 순환 import | 없음 |

## 배포 체크리스트

- [ ] `012_health_check_logs.sql` 마이그레이션 실행
- [ ] D-4 MV RPC 등록: `check_mv_freshness`, `refresh_performance_views`
- [ ] `psutil` 설치 여부 확인 (선택적, I-3)
- [ ] `settings.teams_webhook_url` 설정 확인 (알림 수신)
- [ ] `settings.health_check_enabled = True` 확인

## 향후 개선 (선택)

| 항목 | 우선순위 |
|------|:--------:|
| 프론트엔드 관리자 헬스 대시보드 페이지 | LOW |
| 30일 이상 pass 로그 자동 삭제 (pg_cron) | LOW |
| 검증 항목 추가: WebSocket 연결, 큐 깊이 등 | LOW |
| E-2 Claude API 실제 호출 검증 (일 1회 제한) | LOW |
