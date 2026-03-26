"use client";

/**
 * 노임단가 관리 페이지 (§13-13)
 *
 * /kb/labor-rates
 * labor_rates 테이블 CRUD (기관/연도/등급/단가/출처)
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, type LaborRate } from "@/lib/api";
import DataTable, { type Column, type Filter } from "@/components/DataTable";

const COLUMNS: Column<LaborRate>[] = [
  { key: "agency", label: "기관", width: "20%" },
  { key: "year", label: "연도", width: "10%", type: "number" },
  { key: "grade", label: "등급", width: "20%" },
  {
    key: "monthly_rate",
    label: "단가 (만원)",
    width: "15%",
    type: "number",
    render: (v) => `${Number(v).toLocaleString()}만`,
  },
  { key: "source", label: "출처", width: "15%" },
  {
    key: "updated_at",
    label: "갱신일",
    width: "15%",
    editable: false,
    render: (v) => (v ? new Date(String(v)).toLocaleDateString("ko-KR") : "-"),
  },
];

const FILTERS: Filter[] = [
  {
    key: "agency",
    label: "기관",
    options: [
      { value: "한국SW산업협회", label: "한국SW산업협회" },
      { value: "기재부", label: "기재부" },
      { value: "과기부", label: "과기부" },
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

export default function LaborRatesPage() {
  const [data, setData] = useState<LaborRate[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.kb.laborRates.list(filterValues);
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
    await api.kb.laborRates.create(row as Omit<LaborRate, "id" | "created_at" | "updated_at">);
    fetchData();
  }

  async function handleEdit(id: string, row: Record<string, unknown>) {
    await api.kb.laborRates.update(id, row as Partial<LaborRate>);
    fetchData();
  }

  async function handleDelete(id: string) {
    await api.kb.laborRates.delete(id);
    fetchData();
  }

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-[#ededed]">
      <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 sticky top-0 z-20">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <Link href="/dashboard" className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors">
            ← 대시보드
          </Link>
          <h1 className="text-sm font-semibold text-[#ededed]">원가기준 (노임단가)</h1>
          <div className="flex-1" />
          <Link
            href="/kb/market-prices"
            className="text-xs text-[#8c8c8c] hover:text-[#3ecf8e] transition-colors"
          >
            낙찰가 벤치마크 →
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
          <DataTable<LaborRate>
            title="노임단가"
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
