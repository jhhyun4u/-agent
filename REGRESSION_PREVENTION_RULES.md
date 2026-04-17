# 회귀 방지 규칙 (Regression Prevention Rules)

## 목적
이전 세션에서 발견된 에러가 다시 발생하지 않도록 자동 감지 및 경고

---

## 1. API 파라미터 불일치 [CRITICAL]

**ID**: api_parameter_mismatch  
**Category**: api_compatibility  
**Description**: StateMachine.start_workflow() 파라미터 불일치  
**Pattern**: `unexpected keyword argument.*initial_phase`  
**고정 커밋**: 3616ba5 (2026-04-17)

### 규칙
- ❌ WRONG: `await sm.start_workflow(user_id=owner_id, initial_phase="rfp_analyze")`
- ✅ RIGHT: `await sm.start_workflow(user_id=owner_id, phase="rfp_analyze")`

### 검증 위치
- [app/api/routes_proposal.py:372](app/api/routes_proposal.py#L372)
- [app/api/routes_workflow.py](app/api/routes_workflow.py) (이미 수정됨)

---

## 2. 마이그레이션 테이블 누락 [CRITICAL]

**ID**: migration_table_missing  
**Category**: database  
**Description**: _schema_migrations 테이블 누락 - 마이그레이션 초기화 필요  
**Pattern**: `relation.*_schema_migrations.*does not exist`

### 규칙
1. 새 마이그레이션 적용 전, 000_init_migrations.sql 실행 확인
2. Supabase SQL 에디터에서 테이블 존재 확인:
   ```sql
   SELECT * FROM public._schema_migrations LIMIT 1;
   ```

### 적용 순서
```
1. 000_init_migrations.sql    (테이블 생성)
2. 001~037_*.sql             (데이터 변경)
```

---

## 3. E2E 테스트 Fixture 부족 [MAJOR]

**ID**: fixture_timeout  
**Category**: testing  
**Description**: E2E 테스트 fixture에서 실제 공고 데이터 부족  
**Pattern**: `SKIPPED.*fixture|real_bid_no fixture failed`

### 원인
- conftest.py의 real_bid_no fixture가 /api/bids/monitor 조회하는데 데이터 없음
- 스테이징 환경에서 7일 이내 신규 공고 부족

### 해결책
1. **개발 환경에서**: .env.test에 E2E_BID_NO 사전 설정
   ```bash
   E2E_BID_NO=R26BK01454044  # 테스트 용 실제 공고번호
   ```

2. **자동 테스트 데이터 생성**: tests/seed_test_data.py 개발 예정

---

## 4. 테스트 데이터 예산 미달 [MAJOR]

**ID**: budget_threshold_mismatch  
**Category**: business_logic  
**Description**: 테스트 데이터 예산이 최소 기준(30M) 미만  
**Pattern**: `budget=\d+.*assert.*30000000`

### 기준값
- 최소 예산: 30,000,000원 (KRW)
- 테스트 예산: >= 30,000,000

### 검증
```python
# tests/integration/test_bid_to_proposal_workflow.py:306
assert budget >= 30_000_000, f"예산 미달: {real_bid_no}, budget={budget:,}"
```

---

## 5. 상태 전환 실패 [CRITICAL]

**ID**: state_machine_transition  
**Category**: workflow  
**Description**: StateMachine 상태 전환 실패 - phase 파라미터 검증  
**Pattern**: `상태 전환 실패.*start_workflow`

### 검증 체크리스트
- [ ] StateMachine.start_workflow() 호출 시 `phase` 파라미터 사용
- [ ] `initial_phase` 파라미터 금지 (v3.0+ 삭제됨)
- [ ] 상태 전환 에러 발생 시 로그 레벨: ERROR

---

## 모니터링 & 알림

### CI/CD 체크 (GitHub Actions)
```yaml
- name: Check API Parameter Compatibility
  run: grep -r "initial_phase" app/ && exit 1 || echo "OK"

- name: Verify DB Migrations
  run: python scripts/apply_migrations.py --status
```

### 개발 중 자동 감지
1. `pre-commit` 훅: initial_phase 패턴 감지
2. 타입 체커: 파라미터 타입 검증
3. 테스트 실행: 에러 패턴 정규식 매칭

---

## 기록

| 날짜 | 에러 | 해결책 | 상태 |
|------|------|--------|------|
| 2026-04-17 | initial_phase 파라미터 에러 | phase로 변경 (commit 3616ba5) | ✅ FIXED |
| 2026-04-17 | _schema_migrations 테이블 누락 | 000_init_migrations.sql 먼저 실행 | ✅ FIXED |
| 2026-04-17 | E2E fixture 데이터 부족 | .env.test E2E_BID_NO 설정 | ⚠️ PENDING |
| 2026-04-17 | 테스트 예산 미달 | 최소 30M 공고 데이터 필요 | ⚠️ PENDING |

---

## 다음 조치 (Priority Order)

### 1. Immediate (이번 주)
- [ ] GitHub Actions에 회귀 테스트 규칙 추가
- [ ] pre-commit 훅 설정 (initial_phase 감지)
- [ ] .env.test.example에 E2E_BID_NO 가이드 추가

### 2. Short-term (다음 주)
- [ ] tests/seed_test_data.py 개발 (자동 테스트 데이터 생성)
- [ ] conftest.py fixture 개선 (폴백 데이터)
- [ ] API 변경 감지 CI/CD 체크

### 3. Long-term (다음 달)
- [ ] bkit regression_rules 자동 통합
- [ ] 테스트 환경 격리 (스테이징 vs 로컬)
- [ ] 매주 회귀 리포트 생성

