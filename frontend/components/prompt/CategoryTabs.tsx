"use client";

/**
 * CategoryTabs — 6개 카테고리 필터 탭
 *
 * 프롬프트 카탈로그 페이지에서 카테고리별 필터링에 사용.
 */

import type { PromptCategory } from "@/lib/api";

const CAT_STYLE: Record<string, { emoji: string; color: string }> = {
  bid_analysis: { emoji: "A", color: "#60a5fa" },
  strategy: { emoji: "B", color: "#f59e0b" },
  planning: { emoji: "C", color: "#34d399" },
  proposal_writing: { emoji: "D", color: "#a78bfa" },
  presentation: { emoji: "E", color: "#f472b6" },
  quality_assurance: { emoji: "F", color: "#6ee7b7" },
};

interface CategoryTabsProps {
  categories: PromptCategory[];
  activeCategory: string;
  onSelect: (categoryId: string) => void;
  totalPrompts: number;
}

export default function CategoryTabs({
  categories,
  activeCategory,
  onSelect,
  totalPrompts,
}: CategoryTabsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onSelect("all")}
        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
          activeCategory === "all"
            ? "bg-[#3ecf8e] text-black"
            : "bg-[#1c1c1c] text-[#8c8c8c] hover:bg-[#262626]"
        }`}
      >
        전체 {totalPrompts}
      </button>
      {categories.map((cat) => {
        const style = CAT_STYLE[cat.id];
        return (
          <button
            key={cat.id}
            onClick={() => onSelect(cat.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
              activeCategory === cat.id
                ? "bg-[#262626] text-[#ededed] border border-[#444]"
                : "bg-[#1c1c1c] text-[#8c8c8c] hover:bg-[#262626] border border-transparent"
            }`}
          >
            <span
              className="inline-flex w-4 h-4 rounded text-[10px] font-bold items-center justify-center"
              style={{ backgroundColor: style?.color ?? "#666", color: "#000" }}
            >
              {style?.emoji ?? "?"}
            </span>
            {cat.label} {cat.prompt_count}
          </button>
        );
      })}
    </div>
  );
}

export { CAT_STYLE };
