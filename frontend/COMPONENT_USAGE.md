# UI 컴포넌트 사용 가이드

이 가이드는 새롭게 표준화된 UI 컴포넌트 사용법을 설명합니다.

## 버튼 (Button)

```tsx
import { Button } from "@/components/ui/Button";

export default function Example() {
  return (
    <div className="flex gap-2">
      {/* 주요 액션 */}
      <Button variant="primary" size="md">
        저장
      </Button>

      {/* 보조 액션 */}
      <Button variant="secondary" size="md">
        취소
      </Button>

      {/* 위험한 액션 */}
      <Button variant="danger" size="md" onClick={() => confirm("정말 삭제하시겠습니까?")}>
        삭제
      </Button>

      {/* 텍스트 버튼 */}
      <Button variant="ghost" size="md">
        더보기
      </Button>

      {/* 로딩 상태 */}
      <Button variant="primary" loading>
        처리 중...
      </Button>
    </div>
  );
}
```

### Button Props

| 속성 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `variant` | `primary \| secondary \| danger \| ghost` | `secondary` | 버튼 스타일 |
| `size` | `sm \| md \| lg \| xl` | `md` | 버튼 크기 |
| `loading` | `boolean` | `false` | 로딩 상태 (처리 중... 표시) |
| `disabled` | `boolean` | `false` | 비활성화 상태 |

---

## 카드 (Card)

```tsx
import { Card, CardHeader, CardBody, CardFooter } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function Example() {
  return (
    <Card>
      <CardHeader 
        title="카드 제목" 
        subtitle="부제목"
        action={<Button size="sm">편집</Button>}
      />
      <CardBody>
        <p>카드 본문 내용이 여기에 들어갑니다.</p>
      </CardBody>
      <CardFooter>
        <Button variant="secondary" size="sm">취소</Button>
        <Button variant="primary" size="sm">저장</Button>
      </CardFooter>
    </Card>
  );
}
```

### Card Props

| 컴포넌트 | Props | 설명 |
|---------|-------|------|
| `Card` | `className` | 추가 CSS 클래스 |
| `CardHeader` | `title`, `subtitle`, `action`, `children` | 헤더 구성 |
| `CardBody` | `className`, `children` | 본문 |
| `CardFooter` | `className`, `children` | 푸터 |

---

## 폼 필드 (FormField)

```tsx
import { 
  FormField, 
  TextInput, 
  TextArea, 
  Select 
} from "@/components/ui/FormField";
import { Button } from "@/components/ui/Button";

export default function Example() {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    category: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  return (
    <form className="space-y-4">
      <TextInput
        label="이름"
        placeholder="항목 이름 입력"
        required
        value={formData.name}
        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        error={errors.name}
        helperText="최소 3자 이상"
      />

      <TextArea
        label="설명"
        placeholder="상세 설명을 입력하세요..."
        required
        value={formData.description}
        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
        error={errors.description}
      />

      <Select
        label="분류"
        required
        value={formData.category}
        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
        options={[
          { value: "type-a", label: "유형 A" },
          { value: "type-b", label: "유형 B" },
          { value: "type-c", label: "유형 C" },
        ]}
        error={errors.category}
      />

      <div className="flex gap-2">
        <Button type="submit" variant="primary">
          저장
        </Button>
        <Button type="reset" variant="secondary">
          초기화
        </Button>
      </div>
    </form>
  );
}
```

### FormField Props

| 컴포넌트 | Props | 설명 |
|---------|-------|------|
| `FormField` | `label`, `error`, `helperText`, `required` | 폼 필드 래퍼 |
| `TextInput` | (TextInput의 모든 Props) + FormField Props | 텍스트 입력 |
| `TextArea` | (TextArea의 모든 Props) + FormField Props | 긴 텍스트 입력 |
| `Select` | `options`, (Select의 모든 Props) + FormField Props | 드롭다운 |

---

## 타이포그래피 (Typography)

```tsx
import { TEXT_SIZES, TEXT_PRESETS } from "@/lib/typography";

export default function Example() {
  return (
    <div className="space-y-4">
      {/* 제목들 */}
      <h1 className={TEXT_SIZES.h1}>페이지 제목</h1>
      <h2 className={TEXT_SIZES.h2}>섹션 제목</h2>
      <h3 className={TEXT_SIZES.h3}>부섹션 제목</h3>

      {/* 본문 */}
      <p className={TEXT_SIZES.body}>본문 내용</p>
      <p className={TEXT_SIZES.bodySmall}>작은 본문 내용</p>

      {/* 보조 텍스트 */}
      <p className={TEXT_SIZES.caption}>캡션 텍스트</p>
      <p className={TEXT_SIZES.muted}>음소거 텍스트</p>

      {/* 상태 */}
      <p className={TEXT_SIZES.success}>성공 메시지</p>
      <p className={TEXT_SIZES.error}>에러 메시지</p>

      {/* 프리셋 (빠른 조합) */}
      <h1 className={TEXT_PRESETS.pageTitle}>페이지 제목</h1>
      <h2 className={TEXT_PRESETS.sectionTitle}>섹션 제목</h2>
      <p className={TEXT_PRESETS.paragraph}>일반 단락</p>
      <p className={TEXT_PRESETS.description}>설명 텍스트</p>
    </div>
  );
}
```

---

## 상태 배지 (Status Badge)

```tsx
export default function Example() {
  return (
    <div className="space-y-2">
      <p><span className="status-success">완료</span></p>
      <p><span className="status-warning">진행 중</span></p>
      <p><span className="status-error">오류</span></p>
      <p><span className="status-info">정보</span></p>
    </div>
  );
}
```

---

## 글로벌 클래스

### 카드 클래스

```css
.card           /* 카드 기본 스타일 */
.card-header    /* 헤더 */
.card-title     /* 제목 */
.card-subtitle  /* 부제목 */
.card-body      /* 본문 */
.card-footer    /* 푸터 */
```

### 버튼 클래스 (React 컴포넌트 권장)

```css
.btn-primary
.btn-secondary
.btn-danger
.btn-ghost
.btn-sm / .btn-md / .btn-lg / .btn-xl
```

### 상태 클래스

```css
.status-success   /* 초록색 배지 */
.status-warning   /* 노란색 배지 */
.status-error     /* 빨간색 배지 */
.status-info      /* 파란색 배지 */
```

---

## 마이그레이션 체크리스트

기존 컴포넌트를 새로운 UI 시스템으로 마이그레이션할 때:

- [ ] 버튼 → `<Button>` 컴포넌트로 변경
- [ ] 입력 필드 → `<TextInput>`, `<TextArea>`, `<Select>` 사용
- [ ] 카드 레이아웃 → `<Card>`, `<CardHeader>`, `<CardBody>`, `<CardFooter>` 사용
- [ ] 텍스트 스타일 → `TEXT_SIZES` 또는 `TEXT_PRESETS` 적용
- [ ] 상태 표시 → `.status-*` 클래스 사용
- [ ] 간격 → Tailwind `gap-md`, `p-lg` 등 사용
- [ ] 색상 → CSS 변수 또는 `text-[#...]` 사용

---

## 커스터마이징

### 버튼 커스터마이징

새로운 버튼 변형을 추가하려면 `globals.css`에 클래스를 추가하고,
`Button.tsx`의 `variantClasses`를 업데이트합니다:

```tsx
// Button.tsx
const variantClasses: Record<ButtonVariant, string> = {
  primary: "btn-primary",
  secondary: "btn-secondary",
  danger: "btn-danger",
  ghost: "btn-ghost",
  // 새로운 변형 추가
  outline: "btn-outline",
};
```

### 새로운 입력 필드 타입

새로운 입력 필드를 추가하려면 `FormField.tsx`에:

```tsx
interface EmailInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const EmailInput = React.forwardRef<HTMLInputElement, EmailInputProps>(
  ({ label, error, helperText, required, ...props }, ref) => (
    <FormField label={label} error={error} helperText={helperText} required={required}>
      <input ref={ref} type="email" {...props} />
    </FormField>
  )
);
EmailInput.displayName = "EmailInput";
```

