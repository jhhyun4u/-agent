# 제안결정 워크플로우 분석 보고서

## 문제 정의

**사용자 보고:**
1. 공고 모니터링 > 제안 검토 페이지에서 "제안결정" 버튼 클릭
2. **문제 A:** 공고 모니터링 목록에 해당 공고가 여전히 표시됨 (제거 안 됨)
3. **문제 B:** 제안 프로젝트 목록에 등록되지 않음

---

## 워크플로우 흐름 분석

### Frontend: 제안 검토 페이지 (review/page.tsx)

**라인 512-677: handleDecision 함수**

```
제안결정 버튼 클릭
    ↓
handleDecision("제안결정") 호출
    ↓
1️⃣ POST /api/g2b/bid/{bidNo}/decision
   - decision: "Go"
   - decision_comment: "AI 검토 후 제안 진행으로 의사결정"
    ↓
2️⃣ PUT /api/bids/{bidNo}/status
   - status: "제안결정"
    ↓
3️⃣ POST /api/proposals/from-bid
   - bid_no: bidNo
    ↓
   성공: router.push("/proposals") 이동
   실패: 에러 메시지 표시
```

**주요 API 호출:**
| 단계 | API | 메서드 | 목적 |
|------|-----|--------|------|
| 1 | `/g2b/bid/{bidNo}/decision` | POST | Go 의사결정 기록 |
| 2 | `/bids/{bidNo}/status` | PUT | 공고 상태 업데이트 (제안결정) |
| 3 | `/proposals/from-bid` | POST | 제안 프로젝트 생성 |

---

## Backend: 각 엔드포인트 분석

### ✅ 엔드포인트 1: POST /api/g2b/bid/{bidNo}/decision
**위치:** routes_bids.py 또는 routes.py  
**역할:** Go/No-Go 의사결정 기록  
**상태:** 기존 구현 (검토 필요)

### ⚠️ 엔드포인트 2: PUT /api/bids/{bidNo}/status  
**위치:** routes_bids.py  
**역할:** 공고 상태 업데이트  
**스키마:**
```python
{"status": "제안결정"}  # 또는 "제안포기", "제안유보"
```
**현재 문제:** 
- 데이터베이스 테이블 구조 확인 필요
- `proposal_status` vs `status` 필드명 불일치 가능

### ✅ 엔드포인트 3: POST /api/proposals/from-bid
**위치:** routes_proposal.py (라인 169-412)  
**역할:** 제안 프로젝트 생성  
**구현 상태:** ✅ 완전 구현

**생성되는 제안 데이터:**
```python
{
    "id": proposal_id (UUID),
    "title": bid.bid_title,
    "status": "initialized",
    "owner_id": user.id,              # ✅ 현재 사용자
    "team_id": final_team_id,         # ✅ 사용자 팀
    "org_id": final_org_id,           # ✅ 사용자 조직
    "go_decision": True,              # ✅ 제안결정 표시
    "bid_tracked": False,             # ✅ 공고모니터링에서 숨기기
    "source_bid_no": body.bid_no,     # ✅ 원본 공고번호
}
```

---

## 문제 근원지 분석

### 🔴 문제 A: 공고가 여전히 공고 모니터링에 표시됨

**원인 가설:**

| # | 가설 | 확인방법 | 우선도 |
|----|------|---------|--------|
| 1 | `bid_tracked` 필터링이 적용 안 됨 | 공고모니터링 페이지 필터 코드 확인 | 🔴 높음 |
| 2 | 공고 상태 업데이트(라인 2️⃣)가 실패 | Backend 로그 확인 | 🔴 높음 |
| 3 | 테이블 칼럼명이 다름 | `proposal_status` vs `status` | 🟡 중간 |
| 4 | Frontend 목록 캐시 갱신 안 됨 | 페이지 새로고침 후 확인 | 🟡 중간 |

**라인 2️⃣ 엔드포인트 검토:**
```python
PUT /api/bids/{bidNo}/status
body: { "status": "제안결정" }
```

Backend에서 이 요청을 처리하는 엔드포인트를 찾아야 합니다.

### 🔴 문제 B: 제안 프로젝트가 목록에 안 보임

**원인 가설:**

| # | 가설 | 확인방법 | 우선도 |
|----|------|---------|--------|
| 1 | 제안 생성(라인 3️⃣)이 실패 | Backend 로그/응답 확인 | 🔴 높음 |
| 2 | team_id가 null/잘못됨 | 데이터베이스 직접 확인 | 🔴 높음 |
| 3 | Frontend scope 기본값(team) 문제 | proposal/page.tsx 라인 37 | 🟡 중간 |
| 4 | 캐시 갱신 지연 | 페이지 새로고침 후 확인 | 🟡 중간 |

**라인 3️⃣ 엔드포인트 구현:**
```python
POST /api/proposals/from-bid
응답: { "proposal_id": "...", "status": "initialized", ... }
```

✅ 완전 구현되어 있습니다.

---

## 빠진 부분: PUT /bids/{bidNo}/status 엔드포인트

**문제:** Frontend의 라인 554에서 호출하지만, 해당 엔드포인트를 찾을 수 없음

```typescript
// frontend/app/(app)/monitoring/[bidNo]/review/page.tsx (라인 554-568)
const statusRes = await fetch(`${baseUrl}/bids/${bidNo}/status`, {
  method: "PUT",
  headers,
  body: JSON.stringify({ status: "제안결정" }),
});
```

**필요한 확인:**
1. Backend에 이 엔드포인트가 존재하는가?
2. 존재한다면 어느 파일에 있는가?
3. 데이터베이스 어느 테이블을 업데이트하는가?

---

## 데이터베이스 구조 확인 필요

### bid_announcements 테이블

**현재 열:** bid_no, bid_title, budget, deadline, ...  
**추가되어야 할 열:** proposal_status, bid_tracked  

확인 사항:
```sql
-- 이 칼럼들이 존재하는가?
SELECT column_name FROM information_schema.columns 
WHERE table_name='bid_announcements' 
  AND column_name IN ('proposal_status', 'bid_tracked', 'status');
```

### proposals 테이블

**생성되는 필드:** (라인 299-333)
```
id, title, status, owner_id, team_id, org_id,
go_decision, bid_tracked, source_bid_no, fit_score, ...
```

확인 사항:
```sql
-- bid_tracked가 false로 설정되었는가?
SELECT id, title, bid_tracked, owner_id, team_id 
FROM proposals 
WHERE source_bid_no = 'xxxxx';
```

---

## 수정 계획

### Phase 1: 백엔드 엔드포인트 확인

**Task 1.1:** PUT `/bids/{bidNo}/status` 엔드포인트 찾기
- [ ] routes_bids.py 검색
- [ ] routes.py 검색  
- [ ] routes_proposal.py 검색
- [ ] 없으면 생성

**Task 1.2:** 데이터베이스 칼럼 확인
- [ ] proposal_status / status 칼럼 확인
- [ ] bid_tracked 칼럼 확인
- [ ] 없으면 마이그레이션 추가

### Phase 2: Frontend 필터링 수정

**Task 2.1:** 공고 모니터링 bid_tracked 필터
- [ ] 공고 모니터링 페이지에서 bid_tracked=false 공고 제외

**Task 2.2:** 제안 목록 조회 개선
- [ ] scope 기본값 검토
- [ ] 신규 제안 목록 표시 확인

### Phase 3: 워크플로우 통합 테스트

**Task 3.1:** 엔드-투-엔드 테스트
- [ ] 공고 선택 → 제안 검토 → 제안결정 → 확인

---

## 다음 단계

1. **PUT /bids/{bidNo}/status 엔드포인트 확인**
   - 위치: ?
   - 역할: bid_announcements 테이블 업데이트
   - 필드: status / proposal_status

2. **데이터베이스 구조 검증**
   - bid_announcements: proposal_status / bid_tracked 칼럼 확인
   - proposals: bid_tracked 필드 확인

3. **Frontend 필터링 로직 추가**
   - 공고 모니터링: bid_tracked=false 제외
   - 제안 목록: 신규 제안 표시

