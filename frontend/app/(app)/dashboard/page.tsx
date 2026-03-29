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
import {
  api, CalendarItem, WinRateStats, ProposalSummary, RecommendedBid,
  type FailureReasonsData, type MonthlyTrendsData, type ClientWinRateData,
  type TeamPerformanceData, type PositioningWinRateData,
} from "@/lib/api";
import {
  FailureReasonsPie,
  MonthlyTrendsLine,
  ClientWinRateBar,
} from "@/components/AnalyticsCharts";
import GuidedTour, { TOUR_DASHBOARD } from "@/components/GuidedTour";

// ── 타입 ──────────────────────────────────────────────────────────────

type Scope = "team" | "division" | "company";

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

  // 스코프 (팀/본부/전체만 제공, 개인 제거)
  const [scope, setScope] = useState<Scope>("team");

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

  // 분석 차트
  const [failureData, setFailureData] = useState<FailureReasonsData | null>(null);
  const [trendsData, setTrendsData] = useState<MonthlyTrendsData | null>(null);
  const [clientData, setClientData] = useState<ClientWinRateData | null>(null);

  // 팀 성과 + 포지셔닝별 수주율
  const [teamPerfData, setTeamPerfData] = useState<TeamPerformanceData | null>(null);
  const [posWinData, setPosWinData] = useState<PositioningWinRateData | null>(null);

  // 권고 #6: 대시보드 위젯 토글
  const [widgetConfig, setWidgetConfig] = useState(() => {
    if (typeof window === "undefined") return { action: true, pipeline: true, kpi: true, charts: true, client: true, team: true, positioning: true, bids: true, calendar: true };
    try {
      const stored = localStorage.getItem("tenopa-dashboard-widgets");
      return stored ? JSON.parse(stored) : { action: true, pipeline: true, kpi: true, charts: true, client: true, team: true, positioning: true, bids: true, calendar: true };
    } catch { return { action: true, pipeline: true, kpi: true, charts: true, client: true, team: true, positioning: true, bids: true, calendar: true }; }
  });
  const [showWidgetConfig, setShowWidgetConfig] = useState(false);
  function toggleWidget(key: string) {
    setWidgetConfig((prev: Record<string, boolean>) => {
      const next = { ...prev, [key]: !prev[key] };
      localStorage.setItem("tenopa-dashboard-widgets", JSON.stringify(next));
      return next;
    });
  }

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
      setProposals(res.data);
    } catch {
      setProposals([]);
    }
  }, []);

  const loadCalendar = useCallback(async () => {
    setCalLoading(true);
    try {
      const data = await api.calendar.list({ scope });
      const sorted = [...data.data].sort(
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

  const loadAnalytics = useCallback(async () => {
    const results = await Promise.allSettled([
      api.analytics.failureReasons({}),
      api.analytics.monthlyTrends({}),
      api.analytics.clientWinRate({}),
      api.analytics.teamPerformance({}),
      api.analytics.positioningWinRate({}),
    ]);
    setFailureData(results[0].status === "fulfilled" ? results[0].value : null);
    setTrendsData(results[1].status === "fulfilled" ? results[1].value : null);
    setClientData(results[2].status === "fulfilled" ? results[2].value : null);
    setTeamPerfData(results[3].status === "fulfilled" ? results[3].value : null);
    setPosWinData(results[4].status === "fulfilled" ? results[4].value : null);
  }, []);

  useEffect(() => {
    loadStats(scope);
    loadCalendar();
    loadProposals();
    loadBidRecommendations();
    loadAnalytics();
  }, [scope, loadStats, loadCalendar, loadProposals, loadBidRecommendations, loadAnalytics]);

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
    <>
        {/* 상단 헤더 */}
        <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 shrink-0 flex items-center justify-between">
          <h1 className="text-sm font-semibold text-[#ededed]">
            대시보드
          </h1>

          {/* 위젯 설정 + 스코프 탭 */}
          <div className="flex items-center gap-3">
          {/* 권고 #6: 위젯 표시/숨김 토글 */}
          <div className="relative">
            <button
              onClick={() => setShowWidgetConfig(!showWidgetConfig)}
              className="p-1.5 rounded-lg text-[#8c8c8c] hover:text-[#ededed] hover:bg-[#262626] transition-colors"
              title="위젯 설정"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
            {showWidgetConfig && (
              <>
                <div className="fixed inset-0 z-30" onClick={() => setShowWidgetConfig(false)} />
                <div className="absolute right-0 mt-1.5 w-48 bg-[#1c1c1c] border border-[#262626] rounded-xl shadow-xl z-40 py-2">
                  <p className="px-3 py-1.5 text-[10px] text-[#8c8c8c] uppercase tracking-wider">위젯 표시</p>
                  {([
                    ["action", "지금 해야 할 것"],
                    ["pipeline", "제안 파이프라인"],
                    ["kpi", "제안 분석 KPI"],
                    ["charts", "분석 차트"],
                    ["client", "기관별 수주"],
                    ["team", "팀별 성과"],
                    ["positioning", "포지셔닝별"],
                    ["bids", "공고 모니터링"],
                    ["calendar", "RFP 캘린더"],
                  ] as const).map(([key, label]) => (
                    <button
                      key={key}
                      onClick={() => toggleWidget(key)}
                      className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#ededed] hover:bg-[#262626] transition-colors"
                    >
                      <span className={`w-3.5 h-3.5 rounded border flex items-center justify-center text-[9px] ${widgetConfig[key] ? "bg-[#3ecf8e] border-[#3ecf8e] text-[#0f0f0f]" : "border-[#363636]"}`}>
                        {widgetConfig[key] ? "v" : ""}
                      </span>
                      {label}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          <div className="flex items-center gap-1 bg-[#1c1c1c] rounded-lg p-1 border border-[#262626]">
            {(
              [
                { key: "team" as Scope, label: "팀" },
                { key: "division" as Scope, label: "본부" },
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
          </div>
        </header>

        {/* 스크롤 본문 */}
        <main className="flex-1 overflow-y-auto px-6 py-5 space-y-5">

          {/* ── 결재 대기 (팀장용) ── */}
          {scope === "team" && (() => {
            const pendingReviews = proposals.filter(
              (p) => p.status === "paused" || p.status === "on_hold"
            );
            if (pendingReviews.length === 0) return null;
            return (
              <div className="bg-[#1c1c1c] border border-amber-500/20 rounded-2xl p-5">
                <h2 className="text-sm font-semibold text-[#ededed] mb-3 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                  결재 대기
                  <span className="text-[10px] text-amber-400/80 bg-amber-500/10 px-2 py-0.5 rounded">
                    {pendingReviews.length}건
                  </span>
                </h2>
                <div className="space-y-2">
                  {pendingReviews.map((p) => {
                    const days = p.deadline ? calcDDay(p.deadline) : null;
                    return (
                      <div
                        key={p.id}
                        onClick={() => router.push(`/proposals/${p.id}`)}
                        className="flex items-center gap-3 px-4 py-3 rounded-xl bg-[#111111] border border-[#262626] cursor-pointer hover:border-amber-500/30 transition-colors"
                      >
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-[#ededed] truncate">{p.title}</p>
                          <p className="text-xs text-[#8c8c8c] mt-0.5">
                            {p.current_phase ?? "리뷰 대기"}
                          </p>
                        </div>
                        {days != null && (
                          <span className={`shrink-0 text-xs font-bold ${dDayColor(days)}`}>
                            {dDayLabel(days)}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })()}

          {/* ── 마감 임박 경고 (팀장용) ── */}
          {scope === "team" && (() => {
            const urgentItems = calItems
              .filter((c) => {
                const d = calcDDay(c.deadline);
                return d >= 0 && d <= 7;
              })
              .sort((a, b) => calcDDay(a.deadline) - calcDDay(b.deadline));
            if (urgentItems.length === 0) return null;
            return (
              <div className="bg-[#1c1c1c] border border-red-500/20 rounded-2xl p-5">
                <h2 className="text-sm font-semibold text-[#ededed] mb-3 flex items-center gap-2">
                  <span className="text-red-400">!</span>
                  마감 임박
                  <span className="text-[10px] text-red-400/80 bg-red-500/10 px-2 py-0.5 rounded">
                    D-7 이내 {urgentItems.length}건
                  </span>
                </h2>
                <div className="space-y-2">
                  {urgentItems.map((c) => {
                    const days = calcDDay(c.deadline);
                    const relatedProposal = c.proposal_id
                      ? proposals.find((p) => p.id === c.proposal_id)
                      : null;
                    return (
                      <div
                        key={c.id}
                        onClick={() =>
                          c.proposal_id
                            ? router.push(`/proposals/${c.proposal_id}`)
                            : undefined
                        }
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl bg-[#111111] border border-[#262626] ${c.proposal_id ? "cursor-pointer hover:border-red-500/30" : ""} transition-colors`}
                      >
                        <span className={`shrink-0 text-xs font-bold w-10 text-center ${days <= 3 ? "text-red-400" : "text-yellow-400"}`}>
                          {dDayLabel(days)}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-[#ededed] truncate">{c.title}</p>
                          <p className="text-xs text-[#8c8c8c] mt-0.5">
                            {relatedProposal
                              ? relatedProposal.current_phase ?? relatedProposal.status
                              : "제안서 미생성"}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })()}

          {/* ── 본부별 성과 비교 (경영진용) ── */}
          {scope === "company" && teamPerfData && teamPerfData.teams.length > 0 && (
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
              <h2 className="text-sm font-semibold text-[#ededed] mb-3">본부별 성과 비교</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-[#8c8c8c] border-b border-[#262626]">
                      <th className="text-left py-2 pr-3 font-medium">본부/팀</th>
                      <th className="text-right py-2 px-3 font-medium">진행건</th>
                      <th className="text-right py-2 px-3 font-medium">수주율</th>
                      <th className="text-right py-2 px-3 font-medium">평균 소요</th>
                      <th className="text-right py-2 pl-3 font-medium">전월 대비</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(() => {
                      const avgRate = teamPerfData.teams.length > 0
                        ? teamPerfData.teams.reduce((s, t) => s + t.rate, 0) / teamPerfData.teams.length
                        : 0;
                      return [...teamPerfData.teams]
                        .sort((a, b) => b.rate - a.rate)
                        .map((t) => {
                          const diff = t.rate - avgRate;
                          return (
                            <tr key={t.team_id} className="border-b border-[#1a1a1a] hover:bg-[#111111]">
                              <td className="py-2 pr-3 text-[#ededed] font-medium">{t.team_name}</td>
                              <td className="py-2 px-3 text-right text-[#8c8c8c]">{t.total}건</td>
                              <td className={`py-2 px-3 text-right font-bold ${t.rate >= 0.5 ? "text-[#3ecf8e]" : t.rate >= 0.3 ? "text-amber-400" : "text-red-400"}`}>
                                {(t.rate * 100).toFixed(0)}%
                              </td>
                              <td className="py-2 px-3 text-right text-[#5c5c5c]">{t.avg_duration_days}일</td>
                              <td className={`py-2 pl-3 text-right text-xs font-medium ${diff > 0 ? "text-[#3ecf8e]" : diff < 0 ? "text-red-400" : "text-[#5c5c5c]"}`}>
                                {diff > 0 ? `▲ +${(diff * 100).toFixed(0)}%p` : diff < 0 ? `▼ ${(diff * 100).toFixed(0)}%p` : "-"}
                              </td>
                            </tr>
                          );
                        });
                    })()}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ── 오늘 할 일 ── */}
          {widgetConfig.action && actionItems.length > 0 && (
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
          {widgetConfig.pipeline && <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
            <h2 className="text-sm font-semibold text-[#ededed] mb-4">제안 파이프라인</h2>
            <div className="flex items-stretch gap-0">
              {(
                [
                  { label: "공고 등록", count: pipeline.registered, color: "text-[#8c8c8c]", href: "/monitoring" },
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
          </div>}

          {/* ── 제안 분석 (3개 카드 — 연도별) ── */}
          {widgetConfig.kpi && <div className="grid grid-cols-3 gap-4">
            {/* 총 제안건수 */}
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-4">
              <p className="text-xs text-[#8c8c8c] mb-2">{new Date().getFullYear()}년 총 제안건수</p>
              <p className="text-3xl font-bold text-[#ededed]">
                {stats?.overall.total ?? 0}
                <span className="text-base font-normal text-[#8c8c8c] ml-1">건</span>
              </p>
            </div>

            {/* 수주 성공 건수 */}
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-4">
              <p className="text-xs text-[#8c8c8c] mb-2">{new Date().getFullYear()}년 수주 성공</p>
              <p className="text-3xl font-bold text-[#3ecf8e]">
                {stats?.overall.won ?? 0}
                <span className="text-base font-normal text-[#8c8c8c] ml-1">건</span>
              </p>
              {stats && stats.overall.total > 0 && (
                <p className="text-xs text-[#8c8c8c] mt-1">
                  수주율 {(stats.overall.rate * 100).toFixed(1)}%
                </p>
              )}
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
                  <p className="text-xs text-[#8c8c8c] mt-1">
                    {thisMonthData.total}건 중 {thisMonthData.won}건 수주
                  </p>
                </>
              ) : (
                <p className="text-3xl font-bold text-[#8c8c8c]">N/A</p>
              )}
            </div>
          </div>}

          {/* ── 분석 차트 (월별 추이 + 실패원인) ── */}
          {widgetConfig.charts && <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
              <h2 className="text-sm font-semibold text-[#ededed] mb-4">월별 수주율 추이</h2>
              <MonthlyTrendsLine data={trendsData} />
            </div>
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
              <h2 className="text-sm font-semibold text-[#ededed] mb-4">실패 원인 분석</h2>
              <FailureReasonsPie data={failureData} />
            </div>
          </div>}

          {/* ── 기관별 수주 현황 차트 ── */}
          {widgetConfig.client && clientData && (
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
              <h2 className="text-sm font-semibold text-[#ededed] mb-4">기관별 수주 현황</h2>
              <ClientWinRateBar data={clientData} />
            </div>
          )}

          {/* ── 팀 성과 + 포지셔닝별 수주율 ── */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 팀 성과 */}
            {widgetConfig.team && teamPerfData && teamPerfData.teams.length > 0 && (
              <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
                <h2 className="text-sm font-semibold text-[#ededed] mb-3">팀별 성과</h2>
                <div className="space-y-2">
                  {teamPerfData.teams.map((t) => (
                    <div key={t.team_id} className="flex items-center gap-3 bg-[#111111] rounded-lg px-3 py-2">
                      <span className="text-xs text-[#ededed] font-medium flex-1 truncate">{t.team_name}</span>
                      <span className="text-xs text-[#8c8c8c]">{t.total}건</span>
                      <span className={`text-xs font-bold ${t.rate >= 0.5 ? "text-[#3ecf8e]" : t.rate >= 0.3 ? "text-amber-400" : "text-red-400"}`}>
                        {(t.rate * 100).toFixed(0)}%
                      </span>
                      <span className="text-[10px] text-[#5c5c5c]">평균 {t.avg_duration_days}일</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 포지셔닝별 수주율 */}
            {widgetConfig.positioning && posWinData && posWinData.positioning.length > 0 && (
              <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
                <h2 className="text-sm font-semibold text-[#ededed] mb-3">포지셔닝별 수주율</h2>
                <div className="space-y-2">
                  {posWinData.positioning.map((p) => {
                    const posLabel = p.type === "defensive" ? "🛡️ 수성형" : p.type === "offensive" ? "⚔️ 공격형" : p.type === "adjacent" ? "🔄 인접형" : p.type;
                    return (
                      <div key={p.type} className="bg-[#111111] rounded-lg px-3 py-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-[#ededed]">{posLabel}</span>
                          <span className="text-xs text-[#8c8c8c]">{p.won}/{p.total}건</span>
                        </div>
                        <div className="h-1.5 bg-[#262626] rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${p.rate >= 0.5 ? "bg-[#3ecf8e]" : p.rate >= 0.3 ? "bg-amber-500" : "bg-red-500"}`}
                            style={{ width: `${p.rate * 100}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* ── 공고 모니터링 위젯 ── */}
          {widgetConfig.bids && !bidsLoading && (bidCounts.S > 0 || bidCounts.A > 0) && (
            <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <h2 className="text-sm font-semibold text-[#ededed]">공고 모니터링</h2>
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
                  onClick={() => router.push("/monitoring")}
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
                          `/monitoring/${bid.bid_no}${teamId ? `?team_id=${teamId}` : ""}`
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

          {/* ── RFP 캘린더 ── */}
          {widgetConfig.calendar && <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
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
          </div>}

        </main>
      {/* 권고 #2: 초보 사용자 가이드 투어 */}
      <GuidedTour tourId="dashboard" steps={TOUR_DASHBOARD} />
    </>
  );
}
