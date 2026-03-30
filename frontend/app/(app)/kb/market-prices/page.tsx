"use client";

/**
 * 낙찰가 벤치마크 관리 페이지 (§13-13)
 *
 * /kb/market-prices
 * market_price_data 테이블 CRUD (도메인/예산범위/낙찰률/출처)
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, type MarketPrice } from "@/lib/api";
import DataTable, { type Column, type Filter } from "@/components/DataTable";

const COLUMNS: Column<MarketPrice>[] = [
  { key: "domain", label: "도메인", width: "20%" },
  { key: "budget_range", label: "예산 범위", width: "15%" },
  {
    key: "win_rate",
    label: "낙찰률 (%)",
    width: "12%",
    type: "number",
    render: (v) => `${Number(v).toFixed(1)}%`,
  },
  {
    key: "avg_bid_rate",
    label: "평균 투찰률 (%)",
    width: "12%",
    type: "number",
    render: (v) => `${Number(v).toFixed(1)}%`,
  },
  { key: "source", label: "출처", width: "15%" },
  { key: "year", label: "연도", width: "10%", type: "number" },
  {
    key: "updated_at",
    label: "갱신일",
    width: "12%",
    editable: false,
    render: (v) => (v ? new Date(String(v)).toLocaleDateString("ko-KR") : "-"),
  },
];

const FILTERS: Filter[] = [
  {
    key: "domain",
    label: "도메인",
    options: [
      { value: "SI", label: "SI" },
      { value: "SM", label: "SM" },
      { value: "컨설팅", label: "컨설팅" },
      { value: "AI/빅데이터", label: "AI/빅데이터" },
      { value: "클라우드", label: "클라우드" },
    ],
  },
  {
    key: "year",
    label: "연도",
    options: [
      { value: "2026", label: "2026" },
      { value: "2025", label: "2025" },
      { value: "2024", label: "2024" },
    ],
  },
];

export default function MarketPricesPage() {
  const [data, setData] = useState<MarketPrice[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.kb.marketPrices.list(filterValues);
      setData(res.data);
    } catch {
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [filterValues]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  function handleFilterChange(key: string, value: string) {
    setFilterValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleAdd(row: Record<string, unknown>) {
    await api.kb.marketPrices.create(row as Omit<MarketPrice, "id" | "created_at" | "updated_at">);
    fetchData();
  }

  async function handleEdit(id: string, row: Record<string, unknown>) {
    await api.kb.marketPrices.update(id, row as Partial<MarketPrice>);
    fetchData();
  }

  async function handleDelete(id: string) {
    await api.kb.marketPrices.delete(id);
    fetchData();
  }

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-[#ededed]">
      <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 sticky top-0 z-20">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <Link href="/dashboard" className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors">
            ← 대시보드
          </Link>
          <h1 className="text-sm font-semibold text-[#ededed]">낙찰가 벤치마크</h1>
          <div className="flex-1" />
          <Link
            href="/kb/labor-rates"
            className="text-xs text-[#8c8c8c] hover:text-[#3ecf8e] transition-colors"
          >
            ← 원가기준
          </Link>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-6">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-[#8c8c8c] text-sm">
            <div className="w-5 h-5 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin mr-3" />
            불러오는 중...
          </div>
        ) : (
          <DataTable<MarketPrice>
            title="낙찰가 벤치마크"
            columns={COLUMNS}
            data={data}
            filters={FILTERS}
            filterValues={filterValues}
            onFilterChange={handleFilterChange}
            onAdd={handleAdd}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        )}
      </main>
    </div>
  );
}
