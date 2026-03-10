# 대시보드 개선 설계서 (v1)

## 1. 개요

**목적**: 사용자가 로그인 직후 "지금 뭘 해야 하나"를 즉시 파악할 수 있도록 대시보드를 액션 중심으로 재편한다.

**핵심 원칙**:
- 결과 보고 → 행동 유도로 전환
- 기존 데이터(제안서 + 캘린더)를 재조합해 새 API 없이 구현
- 기존 KPI/캘린더 섹션은 유지

---

## 2. 추가 섹션 명세

### 2-1. 오늘 할 일 (액션 허브)

**위치**: 페이지 최상단 (KPI 카드 위)

**표시 조건**: actionItems.length > 0일 때만 렌더

**데이터 소스**:
| 아이템 유형 | 조건 | CTA |
|------------|------|-----|
| 캘린더 (긴급) | D-day ≤ 14, status = "open" | "지금 시작" → /proposals/new |
| 제안서 (진행 중) | status = "processing" | "확인" → /proposals/{id} |
| 제안서 (미시작) | status = "initialized" | "시작" → /proposals/{id} |

**정렬**: D-day 임박 순, 최대 5개

**시각적 구분**:
- 긴급(D-3 이하): 빨간 D-day 텍스트 (캘린더 섹션 동일 기준)
- 일반 긴급(D-4 ~ D-14): 노란 D-day 텍스트
- 진행 중 제안서: 파란 "생성중" 배지 (text-blue-400)
- 미시작 제안서: 회색 "대기" 배지 (text-[#8c8c8c])

**헤더**: 녹색 점 pulse 애니메이션 + "지금 해야 할 것" 텍스트

---

### 2-2. 제안 파이프라인 뷰

**위치**: 액션 허브 아래, KPI 카드 위

**표시 조건**: 항상 렌더

**파이프라인 단계**:
```
공고 등록 → 작성 중 → 완료 → 결과 대기 → 수주 → 낙찰 실패
```

**카운트 계산 로직**:
| 단계 | 데이터 소스 | 조건 |
|------|------------|------|
| 공고 등록 | calItems | status="open" AND proposal_id=null |
| 작성 중 | proposals | status="initialized" OR status="processing" |
| 완료 | proposals | status="completed" AND win_result=null |
| 결과 대기 | proposals | win_result="pending" |
| 수주 | proposals | win_result="won" |
| 낙찰 실패 | proposals | win_result="lost" |

**색상**:
- 공고 등록: #8c8c8c (회색)
- 작성 중: blue-400 (파랑)
- 완료: #ededed (흰색)
- 결과 대기: yellow-400 (노랑)
- 수주: #3ecf8e (초록)
- 낙찰 실패: red-400 (빨강)

**인터랙션**: 각 단계 클릭 시 해당 페이지로 이동 (router.push)

**단계 구분자**: → 화살표 텍스트

---

## 3. 신규 상태 및 함수

| 이름 | 타입 | 설명 |
|------|------|------|
| `proposals` | `ProposalSummary[]` | 제안서 목록 |
| `loadProposals()` | `useCallback` | api.proposals.list() 호출 |
| `pipeline` | `object` | 6단계 카운트 계산 결과 |
| `actionItems` | `ActionItem[]` | 캘린더 + 제안서 통합 액션 목록 |
| `ActionItem` | union type | calendar | proposal 두 가지 유형 |

---

## 4. API 연동

**신규 호출**:
- `api.proposals.list({ page: 1 })` — 제안서 목록 (기존 API 재사용)

**기존 호출 유지**:
- `api.stats.winRate(scope)`
- `api.calendar.list({ scope })`

**useEffect 추가**: `loadProposals` — scope 변경 시 함께 재호출

---

## 5. 비기능 요구사항

- 제안서 로드 실패 시 빈 배열로 fallback (에러 무시)
- actionItems가 0개면 액션 허브 섹션 숨김
- 파이프라인 카운트가 0이어도 섹션 항상 표시 (신규 사용자 가이드 역할)
