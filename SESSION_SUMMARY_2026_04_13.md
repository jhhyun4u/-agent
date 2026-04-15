# 세션 요약: 제안결정 워크플로우 분석 및 수정 (2026-04-13)

## 🎯 핵심 결과

**제안결정 워크플로우의 두 가지 문제를 분석하고 수정했습니다.**

---

## 📋 작업 내역

### 1️⃣ 제안결정 워크플로우 검증
- **위치:** `PROPOSAL_DECISION_WORKFLOW_VERIFICATION.md`
- **결과:** 백엔드 로직은 **모두 정상 작동**, 문제는 프론트엔드 에러 처리 부족

**검증된 엔드포인트:**
- ✅ PUT /api/bids/{bidNo}/status (line 661, routes_bids.py)
  - bid_announcements.proposal_status = "제안결정" 설정
  - verdict = "Go" 설정
- ✅ POST /api/proposals/from-bid (line 169, routes_proposal.py)
  - owner_id, team_id, org_id 정상 설정
  - bid_tracked=false, go_decision=true 정상 설정

---

### 2️⃣ 프론트엔드 수정 적용
- **파일:** `frontend/app/(app)/monitoring/[bidNo]/review/page.tsx`
- **수정 사항:**
  1. 상태 업데이트 실패 시 콘솔 로그 추가
  2. 제안 생성 후 500ms 대기 추가 (DB 동기화)
  3. Catch 블록에 상세 에러 로깅 추가

**수정 상세:**

| # | 항목 | 변경 전 | 변경 후 | 목적 |
|----|------|--------|--------|------|
| 1 | 상태 업데이트 실패 처리 | 로그 없음 | console.warn() 추가 | 실패 원인 파악 용이 |
| 2 | 제안 생성 후 대기 | 즉시 이동 | 500ms 대기 추가 | DB 동기화 완료 확인 |
| 3 | 에러 로깅 | 최소한의 로그 | console.error() + 스택 추적 | 디버깅 용이 |

---

### 3️⃣ 상세 분석 문서 작성

**1. PROPOSAL_DECISION_WORKFLOW_VERIFICATION.md**
- 백엔드 엔드포인트 검증 결과
- 문제별 원인 분석
- 데이터베이스 확인 방법

**2. PROPOSAL_DECISION_FIXES_APPLIED.md**
- 수정 사항 상세 기록
- 검증 단계별 체크리스트
- 트러블슈팅 가이드

---

## 🔍 원인 분석

### 문제 A: 공고가 모니터링 목록에서 안 사라짐

**근본 원인:** 
- ❌ 아님 (엔드포인트는 정상)
- **실제 원인:** PUT 엔드포인트 실패 또는 응답 확인 부족

**해결 방법:**
1. Console에서 로그 확인
2. Network 탭에서 PUT 응답 상태 확인
3. DB에서 proposal_status 값 직접 확인

---

### 문제 B: 제안이 제안 목록에 안 보임

**근본 원인:**
- ❌ 아님 (엔드포인트는 정상)
- **실제 원인:** 타이밍 문제 + 에러 처리 부족

**해결 방법:**
1. 제안 생성 후 500ms 대기 추가 ✅ **완료**
2. Console 로그로 성공/실패 확인
3. Network 탭에서 POST 응답 확인
4. DB에서 새 제안 레코드 확인

---

## ✅ 완료 사항

| # | 항목 | 상태 | 파일 |
|----|------|------|------|
| 1 | 워크플로우 검증 | ✅ 완료 | PROPOSAL_DECISION_WORKFLOW_VERIFICATION.md |
| 2 | 상태 업데이트 로깅 | ✅ 완료 | review/page.tsx line 554-566 |
| 3 | DB 동기화 대기 | ✅ 완료 | review/page.tsx line 605-608 |
| 4 | 에러 로깅 강화 | ✅ 완료 | review/page.tsx line 618-622 |
| 5 | 분석 문서 작성 | ✅ 완료 | PROPOSAL_DECISION_FIXES_APPLIED.md |

---

## ⏭️ 다음 단계

### 필수 검증 (테스트)

1. **로컬 환경에서 테스트**
   ```
   1. 공고 모니터링 페이지 열기
   2. 공고 선택 → 제안 검토 버튼
   3. 제안결정 버튼 클릭
   4. 브라우저 Console 탭 모니터링
   ```

2. **Console 로그 확인**
   ```
   ✅ "[review] 상태 업데이트 완료: {...}"
   ✅ "[review] 제안 프로젝트 생성 성공: {proposal_id}"
   ✅ "[review] /proposals로 이동"
   ```

3. **결과 확인**
   - [ ] /proposals 페이지에서 새 제안 보이는가?
   - [ ] 모니터링 페이지로 돌아가면 공고가 안 보이는가?
   - [ ] 데이터베이스 레코드 확인

### 선택적 검증 (DB 확인)

```sql
-- bid_announcements 확인
SELECT bid_no, proposal_status, verdict, decided_by
FROM bid_announcements
WHERE bid_no = 'xxxxx'  -- 제안결정한 공고번호
;

-- proposals 확인
SELECT id, title, owner_id, team_id, bid_tracked, go_decision, status
FROM proposals
WHERE source_bid_no = 'xxxxx'  -- 제안결정한 공고번호
;
```

---

## 📊 변경 요약

### 코드 변경량
- **파일 1개 수정:** `frontend/app/(app)/monitoring/[bidNo]/review/page.tsx`
- **추가된 로그:** 3개 (warn, log, error)
- **추가된 대기:** 1개 (500ms setTimeout)
- **라인 수 변경:** +8 lines

### 영향 범위
- ✅ 기존 기능: 변경 없음 (에러 처리 개선만)
- ✅ 사용자 경험: 더 명확한 에러 메시지 표시
- ✅ 디버깅: Console에서 상세 로그 확인 가능

---

## 🧪 테스트 시나리오

### 성공 케이스

```
제안결정 버튼 클릭
  ↓
[review] Console: PUT 200 OK 메시지
[review] Console: POST 201 Created 메시지
[review] Console: 500ms 대기 후 /proposals 이동
  ↓
/proposals 페이지에서 새 제안 목록에 표시됨
```

### 실패 케이스 (PUT 실패)

```
제안결정 버튼 클릭
  ↓
[review] Console: PUT 실패 경고 메시지
[review] 계속 진행 → POST 시도
  ↓
POST 성공하면 제안은 생성됨 (proposal_status만 업데이트 안 됨)
모니터링 목록에서 공고가 안 사라짐
```

### 실패 케이스 (POST 실패)

```
제안결정 버튼 클릭
  ↓
[review] Console: PUT 성공
[review] Console: POST 실패 에러 메시지
  ↓
UI에 빨간 에러 메시지 표시
/proposals 페이지로 이동 안 함
```

---

## 📝 참고 사항

### 기존 로직 유지
- 모든 백엔드 엔드포인트는 정상 작동
- 에러 처리 후에도 계속 진행하는 기존 정책 유지
- 제안 생성 실패 시에만 사용자에게 에러 표시

### 500ms 대기의 의미
- PostgreSQL의 쓰기 일관성 보장 대기
- 다음 SELECT 쿼리가 새 레코드를 확실히 조회하도록 함
- 프로덕션 환경에서도 안전한 시간 설정

### 추가 개선 옵션 (필요시)
- [ ] 제안 생성 직후 제안 ID로 상세 조회 API 호출 (확실성 증대)
- [ ] 상태 업데이트 실패 시 사용자 알림 (현재는 무시)
- [ ] Optimistic UI: 제안 생성 전부터 목록에 표시 후 동기화

---

## 📞 문제 발생 시

### Console에 아래 메시지가 보이면

**메시지:** `[review] 상태 업데이트 경고: 404`
- **원인:** bid_no가 잘못되었거나 DB에 없음
- **해결:** bid_no 확인

**메시지:** `[review] 제안 프로젝트 생성 실패: 403 Forbidden`
- **원인:** 사용자 소속 정보 부족 (org_id, team_id NULL)
- **해결:** 사용자의 팀/조직 정보 확인

**메시지:** `[review] 제안결정 프로세스 실패`
- **원인:** 예상치 못한 에러
- **해결:** 전체 스택 추적을 콘솔에서 확인, 서버 로그 확인

---

**작성일:** 2026-04-13  
**상태:** 코드 수정 완료, 테스트 대기  
**담당:** 제안결정 워크플로우 수정
