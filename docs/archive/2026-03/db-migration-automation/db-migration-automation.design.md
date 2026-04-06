# DB 마이그레이션 자동화 - 설계 문서

**Feature**: DB Migration Automation
**Status**: Design Phase
**Created**: 2026-03-30
**Referenced Plan**: `docs/01-plan/features/db-migration-automation.plan.md`

---

## 1. 아키텍처 개요

### 1.1 시스템 구성도

```
┌─────────────────────────────────────────────────────────────┐
│                   애플리케이션 시작                        │
│                   (app/main.py)                             │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Lifespan Context Manager                       │
│  ├─ Supabase 클라이언트 초기화                             │
│  ├─ Storage 버킷 생성                                      │
│  ├─ 세션 복원                                              │
│  └─ ⭐ 마이그레이션 자동 실행 (NEW)                       │
└────────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│        apply_migrations.py (비동기 실행)                  │
│  ├─ migration_history 테이블 확인                         │
│  ├─ 미적용 마이그레이션 감지 (000~019)                    │
│  └─ 순차 실행 with 오류 처리                              │
└────────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│             Supabase PostgreSQL (pooler)                   │
│  ├─ 000_init_migrations.sql (마이그레이션 테이블)         │
│  ├─ 001~019_*.sql (실제 마이그레이션)                     │
│  └─ migration_history (실행 기록)                         │
└─────────────────────────────────────────────────────────────┘

API 엔드포인트 (선택적 조회):
  GET /api/migrations/status   → 마이그레이션 상태
  GET /api/migrations/history  → 실행 이력
  GET /api/migrations/summary  → 통계
```

### 1.2 데이터 흐름

```
┌──────────────────┐
│ 마이그레이션     │
│ 파일 (004~019)   │
└────────┬─────────┘
         │ 읽기
         ↓
┌──────────────────────────────────┐
│ apply_migrations.py              │
│ ├─ 파일명 → 버전 추출 (sorting) │
│ ├─ migration_history 조회        │
│ └─ 미적용 목록 필터링            │
└────────┬─────────────────────────┘
         │ 버전순 정렬 (000→019)
         ↓
┌──────────────────────────────────┐
│ 각 마이그레이션 실행             │
│ ├─ SQL 파싱 (;로 분리)           │
│ ├─ 주석 제거                     │
│ └─ 트랜잭션 내 실행              │
└────────┬──────────────────────────┘
         │ 성공/실패
         ↓
┌──────────────────────────────────┐
│ migration_history 기록           │
│ ├─ version, name                 │
│ ├─ applied_at, status            │
│ ├─ execution_time_ms             │
│ └─ error_message (실패 시)       │
└──────────────────────────────────┘
```

---

## 2. 데이터 스키마

### 2.1 migration_history 테이블

```sql
CREATE TABLE public.migration_history (
    id BIGSERIAL PRIMARY KEY,

    -- 식별자
    version VARCHAR(255) NOT NULL UNIQUE,     -- "000", "001", ..., "019"
    name VARCHAR(500) NOT NULL,               -- "000_init_migrations"

    -- 타임스탬프
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- 실행 정보
    execution_time_ms INT,                    -- 밀리초 단위
    status VARCHAR(20) DEFAULT 'success',     -- 'success', 'failed', 'rolled_back'
    error_message TEXT,                       -- 오류 메시지 (500자 제한)

    -- 감사
    created_by VARCHAR(255) DEFAULT 'system'  -- 실행자 (시스템 또는 관리자)
);

-- 인덱스
CREATE INDEX idx_migration_history_version ON public.migration_history(version);
CREATE INDEX idx_migration_history_applied_at ON public.migration_history(applied_at DESC);
CREATE INDEX idx_migration_history_status ON public.migration_history(status);
```

### 2.2 데이터 예시

```
version | name                              | applied_at        | execution_time_ms | status  | error_message
--------|-----------------------------------|--------------------|-------------------|---------|---------------
000     | 000_init_migrations               | 2026-03-30 17:05  | 150               | success | NULL
004     | 004_performance_views             | 2026-03-30 17:06  | 320               | success | NULL
005     | 005_bids_and_users                | 2026-03-30 17:06  | 280               | success | NULL
...
019     | 019_unified_state_system          | 2026-03-30 17:12  | 450               | success | NULL
```

---

## 3. 파일 구조

### 3.1 신규 파일

```
database/
├── migrations/
│   └── 000_init_migrations.sql (신규)
│       └── migration_history 테이블 + 함수 정의

scripts/
├── apply_migrations.py (신규)
│   ├─ 마이그레이션 조회 및 정렬
│   ├─ 적용된 마이그레이션 감지
│   ├─ SQL 실행 (비동기)
│   ├─ 에러 처리 및 기록
│   └─ CLI 옵션 (--status, --dry-run, --rollback)
```

### 3.2 수정 파일

```
app/
├── main.py (수정)
│   ├─ lifespan() 함수에 마이그레이션 호출 추가
│   ├─ try-except로 실패 처리 (경고만)
│   └─ 비동기 호출
│
├── api/
│   └── routes_migrations.py (확장)
│       ├─ GET /api/migrations/status
│       ├─ GET /api/migrations/history
│       └─ GET /api/migrations/summary
```

---

## 4. 상세 설계

### 4.1 migration_history 테이블 초기화 (000_init_migrations.sql)

```sql
-- 1️⃣ 기본 테이블 생성
CREATE TABLE IF NOT EXISTS public.migration_history (
    id BIGSERIAL PRIMARY KEY,
    version VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(500) NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INT,
    status VARCHAR(20) DEFAULT 'success' CHECK (status IN ('success', 'failed', 'rolled_back')),
    error_message TEXT,
    created_by VARCHAR(255) DEFAULT 'system'
);

-- 2️⃣ 인덱스
CREATE INDEX IF NOT EXISTS idx_migration_history_version ON public.migration_history(version);
CREATE INDEX IF NOT EXISTS idx_migration_history_applied_at ON public.migration_history(applied_at DESC);

-- 3️⃣ 조회 함수 (선택사항)
CREATE OR REPLACE FUNCTION get_migration_status()
RETURNS TABLE (
    total_migrations BIGINT,
    applied_migrations BIGINT,
    failed_migrations BIGINT,
    last_applied_at TIMESTAMPTZ
) AS $$
SELECT
    COUNT(DISTINCT version) as total,
    COUNT(*) FILTER (WHERE status = 'success') as applied,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    MAX(applied_at) FILTER (WHERE status = 'success') as last
FROM migration_history;
$$ LANGUAGE SQL;

-- 4️⃣ 초기 기록 삽입
INSERT INTO migration_history (version, name, status, execution_time_ms)
VALUES ('000', '000_init_migrations - Migration tracking table', 'success', 0)
ON CONFLICT (version) DO NOTHING;
```

### 4.2 apply_migrations.py (마이그레이션 자동 실행)

#### 주요 함수

```python
# 1️⃣ DB 연결
async def get_db_connection() -> asyncpg.Connection:
    """PostgreSQL 직접 연결 (asyncpg)"""
    - DATABASE_URL 환경변수에서 URL 추출
    - SSL=False (Supabase 풀러 호환)
    - timeout=30초
    - 오류 처리: SSL, 네트워크, 권한

# 2️⃣ 적용된 마이그레이션 조회
async def get_applied_migrations(conn) -> set:
    """migration_history에서 성공한 것만 조회"""
    - SELECT version FROM migration_history WHERE status='success'
    - 반환: {'000', '004', '005', ...}
    - 오류 시: 빈 set 반환 (초기 상태)

# 3️⃣ 마이그레이션 파일 조회
async def get_migration_files() -> list:
    """database/migrations/*.sql 모두 조회"""
    - glob으로 파일 검색
    - 파일명에서 버전 추출 (정렬)
    - 반환: [{'version': '000', 'filename': '000_init_migrations.sql', ...}, ...]

# 4️⃣ SQL 파일 읽기
async def read_migration_file(path: Path) -> str:
    """UTF-8으로 파일 읽기"""

# 5️⃣ 개별 마이그레이션 실행
async def apply_migration(conn, version, filename, sql_content, dry_run=False) -> bool:
    """한 개 마이그레이션 실행"""
    - SQL 구문 분리 (;로 분리)
    - 주석 제거
    - 트랜잭션 내 실행
    - migration_history 기록
    - 오류 시: error_message 저장, False 반환
    - 실행시간 측정: time.time()

# 6️⃣ 전체 마이그레이션 실행
async def apply_all_migrations(dry_run=False) -> dict:
    """모든 미적용 마이그레이션 순차 실행"""
    1. 000_init_migrations 먼저 실행
    2. 적용된 마이그레이션 조회
    3. 미적용 필터링
    4. 순차 실행 (병렬화 금지)
    5. 통계 반환

# 7️⃣ 상태 조회
async def show_migration_status() -> None:
    """마이그레이션 현황 출력"""
    - 전체 / 적용 / 실패 / 대기 통계
    - 파일별 상태 테이블
    - 최근 적용 시간
```

#### CLI 옵션

```bash
# 모든 미적용 마이그레이션 실행
uv run python scripts/apply_migrations.py

# 상태 조회만
uv run python scripts/apply_migrations.py --status

# 실행 예정 파일만 확인 (실행 안함)
uv run python scripts/apply_migrations.py --dry-run

# 특정 마이그레이션 롤백 (향후)
uv run python scripts/apply_migrations.py --rollback 019
```

#### 출력 예시

```
[OK] DATABASE_URL configured: postgresql://...

[INIT] 마이그레이션 추적 테이블 초기화...
  [000] 000_init_migrations.sql... [OK] 0.15s

[MIGRATION] 19개 마이그레이션 적용 예정
──────────────────────────────────────────────
  [004] 004_performance_views.sql... [OK] 0.32s
  [005] 005_bids_and_users.sql... [OK] 0.28s
  ...
  [019] 019_unified_state_system.sql... [OK] 0.45s
──────────────────────────────────────────────

[SUMMARY]
  성공: 19개
  실패: 0개
  총계: 19개 / 적용됨: 19개
```

### 4.3 app/main.py (lifespan 통합)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기"""
    logger.info("Proposal Architect v4.0 시스템 시작")

    # 기존 코드...
    # - Supabase 초기화
    # - Storage 버킷 생성
    # - 세션 복원

    # ⭐ 신규: 마이그레이션 자동 실행
    try:
        from scripts.apply_migrations import apply_all_migrations
        logger.info("DB 마이그레이션 시작...")

        result = await apply_all_migrations(dry_run=False)

        if result['status'] in ['up_to_date', 'completed']:
            logger.info(f"마이그레이션 완료: {result['applied']}/{result['total']}")
        else:
            logger.warning(f"마이그레이션 부분 실패: {result['failed']} 오류")
            # 실패해도 앱 시작 (경고만)

    except Exception as e:
        logger.warning(f"마이그레이션 초기화 실패 (무시됨): {e}")
        # 실패해도 앱은 정상 시작

    yield  # 앱 실행

    # 종료 처리...
```

### 4.4 API 엔드포인트

#### 4.4.1 GET /api/migrations/status

```
요청:
  GET /api/migrations/status
  Authorization: Bearer {token}
  권한: admin

응답 (200 OK):
{
  "status": "ok",
  "total": 19,
  "successful": 19,
  "failed": 0,
  "migrations": [
    {
      "version": "000",
      "name": "000_init_migrations",
      "applied_at": "2026-03-30T17:05:00Z",
      "status": "success",
      "execution_time_ms": 150
    },
    ...
  ]
}

응답 (401):
{
  "detail": "Not authenticated"
}

응답 (403):
{
  "detail": "Insufficient permissions"
}
```

#### 4.4.2 GET /api/migrations/history

```
요청:
  GET /api/migrations/history?limit=50&offset=0
  Authorization: Bearer {token}
  권한: admin

응답 (200 OK):
{
  "total": 19,
  "limit": 50,
  "offset": 0,
  "data": [
    {
      "id": 1,
      "version": "000",
      "name": "000_init_migrations",
      "applied_at": "2026-03-30T17:05:00Z",
      "execution_time_ms": 150,
      "status": "success",
      "error_message": null
    },
    ...
  ]
}
```

#### 4.4.3 GET /api/migrations/summary

```
요청:
  GET /api/migrations/summary
  Authorization: Bearer {token}
  권한: admin

응답 (200 OK):
{
  "total": 19,
  "applied": 19,
  "failed": 0,
  "pending": 0,
  "success_rate": "100.0%",
  "last_applied_at": "2026-03-30T17:12:00Z"
}
```

---

## 5. 에러 처리

### 5.1 예상 오류 및 처리 전략

| 오류 | 원인 | 처리 | 심각도 |
|------|------|------|--------|
| **SSL Error** | Supabase 풀러 SSL | `ssl=False` 옵션 | 낮음 |
| **Connection Timeout** | 네트워크 지연 | 재시도 3회, timeout=30s | 중간 |
| **SQL Syntax Error** | 파일 내용 오류 | error_message 기록, 계속 진행 | 중간 |
| **Permission Denied** | 권한 부족 | 오류 로깅, 앱 시작 (경고) | 낮음 |
| **Duplicate Migration** | 이미 적용됨 | `ON CONFLICT DO NOTHING` | 없음 |
| **File Not Found** | 마이그레이션 파일 누락 | 스킵, 로그 출력 | 매우낮음 |

### 5.2 재시도 로직

```python
# 각 마이그레이션에 대해
for attempt in range(1, 4):  # 3회 시도
    try:
        await apply_migration(...)
        break  # 성공하면 탈출
    except Exception as e:
        if attempt < 3:
            logger.warning(f"재시도 {attempt}/3: {e}")
            await asyncio.sleep(2 ** attempt)  # 지수 백오프
        else:
            logger.error(f"최종 실패: {e}")
            # error_message 기록 후 계속
```

---

## 6. 성능 고려사항

### 6.1 실행 시간 목표

```
목표: 19개 마이그레이션 < 60초

예상 분석:
  - 000_init_migrations:    150ms
  - 004~006 (Core):        1,000ms (~5 파일)
  - 007~014 (Features):    8,000ms (~8 파일)
  - 015~019 (Integration): 4,000ms (~5 파일)
  ────────────────────────
  총계:                    13,150ms (약 13초)
  + Supabase 오버헤드:      2,000ms (연결, 풀러)
  + 여유:                   8,000ms
  ────────────────────────
  예상 총시간:            23초 ✅ (목표 60초)
```

### 6.2 최적화 전략

| 전략 | 효과 | 비고 |
|------|------|------|
| 병렬 실행 금지 | 안정성 | Supabase 제약 |
| 트랜잭션 최소화 | 50ms 단축 | 각 마이그레이션별 1개만 |
| 배치 커밋 | 30ms 단축 | 여러 SQL 문을 하나의 쿼리로 |
| 인덱스 지연 | 20ms 단축 | 테이블 생성 후 인덱스 생성 |
| 연결 재사용 | 100ms 단축 | 한 개 연결로 모든 마이그레이션 |

---

## 7. 보안

### 7.1 접근 제어

```python
# API 엔드포인트
@router.get("/status")
async def get_migration_status(
    current_user = Depends(require_role("admin"))  # admin만
):
    ...
```

### 7.2 SQL Injection 방지

```python
# asyncpg의 매개변수화된 쿼리 사용
await conn.execute(
    "INSERT INTO migration_history (version, name, status) VALUES ($1, $2, $3)",
    version,    # $1
    filename,   # $2
    'success'   # $3
)
```

### 7.3 감사 추적

```
모든 마이그레이션 실행은 migration_history에 기록:
- 누가: created_by (시스템 또는 관리자 ID)
- 언제: applied_at (UTC 타임스탐프)
- 무엇: version, name (마이그레이션 정보)
- 결과: status, error_message (성공/실패)
```

---

## 8. 의존성

### 8.1 라이브러리

```python
# pyproject.toml / requirements.txt
asyncpg>=0.28.0         # PostgreSQL 비동기 드라이버
python-dotenv>=1.0.0    # .env 파일 로드
supabase>=2.0.0         # 기존 (Supabase 클라이언트)
fastapi>=0.100.0        # 기존 (웹 프레임워크)
```

### 8.2 환경 변수

```
DATABASE_URL=postgresql://user:password@host:port/db
# 필수, Supabase 풀러 연결 정보
```

---

## 9. 구현 순서

### Phase: Do (구현 단계)

| # | 항목 | 파일 | 순서 | 의존성 |
|----|------|------|------|--------|
| 1 | migration_history 테이블 | 000_init_migrations.sql | 1순위 | 없음 |
| 2 | apply_migrations.py | scripts/apply_migrations.py | 2순위 | 1번 |
| 3 | main.py lifespan 통합 | app/main.py | 3순위 | 2번 |
| 4 | API 엔드포인트 | app/api/routes_migrations.py | 4순위 | 1번 |
| 5 | 통합 테스트 | tests/test_migrations.py | 5순위 | 1~4번 |

---

## 10. 테스트 전략

### 10.1 단위 테스트

```python
# test_apply_migrations.py

def test_get_applied_migrations():
    """적용된 마이그레이션 조회"""
    # Fixture: migration_history에 데이터 삽입
    # 예상: {'000', '004', '005'} 반환

def test_get_migration_files():
    """마이그레이션 파일 조회"""
    # 예상: 19개 파일 검색, 버전순 정렬

def test_apply_migration_success():
    """마이그레이션 실행 성공"""
    # Fixture: 간단한 CREATE TABLE SQL
    # 예상: migration_history에 기록, status='success'

def test_apply_migration_failure():
    """마이그레이션 실행 실패"""
    # Fixture: 잘못된 SQL
    # 예상: error_message 기록, status='failed'

def test_dry_run():
    """드라이런 (실행하지 않고 확인)"""
    # 예상: migration_history 변경 없음
```

### 10.2 통합 테스트

```python
# test_migrations_integration.py

@pytest.mark.asyncio
async def test_full_migration_flow():
    """전체 마이그레이션 흐름"""
    # 1. 깨끗한 DB 준비
    # 2. apply_all_migrations() 실행
    # 3. migration_history 검증 (19개 모두 성공)
    # 4. 스키마 검증 (예상 테이블 존재)

@pytest.mark.asyncio
async def test_api_endpoints():
    """API 엔드포인트 테스트"""
    # 1. GET /api/migrations/status → 200 + 데이터
    # 2. GET /api/migrations/history → 200 + 페이지 처리
    # 3. GET /api/migrations/summary → 200 + 통계
    # 4. 비인증 사용자 → 401 Unauthorized
```

---

## 11. 롤백 전략 (v2)

### 11.1 수동 롤백

```bash
# 특정 마이그레이션 롤백
uv run python scripts/apply_migrations.py --rollback 019

# 동작:
# 1. 019_unified_state_system_rollback.sql 실행
# 2. migration_history에서 019 제거 (또는 status='rolled_back')
# 3. 로그 출력
```

### 11.2 자동 롤백

```python
# 마이그레이션 실패 시 자동 롤백 (향후)
try:
    async with conn.transaction():
        await conn.execute(migration_sql)
        await record_migration_success(...)
except Exception:
    # 트랜잭션 자동 롤백 (asyncpg)
    await record_migration_failure(...)
```

---

## 12. 모니터링 및 로깅

### 12.1 로그 레벨

```
DEBUG:  SQL 구문, 파일 읽기 상세
INFO:   마이그레이션 시작/완료, 통계
WARN:   재시도, 타임아웃, 부분 실패
ERROR:  연결 실패, 최종 오류
```

### 12.2 구조화 로깅 (JSON)

```json
{
  "timestamp": "2026-03-30T17:05:00Z",
  "level": "INFO",
  "service": "migrations",
  "message": "Migration applied",
  "data": {
    "version": "000",
    "filename": "000_init_migrations.sql",
    "execution_time_ms": 150,
    "status": "success"
  }
}
```

---

## 13. 리스크 및 완화

| 리스크 | 영향 | 완화 |
|--------|------|------|
| SSL 연결 실패 | 마이그레이션 불가 | ssl=False 옵션, 풀러 활용 |
| 네트워크 지연 | 시간 초과 | 재시도 3회, timeout 증가 |
| 권한 부족 | 특정 마이그레이션 실패 | service_role 키 사용 |
| 파일 손상 | SQL 오류 | error_message 기록, 계속 진행 |
| 중복 적용 | 오류 발생 | unique 제약 + ON CONFLICT |

---

## 14. 구현 체크리스트

### 14.1 Core (필수)

- [ ] 000_init_migrations.sql 생성
- [ ] apply_migrations.py 완성 (asyncpg, 에러 처리)
- [ ] main.py lifespan 통합
- [ ] Supabase 환경에서 테스트

### 14.2 API (High Priority)

- [ ] /api/migrations/status 구현
- [ ] /api/migrations/history 구현
- [ ] /api/migrations/summary 구현
- [ ] 접근 제어 (require_role)

### 14.3 문서화

- [ ] 사용 가이드 (--status, --dry-run)
- [ ] API 명세 (OpenAPI)
- [ ] 마이그레이션 추가 방법
- [ ] 트러블슈팅 가이드

### 14.4 테스트

- [ ] 단위 테스트 (apply_migration, 오류 처리)
- [ ] 통합 테스트 (전체 마이그레이션)
- [ ] API 테스트 (엔드포인트, 권한)
- [ ] 성능 테스트 (< 60초)

---

## 다음 단계

→ `/pdca do db-migration-automation` (Do 단계: 구현)
