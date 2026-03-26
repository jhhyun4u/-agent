"use client";

/**
 * ProjectContextHeader — 프로젝트 컨텍스트 헤더
 *
 * 프로젝트명, 발주처, D-day, 예산, 포지셔닝, 상태배지를 한눈에 보여준다.
 */

import { useRef, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, type ProposalStatus_, type ProposalSummary } from "@/lib/api";

// ── 상태 배지 ──
const STATUS_BADGE_MAP: Record<string, { label: string; bg: string; text: string; border: string; pulse?: boolean }> = {
  processing:   { label: "진행중", bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30", pulse: true },
  initialized:  { label: "대기중", bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30" },
  running:      { label: "진행중", bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30", pulse: true },
  searching:    { label: "진행중", bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30", pulse: true },
  analyzing:    { label: "진행중", bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30", pulse: true },
  strategizing: { label: "진행중", bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30", pulse: true },
  completed:    { label: "완료",   bg: "bg-[#3ecf8e]/15", text: "text-[#3ecf8e]", border: "border-[#3ecf8e]/30" },
  won:          { label: "수주",   bg: "bg-[#3ecf8e]/15", text: "text-[#3ecf8e]", border: "border-[#3ecf8e]/30" },
  lost:         { label: "패찰",   bg: "bg-red-500/15", text: "text-red-400", border: "border-red-500/30" },
  submitted:    { label: "결과대기", bg: "bg-purple-500/15", text: "text-purple-400", border: "border-purple-500/30" },
  presented:    { label: "결과대기", bg: "bg-purple-500/15", text: "text-purple-400", border: "border-purple-500/30" },
  on_hold:      { label: "중단",   bg: "bg-orange-500/15", text: "text-orange-400", border: "border-orange-500/30" },
  abandoned:    { label: "포기",   bg: "bg-red-500/15", text: "text-red-400", border: "border-red-500/30" },
  no_go:        { label: "No-Go",  bg: "bg-red-500/15", text: "text-red-300", border: "border-red-500/30" },
};

// ── 포지셔닝 ──
const POS_MAP: Record<string, { icon: string; label: string; color: string }> = {
  offensive: { icon: "\u2694\uFE0F", label: "공격", color: "text-red-400" },
  defensive: { icon: "\uD83D\uDEE1\uFE0F", label: "수성", color: "text-blue-400" },
  adjacent:  { icon: "\uD83D\uDD00", label: "인접", color: "text-amber-400" },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_BADGE_MAP[status] ?? { label: status, bg: "bg-[#262626]", text: "text-[#8c8c8c]", border: "border-[#262626]" };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium ${cfg.bg} ${cfg.text} border ${cfg.border} ${cfg.pulse ? "animate-pulse" : ""}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.text.replace("text-", "bg-")}`} />
      {cfg.label}
    </span>
  );
}

function formatDday(deadline?: string | null): { text: string; color: string } | null {
  if (!deadline) return null;
  const d = new Date(deadline);
  if (isNaN(d.getTime())) return null;
  const diff = Math.ceil((d.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
  if (diff < 0) return { text: `D+${Math.abs(diff)}`, color: "text-red-400" };
  if (diff <= 3) return { text: `D-${diff}`, color: "text-red-400" };
  if (diff <= 7) return { text: `D-${diff}`, color: "text-amber-400" };
  return { text: `D-${diff}`, color: "text-[#8c8c8c]" };
}

function formatBudget(amount?: number | null): string | null {
  if (!amount) return null;
  if (amount >= 100_000_000) return `${(amount / 100_000_000).toFixed(1)}억원`;
  if (amount >= 10_000) return `${(amount / 10_000).toFixed(0)}만원`;
  return `${amount.toLocaleString()}원`;
}

function formatDate(dateStr?: string | null): string | null {
  if (!dateStr) return null;
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return null;
  return `${d.getMonth() + 1}.${d.getDate()}`;
}

// ── Props ──
interface ProjectContextHeaderProps {
  proposalId: string;
  status: ProposalStatus_;
  versions: ProposalSummary[];
  currentVersionLabel: () => string;
  versionLabel: (idx: number) => string;
  onNewVersion: () => void;
  rightPanelOpen: boolean;
  onToggleRightPanel: () => void;
}

export default function ProjectContextHeader({
  proposalId,
  status,
  versions,
  currentVersionLabel,
  versionLabel,
  onNewVersion,
  rightPanelOpen,
  onToggleRightPanel,
}: ProjectContextHeaderProps) {
  const router = useRouter();
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (moreRef.current && !moreRef.current.contains(e.target as Node)) setMoreOpen(false);
    }
    if (moreOpen) document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [moreOpen]);

  const dday = formatDday(status.deadline);
  const budget = formatBudget(status.bid_amount ?? status.budget);
  const pos = status.positioning ? POS_MAP[status.positioning] : null;
  const deadlineDate = formatDate(status.deadline);

  return (
    <header className="bg-[#111111] border-b border-[#262626] shrink-0 z-20">
      {/* Row 1: 네비게이션 */}
      <div className="flex items-center gap-3 px-4 pt-2 pb-1">
        <Link href="/proposals" className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors shrink-0">
          ← 목록
        </Link>
        <div className="flex-1" />
        {/* ⋯ 메뉴 */}
        <div className="relative shrink-0" ref={moreRef}>
          <button
            onClick={() => setMoreOpen((o) => !o)}
            className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs text-[#8c8c8c] hover:text-[#ededed] hover:bg-[#1c1c1c] transition-colors"
          >
            {currentVersionLabel()}
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <circle cx="12" cy="6" r="1.5" fill="currentColor" />
              <circle cx="12" cy="12" r="1.5" fill="currentColor" />
              <circle cx="12" cy="18" r="1.5" fill="currentColor" />
            </svg>
          </button>
          {moreOpen && (
            <div className="absolute right-0 mt-1 w-44 bg-[#1c1c1c] border border-[#262626] rounded-xl shadow-xl overflow-hidden z-30">
              <button
                onClick={() => { setMoreOpen(false); window.open(`/editor/${proposalId}`, "_blank"); }}
                className="w-full text-left px-3 py-2 text-xs text-[#ededed] hover:bg-[#262626] transition-colors"
              >
                편집 (새 창)
              </button>
              <div className="border-t border-[#262626]">
                <p className="px-3 py-1.5 text-[10px] text-[#5c5c5c] uppercase tracking-wider">버전</p>
                {versions.map((v, idx) => (
                  <button
                    key={v.id}
                    onClick={() => { setMoreOpen(false); router.push(`/proposals/${v.id}`); }}
                    className={`w-full text-left px-3 py-1.5 text-xs transition-colors ${
                      v.id === proposalId
                        ? "text-[#3ecf8e] bg-[#3ecf8e]/10"
                        : "text-[#ededed] hover:bg-[#262626]"
                    }`}
                  >
                    {versionLabel(idx)}
                    {v.id === proposalId && <span className="ml-1 text-[#8c8c8c]">(현재)</span>}
                  </button>
                ))}
                <button
                  onClick={() => { setMoreOpen(false); onNewVersion(); }}
                  className="w-full text-left px-3 py-1.5 text-xs text-[#3ecf8e] hover:bg-[#3ecf8e]/10 transition-colors"
                >
                  + 새 버전
                </button>
              </div>
            </div>
          )}
        </div>
        <button
          onClick={onToggleRightPanel}
          className="p-1.5 rounded-lg text-[#8c8c8c] hover:text-[#ededed] hover:bg-[#262626] transition-colors shrink-0"
          title={rightPanelOpen ? "패널 접기" : "패널 펼치기"}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            {rightPanelOpen
              ? <path strokeLinecap="round" strokeLinejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              : <path strokeLinecap="round" strokeLinejoin="round" d="M11 19l-7-7 7-7M19 19l-7-7 7-7" />}
          </svg>
        </button>
      </div>

      {/* Row 2: 프로젝트 제목 + 상태 배지 */}
      <div className="flex items-center gap-2 px-4 pb-1">
        <h1 className="text-base font-semibold text-[#ededed] truncate flex-1 min-w-0">
          {status.rfp_title || status.title || "제안 작업"}
        </h1>
        <StatusBadge status={status.status} />
      </div>

      {/* Row 3: 메타데이터 칩 */}
      <div className="flex items-center gap-2 px-4 pb-2.5 overflow-x-auto scrollbar-none">
        {/* 발주처 */}
        {status.client_name && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-[#1c1c1c] text-[#b0b0b0] border border-[#262626] shrink-0">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            {status.client_name}
          </span>
        )}

        {/* D-day + 마감일 */}
        {dday && (
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-[#1c1c1c] border border-[#262626] shrink-0 ${dday.color}`}>
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {dday.text}
            {deadlineDate && <span className="text-[#8c8c8c] ml-0.5">({deadlineDate})</span>}
          </span>
        )}

        {/* 예산 */}
        {budget && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-[#1c1c1c] text-[#b0b0b0] border border-[#262626] shrink-0">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {budget}
          </span>
        )}

        {/* 포지셔닝 */}
        {pos && (
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-[#1c1c1c] border border-[#262626] shrink-0 ${pos.color}`}>
            {pos.icon} {pos.label}
          </span>
        )}

        {/* 공고번호 */}
        {status.bid_number && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-[#1c1c1c] text-[#8c8c8c] border border-[#262626] shrink-0">
            #{status.bid_number}
          </span>
        )}
      </div>
    </header>
  );
}
