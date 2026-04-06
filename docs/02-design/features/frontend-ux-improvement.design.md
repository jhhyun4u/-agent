# Frontend UX 개선 설계서

> Plan: `docs/01-plan/features/frontend-ux-improvement.plan.md` 기반 상세 설계

## 목차
1. [Phase 1 — 안정성](#1-phase-1--안정성)
2. [Phase 2 — 생산성](#2-phase-2--생산성)
3. [Phase 3 — 확장성](#3-phase-3--확장성)
4. [Phase 4 — 협업](#4-phase-4--협업)
5. [신규 의존성](#5-신규-의존성)
6. [구현 순서](#6-구현-순서)

---

## 1. Phase 1 — 안정성

### 1-1. 비저장 경고 (C3)

**현재 코드**: `ProposalEditView.tsx` — `handleContentUpdate`에서 3초 debounce 자동저장만 존재. `isDirty` 상태 없음.

**수정 파일**: `components/ProposalEditView.tsx`, `components/ProposalEditor.tsx`

#### 설계

```typescript
// ProposalEditView.tsx에 추가할 상태
const [isDirty, setIsDirty] = useState(false);

// ProposalEditor onUpdate 콜백 래핑
function handleEditorUpdate(html: string) {
  setIsDirty(true);
  handleContentUpdate(html); // 기존 자동저장 (3초 debounce)
}

// 자동저장 완료 시 isDirty = false
// handleContentUpdate 내 setSaving(false) 직후에 setIsDirty(false) 추가
```

**beforeunload 이벤트**:
```typescript
// ProposalEditView.tsx useEffect 추가
useEffect(() => {
  function handleBeforeUnload(e: BeforeUnloadEvent) {
    if (isDirty) {
      e.preventDefault();
      e.returnValue = "";
    }
  }
  window.addEventListener("beforeunload", handleBeforeUnload);
  return () => window.removeEventListener("beforeunload", handleBeforeUnload);
}, [isDirty]);
```

**Next.js 라우터 네비게이션 가드**:
```typescript
// ProposalEditView.tsx — 헤더의 "← 돌아가기" 링크를 onClick 핸들러로 교체
function handleBack() {
  if (isDirty && !confirm("저장하지 않은 변경사항이 있습니다. 페이지를 떠나시겠습니까?")) {
    return;
  }
  if (standalone) window.close();
  else router.push(`/proposals/${id}`);
}
```

**상태바 변경** (footer):
```
기존: "미저장" | "저장 중..." | "마지막 저장: HH:MM"
변경: "수정됨 (저장 대기)" | "저장 중..." | "마지막 저장: HH:MM"
       ↑ isDirty && !saving 일 때 amber 색상 표시
```

**변경 범위**:
- `ProposalEditView.tsx`: isDirty 상태 + beforeunload + handleBack + footer 텍스트 변경
- `ProposalEditor.tsx`: 변경 없음 (onUpdate 콜백 시그니처 동일)

---

### 1-2. 키보드 단축키 (H3)

**현재 코드**: `EditorAiPanel.tsx:252-255` — `Cmd+Enter` AI 제출만 존재 (onKeyDown 직접 바인딩)

**신규 파일**: `components/KeyboardShortcutsGuide.tsx`
**수정 파일**: `components/ProposalEditView.tsx`

#### KeyboardShortcutsGuide 컴포넌트

```typescript
interface KeyboardShortcutsGuideProps {
  open: boolean;
  onClose: () => void;
}

// 렌더링: 오버레이 모달 (z-[var(--z-modal)])
// 단축키 목록 테이블:
const SHORTCUTS = [
  { keys: "Ctrl+S", desc: "수동 저장" },
  { keys: "Ctrl+Z", desc: "실행 취소 (Tiptap 내장)" },
  { keys: "Ctrl+Y", desc: "다시 실행 (Tiptap 내장)" },
  { keys: "Ctrl+Enter", desc: "AI 제안 전송" },
  { keys: "Escape", desc: "AI 패널 결과 닫기" },
  { keys: "Ctrl+/", desc: "단축키 가이드 열기/닫기" },
];
```

**스타일**:
```
- 배경: bg-[#0f0f0f]/80 backdrop-blur (오버레이)
- 모달: bg-[#1c1c1c] border border-[#262626] rounded-xl max-w-sm mx-auto mt-24 p-4
- 키 배지: inline-block px-1.5 py-0.5 bg-[#262626] rounded text-[10px] font-mono text-[#ededed]
- 설명: text-xs text-[#8c8c8c]
```

#### ProposalEditView 전역 단축키

```typescript
// ProposalEditView.tsx useEffect 추가
const [shortcutsOpen, setShortcutsOpen] = useState(false);

useEffect(() => {
  function handleKeyDown(e: KeyboardEvent) {
    // Ctrl+S: 즉시 저장 (debounce 무시)
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault();
      // content를 즉시 저장 (flushSave)
      if (isDirty) handleContentUpdate(content);
    }
    // Ctrl+/: 단축키 가이드 토글
    if ((e.ctrlKey || e.metaKey) && e.key === "/") {
      e.preventDefault();
      setShortcutsOpen(prev => !prev);
    }
    // Escape: AI 결과 닫기 (shortcutsOpen이면 가이드 닫기)
    if (e.key === "Escape") {
      if (shortcutsOpen) setShortcutsOpen(false);
    }
  }
  window.addEventListener("keydown", handleKeyDown);
  return () => window.removeEventListener("keydown", handleKeyDown);
}, [isDirty, content, shortcutsOpen]);
```

**Ctrl+S 즉시 저장 구현**: `ProposalEditor.tsx`에서 `flushSave` ref 노출 필요.
- 접근 방식: `ProposalEditor`에 `ref`를 `forwardRef`로 전달하는 대신, `onUpdate`가 debounce 없이 직접 호출되는 `onFlushSave?: () => void` prop 추가
- 실제로는 `ProposalEditView`가 현재 content를 가지고 있으므로, Ctrl+S 시 `handleContentUpdate(content)`를 debounce 무시하고 즉시 호출

```typescript
// handleContentUpdate를 두 가지로 분리
const flushSave = useCallback(async (html: string) => {
  setSaving(true);
  try {
    await api.artifacts.save(id, "proposal", html);
    setLastSaved(new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }));
    setIsDirty(false);
    channelRef.current?.postMessage({ type: "saved" });
  } catch { /* silent */ }
  finally { setSaving(false); }
}, [id]);
```

---

### 1-3. AI 응답 대기 표시 (M1)

**현재 코드**: `EditorAiPanel.tsx:266` — `aiLoading ? "처리 중..." : "AI 제안"` 텍스트만 표시

**수정 파일**: `components/EditorAiPanel.tsx`

#### 설계

```typescript
// AI 요청 시작 시 타이머 시작
const [aiElapsed, setAiElapsed] = useState(0);
const aiTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

// handleAiAssist 수정
const handleAiAssist = useCallback(async () => {
  if (!aiQuery.trim()) return;
  setAiLoading(true);
  setAiElapsed(0);
  aiTimerRef.current = setInterval(() => setAiElapsed(prev => prev + 1), 1000);
  // ... 기존 try/catch ...
  // finally 블록에서:
  if (aiTimerRef.current) clearInterval(aiTimerRef.current);
  setAiLoading(false);
}, [...]);

// handleRegenerate에도 동일 패턴 적용
```

**UI 변경** (aiLoading === true 일 때):
```tsx
{aiLoading && (
  <div className="flex items-center gap-2 py-2">
    <div className="w-3 h-3 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin" />
    <span className="text-[10px] text-[#8c8c8c]">
      AI 분석 중... {aiElapsed}초 <span className="text-[#5c5c5c]">(보통 5~15초)</span>
    </span>
  </div>
)}
```

**버튼 텍스트 변경**:
```
기존: "처리 중..."
변경: "분석 중 ({aiElapsed}s)"
```

---

## 2. Phase 2 — 생산성

### 2-1. AI 제안 인라인 Diff (H1)

**현재 코드**: `EditorAiPanel.tsx:287-293` — "제안 적용" 버튼 클릭 시 `onApplySuggestion(aiResult.suggestion)` → 전체 교체

**신규 파일**: `components/AiSuggestionDiff.tsx`
**신규 의존성**: `diff-match-patch` (npm)
**수정 파일**: `components/EditorAiPanel.tsx`

#### AiSuggestionDiff 컴포넌트

```typescript
interface AiSuggestionDiffProps {
  original: string;      // 현재 에디터 텍스트 (또는 선택 영역)
  suggestion: string;    // AI 제안 텍스트
  onAccept: () => void;  // 전체 수락
  onReject: () => void;  // 거부 (원본 유지)
}
```

**diff 계산**:
```typescript
import DiffMatchPatch from "diff-match-patch";

const dmp = new DiffMatchPatch();
const diffs = dmp.diff_main(original, suggestion);
dmp.diff_cleanupSemantic(diffs);
```

**렌더링**:
```tsx
// diff 결과를 인라인 표시
{diffs.map(([op, text], i) => (
  <span key={i} className={
    op === 1 ? "bg-green-500/20 text-green-300" :     // 추가
    op === -1 ? "bg-red-500/20 text-red-400 line-through" :  // 삭제
    "text-[#8c8c8c]"                                          // 동일
  }>
    {text}
  </span>
))}
```

**스타일**:
```
- 컨테이너: bg-[#111111] border border-[#3ecf8e]/20 rounded-lg p-3
- 버튼 행: flex gap-2 mt-2
  - 수락: bg-[#3ecf8e] text-[#0f0f0f] px-3 py-1 text-[10px] rounded
  - 거부: border border-[#262626] text-[#8c8c8c] px-3 py-1 text-[10px] rounded
- max-h-40 overflow-y-auto (결과가 긴 경우 스크롤)
```

#### EditorAiPanel 수정

```typescript
// 기존 aiResult 표시 영역 교체
// Before:
//   <div className="text-[10px]...max-h-24...">{aiResult.suggestion}</div>
//   <button onClick={() => onApplySuggestion(aiResult.suggestion)}>제안 적용</button>

// After:
{aiResult && (
  <AiSuggestionDiff
    original={currentSectionText}  // 현재 활성 섹션 텍스트
    suggestion={aiResult.suggestion}
    onAccept={() => onApplySuggestion?.(aiResult.suggestion)}
    onReject={() => setAiResult(null)}
  />
)}
```

**currentSectionText 전달**: `EditorAiPanel`에 `currentContent?: string` prop 추가.
`ProposalEditView`에서 `content` 상태를 전달:
```tsx
<EditorAiPanel
  ...
  currentContent={content}
/>
```

---

### 2-2. 브레드크럼 네비게이션 (H2)

**신규 파일**: `components/Breadcrumb.tsx`
**수정 파일**: `components/ProposalEditView.tsx` (에디터 헤더에 통합)

#### Breadcrumb 컴포넌트

```typescript
interface BreadcrumbItem {
  label: string;
  href?: string;  // 없으면 현재 페이지 (비링크)
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}
```

**렌더링**:
```tsx
<nav className="flex items-center gap-1 text-[10px]" aria-label="breadcrumb">
  {items.map((item, i) => (
    <Fragment key={i}>
      {i > 0 && <span className="text-[#5c5c5c]">/</span>}
      {item.href ? (
        <Link href={item.href} className="text-[#8c8c8c] hover:text-[#ededed] transition-colors">
          {item.label}
        </Link>
      ) : (
        <span className="text-[#ededed]">{item.label}</span>
      )}
    </Fragment>
  ))}
</nav>
```

#### 사용 위치

**ProposalEditView 헤더**에 기존 "← 돌아가기" 대신 배치:
```tsx
<Breadcrumb items={[
  { label: "제안 프로젝트", href: "/proposals" },
  { label: rfpTitle || "프로젝트", href: `/proposals/${id}` },
  { label: "편집" },  // 현재 페이지 — 링크 없음
]} />
```

`ProposalEditView`에 `rfpTitle` prop 추가 필요 → 호출측(`app/proposals/[id]/edit/page.tsx`)에서 전달.

---

### 2-3. 산출물 뷰어 개선 (M3)

**현재 코드**: `StepArtifactViewer.tsx:499-520` — `GenericArtifact` — `max-h-[300px]` + "전체 보기" 토글 (이미 부분 구현됨)

**수정 파일**: `components/StepArtifactViewer.tsx`

#### 설계 (GenericArtifact 개선)

현재 이미 `expanded` 토글이 있음. 추가할 것:

1. **전체화면 모달** 버튼 추가:
```tsx
const [fullscreen, setFullscreen] = useState(false);

// 기존 "전체 보기" 옆에 "전체 화면" 버튼 추가
{json.length > 500 && (
  <div className="flex gap-2 mt-1">
    <button onClick={() => setExpanded(!expanded)} className="text-[10px] text-[#3ecf8e] hover:underline">
      {expanded ? "접기" : "펼치기"}
    </button>
    <button onClick={() => setFullscreen(true)} className="text-[10px] text-[#8c8c8c] hover:text-[#ededed]">
      전체 화면
    </button>
  </div>
)}

// 전체화면 모달
{fullscreen && (
  <div className="fixed inset-0 z-[var(--z-modal)] bg-[#0f0f0f]/90 flex items-center justify-center p-8" onClick={() => setFullscreen(false)}>
    <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl w-full max-w-4xl max-h-[85vh] overflow-auto p-6" onClick={e => e.stopPropagation()}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-[#ededed]">산출물 전체 보기</h3>
        <button onClick={() => setFullscreen(false)} className="text-[#8c8c8c] hover:text-[#ededed]">✕</button>
      </div>
      <pre className="text-xs text-[#8c8c8c] whitespace-pre-wrap break-words font-mono leading-relaxed">
        {json}
      </pre>
    </div>
  </div>
)}
```

2. **JSON 구문 강조** (간단한 정규식 기반):
```typescript
function highlightJson(json: string): React.ReactNode {
  // 키: 녹색, 문자열 값: 주황, 숫자: 파랑, boolean: 보라
  return json.split(/("(?:[^"\\]|\\.)*")/g).map((part, i) => {
    if (part.startsWith('"') && part.endsWith('"')) {
      // 키 또는 문자열 값 구분: 다음 문자가 : 이면 키
      return <span key={i} className="text-[#3ecf8e]">{part}</span>;
    }
    // 숫자, boolean 등은 기본 색상 유지
    return <span key={i}>{part}</span>;
  });
}
```

---

### 2-4. 사이드바 KB 메뉴 상태 유지 (M4)

**현재 코드**: `AppSidebar.tsx:81` — `const [kbOpen, setKbOpen] = useState(false);` → 매번 false로 초기화

**수정 파일**: `components/AppSidebar.tsx`

#### 설계

```typescript
// 초기값: localStorage에서 읽기
const [kbOpen, setKbOpen] = useState(() => {
  if (typeof window === "undefined") return false;
  return localStorage.getItem("sidebar-kb-expanded") === "true";
});

// 토글 시 저장
function toggleKb() {
  setKbOpen(prev => {
    const next = !prev;
    localStorage.setItem("sidebar-kb-expanded", String(next));
    return next;
  });
}

// 기존 useEffect 수정 — KB 경로일 때만 열기 (닫기는 안 함)
useEffect(() => {
  if (pathname.startsWith("/kb")) {
    setKbOpen(true);
    localStorage.setItem("sidebar-kb-expanded", "true");
  }
}, [pathname]);

// 버튼 onClick 교체
// 기존: onClick={() => collapsed ? router.push("/kb/search") : setKbOpen(prev => !prev)}
// 변경: onClick={() => collapsed ? router.push("/kb/search") : toggleKb()}
```

---

## 3. Phase 3 — 확장성

### 3-1. 반응형 레이아웃 (C1)

**수정 파일**: `components/ProposalEditView.tsx`, `components/AppSidebar.tsx`, `app/globals.css`

#### 3-1-A. 에디터 반응형 (`ProposalEditView.tsx`)

**현재**: `<div className="flex-1 flex overflow-hidden">` 안에 고정 3컬럼 (w-56 | flex-1 | w-56)

**변경 전략**: Tailwind 브레이크포인트 + 모바일 탭 전환

```tsx
// 모바일 탭 상태
const [mobilePanel, setMobilePanel] = useState<"toc" | "editor" | "ai">("editor");

// 3단 레이아웃 → 반응형
<div className="flex-1 flex overflow-hidden">
  {/* 좌측: TOC — lg 이상에서만 표시 */}
  <aside className="hidden lg:block w-56 bg-[#1c1c1c] border-r border-[#262626] shrink-0 overflow-hidden">
    <EditorTocPanel ... />
  </aside>

  {/* 중앙: 에디터 — 항상 표시 (모바일에서는 탭 전환) */}
  <main className="flex-1 overflow-hidden">
    {/* 모바일 탭 바 — lg 미만에서만 표시 */}
    <div className="lg:hidden flex border-b border-[#262626] bg-[#1c1c1c]">
      {(["toc", "editor", "ai"] as const).map(tab => (
        <button key={tab} onClick={() => setMobilePanel(tab)}
          className={`flex-1 py-2 text-[10px] font-medium ${
            mobilePanel === tab ? "text-[#3ecf8e] border-b-2 border-[#3ecf8e]" : "text-[#8c8c8c]"
          }`}>
          {tab === "toc" ? "목차" : tab === "editor" ? "편집" : "AI"}
        </button>
      ))}
    </div>

    {/* 모바일: 선택된 패널만 표시 */}
    <div className="lg:hidden h-full">
      {mobilePanel === "toc" && <EditorTocPanel ... />}
      {mobilePanel === "editor" && <ProposalEditor ... />}
      {mobilePanel === "ai" && <EditorAiPanel ... />}
    </div>

    {/* 데스크톱: 에디터만 */}
    <div className="hidden lg:block h-full">
      <ProposalEditor ... />
    </div>
  </main>

  {/* 우측: AI — lg 이상에서만 표시 */}
  <aside className="hidden lg:block w-56 bg-[#1c1c1c] border-l border-[#262626] shrink-0 overflow-hidden">
    <EditorAiPanel ... />
  </aside>
</div>
```

**브레이크포인트**:
- `lg` (1024px+): 3컬럼 (현재 동일)
- `<1024px`: 모바일 탭 전환 (목차 | 편집 | AI)

#### 3-1-B. 사이드바 반응형 (`AppSidebar.tsx`)

**현재**: `<aside className={collapsed ? "w-14" : "w-52"}>` — 항상 표시

**변경**:
```tsx
// 모바일 오버레이 상태
const [mobileOpen, setMobileOpen] = useState(false);

// lg 이상: 기존 사이드바
// lg 미만: 햄버거 버튼 + 오버레이 드로어
return (
  <>
    {/* 모바일 햄버거 (lg 미만) */}
    <button
      onClick={() => setMobileOpen(true)}
      className="lg:hidden fixed top-3 left-3 z-[var(--z-overlay)] p-2 bg-[#1c1c1c] border border-[#262626] rounded-lg"
      aria-label="메뉴 열기"
    >
      <SvgIcon d="M3 12h18M3 6h18M3 18h18" />
    </button>

    {/* 모바일 오버레이 */}
    {mobileOpen && (
      <div className="lg:hidden fixed inset-0 z-[var(--z-overlay)] bg-[#0f0f0f]/60" onClick={() => setMobileOpen(false)}>
        <aside className="w-64 h-full bg-[#111111] border-r border-[#262626]" onClick={e => e.stopPropagation()}>
          {/* 기존 사이드바 내용 (collapsed=false 고정) */}
          ...
        </aside>
      </div>
    )}

    {/* 데스크톱 사이드바 (lg 이상) */}
    <aside className={`hidden lg:flex ${collapsed ? "w-14" : "w-52"} shrink-0 flex-col border-r border-[#262626] bg-[#111111] transition-all duration-200`}>
      {/* 기존 내용 그대로 */}
    </aside>
  </>
);
```

---

### 3-2. 라이트/다크 모드 토글 (C2)

**신규 파일**: `components/ThemeToggle.tsx`
**수정 파일**: `app/globals.css`, `app/layout.tsx`, `components/AppSidebar.tsx`

#### CSS 변수 분리 (`globals.css`)

```css
/* 기존 :root는 다크 모드 기본값으로 유지 */
:root {
  --bg: #0f0f0f;
  --surface: #111111;
  --card: #1c1c1c;
  --border: #262626;
  --text: #ededed;
  --muted: #8c8c8c;
  --accent: #3ecf8e;
  color-scheme: dark;
}

/* 라이트 모드 */
:root.light {
  --bg: #ffffff;
  --surface: #f8f9fa;
  --card: #ffffff;
  --border: #e2e8f0;
  --text: #1a202c;
  --muted: #718096;
  --accent: #2b9a6e;
  color-scheme: light;
}

/* 라이트 모드 보정 */
:root.light body { background-color: var(--bg); color: var(--text); }
:root.light ::-webkit-scrollbar-track { background: var(--surface); }
:root.light ::-webkit-scrollbar-thumb { background: var(--border); }
:root.light ::placeholder { color: #a0aec0 !important; }
```

**중요**: 기존 하드코딩된 색상값(`#0f0f0f`, `#111111`, `#ededed` 등)은 이미 CSS 변수와 동일하므로, **점진적으로** `var(--bg)` 등으로 교체. Phase 3에서는 globals.css + layout.tsx + ThemeToggle + AppSidebar만 수정하고, 나머지 컴포넌트의 하드코딩은 Phase 4 디자인 시스템에서 일괄 교체.

#### layout.tsx 수정

```tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <head>
        {/* 테마 깜빡임 방지 — localStorage 선읽기 */}
        <script dangerouslySetInnerHTML={{ __html: `
          try {
            const t = localStorage.getItem('theme');
            if (t === 'light') document.documentElement.classList.add('light');
            else if (!t && window.matchMedia('(prefers-color-scheme: light)').matches) {
              document.documentElement.classList.add('light');
            }
          } catch {}
        `}} />
      </head>
      <body className="min-h-screen bg-[var(--bg)] text-[var(--text)] antialiased">
        {children}
      </body>
    </html>
  );
}
```

#### ThemeToggle 컴포넌트

```typescript
"use client";
export default function ThemeToggle({ collapsed }: { collapsed?: boolean }) {
  const [isLight, setIsLight] = useState(false);

  useEffect(() => {
    setIsLight(document.documentElement.classList.contains("light"));
  }, []);

  function toggle() {
    const next = !isLight;
    setIsLight(next);
    if (next) {
      document.documentElement.classList.add("light");
      localStorage.setItem("theme", "light");
    } else {
      document.documentElement.classList.remove("light");
      localStorage.setItem("theme", "dark");
    }
  }

  return (
    <button onClick={toggle} className="flex items-center gap-2 px-3 py-2 rounded-md text-sm text-[#8c8c8c] hover:bg-[var(--card)] hover:text-[var(--text)] transition-colors" title={isLight ? "다크 모드" : "라이트 모드"}>
      <span className="text-base">{isLight ? "🌙" : "☀️"}</span>
      {!collapsed && <span>{isLight ? "다크 모드" : "라이트 모드"}</span>}
    </button>
  );
}
```

**AppSidebar 통합**: 로그아웃 버튼 위에 ThemeToggle 배치.

---

### 3-3. 버전 비교 전체화면 모드 (H4)

**현재 코드**: `DetailRightPanel.tsx:122-138` — Compare 탭에서 세로 비교 (우측 패널 ~400px 내)

**신규 파일**: `components/VersionCompareModal.tsx`
**신규 의존성**: `diff-match-patch` (Phase 2에서 이미 추가)
**수정 파일**: `components/DetailRightPanel.tsx`

#### VersionCompareModal 컴포넌트

```typescript
interface VersionCompareModalProps {
  open: boolean;
  onClose: () => void;
  proposalId: string;
  versions: ProposalSummary[];
  currentVersionLabel: string;
}
```

**렌더링**:
```
┌──────────────────────────────────────────────────────┐
│  버전 비교                          [버전A ▾] [버전B ▾] ✕ │
├─────────────────────────┬────────────────────────────┤
│  버전 A (이전)           │  버전 B (현재)              │
│                         │                            │
│  diff 하이라이트된 텍스트  │  diff 하이라이트된 텍스트    │
│                         │                            │
└─────────────────────────┴────────────────────────────┘
```

**스타일**:
```
- 오버레이: fixed inset-0 z-[var(--z-modal)] bg-[#0f0f0f]/80
- 모달: bg-[#1c1c1c] border border-[#262626] rounded-xl w-[90vw] h-[85vh] mx-auto mt-[7.5vh]
- 좌/우 분할: flex gap-0 (border-r border-[#262626]로 구분)
- 삭제 텍스트: bg-red-500/10 text-red-400
- 추가 텍스트: bg-green-500/10 text-green-300
```

#### DetailRightPanel 수정

Compare 탭에 "전체화면 비교" 버튼 추가:
```tsx
const [compareModalOpen, setCompareModalOpen] = useState(false);

// Compare 탭 영역에 추가:
<button onClick={() => setCompareModalOpen(true)} className="text-[10px] text-[#3ecf8e] hover:underline">
  전체화면 비교
</button>

{compareModalOpen && (
  <VersionCompareModal
    open={compareModalOpen}
    onClose={() => setCompareModalOpen(false)}
    proposalId={proposalId}
    versions={versions}
    currentVersionLabel={currentVersionLabel}
  />
)}
```

---

## 4. Phase 4 — 협업

### 4-1. 댓글 마크다운 지원 (H5)

**현재 코드**: `DetailRightPanel.tsx:76-92` — `<textarea>` + 순수 텍스트 렌더링

**수정 파일**: `components/DetailRightPanel.tsx`

#### 설계

마크다운 라이브러리 없이 **간단한 정규식 파서**로 구현 (의존성 최소화):

```typescript
function renderSimpleMarkdown(text: string): React.ReactNode {
  // 줄 단위 처리
  return text.split("\n").map((line, i) => {
    let rendered: React.ReactNode = line;
    // **bold**
    rendered = replacePattern(rendered, /\*\*(.+?)\*\*/g, (match) => <strong key={match}>{match}</strong>);
    // `code`
    rendered = replacePattern(rendered, /`(.+?)`/g, (match) => (
      <code key={match} className="px-1 py-0.5 bg-[#262626] rounded text-[10px] font-mono">{match}</code>
    ));
    // - list
    if (line.trimStart().startsWith("- ")) {
      return <li key={i} className="ml-3 list-disc text-[10px] text-[#8c8c8c]">{rendered}</li>;
    }
    return <p key={i} className="text-[10px] text-[#8c8c8c]">{rendered}</p>;
  });
}
```

**댓글 입력 영역**: 기존 `<textarea>` 유지 + 하단에 "마크다운 지원: **볼드**, \`코드\`, - 목록" 힌트 텍스트 추가.

---

### 4-2. 접근성 개선 (M5)

**수정 파일**: `components/AppSidebar.tsx`, `components/PhaseGraph.tsx`, `components/NotificationBell.tsx`

#### aria-label 추가 목록

| 컴포넌트 | 대상 | aria-label |
|----------|------|------------|
| `AppSidebar` | SvgIcon 사용 버튼들 | 이미 `aria-label={entry.label}` 있음 (확인 완료) |
| `AppSidebar` | 접기/펼치기 버튼 | `aria-label={collapsed ? "사이드바 펼치기" : "사이드바 접기"}` (title은 있으나 aria-label 없음) |
| `NotificationBell` | 벨 아이콘 버튼 | `aria-label="알림"` |
| `PhaseGraph` | 각 노드 버튼 | `aria-label={`STEP ${n}: ${name} - ${status}`}` |
| `ProposalEditor` Toolbar | B/I/U 등 버튼 | `aria-label="볼드"`, `aria-label="이탤릭"` 등 |

#### 상태 배지 텍스트 병기

현재 색상만으로 상태 표시하는 곳에 텍스트 추가:
```tsx
// PhaseGraph 노드 — 기존: 색상 원만 표시
// 변경: 색상 원 + 하단에 상태 텍스트 (completed/active/pending)
<span className="text-[8px] text-[#8c8c8c]">{statusText}</span>
```

---

### 4-3. 디자인 시스템 정리 (M2)

**신규 파일**: `components/ui/Card.tsx`, `components/ui/Modal.tsx`, `components/ui/Badge.tsx`

#### Card

```typescript
interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "bordered" | "elevated";
}

// variant별 스타일
// default: bg-[var(--card)] rounded-xl
// bordered: bg-[var(--card)] border border-[var(--border)] rounded-xl
// elevated: bg-[var(--card)] border border-[var(--border)] rounded-2xl shadow-lg
```

#### Modal

```typescript
interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl" | "full";
}

// size별 max-w
// sm: max-w-sm, md: max-w-md, lg: max-w-2xl, xl: max-w-4xl, full: w-[90vw]
// 공통: z-[var(--z-modal)], bg-[#0f0f0f]/80 오버레이, Escape 닫기
```

#### Badge

```typescript
interface BadgeProps {
  children: React.ReactNode;
  variant?: "success" | "warning" | "error" | "info" | "neutral";
  size?: "xs" | "sm";
}

// variant별 색상
// success: bg-[#3ecf8e]/15 text-[#3ecf8e]
// warning: bg-amber-500/15 text-amber-400
// error: bg-red-500/15 text-red-400
// info: bg-blue-500/15 text-blue-400
// neutral: bg-[#262626] text-[#8c8c8c]
```

**적용 전략**: Phase 4에서 컴포넌트만 생성. 기존 코드의 점진적 교체는 별도 리팩터링 사이클에서 수행.

---

## 5. 신규 의존성

| 패키지 | 용도 | Phase | 크기 (gzip) |
|--------|------|-------|-------------|
| `diff-match-patch` | AI diff + 버전 비교 | Phase 2 | ~24KB |

**제외된 의존성**:
- `react-markdown` → 간단한 정규식 파서로 대체 (4-1)
- `cva` (class-variance-authority) → Tailwind 직접 사용 유지

---

## 6. 구현 순서

```
Phase 1 (안정성)
  1-1. ProposalEditView isDirty + beforeunload     ← 가장 먼저
  1-2. KeyboardShortcutsGuide + Ctrl+S/Ctrl+/
  1-3. EditorAiPanel 경과 시간 카운터

Phase 2 (생산성)
  2-1. npm install diff-match-patch                ← 의존성 먼저
  2-2. AiSuggestionDiff 컴포넌트
  2-3. EditorAiPanel 수정 (diff 통합)
  2-4. Breadcrumb 컴포넌트 + ProposalEditView 헤더
  2-5. StepArtifactViewer GenericArtifact 개선
  2-6. AppSidebar KB localStorage

Phase 3 (확장성)
  3-1. globals.css 라이트 모드 변수
  3-2. layout.tsx 테마 깜빡임 방지 스크립트
  3-3. ThemeToggle + AppSidebar 통합
  3-4. ProposalEditView 반응형 (모바일 탭)
  3-5. AppSidebar 모바일 오버레이
  3-6. VersionCompareModal + DetailRightPanel 통합

Phase 4 (협업)
  4-1. DetailRightPanel 댓글 마크다운 렌더링
  4-2. 접근성 aria-label 일괄 추가
  4-3. ui/Card, ui/Modal, ui/Badge 생성
```

### 파일 변경 매트릭스

| 파일 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------|---------|---------|---------|---------|
| `ProposalEditView.tsx` | isDirty, beforeunload, 단축키 | Breadcrumb, currentContent | 반응형 탭 | — |
| `ProposalEditor.tsx` | — | — | — | aria-label |
| `EditorAiPanel.tsx` | 경과 시간 | AiSuggestionDiff | — | — |
| `AppSidebar.tsx` | — | KB localStorage | 모바일 오버레이, ThemeToggle | aria-label |
| `StepArtifactViewer.tsx` | — | 전체화면 모달 | — | — |
| `DetailRightPanel.tsx` | — | — | 비교 모달 | 마크다운 댓글 |
| `globals.css` | — | — | 라이트 모드 변수 | — |
| `layout.tsx` | — | — | 테마 스크립트 | — |
| **신규: KeyboardShortcutsGuide** | ✓ | — | — | — |
| **신규: AiSuggestionDiff** | — | ✓ | — | — |
| **신규: Breadcrumb** | — | ✓ | — | — |
| **신규: ThemeToggle** | — | — | ✓ | — |
| **신규: VersionCompareModal** | — | — | ✓ | — |
| **신규: ui/Card** | — | — | — | ✓ |
| **신규: ui/Modal** | — | — | — | ✓ |
| **신규: ui/Badge** | — | — | — | ✓ |
