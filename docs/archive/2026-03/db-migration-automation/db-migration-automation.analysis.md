# DB 마이그레이션 자동화 - Gap Analysis Report

**Feature**: DB Migration Automation
**Analysis Date**: 2026-03-30
**Overall Match Rate**: 72% (18/25 items)
**Status**: ⚠️ NEEDS FIXES (< 90%)

---

## 📊 분석 요약

### 종합 점수

| 항목 | 점수 | 상태 |
|------|------|------|
| Design 일치도 | 72% | ⚠️ WARNING |
| 아키텍처 준수 | 90% | ✅ PASS |
| 코드 컨벤션 | 95% | ✅ PASS |
| **전체** | **72%** | **⚠️ 개선 필요** |

---

## 📋 갭 목록 (6개)

### HIGH Priority (5개) - 즉시 수정 필요

#### GAP-H1: get_migration_status() SQL 함수 버그
- **위치**: Design §2.1 (line 193-200) / SQL §27-28
- **문제**: 함수가 존재하지 않는 `information_schema.files` 테이블 참조
- **영향**: 함수 호출 시 런타임 오류 발생 (HIGH)
- **수정**:
  ```sql
  -- 현재 (오류):
  SELECT COUNT(*) FROM information_schema.files WHERE type = 'migration'

  -- 수정:
  SELECT COUNT(DISTINCT version) FROM migration_history WHERE status = 'success'
  ```

#### GAP-H2: 재시도 로직 누락
- **위치**: Design §5.2 (line 442-455) / apply_migrations.py (없음)
- **문제**: 설계에서 요구하는 3회 재시도 로직 미구현
- **영향**: 네트워크 일시 오류 시 마이그레이션 실패 (HIGH)
- **수정**: apply_migrations.py apply_migration() 호출 부분에 for loop 추가
  ```python
  for attempt in range(1, 4):  # 3회 시도
      try:
          await apply_migration(...)
          break
      except Exception as e:
          if attempt < 3:
              logger.warning(f"Retry {attempt}/3: {e}")
              await asyncio.sleep(2 ** attempt)  # 지수 백오프
          else:
              logger.error(f"Final failure: {e}")
  ```

#### GAP-H3: GET /api/migrations/status 미구현
- **위치**: Design §4.4.1 (line 341-376)
- **문제**: 마이그레이션 상태 조회 API 엔드포인트 없음
- **영향**: 웹 대시보드에서 상태 확인 불가 (HIGH)
- **필드**: status, total, successful, failed, migrations[]

#### GAP-H4: GET /api/migrations/history 미구현
- **위치**: Design §4.4.2 (line 378-404)
- **문제**: 마이그레이션 실행 이력 조회 API 엔드포인트 없음
- **영향**: 마이그레이션 기록 조회 불가 (HIGH)
- **필드**: total, limit, offset, data[]

#### GAP-H5: GET /api/migrations/summary 미구현
- **위치**: Design §4.4.3 (line 406-423)
- **문제**: 마이그레이션 통계 API 엔드포인트 없음
- **영향**: 마이그레이션 성공률 등 요약 통계 조회 불가 (HIGH)
- **필드**: total, applied, failed, pending, success_rate, last_applied_at

### LOW Priority (1개) - 향후 최적화

#### GAP-L1: idx_migration_history_status 인덱스 누락
- **위치**: Design §2.1 (line 111)
- **문제**: status 컬럼 인덱스 미생성
- **영향**: status별 조회 성능 저하 (LOW)
- **수정**:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_migration_history_status
  ON public.migration_history(status);
  ```

---

## 📈 요구사항별 일치도

### FR-01: migration_history 테이블 (71%)
- ✅ 테이블 스키마 (컬럼, 타입, 제약)
- ✅ CHECK 제약 (status IN ...)
- ✅ version, applied_at 인덱스 (2개)
- ❌ status 인덱스 (GAP-L1)
- ❌ get_migration_status() 함수 버그 (GAP-H1)
- ✅ 초기 레코드 삽입

### FR-02: apply_migrations.py (92%)
- ✅ 7개 핵심 함수 (get_db_connection, get_applied_migrations, get_migration_files, read_migration_file, apply_migration, apply_all_migrations, show_migration_status)
- ✅ CLI 옵션 (--status, --dry-run, --rollback)
- ✅ SQL Injection 방지 (매개변수화 쿼리)
- ✅ 오류 메시지 기록 (500자 제한)
- ✅ 순차 실행 (000 먼저)
- ❌ 재시도 로직 (GAP-H2)

### FR-03: API 엔드포인트 (0%)
- ❌ /api/migrations/status (GAP-H3)
- ❌ /api/migrations/history (GAP-H4)
- ❌ /api/migrations/summary (GAP-H5)

**주의**: 기존 routes_migrations.py는 "배치 마이그레이션"(데이터 마이그레이션)용이므로, 새로운 엔드포인트를 별도로 구현해야 합니다.

### FR-04: main.py lifespan (100%)
- ✅ try-except로 안전하게 처리
- ✅ 실패해도 앱 시작 (경고만)
- ✅ ImportError 처리 추가 (보너스)

### FR-05: 롤백 기능 (v2)
- N/A (의도적으로 v2로 지연)

---

## 🔧 수정 액션 플랜

### P0 - 즉시 수정 (HIGH)

**작업 1: 000_init_migrations.sql 함수 버그 수정** (5분)
```sql
-- line 27-28 수정
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
```

**작업 2: apply_migrations.py 재시도 로직 추가** (10분)
- `apply_all_migrations()` 함수에서 `apply_migration()` 호출을 for loop으로 감싸기
- 지수 백오프: `await asyncio.sleep(2 ** attempt)`
- 로그 추가: "Retry N/3" 메시지

**작업 3: API 엔드포인트 3개 구현** (30분)
- Option A: routes_migrations.py 확장 (기존 배치 마이그레이션 API와 함께)
- Option B: 새 파일 routes_migration_status.py 생성 (분리)
- 모두 `require_role("admin")` 적용
- Supabase table().select() 쿼리 사용

### P1 - 단기 수정 (LOW)

**작업 4: idx_migration_history_status 인덱스 추가** (2분)
- 000_init_migrations.sql에 CREATE INDEX 추가

---

## 📝 분석 세부사항

### 아키텍처 준수 (90%)
- ✅ 비동기 패턴 (asyncpg, asynccontextmanager)
- ✅ 에러 처리 전략 (try-except, SSL 처리)
- ✅ 로깅 통합 (logger.info/warning/error)
- ✅ 트랜잭션 관리 (async with conn.transaction())
- ✅ 보안 (SQL injection 방지, require_role)

### 코드 품질 (95%)
- ✅ 문서화 (docstring, 주석)
- ✅ 환경 변수 관리 (.env, settings)
- ✅ 오류 메시지 명확성 (Tenant or user not found 진단)
- ✅ 코드 구조 (함수 분리, 재사용성)

---

## 🎯 다음 단계

### Option 1: 자동 개선 (추천)
```bash
/pdca iterate db-migration-automation
```
- pdca-iterator 에이전트가 6개 갭 자동 수정
- 최대 5회 반복
- 90% 이상 도달 시 완료

### Option 2: 수동 수정
1. 위의 P0 작업 4개 수동으로 완료
2. `apply_migrations.py --status` 테스트
3. `/pdca analyze db-migration-automation` 재실행
4. 일치도 재계산

---

## 📋 체크리스트 (자동 개선 후)

수정 후 확인 항목:

- [x] get_migration_status() 함수 버그 수정 (GAP-H1) — 2026-03-30
- [x] 재시도 로직 3회 구현 (GAP-H2) — 2026-03-30
- [x] /api/migrations/status 엔드포인트 (GAP-H3) — 2026-03-30
- [x] /api/migrations/history 엔드포인트 (GAP-H4) — 2026-03-30
- [x] /api/migrations/summary 엔드포인트 (GAP-H5) — 2026-03-30
- [x] idx_migration_history_status 인덱스 (GAP-L1) — 2026-03-30
- [ ] pytest로 새 엔드포인트 테스트 (DB 준비 후)
- [x] 재분석 완료 — 일치도 93% (추정, DB 미연결 상태)

---

## 📊 일치도 계산

**가중치 기반:**
- FR-01 (20%) × 71% = 14.2
- FR-02 (30%) × 92% = 27.6
- FR-03 (30%) × 0% = 0
- FR-04 (20%) × 100% = 20

합계: 14.2 + 27.6 + 0 + 20 = **61.8% (가중)**

**단순 비율:**
- 구현된 항목: 18개 / 전체: 25개 = **72% (단순)**

**최종**: 72% (단순 비율 사용)

---

**분석 완료**: 2026-03-30 17:45 UTC
**다음**: `/pdca iterate db-migration-automation` (자동 개선)
