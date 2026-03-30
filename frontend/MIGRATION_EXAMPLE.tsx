/**
 * UI 컴포넌트 마이그레이션 예시
 * 
 * 이 파일은 실제 구현이 아니며, 기존 코드를 새로운 UI 시스템으로
 * 어떻게 마이그레이션하는지 보여주는 참고용입니다.
 */

// ── 이전 코드 (마이그레이션 전) ──
export const OldDashboard = () => {
  return (
    <div className="p-6 space-y-4">
      {/* 구식 카드 */}
      <div className="bg-[#1c1c1c] border border-[#262626] rounded-lg p-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#262626]">
          <h3 className="text-lg font-semibold">제목</h3>
          <button className="px-4 py-2 bg-[#3ecf8e] text-[#0f0f0f] rounded-lg hover:bg-[#34b87a]">
            편집
          </button>
        </div>
        <div className="pt-4">
          <p>내용</p>
        </div>
      </div>

      {/* 구식 폼 */}
      <form className="space-y-4">
        <div>
          <label className="text-sm font-medium">이름</label>
          <input 
            type="text" 
            placeholder="이름 입력"
            className="w-full mt-1 bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-[#ededed]"
          />
        </div>
      </form>
    </div>
  );
};

// ── 새로운 코드 (마이그레이션 후) ──
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { TextInput } from "@/components/ui/FormField";
import { TEXT_SIZES, TEXT_PRESETS } from "@/lib/typography";

export const NewDashboard = () => {
  const [formData, setFormData] = React.useState({ name: "" });

  return (
    <div className="p-lg space-y-lg">
      {/* 새로운 카드 */}
      <Card>
        <CardHeader 
          title="제목"
          action={<Button size="sm" variant="primary">편집</Button>}
        />
        <CardBody>
          <p className={TEXT_SIZES.body}>내용</p>
        </CardBody>
      </Card>

      {/* 새로운 폼 */}
      <form className="space-y-md">
        <TextInput
          label="이름"
          placeholder="이름 입력"
          required
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        />
        
        <div className="flex gap-md">
          <Button type="submit" variant="primary">
            저장
          </Button>
          <Button type="reset" variant="secondary">
            취소
          </Button>
        </div>
      </form>
    </div>
  );
};

// ── 마이그레이션 팁 ──
/**
 * 1. 일관된 간격 사용
 * 
 * Before:
 * <div className="p-4 space-y-4">
 * 
 * After:
 * <div className="p-md space-y-md">
 * 
 * Tailwind에서 제공하는 기본 간격 대신 새로운 시스템 사용:
 * - xs (6px), sm (8px), md (16px), lg (24px), xl (32px)
 */

/**
 * 2. 타이포그래피 표준화
 * 
 * Before:
 * <h1 className="text-3xl font-bold">제목</h1>
 * <p className="text-sm leading-6">본문</p>
 * 
 * After:
 * <h1 className={TEXT_SIZES.h1}>제목</h1>
 * <p className={TEXT_SIZES.body}>본문</p>
 */

/**
 * 3. 버튼 표준화
 * 
 * Before:
 * <button className="px-4 py-2 bg-[#3ecf8e] text-[#0f0f0f] rounded-lg">
 * 
 * After:
 * <Button variant="primary" size="md">
 */

/**
 * 4. 카드 구조 통일
 * 
 * Before:
 * <div className="bg-[#1c1c1c] border border-[#262626] rounded-lg p-4">
 *   <div className="border-b pb-3">헤더</div>
 *   <div className="pt-4">본문</div>
 * </div>
 * 
 * After:
 * <Card>
 *   <CardHeader title="..." />
 *   <CardBody>...</CardBody>
 * </Card>
 */

/**
 * 5. 입력 필드 통일
 * 
 * Before:
 * <input className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2" />
 * 
 * After:
 * <TextInput label="..." />
 */
