# Go/No-Go 스크리닝 고도화 Planning Document

> **Summary**: 유사 수행 이력·요구 자격·경쟁 강도 3축 정량 분석 + 70점 게이트로 리소스 최적화
>
> **Project**: 용역제안 Coworker
> **Author**: AI
> **Date**: 2026-03-26
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

현행 Go/No-Go 판정은 **단일 AI 프롬프트에 정성적 판단을 일임**하여, 점수 산출 근거가 불투명하고 재현성이 낮다. 이를 **유사 수행 이력·요구 자격·경쟁 강도 3축 정량 분석**으로 전환하고, **70점 컷오프**를 적용하여 수주 가능성이 낮은 공고에 조직 리소스가 투입되는 것을 방지한다.

### 1.2 Background

**현행 문제점**:

1. **유사 수행 이력** — `find_similar_cases`가 시맨틱 검색으로 top-3만 가져옴. 실적 건수·금액·기간 등 **정량 매칭**이 없어 RFP `similar_project_requirements`("최근 5년 내 10억 이상 SI 2건") 충족 여부를 판별할 수 없음
2. **요구 자격** — `qualification_requirements`가 RFP 분석에서 파싱되지만, 자사 보유 자격(`capabilities` type=certification/license)과의 **자동 대조**가 없음
3. **경쟁 강도** — `competitors` 테이블 전체를 10건만 뿌려줌. 해당 공고의 **예상 참가업체·낙찰 이력** 기반 분석 부재
4. **70점 컷오프** — `rfp_search`의 `fit_score`와 Go/No-Go의 `feasibility_score` 간 연계 없음. 리소스 최적화 로직 부재

**기대 효과**:
- 자격 미충족 공고 → 즉시 No-Go (시간 절약)
- 유사실적 부족 공고 → 정량 근거로 의사결정 지원
- 70점 이상 공고에만 전략·계획·제안서 작성 리소스 집중 → 조직 효율 극대화

### 1.3 Related Documents

- 설계: `docs/02-design/features/proposal-agent-v1/_index.md` §7 (Go/No-Go)
- 현행 구현: `app/graph/nodes/go_no_go.py`, `app/graph/context_helpers.py`
- DB 스키마: `database/schema_v3.4.sql` §15, `database/migrations/004_performance_views.sql`
- 프론트: `frontend/components/GoNoGoPanel.tsx`

---

## 2. Scope

### 2.1 In Scope

- [x] 3축 정량 스코어링 함수 3개 신규 (`score_similar_performance`, `score_qualification`, `score_competition`)
- [x] Go/No-Go 노드 개편 — 3축 정량 + AI 전략 가산 = 100점 만점
- [x] 70점 게이트 자동 추천 로직 (≥85 적극참여 / ≥70 일반참여 / <70 No-Go)
- [x] GoNoGoResult 모델 확장 (축별 상세 + fatal_flaw 근거 강화)
- [x] GoNoGoPanel 프론트 개편 (4축 바 차트 + 70점 컷라인 + 자격 경고)
- [x] DB 마이그레이션 — capabilities 테이블에 certification/license 구분 데이터 시드

### 2.2 Out of Scope

- G2B API 신규 연동 (기존 `g2b_service.py` 활용, 새 API 엔드포인트 추가 안 함)
- rfp_search 단계의 fit_score 알고리즘 변경 (별도 개선 사항)
- 프론트엔드 전체 UI 리디자인 (GoNoGoPanel만 수정)
- 경쟁사 DB 자동 수집 파이프라인 (수동 등록 기반 유지)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | **유사실적 정량 매칭**: RFP의 `similar_project_requirements` 파싱 → DB `proposal_results` + `proposals`에서 기간·금액·유형 조건 매칭 → 충족률 산출 | High | Pending |
| FR-02 | **자격 적격성 자동 대조**: RFP `qualification_requirements` → `capabilities`(type=certification/license) + 조직 프로필 대조 → 필수/선호 분리 + met/unmet 판정 | High | Pending |
| FR-03 | **경쟁 강도 분석**: 동일 발주기관·유사 사업유형 G2B 낙찰이력 → 예상 참여업체 수 + 자사 대전 승률 산출 | High | Pending |
| FR-04 | **4축 합산 스코어링**: 유사실적(30) + 자격(30) + 경쟁(20) + 전략가산(20) = 100점 만점. `feasibility_score`에 반영 | High | Pending |
| FR-05 | **70점 게이트**: 합산 < 70 → AI 자동 No-Go 추천. ≥ 85 → "적극 참여" 태그. 사용자 오버라이드 가능 | High | Pending |
| FR-06 | **Fatal Flaw 자동 판정**: 필수 자격 미충족 또는 필수 유사실적 0건 → 점수 무관 No-Go + fatal_flaw 사유 자동 생성 | High | Pending |
| FR-07 | **GoNoGoPanel 개편**: 4축 바 차트 (축별 점수/만점), 70점 컷라인 시각화, 자격 미충족 시 빨간 경고, 유사실적 매칭 상세 펼치기 | Medium | Pending |
| FR-08 | **score_breakdown 구조 변경**: 기존 5항목(기술역량/수행실적/가격경쟁력/발주처관계/경쟁환경) → 4축(유사실적/자격/경쟁/전략가산) + 세부 breakdown | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Performance | Go/No-Go 노드 실행 시간 ≤ 15초 (3축 DB 쿼리 + AI 1회) | 로그 타임스탬프 |
| 하위 호환 | 기존 GoNoGoResult 소비자(strategy_generate, GoNoGoPanel, ArtifactReviewPanel) 정상 동작 | 수동 검증 |
| 정확도 | 자격 적격성 자동 판정 정확도 ≥ 90% (수동 검증 10건) | 시드 데이터 테스트 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] 3축 스코어링 함수 구현 + 단위 테스트
- [ ] go_no_go.py 개편 완료 (정량 3축 + AI 전략 가산)
- [ ] GoNoGoResult 모델 확장 (하위 호환 유지)
- [ ] GoNoGoPanel 프론트 4축 바 차트 + 70점 컷라인
- [ ] E2E 수동 검증: 자격 미충족 공고 → fatal No-Go, 70점 미만 → No-Go 추천, 85+ → 적극참여
- [ ] ruff check + mypy 통과

### 4.2 Quality Criteria

- [ ] context_helpers.py 신규 함수 3개 — 각 함수 독립 테스트 가능
- [ ] GoNoGoResult 기존 필드 제거 없음 (하위 호환)
- [ ] TypeScript 빌드 에러 0건

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| capabilities 테이블에 certification/license 데이터 부재 | High | High | 시드 데이터 + 문서에 수동 등록 안내 |
| similar_project_requirements 파싱 실패 (자유 텍스트) | Medium | Medium | AI 파싱 fallback — 정규식 실패 시 Claude에 구조화 요청 |
| G2B 낙찰이력 API 응답 지연 | Medium | Low | 캐시 활용 (g2b_cache 24h TTL), 실패 시 경쟁 축 기본 점수 부여 |
| score_breakdown 구조 변경으로 기존 프론트 깨짐 | Medium | Medium | 기존 5항목 키도 유지 (deprecated), 프론트에서 4축 우선 렌더링 |
| 70점 컷오프가 너무 엄격해 실제 수주 가능 공고 필터링 | High | Low | 컷오프 값 설정화 (config), 초기 60점으로 시작 후 데이터 기반 조정 |

---

## 6. Architecture Considerations

### 6.1 설계 개요

```
go_no_go.py (개선)
│
├── 1) score_similar_performance(rfp_dict, org_id)  ← context_helpers.py 신규
│     └── DB: proposal_results + proposals (정량) + find_similar_cases (시맨틱)
│
├── 2) score_qualification(rfp_dict, org_id)         ← context_helpers.py 신규
│     └── DB: capabilities (certification/license) + AI 파싱 fallback
│
├── 3) score_competition(rfp_dict, org_id)            ← context_helpers.py 신규
│     └── DB: competitor_history + g2b_cache + client_bid_history
│
├── 4) AI 전략 가산 (기존 프롬프트 축소 → 20점 스케일)
│     └── Claude: 기술적합도(8) + 발주처관계(6) + 가격경쟁력(6)
│
└── 합산 → feasibility_score + recommendation + tag
```

### 6.2 점수 체계

| 축 | 만점 | 산출 방식 | Fatal 조건 |
|----|------|-----------|------------|
| ① 유사실적 | 30 | DB 정량 매칭 + 시맨틱 보강 | 필수 유사실적 요건 0건 충족 |
| ② 자격 | 30 | RFP 요건 ↔ capabilities 자동 대조 | 필수 자격 1건이라도 미보유 |
| ③ 경쟁 | 20 | G2B 낙찰이력 + 대전 기록 | 없음 (가점/감점만) |
| ④ 전략가산 | 20 | AI 정성 평가 (축소 프롬프트) | 없음 |
| **합계** | **100** | | |

### 6.3 게이트 로직

```python
if qual.is_fatal or perf.is_fatal:
    recommendation = "no-go"       # 점수 무관 강제 No-Go
    tag = "disqualified"
elif total >= 85:
    recommendation = "go"
    tag = "priority"               # 적극 참여
elif total >= 70:
    recommendation = "go"
    tag = "standard"               # 일반 참여
else:
    recommendation = "no-go"
    tag = "below_threshold"        # 리소스 절약
```

### 6.4 State 모델 확장

```python
# GoNoGoResult 확장 (하위 호환)
class GoNoGoResult(BaseModel):
    # 기존 필드 유지
    rfp_analysis_ref: str = ""
    positioning: Literal["defensive", "offensive", "adjacent"]
    positioning_rationale: str
    feasibility_score: int                   # 4축 합산 (0~100)
    score_breakdown: dict                    # 4축 breakdown
    pros: list[str]
    risks: list[str]
    recommendation: Literal["go", "no-go"]
    fatal_flaw: Optional[str] = None
    strategic_focus: Optional[str] = None
    decision: str = "pending"

    # v4.0 신규 필드
    score_tag: str = ""                      # priority | standard | below_threshold | disqualified
    performance_detail: dict = {}            # 유사실적 상세
    qualification_detail: dict = {}          # 자격 적격성 상세
    competition_detail: dict = {}            # 경쟁 강도 상세
```

### 6.5 수정 대상 파일

| 파일 | 변경 유형 | 내용 |
|------|-----------|------|
| `app/graph/context_helpers.py` | **확장** | `score_similar_performance`, `score_qualification`, `score_competition` 3개 함수 추가 |
| `app/graph/nodes/go_no_go.py` | **개편** | 3축 정량 호출 + AI 전략 가산 축소 + 합산 로직 |
| `app/graph/state.py` | **확장** | GoNoGoResult에 v4.0 필드 추가 |
| `frontend/components/GoNoGoPanel.tsx` | **개편** | 4축 바 차트 + 70점 컷라인 + fatal 경고 |
| `frontend/components/ArtifactReviewPanel.tsx` | **수정** | GoNoGoContent에 4축 상세 렌더링 |
| `database/migrations/` | **신규** | capabilities 시드 확장 (certification/license 타입) |
| `scripts/seed_data.py` | **확장** | certification/license 시드 데이터 추가 |

---

## 7. 축별 상세 설계 방향

### 7.1 ① 유사실적 정량 매칭 (30점)

```
score_similar_performance(rfp_dict, org_id) → dict

Input:
  - rfp_dict["similar_project_requirements"]: ["최근 5년 내 10억 이상 SI 2건", ...]
  - rfp_dict["domain"]: "SI/SW개발"
  - rfp_dict["client"]: "한국정보화진흥원"
  - rfp_dict["budget"]: "15억"

Step 1 — RFP 유사실적 요건 구조화 (AI 파싱)
  - 자유 텍스트 → {period_years, min_amount, min_count, domain_keywords[]}
  - 예: "최근 5년 내 10억 이상 SI 2건" → {period_years:5, min_amount:1_000_000_000, min_count:2, domain_keywords:["SI"]}

Step 2 — DB 정량 매칭
  - proposal_results JOIN proposals WHERE:
    · result = 'won'
    · created_at >= now() - interval '{period_years} years'
    · bid_amount >= min_amount (또는 proposals.budget 파싱)
    · domain ILIKE any of domain_keywords
  - matched_count = 매칭 건수

Step 3 — 점수 산정
  - 기본점수 = (matched_count / required_count) * 25  (최대 25)
  - 동일 발주기관 수주 이력 보너스: +3
  - 동일 domain 승률 60%↑ 보너스: +2
  - 미충족 시 (matched_count == 0 AND required_count > 0) → is_fatal = True
```

### 7.2 ② 자격 적격성 (30점)

```
score_qualification(rfp_dict, org_id) → dict

Input:
  - rfp_dict["qualification_requirements"]: ["소프트웨어사업자 신고", "ISO 27001", ...]

Step 1 — 요건 분류
  - mandatory (참가자격): "~필수", "~보유 업체", "~등록 업체"
  - preferred (가점): "~시 가점", "~우대"

Step 2 — 자사 보유 자격 조회
  - capabilities WHERE org_id AND type IN ('certification', 'license')
  - title/keywords 매칭

Step 3 — 대조 결과
  - mandatory 전체 보유: 30점
  - mandatory 1건 미보유: is_fatal = True → 0점
  - preferred 보유 시: 가점 (만점 범위 내)
```

### 7.3 ③ 경쟁 강도 (20점)

```
score_competition(rfp_dict, org_id) → dict

Step 1 — 유사 공고 낙찰 이력 (기존 DB 활용)
  - client_bid_history WHERE client_name ILIKE rfp_dict["client"]
  - competitor_history WHERE org_id

Step 2 — 예상 참여업체 수 추정
  - 동일 기관 과거 공고 평균 참여 수 (proposal_results.competitor_count)

Step 3 — 점수 산정
  - 예상 참여 ≤3: 기본 18점 / 4~7: 12점 / 8+: 8점
  - 자사 직접 대전 승률 조정: ±4점
  - 해당 기관 점유율 30%↑: +2점
```

### 7.4 ④ 전략 가산 (20점) — AI

```
기존 Go/No-Go 프롬프트 축소:
  - 기술 적합도 (8점): RFP 핫버튼 ↔ 역량 매칭 정도
  - 발주처 관계 (6점): client_intel 기반 관계 수준
  - 가격 경쟁력 (6점): PricingEngine 결과 반영

AI 출력:
{
  "strategic_score": 15,
  "tech_fit": 7,
  "client_relationship": 4,
  "price_competitiveness": 4,
  "positioning": "defensive",
  "positioning_rationale": "...",
  "strategic_focus": "..."
}
```

---

## 8. 구현 순서

| 순서 | 작업 | 예상 파일 | 의존성 |
|------|------|-----------|--------|
| 1 | GoNoGoResult 모델 확장 | `state.py` | 없음 |
| 2 | `score_qualification` 구현 | `context_helpers.py` | 1 |
| 3 | `score_similar_performance` 구현 | `context_helpers.py` | 1 |
| 4 | `score_competition` 구현 | `context_helpers.py` | 1 |
| 5 | `go_no_go.py` 개편 (3축 + AI + 합산) | `go_no_go.py` | 2, 3, 4 |
| 6 | GoNoGoPanel 프론트 개편 | `GoNoGoPanel.tsx` | 5 |
| 7 | ArtifactReviewPanel 수정 | `ArtifactReviewPanel.tsx` | 5 |
| 8 | capabilities 시드 확장 | `seed_data.py`, migration | 없음 |
| 9 | E2E 검증 + ruff/mypy | 전체 | 1~8 |

---

## 9. Next Steps

1. [ ] 설계 문서 작성 (`go-no-go-enhancement.design.md`)
2. [ ] 팀 리뷰 및 점수 배분 확정 (30/30/20/20 vs 대안)
3. [ ] 구현 착수

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-26 | Initial draft — 3축 정량 분석 + 70점 게이트 구상 | AI |
