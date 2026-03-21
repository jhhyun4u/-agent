"use client";

/**
 * 시장 분석 요약 패널
 */

import type { MarketContext } from "@/lib/api";

interface Props {
  context: MarketContext;
}

export default function MarketContextPanel({ context }: Props) {
  return (
    <div className="rounded-lg border border-[#262626] bg-[#161616] p-4 space-y-3">
      <h3 className="text-sm font-medium text-[#ededed]">시장 컨텍스트</h3>

      <div className="grid grid-cols-3 gap-3">
        <div className="text-center">
          <div className="text-lg font-bold text-[#ededed]">
            {context.avg_bid_ratio != null
              ? `${(context.avg_bid_ratio * 100).toFixed(1)}%`
              : "-"}
          </div>
          <div className="text-xs text-[#8c8c8c]">평균 낙찰률</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-[#ededed]">
            {context.avg_num_bidders != null
              ? context.avg_num_bidders.toFixed(1)
              : "-"}
          </div>
          <div className="text-xs text-[#8c8c8c]">평균 참여업체</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-[#ededed]">{context.total_cases}</div>
          <div className="text-xs text-[#8c8c8c]">유사 사례</div>
        </div>
      </div>

      {/* 평가방식 분포 */}
      {Object.keys(context.evaluation_method_distribution).length > 0 && (
        <div>
          <div className="text-xs text-[#8c8c8c] mb-1">평가방식 분포</div>
          <div className="flex gap-2 flex-wrap">
            {Object.entries(context.evaluation_method_distribution).map(([method, count]) => (
              <span
                key={method}
                className="text-xs px-2 py-0.5 rounded bg-[#222] text-[#aaa] border border-[#333]"
              >
                {method} ({count})
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 예산 규모 분포 */}
      {Object.keys(context.budget_tier_distribution).length > 0 && (
        <div>
          <div className="text-xs text-[#8c8c8c] mb-1">예산 규모 분포</div>
          <div className="flex gap-2">
            {Object.entries(context.budget_tier_distribution).map(([tier, count]) => (
              <span
                key={tier}
                className="text-xs px-2 py-0.5 rounded bg-[#222] text-[#aaa] border border-[#333]"
              >
                {tier} ({count})
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
