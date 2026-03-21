"use client";

/**
 * 시뮬레이션 이력 페이지
 *
 * /pricing/history
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { pricingApi, type PricingSimulationSummary } from "@/lib/api";

function fmtWon(amount: number): string {
  if (amount >= 100_000_000) return `${(amount / 100_000_000).toFixed(1)}억`;
  if (amount >= 10_000) return `${Math.round(amount / 10_000).toLocaleString()}만`;
  return `${amount.toLocaleString()}`;
}

const POS_LABELS: Record<string, string> = {
  defensive: "수성",
  offensive: "공격",
  adjacent: "인접",
};

export default function PricingHistoryPage() {
  const [items, setItems] = useState<PricingSimulationSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await pricingApi.getPricingSimulations();
      setItems(res.items || []);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="max-w-5xl mx-auto px-6 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[#ededed]">시뮬레이션 이력</h1>
          <p className="text-sm text-[#8c8c8c] mt-0.5">과거 가격 시뮬레이션 결과를 확인합니다</p>
        </div>
        <Link
          href="/pricing"
          className="text-sm text-[#3ecf8e] hover:underline"
        >
          새 시뮬레이션
        </Link>
      </div>

      {loading ? (
        <div className="text-sm text-[#8c8c8c] animate-pulse">불러오는 중...</div>
      ) : items.length === 0 ? (
        <div className="rounded-lg border border-[#262626] bg-[#161616] p-8 text-center text-[#8c8c8c]">
          <p className="text-sm">시뮬레이션 이력이 없습니다</p>
        </div>
      ) : (
        <div className="rounded-lg border border-[#262626] bg-[#161616] overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#262626] text-[#8c8c8c] text-xs">
                <th className="px-4 py-2.5 text-left">일시</th>
                <th className="px-4 py-2.5 text-left">도메인</th>
                <th className="px-4 py-2.5 text-right">예산</th>
                <th className="px-4 py-2.5 text-left">방식</th>
                <th className="px-4 py-2.5 text-left">포지셔닝</th>
                <th className="px-4 py-2.5 text-left">시나리오</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.id}
                  className="border-b border-[#1c1c1c] hover:bg-[#1a1a1a] transition-colors"
                >
                  <td className="px-4 py-2.5 text-[#8c8c8c]">
                    {item.created_at ? new Date(item.created_at).toLocaleDateString("ko-KR") : "-"}
                  </td>
                  <td className="px-4 py-2.5 text-[#ededed]">{item.domain || "-"}</td>
                  <td className="px-4 py-2.5 text-right text-[#ededed] font-mono">
                    {item.budget ? fmtWon(item.budget) : "-"}
                  </td>
                  <td className="px-4 py-2.5 text-[#8c8c8c]">{item.evaluation_method || "-"}</td>
                  <td className="px-4 py-2.5">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-[#222] text-[#aaa]">
                      {POS_LABELS[item.positioning] || item.positioning || "-"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-[#8c8c8c]">
                    {item.selected_scenario || "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
