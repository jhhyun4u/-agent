# Go/No-Go Enhancement — PDCA Completion Report

> **Feature**: go-no-go-enhancement (Go/No-Go 스크리닝 고도화)
> **PDCA Cycle**: Plan → Design → Do → Check → Report
> **Date**: 2026-03-26 (단일 세션 완료)
> **Match Rate**: 95% (raw) / 98% (severity-adjusted)

---

## 1. Executive Summary

Go/No-Go 판정 노드를 **단일 AI 프롬프트 의존** 구조에서 **3축 정량 분석 + AI 전략가산 = 100점 합산** 구조로 전면 개편. 70점 게이트로 수주 가능성 낮은 공고를 사전 필터링하여 조직 리소스를 최적화.

### 핵심 성과

| 지표 | Before | After |
|------|--------|-------|
| 점수 산출 방식 | AI 단일 프롬프트 (불투명) | 3축 정량 DB + AI 가산 (투명) |
| 자격 검증 | 텍스트 비교 (수동) | capabilities 자동 대조 (자동) |
| 유사실적 매칭 | 시맨틱 top-3 (정성) | DB 정량 매칭 + AI 파싱 (정량) |
| 경쟁 강도 | 경쟁사 10건 나열 | 낙찰이력 + 대전기록 기반 (정량) |
| 리소스 최적화 | 없음 | 70점 게이트 + score_tag |
| Fatal 판정 | AI 판단 | 자격 미충족 / 실적 0건 자동 |

---

## 2. PDCA Phase Summary

### Plan (계획)
- **문서**: `docs/01-plan/features/go-no-go-enhancement.plan.md`
- FR 8건 정의 (유사실적·자격·경쟁·합산·게이트·fatal·프론트·구조변경)
- 4축 점수 배분: 유사실적(30) + 자격(30) + 경쟁(20) + 전략가산(20) = 100
- 리스크 5건 식별 + 완화 방안

### Design (설계)
- **문서**: `docs/02-design/features/go-no-go-enhancement.design.md`
- 7개 섹션: State 모델, 정량 함수 3개, 노드 개편, 프론트, DB migration, 에러/Fallback
- 함수 시그니처, DB 쿼리, 점수 산정 로직, UI 와이어프레임 상세 기술
- 수정 대상 파일 7개 식별

### Do (구현)
- **수정/생성 파일 7개**, 총 변경량 ~550줄 (신규 코드)

| # | 파일 | 유형 | 핵심 내용 |
|---|------|------|-----------|
| 1 | `app/graph/state.py` | 수정 | GoNoGoResult +4 필드 (score_tag, 3 detail dicts) |
| 2 | `app/graph/context_helpers.py` | 수정 | `score_similar_performance` (AI 파싱+DB 매칭 30점), `score_qualification` (AI 분류+capabilities 대조 30점), `score_competition` (낙찰이력+대전기록 20점), `_match_qualification` 헬퍼 |
| 3 | `app/graph/nodes/go_no_go.py` | 전면개편 | 3축 정량 → `_ai_strategic_assessment`(20점) → 합산 → 게이트 |
| 4 | `frontend/components/GoNoGoPanel.tsx` | 전면개편 | 4축 바 차트, 70점 컷라인, CollapsibleSection 3개, fatal 배너, score_tag 배지 |
| 5 | `frontend/components/ArtifactReviewPanel.tsx` | 수정 | GoNoGoContent 4축 바 차트 + score_tag |
| 6 | `database/migrations/016_go_no_go_enhancement.sql` | 신규 | proposals.domain, go_no_go_score, go_no_go_tag |
| 7 | `scripts/seed_data.py` | 수정 | certification/license/registration 시드 11건 |

### Check (검증)
- **문서**: `docs/03-analysis/go-no-go-enhancement.analysis.md`
- gap-detector 에이전트 실행, 147항목 비교
- **Match Rate: 95% (raw) / 98% (severity-adjusted)**
- MEDIUM 갭 1건 (시드 2건 누락) → 즉시 수정 완료
- LOW 갭 7건 (의도적 차이) → 수정 불필요
- 핵심 로직 (점수 산정, 게이트, fatal) = 100% 일치

---

## 3. Architecture Changes

### 3.1 Go/No-Go 판정 흐름 (Before → After)

**Before**:
```
[research_gather] → [go_no_go: AI 단일 프롬프트 → 0~100점] → [review_gng]
```

**After**:
```
[research_gather] → [go_no_go: 3축 DB 정량 + AI 전략가산 → 합산 → 게이트] → [review_gng]
                     ├── score_similar_performance (30점) — DB 매칭
                     ├── score_qualification (30점) — capabilities 대조
                     ├── score_competition (20점) — 낙찰이력 분석
                     └── _ai_strategic_assessment (20점) — AI 정성 평가
```

### 3.2 게이트 로직

```
Fatal (자격 미충족 / 실적 0건) → 점수 무관 No-Go (disqualified)
합산 ≥ 85 → Go 추천 (priority: 적극 참여)
합산 ≥ 70 → Go 추천 (standard: 일반 참여)
합산 < 70 → No-Go 추천 (below_threshold: 리소스 절약)
```

### 3.3 프론트엔드 변경

- 합산 점수 바 + 70점 컷라인 마커
- 4축 수평 바 차트 (축별 score/max, 색상 코딩)
- 3개 접기/펼치기 상세 패널 (유사실적·자격·경쟁)
- Fatal 빨간 배너 (자격 미달 시)
- score_tag 배지 (적극참여/일반참여/기준미달/자격미달)

---

## 4. Quality Metrics

| Metric | Result |
|--------|--------|
| ruff check | All passed |
| TypeScript build | 0 errors |
| mypy (신규 파일) | 0 new errors |
| Gap Match Rate | 98% (adjusted) |
| Fallback 커버리지 | 6/6 시나리오 (100%) |
| 하위 호환 | GoNoGoResult 기존 필드 전체 유지 |

---

## 5. Remaining Items & Future Work

### 잔여 사항 (없음)
- MEDIUM 갭 시드 누락 → Check 단계에서 즉시 수정 완료
- LOW 갭 7건 → 의도적 차이로 수정 불필요

### 향후 개선 가능

| 항목 | 설명 | 우선순위 |
|------|------|----------|
| 컷오프 값 설정화 | 70점 기준을 config에서 조정 가능하게 | Low |
| rfp_search fit_score 연계 | Go/No-Go 합산과 공고 검색 적합도 점수 통합 | Low |
| 자격 만료일 추적 | capabilities에 expiry_date 추가, 마감 전 유효성 체크 | Medium |
| 경쟁사 자동 수집 | G2B 낙찰결과에서 경쟁사 DB 자동 갱신 | Low |

---

## 6. PDCA Documents

| Phase | Document | Status |
|-------|----------|--------|
| Plan | `docs/01-plan/features/go-no-go-enhancement.plan.md` | Complete |
| Design | `docs/02-design/features/go-no-go-enhancement.design.md` | Complete |
| Analysis | `docs/03-analysis/go-no-go-enhancement.analysis.md` | Complete (98%) |
| Report | `docs/04-report/features/go-no-go-enhancement.report.md` | Complete |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-03-26 | PDCA 전체 사이클 완료 보고서 | AI |
