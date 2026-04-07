"use client";

/**
 * 원가 구조 카드 — 인건비/간접비/기술료/VAT 비율 표시
 */

import type { CostBreakdownDetail } from "@/lib/api";

interface Props {
  cost: CostBreakdownDetail;
}

export default function CostBreakdownCard({ cost }: Props) {
  const items = [
    {
      label: "직접인건비",
      value: cost.direct_labor_fmt,
      amount: cost.direct_labor,
    },
    { label: "간접비", value: cost.indirect_fmt, amount: cost.indirect_cost },
    { label: "기술료", value: cost.tech_fee_fmt, amount: cost.technical_fee },
    { label: "부가세", value: cost.vat_fmt, amount: cost.vat },
  ];
  const total = cost.total_cost || 1;

  return (
    <div className="rounded-lg border border-[#262626] bg-[#161616] p-4 space-y-3">
      <h3 className="text-sm font-medium text-[#ededed]">원가 구조</h3>

      {/* 스택바 */}
      <div className="flex h-3 rounded overflow-hidden">
        {items.map((item, i) => {
          const pct = (item.amount / total) * 100;
          const colors = [
            "bg-blue-500",
            "bg-cyan-500",
            "bg-purple-500",
            "bg-orange-500",
          ];
          return (
            <div
              key={i}
              className={`${colors[i]} transition-all`}
              style={{ width: `${pct}%` }}
              title={`${item.label}: ${pct.toFixed(1)}%`}
            />
          );
        })}
      </div>

      {/* 항목 목록 */}
      <div className="grid grid-cols-2 gap-2">
        {items.map((item, i) => {
          const dots = [
            "bg-blue-500",
            "bg-cyan-500",
            "bg-purple-500",
            "bg-orange-500",
          ];
          return (
            <div key={i} className="flex items-center gap-2 text-sm">
              <span className={`w-2 h-2 rounded-full ${dots[i]}`} />
              <span className="text-[#8c8c8c]">{item.label}</span>
              <span className="ml-auto text-[#ededed]">{item.value}</span>
            </div>
          );
        })}
      </div>

      <div className="border-t border-[#333] pt-2 flex justify-between text-sm font-medium">
        <span className="text-[#8c8c8c]">총원가</span>
        <span className="text-[#ededed]">{cost.total_cost_fmt}</span>
      </div>

      {/* 인력 상세 */}
      {cost.personnel_detail.length > 0 && (
        <details className="text-xs text-[#8c8c8c]">
          <summary className="cursor-pointer hover:text-[#ededed]">
            인력 상세 ({cost.personnel_detail.length}명)
          </summary>
          <div className="mt-2 space-y-1">
            {cost.personnel_detail.map((p, i) => (
              <div key={i} className="flex justify-between">
                <span>
                  {p.role} ({p.grade}) {p.person_months}M/M
                </span>
                <span>{p.amount_fmt}</span>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
