# 사이드바(AppSidebar) 메뉴 구조

## 📊 전체 계층 구조

```
AppSidebar (AppSidebar.tsx)
├── 📱 모바일 (lg 미만)
│   ├── 햄버거 버튼 (좌상단 고정)
│   └── 슬라이드 오버레이 (너비: 256px, 애니메이션)
│
└── 🖥️ 데스크톱 (lg 이상)
    ├── PA 아이콘 미니바 (닫혀있을 때)
    └── 전체 사이드바 (열려있을 때, 드래그 리사이즈)
```

---

## 🎯 메뉴 항목 (NAV_REST)

### 1단계 메뉴

#### 대시보드 (Dashboard)
```
🏠 대시보드
   └── href: /dashboard
   └── icon: home
   └── 고정 항목 (DASHBOARD 상수)
```

#### 공고 모니터링 (Bid Monitoring)
```
👁️ 공고 모니터링
   └── href: /monitoring
   └── icon: eye (검색 시력)
   └── 진입점: G2B 공고 검색 및 모니터링
```

#### 제안 프로젝트 (Proposals)
```
📄 제안 프로젝트
   └── href: /proposals
   └── icon: document
   └── 하위: /proposals/[id], /proposals/[id]/edit, /proposals/[id]/evaluation
```

---

## 📚 지식 베이스 (Knowledge Base) - 그룹

```
📖 지식 베이스 (Expandable Group)
├── basePath: /kb
├── icon: book
├── 상태 저장: sidebar-kb-expanded (localStorage)
│
└── 하위 메뉴 (8개):
    ├── 🔍 통합 검색
    │   └── href: /kb/search
    │   └── icon: search
    │   └── 설명: 모든 KB 데이터 통합 검색
    │
    ├── 📝 콘텐츠
    │   └── href: /kb/content
    │   └── icon: list
    │   └── 설명: 제안서 템플릿, 사례 등
    │
    ├── 🏢 발주기관
    │   └── href: /kb/clients
    │   └── icon: organization
    │   └── 설명: 발주처 정보, 성향, 수주율
    │
    ├── 🎯 경쟁사
    │   └── href: /kb/competitors
    │   └── icon: users
    │   └── 설명: 경쟁업체 정보, 수주실적
    │
    ├── 💡 교훈
    │   └── href: /kb/lessons
    │   └── icon: lightbulb
    │   └── 설명: 과거 제안 교훈, 실패 원인
    │
    ├── ❓ Q&A
    │   └── href: /kb/qa
    │   └── icon: question
    │   └── 설명: 제안 작성 중 자주 묻는 질문
    │
    ├── 💰 노임단가
    │   └── href: /kb/labor-rates
    │   └── icon: person
    │   └── 설명: 인력 단가 테이블, 시장 기준
    │
    └── 📊 시장가격
        └── href: /kb/market-prices
        └── icon: chart
        └── 설명: 시장 낙찰가, 예정가격 현황
```

---

## 👨‍💼 Admin (관리자 전용) - 그룹

```
⚙️ Admin (Expandable Group - 관리자/매니저만 표시)
├── basePath: /admin
├── icon: settings
├── 권한: admin, manager
├── 상태 저장: sidebar-admin-expanded (localStorage)
│
└── 하위 메뉴 (3개):
    ├── 👥 이용자 관리
    │   └── href: /admin
    │   └── icon: users
    │   └── 설명: 사용자, 조직, 팀 관리
    │
    ├── 💬 프롬프트 관리
    │   └── href: /admin/prompts
    │   └── icon: message
    │   └── 설명: AI 프롬프트 카탈로그, 관리
    │
    └── 🧪 A/B 실험
        └── href: /admin/prompts/experiments
        └── icon: beaker
        └── 설명: 프롬프트 A/B 테스트
```

---

## 🎯 특수 섹션

### 최근 작업 (Recent Proposals)

```
최근 작업
├── 데이터 소스: api.proposals.list({ scope: "my" })
├── 필터링: ACTIVE_STATUSES = ["initialized", "processing", "running"]
├── 정렬: updated_at 역순
├── 제한: 3개까지만 표시
│
└── 각 항목 구성:
    ├── 상태 아이콘 (동그란 점)
    │   ├── 주황색 (#f59e0b): initialized (준비 중)
    │   └── 초록색 (#3ecf8e): processing/running (진행 중)
    │
    ├── 제목 (텍스트 축약)
    │
    └── 부정보:
        ├── D-Day 표시 (색상 지정)
        │   ├── 빨강: D-3 이하
        │   ├── 노랑: D-3~D-14
        │   └── 회색: 그 이상
        │
        └── Phase 진행도
            └── "Phase 2/5" 형식
```

---

## 🎨 UI 상태

### 활성 상태 (Active)

- **메인 메뉴**: 현재 경로와 일치하면 배경색 강조
  - 배경: `bg-[#1c1c1c]`
  - 텍스트: `text-[#ededed]`

- **서브 메뉴**: 더 밝은 표시
  - 왼쪽 들여쓰기 추가

- **그룹 토글**: 그룹 내 현재 경로가 있으면 활성 표시

### 호버 상태

```
배경: hover:bg-[#1a1a1a]
텍스트: hover:text-[#ededed]
전환: transition-colors (부드러운 애니메이션)
```

---

## 💾 상태 관리 (localStorage)

| 키 | 값 | 설명 | 예시 |
|------|------|------|------|
| `sidebar-collapsed` | "true" / "false" | 사이드바 접힘/펼침 | 기본값: 열려있음 |
| `sidebar-width` | 숫자 (180~360) | 사이드바 너비(px) | 기본값: 208px |
| `sidebar-kb-expanded` | "true" / "false" | 지식베이스 그룹 펼침 | 경로 진입 시 자동 펼침 |
| `sidebar-admin-expanded` | "true" / "false" | Admin 그룹 펼침 | 경로 진입 시 자동 펼침 |

---

## ⌨️ 상호작용

### 데스크톱

| 동작 | 효과 |
|------|------|
| PA 로고 클릭 | 사이드바 접기/펼치기 토글 |
| 우측 경계 드래그 | 너비 조절 (180~360px) |
| 우측 경계 더블클릭 | 기본 너비(208px)로 리셋 |
| 그룹 버튼 클릭 | 하위 메뉴 펼치기/접기 |
| 메뉴 항목 클릭 | 해당 페이지로 이동 |

### 모바일

| 동작 | 효과 |
|------|------|
| 햄버거 아이콘 클릭 | 슬라이드 오버레이 열기/닫기 |
| 배경 영역 클릭 | 오버레이 닫기 |
| Escape 키 | 오버레이 닫기 |
| 메뉴 항목 클릭 | 페이지 이동 + 자동 닫기 |

---

## 🔧 하단 섹션 (Footer)

```
하단 섹션
├── 테마 토글 (라이트/다크 모드)
│
├── 사용자 이메일
│   ├── 링크: /settings
│   ├── 텍스트: development일 때 "dev@tenopa.co.kr"
│   └── 호버 효과 있음
│
├── 알림 벨 (NotificationBell 컴포넌트)
│   └── 미읽음 알림 수 표시
│
└── 로그아웃 버튼
    ├── 아이콘: 로그아웃 화살표
    └── 클릭: Supabase 로그아웃 → /login 리다이렉트
```

---

## 🎯 자동 펼침 로직

지식베이스 또는 Admin 페이지에 진입할 때 자동으로 그룹을 펼칩니다:

```typescript
// 경로 변경 감지
pathname: "/kb/clients" → 지식베이스 자동 펼침
pathname: "/admin/prompts" → Admin 그룹 자동 펼침

// 단, 사용자가 이미 닫은 경우 유지:
// 사용자가 펼쳐진 상태에서 /kb/clients로 이동 → 펼쳐진 상태 유지
// 사용자가 닫은 상태에서 /kb/clients로 이동 → 자동 펼침 (현재 페이지 보기 위해)
```

---

## 🎨 너비 설정

| 상태 | 너비 | 설명 |
|------|------|------|
| Collapsed | 48px | PA 아이콘만 표시 (미니바) |
| Default | 208px | 표준 너비 |
| Minimum | 180px | 드래그 최소값 |
| Maximum | 360px | 드래그 최대값 |

---

## 📱 반응형 동작

### Desktop (lg 이상)

- 사이드바 항상 표시
- 드래그로 너비 조절 가능
- 접기/펼치기 토글 가능
- 최근 작업 표시

### Tablet / Mobile (lg 미만)

- 햄버거 메뉴로 슬라이드 오버레이 형식
- 너비: 고정 256px
- 드래그 불가능
- 페이지 이동 시 자동 닫기
- 배경 클릭 또는 Escape로 닫기 가능

---

## 🔒 권한 제어

### 모든 사용자
- 대시보드
- 공고 모니터링
- 제안 프로젝트
- 지식 베이스 (모든 항목)

### 관리자 / 매니저만
- Admin 섹션 표시
  - 이용자 관리
  - 프롬프트 관리
  - A/B 실험

---

## 📊 아이콘 목록

| 항목 | 아이콘 이름 | SVG 경로 |
|------|-----------|---------|
| 대시보드 | dashboard | 홈 모양 |
| 공고 모니터링 | bids | 눈 모양 |
| 제안 프로젝트 | proposals | 문서 모양 |
| 지식 베이스 | kb | 책 모양 |
| 통합 검색 | search | 돋보기 |
| 콘텐츠 | content | 리스트 |
| 발주기관 | clients | 사람들 |
| 경쟁사 | competitors | 비교 |
| 교훈 | lessons | 전구 |
| Q&A | qa | 물음표 |
| 노임단가 | labor | 사람 |
| 시장가격 | market | 차트 |
| Admin | admin | 설정 |
| 이용자 관리 | org | 조직 |
| 프롬프트 | prompt | 메시지 |
| A/B 실험 | experiment | 실험 |

---

## 🚀 코드 구조

### 주요 컴포넌트

```typescript
// 1. 메뉴 데이터 정의
const DASHBOARD: NavItem = { href, label, icon }
const NAV_REST: NavEntry[] = [/* 아이템들 */]
const ADMIN_GROUP: NavGroup = { label, icon, basePath, children }

// 2. 상태 관리
const [collapsed, setCollapsed] = useState(null)  // SSR 안전
const [sidebarWidth, setSidebarWidth] = useState(208)
const [kbOpen, setKbOpen] = useState(false)
const [adminOpen, setAdminOpen] = useState(false)

// 3. 렌더링
function renderSidebarContent(forMobile) { /* 공유 콘텐츠 */ }
// 모바일과 데스크톱에서 같은 콘텐츠 사용
```

### 성능 최적화

- **localStorage 안전화**: SSR, 시크릿 모드, 스토리지 가득 찬 경우 처리
- **AbortController**: API 요청 취소 처리
- **useCallback**: 콜백 함수 메모이제이션
- **ref 활용**: React 배치와 무관한 실시간 너비 추적

---

## 🔄 경로와 메뉴 매핑

| 경로 | 메뉴 | 상태 |
|------|------|------|
| `/dashboard` | 🏠 대시보드 | 활성 |
| `/monitoring/*` | 👁️ 공고 모니터링 | 활성 |
| `/proposals/*` | 📄 제안 프로젝트 | 활성 |
| `/kb/search` | 📖 지식베이스 > 🔍 통합 검색 | 활성 + KB 펼침 |
| `/kb/content` | 📖 지식베이스 > 📝 콘텐츠 | 활성 + KB 펼침 |
| `/admin/*` | ⚙️ Admin > (해당 항목) | 활성 + Admin 펼침 |
| `/settings` | (메뉴 항목 아님) | - |

---

## 📝 주의사항

1. **SSR 안전**: `collapsed` 초기값은 `null`, 마운트 후 `localStorage` 복원
2. **모바일 우선**: `lg` 이상에서만 데스크톱 사이드바 표시
3. **localStorage**: 시크릿 모드에서도 안전하게 작동
4. **권한 제어**: `userRole`에 따라 Admin 섹션 표시
5. **경로 자동 펼침**: 사용자 의도 존중 (닫은 후 다시 닫지 않음)

