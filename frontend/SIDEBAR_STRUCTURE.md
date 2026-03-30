# AppSidebar 메뉴 구조 및 설계

## 📍 현재 메뉴 레이아웃

```
┌─────────────────────────────────┐
│ 🟢 PA Proposal Coworker         │  ← 로고 (클릭: 열기/닫기)
├─────────────────────────────────┤
│ 📊 대시보드                      │  ← DASHBOARD
├─────────────────────────────────┤
│ 🔍 최근 작업                     │  ← RECENT (동적)
│   • 프로젝트 1    D-5, Ph2/5    │
│   • 프로젝트 2    D-Day, Ph1    │
├─────────────────────────────────┤
│ 👁️  공고 모니터링                │  ← NAV_REST[0]
│ 📄 제안 프로젝트                 │  ← NAV_REST[1]
│ 📚 지식 베이스              ▾   │  ← NAV_REST[2] (그룹)
│   • 통합 검색                    │
│   • 콘텐츠                       │
│   • 발주기관                     │
│   • 경쟁사                       │
│   • 교훈                         │
│   • Q&A                         │
│   • 노임단가                     │
│   • 시장가격                     │
├─────────────────────────────────┤
│ ⚙️  Admin                  ▾   │  ← 관리자만 (그룹)
│   • 이용자 관리                  │
│   • 프롬프트 관리                │
│   • A/B 실험                     │
├─────────────────────────────────┤
│ 🌙 다크모드 토글                 │
│ user@example.com    🔔          │
│ 🚪 로그아웃                      │
└─────────────────────────────────┘
```

---

## 사용자 요청 vs 현재 상태

### ❌ 문제점 1: 메뉴 순서
**사용자 요청:**
```
대시보드 → 공고모니터링 → 제안프로젝트 → 지식베이스 → 최근작업 → Admin
```

**현재 상태:**
```
대시보드 → 최근작업 → 공고모니터링 → 제안프로젝트 → 지식베이스 → Admin
           ↑ 위치 다름!
```

### ❌ 문제점 2: Settings 메뉴
**사용자 요청:**
```
Admin은 로그아웃 위쪽에 "setting"이라는 메뉴로 있으면 좋겠어
```

**현재 상태:**
```
이메일 클릭 → /settings 링크 (명시적 메뉴 아님)
```

---

## 📋 메뉴 정의 (코드 기준)

### 1️⃣ DASHBOARD (항상 표시)
```typescript
const DASHBOARD = {
  href: "/dashboard",
  label: "대시보드",
  icon: "dashboard"
};
```
위치: 라인 67, 렌더: 라인 354

### 2️⃣ RECENT PROPOSALS (동적 표시)
```typescript
if (recentProposals.length > 0) {
  // "최근 작업" 섹션 표시
  // 렌더: 라인 360-383
}
```
- 데이터: API에서 활성 proposal 5개
- D-Day: 빨강(≤3일), 노랑(≤14일), 회색(>14일)
- 상태점: 주황(initialized), 초록(processing/running)

### 3️⃣ NAV_REST (공고~지식베이스)
```typescript
const NAV_REST = [
  { href: "/monitoring", label: "공고 모니터링", ... },
  { href: "/proposals", label: "제안 프로젝트", ... },
  {
    label: "지식 베이스",
    basePath: "/kb",
    children: [
      { href: "/kb/search", label: "통합 검색", ... },
      { href: "/kb/content", label: "콘텐츠", ... },
      { href: "/kb/clients", label: "발주기관", ... },
      { href: "/kb/competitors", label: "경쟁사", ... },
      { href: "/kb/lessons", label: "교훈", ... },
      { href: "/kb/qa", label: "Q&A", ... },
      { href: "/kb/labor-rates", label: "노임단가", ... },
      { href: "/kb/market-prices", label: "시장가격", ... },
    ]
  }
];
```
렌더: 라인 386-423

### 4️⃣ ADMIN_GROUP (관리자만)
```typescript
if (userRole === "admin" || userRole === "manager") {
  const ADMIN_GROUP = {
    label: "Admin",
    basePath: "/admin",
    children: [
      { href: "/admin", label: "이용자 관리", ... },
      { href: "/admin/prompts", label: "프롬프트 관리", ... },
      { href: "/admin/prompts/experiments", label: "A/B 실험", ... },
    ]
  };
}
```
렌더: 라인 426-450

### 5️⃣ 하단 섹션 (항상 표시)
```typescript
// Theme, Email, NotificationBell, Logout
```
렌더: 라인 454-470

---

## 🎨 스타일

### 메인 항목
- 활성: `bg-[#1c1c1c] text-[#ededed]`
- 비활성: `text-[#8c8c8c] hover:bg-[#1a1a1a]`
- 크기: `px-3 py-2 text-sm`

### 자식 항목 (expand 내)
- 활성: `bg-[#1c1c1c] text-[#ededed]`
- 비활성: `text-[#8c8c8c] hover:bg-[#1a1a1a]`
- 크기: `px-3 py-1.5 text-[11px]`
- 들여쓰기: `ml-3`

---

## 💾 상태 관리

```typescript
const [collapsed, setCollapsed] = useState(false);           // 사이드바 열기/닫기
const [sidebarWidth, setSidebarWidth] = useState(208);      // 너비 (180~360px)
const [kbOpen, setKbOpen] = useState(false);                // 지식베이스 expand
const [adminOpen, setAdminOpen] = useState(false);          // Admin expand
const [mobileOpen, setMobileOpen] = useState(false);        // 모바일 슬라이드

// localStorage에 영속화
localStorage.setItem("sidebar-collapsed", collapsed);
localStorage.setItem("sidebar-width", sidebarWidth);
localStorage.setItem("kb-open", kbOpen);
localStorage.setItem("admin-open", adminOpen);
```

---

## 🔧 해결할 문제

### 👉 Priority 1: 메뉴 순서 변경
**파일:** `components/AppSidebar.tsx`

**변경 전:**
```javascript
// Line 353-357: DASHBOARD
// Line 360-383: RECENT (← 여기!)
// Line 386-423: NAV_REST (공고~KB)
// Line 426-450: ADMIN
```

**변경 후:**
```javascript
// Line 353-357: DASHBOARD
// Line 360-423: NAV_REST (공고~KB)
// Line ???-???: RECENT (← 여기로!)
// Line ???-???: ADMIN
```

**코드 변경 위치:**
1. 현재 최근작업 블록 (라인 360-383) 자르기
2. NAV_REST 렌더링 후 붙이기
3. Admin 앞에 위치하도록

### 👉 Priority 2: Settings 메뉴 추가
**추가할 코드:**

```typescript
// 라인 95 (ADMIN_GROUP 아래) 에 추가
const SETTINGS_ITEM: NavItem = {
  href: "/settings",
  label: "설정",
  icon: "gear"  // 새 아이콘
};

// 라인 60 (ICONS 객체에) 추가
gear: "M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z",

// 라인 451 (Admin 섹션 바로 후) 에 추가
<Link href={SETTINGS_ITEM.href} className={lCls(isActive(SETTINGS_ITEM.href))}>
  <SvgIcon d={ICONS[SETTINGS_ITEM.icon] || ""} className="opacity-70 shrink-0" />
  <span>{SETTINGS_ITEM.label}</span>
</Link>
```

---

## ✨ 최종 메뉴 구조 (목표)

```
📊 대시보드
────────────
👁️  공고 모니터링
📄 제안 프로젝트
📚 지식 베이스        ▾
  🔍 통합 검색
  📋 콘텐츠
  👥 발주기관
  🔄 경쟁사
  💡 교훈
  ❓ Q&A
  💰 노임단가
  📊 시장가격
────────────
🔍 최근 작업          ← 위치 변경!
  • 프로젝트 1
  • 프로젝트 2
────────────
⚙️  Admin        ▾   ← 관리자만
  👥 이용자 관리
  🔧 프롬프트 관리
  🧪 A/B 실험
⚙️  설정              ← 새로 추가!
────────────
🌙 테마 토글
user@... 🔔
🚪 로그아웃
```

---

## 📝 구현 체크리스트

- [ ] `components/AppSidebar.tsx` 수정
  - [ ] ICONS에 "gear" 아이콘 추가 (라인 60 근처)
  - [ ] SETTINGS_ITEM 상수 추가 (라인 95 근처)
  - [ ] 최근 작업 블록 이동 (라인 360-383 → 라인 420 후)
  - [ ] Settings 메뉴 렌더링 추가 (Admin 아래, 로그아웃 위)

- [ ] 테스트
  - [ ] 모든 링크 동작 확인
  - [ ] 데스크톱 반응형 확인
  - [ ] 모바일 슬라이드 확인
  - [ ] Admin 권한 확인 (관리자만 표시)

---

## 📂 관련 파일

- **메인:** `frontend/components/AppSidebar.tsx`
- **상수 정의:** 라인 42-95 (ICONS, NAV_REST, ADMIN_GROUP 등)
- **렌더 함수:** 라인 331-473 (renderSidebarContent)
- **스타일:** 라인 110-117 (lCls, cLCls)
