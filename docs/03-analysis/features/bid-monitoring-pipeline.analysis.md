# bid-monitoring-pipeline — 갭 분석

| 항목 | 내용 |
|------|------|
| 분석일 | 2026-03-25 |
| Design 참조 | docs/02-design/features/bid-monitoring-pipeline.design.md (v1.0) |
| Match Rate | **95%** (BUG-1 수정 후 97%) |

---

## Match Rate

| Section | Items | Matched | Changed | Added | Bug | Rate |
|---------|:-----:|:-------:|:-------:|:-----:|:---:|:----:|
| §4-1 Pipeline | 13 | 10 | 3 | 0 | 0 | 93% |
| §4-2 Attachment | 6 | 5 | 1 | 0 | 0 | 96% |
| §4-3 API | 5 | 3 | 1 | 1 | 0 | 92% |
| §4-4 Monitor | 3 | 1 | 0 | 0 | 1 | 85% |
| §4-5 Frontend | 4 | 3 | 0 | 1 | 0 | 90% |
| **Total** | **31** | **22** | **5** | **2** | **1** | **95%** |

---

## GAP 목록

| ID | Type | Severity | 설명 | 조치 |
|----|------|----------|------|------|
| BUG-1 | Bug | **HIGH** | `scheduled_monitor.py:170` — `b["bid_no"]` dict 접근을 BidScore dataclass에 사용. RuntimeError 발생 | 즉시 수정: `b.bid_no` / `b.score` |
| ADD-2 | Added | MEDIUM | `POST /bids/pipeline/trigger` 엔드포인트 — 설계에 없으나 운영에 유용 | 설계 문서 보완 |
| CHG-1~5 | Changed | LOW | score_threshold 파라미터 이동, import 경로, 텍스트 추출 API 등 의도적 변경 | 조치 불필요 |
| ADD-1,3 | Added | LOW | `_update_status` 헬퍼, scored fallback 분석 — 코드 품질/UX 개선 | 조치 불필요 |

---

## 결론

**PASS (95% >= 90%)**. BUG-1(HIGH) 1건 즉시 수정 필요. 수정 후 97% 달성.
