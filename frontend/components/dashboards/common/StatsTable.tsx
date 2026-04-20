/**
 * StatsTable — 공용 통계 테이블 (Day 3 frontend, ~100줄)
 *
 * - 정렬 기능
 * - 페이지네이션
 * - 반응형
 * - 헤더/행 커스터마이징
 */

import { useState, useMemo } from "react";
import type { TableRow } from "@/lib/utils/dashboardTypes";

interface Column {
  key: string;
  header: string;
  sortable?: boolean;
  format?: (value: unknown) => string;
  align?: "left" | "right" | "center";
}

interface StatsTableProps {
  data: TableRow[];
  columns: Column[];
  pageSize?: number;
  striped?: boolean;
}

type SortDirection = "asc" | "desc" | null;

export function StatsTable({
  data,
  columns,
  pageSize = 10,
  striped = true,
}: StatsTableProps) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [currentPage, setCurrentPage] = useState(1);

  // ── 정렬 로직 ──

  const sortedData = useMemo(() => {
    if (!sortKey || !sortDirection) return data;

    return [...data].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (aVal === undefined || bVal === undefined) return 0;

      const aNum = typeof aVal === "number" ? aVal : parseFloat(String(aVal));
      const bNum = typeof bVal === "number" ? bVal : parseFloat(String(bVal));

      if (!isNaN(aNum) && !isNaN(bNum)) {
        return sortDirection === "asc" ? aNum - bNum : bNum - aNum;
      }

      return sortDirection === "asc"
        ? String(aVal).localeCompare(String(bVal))
        : String(bVal).localeCompare(String(aVal));
    });
  }, [data, sortKey, sortDirection]);

  // ── 페이지네이션 ──

  const totalPages = Math.ceil(sortedData.length / pageSize);
  const startIdx = (currentPage - 1) * pageSize;
  const endIdx = startIdx + pageSize;
  const pageData = sortedData.slice(startIdx, endIdx);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      if (sortDirection === "asc") {
        setSortDirection("desc");
      } else if (sortDirection === "desc") {
        setSortKey(null);
        setSortDirection(null);
      }
    } else {
      setSortKey(key);
      setSortDirection("asc");
      setCurrentPage(1);
    }
  };

  // ── 렌더 ──

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          {/* 헤더 */}
          <thead>
            <tr className="text-[#8c8c8c] border-b border-[#262626]">
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() =>
                    col.sortable && handleSort(col.key)
                  }
                  className={`py-3 px-4 text-left font-medium ${
                    col.sortable ? "cursor-pointer hover:text-[#ededed]" : ""
                  }`}
                  style={{
                    textAlign: col.align || "left",
                  }}
                >
                  <div className="flex items-center gap-1.5">
                    <span>{col.header}</span>
                    {col.sortable && sortKey === col.key && sortDirection && (
                      <span className="text-[#3ecf8e]">
                        {sortDirection === "asc" ? "▲" : "▼"}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          {/* 본문 */}
          <tbody>
            {pageData.map((row, idx) => (
              <tr
                key={idx}
                className={`border-b border-[#1a1a1a] ${
                  striped && idx % 2 === 0
                    ? "bg-[#111111]"
                    : "hover:bg-[#111111]"
                } transition-colors`}
              >
                {columns.map((col) => {
                  const value = row[col.key];
                  const formatted = col.format ? col.format(value) : value;

                  return (
                    <td
                      key={col.key}
                      className="py-3 px-4 text-[#ededed]"
                      style={{
                        textAlign: col.align || "left",
                      }}
                    >
                      {formatted}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-[10px] text-[#8c8c8c]">
            전체 {sortedData.length}건 중 {startIdx + 1}-
            {Math.min(endIdx, sortedData.length)}건 표시
          </p>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage(1)}
              disabled={currentPage === 1}
              className="p-1.5 rounded-lg text-[#8c8c8c] hover:bg-[#262626] disabled:opacity-30"
            >
              처음
            </button>

            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="p-1.5 rounded-lg text-[#8c8c8c] hover:bg-[#262626] disabled:opacity-30"
            >
              이전
            </button>

            {Array.from({ length: Math.min(3, totalPages) }, (_, i) => {
              const pageNum =
                totalPages <= 3
                  ? i + 1
                  : currentPage <= 2
                    ? i + 1
                    : Math.max(currentPage - 1 + i - 1, 1);
              return (
                pageNum <= totalPages && (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`w-6 h-6 rounded-lg text-[10px] font-medium transition-colors ${
                      currentPage === pageNum
                        ? "bg-[#3ecf8e] text-[#0f0f0f]"
                        : "text-[#8c8c8c] hover:bg-[#262626]"
                    }`}
                  >
                    {pageNum}
                  </button>
                )
              );
            })}

            <button
              onClick={() =>
                setCurrentPage(Math.min(totalPages, currentPage + 1))
              }
              disabled={currentPage === totalPages}
              className="p-1.5 rounded-lg text-[#8c8c8c] hover:bg-[#262626] disabled:opacity-30"
            >
              다음
            </button>

            <button
              onClick={() => setCurrentPage(totalPages)}
              disabled={currentPage === totalPages}
              className="p-1.5 rounded-lg text-[#8c8c8c] hover:bg-[#262626] disabled:opacity-30"
            >
              마지막
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
