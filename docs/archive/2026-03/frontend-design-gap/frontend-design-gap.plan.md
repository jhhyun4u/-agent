# Frontend Design Gap 해소 계획서

> 설계 문서(§13 프론트엔드 핵심 컴포넌트) 대비 미구현/차이 항목을 체계적으로 해소하여 설계 충실도를 94% → 98%+ 로 끌어올린다.

## 1. 배경 및 목적

### 현재 상태
- **갭 분석 v3.0 기준**: 종합 94% (라우트 100%, 컴포넌트 97%, API 97%, UI 인프라 75%, 기능 충실도 95%)
- **35개 라우트** 100% 존재, **50+ 컴포넌트** 구현 완료
- 핵심 워크플로(3-Panel, Tiptap 편집기, PhaseGraph, 3-Stream 탭) 모두 동작

### 문제점
설계 문서 대비 **디테일 완성도** 부족으로 사용자 체감 품질 저하:

| 등급 | 항목수 | 대표 문제 |
|------|:------:|-----------|
| HIGH | 0 | (v2.0에서 레거시 API 통일, 3가지 진입 경로 해소 완료) |
| MEDIUM | 6 | Go/No-Go 점수 부족, 대시보드 역할 분리, 포지셔닝 미리보기, UI 인프라 |
| LOW | 6 | 병렬 미리보기, AI 하이라이트, 결재선, CSV, 본부별 비교, 역량 인라인 |

### 핵심 원칙
- **백엔드 수정 최소화** — 프론트엔드 UI 보강에 집중 (API는 이미 존재)
- **설계 문서 기준** — §13 와이어프레임에 명시된 정보를 빠짐없이 표시
- **체감 효과 우선** — 사용자가 바로 느낄 수 있는 MEDIUM 항목 먼저

## 2. 구현 범위

### Phase A — Go/No-Go 패널 보강 (§13-4 충실도 85% → 95%)

**현재**: 포지셔닝 선택 + 의사결정 사유만 표시
**설계**: AI 수주 가능성 4축 점수(기술/실적/가격/경쟁) + 강점/리스크 분할 + 종합 점수 바

#### A-1. GoNoGoPanel 4축 점수 표시
- `go_no_go` 노드 산출물에서 `scores` (기술적합도/수행실적/가격경쟁력/경쟁환경) 파싱
- 종합 점수 프로그레스 바 (`████████░░ 78점`)
- 4개 항목별 점수 카드
- **수정 파일**: `components/GoNoGoPanel.tsx`

#### A-2. 강점/리스크 분할 표시
- `go_no_go` 산출물에서 `pros[]`, `risks[]` 배열 파싱
- 좌측: ✅ 강점 리스트 / 우측: ⚠️ 리스크 리스트
- AI 추천 결과 (Go/No-Go/재검토) 표시
- **수정 파일**: `components/GoNoGoPanel.tsx`

### Phase B — 대시보드 역할별 위젯 (§13-8 충실도 75% → 90%)

**현재**: 단일 대시보드 + 스코프 토글 (개인/팀/본부/전체)
**설계**: 팀장 전용 위젯(결재대기/마감임박), 경영진 전용 위젯(본부비교/포지셔닝별)

#### B-1. 팀장 위젯 — 결재 대기 + 마감 임박
- 스코프 `team` 선택 시 결재 대기 목록(review_pending 상태 프로젝트) 위젯 자동 표시
- 마감 임박(D-7 이내) 프로젝트 경고 위젯
- **수정 파일**: `app/(app)/dashboard/page.tsx`
- **API**: `api.proposals.list({ status: 'review_pending' })` (기존 API 활용)

#### B-2. 경영진 위젯 — 본부별 비교 테이블
- 스코프 `company` 선택 시 본부별 비교 테이블(진행건/수주율/평균소요) 표시
- `api.analytics.teamPerformance()` 데이터 활용 (이미 연동됨)
- **수정 파일**: `app/(app)/dashboard/page.tsx`

### Phase C — 포지셔닝 변경 영향 미리보기 (§13-6 미구현 → 구현)

**현재**: 미구현 (impact API는 `routes_workflow.py`에 존재)
**설계**: Ghost/Win Theme 변경 + 재생성 범위 + 승인 초기화 경고 다이얼로그

#### C-1. PositioningImpactModal 신규 컴포넌트
- Go/No-Go 패널에서 포지셔닝 변경 시 `api.workflow.impact(id, step)` 호출
- 변경 영향 표시: Ghost Theme / Win Theme / 가격 전략 / 인력 구성
- ⚠️ 재생성 범위 경고 + [취소] / [변경 확정] 버튼
- **신규 파일**: `components/PositioningImpactModal.tsx`
- **수정 파일**: `components/GoNoGoPanel.tsx` (포지셔닝 변경 시 모달 트리거)

### Phase D — UI 인프라 보강 (§31-3 충실도 75% → 85%)

**현재**: Radix UI 직접 사용 + raw Tailwind. shadcn/ui 미도입.
**방향**: 전면 shadcn/ui 마이그레이션은 과도 → 핵심 유틸만 도입

#### D-1. Tiptap 확장 설치
- `@tiptap/extension-table` — 편집기 테이블 편집 지원
- `@tiptap/extension-placeholder` — 빈 에디터 가이드 텍스트
- **수정 파일**: `components/ProposalEditor.tsx`, `package.json`

#### D-2. tailwind-merge + clsx 도입
- 조건부 스타일 관리 개선 (cn() 유틸 함수)
- **신규 파일**: `lib/utils.ts` (cn 함수)
- **수정 파일**: `package.json`

### Phase E — LOW 우선순위 (선택적)

설계 충실도 98% 달성 후 필요 시 진행:

| # | 항목 | 설계 섹션 | 설명 |
|---|------|-----------|------|
| 1 | 병렬 미리보기 버튼 | §13-7 | 완료 항목 '미리보기' → ArtifactViewer 모달 |
| 2 | AI 인라인 하이라이트 | §13-10 | self_review 피드백 → 노란 하이라이트 자동 주입 |
| 3 | ApprovalChainStatus | §13-8-3 | 결재선 시각화 컴포넌트 |
| 4 | CSV 가져오기/내보내기 | §13-13 | KB 테이블 CSV import/export |
| 5 | 역량 DB 인라인 편집 | §13-9 | 워크플로 내 역량 등록 모달 |
| 6 | 편집기 섹션 잠금 실시간 | §13-10 | SectionLockIndicator 실시간 연동 |

## 3. 구현 순서 및 의존성

```
Phase A (GoNoGoPanel 보강)     ← 의존성 없음, 가장 체감 큼
  ↓
Phase B (대시보드 역할 위젯)    ← 기존 API 활용, 독립적
  ↓
Phase C (포지셔닝 미리보기)     ← Phase A와 연관 (GoNoGoPanel 수정)
  ↓
Phase D (UI 인프라)             ← 독립적, npm install 필요
  ↓
Phase E (LOW, 선택적)
```

> Phase A + C는 GoNoGoPanel 파일을 공유하므로 연속 진행 권장.
> Phase B, D는 독립적이므로 병렬 가능.

## 4. 수정 대상 파일

### 신규 파일 (2개)
| 파일 | 용도 |
|------|------|
| `components/PositioningImpactModal.tsx` | 포지셔닝 변경 영향 미리보기 |
| `lib/utils.ts` | cn() 유틸 (tailwind-merge + clsx) |

### 수정 파일 (4개)
| 파일 | Phase | 변경 내용 |
|------|-------|-----------|
| `components/GoNoGoPanel.tsx` | A, C | 4축 점수 + 강점/리스크 + 모달 트리거 |
| `app/(app)/dashboard/page.tsx` | B | 결재대기/마감임박/본부별 위젯 |
| `components/ProposalEditor.tsx` | D | Tiptap table/placeholder 확장 추가 |
| `package.json` | D | tailwind-merge, clsx, tiptap 확장 |

## 5. 범위 외 (NOT Scope)

| 항목 | 사유 |
|------|------|
| shadcn/ui 전면 도입 | 기존 Radix + Tailwind로 기능 동일. 마이그레이션 비용 대비 효과 미미 |
| Azure AD SSO | 인프라 의존. 별도 PDCA 피처로 관리 |
| SSE → EventSource 전환 | Supabase Realtime + 폴링으로 기능 동일 |
| 실시간 공동 편집 (Yjs) | v2 이후 로드맵 |

## 6. 성공 기준

| 지표 | 현재 | 목표 |
|------|:----:|:----:|
| 갭 분석 종합 | 94% | 98%+ |
| 컴포넌트 충실도 | 97% | 99% |
| 기능 충실도 | 95% | 98% |
| UI 인프라 | 75% | 85% |
| TypeScript 빌드 에러 | 0 | 0 유지 |
