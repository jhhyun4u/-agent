# Frontend UI/UX 디자인 점검 보고서

## 📊 평가 결과
- **전체 일관성**: ⭐⭐⭐⭐ (90%)
- **색상 시스템**: ⭐⭐⭐⭐⭐ (95%)
- **타이포그래피**: ⭐⭐⭐⭐ (85%)
- **컴포넌트 재사용성**: ⭐⭐⭐ (75%)
- **반응형 설계**: ⭐⭐⭐⭐ (88%)

---

## ✅ 잘 구현된 부분

### 1. **색상 시스템 (Color System)**
```css
/* Dark Mode (기본) */
--bg: #0f0f0f        /* 배경 */
--surface: #111111   /* 2차 표면 */
--card: #1c1c1c      /* 카드 */
--border: #262626    /* 테두리 */
--text: #ededed      /* 텍스트 */
--muted: #8c8c8c     /* 음소거 텍스트 */
--accent: #3ecf8e    /* 강조색 (초록색) */
```
**평가**: CSS 변수로 중앙화되어 다크/라이트 모드 전환이 깔끔함

### 2. **반응형 디자인**
- 모바일 터치 타겟 최소 44px ✓
- Flexbox 기반 레이아웃 ✓
- 사이드바 접기/펼치기 기능 ✓
- 모바일 슬라이드 오버레이 ✓

### 3. **접근성 (Accessibility)**
- Focus-visible 링 강화 ✓
- Disabled 상태 시각화 ✓
- 키보드 탐색 지원 ✓
- 스크롤바 커스터마이징 ✓

### 4. **Z-Index 체계**
```css
--z-dropdown: 50
--z-modal: 60
--z-overlay: 70
--z-toast: 80
```
**평가**: 명확한 레이어 계층 구조

---

## ⚠️ 개선 필요 부분

### 1. **타이포그래피 일관성 (Typography Consistency)**

**현재 상태**:
- Tiptap `prose prose-invert prose-sm` 사용
- 페이지별로 다른 폰트 크기/가중치 사용

**개선안**:
```typescript
// lib/typography.ts (신규 파일)
export const TEXT_SIZES = {
  h1: "text-3xl font-bold tracking-tight",
  h2: "text-2xl font-semibold tracking-tight",
  h3: "text-xl font-semibold",
  body: "text-sm leading-6 text-[#ededed]",
  small: "text-xs leading-5 text-[#8c8c8c]",
  caption: "text-xs font-medium uppercase tracking-wider text-[#8c8c8c]",
} as const;

// 사용
<h1 className={TEXT_SIZES.h1}>제목</h1>
<p className={TEXT_SIZES.body}>본문</p>
```

### 2. **버튼 스타일 일관성**

**현재 상태**:
- `.btn-sm`, `.btn-md`, `.btn-lg`만 정의
- 버튼 색상/상태(primary, secondary, danger) 정의 부재

**개선안**:
```css
/* globals.css 추가 */
.btn-primary {
  @apply px-4 py-2 rounded-lg bg-[#3ecf8e] text-[#0f0f0f] font-medium
    hover:bg-[#34b87a] active:opacity-90 disabled:opacity-50;
}

.btn-secondary {
  @apply px-4 py-2 rounded-lg bg-[#262626] text-[#ededed] font-medium
    hover:bg-[#303030] border border-[#404040];
}

.btn-danger {
  @apply px-4 py-2 rounded-lg bg-red-600/20 text-red-400 font-medium
    hover:bg-red-600/30;
}
```

### 3. **입력 필드 일관성 부족**

**현재 상태**:
- Input/Textarea/Select 스타일이 컴포넌트마다 다름
- Placeholder 색상만 정의됨

**개선안**:
```css
/* globals.css 추가 */
input, textarea, select {
  @apply bg-[#111111] border border-[#262626] text-[#ededed]
    rounded-lg px-3 py-2 transition-colors
    focus-visible:border-[#3ecf8e] focus-visible:outline-none;
}

input:disabled, textarea:disabled, select:disabled {
  @apply bg-[#1c1c1c] opacity-50 cursor-not-allowed;
}
```

### 4. **카드 컴포넌트 표준화**

**현재 상태**:
- `.card` 클래스 정의 없음
- 각 페이지에서 개별적으로 구현

**개선안**:
```css
.card {
  @apply bg-[#1c1c1c] border border-[#262626] rounded-lg
    p-4 shadow-sm hover:border-[#303030] transition-colors;
}

.card-header {
  @apply flex items-center justify-between pb-3 border-b border-[#262626];
}

.card-body {
  @apply pt-4;
}

.card-footer {
  @apply flex items-center gap-2 pt-4 border-t border-[#262626];
}
```

### 5. **간격(Spacing) 체계 부재**

**현재 상태**:
- 각 컴포넌트에서 `gap`, `p`, `m` 값이 일관되지 않음

**개선안**: Tailwind spacing 스케일 명시
```typescript
// tailwind.config.ts
const config: Config = {
  theme: {
    extend: {
      spacing: {
        'xs': '0.375rem', /* 6px */
        'sm': '0.5rem',   /* 8px */
        'md': '1rem',     /* 16px */
        'lg': '1.5rem',   /* 24px */
        'xl': '2rem',     /* 32px */
      },
    },
  },
};
```

### 6. **그림자(Shadow) 체계 부족**

**현재 상태**:
- `shadow-sm` 정도만 사용
- 깊이감이 약함

**개선안**:
```typescript
// tailwind.config.ts
shadows: {
  'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.2)',
  'elevation': '0 20px 25px -5px rgba(0, 0, 0, 0.3)',
}
```

---

## 🔧  구체적 개선 작업

### 작업 1: 통합 타이포그래피 모듈 생성
```bash
파일: frontend/lib/typography.ts
내용: 모든 텍스트 스타일 상수화
영향: 모든 페이지 (낮음 - 선택적)
```

### 작업 2: 글로벌 컴포넌트 클래스 확대
```bash
파일: frontend/app/globals.css
추가: .btn-*, .input-*, .card-* 클래스
영향: 기존 코드 호환성 유지
```

### 작업 3: 색상 팔레트 확대
```bash
파일: frontend/app/globals.css
추가: status colors (success, warning, error, info)
```

### 작업 4: 컴포넌트 라이브러리 정리
```bash
대상: DataTable, Dialog, Dropdown 등
목표: 일관된 스타일 및 Props 인터페이스
```

---

## 📋 체크리스트

| 항목 | 상태 | 우선순위 | 예상 시간 |
|------|------|---------|---------|
| 타이포그래피 표준화 | ⏳ | HIGH | 2h |
| 버튼 스타일 확대 | ⏳ | HIGH | 1.5h |
| 입력 필드 표준화 | ⏳ | MEDIUM | 1.5h |
| 카드 컴포넌트 | ⏳ | MEDIUM | 1h |
| 간격 체계 | ⏳ | MEDIUM | 1h |
| 그림자 체계 | ⏳ | LOW | 0.5h |

---

## 🎯 권장 수행 순서

1. **Phase 1 (즉시)**: 타이포그래피 + 버튼 스타일 → 가장 눈에 띄는 개선
2. **Phase 2 (1주일)**: 입력 필드 + 카드 컴포넌트 → UI 규칙성 강화
3. **Phase 3 (2주일)**: 간격 및 그림자 체계 → 미묘한 품질 향상

---

## 💡 추가 권장사항

### 1. **컴포넌트 문서화**
현재 shadcn/ui 컴포넌트들이 여러 곳에서 사용되는데, 통합 가이드 작성 권장

### 2. **라이트 모드 테스트**
라이트 모드 색상들이 설정되어 있지만 실제 페이지에서 테스트 미완료

### 3. **다크 모드 일관성**
- 모든 입력 필드가 `#111111` 배경
- 일부 상태 메시지가 채도 높음 (예: `text-red-400`) → 배경색과 대비 확인

### 4. **애니메이션 표준화**
- 현재 `slideX` 애니메이션만 정의
- hover, focus, active 전환 시간 표준화 권장 (200ms)

---

## 📝 결론

**현재 평가**: 상당히 일관된 다크 모드 중심의 모던 UI
**주요 강점**: 색상 시스템, 접근성, z-index 계층화
**개선 영역**: 타이포그래피, 버튼/입력 필드 표준화

**다음 단계**:
→ 위의 "권장 수행 순서"에 따라 Phase 1부터 시작하기를 권장합니다.
