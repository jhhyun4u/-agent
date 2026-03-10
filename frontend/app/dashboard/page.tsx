"use client";

/**
 * 대시보드 페이지
 * - 오늘 할 일 (긴급 캘린더 + 진행 중 제안서)
 * - 제안 파이프라인 뷰 (공고 등록 → 수주)
 * - 수주율 KPI 카드 (전체/이번달/수주건수)
 * - 기관별 수주율 CSS 막대 차트
 * - 월별 추이 테이블
 * - RFP 캘린더 (D-day, 일정 추가)
 */

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AppSidebar from "@/components/AppSidebar";
import { api, CalendarItem, WinRateStats, ProposalSummary, RecommendedBid } from "@/lib/api";

// ── 타입 ──────────────────────────────────────────────────────────────

type Scope = "personal" | "team" | "company";

type ActionItem =
  | { type: "calendar"; item: CalendarItem; days: number }
  | { type: "proposal"; item: ProposalSummary };

// ── 유틸 ──────────────────────────────────────────────────────────────

function calcDDay(deadlineIso: string): number {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const deadline = new Date(deadlineIso);
  deadline.setHours(0, 0, 0, 0);
  return Math.ceil((deadline.getTime() - now.getTime()) / 86400000);
}

function dDayColor(days: number): string {
  if (days <= 3) return "text-red-400";
  if (days <= 14) return "text-yellow-400";
  return "text-[#8c8c8c]";
}

function dDayLabel(days: number): string {
  if (days === 0) return "D-Day";
  if (days < 0) return `D+${Math.abs(days)}`;
  return `D-${days}`;
}

function statusBadge(status: CalendarItem["status"]): React.ReactNode {
  const map: Record<
    CalendarItem["status"],
    { label: string; cls: string }
  > = {
    open: { label: "공개", cls: "bg-[#262626] text-[#8c8c8c]" },
    submitted: { label: "제출", cls: "bg-blue-500/15 text-blue-400" },
    won: { label: "수주", cls: "bg-[#3ecf8e]/15 text-[#3ecf8e]" },
    lost: { label: "낙찰실패", cls: "bg-red-500/15 text-red-400" },
  };
  const { label, cls } = map[status] ?? map.open;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}
    >
      {label}
    </span>
  );
}

function getCurrentMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function getPrevMonth(): string {
  const d = new Date();
  d.setMonth(d.getMonth() - 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

// ── 메인 페이지 ───────────────────────────────────────────────────────

export default function DashboardPage() {
  const router = useRouter();

  // 스코프
  const [scope, setScope] = useState<Scope>("personal");

  // 통계
  const [stats, setStats] = useState<WinRateStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  // 캘린더
  const [calItems, setCalItems] = useState<CalendarItem[]>([]);
  const [calLoading, setCalLoading] = useState(true);

  // 제안서 목록 (파이프라인 + 액션 허브용)
  const [proposals, setProposals] = useState<ProposalSummary[]>([]);

  // 추천 공고 위젯
  const [teamId, setTeamId] = useState<string | null>(null);
  const [topBids, setTopBids] = useState<RecommendedBid[]>([]);
  const [bidCounts, setBidCounts] = useState({ S: 0, A: 0 });
  const [bidsLoading, setBidsLoading] = useState(true);

  // 일정 추가 폼
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    agency: "",
    deadline: "",
    proposal_id: "",
  });
  const [formSaving, setFormSaving] = useState(false);

  // ── 데이터 로드 ────────────────────────────────────────────────────

  const loadStats = useCallback(async (s: Scope) => {
    setStatsLoading(true);
    try {
      const data = await api.stats.winRate(s);
      setStats(data);
    } catch {
      setStats(null);
    } finally {
      setStatsLoading(false);
    }
  }, []);

  const loadBidRecommendations = useCallback(async () => {
    setBidsLoading(true);
    try {
      const teamsRes = await api.teams.list();
      const firstTeam = teamsRes.teams[0];
      if (!firstTeam) return;
      const tid = firstTeam.team_id;
      setTeamId(tid);

      const recRes = await api.bids.getRecommendations(tid);
      const recommended = recRes.data.recommended;

      setBidCounts({
        S: recommended.filter((b) => b.match_grade === "S").length,
        A: recommended.filter((b) => b.match_grade === "A").length,
      });
      setTopBids(
        recommended
          .filter((b) => b.match_grade === "S" || b.match_grade === "A")
          .sort((a, b) => b.match_score - a.match_score)
          .slice(0, 3)
      );
    } catch {
      // silent fail — 팀 미설정이거나 추천 없는 경우 정상
    } finally {
      setBidsLoading(false);
    }
  }, []);

  const loadProposals = useCallback(async () => {
    try {
      const res = await api.proposals.list({ page: 1 });
      setProposals(res.items);
    } catch {
      setProposals([]);
    }
  }, []);

  const loadCalendar = useCallback(async () => {
    setCalLoading(true);
    try {
      const data = await api.calendar.list({ scope });
      const sorted = [...data.items].sort(
        (a, b) =>
          new Date(a.deadline).getTime() - new Date(b.deadline).getTime()
      );
      setCalItems(sorted);
    } catch {
      setCalItems([]);
    } finally {
      setCalLoading(false);
    }
  }, [scope]);

  useEffect(() => {
    loadStats(scope);
    loadCalendar();
    loadProposals();
    loadBidRecommendations();
  }, [scope, loadStats, loadCalendar, loadProposals, loadBidRecommendations]);

  // ── 일정 추가 저장 ─────────────────────────────────────────────────

  async function handleAddCalendar(e: React.FormEvent) {
    e.preventDefault();
    if (!formData.title || !formData.deadline) return;
    setFormSaving(true);
    try {
      await api.calendar.create({
        title: formData.title,
        agency: formData.agency || undefined,
        deadline: formData.deadline,
        proposal_id: formData.proposal_id || undefined,
      });
      setFormData({ title: "", agency: "", deadline: "", proposal_id: "" });
      setShowAddForm(false);
      await loadCalendar();
    } catch (err) {
      alert(err instanceof Error ? err.message : "저장 실패");
    } finally {
      setFormSaving(false);
    }
  }

  // ── 파이프라인 카운트 계산 ─────────────────────────────────────────

  const pipeline = {
    registered: calItems.filter((c) => c.status === "open" && !c.proposal_id).length,
    inProgress: proposals.filter(
      (p) => p.status === "initialized" || p.status === "processing"
    ).length,
    completed: proposals.filter(
      (p) => p.status === "completed" && p.win_result == null
    ).length,
    pending: proposals.filter((p) => p.win_result === "pending").length,
    won: proposals.filter((p) => p.win_result === "won").length,
    lost: proposals.filter((p) => p.win_result === "lost").length,
  };

  // ── 오늘 할 일 (액션 허브) ────────────────────────────────────────

  const actionItems: ActionItem[] = [
    ...calItems
      .filter((c) => calcDDay(c.deadline) <= 14 && c.status === "open")
      .map((c) => ({ type: "calendar" as const, item: c, days: calcDDay(c.deadline) }))
      .sort((a, b) => a.days - b.days),
    ...proposals
      .filter((p) => p.status === "initialized" || p.status === "processing")
      .map((p) => ({ type: "proposal" as const, item: p })),
  ].slice(0, 5);

  // ── 이번달 통계 계산 ───────────────────────────────────────────────

  const currentMonth = getCurrentMonth();
  const prevMonth = getPrevMonth();
  const thisMonthData = stats?.by_month.find((m) => m.month === currentMonth);
  const prevMonthData = stats?.by_month.find((m) => m.month === prevMonth);

  // 지난달 대비 수주율 변화 (%p)
  const monthTrend =
    thisMonthData && prevMonthData
      ? (thisMonthData.rate - prevMonthData.rate) * 100
      : null;

  // 최근 6개월 추이 (최신순)
  const recentMonths = stats
    ? [...stats.by_month]
        .sort((a, b) => b.month.localeCompare(a.month))
        .slice(0, 6)
    : [];

  // ── 인사이트 계산 ──────────────────────────────────────────────────

  // 수주율 TOP 기관 (최소 2건 이상)
  const topAgency = stats
    ? [...stats.by_agency]
        .filter((a) => a.total >= 2)
        .sort((a, b) => b.rate - a.rate)[0] ?? null
    : null;

  // 최근 6개월 평균 수주율
  const avgRate6m =
    recentMonths.length > 0
      ? recentMonths.reduce((sum, m) => sum + m.rate, 0) / recentMonths.length
      : null;

  // 가장 많이 제안한 기관
  const mostProposedAgency = stats
    ? [...stats.by_agency].sort((a, b) => b.total - a.total)[0] ?? null
    : null;

  // ── 렌더 ──────────────────────────────────────────────────────────

  return (
    <div className="flex h-screen bg-[#0f0f0f] overflow-hidden">
      <AppSidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 상단 헤더 */}
        <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 shrink-0 flex items-center justify-between">
          <h1 className="text-sm font-semibold text-[#ededed]">
            대시보드
          </h1>

          {/* 스코프 탭 */}
          <div className="flex items-center gap-1 bg-[#1c1c1c] rounded-lg p-1 border border-[#262626]">
            {(
              [
                { key: "personal" as Scope, label: "개인" },
                { key: "team" as Scope, label: "팀" },
                { key: "company" as Scope, label: "전체" },
              ] as const
            ).map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setScope(key)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  scope === key
                    ? "bg-[#3ecf8e] text-[#0f0f0f]"
                    : "text-[#8c8c8c] hover:text-[#ededed]"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </header>

        {/* 스크롤 본문 */}
        <main className="flex-1 overflow-y-auto px-6 py-5 space-y-5">

          {/* ── 오늘 할 일 ── */}
          {actionItems.length > 0 && (
            <div className="bg-[#1c1c1c] border border-[#3ecf8e]/20 rounded-2xl p-5">
              <h2 className="text-sm font-semibold text-[#ededed] mb-3 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#3ecf8e] animate-pulse" />
                지금 해야 할 것
              </h2>
              <div className="space-y-2">
                {actionItems.map((action) => {
                  if (action.type === "calendar") {
                    const { item, days } = action;
                    const urgent = days <= 3;
                    return (
                      <div
                        key={`cal-${item.id}`}
                        className="flex items-center gap-3 px-4 py-3 rounded-xl bg-[#111111] border border-[#262626]"
                      >
                        <span
                          className={`shrink-0 text-xs font-bold w-10 text-center ${
                            urgent ? "text-red-400" : "text-yellow-400"
                          }`}
                        >
                          {dDayLabel(days)}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-[#ededed] truncate">
                            {item.title}
                          </p>
                          <p className="text-xs text-[#8c8c8c] mt-0.5">
                            {item.agency ? `${item.agency} · ` : ""}제안서 미생성
                          </p>
                        </div>
                        <button
                          onClick={() => router.push("/proposals/new")}
                          className="shrink-0 px-3 py-1.5 rounded-lg bg-[#3ecf8e] hover:bg-[#49e59e] text-[#0f0f0f] text-xs font-semibold transition-colors"
                        >
                          지금 시작
                        </button>
                      </div>
                    );
                  }

                  const { item } = action;
                  const isProcessing = item.status === "processing";
                  return (
                    <div
                      key={`prop-${item.id}`}
                      className="flex items-center gap-3 px-4 py-3 rounded-xl bg-[#111111] border border-[#262626]"
                    >
                      <span
                        className={`shrink-0 text-xs font-bold w-10 text-center ${
                          isProcessing ? "text-blue-400" : "text-[#8c8c8c]"
                        }`}
                      >
                        {isProcessing ? "생성중" : "대기"}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-[#ededed] truncate">
                          {item.title}
                        </p>
                        <p className="text-xs text-[#8c8c8c] mt-0.5">
                          {isProcessing
                            ? `Phase ${item.phases_completed + 1} 진행 중`
                            : "생성 시작 전"}
                        </p>
                      </div>
                      <button
                        onClick={() => router.push(`/proposals/${item.id}`)}
                        className="shrink-0 px-3 py-1.5 rounded-lg bg-[#262626] hover:bg-[#333] text-[#ededed] text-xs font-semibold transition-colors"
                      >
                        {isProcessing ? "확인" : "시작"}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── 파이프라인 뷰 ── */}
          <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
            <h2 className="text-sm font-semibold text-[#ededed] mb-4">제안 파이프라인</h2>
            <div className="flex items-stretch gap-0">
              {(
                [
                  { label: "공고 등록", count: pipeline.registered, color: "text-[#8c8c8c]", href: "/bids" },
                  { label: "작성 중", count: pipeline.inProgress, color: "text-blue-400", href: "/proposals?status=processing" },
                  { label: "완료", count: pipeline.completed, color: "text-[#ededed]", href: "/proposals?status=completed" },
                  { label: "결과 대기", count: pipeline.pending, color: "text-yellow-400", href: "/proposals" },
                  { label: "수주", count: pipeline.won, color: "text-[#3ecf8e]", href: "/archive?win_result=won" },
                  { label: "낙찰 실패", count: pipeline.lost, color: "text-red-400", href: "/archive?win_result=lost" },
                ] as const
              ).map((stage, i, arr) => (
                <div key={stage.label} className="flex items-stretch">
                  <button
                    onClick={() => router.push(stage.href)}
                    className="flex flex-col items-center px-4 py-3 rounded-xl hover:bg-[#262626] transition-colors min-w-[80px]"
                  >
                    <span className={`text-2xl font-bold ${stage.color}`}>
                      {stage.count}
                    </span>
                    <span className="text-xs text-[#8c8c8c] mt-1 whitespace-nowrap">
                      {stage.label}
                    </span>
                  </button>
                  {i < arr.length - 1 && (
                    <div className="flex items-center px-1 text-[#3c3c3c] text-sm select-none">
                      →
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* ── 추천 공고 위젯 ── */}
          {!bidsLoading && (bidCounts.S > 0 || bidCounts.A > 0) && (
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <h2 className="text-sm font-semibold text-[#ededed]">추천 공고</h2>
                  {bidCounts.S > 0 && (
                    <span className="text-xs px-2 py-0.5 rounded-md font-bold bg-purple-950/60 text-purple-400 border border-purple-900">
                      S {bidCounts.S}건
                    </span>
                  )}
                  {bidCounts.A > 0 && (
                    <span className="text-xs px-2 py-0.5 rounded-md font-bold bg-emerald-950/60 text-emerald-400 border border-emerald-900">
                      A {bidCounts.A}건
                    </span>
                  )}
                </div>
                <button
                  onClick={() => router.push("/bids")}
                  className="text-xs text-[#3ecf8e] hover:underline"
                >
                  전체 보기 →
                </button>
              </div>

              <div className="space-y-2">
                {topBids.map((bid) => {
                  const gradeColor =
                    bid.match_grade === "S"
                      ? "bg-purple-950/60 text-purple-400 border border-purple-900"
                      : "bg-emerald-950/60 text-emerald-400 border border-emerald-900";
                  const dDays = bid.days_remaining;
                  const dColor =
                    dDays !== null && dDays <= 7
                      ? "text-red-400"
                      : dDays !== null && dDays <= 14
                      ? "text-yellow-400"
                      : "text-[#8c8c8c]";

                  return (
                    <button
                      key={bid.bid_no}
                      onClick={() =>
                        router.push(
                          `/bids/${bid.bid_no}${teamId ? `?team_id=${teamId}` : ""}`
                        )
                      }
                      className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-[#111111] border border-[#262626] hover:border-[#3ecf8e]/30 hover:bg-[#161616] transition-colors text-left"
                    >
                      <span
                        className={`shrink-0 text-xs px-1.5 py-0.5 rounded font-bold ${gradeColor}`}
                      >
                        {bid.match_grade}
                      </span>
                      <span className="flex-1 text-sm text-[#ededed] truncate">
                        {bid.bid_title}
                      </span>
                      <span className="shrink-0 text-xs font-medium text-[#8c8c8c]">
                        {bid.agency}
                      </span>
                      {dDays !== null && (
                        <span className={`shrink-0 text-xs font-bold ${dColor}`}>
                          D-{dDays}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── KPI 카드 3개 ── */}
          {statsLoading ? (
            <p className="text-sm text-[#8c8c8c]">로딩 중...</p>
          ) : !stats ? (
            <p className="text-sm text-[#8c8c8c]">통계 데이터를 불러올 수 없습니다.</p>
          ) : (
            <div className="grid grid-cols-3 gap-4">
              {/* 전체 수주율 */}
              <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-4">
                <p className="text-xs text-[#8c8c8c] mb-2">전체 수주율</p>
                <p className="text-3xl font-bold text-[#3ecf8e]">
                  {(stats.overall.rate * 100).toFixed(1)}
                  <span className="text-base font-normal text-[#8c8c8c] ml-1">%</span>
                </p>
                <p className="text-xs text-[#8c8c8c] mt-1">
                  총 {stats.overall.total}건 중 {stats.overall.won}건 수주
                </p>
              </div>

              {/* 이번달 수주율 */}
              <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-4">
                <p className="text-xs text-[#8c8c8c] mb-2">이번달 수주율</p>
                {thisMonthData ? (
                  <>
                    <p className="text-3xl font-bold text-[#ededed]">
                      {(thisMonthData.rate * 100).toFixed(1)}
                      <span className="text-base font-normal text-[#8c8c8c] ml-1">%</span>
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-[#8c8c8c]">
                        {thisMonthData.total}건 중 {thisMonthData.won}건 수주
                      </span>
                      {monthTrend !== null && (
                        <span
                          className={`text-xs font-semibold ${
                            monthTrend > 0
                              ? "text-[#3ecf8e]"
                              : monthTrend < 0
                              ? "text-red-400"
                              : "text-[#8c8c8c]"
                          }`}
                        >
                          {monthTrend > 0 ? "↑" : monthTrend < 0 ? "↓" : "–"}
                          {Math.abs(monthTrend).toFixed(1)}%p
                        </span>
                      )}
                    </div>
                  </>
                ) : (
                  <>
                    <p className="text-3xl font-bold text-[#8c8c8c]">N/A</p>
                    <p className="text-xs text-[#8c8c8c] mt-1">이번달 데이터 없음</p>
                  </>
                )}
              </div>

              {/* 총 수주 건수 */}
              <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-4">
                <p className="text-xs text-[#8c8c8c] mb-2">총 수주 건수</p>
                <p className="text-3xl font-bold text-[#ededed]">
                  {stats.overall.won}
                  <span className="text-base font-normal text-[#8c8c8c] ml-1">건</span>
                </p>
                <p className="text-xs text-[#8c8c8c] mt-1">
                  누적 제안 {stats.overall.total}건
                </p>
              </div>
            </div>
          )}

          {/* ── 인사이트 ── */}
          {!statsLoading && stats && (topAgency || avgRate6m !== null || mostProposedAgency) && (
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
              <h2 className="text-sm font-semibold text-[#ededed] mb-3">인사이트</h2>
              <div className="space-y-2.5">

                {/* 수주율 최강 기관 */}
                {topAgency && (
                  <div className="flex items-start gap-3 px-3 py-2.5 rounded-xl bg-[#111111]">
                    <span className="text-base shrink-0 mt-0.5">🏆</span>
                    <p className="text-xs text-[#8c8c8c] leading-relaxed">
                      <span className="text-[#ededed] font-medium">{topAgency.agency}</span>
                      에서 수주율{" "}
                      <span className="text-[#3ecf8e] font-semibold">
                        {Math.round(topAgency.rate * 100)}%
                      </span>{" "}
                      기록 ({topAgency.total}건 중 {topAgency.won}건 수주)
                    </p>
                  </div>
                )}

                {/* 최근 6개월 평균 */}
                {avgRate6m !== null && recentMonths.length >= 2 && (
                  <div className="flex items-start gap-3 px-3 py-2.5 rounded-xl bg-[#111111]">
                    <span className="text-base shrink-0 mt-0.5">📊</span>
                    <p className="text-xs text-[#8c8c8c] leading-relaxed">
                      최근 {recentMonths.length}개월 평균 수주율{" "}
                      <span className="text-[#ededed] font-semibold">
                        {(avgRate6m * 100).toFixed(1)}%
                      </span>
                      {monthTrend !== null && monthTrend !== 0 && (
                        <>
                          {" "}— 이번달{" "}
                          <span
                            className={
                              monthTrend > 0 ? "text-[#3ecf8e] font-semibold" : "text-red-400 font-semibold"
                            }
                          >
                            {monthTrend > 0 ? "상승" : "하락"}
                          </span>{" "}
                          추세
                        </>
                      )}
                    </p>
                  </div>
                )}

                {/* 가장 많이 제안한 기관 */}
                {mostProposedAgency && mostProposedAgency.total >= 2 && (
                  <div className="flex items-start gap-3 px-3 py-2.5 rounded-xl bg-[#111111]">
                    <span className="text-base shrink-0 mt-0.5">📋</span>
                    <p className="text-xs text-[#8c8c8c] leading-relaxed">
                      <span className="text-[#ededed] font-medium">{mostProposedAgency.agency}</span>
                      에 가장 많이 제안 ({mostProposedAgency.total}건) —{" "}
                      수주율{" "}
                      <span className="font-medium text-[#ededed]">
                        {Math.round(mostProposedAgency.rate * 100)}%
                      </span>
                    </p>
                  </div>
                )}

              </div>
            </div>
          )}

          {/* ── 기관별 수주율 ── */}
          {!statsLoading && stats && stats.by_agency.length > 0 && (
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
              <h2 className="text-sm font-semibold text-[#ededed] mb-4">
                기관별 수주율
              </h2>
              <div className="space-y-3">
                {stats.by_agency.slice(0, 10).map((item) => {
                  const pct = Math.round(item.rate * 100);
                  return (
                    <div key={item.agency} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-[#ededed] w-24 truncate shrink-0">
                          {item.agency}
                        </span>
                        <div className="flex-1 mx-3">
                          <div className="h-2 bg-[#262626] rounded-full overflow-hidden">
                            <div
                              className="h-full bg-[#3ecf8e] rounded-full transition-all duration-500"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                        <span className="text-[#3ecf8e] font-medium w-10 text-right shrink-0">
                          {pct}%
                        </span>
                        <span className="text-[#8c8c8c] w-12 text-right shrink-0 ml-2">
                          {item.won}/{item.total}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── 월별 추이 테이블 ── */}
          {!statsLoading && stats && recentMonths.length > 0 && (
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
              <h2 className="text-sm font-semibold text-[#ededed] mb-4">
                월별 추이
                <span className="ml-2 text-xs font-normal text-[#8c8c8c]">
                  최근 6개월
                </span>
              </h2>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#262626]">
                    <th className="text-left pb-2 text-xs text-[#8c8c8c] font-medium">
                      월
                    </th>
                    <th className="text-right pb-2 text-xs text-[#8c8c8c] font-medium">
                      건수
                    </th>
                    <th className="text-right pb-2 text-xs text-[#8c8c8c] font-medium">
                      수주
                    </th>
                    <th className="text-right pb-2 text-xs text-[#8c8c8c] font-medium">
                      수주율
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {recentMonths.map((m) => (
                    <tr
                      key={m.month}
                      className="border-b border-[#262626]/50 last:border-0"
                    >
                      <td className="py-2.5 text-[#ededed]">{m.month}</td>
                      <td className="py-2.5 text-right text-[#8c8c8c]">
                        {m.total}건
                      </td>
                      <td className="py-2.5 text-right text-[#8c8c8c]">
                        {m.won}수주
                      </td>
                      <td className="py-2.5 text-right font-medium text-[#3ecf8e]">
                        {(m.rate * 100).toFixed(0)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* ── RFP 캘린더 ── */}
          <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
            {/* 헤더 */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-[#ededed]">
                RFP 캘린더
              </h2>
              <button
                onClick={() => setShowAddForm((v) => !v)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#3ecf8e] hover:bg-[#3ecf8e]/90 text-[#0f0f0f] text-xs font-semibold transition-colors"
              >
                <span>+</span>
                <span>일정 추가</span>
              </button>
            </div>

            {/* 일정 추가 인라인 폼 */}
            {showAddForm && (
              <form
                onSubmit={handleAddCalendar}
                className="mb-4 bg-[#111111] border border-[#262626] rounded-xl p-4 space-y-3"
              >
                <p className="text-xs font-semibold text-[#ededed] mb-1">
                  새 일정
                </p>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-[#8c8c8c] mb-1">
                      제목 <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.title}
                      onChange={(e) =>
                        setFormData((f) => ({ ...f, title: e.target.value }))
                      }
                      placeholder="예: 스마트시티 제안서"
                      className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#8c8c8c] focus:outline-none focus:ring-2 focus:ring-[#3ecf8e]/40 focus:border-[#3ecf8e]/50 transition-colors"
                    />
                  </div>

                  <div>
                    <label className="block text-xs text-[#8c8c8c] mb-1">
                      기관명
                    </label>
                    <input
                      type="text"
                      value={formData.agency}
                      onChange={(e) =>
                        setFormData((f) => ({ ...f, agency: e.target.value }))
                      }
                      placeholder="예: 국토교통부"
                      className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#8c8c8c] focus:outline-none focus:ring-2 focus:ring-[#3ecf8e]/40 focus:border-[#3ecf8e]/50 transition-colors"
                    />
                  </div>

                  <div>
                    <label className="block text-xs text-[#8c8c8c] mb-1">
                      마감일 <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="date"
                      required
                      value={formData.deadline}
                      onChange={(e) =>
                        setFormData((f) => ({
                          ...f,
                          deadline: e.target.value,
                        }))
                      }
                      className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] focus:outline-none focus:ring-2 focus:ring-[#3ecf8e]/40 focus:border-[#3ecf8e]/50 transition-colors [color-scheme:dark]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs text-[#8c8c8c] mb-1">
                      연결 제안서 ID (선택)
                    </label>
                    <input
                      type="text"
                      value={formData.proposal_id}
                      onChange={(e) =>
                        setFormData((f) => ({
                          ...f,
                          proposal_id: e.target.value,
                        }))
                      }
                      placeholder="제안서 UUID"
                      className="w-full bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#8c8c8c] focus:outline-none focus:ring-2 focus:ring-[#3ecf8e]/40 focus:border-[#3ecf8e]/50 transition-colors"
                    />
                  </div>
                </div>

                <div className="flex gap-2 pt-1">
                  <button
                    type="submit"
                    disabled={formSaving}
                    className="px-4 py-2 bg-[#3ecf8e] hover:bg-[#3ecf8e]/90 disabled:opacity-50 text-[#0f0f0f] text-sm font-semibold rounded-lg transition-colors"
                  >
                    {formSaving ? "저장 중..." : "저장"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddForm(false);
                      setFormData({
                        title: "",
                        agency: "",
                        deadline: "",
                        proposal_id: "",
                      });
                    }}
                    className="px-4 py-2 bg-[#262626] hover:bg-[#333] text-[#8c8c8c] hover:text-[#ededed] text-sm rounded-lg transition-colors"
                  >
                    취소
                  </button>
                </div>
              </form>
            )}

            {/* 캘린더 목록 */}
            {calLoading ? (
              <p className="text-sm text-[#8c8c8c] py-4">로딩 중...</p>
            ) : calItems.length === 0 ? (
              <div className="py-8 text-center">
                <p className="text-sm text-[#8c8c8c]">등록된 일정이 없습니다.</p>
                <p className="text-xs text-[#5c5c5c] mt-1">
                  위의 일정 추가 버튼으로 RFP 마감일을 등록하세요.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {calItems.map((item) => {
                  const days = calcDDay(item.deadline);
                  const ddColor = dDayColor(days);
                  const isClickable = !!item.proposal_id;
                  const deadlineDate = new Date(item.deadline).toLocaleDateString(
                    "ko-KR",
                    { month: "numeric", day: "numeric" }
                  );

                  return (
                    <div
                      key={item.id}
                      onClick={() => {
                        if (isClickable) {
                          router.push(`/proposals/${item.proposal_id}`);
                        }
                      }}
                      className={`flex items-center gap-3 px-4 py-3 rounded-xl border border-[#262626] bg-[#111111] transition-colors ${
                        isClickable
                          ? "cursor-pointer hover:border-[#3ecf8e]/30 hover:bg-[#1c1c1c]"
                          : ""
                      }`}
                    >
                      {/* D-Day 배지 */}
                      <div
                        className={`shrink-0 text-xs font-bold w-12 text-center ${ddColor}`}
                      >
                        {dDayLabel(days)}
                      </div>

                      {/* 내용 */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-[#ededed] truncate">
                          {item.title}
                        </p>
                        <p className="text-xs text-[#8c8c8c] mt-0.5">
                          {item.agency ? `${item.agency} · ` : ""}마감:{" "}
                          {deadlineDate}
                        </p>
                      </div>

                      {/* 상태 배지 */}
                      <div className="shrink-0">{statusBadge(item.status)}</div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

        </main>
      </div>
    </div>
  );
}
