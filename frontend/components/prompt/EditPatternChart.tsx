"use client";

/**
 * EditPatternChart — 수정 패턴 수평 막대 차트
 *
 * "사람이 어떤 종류의 수정을 많이 하는가"를 시각화.
 */

interface EditPattern {
  pattern: string;
  count: number;
  pct?: number;
}

interface EditPatternChartProps {
  patterns: EditPattern[];
  maxItems?: number;
}

export default function EditPatternChart({ patterns, maxItems = 5 }: EditPatternChartProps) {
  if (!patterns.length) {
    return <div className="text-xs text-[#8c8c8c]">수정 패턴 데이터 없음</div>;
  }

  const items = patterns.slice(0, maxItems);
  const maxCount = Math.max(...items.map((p) => p.count));

  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold">사람 수정 패턴 TOP {items.length}</h3>
      {items.map((p, i) => {
        const barPct = (p.count / maxCount) * 100;
        return (
          <div key={p.pattern} className="flex items-center gap-2 text-xs">
            <span className="w-4 text-[#8c8c8c]">{i + 1}.</span>
            <span className="w-40 truncate text-[#ededed]">{p.pattern}</span>
            <div className="flex-1 h-3 bg-[#1a1a1a] rounded-full overflow-hidden">
              <div
                className="h-full bg-[#f5a623] rounded-full"
                style={{ width: `${barPct}%` }}
              />
            </div>
            <span className="w-10 text-right text-[#f5a623]">{p.count}건</span>
          </div>
        );
      })}
    </div>
  );
}
