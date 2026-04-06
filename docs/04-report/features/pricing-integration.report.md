# PDCA Report: pricing-integration (Option A — 통합)

> 독립 가격 시뮬레이터 제거 + 워크플로 집중 + 빠른 견적 이관

## 1. 개요

| 항목 | 내용 |
|------|------|
| Feature | pricing-integration |
| 기간 | 2026-03-26 (단일 세션) |
| 최초 방향 | Option C (양립) → 구현 완료 |
| 최종 방향 | Option A (통합) → 방향 전환 후 재구현 |
| 빌드 | TypeScript 에러 0, 경고 0, 정적 페이지 29개 |

## 2. 의사결정 과정

1. 독립 도구 vs 워크플로 통합 검토 → 3가지 옵션 제시
2. Option C(양립) 채택 → 구현 완료 (apply 엔드포인트 + 프로젝트 연결 + 시뮬레이션 불러오기)
3. 재검토 후 **Option A(통합)로 전환** — 이용자가 맥락 없이 시뮬레이션하는 경우가 드물다고 판단

## 3. 완료 항목

### 삭제
| 파일 | 설명 |
|------|------|
| `app/(app)/pricing/page.tsx` | 독립 시뮬레이터 페이지 |
| `app/(app)/pricing/history/page.tsx` | 시뮬레이션 이력 페이지 |
| `components/pricing/PricingSimulator.tsx` | 독립 시뮬레이터 컴포넌트 |

### 수정
| 파일 | 변경 |
|------|------|
| `components/AppSidebar.tsx` | NAV에서 "가격 시뮬레이터" 항목 + isActive 분기 제거 |
| `app/(app)/proposals/new/page.tsx` | 빠른 견적 UI 추가 (~50줄) |

### 유지 (Option C에서 구현, 그대로 활용)
| 파일 | 설명 |
|------|------|
| `app/api/routes_pricing.py` | apply 엔드포인트 (향후 활용) |
| `lib/api.ts` | `pricingApi.applyToProposal` 메서드 |
| `components/pricing/BidPlanReviewPanel.tsx` | 기존 시뮬레이션 불러오기 |

### 유지 (기존 하위 컴포넌트, BidPlanReviewPanel에서 사용)
- `ScenarioCards.tsx`, `SensitivityChart.tsx`, `WinProbabilityGauge.tsx`
- `CostBreakdownCard.tsx`, `MarketContextPanel.tsx`, `PriceScoreTable.tsx`
- `CostSheetEditor.tsx`, `BidPlanReviewPanel.tsx`

## 4. 빠른 견적 UI

`/proposals/new` — 공고 모니터링에서 진입 시, 예산이 있는 공고에만 표시:

```
┌──────────────────────────────────┐
│ $ 빠른 견적          [견적 확인] │
│                                  │
│  4.5억원    85.2%     62%       │
│  추천 입찰가  추천 낙찰률  수주확률  │
│                                  │
│  규칙 기반 · 유사 사례 12건      │
└──────────────────────────────────┘
```

- `pricingApi.quickEstimate({ budget })` 호출
- 추천가, 낙찰률, 수주확률 3칸 그리드
- 신뢰도/유사사례 하단 표시

## 5. 라우트 변경

| 변경 전 (35개) | 변경 후 (33개) |
|:---:|:---:|
| `/pricing` | 삭제 |
| `/pricing/history` | 삭제 |

## 6. 교훈

- **방향 전환 비용이 낮았던 이유**: Option C 코드 중 BidPlanReviewPanel 개선 + apply 엔드포인트는 Option A에서도 유용 → 삭제 대상은 3파일(페이지 2개 + PricingSimulator 1개) + 사이드바 2줄뿐
- **YAGNI 적용**: 독립 시뮬레이터는 "언젠가 쓸 수 있을 것 같은" 기능이었지만, 실제 이용자 워크플로에서는 항상 공고/프로젝트 맥락이 선행됨
