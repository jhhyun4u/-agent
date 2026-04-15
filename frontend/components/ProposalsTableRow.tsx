import Link from "next/link";
import { ProposalSummary } from "@/lib/api";
import {
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
  onClickRow?: (proposal: ProposalSummary) => void;
}

export function ProposalsTableRow({
  proposal: p,
  menuOpen,
  onMenuToggle,
  onMenuAction,
  onClickRow,
}: ProposalsTableRowProps) {
  const stepInfo = getStepInfo(p.current_phase);
  const dl = formatDeadline(p.deadline);
  const st = deriveStatus(p);

  // 적합도 점수 색상 코딩
  const fitScoreColor =
    p.fit_score !== null && p.fit_score !== undefined
      ? p.fit_score >= 70
        ? "text-[#3ecf8e]"
        : p.fit_score >= 50
          ? "text-yellow-400"
          : "text-[#5c5c5c]"
      : "text-[#5c5c5c]";

  // 작업대기 상태일 때는 모달을 열고, 아니면 상세페이지로 이동
  const isAwaitingStart = p.status === "initialized";
  const commonClassName = cn(
    `grid ${GRID_LAYOUT_CLASS} gap-3 px-4 py-3.5 border-b border-[#1a1a1a] last:border-0 hover:bg-[#161616] transition-colors items-center`,
    (p.status === "completed" || p.status === "closed" || p.status === "archived") && "opacity-60",
  );

  return (
    <div className={commonClassName}>
      {/* 상태 배지 */}
      <div className="flex justify-center">
        <span
          className={`px-2 py-1 rounded text-xs font-medium ${
            st.label === "결과대기"
              ? "bg-purple-500/15 text-purple-400"
              : st.label === "작업진행"
                ? "bg-[#3ecf8e]/15 text-[#3ecf8e]"
                : "bg-[#1c1c1c] text-[#8c8c8c]"
          }`}
        >
          {st.label}
        </span>
      </div>

      {/* 마감일 */}
      <span
        className={`text-xs text-center ${dl.urgent ? "text-red-400 font-semibold" : "text-[#5c5c5c]"}`}
      >
        {dl.text}
      </span>

      {/* 프로젝트명 */}
      <div className="min-w-0">
        <p className="text-sm text-[#ededed] truncate font-medium">{p.title}</p>
      </div>

      {/* 단계 */}
      <div className="flex flex-col gap-1">
        <span className="text-[11px] text-[#8c8c8c]">{stepInfo.label}</span>
        <div className="flex gap-0.5">
          {[1, 2, 3, 4, 5, 6, 7].map((s) => (
            <div
              key={s}
              className={`w-2.5 h-1 rounded-full ${
                s <= stepInfo.step ? "bg-[#3ecf8e]" : "bg-[#262626]"
              }`}
            />
          ))}
        </div>
      </div>

      {/* 적합도 점수 */}
      <span className={`text-xs font-medium text-center ${fitScoreColor}`}>
        {p.fit_score !== null && p.fit_score !== undefined ? `${p.fit_score}%` : "—"}
      </span>

      {/* 팀명 */}
      <span className="text-xs text-[#8c8c8c] truncate">
        {p.team_name || "미지정"}
      </span>

      {/* 담당자 */}
      <span className="text-xs text-[#8c8c8c] truncate">
        {p.owner_name || "미지정"}
      </span>

      {/* 발주처 */}
      <span className="text-xs text-[#8c8c8c] truncate">
        {p.client_name || "미지정"}
      </span>

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
            {p.status !== "completed" && p.status !== "closed" && p.status !== "archived" && p.status !== "expired" && (
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
    </div>
  );
}
