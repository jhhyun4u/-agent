# Archive Index - 2026-03

| Feature | 완료일 | Match Rate | 이터레이션 | 경로 |
|---------|--------|------------|------------|------|
| proposal-agent-v33 | 2026-03-05 | 100% | 1 | proposal-agent-v33/ |
| tenopa-proposer | 2026-03-08 | 97% | 2 | tenopa-proposer/ |
| frontend-components | 2026-03-07 | 95% | 0 | frontend-components/ |
| admin-page | 2026-03-07 | 97% | 0 | admin-page/ |
| prompt-enhancement | 2026-03-08 | 97% | 0 | prompt-enhancement/ |
| proposal-quality-v2 | 2026-03-08 | 100% | 0 | proposal-quality-v2/ |
| proposal-quality-v3 | 2026-03-08 | 100% | 0 | proposal-quality-v3/ |
| proposal-quality-v4 | 2026-03-08 | 100% | 0 | proposal-quality-v4/ |
| proposal-platform-v2 | 2026-03-08 | 91% | 1 | proposal-platform-v2/ |
| proposal-platform-v2.1 | 2026-03-08 | 97% | 0 | proposal-platform-v2.1/ |
| bid-recommendation | 2026-03-08 | 100% | 0 | bid-recommendation/ |
| presentation-generator | 2026-03-08 | 95% | 0 | presentation-generator/ |
| dashboard | 2026-03-08 | 100% | 1 | dashboard/ |
| api | 2026-03-08 | 90% | 1 | api/ |
| bid-search | 2026-03-08 | 96% | 0 | bid-search/ |

---

## proposal-agent-v33

| 항목 | 내용 |
|------|------|
| 완료일 | 2026-03-05 |
| Match Rate | 100% |
| Documents | plan, design, analysis, report |
| Path | docs/archive/2026-03/proposal-agent-v33/ |

---

## tenopa-proposer (proposal-platform-v1) — Completed

| 항목 | 내용 |
|------|------|
| 완료일 | 2026-03-08 |
| 시작일 | 2026-03-05 |
| 기간 | 4일 |
| Match Rate | **97%** |
| PDCA 반복 | 2회 Act (85% → 93% → 97%) |
| Documents | plan, design, analysis, report |
| Path | docs/archive/2026-03/tenopa-proposer/ |
| 주요 성과 | SaaS 플랫폼 전환 완료 — G2B API, Supabase 전체 스택, 팀 협업, JWT, Realtime, Storage, HWPX |
| 성공 기준 | 18/18 (100%) |

---

## frontend-components

| 항목 | 내용 |
|------|------|
| 완료일 | 2026-03-07 |
| Match Rate | **95%** |
| PDCA 반복 | 0회 (첫 번째 시도 통과) |
| Documents | plan, design, analysis, report |
| Path | docs/archive/2026-03/frontend-components/ |
| 주요 성과 | 3초 polling → Supabase Realtime 전환, API 호출 95% 감소, hybrid fetch 전략 |

---

## admin-page

| 항목 | 내용 |
|------|------|
| 완료일 | 2026-03-07 |
| Match Rate | **97%** |
| PDCA 반복 | 0회 (첫 번째 시도 통과) |
| Documents | plan, design, analysis, report |
| Path | docs/archive/2026-03/admin-page/ |
| 주요 성과 | 팀원 UUID→이메일 표시, 팀 이름 수정 UI, 팀 통계 섹션 |

---

## prompt-enhancement

| 항목 | 내용 |
|------|------|
| 완료일 | 2026-03-08 |
| Match Rate | **97%** |
| PDCA 반복 | 0회 |
| Documents | plan, design, analysis, report |
| Path | docs/archive/2026-03/prompt-enhancement/ |
| 주요 성과 | Alternatives Considered, Risks/Mitigations, Implementation Checklist 자동 생성 |
| 참조 | foreline/js-editor proposal-writer SKILL.md |

---

## proposal-quality-v2

| 항목 | 내용 |
|------|------|
| 완료일 | 2026-03-08 |
| Match Rate | **100%** |
| PDCA 반복 | 0회 |
| Documents | plan, design, analysis, report |
| Path | docs/archive/2026-03/proposal-quality-v2/ |
| 주요 성과 | 평가항목-섹션 매핑(target_criteria/score_weight), Logic Model(inputs→outcomes) 자동 생성 |
| 참조 | travisjneuman/claude-grant-proposal-builder SKILL.md |

---

## proposal-platform-v2 — Completed

| 항목 | 내용 |
|------|------|
| 완료일 | 2026-03-08 |
| Match Rate | **91%** |
| PDCA 반복 | 1회 Act (78% → 93% → 91% 최종) |
| Documents | plan, design, analysis, report |
| Path | docs/archive/2026-03/proposal-platform-v2/ |
| 주요 성과 | 섹션 라이브러리 + 공통서식 + 버전관리 + 수주율 대시보드 + RFP 캘린더 (Phase A~D) |
| API 엔드포인트 | 27개 신규 |
| DB 테이블 | 4개 신규 (sections, company_assets, form_templates, rfp_calendar) |
| 잔여 P2 | G-01(섹션선택UI), G-03(버전비교UI), G-09(asset_extractor) → v2.1 완료 |

---

## bid-recommendation — Completed (v2.0)

| 항목 | 내용 |
|------|------|
| 완료일 | 2026-03-08 |
| Match Rate | **100%** (백엔드 100% + 프론트엔드 100%) |
| PDCA 반복 | 0회 (6개 P0/P1/P2 수정 후 통과) |
| Documents | plan, design, analysis, report |
| Path | docs/archive/2026-03/bid-recommendation/ |
| 주요 성과 | 나라장터 공고 AI 추천 풀스택 완료 — 2단계 분석(자격판정+매칭점수), 폴링 패턴, 온보딩 3단계, announce_date_range_days 날짜 필터, preferred_agencies 입력, 공고→제안서 자동 주입 |
| API 엔드포인트 | 12개 신규 (routes_bids.py) |
| DB 테이블 | 4개 신규 (bid_announcements, team_bid_profiles, search_presets, bid_recommendations) |
| 프론트엔드 | 3페이지 완료 (/bids, /bids/[bidNo], /bids/settings) |

---

## presentation-generator — Completed

| 항목 | 내용 |
|------|------|
| 완료일 | 2026-03-08 |
| Match Rate | **95%** |
| PDCA 반복 | 0회 (첫 번째 시도 통과) |
| Documents | plan, design, analysis, report |
| Path | docs/archive/2026-03/presentation-generator/ |
| 주요 성과 | 평가항목 배점 기반 2-step 파이프라인(TOC→스토리보드), 7종 레이아웃 PPTX 빌더, 4개 API 엔드포인트 |
| 잔여 작업 | PPTX 템플릿 파일 3개 (scratch fallback으로 동작) |

---

## bid-search — Completed (테스트 커버리지 강화)

| 항목 | 내용 |
|------|------|
| 완료일 | 2026-03-08 |
| Match Rate | **96%** |
| PDCA 반복 | 0회 (첫 번째 시도 통과) |
| Documents | analysis, report |
| Path | docs/archive/2026-03/bid-search/ |
| 주요 성과 | 74개 유닛/API 테스트 신규 작성, BidFetcher 95%·BidRecommender 98% 커버리지, 프로덕션 버그 1건 수정 (routes_bids.py:286 team_id 중복) |
| 성공 기준 | 8/8 (100%) |

---

## proposal-platform-v2.1 — Completed

| 항목 | 내용 |
|------|------|
| 완료일 | 2026-03-08 |
| Match Rate | **97%** |
| PDCA 반복 | 0회 (직접 수정) |
| Documents | plan, analysis, report |
| Path | docs/archive/2026-03/proposal-platform-v2.1/ |
| 주요 성과 | v2 잔여 P2 3건 해결 — 섹션 선택 UI, AI 섹션 자동 추출(asset_extractor), 버전 비교 탭 |
| 성공 기준 | 6/6 (100%) |

---

## dashboard — Completed

| 항목 | 내용 |
|------|------|
| 완료일 | 2026-03-08 |
| Match Rate | **100%** |
| PDCA 반복 | 1회 (95.3% → 100%) |
| Documents | design, analysis, report |
| Path | docs/archive/2026-03/dashboard/ |
| 주요 성과 | 오늘 할 일(액션 허브), 제안 파이프라인 뷰, 추천 공고 S/A 위젯, KPI 추세 표시, 인사이트 카드 |
| 핵심 원칙 | 기존 API 재사용, 신규 백엔드 없음, 사용자 행동 유도 중심 UX |

