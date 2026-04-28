"use client";

/**
 * TodayActionHub — 대시보드 상단 "오늘 할 일" 허브
 *
 * 우선순위: 검토 대기 → D-7 마감 → AI 작업중 → 시작 전
 */

import { useRouter } from "next/navigation";
import type { ProposalSummary, CalendarItem } from "@/lib/api";

interface Props {
  proposals: ProposalSummary[];
  calItems: CalendarItem[];
}

// ── 리뷰 게이트 라벨 ──────────────────────────────────────────────────
const REVIEW_LABELS: Record<string, string> = {
  review_search: "공고 검색 검토",
  review_rfp: "RFP 분석 검토",
  review_gng: "Go/No-Go 의사결정",
  review_strategy: "제안전략 검토",
  review_bid_plan: "입찰가격 계획 검토",
  review_plan: "제안계획서 검토",
  review_section: "섹션별 검토",
  review_gap_analysis: "갭 분석 검토",
  review_proposal: "제안서 최종 검토",
  review_ppt: "PPT 검토",
};

// ── 유틸 ─────────────────────────────────────────────────────────────
function calcDDay(iso: string): number {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const d = new Date(iso);
  d.setHours(0, 0, 0, 0);
  return Math.ceil((d.getTime() - now.getTime()) / 86_400_000);
}

function dDayLabel(days: number): string {
  if (days === 0) return "D-Day";
  if (days < 0) return `D+${Math.abs(days)}`;
  return `D-${days}`;
}

// ── 액션 아이템 타입 ───────────────────────────────────────────────────
type ReviewAction  = { kind: "review";   proposal: ProposalSummary; reviewLabel: string };
type DeadlineAction= { kind: "deadline"; cal: CalendarItem; days: number };
type RunningAction = { kind: "running";  proposal: ProposalSummary };
type InitAction    = { kind: "init";     proposal: ProposalSummary };
type Action = ReviewAction | DeadlineAction | RunningAction | InitAction;

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────
export default function TodayActionHub({ proposals, calItems }: Props) {
  const router = useRouter();

  // ── 액션 아이템 수집 ──────────────────────────────────────────────
  const actions: Action[] = [];

  // 1순위: 내 검토가 필요한 제안서 (waiting + 리뷰 게이트)
  for (const p of proposals) {
    if (p.status === "waiting" && p.current_phase) {
      const reviewLabel = REVIEW_LABELS[p.current_phase];
      if (reviewLabel) {
        actions.push({ kind: "review", proposal: p, reviewLabel });
      }
    }
  }

  // 2순위: D-7 이내 마감 일정 (제안서 없는 공고)
  const now7 = calItems
    .filter((c) => c.status === "open" && calcDDay(c.deadline) <= 7)
    .sort((a, b) => calcDDay(a.deadline) - calcDDay(b.deadline));
  for (const c of now7) {
    actions.push({ kind: "deadline", cal: c, days: calcDDay(c.deadline) });
  }

  // 3순위: AI 작업 중
  for (const p of proposals) {
    if (p.status === "in_progress") {
      actions.push({ kind: "running", proposal: p });
    }
  }

  // 4순위: 아직 시작 전
  for (const p of proposals) {
    if (p.status === "initialized") {
      actions.push({ kind: "init", proposal: p });
    }
  }

  const items = actions.slice(0, 5);

  // ── 빈 상태 ──────────────────────────────────────────────────────
  if (items.length === 0) {
    return (
      <div className="bg-[#1c1c1c] border border-[#3ecf8e]/20 rounded-2xl px-5 py-4 flex items-center gap-3">
        <span className="text-[#3ecf8e] text-lg">✓</span>
        <div>
          <p className="text-sm font-semibold text-[#ededed]">오늘 할 일 없음</p>
          <p className="text-xs text-[#8c8c8c] mt-0.5">진행 중인 제안서나 마감 임박 일정이 없습니다.</p>
        </div>
      </div>
    );
  }

  // ── 렌더 ─────────────────────────────────────────────────────────
  return (
    <div className="bg-[#1c1c1c] border border-[#3ecf8e]/20 rounded-2xl overflow-hidden">
      {/* 헤더 */}
      <div className="px-5 py-3 flex items-center gap-2 border-b border-[#262626]">
        <span className="w-1.5 h-1.5 rounded-full bg-[#3ecf8e] animate-pulse shrink-0" />
        <h2 className="text-sm font-semibold text-[#ededed]">오늘 할 일</h2>
        <span className="ml-1 text-xs font-bold text-[#3ecf8e] bg-[#3ecf8e]/10 px-1.5 py-0.5 rounded-full">
          {items.length}
        </span>
      </div>

      {/* 아이템 목록 */}
      <div className="divide-y divide-[#262626]">
        {items.map((action, i) => {
          if (action.kind === "review") {
            const { proposal, reviewLabel } = action;
            return (
              <div key={`r-${proposal.id}-${i}`} className="flex items-center gap-3 px-5 py-3.5 hover:bg-[#222] transition-colors">
                {/* 긴급 배지 */}
                <div className="shrink-0 flex flex-col items-center gap-0.5 w-14">
                  <span className="text-[10px] font-bold text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded-full whitespace-nowrap">
                    검토 대기
                  </span>
                </div>
                {/* 내용 */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#ededed] truncate">{proposal.title}</p>
                  <p className="text-xs text-amber-400/80 mt-0.5 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                    {reviewLabel}
                  </p>
                </div>
                {/* CTA */}
                <button
                  onClick={() => router.push(`/proposals/${proposal.id}`)}
                  className="shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-500 text-white hover:bg-amber-400 transition-colors"
                >
                  검토하기 →
                </button>
              </div>
            );
          }

          if (action.kind === "deadline") {
            const { cal, days } = action;
            const urgent = days <= 3;
            return (
              <div key={`d-${cal.id}-${i}`} className="flex items-center gap-3 px-5 py-3.5 hover:bg-[#222] transition-colors">
                <div className="shrink-0 w-14 text-center">
                  <span className={`text-xs font-bold ${urgent ? "text-red-400" : "text-yellow-400"}`}>
                    {dDayLabel(days)}
                  </span>
                  {urgent && <div className="w-1 h-1 rounded-full bg-red-400 animate-ping mx-auto mt-1" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#ededed] truncate">{cal.title}</p>
                  <p className="text-xs text-[#8c8c8c] mt-0.5">
                    {cal.agency ? `${cal.agency} · ` : ""}제안서 미생성
                  </p>
                </div>
                <button
                  onClick={() => router.push("/proposals/new")}
                  className={`shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                    urgent
                      ? "bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30"
                      : "bg-yellow-500/15 text-yellow-400 hover:bg-yellow-500/25 border border-yellow-500/20"
                  }`}
                >
                  지금 시작 →
                </button>
              </div>
            );
          }

          if (action.kind === "running") {
            const { proposal } = action;
            return (
              <div key={`ai-${proposal.id}-${i}`} className="flex items-center gap-3 px-5 py-3.5 hover:bg-[#222] transition-colors">
                <div className="shrink-0 w-14 flex justify-center">
                  <span className="text-[10px] font-bold text-blue-400 bg-blue-400/10 px-1.5 py-0.5 rounded-full">
                    AI 중
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#ededed] truncate">{proposal.title}</p>
                  <p className="text-xs text-[#8c8c8c] mt-0.5">
                    Phase {(proposal.phases_completed ?? 0) + 1} 진행 중
                  </p>
                </div>
                <button
                  onClick={() => router.push(`/proposals/${proposal.id}`)}
                  className="shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-500/15 text-blue-400 hover:bg-blue-500/25 border border-blue-500/20 transition-colors"
                >
                  진행 확인
                </button>
              </div>
            );
          }

          if (action.kind === "init") {
            const { proposal } = action;
            return (
              <div key={`n-${proposal.id}-${i}`} className="flex items-center gap-3 px-5 py-3.5 hover:bg-[#222] transition-colors">
                <div className="shrink-0 w-14 flex justify-center">
                  <span className="text-[10px] font-bold text-[#8c8c8c] bg-[#262626] px-1.5 py-0.5 rounded-full">
                    시작 전
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#ededed] truncate">{proposal.title}</p>
                  <p className="text-xs text-[#8c8c8c] mt-0.5">워크플로 아직 시작 안 됨</p>
                </div>
                <button
                  onClick={() => router.push(`/proposals/${proposal.id}`)}
                  className="shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#262626] text-[#ededed] hover:bg-[#333] transition-colors"
                >
                  시작하기
                </button>
              </div>
            );
          }

          return null;
        })}
      </div>
    </div>
  );
}
