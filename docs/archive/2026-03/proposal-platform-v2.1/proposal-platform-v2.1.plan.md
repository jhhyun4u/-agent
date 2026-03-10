# Plan: proposal-platform-v2.1

## 메타 정보
| 항목 | 내용 |
|------|------|
| Feature | proposal-platform-v2.1 |
| 작성일 | 2026-03-08 |
| 기반 | proposal-platform-v2 (archived, 91% match) |
| 목표 | v2 잔여 P2 이슈 3건 해결 → Match Rate 97%+ |

---

## 배경

proposal-platform-v2 PDCA 사이클에서 91% match rate 달성 후 아카이브 완료.
잔여 P2 이슈 3건을 v2.1에서 처리한다.

---

## 구현 범위

### G-01: proposals/new 섹션 선택 스텝

**현재 상태:** proposals/new 페이지에 파일 업로드 + 서식 선택 + 기본 정보 입력만 있음
**목표:** 섹션 라이브러리에서 관련 섹션을 선택하여 AI 컨텍스트에 포함

**구현 내용:**
- `frontend/app/proposals/new/page.tsx` — 섹션 선택 UI 추가
  - `api.sections.list()` 호출로 섹션 목록 로드
  - 카테고리별 탭/필터 (company_intro, track_record, methodology, organization, schedule, cost, other)
  - 섹션 카드 클릭 → 다중 선택 (toggle)
  - 선택된 섹션 ID 배열 → FormData `section_ids` 필드로 제출
- `app/api/routes_v31.py` — generate 엔드포인트에서 `section_ids` 파라미터 수신 및 proposals 테이블 저장

**예상 공수:** ~4h

---

### G-03: 버전 비교 UI

**현재 상태:** 버전 드롭다운으로 전환만 가능, 나란히 비교 불가
**목표:** v1 vs v2 등 두 버전 결과물을 나란히 표시

**구현 내용:**
- `frontend/app/proposals/[id]/page.tsx` — 버전 비교 탭/모드 추가
  - "버전 비교" 탭 또는 헤더 "비교" 버튼
  - 비교 대상 버전 선택 드롭다운 (현재 버전 기준으로 다른 버전 선택)
  - 2-column 레이아웃: 왼쪽 현재 버전 결과물 / 오른쪽 선택된 버전 결과물
  - 양쪽 모두 Phase별 탭으로 전환 가능
  - 반응형: 모바일에서는 탭으로 전환

**예상 공수:** ~6h

---

### G-09: asset_extractor.py (AI 섹션 자동 추출)

**현재 상태:** 회사 자료 업로드 시 Storage에 저장만 됨, AI 분석 없음
**목표:** 업로드된 PDF/DOCX에서 Claude API를 통해 섹션 자동 추출

**구현 내용:**
- `app/services/asset_extractor.py` (신규)
  - `extract_sections_from_asset(asset_id, file_content, file_type)` async 함수
  - Claude API로 문서 분석 → 카테고리별 섹션 자동 생성
  - 생성된 섹션을 `sections` 테이블에 INSERT
  - `company_assets.extracted_sections` 컬럼 업데이트
  - `company_assets.status` = 'processing' → 'done' / 'failed'
- `app/api/routes_resources.py` — assets POST 엔드포인트에서 백그라운드 작업으로 추출 트리거
- 프론트엔드: 자료 카드에 추출 상태 폴링 or Realtime 구독 (status 뱃지)

**예상 공수:** ~7h

---

## 우선순위

| 항목 | 우선순위 | 난이도 | 공수 |
|------|----------|--------|------|
| G-01 섹션 선택 UI | High | Low | ~4h |
| G-09 asset_extractor | High | High | ~7h |
| G-03 버전 비교 UI | Medium | Medium | ~6h |

**구현 순서:** G-01 → G-09 → G-03

---

## 성공 기준

- [ ] proposals/new에서 섹션 다중 선택 가능
- [ ] 선택된 섹션이 proposals.section_ids에 저장됨
- [ ] 회사 자료 업로드 후 AI가 섹션을 자동 추출
- [ ] 추출 상태가 UI에 표시됨 (processing → done)
- [ ] 두 버전의 결과물을 나란히 비교 가능
- [ ] Gap Analysis >= 97%

---

## 비범위

- 새로운 Phase 추가 없음
- 기존 API 스펙 변경 없음
- DB 스키마 변경 없음 (proposals.section_ids, company_assets.extracted_sections 이미 존재)
