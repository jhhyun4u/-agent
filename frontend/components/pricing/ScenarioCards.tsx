"use client";

/**
 * 시나리오 비교 카드 — 보수적/균형/공격적
 */

import type { PricingScenario } from "@/lib/api";

interface Props {
  scenarios: PricingScenario[];
  selected?: string;
  onSelect?: (name: string) => void;
}

const RISK_COLORS: Record<string, string> = {
  low: "border-green-500/30 bg-green-500/5",
  medium: "border-blue-500/30 bg-blue-500/5",
  high: "border-orange-500/30 bg-orange-500/5",
};

const RISK_BADGES: Record<string, string> = {
  low: "text-green-400 bg-green-400/10",
  medium: "text-blue-400 bg-blue-400/10",
  high: "text-orange-400 bg-orange-400/10",
};

function fmtWon(amount: number): string {
  if (Math.abs(amount) >= 100_000_000) return `${(amount / 100_000_000).toFixed(1)}억원`;
  if (Math.abs(amount) >= 10_000) return `${(amount / 10_000).toFixed(0)}만원`;
  return `${amount.toLocaleString()}원`;
}

export default function ScenarioCards({ scenarios, selected, onSelect }: Props) {
  if (!scenarios.length) return null;

  return (
    <div className="rounded-lg border border-[#262626] bg-[#161616] p-4 space-y-3">
      <h3 className="text-sm font-medium text-[#ededed]">시나리오 비교</h3>
      <div className="grid grid-cols-3 gap-3">
        {scenarios.map((s) => {
          const isSelected = selected === s.name;
          return (
            <button
              key={s.name}
              onClick={() => onSelect?.(s.name)}
              className={`rounded-lg border p-3 text-left transition-all ${
                isSelected
                  ? "border-[#3ecf8e] bg-[#3ecf8e]/5 ring-1 ring-[#3ecf8e]/30"
                  : RISK_COLORS[s.risk_level] || RISK_COLORS.medium
              } hover:brightness-110`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-[#ededed]">{s.label}</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${RISK_BADGES[s.risk_level] || ""}`}>
                  {s.risk_level === "low" ? "저위험" : s.risk_level === "high" ? "고위험" : "중위험"}
                </span>
              </div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-[#8c8c8c]">낙찰률</span>
                  <span className="text-[#ededed] font-mono">{s.bid_ratio.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#8c8c8c]">입찰가</span>
                  <span className="text-[#ededed]">{fmtWon(s.bid_price)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#8c8c8c]">수주확률</span>
                  <span className="text-[#ededed] font-mono">{Math.round(s.win_probability * 100)}%</span>
                </div>
                {s.price_score_detail && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-[#8c8c8c]">가격점수</span>
                      <span className="text-[#ededed] font-mono">
                        {s.price_score_detail.price_score.toFixed(1)}/{s.price_score_detail.price_weight}점
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#8c8c8c]">예상총점</span>
                      <span className="text-[#ededed] font-mono font-medium">
                        {s.price_score_detail.total_score.toFixed(1)}점
                      </span>
                    </div>
                  </>
                )}
                <div className="flex justify-between border-t border-[#333] pt-1 mt-1">
                  <span className="text-[#8c8c8c]">기대수익</span>
                  <span className={`font-mono ${s.expected_payoff >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {fmtWon(s.expected_payoff)}
                  </span>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
