# DB 마이그레이션 자동화 - 요구사항 문서

**Feature**: DB Migration Automation
**Level**: Enterprise
**Status**: Planning
**Created**: 2026-03-30
**Owner**: tenopa DevOps Team

---

## 1. 개요

### 1.1 목표
- **현황**: 19개 마이그레이션 파일이 존재하지만, 적용 여부 추적 불가
- **목표**: 마이그레이션을 자동으로 추적·실행하고, 실패 시 롤백 가능한 시스템 구축
- **기대효과**: DB 스키마 버전 관리 자동화, 배포 시간 단축, 오류 감소

### 1.2 문제 정의
```
현재 상황:
  ❌ 마이그레이션 실행 기록 없음
  ❌ 적용된 마이그레이션 파악 불가
  ❌ 롤백 불가능
  ❌ 배포 자동화 불가
  ❌ 마이그레이션 충돌/순서 오류 위험

목표 상태:
  ✅ 모든 마이그레이션 자동 추적
  ✅ 적용 여부 DB에 기록
  ✅ 실패한 마이그레이션 자동 롤백
  ✅ 주기적 마이그레이션 스케줄
  ✅ API로 상태 조회 가능
```

---

## 2. 요구사항

### 2.1 기능 요구사항 (Functional)

#### FR-01: 마이그레이션 추적 (Core)
- **설명**: 모든 마이그레이션 실행 기록을 `migration_history` 테이블에 저장
- **대상**: 000~019 모든 파일 (19개)
- **필드**: version, filename, applied_at, status, execution_time, error_message
- **우선순위**: CRITICAL

#### FR-02: 자동 실행 스크립트 (Core)
- **파일**: `scripts/apply_migrations.py`
- **기능**:
  - 미적용 마이그레이션 감지
  - 순차적 실행 (000 → 019)
  - 실행 시간 측정
  - 오류 기록
- **사용법**: `uv run python scripts/apply_migrations.py`
- **옵션**: `--status`, `--dry-run`, `--rollback`
- **우선순위**: CRITICAL

#### FR-03: 마이그레이션 상태 조회 API (High)
- **엔드포인트**: `/api/migrations/status`, `/api/migrations/history`, `/api/migrations/summary`
- **기능**: 웹 대시보드에서 마이그레이션 상태 확인
- **접근**: admin 역할만 가능
- **우선순위**: HIGH

#### FR-04: 자동 마이그레이션 (High)
- **시점**: 애플리케이션 시작 시 (main.py lifespan)
- **동작**: 미적용 마이그레이션 자동 실행
- **재시도**: 3회 시도 후 경고만 (실패해도 앱 시작)
- **우선순위**: HIGH

#### FR-05: 롤백 기능 (Medium)
- **기능**: 특정 마이그레이션 롤백 (향후 구현)
- **대상**: 019_unified_state_system_rollback.sql 참고
- **우선순위**: MEDIUM (v2)

#### FR-06: 마이그레이션 검증 (Medium)
- **기능**: SQL 구문 검증, 이미 적용된 마이그레이션 스킵
- **실패 처리**: 오류 기록 후 계속 진행 (All-or-Nothing 아님)
- **우선순위**: MEDIUM

### 2.2 비기능 요구사항 (Non-Functional)

#### NFR-01: 성능
- **목표**: 19개 전체 마이그레이션 < 60초
- **병목**: Supabase 네트워크 (SSL, 풀러 오버헤드 고려)
- **최적화**: 트랜잭션 단위 최소화, 배치 처리

#### NFR-02: 안정성
- **목표**: 99% 성공률
- **재시도**: 중요 마이그레이션 자동 재시도 (3회)
- **롤백**: 실패한 마이그레이션만 롤백 (다른 것은 유지)

#### NFR-03: 추적성
- **기록**: 모든 실행 기록 DB에 영구 보관
- **로그**: 애플리케이션 로그에도 기록 (JSON 포맷)
- **감사**: 누가, 언제, 어떤 마이그레이션을 실행했는지 추적 가능

#### NFR-04: 확장성
- **구조**: 새로운 마이그레이션 추가 시 자동 감지
- **파일명**: 명확한 버전 번호 규칙 (001_*, 002_*, ...)
- **호환성**: Supabase, PostgreSQL 호환

---

## 3. 구현 범위

### 3.1 포함되는 항목 (In Scope)

| # | 항목 | 상태 | 설명 |
|----|------|------|------|
| 1 | `000_init_migrations.sql` | ✅ 완료 | 마이그레이션 추적 테이블 생성 |
| 2 | `scripts/apply_migrations.py` | ✅ 완료 | 자동 실행 스크립트 |
| 3 | 004~019 마이그레이션 | ⏳ 대기 | 모두 순차 실행 |
| 4 | `app/main.py` lifespan | ⏳ 대기 | 시작 시 자동 실행 hook |
| 5 | API 엔드포인트 | ⏳ 대기 | 상태 조회 API |
| 6 | 에러 처리 | ⏳ 대기 | SSL, 네트워크 오류 처리 |

### 3.2 제외되는 항목 (Out of Scope - v2)

| # | 항목 | 이유 |
|----|------|------|
| 1 | 롤백 자동화 | 향후 구현 (rollback.sql 스크립트 필요) |
| 2 | 마이그레이션 병렬화 | Supabase 제약 (순차 실행 필수) |
| 3 | 관리자 UI | 향후 추가 (대시보드 구현) |
| 4 | 다중 환경 | 현재 Supabase 프로덕션만 |

---

## 4. 기술 아키텍처

### 4.1 시스템 구성

```
┌─────────────────────────────────────────────┐
│ PDCA Phase: Plan ✅ Design ⏳ Do ⏳         │
└─────────────────────────────────────────────┘

애플리케이션 시작 (app/main.py lifespan)
            ↓
    ┌───────────────────┐
    │ apply_migrations  │ (scripts/apply_migrations.py)
    │ --status 조회     │
    └─────────┬─────────┘
              ↓
    ┌───────────────────────────────────────┐
    │ 미적용 마이그레이션 감지              │
    │ (000_init_migrations 먼저)             │
    └─────────┬─────────────────────────────┘
              ↓
    ┌───────────────────────────────────────┐
    │ 순차 실행: 001, 002, ..., 019        │
    │ ├─ SQL 구문 분석                      │
    │ ├─ 주석 제거                          │
    │ └─ 트랜잭션 단위 실행                 │
    └─────────┬─────────────────────────────┘
              ↓
    ┌───────────────────────────────────────┐
    │ migration_history에 기록              │
    │ (version, status, execution_time)    │
    └─────────┬─────────────────────────────┘
              ↓
    ┌───────────────────────────────────────┐
    │ 오류 발생 시: error_message 기록      │
    │ (나머지 마이그레이션은 계속 실행)     │
    └─────────┬─────────────────────────────┘
              ↓
    ┌───────────────────────────────────────┐
    │ 완료 보고 (로그 출력)                │
    │ 총 19개 중 성공/실패 통계             │
    └───────────────────────────────────────┘
```

### 4.2 파일 구조

```
database/
├── migrations/
│   ├── 000_init_migrations.sql          ✅ 신규
│   ├── 001~019_*.sql                    ⏳ 기존 (순차 실행)
│   └── 019_unified_state_system_rollback.sql (롤백용)
├── schema_v3.4.sql                      (초기 스키마)
└── README.md

scripts/
├── apply_migrations.py                  ✅ 신규 (자동 실행)
├── migrate_intranet.py                  (기존)
└── ...

app/
├── main.py                              ⏳ 수정 (lifespan)
├── api/
│   └── routes_migrations.py              ⏳ 확장 (상태 조회 API)
└── ...
```

### 4.3 마이그레이션 파일 분석

```
현재 19개 마이그레이션:
├── Core Schema (004~006)         [~5 files]
│   └── 테이블, 컬럼, 인덱스 생성
├── Feature Enhancements (007~015) [~9 files]
│   └── 가격, 품질, 저장소, 알림 등
├── Integration (016~019)         [~4 files]
│   └── 스케줄러, 인트라넷, 상태 시스템
└── Status: 추적 불가 → 추적 가능 (예상 완료율 90%)
```

---

## 5. 마이그레이션 파일 목록 (004~019)

| # | 파일명 | 설명 | 크기 | 적용됨? |
|----|--------|------|------|--------|
| 4 | 004_performance_views.sql | 성과 추적 뷰 | 4.0K | ❓ |
| 5 | 005_*.sql (4개) | 입찰, 토큰, QA | ~7K | ❓ |
| 6 | 006_*.sql (2개) | G2B 로그, 컬럼 | ~2K | ❓ |
| 7 | 007_*.sql (3개) | 저장소, 가격, 테이블 | ~12K | ❓ |
| 8 | 008_user_password_flag.sql | 암호 플래그 | 147B | ❓ |
| 9 | 009_proposal_files.sql | 파일 관리 | 873B | ❓ |
| 10 | 010_prompt_evolution.sql | 프롬프트 진화 | 5.8K | ❓ |
| 11 | 011_three_streams.sql | 3-스트림 병행 | 4.4K | ❓ |
| 12 | 012_*.sql (6개) | 낙찰정보, 알림 설정, KB 등 | ~14K | ❓ |
| 13 | 013_*.sql (2개) | 프롬프트 분석, 컬럼 | ~2K | ❓ |
| 14 | 014_bid_decision_flow.sql | 입찰 의사결정 | 741B | ❓ |
| 15 | 015_*.sql (3개) | 산출물 버전, 클라이언트 오류, 노드 헬스 | ~9K | ❓ |
| 16 | 016_*.sql (2개) | Go/No-Go, 스케줄러 | ~10K | ❓ |
| 17 | 017_intranet_documents.sql | 인트라넷 문서 | 8.0K | ❓ |
| 18 | 018_intranet_sync_log.sql | 인트라넷 동기화 로그 | 1.8K | ❓ |
| 19 | 019_unified_state_system.sql | 통합 상태 시스템 | 8.1K | ❓ |

**합계**: ~104K SQL, 19개 마이그레이션, 적용 상태 미추적

---

## 6. 구현 계획 (Timeline)

### Phase: Design (다음 단계)
- [ ] 마이그레이션 실행 순서 정의 및 의존성 분석
- [ ] 에러 처리 전략 수립 (SSL, 네트워크, 권한)
- [ ] API 설계 (엔드포인트, 스키마)
- [ ] 테스트 계획 수립

### Phase: Do (구현)
- [ ] 000_init_migrations.sql 재검토 및 최적화
- [ ] apply_migrations.py 완성 (SSL 오류 해결)
- [ ] main.py lifespan 통합
- [ ] API 엔드포인트 구현
- [ ] 통합 테스트 (Supabase 실제 환경)

### Phase: Check (검증)
- [ ] 19개 마이그레이션 모두 적용 확인
- [ ] migration_history 테이블 검증
- [ ] API 기능 테스트
- [ ] 롤백 테스트

### Phase: Act (최적화)
- [ ] 성능 최적화 (< 60초 목표)
- [ ] 문서화
- [ ] 롤백 기능 추가 (v2)

---

## 7. 위험 요소 및 완화 전략

| # | 위험 | 영향 | 확률 | 완화 전략 |
|----|------|------|------|----------|
| 1 | SSL 인증서 오류 | 마이그레이션 실패 | 중 | `ssl=False` + 풀러 사용 |
| 2 | Supabase 네트워크 타임아웃 | 실행 중단 | 중 | 재시도 로직 + 타임아웃 증가 |
| 3 | 마이그레이션 중복 실행 | 오류 발생 | 낮음 | `ON CONFLICT DO NOTHING` 사용 |
| 4 | 마이그레이션 순서 오류 | 스키마 불일치 | 낮음 | 버전 순서 자동 정렬 |
| 5 | 적용되지 않은 롤백 파일 | 데이터 손실 | 매우낮음 | 사전 백업 필수 |

---

## 8. 성공 기준 (Definition of Done)

### 8.1 Functional
- [ ] 000_init_migrations.sql 성공적으로 실행
- [ ] 모든 19개 마이그레이션 순차 실행
- [ ] migration_history 테이블에 모든 실행 기록 저장
- [ ] 적용된 마이그레이션 자동 스킵 (중복 실행 방지)
- [ ] 오류 발생 시 error_message 기록

### 8.2 API
- [ ] GET /api/migrations/status → 200 OK + 마이그레이션 목록
- [ ] GET /api/migrations/history → 200 OK + 실행 기록 (페이지 처리)
- [ ] GET /api/migrations/summary → 200 OK + 통계 (성공/실패 비율)
- [ ] 비인증 사용자 접근 → 401 Unauthorized

### 8.3 자동화
- [ ] 애플리케이션 시작 시 미적용 마이그레이션 자동 실행
- [ ] 성공/실패 여부 로그 출력
- [ ] 마이그레이션 실패해도 앱 시작 가능 (경고만)

### 8.4 성능
- [ ] 19개 마이그레이션 전체 실행 시간 < 60초
- [ ] 각 마이그레이션 실행 시간 측정 및 기록

### 8.5 문서화
- [ ] apply_migrations.py 사용 방법 (--status, --dry-run, --rollback)
- [ ] API 엔드포인트 문서
- [ ] 마이그레이션 추가 방법 가이드

---

## 9. 참고 자료

### 기존 마이그레이션 파일
- `database/migrations/000~019_*.sql` (19개)
- `database/schema_v3.4.sql` (초기 스키마)
- `database/README.md` (구식 가이드)

### 기존 구현
- `scripts/migrate_intranet.py` (참고용)
- `app/api/routes_migrations.py` (배치 마이그레이션용, 다른 목적)
- `app/services/migration_service.py` (참고용)

### 외부 라이브러리
- `asyncpg` (PostgreSQL 비동기 드라이버)
- `supabase` (Supabase 클라이언트)
- `python-dotenv` (환경 변수 로드)

---

## 10. 부록: 마이그레이션 파일 예시

### 000_init_migrations.sql (신규)
```sql
CREATE TABLE migration_history (
    id BIGSERIAL PRIMARY KEY,
    version VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(500) NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INT,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT
);
```

### 004_performance_views.sql (기존 예시)
```sql
CREATE MATERIALIZED VIEW mv_team_performance AS
SELECT team_id, COUNT(*) as proposal_count, ...
FROM proposals
GROUP BY team_id;
```

---

**다음 단계**: `/pdca design db-migration-automation` → 설계 문서 작성
