# 배포 준비 긴급 액션 플랜
**작성**: 2026-04-17  
**상태**: 테스트 완료 후 배포 준비 Phase

---

## 📊 현재 상태
- **전체 준비도**: 75%
- **백엔드 테스트**: 10/21 통과 (47.6%)
- **프론트엔드 테스트**: 1/12 통과 (8.3%)
- **코드 품질**: 792/2,665 자동 수정 (기능 이슈 아님)

---

## 🚨 Immediate Actions (NOW - 1시간)

### Phase 1: 서버 캐시 초기화 & 재시작
```bash
# Step 1: Python 캐시 삭제
cd /c/project/tenopa\ proposer
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type d -name .pytest_cache -exec rm -rf {} +

# Step 2: pip 캐시 초기화 (선택)
# pip cache purge

# Step 3: 개발 서버 재시작
uv run uvicorn app.main:app --reload --env-file .env
```

**예상 효과**: initial_phase 버그 해결 → 테스트 성공률 47.6% → 70% (예상)

---

### Phase 2: 테스트 데이터 재생성 (15분)
```bash
# Step 1: 테스트 데이터 생성
python tests/seed_test_data.py create

# Step 2: 확인
python tests/seed_test_data.py check

# 출력 예상:
# ✅ E26BK00000001 | 50M | 30일 | Standard
# ✅ E26BK00000002 | 80M | 45일 | High budget
# ✅ E26BK00000003 | 20M | 7일  | Low budget
# ✅ E26BK00000004 | 30M | -1일 | Expired
```

**예상 효과**: test_full_e2e_workflow 통과

---

### Phase 3: 백엔드 회귀 테스트 (5분)
```bash
# 모니터링 테스트만 먼저 실행
python -m pytest tests/integration/live/test_g2b_monitoring.py::test_monitor_diagnostics -xvs

# 모든 모니터링 테스트
python -m pytest tests/integration/live/test_g2b_monitoring.py -v --tb=short

# 전체 통합 테스트
python -m pytest tests/integration/live/ tests/integration/test_bid_to_proposal_workflow.py -v
```

**예상 결과**: 70%+ 통과 (15개+)

---

## 🔧 High Priority Fixes (1-4시간)

### Fix #1: 권한 검증 로직 (1시간)
**파일**: `app/api/deps.py`  
**문제**: test_unauthorized_team_access에서 500 반환 (403 예상)

```python
# 현재 (문제)
@app.get("/api/bids/{bid_no}")
async def get_bid(bid_no: str, current_user = Depends(get_current_user)):
    # 권한 체크 없음 → 500 에러

# 수정 (필요)
@app.get("/api/bids/{bid_no}")
async def get_bid(bid_no: str, current_user = Depends(get_current_user)):
    # 팀 확인 후 403 반환
    bid = await db.get_bid(bid_no)
    if not await user_can_access_team(current_user, bid.team_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    return bid
```

**테스트**:
```bash
pytest tests/integration/live/test_g2b_monitoring.py::test_unauthorized_team_access -xvs
```

**예상**: PASSED

---

### Fix #2: 예산 필터링 로직 (1시간)
**파일**: `app/services/bidding/monitor/scorer.py` 또는 filter 로직  
**문제**: test_bid_with_budget_below_threshold에서 27.2M < 30M 공고 포함

```python
# 현재 (문제)
if bid.budget_amount > 0:  # 너무 너그러운 조건
    include_bid = True

# 수정 (필요)
MIN_BUDGET = 30_000_000  # 30M
if bid.budget_amount < MIN_BUDGET:
    status = "excluded"  # 목록에서 제외
    return None
```

**테스트**:
```bash
pytest tests/integration/test_bid_to_proposal_workflow.py::test_bid_with_budget_below_threshold -xvs
```

**예상**: PASSED

---

### Fix #3: AI 분석 상태 로직 (1시간)
**파일**: `app/api/routes_bids.py` (GET /api/bids/{bid_no}/analysis)  
**문제**: test_nonexistent_bid_no_creates_pending에서 'analyzed' 반환 (pending 예상)

```python
# 현재 (문제)
status = "analyzed"  # 바로 analyzed로 설정

# 수정 (필요)
if bid_no not in existing_bids:
    status = "pending"  # 먼저 pending으로 시작
    # 큐에 추가 → 나중에 analyzing → analyzed 전환
```

**테스트**:
```bash
pytest tests/integration/live/test_g2b_monitoring.py::test_nonexistent_bid_no_creates_pending -xvs
```

**예상**: PASSED

---

## 📱 프론트엔드 E2E 설정 (2-3시간)

### E2E 환경 설정
```bash
cd frontend

# Step 1: 환경변수 확인
cat .env.local  # E2E_USER_EMAIL, E2E_USER_PASSWORD 있는지 확인

# Step 2: auth.setup 실행
npx playwright test e2e/auth.setup.ts

# Step 3: storageState 확인
ls -la e2e/.auth/user.json
# 파일이 있어야 함 (크기 > 0)

# Step 4: E2E 테스트 실행
E2E_USER_EMAIL="e2e-test@tenopa.co.kr" \
E2E_USER_PASSWORD="e2e-test-password-2026!" \
npx playwright test e2e/bid-monitoring-flow.spec.ts --reporter=html
```

**예상**: 성공률 개선 (1/12 → 6-8/12)

---

## ✅ 배포 체크리스트

### Pre-Deployment Check (4-6시간)
- [ ] 캐시 초기화 완료
- [ ] 테스트 데이터 재생성 완료
- [ ] 백엔드 테스트 70%+ 통과
- [ ] 권한 검증 고정 완료
- [ ] 예산 필터 고정 완료
- [ ] AI 상태 로직 고정 완료
- [ ] 프론트엔드 E2E 환경 설정 완료
- [ ] E2E 테스트 실행 및 결과 정리

### Smoke Test (30분)
```bash
# 핵심 워크플로우 테스트
1. 공고 모니터링 페이지 진입 → ✅ 렌더링 확인
2. 공고 AI 분석 → ✅ 분석 결과 표시
3. Go 결정 → ✅ 제안 생성
4. No-Go 결정 → ✅ 포기 기록

# API 헬스 체크
curl http://localhost:8000/api/health
# {"status": "ok"}

# DB 연결 확인
curl http://localhost:8000/api/bids/monitor
# {"success": true, "data": [...]}
```

### UAT Preparation
- [ ] 테스트 계정 준비 (e2e-test@tenopa.co.kr)
- [ ] 테스트 공고 데이터 확인
- [ ] 고객 리뷰 일정 예약
- [ ] 배포 후 지원 계획 수립

---

## 📋 시간 계획

| Phase | 소요시간 | 완료 예상 |
|-------|---------|----------|
| **Phase 1**: 캐시 초기화 | 15분 | 13:00 |
| **Phase 2**: 테스트 데이터 | 15분 | 13:15 |
| **Phase 3**: 회귀 테스트 | 5분 | 13:20 |
| **Phase 4**: 권한 검증 고정 | 1시간 | 14:20 |
| **Phase 5**: 예산 필터 고정 | 1시간 | 15:20 |
| **Phase 6**: AI 상태 고정 | 1시간 | 16:20 |
| **Phase 7**: E2E 설정 | 1.5시간 | 17:50 |
| **Phase 8**: Smoke 테스트 | 30분 | 18:20 |
| **총 소요**: | **5.5시간** | **18:20** |

---

## 🎯 성공 기준

### 배포 전 요구사항 (All or Nothing)
- [ ] 백엔드 테스트 **80%+ 통과** (16/20 이상)
- [ ] 프론트엔드 E2E **최소 50% 통과** (6/12 이상) 또는 수동 테스트 완료
- [ ] Smoke 테스트 **100% 통과** (4/4)
- [ ] 코드 품질 **자동 수정 완료** (792/792)
- [ ] 보안 검사 **통과** (SQL injection, XSS, CSRF 검증)

### 배포 후 모니터링
- [ ] 로그 모니터링 (Sentry, CloudWatch)
- [ ] 성능 메트릭 (응답 시간 < 500ms)
- [ ] 에러율 (< 1%)
- [ ] 사용자 피드백 수집

---

## 🔗 관련 문서

- [TEST_EXECUTION_REPORT_2026-04-17.md](TEST_EXECUTION_REPORT_2026-04-17.md) — 상세 테스트 분석
- [PHASE1_PERFORMANCE_BASELINE.md](PHASE1_PERFORMANCE_BASELINE.md) — 성능 기준
- [database/schema_v3.4.sql](database/schema_v3.4.sql) — DB 스키마

---

## 📞 담당자 연락

**테스트 팀**: hyunjaeho@tenopa.co.kr  
**개발 리드**: (프로젝트 리더)  
**배포 담당**: (DevOps)

---

## 다음 회의

**시간**: 2026-04-17 17:00 KST  
**안건**: 
1. Phase 1-6 완료 상태 확인
2. E2E 테스트 결과 검토
3. 배포 승인 여부 결정
4. 배포 일정 확정

---

*Action Plan Generated: 2026-04-17 13:45 UTC*  
*Status: Ready for Immediate Execution*  
*Target Deployment: 2026-04-18 (AFTER fixes completed)*
