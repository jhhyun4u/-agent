import { TABLE_COLUMNS, GRID_LAYOUT_CLASS } from "@/lib/proposals-utils";

interface ProposalsTableHeaderProps {
  sortKey: "deadline" | "step" | "created_at" | null;
  sortAsc: boolean;
  onSort: (key: "deadline" | "step" | "created_at" | null) => void;
}

export function ProposalsTableHeader({
  sortKey,
  sortAsc,
  onSort,
}: ProposalsTableHeaderProps) {
  return (
    <div
      className={`grid ${GRID_LAYOUT_CLASS} gap-3 px-4 py-2.5 border-b border-[#262626] bg-[#0f0f0f]`}
    >
      {TABLE_COLUMNS.map((col) => (
        <div key={col.key} style={{ textAlign: col.align as any }}>
          {col.sortable ? (
            <button
              onClick={() => onSort(col.key as any)}
              className={`text-xs font-medium uppercase tracking-wider transition-colors ${
                sortKey === col.key
                  ? "text-[#ededed]"
                  : "text-[#5c5c5c] hover:text-[#8c8c8c]"
              }`}
            >
              {col.label} {sortKey === col.key ? (sortAsc ? "↑" : "↓") : ""}
            </button>
          ) : (
            <span className="text-xs font-medium text-[#5c5c5c] uppercase tracking-wider">
              {col.label}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
