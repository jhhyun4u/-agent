# 간격(Spacing) 및 그림자(Shadow) 시스템

## 간격 체계 (Spacing System)

8px 기반 일관된 간격 시스템을 사용합니다.

### 간격 스케일

| 변수 | 크기 | CSS | Tailwind | 사용 예 |
|------|------|-----|----------|--------|
| `xs` | 6px | `0.375rem` | `gap-xs` | 아이콘과 텍스트 사이 |
| `sm` | 8px | `0.5rem` | `gap-sm` | 인라인 요소 간격 |
| `md` | 16px | `1rem` | `gap-md` `p-md` | 컴포넌트 간 기본 간격 |
| `lg` | 24px | `1.5rem` | `gap-lg` `p-lg` | 섹션 간 간격 |
| `xl` | 32px | `2rem` | `gap-xl` | 주요 영역 간 간격 |
| `2xl` | 48px | `3rem` | `gap-2xl` | 큰 섹션 간 |
| `3xl` | 64px | `4rem` | `gap-3xl` | 페이지 최상단 간격 |

### 사용 방법

```tsx
// Padding (내부 간격)
<div className="p-md">콘텐츠</div>
<div className="p-lg">큰 영역</div>
<div className="px-md py-lg">좌우 16px, 상하 24px</div>

// Margin (외부 간격)
<div className="m-md">외부 간격</div>
<div className="mb-lg">아래쪽 24px</div>

// Gap (플렉스박스/그리드)
<div className="flex gap-md">
  <div>항목 1</div>
  <div>항목 2</div>
</div>

<div className="grid grid-cols-3 gap-lg">
  <div>칸 1</div>
  <div>칸 2</div>
  <div>칸 3</div>
</div>

// Space-between (자동 간격)
<div className="space-y-md">
  <div>항목 1</div>
  <div>항목 2</div>
  <div>항목 3</div>
</div>
```

### 일반적인 패턴

```tsx
// 카드 내부
<Card>
  <CardHeader />        {/* 자동 pb-3 border-b */}
  <CardBody className="pt-md">      {/* 위쪽 16px */}
    <p>본문</p>
  </CardBody>
  <CardFooter className="mt-md">   {/* 위쪽 16px, border-t */}
    <Button>버튼</Button>
  </CardFooter>
</Card>

// 폼 그룹
<form className="space-y-lg">
  <TextInput label="..." />
  <TextInput label="..." />
  <TextArea label="..." />
  <div className="flex gap-md">
    <Button>저장</Button>
    <Button>취소</Button>
  </div>
</form>

// 페이지 레이아웃
<div className="p-lg space-y-xl">
  <h1 className={TEXT_SIZES.h1}>페이지 제목</h1>
  
  <section className="space-y-md">
    <h2 className={TEXT_SIZES.h2}>섹션 1</h2>
    <Card>...</Card>
  </section>
  
  <section className="space-y-md">
    <h2 className={TEXT_SIZES.h2}>섹션 2</h2>
    <Card>...</Card>
  </section>
</div>
```

---

## 그림자 체계 (Shadow System)

시각적 계층을 표현하기 위한 그림자 스케일입니다.

### 그림자 레벨

| 레벨 | CSS 클래스 | 설명 | 사용 예 |
|------|-----------|------|--------|
| No Shadow | (없음) | 평면 | 배경, 모드별 컴포넌트 |
| Small | `shadow-sm` | 미묘한 깊이 | 호버 상태, 팝오버 |
| Medium | `shadow-md` | 일반적인 깊이 | 카드, 모달 |
| Large | `shadow-lg` | 두드러진 깊이 | 드롭다운, 플로팅 버튼 |
| XLarge | `shadow-xl` | 강한 깊이 | 모달 배경, 중요 오버레이 |
| Elevation | `shadow-elevation` | 최고 깊이 | 전체 화면 오버레이 |
| Card Hover | `shadow-card-hover` | 카드 호버 | 카드 인터랙션 |

### 사용 방법

```tsx
// 기본 카드 (shadow-sm)
<Card className="shadow-sm">
  <CardHeader title="카드" />
  <CardBody>내용</CardBody>
</Card>

// 호버 시 그림자 증가
<Card className="shadow-sm hover:shadow-card-hover transition-shadow">
  <CardHeader title="인터랙티브 카드" />
  <CardBody>내용</CardBody>
</Card>

// 모달 배경
<div className="fixed inset-0 bg-black/50 shadow-elevation">
  <div className="absolute inset-0 flex items-center justify-center">
    <div className="bg-white shadow-lg rounded-lg">
      모달 내용
    </div>
  </div>
</div>

// 드롭다운
<button className="relative">
  메뉴
  <div className="absolute top-full mt-sm shadow-lg rounded-lg bg-white">
    <div>옵션 1</div>
    <div>옵션 2</div>
  </div>
</button>

// 플로팅 버튼
<button className="fixed bottom-lg right-lg shadow-lg hover:shadow-elevation transition-shadow">
  +
</button>
```

---

## 그림자 색상 (다크모드)

다크 모드에서 그림자는 검은색의 다양한 투명도로 표현됩니다:

```css
/* Dark Mode Shadow */
.shadow-sm {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.shadow-md {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.shadow-lg {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
}

.shadow-elevation {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4);
}

.shadow-card-hover {
  box-shadow: 0 20px 25px -5px rgba(62, 207, 142, 0.1);
}
```

---

## 실제 적용 예시

### 다층 구조

```tsx
export default function ComplexLayout() {
  return (
    <div className="min-h-screen bg-[#0f0f0f] p-3xl">
      {/* 페이지 제목 섹션 */}
      <div className="space-y-lg mb-3xl">
        <h1 className={TEXT_SIZES.h1}>제목</h1>
        <p className={TEXT_SIZES.caption}>부제목</p>
      </div>

      {/* 주요 콘텐츠 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-xl mb-xl">
        {/* 카드 1 */}
        <Card className="shadow-sm hover:shadow-card-hover">
          <CardHeader title="카드 1" />
          <CardBody className="space-y-md">
            <p className={TEXT_SIZES.body}>내용</p>
          </CardBody>
          <CardFooter className="gap-md">
            <Button size="sm">작업</Button>
          </CardFooter>
        </Card>

        {/* 카드 2 */}
        <Card className="shadow-sm hover:shadow-card-hover">
          <CardHeader title="카드 2" />
          <CardBody className="space-y-md">
            <p className={TEXT_SIZES.body}>내용</p>
          </CardBody>
        </Card>
      </div>

      {/* 폼 섹션 */}
      <Card className="shadow-md">
        <CardHeader title="폼" />
        <CardBody className="space-y-lg">
          <TextInput label="필드 1" />
          <TextInput label="필드 2" />
        </CardBody>
        <CardFooter className="gap-md">
          <Button variant="primary">저장</Button>
          <Button variant="secondary">취소</Button>
        </CardFooter>
      </Card>
    </div>
  );
}
```

---

## 마이그레이션 체크리스트

- [ ] 모든 `p-4` → `p-md`, `p-6` → `p-lg` 변경
- [ ] 모든 `gap-4` → `gap-md`, `gap-6` → `gap-lg` 변경
- [ ] 모든 `space-y-4` → `space-y-md` 변경
- [ ] 카드에 `shadow-sm` 추가
- [ ] 호버 상태에 `hover:shadow-card-hover` 추가
- [ ] 모달에 `shadow-lg` 또는 `shadow-elevation` 사용
- [ ] 플로팅 요소에 적절한 그림자 추가
- [ ] 페이지 상단 여백에 `pt-3xl` 또는 `p-3xl` 사용

---

## 주의사항

1. **과도한 그림자**: 그림자가 많으면 오히려 어색해 보입니다. 필요한 곳에만 사용합니다.
2. **라이트 모드**: 라이트 모드에서는 그림자가 덜 눈에 띕니다. 스케일을 조정할 수 있습니다.
3. **성능**: 과도한 그림자는 렌더링 성능에 영향을 줄 수 있습니다.
4. **일관성**: 같은 목적의 요소는 같은 그림자를 사용합니다.

