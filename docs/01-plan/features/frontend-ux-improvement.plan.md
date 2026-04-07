# Frontend UX 개선 계획서

> 제안작업 담당자가 제안서를 작성하는 데 편리한 플랫폼으로 개선하기 위한 UX 리뷰 기반 4단계 로드맵

## 1. 배경 및 목적

### 현재 상태
- **34개 페이지, 31개 컴포넌트** — 제안서 라이프사이클 전체를 커버하는 풀스택 플랫폼
- **다크 테마 전용** (#111111 배경, #3ecf8e 액센트) — 일관된 시각 디자인
- **3컬럼 에디터** (TOC+Compliance | Tiptap 본문 | AI 패널) — 핵심 강점
- **AI 4가지 모드** (개선/축약/확장/격식화) + 섹션 재생성 — 콘텐츠 생성 지원
- **PhaseGraph 5단계** + HITL 리뷰 게이트 — 워크플로 가시성

### 문제점 (UX 리뷰 결과)
| 등급 | 문제 | 영향 |
|------|------|------|
| **Critical** | 모바일/태블릿 미지원 (3컬럼 고정) | 출장/회의 중 제안서 검토 불가 |
| **Critical** | 라이트 모드 없음 | 밝은 환경 가독성 저하, 인쇄 문제 |
| **Critical** | 비저장 경고 없음 | 작성 중 내용 유실 위험 |
| **High** | AI 제안 적용이 복사-붙여넣기 (diff/merge UI 없음) | 수정 반영 번거로움 |
| **High** | 브레드크럼 없음 | 중첩 경로 방향감각 상실 |
| **High** | 키보드 단축키 미노출 | 파워유저 생산성 저하 |
| **High** | 버전 비교 세로 전용 (우측 패널 폭 제약) | 변경사항 비교 어려움 |
| **High** | 댓글 서식 미지원 | 피드백 구조화 어려움 |
| **Medium** | AI 응답 대기 시간 표시 없음 | 사용자 불안감 |
| **Medium** | 카드/모달 패턴 비통일 | 유지보수 비용 |
| **Medium** | 산출물 뷰어 300px 잘림 | 대용량 문서 확인 불편 |
| **Medium** | 사이드바 KB 서브메뉴 상태 미저장 | 매번 수동 펼침 |
| **Medium** | SVG 아이콘 alt text 누락 | 접근성 미준수 |

### 핵심 원칙
- **백엔드 수정 최소화** — 프론트엔드 UX 개선에 집중
- **기존 기능 보존** — 현재 잘 작동하는 3컬럼 에디터, PhaseGraph 등은 그대로 유지
- **제안 담당자 일일 워크플로 기준** — 실무 빈도 높은 개선 우선

## 2. 구현 범위 (4개 Phase)

### Phase 1 — 안정성 (즉시, ~2일)

작성 중 데이터 유실 방지 + 기본 사용성 보강. 가장 시급하고 영향 큰 항목.

#### 1-1. 비저장 경고 (C3)
**문제**: 에디터에서 수정 후 페이지 이탈 시 경고 없음 → 내용 유실
**구현**:
- `beforeunload` 이벤트 핸들러 추가 (ProposalEditor.tsx)
- Next.js `useRouter` 감지로 클라이언트 네비게이션 시에도 확인 다이얼로그
- `isDirty` 상태 관리: Tiptap `onUpdate` → true, 저장 완료 → false
**수정 파일**: `components/ProposalEditor.tsx`, `components/ProposalEditView.tsx`

#### 1-2. 키보드 단축키 (H3)
**문제**: Cmd+Enter(AI 제출)만 숨겨진 상태, 다른 단축키 없음
**구현**:
- 전역 단축키 등록: `Ctrl+S` (수동 저장), `Ctrl+Z/Y` (Undo/Redo — Tiptap 기본 노출)
- `Escape` (AI 패널 닫기), `Ctrl+/` (단축키 가이드 토글)
- 단축키 가이드 오버레이 컴포넌트 (Ctrl+/ 또는 ? 키)
**신규 파일**: `components/KeyboardShortcutsGuide.tsx`
**수정 파일**: `components/ProposalEditView.tsx`, `components/EditorAiPanel.tsx`

#### 1-3. AI 응답 대기 표시 (M1)
**문제**: AI 요청 후 "로딩 중..." 외 정보 없음
**구현**:
- 경과 시간 카운터 (0:00 → 0:05 → …) + 예상 시간 텍스트 ("보통 5~15초")
- Skeleton UI로 응답 영역 사전 확보
- EditorAiPanel의 AI assist/regenerate 요청에 적용
**수정 파일**: `components/EditorAiPanel.tsx`

### Phase 2 — 생산성 (단기, ~3일)

제안서 작성 효율 직접 향상. 담당자의 반복 작업 감소.

#### 2-1. AI 제안 인라인 Diff (H1)
**문제**: AI 제안을 복사-붙여넣기로만 반영 가능
**구현**:
- AI 응답 시 현재 텍스트 vs 제안 텍스트 diff 계산 (diff-match-patch 라이브러리)
- 인라인 diff 뷰: 삭제(빨간 취소선) / 추가(녹색 하이라이트)
- "수락" / "거부" / "부분 수락" 버튼
- 수락 시 Tiptap 에디터에 자동 반영
**신규 의존성**: `diff-match-patch`
**수정 파일**: `components/EditorAiPanel.tsx`
**신규 파일**: `components/AiSuggestionDiff.tsx`

#### 2-2. 브레드크럼 네비게이션 (H2)
**문제**: `/proposals/abc123/edit` 같은 깊은 경로에서 현재 위치 파악 어려움
**구현**:
- 경로 기반 자동 브레드크럼 (Home > 제안 프로젝트 > [프로젝트명] > 편집)
- 각 세그먼트 클릭 시 해당 페이지 이동
- 프로젝트 상세 이후 경로에만 표시 (대시보드/목록은 불필요)
**신규 파일**: `components/Breadcrumb.tsx`
**수정 파일**: `app/proposals/[id]/layout.tsx`

#### 2-3. 산출물 뷰어 개선 (M3)
**문제**: GenericArtifact `<pre>` max-h-300px 잘림
**구현**:
- 접이식 (기본 축소 300px + "더 보기" 토글)
- "전체 보기" 클릭 시 전체화면 모달
- JSON 데이터는 포맷팅 + 구문 강조
**수정 파일**: `components/StepArtifactViewer.tsx`

#### 2-4. 사이드바 KB 메뉴 상태 유지 (M4)
**문제**: KB 서브메뉴 열림/닫힘 상태가 새로고침 시 초기화
**구현**:
- `localStorage`에 `sidebar-kb-expanded` 키로 상태 저장
- AppSidebar 마운트 시 읽기, 토글 시 쓰기
**수정 파일**: `components/AppSidebar.tsx`

### Phase 3 — 확장성 (중기, ~5일)

다양한 환경(모바일, 밝은 환경)에서의 사용성 확보.

#### 3-1. 반응형 레이아웃 (C1)
**문제**: 3컬럼 고정 → 태블릿/모바일에서 사용 불가
**구현**:
- **에디터 (`ProposalEditView`)**:
  - ≥1280px: 3컬럼 (현재)
  - 768~1279px: 2컬럼 (TOC 접힘 → 햄버거, 본문+AI 패널)
  - <768px: 1컬럼 (본문 전체 + 하단 탭으로 TOC/AI 전환)
- **상세 (`proposals/[id]/page.tsx`)**:
  - ≥1024px: 센터+우측 2패널
  - <1024px: 탭 전환 (워크플로 | 산출물 | 댓글)
- **사이드바**: <768px 시 오버레이 드로어로 전환
- Tailwind `md:`, `lg:`, `xl:` 브레이크포인트 활용
**수정 파일**: `components/ProposalEditView.tsx`, `components/AppSidebar.tsx`, `app/proposals/[id]/page.tsx`, `components/DetailCenterPanel.tsx`, `components/DetailRightPanel.tsx`

#### 3-2. 라이트/다크 모드 토글 (C2)
**문제**: 다크 전용 → 밝은 환경·인쇄 시 불편
**구현**:
- CSS 변수 기반 테마 분리 (globals.css에 `:root` + `.dark` 클래스)
- 라이트 테마 색상 정의 (white 배경, gray-900 텍스트, teal-600 액센트)
- 토글 버튼: 사이드바 하단 (🌙/☀️ 아이콘)
- `localStorage` + `prefers-color-scheme` 미디어쿼리 연동
- Tiptap 에디터 prose 클래스 테마 대응
**수정 파일**: `app/globals.css`, `app/layout.tsx`, `components/AppSidebar.tsx`
**신규 파일**: `components/ThemeToggle.tsx`

#### 3-3. 버전 비교 전체화면 모드 (H4)
**문제**: 우측 패널(~400px) 안에서 Side-by-side 비교 불가능
**구현**:
- "전체화면 비교" 버튼 → 오버레이 모달 (90vw × 85vh)
- 좌/우 분할: 이전 버전 | 현재 버전 (diff 하이라이트)
- 버전 드롭다운 선택기 2개 (A vs B)
- diff-match-patch로 변경 부분 색상 표시
**신규 파일**: `components/VersionCompareModal.tsx`
**수정 파일**: `components/DetailRightPanel.tsx`

### Phase 4 — 협업 (장기, ~3일)

팀 협업 품질 향상.

#### 4-1. 댓글 마크다운 지원 (H5)
**문제**: 순수 텍스트만 지원 → 구조화된 피드백 불가
**구현**:
- 댓글 입력에 간이 마크다운 (볼드, 리스트, 코드블록) 지원
- 렌더링: `react-markdown` (또는 간단한 정규식 파서)
- 미리보기 탭 (작성 | 미리보기)
**수정 파일**: `components/DetailRightPanel.tsx` (댓글 탭)
**신규 의존성**: `react-markdown` (이미 설치되어 있다면 활용)

#### 4-2. 접근성 개선 (M5)
**문제**: SVG 아이콘 alt text 누락, 색상 전용 상태 표시
**구현**:
- 모든 아이콘 버튼에 `aria-label` 추가
- 상태 배지에 텍스트 레이블 병기 (색상 + 텍스트)
- PhaseGraph 노드에 tooltip 강화 (현재 상태 텍스트)
- focus 순서 검증 (Tab 키 네비게이션)
**수정 파일**: `components/AppSidebar.tsx`, `components/PhaseGraph.tsx`, `components/NotificationBell.tsx`, `components/WorkflowPanel.tsx`

#### 4-3. 디자인 시스템 정리 (M2)
**문제**: 카드/모달 스타일이 컴포넌트마다 inline class 중복
**구현**:
- 공통 `Card`, `Modal`, `Badge`, `StatusDot` 컴포넌트 추출
- 기존 GoNoGoPanel, ReviewPanel, RfpSearchPanel 등에서 공통 패턴 사용
- Tailwind `@apply` 또는 cva(class-variance-authority) 활용
**신규 파일**: `components/ui/Card.tsx`, `components/ui/Modal.tsx`, `components/ui/Badge.tsx`
**수정 파일**: 카드/모달 사용 컴포넌트 전체 (점진적 교체)

## 3. 영향 범위

### 수정 파일 요약
| Phase | 신규 파일 | 수정 파일 | 신규 의존성 |
|-------|-----------|-----------|-------------|
| Phase 1 | 1 (KeyboardShortcutsGuide) | 3 | — |
| Phase 2 | 2 (AiSuggestionDiff, Breadcrumb) | 4 | diff-match-patch |
| Phase 3 | 2 (ThemeToggle, VersionCompareModal) | 6 | — |
| Phase 4 | 3 (Card, Modal, Badge) | 5+ | react-markdown (optional) |
| **합계** | **8** | **~18** | **1~2** |

### 백엔드 변경
- **없음** — 모든 개선이 프론트엔드 전용

### 리스크
| 리스크 | 완화 |
|--------|------|
| 반응형 전환 시 기존 레이아웃 깨짐 | Tailwind 브레이크포인트만 추가, 기존 클래스 유지 |
| 라이트 모드 색상 조합 미검증 | globals.css CSS 변수 분리 → 한 곳에서 조정 가능 |
| diff-match-patch 번들 크기 | ~50KB gzip, 에디터 페이지 lazy load |
| 디자인 시스템 교체 범위 확대 | Phase 4에서 점진적 교체, 한 번에 전체 교체하지 않음 |

## 4. Phase별 우선순위 근거

```
Phase 1 (즉시) — 데이터 유실 방지 + 기본 사용성
  ↑ 제안서 작성 중 내용 유실 = 실무자 신뢰 상실

Phase 2 (단기) — 작성 효율 직접 향상
  ↑ AI 협업 핵심 기능(diff), 네비게이션 개선

Phase 3 (중기) — 환경 확장
  ↑ 모바일 검토, 밝은 환경, 버전 비교 — 사용 빈도는 낮지만 요청 시 필수

Phase 4 (장기) — 코드 품질 + 접근성
  ↑ 장기 유지보수성, 점진적 적용 가능
```

## 5. 성공 기준

| 항목 | 현재 | 목표 |
|------|------|------|
| UX 종합 점수 | 8.1/10 | 9.0+/10 |
| 접근성/반응형 | 6/10 | 8/10 |
| 편집 생산성 | AI 복붙 방식 | 인라인 수락/거부 |
| 데이터 안전성 | 비저장 경고 없음 | 이탈 시 100% 경고 |
| 환경 지원 | 데스크톱 다크 전용 | 데스크톱+태블릿, 라이트/다크 |

## 6. 의존 관계

```
Phase 1 (독립, 즉시 시작 가능)
  ↓
Phase 2 (Phase 1 완료 후 — diff 라이브러리 Phase 3에서도 재사용)
  ↓
Phase 3 (Phase 2의 Breadcrumb 반응형 포함)
  ↓
Phase 4 (Phase 3의 반응형 컴포넌트에 디자인 시스템 적용)
```

## 7. 범위 외 (Out of Scope)

- **실시간 협업 커서** (Yjs/CRDT) — 아키텍처 변경 필요, 별도 프로젝트
- **워크플로 실시간 가시성** — 기존 `workflow-ux.plan.md`에서 별도 관리
- **3-Stream 병행 업무 UX** — Phase 6에서 이미 구현 완료
- **Azure AD SSO UI** — 인프라 의존, 별도 관리
