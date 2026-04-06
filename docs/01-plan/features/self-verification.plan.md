# Plan: 플랫폼 자가검증 시스템 (Self-Verification)

## 1. 개요

| 항목 | 내용 |
|------|------|
| Feature | self-verification |
| 목적 | 플랫폼 전체를 주기적으로 자가검증하고, 이상 발견 시 알림 + 자동 복구 |
| 실행 방식 | FastAPI lifespan 내 APScheduler (기존 `setup_scheduler` 확장) |
| 알림 채널 | Teams Webhook (기존 `notification_service.py`) + 구조화 로깅 |

## 2. 기존 인프라 활용

| 기존 자산 | 위치 | 활용 방법 |
|-----------|------|----------|
| `/health` 엔드포인트 | `main.py:279` | DB 연결 체크 이미 존재 → 확장 |
| `setup_scheduler()` | `scheduled_monitor.py:412` | APScheduler 이미 구성 → 검증 잡 추가 |
| `send_teams_notification()` | `notification_service.py:62` | 이상 알림 전송 |
| `session_manager.mark_expired_proposals` | `main.py:108` | lifespan에서 이미 stale 세션 정리 |
| `cleanup_expired_g2b_cache` RPC | `main.py:64` | G2B 캐시 자동 정리 |

## 3. 검증 항목 설계

### 3-1. 인프라 레이어 (매 5분)

| # | 검증 | 판정 기준 | 자동 복구 |
|---|------|----------|----------|
| I-1 | DB 연결 | `SELECT 1` 성공 | 연결 풀 재생성 |
| I-2 | Supabase Storage | 버킷 목록 접근 가능 | - (알림만) |
| I-3 | 메모리/CPU | `psutil` 기반 임계치 | - (알림만) |

### 3-2. 데이터 정합성 (매 30분)

| # | 검증 | 판정 기준 | 자동 복구 |
|---|------|----------|----------|
| D-1 | 마감 경과 공고 | `deadline_date < now`인데 `days_remaining > 0` | `days_remaining` 재계산 |
| D-2 | 고아 추천 레코드 | `bid_recommendations`에 공고 없는 bid_no | 고아 레코드 삭제 |
| D-3 | Stale 세션 | `proposals.status = 'running'` + 마지막 업데이트 >2시간 | `status = 'stale'` 전환 |
| D-4 | MV 최신성 | `mv_team_performance` 갱신 시각 > 24시간 | `REFRESH MATERIALIZED VIEW` |
| D-5 | 파일 캐시-DB 불일치 | `data/bid_status/*.json` vs `bid_announcements.proposal_status` | DB 값으로 파일 덮어쓰기 |

### 3-3. 외부 서비스 (매 1시간)

| # | 검증 | 판정 기준 | 자동 복구 |
|---|------|----------|----------|
| E-1 | G2B API 응답 | 검색 API 호출 → HTTP 200 + 결과 존재 | - (알림만) |
| E-2 | Claude API 잔여 토큰 | `settings.anthropic_api_key` 유효성 + 간단 호출 | - (알림만) |
| E-3 | Teams Webhook | 테스트 메시지 전송 성공 여부 | - (알림만) |

### 3-4. API 스모크 테스트 (매 1시간)

| # | 검증 | 판정 기준 | 자동 복구 |
|---|------|----------|----------|
| A-1 | `GET /health` | status != "degraded" | - |
| A-2 | `GET /api/bids/monitor` | HTTP 200 + `data` 필드 존재 + `attachments`/`bid_stage`/`relevance` 필드 존재 | - (알림만) |
| A-3 | `GET /api/bids/scored` | HTTP 200 + `items` 배열 | - (알림만) |
| A-4 | `GET /api/proposals` | HTTP 200 | - (알림만) |

## 4. 아키텍처

```
┌─────────────────────────────────────────────────┐
│ FastAPI lifespan                                │
│   └── setup_scheduler()                         │
│         ├── [기존] daily_g2b_monitor (매시)      │
│         ├── [기존] daily_summary_email (09:00)   │
│         ├── [기존] prompt_maintenance (02:00)    │
│         │                                       │
│         ├── [신규] infra_check (매 5분)          │
│         ├── [신규] data_integrity_check (매 30분)│
│         └── [신규] service_smoke_test (매 1시간) │
│                     │                           │
│                     ▼                           │
│         ┌──────────────────┐                    │
│         │ HealthCheckRunner │                    │
│         │  .run_all()       │                    │
│         │  .run_category()  │                    │
│         └──────┬───────────┘                    │
│                │                                │
│           ┌────┴────┐                           │
│           ▼         ▼                           │
│     HealthResult  AlertManager                  │
│     (pass/warn/   (Teams + DB 로깅              │
│      fail/fixed)   + 중복 알림 억제)            │
└─────────────────────────────────────────────────┘
```

## 5. 핵심 모듈

### 5-1. `app/services/health_checker.py` (신규)

```python
@dataclass
class HealthResult:
    check_id: str           # "I-1", "D-3" 등
    category: str           # "infra", "data", "external", "api"
    status: Literal["pass", "warn", "fail", "fixed"]
    message: str
    auto_recovered: bool = False
    duration_ms: float = 0

class HealthCheckRunner:
    async def run_all() -> list[HealthResult]
    async def run_category(cat: str) -> list[HealthResult]
    async def run_single(check_id: str) -> HealthResult
```

### 5-2. `app/services/alert_manager.py` (신규)

```python
class AlertManager:
    # 중복 알림 억제: 같은 check_id fail이 30분 이내 반복 시 스킵
    async def handle_results(results: list[HealthResult]) -> None
    async def send_alert(result: HealthResult) -> None
    async def log_to_db(result: HealthResult) -> None
```

### 5-3. 스케줄러 확장 (`scheduled_monitor.py`)

기존 `setup_scheduler()`에 3개 잡 추가.

### 5-4. API 엔드포인트 (`main.py` 또는 별도 라우터)

| 엔드포인트 | 용도 |
|-----------|------|
| `GET /health` | 기존 확장 — 전체 검증 결과 요약 포함 |
| `GET /api/admin/health/detail` | 관리자용 — 최근 검증 이력 + 상세 |
| `POST /api/admin/health/run` | 관리자용 — 수동 즉시 실행 |

## 6. DB 스키마

```sql
CREATE TABLE IF NOT EXISTS health_check_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    check_id TEXT NOT NULL,          -- "I-1", "D-3"
    category TEXT NOT NULL,          -- "infra", "data", "external", "api"
    status TEXT NOT NULL,            -- "pass", "warn", "fail", "fixed"
    message TEXT,
    auto_recovered BOOLEAN DEFAULT FALSE,
    duration_ms REAL,
    checked_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_health_logs_checked ON health_check_logs (checked_at DESC);
CREATE INDEX idx_health_logs_status ON health_check_logs (status) WHERE status != 'pass';
```

## 7. 알림 형식

### Teams Adaptive Card

```
🔴 [FAIL] D-1: 마감 경과 공고 days_remaining 불일치
━━━━━━━━━━━━━━━━━━━━━
발견: 15건 (deadline < now, days_remaining > 0)
자동 복구: ✅ 15건 재계산 완료
시각: 2026-03-26 14:30 KST
━━━━━━━━━━━━━━━━━━━━━
🟢 [FIXED] D-1: 자동 복구 성공
```

### 중복 억제 규칙
- 같은 `check_id` + `status=fail`이 **30분 이내** 재발 → Teams 알림 스킵, DB 로깅만
- `status=fixed` 복구 성공 시 → 항상 알림 (복구 확인)

## 8. 구현 순서

| Phase | 작업 | 파일 | 예상 규모 |
|:-----:|------|------|:---------:|
| **A** | HealthResult + HealthCheckRunner 코어 | `health_checker.py` | ~200줄 |
| **B** | AlertManager (Teams + DB 로깅 + 중복 억제) | `alert_manager.py` | ~100줄 |
| **C** | 인프라 검증 3건 (I-1~I-3) | `health_checker.py` | ~60줄 |
| **D** | 데이터 정합성 5건 (D-1~D-5) + 자동 복구 | `health_checker.py` | ~150줄 |
| **E** | 외부 서비스 3건 (E-1~E-3) | `health_checker.py` | ~80줄 |
| **F** | API 스모크 테스트 4건 (A-1~A-4) | `health_checker.py` | ~60줄 |
| **G** | 스케줄러 통합 + `/health` 확장 | `scheduled_monitor.py`, `main.py` | ~50줄 |
| **H** | 관리자 API + 프론트엔드 상태 페이지 | `routes_admin.py`, 프론트엔드 | ~150줄 |

**총 예상: ~850줄 (백엔드), 프론트엔드 별도**

## 9. 의존성

- `psutil` — 메모리/CPU 모니터링 (I-3). 선택적 (미설치 시 해당 체크 스킵)
- `httpx` — API 스모크 테스트 (내부 HTTP 호출). 이미 사용 중이면 추가 불필요

## 10. 제약 사항 및 결정

| 결정 | 이유 |
|------|------|
| Claude API 검증은 실제 호출 대신 키 유효성만 | 비용 절약 (매시간 토큰 소모 방지) |
| Teams Webhook 테스트는 E-3에서만 (별도 채널) | 운영 채널 스팸 방지 |
| API 스모크 테스트는 내부 함수 호출 (HTTP X) | localhost 셀프 호출보다 안정적 + 빠름 |
| `psutil` 선택적 의존성 | Railway/Render에서 미설치 가능 |

## 11. 성공 기준

- [ ] 15개 검증 항목이 스케줄에 따라 자동 실행
- [ ] fail 발견 시 30초 이내 Teams 알림 전송
- [ ] D-1, D-3, D-4, D-5 자동 복구 정상 작동
- [ ] `GET /health` 응답에 최근 검증 요약 포함
- [ ] `health_check_logs` 테이블에 이력 누적
- [ ] 중복 알림 억제 (30분 이내 같은 fail → 1회만)
