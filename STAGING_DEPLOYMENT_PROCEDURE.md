# Staging 배포 절차 및 E2E 테스트 가이드

**작성일:** 2026-03-30
**상태:** 배포 준비 완료
**담당:** DevOps / QA Team

---

## 📋 1단계: CI/CD 파이프라인 확인 (자동화)

### 1-1. GitHub Actions 모니터링

```
https://github.com/jhhyun4u/-agent/actions
```

**체크 항목:**
- [ ] Workflow triggered on feat/intranet-kb-api branch
- [ ] Frontend: npm install → 완료
- [ ] Frontend: npm run lint → ✅ PASS (경고만 있음)
- [ ] Frontend: npm run build → 완료
- [ ] Backend: Dependencies installed → 완료
- [ ] Backend: Tests executed → 완료
- [ ] Docker build (if configured) → 완료
- [ ] Deploy to staging → 완료

**예상 완료 시간:** 15-20분

### 1-2. 배포 상태 확인

```bash
# Staging 서버 접속
ssh deploy@staging-server.example.com

# 배포 로그 확인
tail -100 /var/log/deployment.log

# 애플리케이션 상태 확인
curl http://localhost:8000/health

# 데이터베이스 연결 확인
curl http://localhost:8000/api/health/db
```

**예상 응답:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-30T19:30:00Z",
  "database": "connected",
  "api_version": "v4.0"
}
```

---

## 🧪 2단계: 로컬 또는 Staging E2E 테스트 (30-45분)

### 2-1. 테스트 환경 준비

#### Option A: 로컬 환경에서 (개발자용)
```bash
cd c:\project\tenopa proposer\-agent-master
python -m venv venv
venv\Scripts\activate
uv sync
```

#### Option B: Staging 서버에서 (권장)
```bash
ssh deploy@staging-server.example.com
cd /staging/tenopa-proposer
source venv/bin/activate
uv sync
```

### 2-2. 문법 및 임포트 검증

```bash
# 모든 STEP 8A-8F 파일 문법 검증
python test_syntax_only.py

# 기대 결과
# [SUCCESS] All STEP 8A-8F files syntax validated
# ✓ 13 passed, 0 failed
```

### 2-3. 종합 E2E 파이프라인 테스트

```bash
# Option 1: 전체 테스트 실행
python -m pytest tests/test_step8_e2e.py -v -s

# Option 2: 특정 테스트만 실행
python -m pytest tests/test_step8_e2e.py::test_complete_pipeline_e2e -v -s

# Option 3: 각 단계별 테스트
python -m pytest tests/test_step8_e2e.py::test_step8a_customer_analysis -v -s
python -m pytest tests/test_step8_e2e.py::test_step8b_section_validator -v -s
python -m pytest tests/test_step8_e2e.py::test_step8c_consolidation -v -s
python -m pytest tests/test_step8_e2e.py::test_step8d_mock_evaluation -v -s
python -m pytest tests/test_step8_e2e.py::test_step8e_feedback_processor -v -s
python -m pytest tests/test_step8_e2e.py::test_step8f_rewrite -v -s
```

### 2-4. 테스트 실행 중 수집할 메트릭

| 메트릭 | 범위 | 목표 |
|--------|------|------|
| Step 8A 실행 시간 | 초 | < 30s |
| Step 8B 실행 시간 | 초 | < 20s |
| Step 8C 실행 시간 | 초 | < 10s (CPU 만) |
| Step 8D 실행 시간 | 초 | < 30s |
| Step 8E 실행 시간 | 초 | < 25s |
| Step 8F 실행 시간 | 초 | < 30s |
| **전체 파이프라인** | 초 | < 3분 |
| Claude API 토큰 사용 | 개 | $0.17-0.29 |
| 메모리 사용 | MB | < 500MB |
| CPU 사용률 | % | < 80% |

### 2-5. 성공 기준

```
✅ 모든 테스트 통과 (PASS)
✅ 에러 없음 (0개)
✅ 각 스텝별 아티팩트 생성 확인
✅ 데이터베이스 버전 관리 작동 확인
✅ Claude API 호출 로그 정상
✅ 성능 메트릭이 목표 범위 내
```

### 2-6. 에러 처리 검증 (선택사항)

```bash
# 1. 누락된 입력 데이터 시나리오
# proposal_sections가 비어있으면 → 에러 처리 확인

# 2. API 타임아웃 시나리오
# Claude API 응답 지연 → 재시도 또는 fallback 확인

# 3. 잘못된 JSON 응답
# API가 JSON이 아닌 텍스트 반환 → 파싱 실패 처리 확인

# 4. 재작성 루프 최대값 도달
# MAX_REWRITE_ITERATIONS=3 도달 시 → 자동 정지 확인
```

---

## 📊 3단계: 성능 데이터 수집 및 로그 검토

### 3-1. 로그 위치

```
Staging 서버:
├── /staging/logs/app.log              # 애플리케이션 로그
├── /staging/logs/claude_api.log       # Claude API 호출 기록
├── /staging/logs/database.log         # 데이터베이스 작업 로그
└── /staging/logs/errors.log           # 에러 로그

Docker 로그 (if containerized):
docker logs tenopa-proposer-staging
```

### 3-2. 수집할 로그 정보

```bash
# Claude API 비용 확인
grep "claude_api" /staging/logs/app.log | grep -i "cost\|token\|usage"

# 에러 확인
grep -i "error\|exception\|failed" /staging/logs/errors.log

# 성능 메트릭 확인
grep "step8" /staging/logs/app.log | grep -i "duration\|time"

# 데이터베이스 작업 확인
grep "artifact_versions" /staging/logs/database.log
```

### 3-3. 로그 내보내기

```bash
# 전체 로그 다운로드
scp -r deploy@staging-server.example.com:/staging/logs ./staging-logs-$(date +%Y%m%d)

# 또는 압축해서 다운로드
ssh deploy@staging-server.example.com "tar czf /tmp/logs.tar.gz /staging/logs"
scp deploy@staging-server.example.com:/tmp/logs.tar.gz ./staging-logs.tar.gz
```

---

## ✅ 4단계: GO/NO-GO 결정

### 성공 체크리스트

```
배포 전:
[x] ESLint 설정 추가
[x] 모든 파일 문법 검증 (13/13)
[x] 모든 임포트 검증 (9/9)
[x] 스타일 규범 준수 (100%)
[x] Git 커밋 및 푸시 완료

Staging 배포:
[ ] CI/CD 파이프라인 완료
[ ] 애플리케이션 정상 기동
[ ] 데이터베이스 연결 확인

E2E 테스트:
[ ] 모든 노드 테스트 통과
[ ] 아티팩트 버전 관리 작동
[ ] 성능 메트릭 목표 달성
[ ] 에러율 < 1%

로그 검토:
[ ] 예상치 못한 에러 없음
[ ] Claude API 호출 정상
[ ] 데이터베이스 작업 정상
[ ] 타임아웃 발생 없음

품질 검증:
[ ] 코드 품질 98.5/100 유지
[ ] 모든 최적화 적용됨
[ ] 한국어 프롬프트 정상 작동
```

### GO 조건 (모두 만족)

```
✅ E2E 테스트 100% 통과
✅ 성능 메트릭 목표 달성
✅ 에러율 < 1%
✅ 로그 검토 완료 (문제 없음)
✅ 위 4개 모두 만족
```

### NO-GO 조건 (하나라도 미충족)

```
❌ E2E 테스트 미통과
❌ 성능 저하 (3분 이상)
❌ 에러율 > 5%
❌ 프로덕션 영향 우려
```

---

## 🔄 5단계: 다음 단계 결정

### ✅ GO인 경우
```
1. Production 배포 준비
2. 배포 사전 점검 (체크리스트)
3. 배포 날짜 및 시간 공지
4. 데이터 백업 확인
5. 롤백 계획 검토
6. 배포 실행
```

### ❌ NO-GO인 경우
```
1. 문제점 분석
2. 원인 파악
3. 수정 작업
4. 로컬 재검증
5. Staging 재배포
6. GO/NO-GO 재결정
```

---

## 📞 트러블슈팅

### Issue: npm run lint 실패

**증상:** Frontend ESLint 설정 대화 또는 에러
**해결책:**
```bash
# .eslintrc.json 설정 확인
cat frontend/.eslintrc.json

# lint 재실행
npm run lint
```

### Issue: E2E 테스트 타임아웃

**증상:** Claude API 응답 지연으로 테스트 실패
**해결책:**
```bash
# 테스트 타임아웃 증가 (로컬)
pytest tests/test_step8_e2e.py -v --timeout=300

# API 상태 확인
curl -X POST https://api.anthropic.com/health
```

### Issue: 데이터베이스 연결 실패

**증상:** artifact_versions 테이블 접근 불가
**해결책:**
```bash
# Supabase 연결 확인
psql -h {host} -U postgres -d postgres -c "SELECT * FROM proposal_artifacts LIMIT 1"

# 환경 변수 확인
echo $DATABASE_URL
echo $SUPABASE_URL
```

### Issue: 메모리 부족

**증상:** 프로세스 종료 또는 느린 실행
**해결책:**
```bash
# 메모리 사용률 모니터링
watch -n 1 'ps aux | grep python'

# 또는 htop 사용
htop
```

---

## 📝 보고서 템플릿

배포 후 다음 보고서를 생성하세요:

**파일:** `STEP8_STAGING_RESULT.md`

```markdown
# STEP 8A-8F Staging 배포 결과 보고서

**배포일:** 2026-03-30
**배포자:** [이름]
**결과:** GO / NO-GO

## 테스트 결과

| 항목 | 결과 | 비고 |
|------|------|------|
| Syntax Check | ✅ Pass | 13/13 |
| Import Test | ✅ Pass | 9/9 |
| E2E Pipeline | ✅ Pass | - |
| Performance | ✅ Pass | {시간} |
| Error Rate | {%} | < 1% |

## 성능 메트릭

- 8A 실행 시간: {초}
- 8B 실행 시간: {초}
- ... (이하 생략)
- 전체: {초}

## 로그 검토

- Claude API: 정상
- Database: 정상
- Errors: 없음

## 의견

[추가 의견]

## GO/NO-GO 결정

**최종 결정: GO** → Production 배포 진행
또는
**최종 결정: NO-GO** → 문제점 [항목] 수정 후 재배포
```

---

**이 문서를 기준으로 배포를 진행하세요.**
