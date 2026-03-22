"use client";

/**
 * F-05: 공고 모니터링 페이지
 * - 뷰: AI 추천 (Scored) / 모니터링 (Monitor)
 * - 통합 필터 바: 텍스트검색, 예산, 발주처, 단계, 퀵프리셋, 컬럼 정렬
 * - URL 파라미터로 필터 상태 저장
 */

import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, MonitoredBid, ScoredBid, BidAttachment } from "@/lib/api";

// ── 타입 ──────────────────────────────────────────────────

type ViewMode = "scored" | "monitor";
type Scope = "my" | "team" | "division" | "company";
type SortConfig = { key: string; dir: "asc" | "desc" } | null;

const SCOPE_LABELS: Record<Scope, { label: string; desc: string }> = {
  my: { label: "개인", desc: "내 관심 분야 + 북마크 공고" },
  team: { label: "팀", desc: "우리 팀 추천 공고" },
  division: { label: "본부", desc: "우리 본부 추천 공고" },
  company: { label: "전체", desc: "TENOPA 전체 진행중 공고" },
};

const BUDGET_OPTIONS = [
  { label: "전체", value: 0 },
  { label: "5천만+", value: 50_000_000 },
  { label: "1억+", value: 100_000_000 },
  { label: "3억+", value: 300_000_000 },
  { label: "5억+", value: 500_000_000 },
  { label: "10억+", value: 1_000_000_000 },
];

// ── 유틸 ──────────────────────────────────────────────────

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

function StageBadge({ stage }: { stage: string }) {
  const style: Record<string, string> = {
    "입찰공고": "text-[#8c8c8c] bg-[#1c1c1c] border-[#262626]",
    "사전규격": "text-blue-400 bg-blue-950/60 border-blue-900",
    "발주계획": "text-purple-400 bg-purple-950/60 border-purple-900",
  };
  const label: Record<string, string> = { "입찰공고": "공고", "사전규격": "사전", "발주계획": "계획" };
  return (
    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${style[stage] || style["입찰공고"]}`}>
      {label[stage] || stage}
    </span>
  );
}

function scoreColor(score: number): string {
  if (score >= 120) return "text-purple-400 bg-purple-950/60 border-purple-900";
  if (score >= 100) return "text-emerald-400 bg-emerald-950/60 border-emerald-900";
  if (score >= 80) return "text-blue-400 bg-blue-950/60 border-blue-900";
  if (score >= 50) return "text-yellow-400 bg-yellow-950/60 border-yellow-900";
  return "text-[#8c8c8c] bg-[#1c1c1c] border-[#262626]";
}

// ── 캐시 (모듈 레벨, 컴포넌트 리마운트에도 유지) ──────────

interface CacheEntry<T> {
  data: T;
  fetchedAt: number;   // Date.now()
  cacheKey: string;
}

const CACHE_TTL = 5 * 60 * 1000; // 5분

const scoredCache: { current: CacheEntry<{ bids: ScoredBid[]; totalFetched: number; dateFrom: string; dateTo: string; sources: Record<string, number> }> | null } = { current: null };
const monitorCache: { current: CacheEntry<{ bids: MonitoredBid[]; total: number }> | null } = { current: null };

function formatFetchedAt(ts: number | null): string {
  if (!ts) return "";
  const d = new Date(ts);
  const hh = d.getHours().toString().padStart(2, "0");
  const mm = d.getMinutes().toString().padStart(2, "0");
  return `${hh}:${mm}`;
}

// ── 필터 유틸 ─────────────────────────────────────────────

function matchesScoredSearch(bid: ScoredBid, query: string): boolean {
  if (!query) return true;
  const tokens = query.toLowerCase().split(/\s+/).filter(Boolean);
  const haystack = [bid.title, bid.agency, bid.classification, ...bid.role_keywords, ...bid.domain_keywords]
    .join(" ")
    .toLowerCase();
  return tokens.every((t) => haystack.includes(t));
}

function matchesMonitorSearch(bid: MonitoredBid, query: string): boolean {
  if (!query) return true;
  const tokens = query.toLowerCase().split(/\s+/).filter(Boolean);
  const haystack = [bid.bid_title, bid.agency, bid.recommendation_summary || "", ...(bid.related_teams || [])]
    .join(" ")
    .toLowerCase();
  return tokens.every((t) => haystack.includes(t));
}

function sortBids<T>(items: T[], config: SortConfig, getter: (item: T, key: string) => number | null): T[] {
  if (!config) return items;
  const { key, dir } = config;
  return [...items].sort((a, b) => {
    const va = getter(a, key) ?? (dir === "asc" ? Infinity : -Infinity);
    const vb = getter(b, key) ?? (dir === "asc" ? Infinity : -Infinity);
    return dir === "asc" ? va - vb : vb - va;
  });
}

// ── 정렬 헤더 컴포넌트 ────────────────────────────────────

function SortableHeader({
  label,
  sortKey,
  current,
  onSort,
  className = "",
}: {
  label: string;
  sortKey: string;
  current: SortConfig;
  onSort: (key: string) => void;
  className?: string;
}) {
  const isActive = current?.key === sortKey;
  const arrow = isActive ? (current.dir === "desc" ? "▼" : "▲") : "⇅";
  const arrowColor = isActive ? "text-[#3ecf8e]" : "text-[#3c3c3c]";
  return (
    <th
      onClick={() => onSort(sortKey)}
      className={`px-3 py-2.5 text-xs font-medium text-[#5c5c5c] cursor-pointer hover:text-[#8c8c8c] select-none whitespace-nowrap ${className}`}
    >
      {label} <span className={`${arrowColor} ml-0.5`}>{arrow}</span>
    </th>
  );
}

// ── 발주처 타이프어헤드 ───────────────────────────────────

function AgencyTypeahead({
  agencies,
  value,
  onChange,
}: {
  agencies: string[];
  value: string;
  onChange: (v: string) => void;
}) {
  const [input, setInput] = useState(value);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => setInput(value), [value]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const filtered = input
    ? agencies.filter((a) => a.toLowerCase().includes(input.toLowerCase())).slice(0, 8)
    : agencies.slice(0, 8);

  return (
    <div ref={ref} className="relative">
      <div className="flex items-center gap-1">
        <input
          type="text"
          value={input}
          placeholder="발주처"
          onChange={(e) => {
            setInput(e.target.value);
            setOpen(true);
            if (!e.target.value) onChange("");
          }}
          onFocus={() => setOpen(true)}
          className="w-[140px] bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-xs text-[#ededed] placeholder:text-[#5c5c5c]"
        />
        {value && (
          <button onClick={() => { onChange(""); setInput(""); }} className="text-[#5c5c5c] hover:text-[#ededed] text-xs">
            ✕
          </button>
        )}
      </div>
      {open && filtered.length > 0 && (
        <div className="absolute top-full left-0 mt-1 w-[220px] bg-[#1c1c1c] border border-[#262626] rounded-lg shadow-lg z-20 max-h-48 overflow-y-auto">
          {filtered.map((a) => (
            <button
              key={a}
              onClick={() => { onChange(a); setInput(a); setOpen(false); }}
              className="block w-full text-left px-3 py-1.5 text-xs text-[#ededed] hover:bg-[#262626] truncate"
            >
              {a}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── 퀵프리셋 버튼 ─────────────────────────────────────────

function PresetButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-2.5 py-1 rounded-md text-[10px] font-medium border transition-colors ${
        active
          ? "bg-[#3ecf8e]/10 border-[#3ecf8e]/30 text-[#3ecf8e]"
          : "bg-[#1c1c1c] border-[#262626] text-[#5c5c5c] hover:text-[#8c8c8c]"
      }`}
    >
      {label}
    </button>
  );
}

// ══════════════════════════════════════════════════════════
// 메인 페이지
// ══════════════════════════════════════════════════════════

export default function BidsMonitorPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // ── URL → 초기값 ──
  const initView = (searchParams.get("view") as ViewMode) || "scored";
  const initScope = (searchParams.get("scope") as Scope) || "company";

  const [viewMode, setViewMode] = useState<ViewMode>(initView);
  const [scope, setScope] = useState<Scope>(initScope);

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
      {/* 헤더 */}
      <div className="border-b border-[#262626] px-6 py-4 shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-sm font-semibold text-[#ededed]">공고 모니터링</h1>
            <p className="text-xs text-[#8c8c8c] mt-0.5">
              {viewMode === "scored" ? "AI 적합도 스코어링 기반 추천" : SCOPE_LABELS[scope].desc}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* 뷰 모드 토글 */}
            <div className="flex items-center gap-1 bg-[#1c1c1c] rounded-lg p-1 border border-[#262626]">
              {(["scored", "monitor"] as ViewMode[]).map((v) => (
                <button
                  key={v}
                  onClick={() => setViewMode(v)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    viewMode === v ? "bg-[#3ecf8e] text-[#0f0f0f]" : "text-[#8c8c8c] hover:text-[#ededed]"
                  }`}
                >
                  {v === "scored" ? "AI 추천" : "모니터링"}
                </button>
              ))}
            </div>
            {/* 스코프 탭 */}
            {viewMode === "monitor" && (
              <div className="flex items-center gap-1 bg-[#1c1c1c] rounded-lg p-1 border border-[#262626]">
                {(["my", "team", "division", "company"] as Scope[]).map((s) => (
                  <button
                    key={s}
                    onClick={() => setScope(s)}
                    className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      scope === s ? "bg-[#3ecf8e] text-[#0f0f0f]" : "text-[#8c8c8c] hover:text-[#ededed]"
                    }`}
                  >
                    {SCOPE_LABELS[s].label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 콘텐츠 */}
      <div className="flex-1 overflow-auto px-6 py-4">
        {viewMode === "scored" ? <ScoredBidsView /> : <MonitorBidsView scope={scope} />}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// AI 추천 (Scored) 뷰
// ══════════════════════════════════════════════════════════

function ScoredBidsView() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // ── 데이터 ──
  const [bids, setBids] = useState<ScoredBid[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [totalFetched, setTotalFetched] = useState(0);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sources, setSources] = useState<Record<string, number>>({});
  const [fetchedAt, setFetchedAt] = useState<number | null>(null);

  // ── 서버 필터 (API 파라미터) ──
  const [days, setDays] = useState(Number(searchParams.get("days")) || 7);
  const [minScoreServer, setMinScoreServer] = useState(Number(searchParams.get("score")) || 20);

  // ── 클라이언트 필터 ──
  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [debouncedQuery, setDebouncedQuery] = useState(query);
  const [minBudget, setMinBudget] = useState(Number(searchParams.get("budget")) || 0);
  const [agency, setAgency] = useState(searchParams.get("agency") || "");
  const [stageFilter, setStageFilter] = useState<Set<string>>(new Set(["입찰공고", "사전규격", "발주계획"]));
  const [sortConfig, setSortConfig] = useState<SortConfig>(null);
  const [activePreset, setActivePreset] = useState<string | null>(null);

  // 디바운스
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query), 200);
    return () => clearTimeout(t);
  }, [query]);

  // 응답을 state에 반영하는 헬퍼
  function applyResponse(data: ScoredBid[], total: number, from: string, to: string, src: Record<string, number>, ts: number) {
    setBids(data);
    setTotalFetched(total);
    setDateFrom(from);
    setDateTo(to);
    setSources(src);
    setFetchedAt(ts);
  }

  // 데이터 로드 (캐시 활용, forceRefresh로 강제 갱신)
  const load = useCallback(async (forceRefresh = false) => {
    const cacheKey = `scored_${days}_${minScoreServer}`;

    // 캐시 히트: 같은 파라미터 + 5분 이내
    if (!forceRefresh && scoredCache.current && scoredCache.current.cacheKey === cacheKey && Date.now() - scoredCache.current.fetchedAt < CACHE_TTL) {
      const c = scoredCache.current.data;
      applyResponse(c.bids, c.totalFetched, c.dateFrom, c.dateTo, c.sources, scoredCache.current.fetchedAt);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");
    try {
      const res = await api.bids.scored({ days, minScore: minScoreServer, maxResults: 200 });
      const now = Date.now();
      const d = res.data || [];
      applyResponse(d, res.total_fetched || 0, res.date_from || "", res.date_to || "", res.sources || {}, now);
      scoredCache.current = { data: { bids: d, totalFetched: res.total_fetched || 0, dateFrom: res.date_from || "", dateTo: res.date_to || "", sources: res.sources || {} }, fetchedAt: now, cacheKey };
    } catch {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
        const directRes = await fetch(`${baseUrl}/bids/scored?days=${days}&min_score=${minScoreServer}&max_results=200`);
        if (directRes.ok) {
          const json = await directRes.json();
          const now = Date.now();
          const d = json.data || [];
          applyResponse(d, json.total_fetched || 0, json.date_from || "", json.date_to || "", json.sources || {}, now);
          scoredCache.current = { data: { bids: d, totalFetched: json.total_fetched || 0, dateFrom: json.date_from || "", dateTo: json.date_to || "", sources: json.sources || {} }, fetchedAt: now, cacheKey };
          return;
        }
      } catch {
        setError("백엔드에 연결할 수 없습니다.");
      }
      setBids([]);
    } finally {
      setLoading(false);
    }
  }, [days, minScoreServer]);

  useEffect(() => { load(); }, [load]);

  // 발주처 목록 추출
  const agencies = useMemo(() => [...new Set(bids.map((b) => b.agency))].sort(), [bids]);

  // 클라이언트 필터 + 정렬
  const filteredBids = useMemo(() => {
    let result = bids
      .filter((b) => stageFilter.has(b.bid_stage || "입찰공고"))
      .filter((b) => matchesScoredSearch(b, debouncedQuery))
      .filter((b) => minBudget === 0 || (b.budget ?? 0) >= minBudget)
      .filter((b) => !agency || b.agency.includes(agency));

    return sortBids(result, sortConfig, (b, key) => {
      if (key === "score") return b.score;
      if (key === "budget") return b.budget;
      if (key === "d_day") return b.d_day;
      return null;
    });
  }, [bids, stageFilter, debouncedQuery, minBudget, agency, sortConfig]);

  // 정렬 토글
  function handleSort(key: string) {
    setSortConfig((prev) => {
      if (!prev || prev.key !== key) return { key, dir: "desc" };
      if (prev.dir === "desc") return { key, dir: "asc" };
      return null;
    });
  }

  // 단계 토글
  function toggleStage(stage: string) {
    setStageFilter((prev) => {
      const next = new Set(prev);
      if (next.has(stage)) { if (next.size > 1) next.delete(stage); }
      else next.add(stage);
      return next;
    });
  }

  // 퀵 프리셋
  function applyPreset(name: string) {
    if (activePreset === name) {
      setActivePreset(null);
      resetFilters();
      return;
    }
    setActivePreset(name);
    if (name === "big-high") { setMinBudget(100_000_000); setMinScoreServer(80); }
    else if (name === "strategy") { setQuery("전략 기획"); }
    else if (name === "urgent") { setSortConfig({ key: "d_day", dir: "asc" }); }
  }

  // 활성 필터 수
  const activeFilterCount = [
    debouncedQuery !== "",
    minBudget > 0,
    agency !== "",
    stageFilter.size < 3,
    sortConfig !== null,
  ].filter(Boolean).length;

  // 초기화
  function resetFilters() {
    setQuery("");
    setMinBudget(0);
    setAgency("");
    setStageFilter(new Set(["입찰공고", "사전규격", "발주계획"]));
    setSortConfig(null);
    setActivePreset(null);
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
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        {/* 퀵 프리셋 */}
        <PresetButton label="1억+ 고점수" active={activePreset === "big-high"} onClick={() => applyPreset("big-high")} />
        <PresetButton label="전략/기획" active={activePreset === "strategy"} onClick={() => applyPreset("strategy")} />
        <PresetButton label="D-7 임박" active={activePreset === "urgent"} onClick={() => applyPreset("urgent")} />
        <div className="w-px h-5 bg-[#262626]" />

        {/* 검색 */}
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="공고명, 발주처, 키워드 검색"
          className="w-[220px] bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-xs text-[#ededed] placeholder:text-[#5c5c5c]"
        />

        {/* 예산 */}
        <select value={minBudget} onChange={(e) => setMinBudget(Number(e.target.value))} className="bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-xs text-[#ededed]">
          {BUDGET_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        {/* 발주처 */}
        <AgencyTypeahead agencies={agencies} value={agency} onChange={setAgency} />

        {/* 기간 */}
        <label className="flex items-center gap-1 text-xs text-[#8c8c8c]">
          기간
          <select value={days} onChange={(e) => setDays(Number(e.target.value))} className="bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-xs text-[#ededed]">
            {[1, 3, 5, 7, 10, 14, 30].map((d) => (
              <option key={d} value={d}>{d === 1 ? "당일" : `${d}일`}</option>
            ))}
          </select>
        </label>

        {/* 최소 점수 */}
        <label className="flex items-center gap-1 text-xs text-[#8c8c8c]">
          점수
          <select value={minScoreServer} onChange={(e) => setMinScoreServer(Number(e.target.value))} className="bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-xs text-[#ededed]">
            {[0, 20, 50, 80, 100].map((s) => (
              <option key={s} value={s}>{s === 0 ? "전체" : `${s}+`}</option>
            ))}
          </select>
        </label>

        {/* 단계 */}
        <div className="flex items-center gap-2 text-[10px] text-[#5c5c5c]">
          {(["입찰공고", "사전규격", "발주계획"] as const).map((stage) => (
            <label key={stage} className="flex items-center gap-1 cursor-pointer">
              <input type="checkbox" checked={stageFilter.has(stage)} onChange={() => toggleStage(stage)} className="w-3 h-3 rounded border-[#262626] bg-[#1c1c1c] accent-[#3ecf8e]" />
              <span>{stage === "입찰공고" ? "공고" : stage === "사전규격" ? "사전" : "계획"}</span>
            </label>
          ))}
        </div>

        {/* 필터 카운트 + 초기화 + 크롤링 시각 + 새로고침 */}
        <span className="text-[10px] text-[#5c5c5c] ml-auto flex items-center gap-2">
          {activeFilterCount > 0 && (
            <>
              <span>{activeFilterCount}개 필터</span>
              <button onClick={resetFilters} className="text-[#3ecf8e] hover:underline">초기화</button>
              <span>·</span>
            </>
          )}
          {loading
            ? "수집 중..."
            : `${filteredBids.length}건` + (totalFetched > 0 ? ` / 전수 ${totalFetched.toLocaleString()}건` : "")}
          {fetchedAt && !loading && (
            <>
              <span>·</span>
              <span>수집 {formatFetchedAt(fetchedAt)}</span>
            </>
          )}
          <button
            onClick={() => load(true)}
            disabled={loading}
            title="G2B 공고 새로 수집"
            className="ml-1 px-2 py-0.5 rounded border border-[#262626] text-[10px] text-[#8c8c8c] hover:text-[#3ecf8e] hover:border-[#3ecf8e]/30 disabled:opacity-40 transition-colors"
          >
            {loading ? "수집 중..." : "새로고침"}
          </button>
        </span>
      </div>

      {/* 테이블 */}
      {loading ? (
        <div className="flex items-center justify-center h-40">
          <p className="text-sm text-[#5c5c5c]">G2B 전수 수집 + 스코어링 중...</p>
        </div>
      ) : filteredBids.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-40 text-center">
          <p className="text-sm text-[#8c8c8c]">조건에 맞는 공고가 없습니다</p>
          <p className="text-xs text-[#5c5c5c] mt-1">기간을 늘리거나 필터를 조정해보세요</p>
        </div>
      ) : (
        <div className="rounded-lg border border-[#262626] bg-[#111111] overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#262626] bg-[#0f0f0f]">
                <th className="text-center px-2 py-2.5 text-xs font-medium text-[#5c5c5c] w-10">#</th>
                <th className="text-center px-2 py-2.5 text-xs font-medium text-[#5c5c5c] w-14">단계</th>
                <SortableHeader label="적합도" sortKey="score" current={sortConfig} onSort={handleSort} className="text-center w-16" />
                <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c]">공고명</th>
                <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">발주기관</th>
                <SortableHeader label="예산" sortKey="budget" current={sortConfig} onSort={handleSort} className="text-right" />
                <SortableHeader label="마감" sortKey="d_day" current={sortConfig} onSort={handleSort} className="text-center" />
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
                  <td className="px-2 py-3 text-center"><StageBadge stage={bid.bid_stage || "입찰공고"} /></td>
                  <td className="px-2 py-3 text-center">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-md border ${scoreColor(bid.score)}`}>{bid.score.toFixed(0)}</span>
                  </td>
                  <td className="px-3 py-3"><span className="text-sm text-[#ededed] leading-snug">{bid.title}</span></td>
                  <td className="px-3 py-3 whitespace-nowrap">
                    <span className="text-[11px] text-[#8c8c8c]">{bid.agency.length > 12 ? bid.agency.slice(0, 12) + "…" : bid.agency}</span>
                  </td>
                  <td className="px-3 py-3 text-right whitespace-nowrap"><span className="text-xs text-[#8c8c8c]">{formatBudget(bid.budget)}</span></td>
                  <td className="px-3 py-3 text-center whitespace-nowrap">{bid.d_day !== null ? <DdayBadge days={bid.d_day} /> : <span className="text-xs text-[#3c3c3c]">-</span>}</td>
                  <td className="px-3 py-3">
                    <div className="flex flex-wrap gap-1">
                      {bid.role_keywords.map((kw) => (
                        <span key={kw} className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-900/50">{kw}</span>
                      ))}
                    </div>
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex flex-wrap gap-1">
                      {bid.domain_keywords.slice(0, 3).map((kw) => (
                        <span key={kw} className="text-[10px] px-1.5 py-0.5 rounded bg-blue-950/40 text-blue-400 border border-blue-900/50">{kw}</span>
                      ))}
                    </div>
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap"><span className="text-[10px] text-[#5c5c5c]">{bid.classification.length > 14 ? bid.classification.slice(0, 14) + "…" : bid.classification}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// 모니터링 뷰
// ══════════════════════════════════════════════════════════

function MonitorBidsView({ scope }: { scope: Scope }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [bids, setBids] = useState<MonitoredBid[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [fetchedAt, setFetchedAt] = useState<number | null>(null);

  // ── 클라이언트 필터 ──
  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [debouncedQuery, setDebouncedQuery] = useState(query);
  const [minBudget, setMinBudget] = useState(Number(searchParams.get("budget")) || 0);
  const [agency, setAgency] = useState(searchParams.get("agency") || "");
  const [statusFilter, setStatusFilter] = useState("");
  const [relevanceFilter, setRelevanceFilter] = useState("");
  const [sortConfig, setSortConfig] = useState<SortConfig>(null);
  const [activePreset, setActivePreset] = useState<string | null>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query), 200);
    return () => clearTimeout(t);
  }, [query]);

  const loadBids = useCallback(async (s: Scope, p: number, forceRefresh = false) => {
    const cacheKey = `monitor_${s}_${p}`;

    if (!forceRefresh && monitorCache.current && monitorCache.current.cacheKey === cacheKey && Date.now() - monitorCache.current.fetchedAt < CACHE_TTL) {
      const c = monitorCache.current.data;
      setBids(c.bids);
      setTotal(c.total);
      setFetchedAt(monitorCache.current.fetchedAt);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");
    try {
      const res = await api.bids.monitor(s, p, true);
      const now = Date.now();
      setBids(res.data || []);
      setTotal(res.meta?.total || 0);
      setFetchedAt(now);
      monitorCache.current = { data: { bids: res.data || [], total: res.meta?.total || 0 }, fetchedAt: now, cacheKey };
    } catch {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
        const directRes = await fetch(`${baseUrl}/bids/monitor?scope=${s}&page=${p}&show_all=true`);
        if (directRes.ok) {
          const json = await directRes.json();
          const now = Date.now();
          setBids(json.data || []);
          setTotal(json.meta?.total || 0);
          setFetchedAt(now);
          monitorCache.current = { data: { bids: json.data || [], total: json.meta?.total || 0 }, fetchedAt: now, cacheKey };
          return;
        }
      } catch {
        setError("백엔드에 연결할 수 없습니다.");
      }
      setBids([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { setPage(1); loadBids(scope, 1); }, [scope, loadBids]);
  useEffect(() => { if (page > 1) loadBids(scope, page); }, [page, scope, loadBids]);

  const agencies = useMemo(() => [...new Set(bids.map((b) => b.agency))].sort(), [bids]);

  const RELEVANCE_MAP: Record<string, number> = { "적극 추천": 3, "보통": 2, "낮음": 1 };

  const filteredBids = useMemo(() => {
    let result = bids
      .filter((b) => matchesMonitorSearch(b, debouncedQuery))
      .filter((b) => minBudget === 0 || (b.budget_amount ?? 0) >= minBudget)
      .filter((b) => !agency || b.agency.includes(agency))
      .filter((b) => {
        if (!statusFilter) return true;
        if (statusFilter === "미검토") return !b.proposal_status;
        return b.proposal_status === statusFilter;
      })
      .filter((b) => !relevanceFilter || b.relevance === relevanceFilter);

    return sortBids(result, sortConfig, (b, key) => {
      if (key === "budget") return b.budget_amount;
      if (key === "days") return b.days_remaining;
      if (key === "relevance") return RELEVANCE_MAP[b.relevance || "낮음"] || 0;
      return null;
    });
  }, [bids, debouncedQuery, minBudget, agency, statusFilter, relevanceFilter, sortConfig]);

  function handleSort(key: string) {
    setSortConfig((prev) => {
      if (!prev || prev.key !== key) return { key, dir: "desc" };
      if (prev.dir === "desc") return { key, dir: "asc" };
      return null;
    });
  }

  function applyPreset(name: string) {
    if (activePreset === name) { setActivePreset(null); resetFilters(); return; }
    setActivePreset(name);
    if (name === "unreviewed") setStatusFilter("미검토");
    else if (name === "recommended") setRelevanceFilter("적극 추천");
    else if (name === "big") setMinBudget(100_000_000);
  }

  const activeFilterCount = [
    debouncedQuery !== "",
    minBudget > 0,
    agency !== "",
    statusFilter !== "",
    relevanceFilter !== "",
    sortConfig !== null,
  ].filter(Boolean).length;

  function resetFilters() {
    setQuery("");
    setMinBudget(0);
    setAgency("");
    setStatusFilter("");
    setRelevanceFilter("");
    setSortConfig(null);
    setActivePreset(null);
  }

  async function handleStatusChange(bidNo: string, status: "검토중" | "제안착수" | "관련없음") {
    try {
      await api.bids.updateStatus(bidNo, status);
      setBids((prev) => prev.map((b) => b.bid_no === bidNo ? { ...b, proposal_status: status } : b));
    } catch { /* 인증 실패 허용 */ }
  }

  async function handleBookmark(bidNo: string) {
    try {
      const res = await api.bids.toggleBookmark(bidNo);
      setBids((prev) => prev.map((b) => b.bid_no === bidNo ? { ...b, is_bookmarked: res.bookmarked } : b));
    } catch { /* 무시 */ }
  }

  if (error) {
    return <div className="mx-2 mt-3 px-4 py-2 bg-red-950/40 border border-red-900/50 rounded-lg text-xs text-red-400">{error}</div>;
  }

  return (
    <div>
      {/* 필터 바 */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <PresetButton label="검토대기만" active={activePreset === "unreviewed"} onClick={() => applyPreset("unreviewed")} />
        <PresetButton label="적극 추천" active={activePreset === "recommended"} onClick={() => applyPreset("recommended")} />
        <PresetButton label="대형 1억+" active={activePreset === "big"} onClick={() => applyPreset("big")} />
        <div className="w-px h-5 bg-[#262626]" />

        <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="공고명, 발주처, 키워드 검색" className="w-[220px] bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-xs text-[#ededed] placeholder:text-[#5c5c5c]" />

        <select value={minBudget} onChange={(e) => setMinBudget(Number(e.target.value))} className="bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-xs text-[#ededed]">
          {BUDGET_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>

        <AgencyTypeahead agencies={agencies} value={agency} onChange={setAgency} />

        {/* 관련성 */}
        <div className="flex items-center gap-1 bg-[#1c1c1c] rounded-lg p-0.5 border border-[#262626]">
          {["", "적극 추천", "보통"].map((r) => (
            <button
              key={r}
              onClick={() => setRelevanceFilter(r)}
              className={`px-2 py-1 rounded-md text-[10px] font-medium transition-colors ${
                relevanceFilter === r ? "bg-[#3ecf8e] text-[#0f0f0f]" : "text-[#5c5c5c] hover:text-[#8c8c8c]"
              }`}
            >
              {r || "전체"}
            </button>
          ))}
        </div>

        {/* 검토상태 */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-xs text-[#ededed]"
        >
          <option value="">검토상태 전체</option>
          <option value="미검토">검토대기</option>
          <option value="검토중">검토진행</option>
          <option value="제안결정">제안결정</option>
          <option value="제안착수">제안착수</option>
          <option value="제안유보">제안유보</option>
          <option value="제안포기">제안포기</option>
          <option value="관련없음">관련없음</option>
        </select>

        <span className="text-[10px] text-[#5c5c5c] ml-auto flex items-center gap-2">
          {activeFilterCount > 0 && (
            <>
              <span>{activeFilterCount}개 필터</span>
              <button onClick={resetFilters} className="text-[#3ecf8e] hover:underline">초기화</button>
              <span>·</span>
            </>
          )}
          {loading ? "불러오는 중..." : `${filteredBids.length}건`}
          {fetchedAt && !loading && (
            <>
              <span>·</span>
              <span>수집 {formatFetchedAt(fetchedAt)}</span>
            </>
          )}
          <button
            onClick={() => loadBids(scope, page, true)}
            disabled={loading}
            title="공고 데이터 새로 불러오기"
            className="ml-1 px-2 py-0.5 rounded border border-[#262626] text-[10px] text-[#8c8c8c] hover:text-[#3ecf8e] hover:border-[#3ecf8e]/30 disabled:opacity-40 transition-colors"
          >
            {loading ? "수집 중..." : "새로고침"}
          </button>
        </span>
      </div>

      {/* 테이블 */}
      {loading ? (
        <div className="flex items-center justify-center h-40"><p className="text-sm text-[#5c5c5c]">불러오는 중...</p></div>
      ) : filteredBids.length === 0 ? (
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
                  <SortableHeader label="용역비" sortKey="budget" current={sortConfig} onSort={handleSort} className="text-right" />
                  <SortableHeader label="마감일" sortKey="days" current={sortConfig} onSort={handleSort} className="text-center" />
                  <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">관련 팀</th>
                  <SortableHeader label="관련성" sortKey="relevance" current={sortConfig} onSort={handleSort} className="text-center" />
                  <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">공고문</th>
                  <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">제안요청서</th>
                  <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">과업지시서</th>
                  <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">검토결과</th>
                </tr>
              </thead>
              <tbody>
                {filteredBids.map((bid) => (
                  <BidRow key={bid.bid_no} bid={bid} scope={scope} onBookmark={handleBookmark} onStatusChange={handleStatusChange} onClick={() => router.push(`/bids/${bid.bid_no}/review`)} />
                ))}
              </tbody>
            </table>
          </div>
          {total > 30 && (
            <div className="flex items-center justify-center gap-2 mt-4">
              <button disabled={page === 1} onClick={() => setPage((p) => p - 1)} className="px-3 py-1.5 text-xs border border-[#262626] rounded-lg text-[#8c8c8c] disabled:opacity-40 hover:bg-[#1c1c1c] transition-colors">이전</button>
              <span className="px-3 py-1.5 text-xs text-[#8c8c8c]">{page}</span>
              <button onClick={() => setPage((p) => p + 1)} className="px-3 py-1.5 text-xs border border-[#262626] rounded-lg text-[#8c8c8c] hover:bg-[#1c1c1c] transition-colors">다음</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── 모니터링 행 ─────────────────────────────────────────

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
    <a href={match.url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} className="inline-flex items-center gap-1 text-[#3ecf8e] hover:underline" title={match.name}>
      <span>{ext}</span><span>↓</span>
    </a>
  );
}

function formatDeadline(dateStr: string | null): { text: string; dday: string; color: string } {
  if (!dateStr) return { text: "-", dday: "", color: "text-[#8c8c8c]" };
  const d = new Date(dateStr);
  const text = d.toLocaleDateString("ko-KR", { month: "numeric", day: "numeric" });
  const now = new Date(); now.setHours(0, 0, 0, 0);
  const diff = Math.ceil((d.getTime() - now.getTime()) / 86400000);
  const dday = diff <= 0 ? "마감" : `D-${diff}`;
  const color = diff <= 7 ? "text-red-400" : diff <= 14 ? "text-orange-400" : "text-[#8c8c8c]";
  return { text, dday, color };
}

function BidRow({ bid, scope, onBookmark, onStatusChange, onClick }: {
  bid: MonitoredBid; scope: Scope;
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
    <tr onClick={onClick} className="border-b border-[#1a1a1a] last:border-0 hover:bg-[#161616] transition-colors cursor-pointer">
      <td className="px-2 py-3 text-center">
        <button onClick={(e) => { e.stopPropagation(); onBookmark(bid.bid_no); }} className={`text-base transition-colors ${bid.is_bookmarked ? "text-yellow-400" : "text-[#3c3c3c] hover:text-yellow-400"}`}>
          {bid.is_bookmarked ? "★" : "☆"}
        </button>
      </td>
      <td className="px-2 py-3 text-center">
        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${bid.bid_stage === "사전공고" ? "text-blue-400 bg-blue-950/60 border border-blue-900" : "text-[#8c8c8c] bg-[#1c1c1c] border border-[#262626]"}`}>
          {bid.bid_stage === "사전공고" ? "사전" : "본공고"}
        </span>
      </td>
      <td className="px-3 py-3"><span className="text-sm text-[#ededed] leading-snug">{bid.bid_title}</span></td>
      <td className="px-3 py-3 whitespace-nowrap"><span className="text-[11px] text-[#8c8c8c]">{bid.agency.length > 8 ? bid.agency.slice(0, 8) + "…" : bid.agency}</span></td>
      <td className="px-3 py-3 text-right whitespace-nowrap"><span className="text-xs text-[#8c8c8c]">{formatBudget(bid.budget_amount)}</span></td>
      <td className="px-3 py-3 text-center whitespace-nowrap">
        <div className="flex flex-col items-center">
          <span className="text-xs text-[#8c8c8c]">{deadline.text}</span>
          <span className={`text-[10px] font-bold ${deadline.color}`}>{deadline.dday}</span>
        </div>
      </td>
      <td className="px-3 py-3 text-center">
        {teams.length > 0 ? (
          <div className="flex flex-col items-center gap-0.5">
            {teams.map((t, i) => (<span key={i} className="text-[10px] text-[#8c8c8c] bg-[#1c1c1c] border border-[#262626] rounded px-1.5 py-0.5 whitespace-nowrap">{t}</span>))}
          </div>
        ) : <span className="text-xs text-[#3c3c3c]">-</span>}
      </td>
      <td className="px-3 py-3 text-center">
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${relevanceColor[rel]}`}>{rel}</span>
      </td>
      <td className="px-3 py-3 text-center text-xs"><AttachmentLink attachments={atts} type="공고문" /></td>
      <td className="px-3 py-3 text-center text-xs"><AttachmentLink attachments={atts} type="제안요청서" /></td>
      <td className="px-3 py-3 text-center text-xs"><AttachmentLink attachments={atts} type="과업지시서" /></td>
      <td className="px-3 py-3 text-center">
        {bid.proposal_status ? (
          <div className="flex flex-col items-center gap-0.5">
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border whitespace-nowrap ${
              bid.proposal_status === "제안결정" || bid.proposal_status === "제안착수" ? "text-[#3ecf8e] bg-emerald-950/60 border-emerald-900"
              : bid.proposal_status === "제안포기" ? "text-red-400 bg-red-950/60 border-red-900"
              : bid.proposal_status === "제안유보" ? "text-orange-400 bg-orange-950/60 border-orange-900"
              : bid.proposal_status === "관련없음" ? "text-[#5c5c5c] bg-[#1c1c1c] border-[#262626]"
              : bid.proposal_status === "검토중" ? "text-yellow-400 bg-yellow-950/60 border-yellow-900"
              : "text-[#8c8c8c] bg-[#1c1c1c] border-[#262626]"
            }`}>
              {bid.proposal_status === "제안결정" && teams.length > 0 ? `${teams[0]} 제안착수` : bid.proposal_status}
            </span>
            {bid.decided_by && <span className="text-[11px] text-[#5c5c5c]">{bid.decided_by}</span>}
          </div>
        ) : <span className="text-[10px] text-[#3c3c3c]">-</span>}
      </td>
    </tr>
  );
}

function EmptyState({ scope }: { scope: Scope }) {
  const messages: Record<Scope, { title: string; desc: string; icon: string }> = {
    my: { title: "관심 공고가 없습니다", desc: "전체 탭에서 관심 있는 공고를 북마크하거나, 프로필의 관심분야를 설정하세요.", icon: "★" },
    team: { title: "팀 추천 공고가 없습니다", desc: "팀 프로필과 검색 조건을 설정하면 AI가 맞춤 공고를 추천합니다.", icon: "👥" },
    division: { title: "본부 추천 공고가 없습니다", desc: "본부 내 팀들의 추천 공고가 수집되면 여기에 표시됩니다.", icon: "🏢" },
    company: { title: "모니터링된 공고가 없습니다", desc: "공고 수집이 아직 실행되지 않았습니다. 팀 설정 후 공고를 수집해주세요.", icon: "📡" },
  };
  const m = messages[scope];
  return (
    <div className="flex flex-col items-center justify-center h-64 text-center">
      <div className="w-12 h-12 rounded-xl bg-[#1c1c1c] border border-[#262626] flex items-center justify-center text-2xl mb-4">{m.icon}</div>
      <h3 className="text-sm font-semibold text-[#ededed] mb-1">{m.title}</h3>
      <p className="text-xs text-[#8c8c8c] mb-6 max-w-xs">{m.desc}</p>
      {scope === "team" && (
        <Link href="/bids/settings" className="bg-[#3ecf8e] hover:bg-[#49e59e] text-black font-semibold rounded-lg px-5 py-2 text-sm transition-colors">설정하기</Link>
      )}
    </div>
  );
}
