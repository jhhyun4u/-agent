"use client";

/**
 * F-05: 공고 모니터링 페이지
 * - 탭: My Page / Our Team / TENOPA
 * - My Page: 관심분야 자동매칭 + 북마크
 * - Our Team: 소속 팀 추천 공고
 * - TENOPA: 전체 진행중 공고
 */

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, MonitoredBid, ScoredBid, BidAttachment } from "@/lib/api";

type ViewMode = "scored" | "monitor";
type Scope = "my" | "team" | "division" | "company";

const SCOPE_LABELS: Record<Scope, { label: string; desc: string }> = {
  my: { label: "개인", desc: "내 관심 분야 + 북마크 공고" },
  team: { label: "팀", desc: "우리 팀 추천 공고" },
  division: { label: "본부", desc: "우리 본부 추천 공고" },
  company: { label: "전체", desc: "TENOPA 전체 진행중 공고" },
};

const GRADE_COLOR: Record<string, string> = {
  S: "bg-purple-950/60 text-purple-400 border border-purple-900",
  A: "bg-emerald-950/60 text-emerald-400 border border-emerald-900",
  B: "bg-blue-950/60 text-blue-400 border border-blue-900",
  C: "bg-yellow-950/60 text-yellow-400 border border-yellow-900",
  D: "bg-[#1c1c1c] text-[#8c8c8c] border border-[#262626]",
};

function formatBudget(amount: number | null): string {
  if (!amount) return "미기재";
  if (amount >= 100_000_000) return `${(amount / 100_000_000).toFixed(1)}억`;
  if (amount >= 10_000) return `${(amount / 10_000).toFixed(0)}만`;
  return `${amount.toLocaleString()}원`;
}

function DdayBadge({ days }: { days: number | null }) {
  if (days === null || days === undefined) return null;
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

export default function BidsMonitorPage() {
  const router = useRouter();
  const [viewMode, setViewMode] = useState<ViewMode>("scored");
  const [scope, setScope] = useState<Scope>("company");
  const [bids, setBids] = useState<MonitoredBid[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [showAll, setShowAll] = useState(false);

  const loadBids = useCallback(async (s: Scope, p: number) => {
    setLoading(true);
    setError("");
    try {
      // 인증 토큰 포함 시도
      const res = await api.bids.monitor(s, p, showAll);
      setBids(res.data || []);
      setTotal(res.meta?.total || 0);
    } catch {
      // 인증 실패 시 — 토큰 없이 직접 호출 (company 스코프)
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
        const directRes = await fetch(`${baseUrl}/bids/monitor?scope=company&page=${p}&show_all=${showAll}`);
        if (directRes.ok) {
          const json = await directRes.json();
          setBids(json.data || []);
          setTotal(json.meta?.total || 0);
          return;
        }
      } catch {
        setError("백엔드에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.");
      }
      setBids([]);
    } finally {
      setLoading(false);
    }
  }, [showAll]);

  useEffect(() => {
    setPage(1);
    loadBids(scope, 1);
  }, [scope, showAll, loadBids]);

  useEffect(() => {
    if (page > 1) loadBids(scope, page);
  }, [page, scope, loadBids]);

  async function handleStatusChange(bidNo: string, status: "검토중" | "제안착수" | "관련없음") {
    try {
      await api.bids.updateStatus(bidNo, status);
      setBids((prev) =>
        prev.map((b) =>
          b.bid_no === bidNo ? { ...b, proposal_status: status } : b
        )
      );
    } catch {
      // 인증 없이는 실패할 수 있음 — 무시
    }
  }

  async function handleBookmark(bidNo: string) {
    try {
      const res = await api.bids.toggleBookmark(bidNo);
      setBids((prev) =>
        prev.map((b) =>
          b.bid_no === bidNo ? { ...b, is_bookmarked: res.bookmarked } : b
        )
      );
    } catch {
      // 무시
    }
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
      {/* 헤더 */}
      <div className="border-b border-[#262626] px-6 py-4 shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-sm font-semibold text-[#ededed]">공고 모니터링</h1>
            <p className="text-xs text-[#8c8c8c] mt-0.5">
              {viewMode === "scored"
                ? "AI 적합도 스코어링 기반 추천"
                : SCOPE_LABELS[scope].desc}
              {total > 0 && ` · ${total}건`}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* 뷰 모드 토글 */}
            <div className="flex items-center gap-1 bg-[#1c1c1c] rounded-lg p-1 border border-[#262626]">
              <button
                onClick={() => setViewMode("scored")}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  viewMode === "scored"
                    ? "bg-[#3ecf8e] text-[#0f0f0f]"
                    : "text-[#8c8c8c] hover:text-[#ededed]"
                }`}
              >
                AI 추천
              </button>
              <button
                onClick={() => setViewMode("monitor")}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  viewMode === "monitor"
                    ? "bg-[#3ecf8e] text-[#0f0f0f]"
                    : "text-[#8c8c8c] hover:text-[#ededed]"
                }`}
              >
                모니터링
              </button>
            </div>

            {/* 스코프 탭 (모니터링 모드에서만) */}
            {viewMode === "monitor" && (
              <div className="flex items-center gap-1 bg-[#1c1c1c] rounded-lg p-1 border border-[#262626]">
                {(["my", "team", "division", "company"] as Scope[]).map((s) => (
                  <button
                    key={s}
                    onClick={() => setScope(s)}
                    className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      scope === s
                        ? "bg-[#3ecf8e] text-[#0f0f0f]"
                        : "text-[#8c8c8c] hover:text-[#ededed]"
                    }`}
                  >
                    {SCOPE_LABELS[s].label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 필터 바 (모니터링 모드에서만) */}
        {viewMode === "monitor" && (
          <div className="flex items-center justify-end px-2 pt-2">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={showAll}
                onChange={(e) => setShowAll(e.target.checked)}
                className="w-3 h-3 rounded border-[#262626] bg-[#1c1c1c] accent-[#3ecf8e]"
              />
              <span className="text-[10px] text-[#5c5c5c]">포기/관련없음 포함</span>
            </label>
          </div>
        )}
      </div>

      {/* 에러 */}
      {error && (
        <div className="mx-6 mt-3 px-4 py-2 bg-red-950/40 border border-red-900/50 rounded-lg text-xs text-red-400">
          {error}
        </div>
      )}

      {/* 콘텐츠 */}
      <div className="flex-1 overflow-auto px-6 py-4">
        {viewMode === "scored" ? (
          <ScoredBidsView />
        ) : loading ? (
          <div className="flex items-center justify-center h-40">
            <p className="text-sm text-[#5c5c5c]">불러오는 중...</p>
          </div>
        ) : bids.length === 0 ? (
          <EmptyState scope={scope} />
        ) : (
          <>
            <div className="rounded-lg border border-[#262626] bg-[#111111] overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#262626] bg-[#0f0f0f]">
                    <th className="text-center px-2 py-2.5 text-xs font-medium text-[#5c5c5c] w-8"></th>
                    <th className="text-center px-2 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">단계</th>
                    <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">공고명</th>
                    <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">발주처</th>
                    <th className="text-right px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">용역비</th>
                    <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">마감일</th>
                    <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">관련 팀</th>
                    <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">관련성</th>
                    <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">공고문</th>
                    <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">제안요청서</th>
                    <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">과업지시서</th>
                    <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">검토결과</th>
                  </tr>
                </thead>
                <tbody>
                  {bids.map((bid) => (
                    <BidRow
                      key={bid.bid_no}
                      bid={bid}
                      scope={scope}
                      onBookmark={handleBookmark}
                      onStatusChange={handleStatusChange}
                      onClick={() => router.push(`/bids/${bid.bid_no}/review`)}
                    />
                  ))}
                </tbody>
              </table>
            </div>

            {/* 페이지네이션 */}
            {total > 30 && (
              <div className="flex items-center justify-center gap-2 mt-4">
                <button
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="px-3 py-1.5 text-xs border border-[#262626] rounded-lg text-[#8c8c8c] disabled:opacity-40 hover:bg-[#1c1c1c] transition-colors"
                >
                  이전
                </button>
                <span className="px-3 py-1.5 text-xs text-[#8c8c8c]">{page}</span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1.5 text-xs border border-[#262626] rounded-lg text-[#8c8c8c] hover:bg-[#1c1c1c] transition-colors"
                >
                  다음
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── AI 추천 (Scored) 뷰 ──────────────────────────────────

function ScoredBidsView() {
  const router = useRouter();
  const [bids, setBids] = useState<ScoredBid[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [days, setDays] = useState(7);
  const [minScore, setMinScore] = useState(20);
  const [totalFetched, setTotalFetched] = useState(0);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sources, setSources] = useState<Record<string, number>>({});
  const [stageFilter, setStageFilter] = useState<Set<string>>(
    new Set(["입찰공고", "사전규격", "발주계획"])
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.bids.scored({ days, minScore, maxResults: 200 });
      setBids(res.data || []);
      setTotalFetched(res.total_fetched || 0);
      setDateFrom(res.date_from || "");
      setDateTo(res.date_to || "");
      setSources(res.sources || {});
    } catch {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
        const directRes = await fetch(`${baseUrl}/bids/scored?days=${days}&min_score=${minScore}&max_results=200`);
        if (directRes.ok) {
          const json = await directRes.json();
          setBids(json.data || []);
          setTotalFetched(json.total_fetched || 0);
          setDateFrom(json.date_from || "");
          setDateTo(json.date_to || "");
          setSources(json.sources || {});
          return;
        }
      } catch {
        setError("백엔드에 연결할 수 없습니다.");
      }
      setBids([]);
    } finally {
      setLoading(false);
    }
  }, [days, minScore]);

  useEffect(() => { load(); }, [load]);

  const filteredBids = bids.filter((b) => stageFilter.has(b.bid_stage || "입찰공고"));

  function toggleStage(stage: string) {
    setStageFilter((prev) => {
      const next = new Set(prev);
      if (next.has(stage)) {
        if (next.size > 1) next.delete(stage);
      } else {
        next.add(stage);
      }
      return next;
    });
  }

  function scoreColor(score: number): string {
    if (score >= 120) return "text-purple-400 bg-purple-950/60 border-purple-900";
    if (score >= 100) return "text-emerald-400 bg-emerald-950/60 border-emerald-900";
    if (score >= 80) return "text-blue-400 bg-blue-950/60 border-blue-900";
    if (score >= 50) return "text-yellow-400 bg-yellow-950/60 border-yellow-900";
    return "text-[#8c8c8c] bg-[#1c1c1c] border-[#262626]";
  }

  if (error) {
    return (
      <div className="mx-2 mt-3 px-4 py-2 bg-red-950/40 border border-red-900/50 rounded-lg text-xs text-red-400">
        {error}
      </div>
    );
  }

  return (
    <div>
      {/* 필터 바 */}
      <div className="flex items-center gap-4 mb-4">
        <label className="flex items-center gap-1.5 text-xs text-[#8c8c8c]">
          기간
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-xs text-[#ededed]"
          >
            <option value={1}>당일</option>
            <option value={3}>3일</option>
            <option value={5}>5일</option>
            <option value={7}>7일</option>
            <option value={10}>10일</option>
            <option value={14}>14일</option>
            <option value={30}>30일</option>
          </select>
        </label>
        <label className="flex items-center gap-1.5 text-xs text-[#8c8c8c]">
          최소 점수
          <select
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
            className="bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-xs text-[#ededed]"
          >
            <option value={0}>전체</option>
            <option value={20}>20+</option>
            <option value={50}>50+</option>
            <option value={80}>80+</option>
            <option value={100}>100+</option>
          </select>
        </label>
        <div className="flex items-center gap-2 text-[10px] text-[#5c5c5c]">
          {(["입찰공고", "사전규격", "발주계획"] as const).map((stage) => (
            <label key={stage} className="flex items-center gap-1 cursor-pointer">
              <input
                type="checkbox"
                checked={stageFilter.has(stage)}
                onChange={() => toggleStage(stage)}
                className="w-3 h-3 rounded border-[#262626] bg-[#1c1c1c] accent-[#3ecf8e]"
              />
              <span>{stage === "입찰공고" ? "공고" : stage === "사전규격" ? "사전" : "계획"}</span>
            </label>
          ))}
        </div>
        <span className="text-[10px] text-[#5c5c5c] ml-auto">
          {loading ? "검색 중..." : dateFrom && dateTo ? (
            `${dateFrom.slice(4,6)}/${dateFrom.slice(6,8)}~${dateTo.slice(4,6)}/${dateTo.slice(6,8)} (${days}일간) · 전수 ${totalFetched.toLocaleString()}건 중 ${filteredBids.length}건 추천` +
            (Object.values(sources).some(v => v > 0)
              ? ` (${[
                  sources["입찰공고"] ? `공고 ${sources["입찰공고"]}` : "",
                  sources["사전규격"] ? `사전 ${sources["사전규격"]}` : "",
                  sources["발주계획"] ? `계획 ${sources["발주계획"]}` : "",
                ].filter(Boolean).join(" · ")})`
              : "")
          ) : `${filteredBids.length}건`}
        </span>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <p className="text-sm text-[#5c5c5c]">G2B 전수 수집 + 스코어링 중...</p>
        </div>
      ) : filteredBids.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-40 text-center">
          <p className="text-sm text-[#8c8c8c]">조건에 맞는 공고가 없습니다</p>
          <p className="text-xs text-[#5c5c5c] mt-1">기간을 늘리거나 최소 점수를 낮춰보세요</p>
        </div>
      ) : (
        <div className="rounded-lg border border-[#262626] bg-[#111111] overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#262626] bg-[#0f0f0f]">
                <th className="text-center px-2 py-2.5 text-xs font-medium text-[#5c5c5c] w-10">#</th>
                <th className="text-center px-2 py-2.5 text-xs font-medium text-[#5c5c5c] w-14">단계</th>
                <th className="text-center px-2 py-2.5 text-xs font-medium text-[#5c5c5c] w-16">적합도</th>
                <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c]">공고명</th>
                <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">발주기관</th>
                <th className="text-right px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">예산</th>
                <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">마감</th>
                <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">역할 키워드</th>
                <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">도메인</th>
                <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">분류</th>
              </tr>
            </thead>
            <tbody>
              {filteredBids.map((bid, idx) => (
                <tr
                  key={bid.bid_no}
                  onClick={() => router.push(`/bids/${bid.bid_no}/review`)}
                  className="border-b border-[#1a1a1a] last:border-0 hover:bg-[#161616] transition-colors cursor-pointer"
                >
                  <td className="px-2 py-3 text-center text-xs text-[#5c5c5c]">{idx + 1}</td>
                  <td className="px-2 py-3 text-center">
                    <StageBadge stage={bid.bid_stage || "입찰공고"} />
                  </td>
                  <td className="px-2 py-3 text-center">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-md border ${scoreColor(bid.score)}`}>
                      {bid.score.toFixed(0)}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    <span className="text-sm text-[#ededed] leading-snug">{bid.title}</span>
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap">
                    <span className="text-[11px] text-[#8c8c8c]">
                      {bid.agency.length > 12 ? bid.agency.slice(0, 12) + "…" : bid.agency}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-right whitespace-nowrap">
                    <span className="text-xs text-[#8c8c8c]">{formatBudget(bid.budget)}</span>
                  </td>
                  <td className="px-3 py-3 text-center whitespace-nowrap">
                    {bid.d_day !== null ? (
                      <DdayBadge days={bid.d_day} />
                    ) : (
                      <span className="text-xs text-[#3c3c3c]">-</span>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex flex-wrap gap-1">
                      {bid.role_keywords.map((kw) => (
                        <span key={kw} className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-900/50">
                          {kw}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex flex-wrap gap-1">
                      {bid.domain_keywords.slice(0, 3).map((kw) => (
                        <span key={kw} className="text-[10px] px-1.5 py-0.5 rounded bg-blue-950/40 text-blue-400 border border-blue-900/50">
                          {kw}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap">
                    <span className="text-[10px] text-[#5c5c5c]">
                      {bid.classification.length > 14 ? bid.classification.slice(0, 14) + "…" : bid.classification}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StageBadge({ stage }: { stage: string }) {
  const style: Record<string, string> = {
    "입찰공고": "text-[#8c8c8c] bg-[#1c1c1c] border-[#262626]",
    "사전규격": "text-blue-400 bg-blue-950/60 border-blue-900",
    "발주계획": "text-purple-400 bg-purple-950/60 border-purple-900",
  };
  const label: Record<string, string> = {
    "입찰공고": "공고",
    "사전규격": "사전",
    "발주계획": "계획",
  };
  return (
    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${style[stage] || style["입찰공고"]}`}>
      {label[stage] || stage}
    </span>
  );
}

function classifyAttachment(name: string): "공고문" | "제안요청서" | "과업지시서" | null {
  const lower = name.toLowerCase();
  if (lower.includes("제안요청") || lower.includes("rfp")) return "제안요청서";
  if (lower.includes("과업지시") || lower.includes("과업내용") || lower.includes("사양서")) return "과업지시서";
  if (lower.includes("공고") || lower.includes("입찰")) return "공고문";
  return null;
}

function AttachmentLink({ attachments, type }: { attachments: BidAttachment[]; type: "공고문" | "제안요청서" | "과업지시서" }) {
  const match = attachments.find((a) => classifyAttachment(a.name) === type);
  if (!match) return <span className="text-[#3c3c3c]">-</span>;
  const ext = match.name.split(".").pop()?.toUpperCase() ?? "";
  return (
    <a
      href={match.url}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => e.stopPropagation()}
      className="inline-flex items-center gap-1 text-[#3ecf8e] hover:underline"
      title={match.name}
    >
      <span>{ext}</span>
      <span>↓</span>
    </a>
  );
}

function formatDeadline(dateStr: string | null): { text: string; dday: string; color: string } {
  if (!dateStr) return { text: "-", dday: "", color: "text-[#8c8c8c]" };
  const d = new Date(dateStr);
  const text = d.toLocaleDateString("ko-KR", { month: "numeric", day: "numeric" });
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const diff = Math.ceil((d.getTime() - now.getTime()) / 86400000);
  const dday = diff <= 0 ? "마감" : `D-${diff}`;
  const color = diff <= 7 ? "text-red-400" : diff <= 14 ? "text-orange-400" : "text-[#8c8c8c]";
  return { text, dday, color };
}

function BidRow({
  bid,
  scope,
  onBookmark,
  onStatusChange,
  onClick,
}: {
  bid: MonitoredBid;
  scope: Scope;
  onBookmark: (bidNo: string) => void;
  onStatusChange: (bidNo: string, status: "검토중" | "제안착수" | "관련없음") => void;
  onClick: () => void;
}) {
  const deadline = formatDeadline(bid.deadline_date);
  const atts = bid.attachments || [];

  const relevanceColor: Record<string, string> = {
    "적극 추천": "text-[#3ecf8e] bg-emerald-950/60 border-emerald-900",
    "보통": "text-yellow-400 bg-yellow-950/60 border-yellow-900",
    "낮음": "text-[#5c5c5c] bg-[#1c1c1c] border-[#262626]",
  };
  const rel = bid.relevance || "낮음";
  const teams = bid.related_teams || [];

  return (
    <tr
      onClick={onClick}
      className="border-b border-[#1a1a1a] last:border-0 hover:bg-[#161616] transition-colors cursor-pointer"
    >
      {/* 별표 */}
      <td className="px-2 py-3 text-center">
        <button
          onClick={(e) => { e.stopPropagation(); onBookmark(bid.bid_no); }}
          className={`text-base transition-colors ${bid.is_bookmarked ? "text-yellow-400" : "text-[#3c3c3c] hover:text-yellow-400"}`}
        >
          {bid.is_bookmarked ? "★" : "☆"}
        </button>
      </td>

      {/* 공고 단계 */}
      <td className="px-2 py-3 text-center">
        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
          bid.bid_stage === "사전공고"
            ? "text-blue-400 bg-blue-950/60 border border-blue-900"
            : "text-[#8c8c8c] bg-[#1c1c1c] border border-[#262626]"
        }`}>
          {bid.bid_stage === "사전공고" ? "사전" : "본공고"}
        </span>
      </td>

      {/* 공고명 (전체 표시) */}
      <td className="px-3 py-3">
        <span className="text-sm text-[#ededed] leading-snug">{bid.bid_title}</span>
      </td>

      {/* 발주처 (축약) */}
      <td className="px-3 py-3 whitespace-nowrap">
        <span className="text-[11px] text-[#8c8c8c]">{bid.agency.length > 8 ? bid.agency.slice(0, 8) + "…" : bid.agency}</span>
      </td>

      {/* 용역비 */}
      <td className="px-3 py-3 text-right whitespace-nowrap">
        <span className="text-xs text-[#8c8c8c]">{formatBudget(bid.budget_amount)}</span>
      </td>

      {/* 마감일 */}
      <td className="px-3 py-3 text-center whitespace-nowrap">
        <div className="flex flex-col items-center">
          <span className="text-xs text-[#8c8c8c]">{deadline.text}</span>
          <span className={`text-[10px] font-bold ${deadline.color}`}>{deadline.dday}</span>
        </div>
      </td>

      {/* 관련 팀 */}
      <td className="px-3 py-3 text-center">
        {teams.length > 0 ? (
          <div className="flex flex-col items-center gap-0.5">
            {teams.map((t, i) => (
              <span key={i} className="text-[10px] text-[#8c8c8c] bg-[#1c1c1c] border border-[#262626] rounded px-1.5 py-0.5 whitespace-nowrap">
                {t}
              </span>
            ))}
          </div>
        ) : (
          <span className="text-xs text-[#3c3c3c]">-</span>
        )}
      </td>

      {/* 관련성 */}
      <td className="px-3 py-3 text-center">
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${relevanceColor[rel]}`}>
          {rel}
        </span>
      </td>

      {/* 공고문 */}
      <td className="px-3 py-3 text-center text-xs">
        <AttachmentLink attachments={atts} type="공고문" />
      </td>

      {/* 제안요청서 */}
      <td className="px-3 py-3 text-center text-xs">
        <AttachmentLink attachments={atts} type="제안요청서" />
      </td>

      {/* 과업지시서 */}
      <td className="px-3 py-3 text-center text-xs">
        <AttachmentLink attachments={atts} type="과업지시서" />
      </td>

      {/* 검토결과 + 의사결정자 */}
      <td className="px-3 py-3 text-center">
        {bid.proposal_status ? (
          <div className="flex flex-col items-center gap-0.5">
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border whitespace-nowrap ${
              bid.proposal_status === "제안결정" || bid.proposal_status === "제안착수"
                ? "text-[#3ecf8e] bg-emerald-950/60 border-emerald-900"
                : bid.proposal_status === "제안포기"
                ? "text-red-400 bg-red-950/60 border-red-900"
                : bid.proposal_status === "제안유보"
                ? "text-orange-400 bg-orange-950/60 border-orange-900"
                : bid.proposal_status === "관련없음"
                ? "text-[#5c5c5c] bg-[#1c1c1c] border-[#262626]"
                : bid.proposal_status === "검토중"
                ? "text-yellow-400 bg-yellow-950/60 border-yellow-900"
                : "text-[#8c8c8c] bg-[#1c1c1c] border-[#262626]"
            }`}>
              {bid.proposal_status === "제안결정" && teams.length > 0
                ? `${teams[0]} 제안착수`
                : bid.proposal_status}
            </span>
            {bid.decided_by && (
              <span className="text-[11px] text-[#5c5c5c]">{bid.decided_by}</span>
            )}
          </div>
        ) : (
          <span className="text-[10px] text-[#3c3c3c]">-</span>
        )}
      </td>

    </tr>
  );
}

function EmptyState({ scope }: { scope: Scope }) {
  const messages: Record<Scope, { title: string; desc: string; icon: string }> = {
    my: {
      title: "관심 공고가 없습니다",
      desc: "전체 탭에서 관심 있는 공고를 북마크하거나, 프로필의 관심분야를 설정하세요.",
      icon: "★",
    },
    team: {
      title: "팀 추천 공고가 없습니다",
      desc: "팀 프로필과 검색 조건을 설정하면 AI가 맞춤 공고를 추천합니다.",
      icon: "👥",
    },
    division: {
      title: "본부 추천 공고가 없습니다",
      desc: "본부 내 팀들의 추천 공고가 수집되면 여기에 표시됩니다.",
      icon: "🏢",
    },
    company: {
      title: "모니터링된 공고가 없습니다",
      desc: "공고 수집이 아직 실행되지 않았습니다. 팀 설정 후 공고를 수집해주세요.",
      icon: "📡",
    },
  };

  const m = messages[scope];

  return (
    <div className="flex flex-col items-center justify-center h-64 text-center">
      <div className="w-12 h-12 rounded-xl bg-[#1c1c1c] border border-[#262626] flex items-center justify-center text-2xl mb-4">
        {m.icon}
      </div>
      <h3 className="text-sm font-semibold text-[#ededed] mb-1">{m.title}</h3>
      <p className="text-xs text-[#8c8c8c] mb-6 max-w-xs">{m.desc}</p>
      {scope === "team" && (
        <Link
          href="/bids/settings"
          className="bg-[#3ecf8e] hover:bg-[#49e59e] text-black font-semibold rounded-lg px-5 py-2 text-sm transition-colors"
        >
          설정하기
        </Link>
      )}
    </div>
  );
}
