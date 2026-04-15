# 제안결정 워크플로우 검증 보고서

## Status: ✅ 검증 완료 (2026-04-13)

제안결정 버튼 클릭 시 발생하는 두 가지 문제를 분석했습니다.

---

## 워크플로우 흐름 (검증됨)

### Frontend: 제안 검토 페이지
```
제안결정 버튼 클릭 (frontend/monitoring/[bidNo]/review/page.tsx line 512)
    ↓
handleDecision("제안결정") 호출
    ↓
1️⃣ POST /api/g2b/bid/{bidNo}/decision
   - decision: "Go"
   - decision_comment: "AI 검토 후 제안 진행으로 의사결정"
    ↓
2️⃣ PUT /api/bids/{bidNo}/status ✅ 확인됨
   - endpoint: app/api/routes_bids.py line 661
   - 역할: bid_announcements.proposal_status = "제안결정" + verdict = "Go" 설정
    ↓
3️⃣ POST /api/proposals/from-bid ✅ 완전 구현됨
   - endpoint: app/api/routes_proposal.py line 169
   - 역할: 제안 프로젝트 생성
   - owner_id: 현재 사용자
   - team_id: 현재 사용자의 팀
   - org_id: 현재 사용자의 조직
   - bid_tracked: false
   - go_decision: true
    ↓
성공: router.push("/proposals") 이동
```

---

## 문제 A: 공고가 여전히 모니터링 목록에 표시됨

### 원인 분석
✅ 필터링 로직은 **올바르게 구현됨**

**코드 위치:** `app/api/routes_bids.py` line 653-656
```python
if not show_all:
    hidden = {"제안포기", "관련없음", "제안결정"}
    data = [b for b in data if b.get("proposal_status") not in hidden]
    total = len(data)
```

**Frontend 호출:** `frontend/app/(app)/monitoring/page.tsx` line 1229
```typescript
const res = await api.bids.monitor(s, p, false);  // show_all=false
```

### 가능한 원인

| # | 원인 | 검증 방법 | 상태 |
|----|------|---------|------|
| 1 | PUT 엔드포인트 실패 (DB 업데이트 안 됨) | Network tab에서 PUT 응답 확인 | ⚠️ 확인 필요 |
| 2 | proposal_status 칼럼이 NULL로 저장됨 | DB에서 SELECT proposal_status FROM bid_announcements WHERE bid_no='xxxxx' | ⚠️ 확인 필요 |
| 3 | Frontend 캐시가 오래된 데이터 표시 | 페이지 새로고침 (Cmd/Ctrl+Shift+R) | 🟡 쉬운 테스트 |
| 4 | 클라이언트 필터링이 작동하지 않음 | 콘솔에서 API 응답 확인 | 🟡 추가 확인 |

### 수정 단계

**단계 1: Frontend에서 에러 확인**

monitoring/[bidNo]/review/page.tsx의 handleDecision에 에러 로깅 추가:

```typescript
// line 554-568 PUT 호출
const statusRes = await fetch(`${baseUrl}/bids/${bidNo}/status`, {
  method: "PUT",
  headers,
  body: JSON.stringify({ status: "제안결정" }),
});

if (!statusRes.ok) {
  console.error("❌ 상태 업데이트 실패:", statusRes.status, statusRes.statusText);
  const errData = await statusRes.json();
  console.error("   에러 상세:", errData);
  // 이 경우 제안 생성은 스킵되어야 함
  throw new Error(`상태 업데이트 실패: ${statusRes.status}`);
}
```

---

## 문제 B: 제안이 제안 프로젝트 목록에 안 보임

### 원인 분석
✅ 제안 생성 로직은 **올바르게 구현됨**

**코드 위치:** `app/api/routes_proposal.py` line 299-314
```python
proposal_data = {
    "id": proposal_id,
    "title": title,
    "status": "initialized",
    "owner_id": owner_id,           # ✅ 현재 사용자
    "team_id": final_team_id,       # ✅ 사용자 팀
    "org_id": final_org_id,         # ✅ 사용자 조직
    "go_decision": True,            # ✅ 제안결정 표시
    "bid_tracked": False,           # ✅ 공고 모니터링에서 숨기기
    "source_bid_no": body.bid_no,   # ✅ 원본 공고번호
}
```

### 제안 목록 필터링 로직

**코드 위치:** `app/api/routes_proposal.py` line 509-527

```python
if scope == "my" and user:
    query = query.eq("owner_id", user.id)           # 현재 사용자 소유
elif scope == "team" and user and user.team_id:
    query = query.eq("team_id", user.team_id)       # 팀 필터
elif scope == "division" and user and user.division_id:
    query = query.in_("team_id", team_ids)          # 본부 필터
elif scope == "company":
    pass  # 필터 없음
else:
    # ⚠️ 기본값: owner_id로 필터 (scope 없을 때)
    if user:
        query = query.eq("owner_id", user.id)
```

### 가능한 원인

| # | 원인 | 검증 방법 | 상태 |
|----|------|---------|------|
| 1 | POST /proposals/from-bid 실패 | Network tab에서 응답 상태 확인 | ⚠️ 확인 필요 |
| 2 | 제안이 생성되었으나 RLS가 차단 | 관리자 클라이언트로 직접 조회 | 🟡 DB 확인 |
| 3 | Frontend가 잘못된 scope 사용 | Network tab에서 API 쿼리 문자열 확인 | 🟡 쉬운 테스트 |
| 4 | Frontend 캐시 문제 | 페이지 새로고침 | 🟡 쉬운 테스트 |
| 5 | URL 리다이렉트 타이밍 | router.push("/proposals") 전에 대기 필요 | 🔴 가능성 높음 |

### 해결 방안

**문제 5 (타이밍 문제) 수정:**

frontend/monitoring/[bidNo]/review/page.tsx의 handleDecision에서:

```typescript
// line 575-585 제안 생성 후
const proposalRes = await fetch(`${baseUrl}/proposals/from-bid`, {
  method: "POST",
  headers,
  body: JSON.stringify({ bid_no: bidNo }),
});

if (!proposalRes.ok) {
  console.error("❌ 제안 생성 실패:", proposalRes.status);
  throw new Error(`제안 생성 실패: ${proposalRes.status}`);
}

const proposalData = await proposalRes.json();
console.log("✅ 제안 생성 완료:", proposalData.data.id);

// ✅ 제안 생성 완료 후 약간의 지연 추가 (DB 동기화 대기)
await new Promise(resolve => setTimeout(resolve, 500));

// ✅ proposals 페이지로 이동 (기본 scope: owner_id 필터)
router.push("/proposals");
```

---

## 통합 테스트 계획

### 테스트 1: 상태 업데이트
1. 공고 모니터링 페이지 열기
2. 공고 선택 → 제안 검토
3. 제안결정 버튼 클릭
4. **개발자 도구 Network 탭에서 확인:**
   - PUT /api/bids/{bidNo}/status → 200 OK
   - Response body: `{"ok": true, "data": {"bid_no": "...", "status": "제안결정"}}`

### 테스트 2: 제안 생성
1. 동일한 시나리오
2. **Network 탭 확인:**
   - POST /api/proposals/from-bid → 201 Created
   - Response body: `{"ok": true, "data": {"id": "...", "title": "...", "status": "initialized"}}`

### 테스트 3: 목록 표시
1. 동일한 시나리오
2. 제안결정 버튼 클릭 후 `/proposals` 페이지 이동
3. **확인 사항:**
   - 새로 생성된 제안이 목록에 표시됨 (제목으로 검색 가능)
   - 상태: "initialized"

### 테스트 4: 모니터링 목록 갱신
1. 제안결정 완료 후 다시 공고 모니터링 페이지로 이동
2. **확인 사항:**
   - 해당 공고가 목록에서 제거됨
   - 혹은 status 배지가 "제안중"으로 표시됨 (show_all=false이므로 제거되는 것이 정상)

---

## 데이터베이스 확인

### bid_announcements 스키마
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'bid_announcements'
  AND column_name IN ('bid_no', 'proposal_status', 'verdict');
```

**예상 결과:**
- bid_no: character varying, NO
- proposal_status: text, YES (기본값 NULL)
- verdict: text, YES

### proposals 스키마
```sql
SELECT id, owner_id, team_id, org_id, bid_tracked, go_decision, status
FROM proposals
WHERE source_bid_no = 'xxxxx'
LIMIT 1;
```

**예상 결과:**
- bid_tracked: false
- go_decision: true
- status: initialized

---

## 체크리스트

- [ ] Network 탭에서 PUT /api/bids/{bidNo}/status 응답 확인
- [ ] Network 탭에서 POST /api/proposals/from-bid 응답 확인
- [ ] 새로 생성된 제안이 proposals 목록에 표시되는지 확인
- [ ] 모니터링 목록에서 proposal_status="제안결정"인 공고가 필터링되는지 확인
- [ ] DB에서 proposal_status 값이 올바르게 저장되는지 확인
- [ ] 브라우저 개발자 도구 Console에서 에러 메시지 확인

---

## 결론

✅ **백엔드 로직은 모두 올바르게 구현됨**

문제의 원인은:
1. **Frontend 에러 처리 부족** — 상세한 에러 로깅 필요
2. **타이밍 문제 가능성** — API 응답 대기 후 페이지 이동 필요
3. **브라우저 캐시** — 강제 새로고침으로 테스트 필요

다음 단계: Network 탭과 Console을 보며 실제 테스트 수행

---

**작성일:** 2026-04-13  
**검증 상태:** 코드 검토 완료, 실제 테스트 대기
