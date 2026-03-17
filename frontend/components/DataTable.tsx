"use client";

/**
 * DataTable — 범용 CRUD 테이블 (§13-13)
 *
 * 필터, 정렬, 행 추가/편집/삭제 지원
 */

import { useState } from "react";

// ── 타입 ──

export interface Column<T> {
  key: keyof T & string;
  label: string;
  width?: string;
  render?: (value: unknown, row: T) => React.ReactNode;
  editable?: boolean;
  type?: "text" | "number" | "select";
  options?: string[]; // select 옵션
}

export interface Filter {
  key: string;
  label: string;
  options: Array<{ value: string; label: string }>;
}

interface DataTableProps<T extends { id: string }> {
  title: string;
  columns: Column<T>[];
  data: T[];
  filters?: Filter[];
  filterValues?: Record<string, string>;
  onFilterChange?: (key: string, value: string) => void;
  onAdd?: (row: Record<string, unknown>) => Promise<void>;
  onEdit?: (id: string, row: Record<string, unknown>) => Promise<void>;
  onDelete?: (id: string) => Promise<void>;
  className?: string;
}

export default function DataTable<T extends { id: string }>({
  title,
  columns,
  data,
  filters = [],
  filterValues = {},
  onFilterChange,
  onAdd,
  onEdit,
  onDelete,
  className = "",
}: DataTableProps<T>) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<Record<string, unknown>>({});
  const [addingRow, setAddingRow] = useState(false);
  const [newRow, setNewRow] = useState<Record<string, unknown>>({});
  const [submitting, setSubmitting] = useState(false);

  // 편집 시작
  function startEdit(row: T) {
    setEditingId(row.id);
    const vals: Record<string, unknown> = {};
    for (const col of columns) {
      vals[col.key] = row[col.key];
    }
    setEditValues(vals);
  }

  // 편집 저장
  async function saveEdit() {
    if (!editingId || !onEdit) return;
    setSubmitting(true);
    try {
      await onEdit(editingId, editValues);
      setEditingId(null);
    } catch (e) {
      alert(e instanceof Error ? e.message : "저장 실패");
    } finally {
      setSubmitting(false);
    }
  }

  // 행 추가
  async function saveAdd() {
    if (!onAdd) return;
    setSubmitting(true);
    try {
      await onAdd(newRow);
      setAddingRow(false);
      setNewRow({});
    } catch (e) {
      alert(e instanceof Error ? e.message : "등록 실패");
    } finally {
      setSubmitting(false);
    }
  }

  // 행 삭제
  async function handleDelete(id: string) {
    if (!onDelete || !confirm("삭제하시겠습니까?")) return;
    try {
      await onDelete(id);
    } catch (e) {
      alert(e instanceof Error ? e.message : "삭제 실패");
    }
  }

  return (
    <div className={`bg-[#1c1c1c] rounded-2xl border border-[#262626] overflow-hidden ${className}`}>
      {/* 헤더 */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-[#262626]">
        <h2 className="text-sm font-semibold text-[#ededed]">{title}</h2>
        {onAdd && (
          <button
            onClick={() => { setAddingRow(true); setNewRow({}); }}
            className="text-xs font-medium text-[#3ecf8e] hover:text-[#3ecf8e]/80 transition-colors"
          >
            + 등록
          </button>
        )}
      </div>

      {/* 필터 */}
      {filters.length > 0 && (
        <div className="flex items-center gap-3 px-5 py-2 border-b border-[#262626] bg-[#111111]">
          {filters.map((f) => (
            <div key={f.key} className="flex items-center gap-1.5">
              <span className="text-[10px] text-[#8c8c8c]">{f.label}:</span>
              <select
                value={filterValues[f.key] ?? ""}
                onChange={(e) => onFilterChange?.(f.key, e.target.value)}
                className="bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-[10px] text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]"
              >
                <option value="">전체</option>
                {f.options.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          ))}
        </div>
      )}

      {/* 테이블 */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[#262626]">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="text-left px-4 py-2.5 text-[10px] text-[#8c8c8c] uppercase tracking-wider font-medium"
                  style={col.width ? { width: col.width } : undefined}
                >
                  {col.label}
                </th>
              ))}
              {(onEdit || onDelete) && (
                <th className="text-right px-4 py-2.5 text-[10px] text-[#8c8c8c] uppercase tracking-wider font-medium w-24">
                  작업
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {/* 추가 행 */}
            {addingRow && (
              <tr className="border-b border-[#262626] bg-[#3ecf8e]/5">
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-2">
                    <CellInput
                      column={col}
                      value={newRow[col.key] ?? ""}
                      onChange={(v) => setNewRow((r) => ({ ...r, [col.key]: v }))}
                    />
                  </td>
                ))}
                <td className="px-4 py-2 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={saveAdd}
                      disabled={submitting}
                      className="text-[10px] text-[#3ecf8e] hover:underline disabled:opacity-40"
                    >
                      저장
                    </button>
                    <button
                      onClick={() => setAddingRow(false)}
                      className="text-[10px] text-[#8c8c8c] hover:underline"
                    >
                      취소
                    </button>
                  </div>
                </td>
              </tr>
            )}

            {/* 데이터 행 */}
            {data.map((row) => (
              <tr key={row.id} className="border-b border-[#262626] hover:bg-[#262626]/30 transition-colors">
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-2.5 text-[#ededed]">
                    {editingId === row.id && col.editable !== false ? (
                      <CellInput
                        column={col}
                        value={editValues[col.key] ?? ""}
                        onChange={(v) => setEditValues((ev) => ({ ...ev, [col.key]: v }))}
                      />
                    ) : col.render ? (
                      col.render(row[col.key], row)
                    ) : (
                      String(row[col.key] ?? "")
                    )}
                  </td>
                ))}
                {(onEdit || onDelete) && (
                  <td className="px-4 py-2.5 text-right">
                    {editingId === row.id ? (
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={saveEdit} disabled={submitting} className="text-[10px] text-[#3ecf8e] hover:underline disabled:opacity-40">저장</button>
                        <button onClick={() => setEditingId(null)} className="text-[10px] text-[#8c8c8c] hover:underline">취소</button>
                      </div>
                    ) : (
                      <div className="flex items-center justify-end gap-1">
                        {onEdit && <button onClick={() => startEdit(row)} className="text-[10px] text-[#8c8c8c] hover:text-[#ededed]">수정</button>}
                        {onDelete && <button onClick={() => handleDelete(row.id)} className="text-[10px] text-red-400/70 hover:text-red-400">삭제</button>}
                      </div>
                    )}
                  </td>
                )}
              </tr>
            ))}

            {data.length === 0 && !addingRow && (
              <tr>
                <td colSpan={columns.length + 1} className="px-4 py-8 text-center text-[#5c5c5c]">
                  데이터가 없습니다.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── 셀 입력 ──

function CellInput<T>({
  column,
  value,
  onChange,
}: {
  column: Column<T>;
  value: unknown;
  onChange: (value: unknown) => void;
}) {
  if (column.type === "select" && column.options) {
    return (
      <select
        value={String(value)}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-[#111111] border border-[#262626] rounded px-2 py-1 text-[10px] text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]"
      >
        <option value="">선택...</option>
        {column.options.map((opt) => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    );
  }

  return (
    <input
      type={column.type === "number" ? "number" : "text"}
      value={String(value)}
      onChange={(e) => onChange(column.type === "number" ? Number(e.target.value) : e.target.value)}
      className="w-full bg-[#111111] border border-[#262626] rounded px-2 py-1 text-[10px] text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]"
    />
  );
}
