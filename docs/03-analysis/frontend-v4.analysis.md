# 프론트엔드 설계-구현 갭 분석 보고서 v4.0

> **분석 대상**: 프론트엔드 (Next.js + React)
> **설계 문서**: `docs/02-design/features/frontend-ux-improvement.design.md`, `proposal-agent-v1/` (SS12, SS13, SS31)
> **구현 경로**: `frontend/`
> **분석일**: 2026-03-26 (v4.0)
> **이전 분석**: v3.0 (2026-03-19, 94%)
> **종합 일치율**: **93%** (90% 품질 게이트 통과)

---

## 1. 전체 요약

| 카테고리 | v3.0 (03-19) | v4.0 (03-26) | 상태 |
|----------|:----:|:----:|:----:|
| 라우트 완전성 | 100% | **100%** | O |
| 컴포넌트 완전성 | 97% | **96%** | O |
| API 클라이언트 커버리지 | 97% | **96%** | O |
| UX 개선 설계 일치 | - | **91%** | O |
| UI 라이브러리 인프라 | 75% | **78%** | ! |
| 컨벤션 준수 | - | **90%** | O |
| **종합** | **94%** | **93%** | **O** |

> 점수 기준: O = 90%+, ! = 70~89%, X = 70% 미만

---

## 2. 라우트 현황 (100%)

37개 page.tsx — 설계 22개 전수 구현 + 추가 15개 라우트 (monitoring, pricing, admin/prompts, editor 등)

---

## 3. 갭 목록

### MISSING (설계 O, 구현 X)

| GAP# | 항목 | 설계 위치 | 우선순위 | 설명 |
|------|------|----------|:--------:|------|
| GAP-1 | **AppSidebar 모바일 오버레이** | UX Design 3-1-B | **HIGH** | `lg:hidden` 햄버거 + 오버레이 드로어 미구현. 기존 분석 보고서에 "수정 완료"로 오기록 |
| GAP-2 | artifacts.diff API 메서드 | SS12-4 M2 | MEDIUM | `api.ts`에 `artifacts/{step}/diff` 메서드 없음 |
| GAP-3 | Tiptap placeholder 확장 | SS31-3-4 | LOW | `@tiptap/extension-placeholder` 미설치 |
| GAP-4 | Tiptap table 확장 | SS31-3-4 | LOW | `@tiptap/extension-table` 미설치 |
| GAP-5 | CSS 유틸리티 라이브러리 | SS31-3-4 | LOW | `tailwind-merge`, `clsx`, `cva` 미설치 |

### UNUSED (구현 O, 사용 X)

| GAP# | 항목 | 파일 | 우선순위 | 설명 |
|------|------|------|:--------:|------|
| GAP-6 | ui/Card | `components/ui/Card.tsx` | LOW | import 0건 |
| GAP-7 | ui/Modal | `components/ui/Modal.tsx` | LOW | import 0건 |
| GAP-8 | ui/Badge | `components/ui/Badge.tsx` | LOW | import 0건 |
| GAP-9 | FileBar | `components/FileBar.tsx` | LOW | import 0건 |
| GAP-10 | ProjectArchivePanel | `components/ProjectArchivePanel.tsx` | LOW | import 0건 |

### CHANGED (설계 ≠ 구현, 의도적)

| CHG# | 항목 | 설계 | 구현 | 영향 |
|------|------|------|------|:----:|
| CHG-1 | 인증 | Azure AD SSO | Supabase email/password | HIGH (인프라) |
| CHG-2 | 실시간 | SSE only | SSE + Supabase Realtime | LOW |
| CHG-3 | UI 시스템 | shadcn/ui | Radix direct + Tailwind | LOW |
| CHG-4 | 대시보드 | 역할별 5뷰 | 스코프 토글 단일 뷰 | LOW |

---

## 4. 주요 발견사항

1. **분석 보고서 오류**: `frontend-ux-improvement.analysis.md`에서 GAP-2(사이드바 모바일)를 "수정 완료"로 오기록 → 구현 누락 상태
2. **설계 초과 구현**: 가격 시뮬레이션(8 컴포넌트), 프롬프트 진화(8 컴포넌트+7 라우트), 모니터링 재구성(4 라우트) — 설계 역반영 필요
3. **디자인 시스템 미활용**: ui/Card, Modal, Badge 생성만 되고 실제 사용 0건
4. **v3.1 레거시 완전 제거 확인**: api.ts에서 `/v3.1/` 참조 0건
5. **diff-match-patch**: 이번 세션에서 설치 완료, 빌드 경고 해소

---

## 5. 권고 조치

| 순서 | 항목 | 공수 | 비고 |
|:----:|------|------|------|
| 1 | GAP-1: AppSidebar 모바일 오버레이 | 0.5d | UX 설계서에 코드 예시 있음 |
| 2 | GAP-2: artifacts.diff API 메서드 | 0.5d | api.ts 추가 + 버전 비교 UI 연동 |
| 3 | GAP-3/4: Tiptap 확장 설치 | 0.5d | placeholder + table |
| 4 | GAP-6~10: 미사용 컴포넌트 정리 | 0.5d | 삭제 또는 실제 적용 |
| 5 | 설계 역반영 | 1d | 추가 15개 라우트 + pricing/prompts 설계 문서화 |
