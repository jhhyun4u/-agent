"use client";

/**
 * F-05: 추천 공고 목록 페이지
 * - 활성 프리셋 요약 배너
 * - 탭: 추천 공고 / 제외된 공고
 * - 추천 카드: Match Score, D-day, 카테고리 배지, 추천 요약
 */

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { api, RecommendedBid, ExcludedBid, SearchPreset, RecommendationReason } from "@/lib/api";

const POLL_INTERVAL_MS = 5000;
const POLL_MAX_ATTEMPTS = 12; // 최대 60초

const GRADE_COLOR: Record<string, string> = {
  S: "bg-purple-950/60 text-purple-400 border border-purple-900",
  A: "bg-emerald-950/60 text-emerald-400 border border-emerald-900",
  B: "bg-blue-950/60 text-blue-400 border border-blue-900",
  C: "bg-yellow-950/60 text-yellow-400 border border-yellow-900",
  D: "bg-[#1c1c1c] text-[#8c8c8c] border border-[#262626]",
};

const CATEGORY_ICON: Record<string, string> = {
  전문성: "⚡",
  실적: "📋",
  규모: "💰",
  기술: "🔧",
  지역: "📍",
  기타: "•",
};

function formatBudget(amount: number | null): string {
  if (!amount) return "미기재";
  if (amount >= 100_000_000) return `${(amount / 100_000_000).toFixed(1)}억`;
  if (amount >= 10_000) return `${(amount / 10_000).toFixed(0)}만`;
  return `${amount.toLocaleString()}원`;
}

function DdayBadge({ days }: { days: number | null }) {
  if (days === null) return null;
  const color =
    days <= 7
      ? "bg-red-950/60 text-red-400 border border-red-900"
      : days <= 14
      ? "bg-orange-950/60 text-orange-400 border border-orange-900"
      : "bg-[#1c1c1c] text-[#8c8c8c] border border-[#262626]";
  return (
    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${color}`}>
      D-{days}
    </span>
  );
}

function CategoryBadges({ reasons }: { reasons: RecommendationReason[] }) {
  const high = reasons.filter((r) => r.strength === "high").slice(0, 3);
  return (
    <div className="flex flex-wrap gap-1">
      {high.map((r, i) => (
        <span
          key={i}
          className="text-xs px-2 py-0.5 rounded-full bg-[#1c1c1c] border border-[#262626] text-[#8c8c8c]"
        >
          {CATEGORY_ICON[r.category] ?? "•"} {r.category}
        </span>
      ))}
    </div>
  );
}

export default function BidsPage() {
  const router = useRouter();
  const [teamId, setTeamId] = useState<string | null>(null);
  const [activePreset, setActivePreset] = useState<SearchPreset | null>(null);
  const [recommended, setRecommended] = useState<RecommendedBid[]>([]);
  const [excluded, setExcluded] = useState<ExcludedBid[]>([]);
  const [tab, setTab] = useState<"recommended" | "excluded">("recommended");
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [fetchPhase, setFetchPhase] = useState<"collecting" | "analyzing" | "">("");
  const [error, setError] = useState("");
  const [analyzedAt, setAnalyzedAt] = useState<string | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fetchStartTimeRef = useRef<number>(0);

  // 현재 팀 ID 조회
  useEffect(() => {
    (async () => {
      const { data } = await createClient().auth.getSession();
      if (!data.session) { router.push("/login"); return; }
      try {
        const res = await api.teams.list();
        const team = res.teams[0];
        if (!team) { router.push("/bids/settings"); return; }
        setTeamId(team.team_id);
      } catch {
        setError("팀 정보를 불러올 수 없습니다.");
        setLoading(false);
      }
    })();
  }, [router]);

  const loadData = useCallback(async (id: string) => {
    setLoading(true);
    setError("");
    try {
      // 활성 프리셋 조회
      const presetsRes = await api.bids.listPresets(id);
      const active = presetsRes.data.find((p) => p.is_active) ?? null;
      setActivePreset(active);

      if (!active) {
        setLoading(false);
        return;
      }

      // 추천 목록 조회
      const recRes = await api.bids.getRecommendations(id);
      setRecommended(recRes.data.recommended);
      setExcluded(recRes.data.excluded);
      setAnalyzedAt(recRes.meta.analyzed_at);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "오류가 발생했습니다.";
      if (!msg.includes("프리셋") && !msg.includes("프로필")) setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (teamId) loadData(teamId);
  }, [teamId, loadData]);

  async function handleFetch() {
    if (!teamId) return;

    // 기존 폴링 취소
    if (pollTimerRef.current) clearTimeout(pollTimerRef.current);

    setFetching(true);
    setFetchPhase("collecting");
    setError("");
    fetchStartTimeRef.current = Date.now();

    try {
      await api.bids.triggerFetch(teamId);
      setFetchPhase("analyzing");

      let attempts = 0;
      const poll = async () => {
        attempts++;
        try {
          const recRes = await api.bids.getRecommendations(teamId, true);
          const newAnalyzedAt = recRes.meta.analyzed_at;
          if (newAnalyzedAt && new Date(newAnalyzedAt).getTime() > fetchStartTimeRef.current) {
            // 분석 완료
            setRecommended(recRes.data.recommended);
            setExcluded(recRes.data.excluded);
            setAnalyzedAt(newAnalyzedAt);
            setFetching(false);
            setFetchPhase("");
            return;
          }
        } catch {
          // 폴링 중 일시 오류는 무시하고 재시도
        }

        if (attempts >= POLL_MAX_ATTEMPTS) {
          setFetching(false);
          setFetchPhase("");
          setError("수집 시간이 초과되었습니다. 잠시 후 새로고침하거나 다시 수집해 주세요.");
          return;
        }

        pollTimerRef.current = setTimeout(poll, POLL_INTERVAL_MS);
      };

      pollTimerRef.current = setTimeout(poll, POLL_INTERVAL_MS);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "수집 오류");
      setFetching(false);
      setFetchPhase("");
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-sm text-[#5c5c5c]">불러오는 중...</p>
      </div>
    );
  }

  if (!activePreset) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-6">
        <div className="w-12 h-12 rounded-xl bg-[#1c1c1c] border border-[#262626] flex items-center justify-center text-2xl">
          🔍
        </div>
        <h3 className="text-sm font-semibold text-[#ededed]">검색 조건이 없습니다</h3>
        <p className="text-xs text-[#8c8c8c] max-w-xs">
          팀 프로필과 검색 조건 프리셋을 설정하면 맞춤 공고 추천이 시작됩니다.
        </p>
        <Link
          href="/bids/settings"
          className="bg-[#3ecf8e] hover:bg-[#49e59e] text-black font-semibold rounded-lg px-5 py-2 text-sm transition-colors"
        >
          설정하기
        </Link>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
      {/* 헤더 */}
      <div className="border-b border-[#262626] px-6 py-4 shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-sm font-semibold text-[#ededed]">공고 추천</h1>
            <p className="text-xs text-[#8c8c8c] mt-0.5">
              {analyzedAt
                ? `마지막 분석: ${new Date(analyzedAt).toLocaleString("ko-KR")}`
                : "공고를 수집하면 AI가 팀에 맞는 공고를 추천합니다"}
            </p>
          </div>
          <div className="flex flex-col items-end gap-1">
            <button
              onClick={handleFetch}
              disabled={fetching}
              className="bg-[#3ecf8e] hover:bg-[#49e59e] disabled:opacity-50 text-black font-semibold rounded-lg px-4 py-2 text-xs transition-colors"
            >
              {fetching ? "수집 중..." : "공고 수집"}
            </button>
            {fetching && (
              <p className="text-[10px] text-[#5c5c5c]">
                {fetchPhase === "collecting" ? "나라장터 공고 수집 중..." : "AI 분석 중 (최대 1분)..."}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* 활성 프리셋 배너 */}
      <div className="border-b border-[#262626] px-6 py-2.5 shrink-0 bg-[#111111]">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-xs text-[#5c5c5c]">활성 프리셋:</span>
          <span className="text-xs font-medium text-[#ededed]">{activePreset.name}</span>
          <span className="text-xs text-[#5c5c5c]">
            키워드: {activePreset.keywords.join(", ")}
          </span>
          <span className="text-xs text-[#5c5c5c]">
            최소 {formatBudget(activePreset.min_budget)}
          </span>
          <span className="text-xs text-[#5c5c5c]">
            잔여 {activePreset.min_days_remaining}일 이상
          </span>
          <Link href="/bids/settings" className="text-xs text-[#3ecf8e] hover:underline ml-auto">
            설정 변경
          </Link>
        </div>
      </div>

      {/* 탭 */}
      <div className="border-b border-[#262626] px-6 shrink-0">
        <div className="flex gap-0">
          {(["recommended", "excluded"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors ${
                tab === t
                  ? "border-[#3ecf8e] text-[#ededed]"
                  : "border-transparent text-[#8c8c8c] hover:text-[#ededed]"
              }`}
            >
              {t === "recommended"
                ? `추천 공고 ${recommended.length}건`
                : `제외된 공고 ${excluded.length}건`}
            </button>
          ))}
        </div>
      </div>

      {/* 에러 */}
      {error && (
        <div className="mx-6 mt-3 px-4 py-2 bg-red-950/40 border border-red-900/50 rounded-lg text-xs text-red-400">
          {error}
        </div>
      )}

      {/* 콘텐츠 */}
      <div className="flex-1 overflow-auto px-6 py-4 space-y-3">
        {tab === "recommended" ? (
          recommended.length === 0 ? (
            <EmptyRecommended onFetch={handleFetch} fetching={fetching} />
          ) : (
            recommended.map((bid) => (
              <RecommendedCard key={bid.bid_no} bid={bid} teamId={teamId!} />
            ))
          )
        ) : (
          excluded.length === 0 ? (
            <div className="flex items-center justify-center h-32">
              <p className="text-sm text-[#5c5c5c]">제외된 공고가 없습니다</p>
            </div>
          ) : (
            excluded.map((bid) => <ExcludedCard key={bid.bid_no} bid={bid} teamId={teamId!} />)
          )
        )}
      </div>
    </div>
  );
}

function RecommendedCard({ bid, teamId }: { bid: RecommendedBid; teamId: string }) {
  return (
    <Link
      href={`/bids/${bid.bid_no}?team_id=${teamId}`}
      className="block rounded-lg border border-[#262626] bg-[#111111] hover:bg-[#161616] transition-colors p-4"
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-xs px-2 py-0.5 rounded-md font-bold ${GRADE_COLOR[bid.match_grade] ?? GRADE_COLOR.D}`}>
            {bid.match_score}점 {bid.match_grade}
          </span>
          <DdayBadge days={bid.days_remaining} />
          {bid.qualification_status === "ambiguous" && (
            <span className="text-xs px-2 py-0.5 rounded-md bg-orange-950/60 text-orange-400 border border-orange-900">
              자격 확인 필요
            </span>
          )}
        </div>
        <span className="text-xs text-[#8c8c8c] shrink-0">{bid.recommended_action}</span>
      </div>

      <h3 className="text-sm font-medium text-[#ededed] mb-1 line-clamp-1">{bid.bid_title}</h3>

      <div className="flex items-center gap-2 text-xs text-[#5c5c5c] mb-3">
        <span>{bid.agency}</span>
        {bid.budget_amount && (
          <>
            <span>·</span>
            <span>{formatBudget(bid.budget_amount)}</span>
          </>
        )}
      </div>

      <CategoryBadges reasons={bid.recommendation_reasons} />

      {bid.recommendation_summary && (
        <p className="text-xs text-[#8c8c8c] mt-2 line-clamp-2 italic">
          "{bid.recommendation_summary}"
        </p>
      )}
    </Link>
  );
}

function ExcludedCard({ bid, teamId }: { bid: ExcludedBid; teamId: string }) {
  return (
    <Link
      href={`/bids/${bid.bid_no}?team_id=${teamId}`}
      className="block rounded-lg border border-[#262626] bg-[#111111] hover:bg-[#161616] transition-colors p-4 opacity-70 hover:opacity-90"
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs px-2 py-0.5 rounded-md bg-red-950/60 text-red-400 border border-red-900">
          자격 불충족
        </span>
        {bid.budget_amount && (
          <span className="text-xs text-[#5c5c5c]">{formatBudget(bid.budget_amount)}</span>
        )}
        <span className="text-xs text-[#3c3c3c] ml-auto">원문 보기 →</span>
      </div>
      <h3 className="text-sm font-medium text-[#ededed] mb-1 line-clamp-1">{bid.bid_title}</h3>
      <p className="text-xs text-[#5c5c5c] mb-1">{bid.agency}</p>
      {bid.disqualification_reason && (
        <p className="text-xs text-red-400/80 mt-1">{bid.disqualification_reason}</p>
      )}
    </Link>
  );
}

function EmptyRecommended({ onFetch, fetching }: { onFetch: () => void; fetching: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-center">
      <div className="w-12 h-12 rounded-xl bg-[#1c1c1c] border border-[#262626] flex items-center justify-center text-2xl mb-4">
        📡
      </div>
      <h3 className="text-sm font-semibold text-[#ededed] mb-1">추천 공고가 없습니다</h3>
      <p className="text-xs text-[#8c8c8c] mb-6 max-w-xs">
        공고를 수집하면 AI가 팀 역량에 맞는 공고를 추천합니다.
      </p>
      <button
        onClick={onFetch}
        disabled={fetching}
        className="bg-[#3ecf8e] hover:bg-[#49e59e] disabled:opacity-50 text-black font-semibold rounded-lg px-5 py-2 text-sm transition-colors"
      >
        {fetching ? "수집 중..." : "지금 수집하기"}
      </button>
    </div>
  );
}
