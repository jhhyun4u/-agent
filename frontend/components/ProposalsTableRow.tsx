import Link from "next/link";
import { ProposalSummary } from "@/lib/api";
import {
  POS_LABELS,
  getStepInfo,
  formatDeadline,
  formatBudgetCompact,
  deriveStatus,
  GRID_LAYOUT_CLASS,
} from "@/lib/proposals-utils";
import { cn } from "@/lib/utils";

interface ProposalsTableRowProps {
  proposal: ProposalSummary;
  menuOpen: string | null;
  onMenuToggle: (id: string) => void;
  onMenuAction: (id: string, action: "view" | "resume" | "delete") => void;
}

export function ProposalsTableRow({
  proposal: p,
  menuOpen,
  onMenuToggle,
  onMenuAction,
}: ProposalsTableRowProps) {
  const pos = p.positioning ? POS_LABELS[p.positioning as keyof typeof POS_LABELS] : null;
  const stepInfo = getStepInfo(p.current_phase);
  const dl = formatDeadline(p.deadline);
  const st = deriveStatus(p);

  return (
    <Link
      href={`/proposals/${p.id}`}
      className={cn(
        `grid ${GRID_LAYOUT_CLASS} gap-3 px-4 py-3.5 border-b border-[#1a1a1a] last:border-0 hover:bg-[#161616] transition-colors items-center`,
        (p.status === "completed" || p.status === "failed" || p.win_result === "no_go") &&
          "opacity-60",
      )}
    >
      {/* 프로젝트명 */}
      <div className="min-w-0">
        <p className="text-sm text-[#ededed] truncate font-medium">{p.title}</p>
        <p className="text-xs text-[#5c5c5c] mt-0.5 truncate">
          {p.win_result &&
            p.win_result !== "no_go" &&
            p.win_result !== "not_interested" && (
              <span className="text-[#8c8c8c]">
                {p.win_result === "won"
                  ? "수주"
                  : p.win_result === "lost"
                    ? "낙찰 실패"
                    : "결과 대기"}
              </span>
            )}
        </p>
      </div>

      {/* 포지셔닝 */}
      <span className={`text-xs font-medium ${pos?.color ?? "text-[#3c3c3c]"}`}>
        {pos ? `${pos.icon} ${pos.label}` : "—"}
      </span>

      {/* 단계 */}
      <div className="flex flex-col gap-1">
        <span className="text-[11px] text-[#8c8c8c]">{stepInfo.label}</span>
        <div className="flex gap-0.5">
          {[1, 2, 3, 4, 5].map((s) => (
            <div
              key={s}
              className={`w-3 h-1 rounded-full ${
                s <= stepInfo.step ? "bg-[#3ecf8e]" : "bg-[#262626]"
              }`}
            />
          ))}
        </div>
      </div>

      {/* 예정가 */}
      <span className="text-xs text-right text-[#8c8c8c]">
        {formatBudgetCompact(p.budget)}
      </span>

      {/* 입찰가 */}
      <span className="text-xs text-right font-medium">
        {p.bid_amount ? (
          <span className="text-[#3ecf8e]">{formatBudgetCompact(p.bid_amount)}</span>
        ) : (
          <span className="text-[#5c5c5c]">미결정</span>
        )}
      </span>

      {/* 마감일 */}
      <span className={`text-xs ${dl.urgent ? "text-red-400 font-semibold" : "text-[#5c5c5c]"}`}>
        {dl.text}
      </span>

      {/* 발주처 */}
      <span className="text-xs text-[#5c5c5c] truncate">{p.client_name || "미지정"}</span>

      {/* 상태 */}
      <span className="flex items-center gap-1.5" title={st.tooltip}>
        <span className={`w-2 h-2 rounded-full shrink-0 ${st.dotColor}`} />
        <span className={`text-xs font-medium ${st.textColor}`}>{st.label}</span>
      </span>

      {/* 메뉴 */}
      <div className="relative">
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onMenuToggle(p.id);
          }}
          className="w-7 h-7 flex items-center justify-center rounded-md text-[#5c5c5c] hover:text-[#ededed] hover:bg-[#1c1c1c] transition-colors"
        >
          ⋯
        </button>
        {menuOpen === p.id && (
          <div className="absolute right-0 top-8 z-50 bg-[#1c1c1c] border border-[#262626] rounded-lg shadow-xl py-1 min-w-[140px] animate-in fade-in slide-in-from-top-1 duration-150">
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onMenuAction(p.id, "view");
              }}
              className="w-full px-3 py-1.5 text-xs text-[#ededed] hover:bg-[#262626] text-left transition-colors"
            >
              상세 보기
            </button>
            {p.status !== "completed" && p.status !== "failed" && (
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  onMenuAction(p.id, "resume");
                }}
                className="w-full px-3 py-1.5 text-xs text-[#ededed] hover:bg-[#262626] text-left transition-colors"
              >
                워크플로 재개
              </button>
            )}
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onMenuAction(p.id, "delete");
              }}
              className="w-full px-3 py-1.5 text-xs text-red-400 hover:bg-red-950/30 text-left transition-colors"
            >
              삭제
            </button>
          </div>
        )}
      </div>
    </Link>
  );
}
