# Design: pricing-integration

> Plan: `docs/01-plan/features/pricing-integration.plan.md`

## 1. 백엔드 API

### 1-1. POST /pricing/simulations/{simulation_id}/apply/{proposal_id}

시뮬레이션 결과를 프로젝트 bid_plan 상태에 적용.

```python
# routes_pricing.py 추가
@router.post("/simulations/{simulation_id}/apply/{proposal_id}")
async def apply_simulation_to_proposal(
    simulation_id: str,
    proposal_id: str,
    user=Depends(get_current_user),
):
    # 1. pricing_simulations에서 result 조회
    # 2. graph.aupdate_state()로 bid_plan + bid_budget_constraint 업데이트
    # 3. pricing_simulations.proposal_id 업데이트
    # return { applied: true, proposal_id, simulation_id }
```

### 1-2. GET /proposals/{proposal_id}/context (기존 활용)

RFP 분석 데이터에서 예산/도메인/조달방식을 반환. 기존 `routes_workflow.py`의 `get_state`에서 추출 가능하므로 신규 API 불필요. 프론트에서 `workflow.getState(proposalId)`로 직접 조회.

## 2. 프론트엔드

### 2-1. PricingSimulator.tsx 변경

```
기존: [시뮬레이션 실행] 버튼만
추가:
- 상단: "프로젝트 연결" 드롭다운 (proposal_id 선택)
  → 선택 시 RFP 데이터로 입력값 자동 채움
- 결과 영역: "프로젝트에 적용" 버튼 (proposal_id 연결 시만 표시)
  → POST /pricing/simulations/{id}/apply/{proposal_id}
  → 성공 시 "적용됨" 배지 + 프로젝트 링크
```

### 2-2. BidPlanReviewPanel.tsx 변경

```
기존: AI가 생성한 bid_plan만 표시
추가:
- 헤더: "기존 시뮬레이션 불러오기" 버튼
  → 모달: pricingApi.getPricingSimulations(proposalId) 목록
  → 선택 시 해당 결과로 bid_plan 데이터 교체
```

### 2-3. api.ts 추가 메서드

```typescript
pricingApi.applyToProposal(simulationId: string, proposalId: string)
  → POST /pricing/simulations/{simulationId}/apply/{proposalId}
```

## 3. 구현 순서

1. 백엔드: `routes_pricing.py`에 apply 엔드포인트 추가
2. 프론트: `api.ts`에 메서드 추가
3. 프론트: `PricingSimulator.tsx` — 프로젝트 연결 + 적용 버튼
4. 프론트: `BidPlanReviewPanel.tsx` — 기존 시뮬레이션 불러오기
5. 빌드 검증
