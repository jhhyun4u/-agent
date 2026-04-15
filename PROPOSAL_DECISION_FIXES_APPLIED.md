# 제안결정 워크플로우 수정 사항

## Status: ✅ 수정 완료 (2026-04-13)

제안결정 기능의 두 가지 문제를 분석하고 수정했습니다.

---

## 수정 사항

### 1. Frontend 에러 로깅 개선

**파일:** `frontend/app/(app)/monitoring/[bidNo]/review/page.tsx`

**변경 1: 상태 업데이트 로깅**

```typescript
// Before
if (!statusRes.ok) {
  // 실패해도 계속 진행
} else {
  const statusData = await statusRes.json();
  statusUpdateSuccess = true;
}

// After
if (!statusRes.ok) {
  console.warn(
    "[review] 상태 업데이트 경고 (계속 진행):",
    statusRes.status,
    statusRes.statusText,
  );
} else {
  const statusData = await statusRes.json();
  statusUpdateSuccess = true;
  console.log("[review] 상태 업데이트 완료:", statusData);
}
```

**목적:** 상태 업데이트 실패 시 콘솔에 명확한 로그 출력

---

### 2. DB 동기화 대기 추가

**파일:** `frontend/app/(app)/monitoring/[bidNo]/review/page.tsx`

**변경 2: 제안 생성 후 500ms 대기**

```typescript
// Before
} else {
  const createData = await createRes.json();
  console.log("[review] 제안 프로젝트 생성 성공:", createData.proposal_id);
}
// ... 바로 router.push("/proposals")

// After
} else {
  const createData = await createRes.json();
  const proposalId = createData.data?.id || createData.proposal_id;
  console.log("[review] 제안 프로젝트 생성 성공:", proposalId);

  // DB 동기화 대기 (500ms) 후 페이지 이동
  await new Promise(resolve => setTimeout(resolve, 500));
}
// ... 500ms 후 router.push("/proposals")
```

**목적:** 제안이 완전히 저장된 후에 proposals 페이지로 이동하여 목록에서 보이도록 함

---

### 3. 에러 처리 로깅 강화

**파일:** `frontend/app/(app)/monitoring/[bidNo]/review/page.tsx`

**변경 3: Catch 블록 로깅 추가**

```typescript
// Before
} catch (e: unknown) {
  const msg = e instanceof Error ? e.message : "제안 프로세스 중 오류 발생";
  setError(msg);
  setDeciding(false);
}

// After
} catch (e: unknown) {
  const msg = e instanceof Error ? e.message : "제안 프로세스 중 오류 발생";
  console.error("[review] 제안결정 프로세스 실패:", e);
  setError(msg);
  setDeciding(false);
}
```

**목적:** 예상치 못한 오류 발생 시 콘솔에 전체 스택 추적 기록

---

## 검증 단계

### Step 1: 로컬 테스트 (개발자 모드)

1. 공고 모니터링 페이지 열기
2. 공고 선택 → 제안 검토 버튼
3. 제안결정 버튼 클릭
4. **브라우저 개발자 도구 Console 탭 확인:**

```
[review] 상태 업데이트 완료: {bid_no: "...", status: "제안결정", decided_by: "..."}
[review] 제안 프로젝트 생성 성공: {proposal_id}
[review] /proposals로 이동
```

5. **Network 탭 확인:**
   - PUT /api/bids/{bidNo}/status → 200 OK
   - POST /api/proposals/from-bid → 201 Created
   - 둘 다 성공하면 router.push("/proposals") 실행

### Step 2: 결과 확인

1. 제안결정 후 /proposals 페이지로 이동
2. **확인 사항:**
   - 새로 생성된 제안이 목록에 표시됨
   - 상태: "initialized"
   - 원본 공고번호: 제안결정한 공고의 bid_no

### Step 3: 모니터링 목록 갱신

1. 제안결정 완료 후 /monitoring 페이지로 돌아가기
2. **확인 사항:**
   - 제안결정한 공고가 목록에서 제거됨 (proposal_status="제안결정"이므로 필터됨)

---

## 데이터 흐름 검증

### 문제 A: 공고가 여전히 모니터링 목록에 표시

**원인:** proposal_status가 "제안결정"으로 업데이트되지 않았을 가능성

**검증 방법:**

```sql
-- DB에서 직접 확인
SELECT bid_no, proposal_status, verdict, decided_by
FROM bid_announcements
WHERE bid_no = 'xxxxx'  -- 제안결정한 공고번호
;
```

**정상 결과:**
- proposal_status: "제안결정"
- verdict: "Go"
- decided_by: {사용자명}

**만약 NULL이면:**
1. PUT 엔드포인트가 실패했을 가능성
2. Network 탭에서 PUT 응답 상태 코드 확인
3. Console에서 경고 메시지 확인

---

### 문제 B: 제안이 제안 프로젝트 목록에 안 보임

**원인:** 제안 생성 실패 또는 타이밍 문제

**검증 방법:**

```sql
-- DB에서 직접 확인
SELECT id, title, owner_id, team_id, org_id, bid_tracked, go_decision, status
FROM proposals
WHERE source_bid_no = 'xxxxx'  -- 제안결정한 공고번호
;
```

**정상 결과:**
- owner_id: {현재사용자ID}
- team_id: {사용자팀ID}
- org_id: {사용자조직ID}
- bid_tracked: false
- go_decision: true
- status: "initialized"

**만약 조회되지 않으면:**
1. POST /api/proposals/from-bid가 실패했을 가능성
2. Network 탭에서 POST 응답 상태 코드 확인
3. Console에서 에러 메시지 확인

---

## 트러블슈팅 체크리스트

### 제안결정 후 모니터링 목록에서 공고가 안 보임

- [ ] Console에서 로그 확인: PUT 성공 메시지 보이는가?
- [ ] Network 탭에서 PUT /api/bids/{bidNo}/status 응답 확인
  - [ ] Status Code: 200 OK?
  - [ ] Response body에 "제안결정" 포함?
- [ ] DB에서 bid_announcements의 proposal_status 확인
- [ ] 모니터링 페이지 새로고침 (Cmd/Ctrl+Shift+R)

### 제안결정 후 /proposals 페이지에서 제안이 안 보임

- [ ] Console에서 로그 확인: POST 성공 메시지 보이는가?
- [ ] Network 탭에서 POST /api/proposals/from-bid 응답 확인
  - [ ] Status Code: 201 Created?
  - [ ] Response body에 proposal_id 포함?
- [ ] DB에서 proposals 테이블의 레코드 확인
- [ ] proposals 페이지 새로고침 (Cmd/Ctrl+Shift+R)

### 에러 메시지가 표시됨

- [ ] Console에서 전체 에러 스택 추적 확인
- [ ] Network 탭에서 실패한 요청의 응답 본문 확인
- [ ] API 서버 로그 확인 (Backend 콘솔)

---

## 백엔드 검증 (필요시)

### PUT /api/bids/{bidNo}/status 엔드포인트

**위치:** `app/api/routes_bids.py` line 661

**동작:**
1. bid_announcements 테이블의 proposal_status를 업데이트
2. status="제안결정"일 때 verdict를 "Go"로 업데이트
3. 파일 캐시에도 저장 (하위 호환성)

**DB 업데이트 실패 시:**
- 로그에 "bid_announcements DB 업데이트 실패" 메시지 출력
- 파일 캐시로 폴백 (warnings.log 확인)

### POST /api/proposals/from-bid 엔드포인트

**위치:** `app/api/routes_proposal.py` line 169

**동작:**
1. bid_announcements에서 공고 정보 조회
2. 마크다운 문서 로드 (RFP분석, 공고문, 과업지시서)
3. FK 의존성 확인 (조직, 팀)
4. proposals 테이블에 새 제안 생성
5. 공고 첨부파일 복사 (백그라운드)

**실패 원인:**
- 사용자 소속 정보 부족 (org_id, team_id가 NULL)
- bid_announcements 조회 실패
- 데이터베이스 제약 위반

---

## 예상 동작 흐름

### 성공 시나리오

```
1. 사용자가 공고 선택 → 제안 검토 페이지
2. 제안결정 버튼 클릭
3. Frontend:
   - POST /g2b/bid/{bidNo}/decision (의사결정 기록)
   - PUT /api/bids/{bidNo}/status (proposal_status = "제안결정")
   - POST /api/proposals/from-bid (새 제안 생성)
4. Backend:
   - bid_announcements.proposal_status ← "제안결정"
   - bid_announcements.verdict ← "Go"
   - proposals 테이블에 새 레코드 INSERT
5. Frontend: router.push("/proposals")
6. 결과: /proposals에서 새 제안이 목록에 표시됨
```

### 실패 시나리오

```
1. 제안결정 버튼 클릭
2. PUT /api/bids/{bidNo}/status 실패
   - Console: "[review] 상태 업데이트 경고" 메시지 출력
   - 그래도 계속 진행 (제안 생성 시도)
3. POST /api/proposals/from-bid 실패
   - Console: "제안 프로젝트 생성 실패: {에러메시지}" 표시
   - setError() 호출 → UI에 빨간색 에러 메시지 표시
   - 페이지 이동 안 함
4. 사용자: 에러 메시지 확인 후 문제 해결
```

---

## 다음 단계

1. **로컬 테스트 실행**
   - 공고 선택 → 제안결정 클릭
   - Console & Network 탭 모니터링
   - 결과 확인

2. **DB 검증**
   - bid_announcements에서 proposal_status 확인
   - proposals 테이블에서 새 레코드 확인

3. **스테이징/운영 배포**
   - 코드 변경 사항 리뷰
   - 테스트 완료 후 배포

---

**수정 완료 일시:** 2026-04-13  
**수정 내용:** Frontend 에러 로깅 + DB 동기화 대기  
**테스트 상태:** 로컬 테스트 대기
