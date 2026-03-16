# Phase 4 계획: G2B 클라이언트 + 성과 추적

| 항목 | 내용 |
|------|------|
| 문서 버전 | v1.0 |
| 작성일 | 2026-03-16 |
| 상태 | 초안 |
| 기반 설계 | docs/02-design/features/proposal-agent-v1/_index.md (v3.6) |
| 선행 Phase | Phase 0~3 완료 (98% match rate) |
| 제외 항목 | PPTX 빌더 (별도 Phase로 분리) |

---

## 1. 목적

Phase 0~3에서 구축한 LangGraph 워크플로(RFP 분석 → 전략 → 계획 → 제안서 작성 → 산출물)의 **사업 생애주기 완결**을 위해, 입찰 결과 추적과 성과 분석 기능을 구현한다.

### 핵심 가치
- **제안 결과 피드백 루프**: 수주/패찰/유찰 결과를 KB에 축적 → 다음 제안 품질 향상
- **G2B 낙찰정보 자동 수집**: 수동 확인 없이 입찰 결과를 자동 업데이트
- **성과 대시보드**: 부서/팀별 수주율, 금액, 트렌드를 한눈에 파악

---

## 2. 범위 (Scope)

### In-Scope

| # | 기능 | 설계 참조 | 우선순위 |
|---|------|----------|:--------:|
| 4-1 | G2B 낙찰정보 클라이언트 | §12-12 (낙찰가 API), §15-5i (market_price_data) | HIGH |
| 4-2 | 제안 결과 등록 API | §12-4 (프로젝트 상태 관리) | HIGH |
| 4-3 | 성과 추적 Materialized View | §15 (MV 정의) | HIGH |
| 4-4 | 분석 대시보드 API | §12-13 (routes_analytics.py), §31-8 | MEDIUM |
| 4-5 | 교훈(Lessons Learned) 등록 | §20-5 (LRN KB), §23 | MEDIUM |
| 4-6 | 성과 기반 KB 업데이트 | §20-5 (LRN-08 포지셔닝 정확도) | MEDIUM |

### Out-of-Scope (이번 Phase 제외)
- PPTX 빌더 (python-pptx) — 별도 Phase
- 프론트엔드 구현 — Phase 5 이후
- 실시간 G2B 모니터링 스케줄러 — OPS-01 (LOW)

---

## 3. 기능 상세

### 4-1. G2B 낙찰정보 클라이언트

**목적**: 나라장터 낙찰정보를 조회하여 `market_price_data` 테이블에 저장

**구현 파일**: `app/services/g2b_client.py` (기존 `g2b_service.py` 확장)

**핵심 기능**:
- 공고번호 기반 낙찰 결과 조회 (낙찰업체, 낙찰가, 투찰업체 수)
- 낙찰률(낙찰가/예정가) 자동 산출
- `market_price_data` 테이블 자동 적재
- 조회 실패 시 재시도 + 캐싱 (§22-4 Fallback 전략)

**API 엔드포인트**:
```
POST /api/g2b/bid-results/{bid_notice_id}  — 특정 공고 낙찰정보 수집
GET  /api/g2b/bid-results                  — 낙찰정보 목록 조회 (필터: 도메인, 기간, 금액 범위)
POST /api/g2b/bid-results/bulk-sync        — 진행 중인 프로젝트의 낙찰정보 일괄 동기화
```

**데이터 모델** (기존 `market_price_data` 테이블 활용):
```sql
-- database/schema_v3.4.sql §15-5i 이미 정의됨
-- 추가 필요 컬럼 없음, 기존 스키마 그대로 사용
```

### 4-2. 제안 결과 등록 API

**목적**: 프로젝트의 입찰 결과(수주/패찰/유찰)를 등록하고 KB에 반영

**구현 파일**: `app/api/routes_proposal.py` (기존 라우트 확장)

**API 엔드포인트**:
```
POST /api/proposals/{id}/result    — 입찰 결과 등록
GET  /api/proposals/{id}/result    — 입찰 결과 조회
PUT  /api/proposals/{id}/result    — 입찰 결과 수정
```

**입력 스키마**:
```python
class ProposalResultCreate(BaseModel):
    result: Literal["won", "lost", "void"]  # 수주/패찰/유찰
    final_price: int | None = None           # 최종 낙찰가
    competitor_count: int | None = None      # 경쟁업체 수
    ranking: int | None = None               # 순위 (패찰 시)
    tech_score: float | None = None          # 기술점수
    price_score: float | None = None         # 가격점수
    total_score: float | None = None         # 종합점수
    feedback_notes: str | None = None        # 패찰 사유/교훈
    won_by: str | None = None                # 낙찰업체 (패찰 시)
```

**후처리**:
- `proposals.status` → `won` / `lost` / `void` 업데이트
- `result == "won"` → 수주 실적 KB 자동 등록 제안 (알림)
- `result == "lost"` → 교훈 등록 유도 (알림)
- Materialized View 갱신 트리거

### 4-3. 성과 추적 Materialized View

**목적**: 부서/팀/개인별 수주율, 금액, 트렌드를 실시간 집계

**구현 파일**: `database/migrations/004_performance_views.sql`

```sql
-- 부서별 성과 집계
CREATE MATERIALIZED VIEW mv_team_performance AS
SELECT
    t.id AS team_id,
    t.name AS team_name,
    d.name AS division_name,
    COUNT(*) FILTER (WHERE p.status IN ('won', 'lost', 'void')) AS total_proposals,
    COUNT(*) FILTER (WHERE p.status = 'won') AS won_count,
    COUNT(*) FILTER (WHERE p.status = 'lost') AS lost_count,
    ROUND(
        COUNT(*) FILTER (WHERE p.status = 'won')::numeric /
        NULLIF(COUNT(*) FILTER (WHERE p.status IN ('won', 'lost')), 0) * 100, 1
    ) AS win_rate,
    SUM(p.budget) FILTER (WHERE p.status = 'won') AS total_won_amount,
    AVG(pr.tech_score) FILTER (WHERE pr.tech_score IS NOT NULL) AS avg_tech_score,
    DATE_TRUNC('quarter', p.created_at) AS quarter
FROM proposals p
JOIN proposal_results pr ON pr.proposal_id = p.id
JOIN teams t ON t.id = p.team_id
JOIN divisions d ON d.id = t.division_id
GROUP BY t.id, t.name, d.name, DATE_TRUNC('quarter', p.created_at);

-- 포지셔닝별 성과 (LRN-08)
CREATE MATERIALIZED VIEW mv_positioning_accuracy AS
SELECT
    s.positioning,
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE p.status = 'won') AS won,
    ROUND(
        COUNT(*) FILTER (WHERE p.status = 'won')::numeric /
        NULLIF(COUNT(*), 0) * 100, 1
    ) AS win_rate
FROM proposals p
JOIN proposal_strategies s ON s.proposal_id = p.id
GROUP BY s.positioning;

-- MV 갱신 함수
CREATE OR REPLACE FUNCTION refresh_performance_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_team_performance;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_positioning_accuracy;
END;
$$ LANGUAGE plpgsql;
```

### 4-4. 분석 대시보드 API

**목적**: 프론트엔드 AnalyticsPage에 데이터 제공

**구현 파일**: `app/api/routes_analytics.py` (기존 파일 확장)

**API 엔드포인트** (§12-13 + §31-8):
```
GET /api/analytics/win-rate          — 수주율 트렌드 (분기별/연도별)
GET /api/analytics/team-performance  — 부서/팀별 성과 비교
GET /api/analytics/positioning       — 포지셔닝별 수주율 (LRN-08)
GET /api/analytics/competitor        — 경쟁사별 대전 기록
```

### 4-5. 교훈(Lessons Learned) 등록

**목적**: 패찰 사유 및 수주 성공 요인을 KB에 축적

**구현 파일**: `app/api/routes_proposal.py` (result 등록 시 연동)

**API 엔드포인트**:
```
POST /api/proposals/{id}/lessons     — 교훈 등록
GET  /api/proposals/{id}/lessons     — 교훈 조회
GET  /api/lessons                    — 교훈 검색 (키워드, 도메인, 기간)
```

**교훈 스키마**:
```python
class LessonCreate(BaseModel):
    category: Literal["strategy", "pricing", "team", "technical", "process", "other"]
    title: str                         # 교훈 제목
    description: str                   # 상세 내용
    impact: Literal["high", "medium", "low"]  # 영향도
    action_items: list[str] = []       # 개선 조치 사항
    applicable_domains: list[str] = [] # 적용 가능 도메인
```

### 4-6. 성과 기반 KB 업데이트

**목적**: 입찰 결과를 KB(역량 DB, 경쟁사 DB, 교훈 DB)에 자동 반영

**트리거**:
- 수주 시: `capabilities` 테이블에 수행 실적 추가 제안 (알림)
- 패찰 시: `competitors` 테이블에 낙찰업체 정보 업데이트
- 교훈 등록 시: `lessons_learned` 테이블 + 벡터 임베딩 생성 (pgvector)

---

## 4. 구현 순서

```
4-1. G2B 낙찰정보 클라이언트     ──┐
                                   ├── 4-3. Materialized View ── 4-4. 분석 API
4-2. 제안 결과 등록 API          ──┘
                                         │
                                   4-5. 교훈 등록 ── 4-6. KB 업데이트
```

| 순서 | 항목 | 예상 작업량 | 의존성 |
|:----:|------|:----------:|--------|
| 1 | 4-2. 제안 결과 등록 API | 중 | Phase 3 완료 |
| 2 | 4-1. G2B 낙찰정보 클라이언트 | 중 | 기존 g2b_service.py |
| 3 | 4-3. Materialized View | 소 | 4-1, 4-2 |
| 4 | 4-4. 분석 대시보드 API | 소 | 4-3 |
| 5 | 4-5. 교훈 등록 | 소 | 4-2 |
| 6 | 4-6. KB 업데이트 | 소 | 4-5 |

---

## 5. 검증 방법

1. **제안 결과 등록**: 수주/패찰/유찰 각 케이스 API 테스트
2. **G2B 클라이언트**: mock 응답 기반 낙찰정보 파싱 + DB 적재 확인
3. **Materialized View**: 시드 데이터 기반 집계 정확성 검증
4. **분석 API**: 각 엔드포인트 응답 스키마 + 필터 동작 확인
5. **교훈 → KB**: 등록 후 벡터 검색에서 검색 가능 여부 확인

---

## 6. 잔여 갭 해소 계획

| 갭 ID | 항목 | Phase 4 대응 |
|-------|------|-------------|
| PSM-05 | 프로젝트 상태 머신 완결 | 4-2에서 won/lost/void 상태 전이 구현 |
| PSM-16 | 결과 기반 KB 업데이트 | 4-6에서 자동 반영 구현 |
| POST-06 | 성과 추적 MV | 4-3에서 구현 |
| OPS-02 | 성과 데이터 백업 | MV CONCURRENTLY 갱신으로 무중단 |
| OPS-03 | 데이터 보존 정책 | 결과 데이터 soft-delete 적용 |
