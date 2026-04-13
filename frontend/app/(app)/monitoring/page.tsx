"use client";

/**
 * F-05: 공고 모니터링 페이지
 * - 뷰: AI 추천 (Scored) / 모니터링 (Monitor)
 * - 통합 필터 바: 텍스트검색, 예산, 발주처, 단계, 퀵프리셋, 컬럼 정렬
 * - URL 파라미터로 필터 상태 저장
 */

import React, { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, MonitoredBid, ScoredBid, BidAttachment } from "@/lib/api";

// ── 타입 ──────────────────────────────────────────────────

type ViewMode = "scored" | "monitor";
type Scope = "my" | "team" | "division" | "company";
type SortConfig = { key: string; dir: "asc" | "desc" } | null;

const SCOPE_LABELS: Record<Scope, { label: string; desc: string }> = {
  my: { label: "개인", desc: "내 관심분야" },
  team: { label: "팀", desc: "우리팀 관심분야" },
  division: { label: "본부", desc: "우리본부 관심분야" },
  company: { label: "전체", desc: "TENOPA 관심분야" },
};

const BUDGET_OPTIONS = [
  { label: "금액", value: 0 },
  { label: "5천만+", value: 50_000_000 },
  { label: "1억+", value: 100_000_000 },
  { label: "3억+", value: 300_000_000 },
  { label: "5억+", value: 500_000_000 },
  { label: "10억+", value: 1_000_000_000 },
];

// ── 유틸 ──────────────────────────────────────────────────

function formatBudget(amount: number | null): string {
  if (!amount) return "미기재";
  // 억원 단위 통일 (소수점 2자리)
  return `${(amount / 100_000_000).toFixed(2)}억`;
}

function calcDday(deadline: string | null | undefined): number | null {
  if (!deadline) return null;
  const d = new Date(deadline);
  if (isNaN(d.getTime())) return null;
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  d.setHours(0, 0, 0, 0);
  return Math.ceil((d.getTime() - now.getTime()) / 86400000);
}

function extractDomain(title: string): string[] {
  const DOMAIN_MAP: [RegExp, string][] = [
    // 구체적 패턴 먼저 배치 (스마트시티/스마트제조 구분 개선)
    [/스마트제조|산업4\.0|스마트팩토리/i, "제조"],
    [/제조(?!팩토리)|생산\s*기술/i, "제조"],
    [/스마트시티|스마트도시/i, "스마트시티"],
    [/디지털트랜스포메이션|DX\b|디지털화|고도화/i, "DX"],

    [/양자/i, "양자"],
    [/공항|항공/i, "항공"],
    [/결핵|감염|방역|보건|의료|건강/i, "보건의료"],
    [/소부장|소재|부품|장비/i, "소부장"],
    [/디자인/i, "디자인"],
    [/AI|인공지능|머신러닝|딥러닝/i, "AI"],
    [/클라우드|SaaS|IaaS/i, "클라우드"],
    [/빅데이터|데이터/i, "데이터"],
    [/블록체인/i, "블록체인"],
    [/로봇|드론|자율주행/i, "로봇/자율"],
    [/에너지|태양광|풍력|수소|탄소/i, "에너지"],
    [/환경|폐기물|재활용|기후/i, "환경"],
    [/교통|도로|철도|물류/i, "교통물류"],
    [/건설|건축|토목|인프라/i, "건설"],
    [/농업|농촌|축산|수산/i, "농수산"],
    [/교육|학교|대학|훈련/i, "교육"],
    [/문화|관광|콘텐츠|미디어/i, "문화관광"],
    [/국방|군사|방위/i, "국방"],
    [/우주|위성/i, "우주"],
    [/반도체|디스플레이/i, "반도체"],
    [/바이오|제약|의약/i, "바이오"],
    [/정보보안|보안|사이버/i, "정보보안"],
    [/ICT|정보통신|SW|소프트웨어/i, "ICT"],
    [/해양|해운|항만/i, "해양"],
    [/산림|녹지|공원/i, "산림"],
    [/복지|사회/i, "사회복지"],
  ];
  const found: string[] = [];
  for (const [re, label] of DOMAIN_MAP) {
    if (re.test(title) && !found.includes(label)) found.push(label);
    if (found.length >= 2) break;
  }
  return found;
}

// TENOPA 실제 조직도 기반 팀 추천
const TEAM_SPECS: { name: string; division: string; keywords: RegExp }[] = [
  {
    name: "혁신1팀",
    division: "혁신전략본부",
    keywords:
      /과학기술인재|신산업정책|AI안전|탄소소재|국토교통|탄소중립|기후변화|탄소|교통|국토/i,
  },
  {
    name: "혁신2팀",
    division: "혁신전략본부",
    keywords:
      /성과분석|정밀의료|동향조사|감염병|바이오빅데이터|바이오헬스|성과|동향|바이오|감염|방역|보건|의약|제약/i,
  },
  {
    name: "혁신3팀",
    division: "혁신전략본부",
    keywords:
      /건강관리|재생의료|정신건강|의료기기|마약류|고령친화|만성질환|의료|건강|복지|고령|재활/i,
  },
  {
    name: "버티컬AX1팀",
    division: "버티컬AX본부",
    keywords:
      /AI시티|AI빅데이터|피지컬AI|정신건강|필수의료|예타기획|AI|인공지능|빅데이터|스마트시티|스마트|디지털|데이터|ICT/i,
  },
  {
    name: "공공1팀",
    division: "공공AX본부",
    keywords:
      /재난안전|원자력|토양지하수|환경보험|유해물질|재생의료|양자|자율제조|지역혁신|재난|원자력|환경|에너지|안전|폐기물|유해|양자|지역/i,
  },
  {
    name: "기술사업화1팀",
    division: "기술사업화본부",
    keywords:
      /스케일업|기술사업화|벤처성장|딥테크|PMO|프로젝트관리|벤처|창업|기술이전|사업화|스타트업|중소기업|성장지원/i,
  },
  {
    name: "AX혁신팀",
    division: "AX허브연구소",
    keywords:
      /AI업무자동화|AI\s?교육|AX컨설팅|업무자동화|교육훈련|컨설팅|DX|디지털전환|SW|소프트웨어|정보화|ISP/i,
  },
];

function guessTeam(title: string, classification: string): string {
  const text = `${title} ${classification}`;
  let bestTeam = "혁신1팀";
  let bestScore = 0;
  for (const t of TEAM_SPECS) {
    const matches = text.match(t.keywords);
    const score = matches ? matches.length : 0;
    if (score > bestScore) {
      bestScore = score;
      bestTeam = t.name;
    }
  }
  return bestTeam;
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
    입찰공고: "text-[#8c8c8c] bg-[#1c1c1c] border-[#262626]",
    사전규격: "text-blue-400 bg-blue-950/60 border-blue-900",
    발주계획: "text-purple-400 bg-purple-950/60 border-purple-900",
  };
  const label: Record<string, string> = {
    입찰공고: "공고",
    사전규격: "사전",
    발주계획: "계획",
  };
  return (
    <span
      className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${style[stage] || style["입찰공고"]}`}
    >
      {label[stage] || stage}
    </span>
  );
}

function scoreColor(score: number): string {
  // 점수 범위 감지: 0-100 (AI 분석) vs 0-150+ (규칙 기반)
  // AI 점수: 0-100 → 80%, 67%, 53%, 33% 기준
  // 규칙 점수: 0-150+ → 120, 100, 80, 50 기준
  const isAiScore = score <= 100;

  if (isAiScore) {
    // 0-100 범위 (AI 분석 점수)
    if (score >= 80) return "text-purple-400 bg-purple-950/60 border-purple-900";
    if (score >= 67) return "text-emerald-400 bg-emerald-950/60 border-emerald-900";
    if (score >= 53) return "text-blue-400 bg-blue-950/60 border-blue-900";
    if (score >= 33) return "text-yellow-400 bg-yellow-950/60 border-yellow-900";
  } else {
    // 0-150+ 범위 (규칙 기반 점수)
    if (score >= 120) return "text-purple-400 bg-purple-950/60 border-purple-900";
    if (score >= 100) return "text-emerald-400 bg-emerald-950/60 border-emerald-900";
    if (score >= 80) return "text-blue-400 bg-blue-950/60 border-blue-900";
    if (score >= 50) return "text-yellow-400 bg-yellow-950/60 border-yellow-900";
  }

  return "text-[#8c8c8c] bg-[#1c1c1c] border-[#262626]";
}

// ── 캐시 (모듈 레벨, 컴포넌트 리마운트에도 유지) ──────────

interface CacheEntry<T> {
  data: T;
  fetchedAt: number; // Date.now()
  cacheKey: string;
}

const CACHE_TTL = 5 * 60 * 1000; // 5분

const scoredCache: {
  current: CacheEntry<{
    bids: ScoredBid[];
    totalFetched: number;
    dateFrom: string;
    dateTo: string;
    sources: Record<string, number>;
  }> | null;
} = { current: null };
const monitorCache: {
  current: CacheEntry<{ bids: MonitoredBid[]; total: number }> | null;
} = { current: null };

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
  const haystack = [
    bid.title,
    bid.agency,
    bid.classification,
    ...bid.role_keywords,
    ...bid.domain_keywords,
  ]
    .join(" ")
    .toLowerCase();
  return tokens.every((t) => haystack.includes(t));
}

function matchesMonitorSearch(bid: MonitoredBid, query: string): boolean {
  if (!query) return true;
  const tokens = query.toLowerCase().split(/\s+/).filter(Boolean);
  const haystack = [
    bid.bid_title,
    bid.agency,
    bid.recommendation_summary || "",
    ...(bid.related_teams || []),
  ]
    .join(" ")
    .toLowerCase();
  return tokens.every((t) => haystack.includes(t));
}

function sortBids<T>(
  items: T[],
  config: SortConfig,
  getter: (item: T, key: string) => number | null,
): T[] {
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

// ── 필터링 + 정렬 헤더 컴포넌트 ────────────────────────────────

function FilterableSortableHeader({
  sortKey,
  current,
  onSort,
  filterValue,
  onFilterChange,
  className = "",
}: {
  sortKey: string;
  current: SortConfig;
  onSort: (key: string) => void;
  filterValue: "all" | "under100" | "over100";
  onFilterChange: (value: "all" | "under100" | "over100") => void;
  className?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const isActive = current?.key === sortKey;
  const arrowColor = isActive ? "text-[#3ecf8e]" : "text-[#3c3c3c]";

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  return (
    <th
      className={`px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap relative ${className}`}
    >
      <div className="flex items-center gap-2 relative" ref={dropdownRef}>
        {/* 드롭다운 버튼 */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="text-[#5c5c5c] font-medium hover:text-[#8c8c8c] transition-colors cursor-pointer"
        >
          예산 ▼
        </button>

        {/* 드롭다운 메뉴 */}
        {isOpen && (
          <div className="absolute top-full left-0 mt-1 bg-[#1c1c1c] border border-[#262626] rounded shadow-lg z-50 min-w-max">
            {(["all", "under100", "over100"] as const).map((value) => {
              const labels = {
                all: "전체",
                under100: "1억원 이하",
                over100: "1억원 초과",
              };
              return (
                <button
                  key={value}
                  onClick={() => {
                    onFilterChange(value);
                    setIsOpen(false);
                  }}
                  className={`block w-full text-left px-3 py-2 text-xs hover:bg-[#262626] transition-colors ${
                    filterValue === value
                      ? "text-[#3ecf8e] font-medium"
                      : "text-[#ededed]"
                  }`}
                >
                  {labels[value]}
                </button>
              );
            })}
          </div>
        )}

        {/* 정렬 버튼 */}
        <button
          onClick={() => onSort(sortKey)}
          title="오름/내림차순 정렬"
          className={`px-1.5 py-0.5 rounded hover:bg-[#262626] transition-colors ${arrowColor} hover:text-[#8c8c8c]`}
        >
          {isActive ? (current.dir === "desc" ? "▼" : "▲") : "⇅"}
        </button>
      </div>
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
      if (ref.current && !ref.current.contains(e.target as Node))
        setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const filtered = input
    ? agencies
        .filter((a) => a.toLowerCase().includes(input.toLowerCase()))
        .slice(0, 8)
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
          <button
            onClick={() => {
              onChange("");
              setInput("");
            }}
            className="text-[#5c5c5c] hover:text-[#ededed] text-xs"
          >
            ✕
          </button>
        )}
      </div>
      {open && filtered.length > 0 && (
        <div className="absolute top-full left-0 mt-1 w-[220px] bg-[#1c1c1c] border border-[#262626] rounded-lg shadow-lg z-20 max-h-48 overflow-y-auto">
          {filtered.map((a) => (
            <button
              key={a}
              onClick={() => {
                onChange(a);
                setInput(a);
                setOpen(false);
              }}
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

function formatCrawledAt(ts: number | null): string {
  if (!ts) return "";
  const d = new Date(ts);
  const yyyy = d.getFullYear();
  const MM = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  return `${yyyy}-${MM}-${dd} ${hh}:${mm}:${ss}`;
}

export default function BidsMonitorPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // ── URL -> initial values ──
  const initView = (searchParams.get("view") as ViewMode) || "scored";
  const initScope = (searchParams.get("scope") as Scope) || "company";

  const [scope, setScope] = useState<Scope>(initScope);
  const [lastCrawledAt, setLastCrawledAt] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [crawling, setCrawling] = useState(false);
  // 크롤링할 때 사용할 최소 예산 (기본값: 5천만원)
  const [minBudgetForCrawl, setMinBudgetForCrawl] = useState(
    Number(searchParams.get("budget")) || 0,
  );

  // 수동 크롤링 트리거 (POST /bids/crawl → DB 저장 후 목록 갱신)
  async function handleManualCrawl() {
    setCrawling(true);
    try {
      const baseUrl =
        process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
      // min_budget 파라미터 포함: 사용자 선택 예산 이상의 공고만 크롤링
      const res = await fetch(`${baseUrl}/bids/crawl?days=1&min_budget=${minBudgetForCrawl}`, {
        method: "POST",
      });
      if (!res.ok) {
        // 크롤링 실패해도 새로고침 수행
      }
      setRefreshKey((k) => k + 1);
    } catch (e) {
      // 크롤링 요청 중 오류 발생
    } finally {
      setCrawling(false);
    }
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
      {/* 헤더 */}
      <div className="border-b border-[#262626] px-6 py-4 shrink-0">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <h1 className="text-sm font-semibold text-[#ededed] shrink-0">
              공고 모니터링
            </h1>
            {/* 수동 크롤링 버튼 */}
            <button
              onClick={handleManualCrawl}
              disabled={crawling}
              title="나라장터 공고 새로고침"
              className="p-1 rounded-md text-[#8c8c8c] hover:text-[#3ecf8e] hover:bg-[#1c1c1c] transition-colors disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className={crawling ? "animate-spin" : ""}
              >
                <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" />
                <path d="M21 3v5h-5" />
              </svg>
            </button>
            <p className="text-xs text-[#8c8c8c] ml-1 truncate hidden sm:block">
              AI 적합도 스코어링 기반 추천 · {SCOPE_LABELS[scope].desc}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* 스코프 탭 */}
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
          </div>
        </div>
      </div>

      {/* 콘텐츠 */}
      <div className="flex-1 overflow-auto px-6 py-4">
        <ScoredBidsView refreshKey={refreshKey} onFetched={setLastCrawledAt} />
      </div>

      {/* 하단 크롤링 시간 */}
      <div className="border-t border-[#262626] px-6 py-2 shrink-0 flex items-center justify-between">
        <p className="text-[10px] text-[#5c5c5c]">
          {lastCrawledAt
            ? `마지막 데이터 수집: ${formatCrawledAt(lastCrawledAt)}`
            : "데이터 수집 대기 중..."}
        </p>
        <p className="text-[10px] text-[#5c5c5c]">출처: 나라장터 (G2B)</p>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// AI 추천 (Scored) 뷰
// ══════════════════════════════════════════════════════════

function ScoredBidsView({
  refreshKey,
  onFetched,
}: {
  refreshKey?: number;
  onFetched?: (ts: number) => void;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();

  // ── 데이터 ──
  const [bids, setBids] = useState<ScoredBid[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [requiresCrawl, setRequiresCrawl] = useState(false);
  const [totalFetched, setTotalFetched] = useState(0);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sources, setSources] = useState<Record<string, number>>({});
  const [fetchedAt, setFetchedAt] = useState<number | null>(null);

  // ── 서버 필터 (API 파라미터) ──
  const [days, setDays] = useState(Number(searchParams.get("days")) || 7);
  const [minScoreServer, setMinScoreServer] = useState(
    Number(searchParams.get("score")) || 20,
  );

  // ── 클라이언트 필터 ──
  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [debouncedQuery, setDebouncedQuery] = useState(query);
  const [minBudget, setMinBudget] = useState(
    Number(searchParams.get("budget")) || 0,
  );
  const [budgetFilterType, setBudgetFilterType] = useState<"all" | "under100" | "over100">(
    (searchParams.get("budgetFilter") as "all" | "under100" | "over100") || "all",
  );
  const [agency, setAgency] = useState(searchParams.get("agency") || "");
  const [stageFilter, setStageFilter] = useState<Set<string>>(
    new Set(["입찰공고", "사전규격", "발주계획"]),
  );
  const [sortConfig, setSortConfig] = useState<SortConfig>(null);

  // 디바운스
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query), 200);
    return () => clearTimeout(t);
  }, [query]);

  // 응답을 state에 반영하는 헬퍼
  function applyResponse(
    data: ScoredBid[],
    total: number,
    from: string,
    to: string,
    src: Record<string, number>,
    ts: number,
    crawlNeeded = false,
  ) {
    setBids(data);
    setTotalFetched(total);
    setDateFrom(from);
    setDateTo(to);
    setSources(src);
    setFetchedAt(ts);
    setRequiresCrawl(crawlNeeded);
    onFetched?.(ts);
  }

  // refreshKey 변경 시 강제 새로고침
  useEffect(() => {
    if (refreshKey && refreshKey > 0) load(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  // 데이터 로드 (캐시 활용, forceRefresh로 강제 갱신)
  const load = useCallback(
    async (forceRefresh = false) => {
      const cacheKey = `scored_${days}_${minScoreServer}`;

      // 캐시 히트: 같은 파라미터 + 5분 이내
      if (
        !forceRefresh &&
        scoredCache.current &&
        scoredCache.current.cacheKey === cacheKey &&
        Date.now() - scoredCache.current.fetchedAt < CACHE_TTL
      ) {
        const c = scoredCache.current.data;
        applyResponse(
          c.bids,
          c.totalFetched,
          c.dateFrom,
          c.dateTo,
          c.sources,
          scoredCache.current.fetchedAt,
        );
        setLoading(false);
        return;
      }

      setLoading(true);
      setError("");
      try {
        const res = await api.bids.scored({
          days,
          minScore: minScoreServer,
          maxResults: 200,
        });
        const now = Date.now();
        const payload = res.data ?? res;
        const d = (payload as { data?: unknown }).data ?? payload ?? [];
        const dataArr = Array.isArray(d) ? d : [];
        const crawlNeeded = !!(payload as { requires_crawl?: boolean }).requires_crawl;
        applyResponse(
          dataArr,
          (payload as { total_fetched?: number }).total_fetched || 0,
          (payload as { date_from?: string }).date_from || "",
          (payload as { date_to?: string }).date_to || "",
          (payload as { sources?: Record<string, number> }).sources || {},
          now,
          crawlNeeded,
        );
        scoredCache.current = {
          data: {
            bids: dataArr,
            totalFetched: (payload as { total_fetched?: number }).total_fetched || 0,
            dateFrom: (payload as { date_from?: string }).date_from || "",
            dateTo: (payload as { date_to?: string }).date_to || "",
            sources: (payload as { sources?: Record<string, number> }).sources || {},
          },
          fetchedAt: now,
          cacheKey,
        };
      } catch {
        try {
          const baseUrl =
            process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
          const directRes = await fetch(
            `${baseUrl}/bids/scored?days=${days}&min_score=${minScoreServer}&max_results=200`,
          );
          if (directRes.ok) {
            const json = await directRes.json();
            const now = Date.now();
            const jsonPayload = json.data ?? json;
            const d = (jsonPayload as { data?: unknown }).data ?? jsonPayload ?? [];
            const dataArr = Array.isArray(d) ? d : [];
            applyResponse(
              dataArr,
              (jsonPayload as { total_fetched?: number }).total_fetched || 0,
              (jsonPayload as { date_from?: string }).date_from || "",
              (jsonPayload as { date_to?: string }).date_to || "",
              (jsonPayload as { sources?: Record<string, number> }).sources || {},
              now,
            );
            scoredCache.current = {
              data: {
                bids: dataArr,
                totalFetched: (jsonPayload as { total_fetched?: number }).total_fetched || 0,
                dateFrom: (jsonPayload as { date_from?: string }).date_from || "",
                dateTo: (jsonPayload as { date_to?: string }).date_to || "",
                sources: (jsonPayload as { sources?: Record<string, number> }).sources || {},
              },
              fetchedAt: now,
              cacheKey,
            };
            return;
          }
        } catch {
          setError("백엔드에 연결할 수 없습니다.");
        }
        setBids([]);
      } finally {
        setLoading(false);
      }
    },
    [days, minScoreServer],
  );

  useEffect(() => {
    load();
  }, [load]);

  // 발주처 목록 추출
  const agencies = useMemo(
    () => [...new Set(bids.map((b) => b.agency))].sort(),
    [bids],
  );

  // 클라이언트 필터 + 정렬
  const filteredBids = useMemo(() => {
    let result = bids
      .filter((b) => stageFilter.has(b.bid_stage || "입찰공고"))
      .filter((b) => matchesScoredSearch(b, debouncedQuery))
      .filter((b) => {
        // 예산 필터
        if (budgetFilterType === "all") return true;
        const budget = b.budget || 0;
        if (budgetFilterType === "under100") return budget <= 100_000_000;
        if (budgetFilterType === "over100") return budget > 100_000_000;
        return true;
      });

    return sortBids(result, sortConfig, (b, key) => {
      if (key === "score") return (b.suitability_score ?? b.score) || 0;
      if (key === "budget") return b.budget || 0;
      if (key === "d_day") return b.d_day ?? 999;
      return null;
    });
  }, [bids, stageFilter, debouncedQuery, sortConfig, budgetFilterType]);

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
      if (next.has(stage)) {
        if (next.size > 1) next.delete(stage);
      } else next.add(stage);
      return next;
    });
  }

  // 활성 필터 수
  const activeFilterCount = [
    debouncedQuery !== "",
    budgetFilterType !== "all",
    stageFilter.size < 3,
    sortConfig !== null,
  ].filter(Boolean).length;

  // 초기화
  function resetFilters() {
    setQuery("");
    setBudgetFilterType("all");
    setStageFilter(new Set(["입찰공고", "사전규격", "발주계획"]));
    setSortConfig(null);
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
        {/* 공고/사전/계획 필터 (상단 좌측) */}
        <div className="flex items-center gap-2 text-[10px] text-[#5c5c5c]">
          {(["입찰공고", "사전규격", "발주계획"] as const).map((stage) => (
            <label
              key={stage}
              className="flex items-center gap-1 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={stageFilter.has(stage)}
                onChange={() => toggleStage(stage)}
                className="w-3 h-3 rounded border-[#262626] bg-[#1c1c1c] accent-[#3ecf8e]"
              />
              <span>
                {stage === "입찰공고"
                  ? "공고"
                  : stage === "사전규격"
                    ? "사전"
                    : "계획"}
              </span>
            </label>
          ))}
        </div>

        {/* 검색 */}
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="공고명, 키워드 검색"
          className="w-[220px] bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-xs text-[#ededed] placeholder:text-[#5c5c5c]"
        />

        {/* 필터 카운트 + 초기화 + 크롤링 시각 + 새로고침 */}
        <span className="text-[10px] text-[#5c5c5c] ml-auto flex items-center gap-2">
          {activeFilterCount > 0 && (
            <>
              <span>{activeFilterCount}개 필터</span>
              <button
                onClick={resetFilters}
                className="text-[#3ecf8e] hover:underline"
              >
                초기화
              </button>
              <span>·</span>
            </>
          )}
          {loading ? (
            "수집 중..."
          ) : (
            <>
              {`${filteredBids.length}건`}
              {totalFetched > 0 && ` / 전수 ${totalFetched.toLocaleString()}건`}
              {Object.keys(sources).length > 0 &&
                (() => {
                  const parts = (["입찰공고", "사전규격", "발주계획"] as const)
                    .filter((k) => (sources[k] ?? 0) > 0)
                    .map(
                      (k) =>
                        `${{ 입찰공고: "공고", 사전규격: "사전규격", 발주계획: "발주계획" }[k]} ${sources[k]}`,
                    );
                  return parts.length > 0 ? ` (${parts.join(" · ")})` : null;
                })()}
            </>
          )}
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
          <p className="text-sm text-[#5c5c5c]">
            G2B 전수 수집 + 스코어링 중...
          </p>
        </div>
      ) : filteredBids.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-40 text-center gap-2">
          {requiresCrawl ? (
            <>
              <p className="text-sm text-[#8c8c8c]">공고 데이터가 없습니다</p>
              <p className="text-xs text-[#5c5c5c]">
                상단 ↻ 버튼을 눌러 나라장터에서 공고를 불러오세요
              </p>
            </>
          ) : (
            <>
              <p className="text-sm text-[#8c8c8c]">조건에 맞는 공고가 없습니다</p>
              <p className="text-xs text-[#5c5c5c]">
                기간을 늘리거나 필터를 조정해보세요
              </p>
            </>
          )}
        </div>
      ) : (
        <div className="rounded-lg border border-[#262626] bg-[#111111] overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#262626] bg-[#0f0f0f]">
                <th className="text-center px-2 py-2.5 text-xs font-medium text-[#5c5c5c] w-10">
                  #
                </th>
                <th className="text-center px-2 py-2.5 text-xs font-medium text-[#5c5c5c] w-14">
                  구분
                </th>
                <SortableHeader
                  label="적합도"
                  sortKey="score"
                  current={sortConfig}
                  onSort={handleSort}
                  className="text-center w-16"
                />
                <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c]">
                  공고명
                </th>
                <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">
                  발주기관
                </th>
                <FilterableSortableHeader
                  sortKey="budget"
                  current={sortConfig}
                  onSort={handleSort}
                  filterValue={budgetFilterType}
                  onFilterChange={setBudgetFilterType}
                  className="text-right"
                />
                <SortableHeader
                  label="마감"
                  sortKey="d_day"
                  current={sortConfig}
                  onSort={handleSort}
                  className="text-center"
                />
                <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">
                  컨설팅 영역
                </th>
                <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">
                  산업/기술
                </th>
                <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">
                  추천 팀
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredBids.map((bid, idx) => (
                <tr
                  key={bid.bid_no}
                  onClick={async () => {
                    sessionStorage.setItem(
                      `bid_scored_${bid.bid_no}`,
                      JSON.stringify(bid),
                    );
                    // DB에 공고가 없을 수 있으므로 상세 API를 미리 호출하여 G2B fallback + DB 저장 트리거
                    const baseUrl =
                      process.env.NEXT_PUBLIC_API_URL ??
                      "http://localhost:8000/api";
                    fetch(`${baseUrl}/bids/${bid.bid_no}`, {
                      signal: AbortSignal.timeout(10000),
                    }).catch(() => {});
                    router.push(`/monitoring/${bid.bid_no}/review`);
                  }}
                  className="border-b border-[#1a1a1a] last:border-0 hover:bg-[#161616] transition-colors cursor-pointer"
                >
                  <td className="px-2 py-3 text-center text-xs text-[#5c5c5c]">
                    {idx + 1}
                  </td>
                  <td className="px-2 py-3 text-center">
                    <StageBadge stage={bid.bid_stage || "입찰공고"} />
                  </td>
                  <td className="px-2 py-3 text-center">
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded-md border ${scoreColor(bid.suitability_score ?? bid.score)}`}
                    >
                      {(bid.suitability_score ?? bid.score).toFixed(0)}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    <span className="text-sm text-[#ededed] leading-snug">
                      {bid.title}
                    </span>
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap">
                    <span className="text-[11px] text-[#8c8c8c]">
                      {bid.agency.length > 12
                        ? bid.agency.slice(0, 12) + "…"
                        : bid.agency}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-right whitespace-nowrap">
                    <span className="text-xs text-[#8c8c8c]">
                      {formatBudget(bid.budget)}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-center whitespace-nowrap">
                    {(() => {
                      const dday = calcDday(bid.deadline);
                      return dday !== null ? (
                        <DdayBadge days={dday} />
                      ) : (
                        <span className="text-xs text-[#3c3c3c]">-</span>
                      );
                    })()}
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex flex-wrap gap-1">
                      {(bid.role_keywords || []).map((kw) => (
                        <span
                          key={kw}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950/40 text-emerald-400 border border-emerald-900/50"
                        >
                          {kw}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex flex-wrap gap-1">
                      {(bid.domain_keywords || extractDomain(bid.title)).map((kw) => (
                        <span
                          key={kw}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-blue-950/40 text-blue-400 border border-blue-900/50"
                        >
                          {kw}
                        </span>
                      ))}
                      {(bid.domain_keywords || extractDomain(bid.title)).length === 0 && (
                        <span className="text-[10px] text-[#3c3c3c]">-</span>
                      )}
                    </div>
                  </td>
                  <td className="px-3 py-3 text-center whitespace-nowrap">
                    <span className="text-[10px] text-[#8c8c8c]">
                      {guessTeam(bid.title, bid.classification)}
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

// ══════════════════════════════════════════════════════════
// 모니터링 뷰
// ══════════════════════════════════════════════════════════

function MonitorBidsView({
  scope,
  refreshKey,
  onFetched,
}: {
  scope: Scope;
  refreshKey?: number;
  onFetched?: (ts: number) => void;
}) {
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
  const [minBudget, setMinBudget] = useState(
    Number(searchParams.get("budget")) || 0,
  );
  const [budgetFilterType, setBudgetFilterType] = useState<"all" | "under100" | "over100">(
    (searchParams.get("budgetFilter") as "all" | "under100" | "over100") || "all",
  );
  const [agency, setAgency] = useState(searchParams.get("agency") || "");
  const [statusFilter, setStatusFilter] = useState("");
  const [relevanceFilter, setRelevanceFilter] = useState("");
  const [sortConfig, setSortConfig] = useState<SortConfig>(null);
  const [activePreset, setActivePreset] = useState<string | null>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query), 200);
    return () => clearTimeout(t);
  }, [query]);

  const loadBids = useCallback(
    async (s: Scope, p: number, forceRefresh = false) => {
      const cacheKey = `monitor_${s}_${p}`;

      if (
        !forceRefresh &&
        monitorCache.current &&
        monitorCache.current.cacheKey === cacheKey &&
        Date.now() - monitorCache.current.fetchedAt < CACHE_TTL
      ) {
        const c = monitorCache.current.data;
        setBids(c.bids);
        setTotal(c.total);
        setFetchedAt(monitorCache.current.fetchedAt);
        onFetched?.(monitorCache.current.fetchedAt);
        setLoading(false);
        return;
      }

      setLoading(true);
      setError("");
      try {
        const res = await api.bids.monitor(s, p, false);
        const now = Date.now();
        setBids(res.data || []);
        setTotal(res.meta?.total || 0);
        setFetchedAt(now);
        onFetched?.(now);
        monitorCache.current = {
          data: { bids: res.data || [], total: res.meta?.total || 0 },
          fetchedAt: now,
          cacheKey,
        };
      } catch {
        try {
          const baseUrl =
            process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
          const directRes = await fetch(
            `${baseUrl}/bids/monitor?scope=${s}&page=${p}&show_all=false`,
          );
          if (directRes.ok) {
            const json = await directRes.json();
            const now = Date.now();
            setBids(json.data || []);
            setTotal(json.meta?.total || 0);
            setFetchedAt(now);
            onFetched?.(now);
            monitorCache.current = {
              data: { bids: json.data || [], total: json.meta?.total || 0 },
              fetchedAt: now,
              cacheKey,
            };
            return;
          }
        } catch {
          setError("백엔드에 연결할 수 없습니다.");
        }
        setBids([]);
      } finally {
        setLoading(false);
      }
    },
    [onFetched],
  );

  // refreshKey 변경 시 강제 새로고침
  useEffect(() => {
    if (refreshKey && refreshKey > 0) loadBids(scope, page, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  useEffect(() => {
    setPage(1);
    loadBids(scope, 1);
  }, [scope, loadBids]);
  useEffect(() => {
    if (page > 1) loadBids(scope, page);
  }, [page, scope, loadBids]);

  const agencies = useMemo(
    () => [...new Set(bids.map((b) => b.agency))].sort(),
    [bids],
  );

  const RELEVANCE_MAP: Record<string, number> = {
    "적극 추천": 3,
    보통: 2,
    낮음: 1,
  };

  const filteredBids = useMemo(() => {
    let result = bids
      .filter((b) => matchesMonitorSearch(b, debouncedQuery))
      .filter((b) => {
        // 예산 필터
        if (budgetFilterType === "all") return true;
        const budget = b.budget_amount ?? 0;
        if (budgetFilterType === "under100") return budget <= 100_000_000;
        if (budgetFilterType === "over100") return budget > 100_000_000;
        return true;
      })
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
  }, [
    bids,
    debouncedQuery,
    budgetFilterType,
    agency,
    statusFilter,
    relevanceFilter,
    sortConfig,
  ]);

  function handleSort(key: string) {
    setSortConfig((prev) => {
      if (!prev || prev.key !== key) return { key, dir: "desc" };
      if (prev.dir === "desc") return { key, dir: "asc" };
      return null;
    });
  }

  function applyPreset(name: string) {
    if (activePreset === name) {
      setActivePreset(null);
      resetFilters();
      return;
    }
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

  async function handleStatusChange(
    bidNo: string,
    status: "검토중" | "제안착수" | "관련없음",
  ) {
    try {
      await api.bids.updateStatus(bidNo, status);
      setBids((prev) =>
        prev.map((b) =>
          b.bid_no === bidNo ? { ...b, proposal_status: status } : b,
        ),
      );
    } catch {
      /* 인증 실패 허용 */
    }
  }

  async function handleBookmark(bidNo: string) {
    try {
      const res = await api.bids.toggleBookmark(bidNo);
      setBids((prev) =>
        prev.map((b) =>
          b.bid_no === bidNo ? { ...b, is_bookmarked: res.bookmarked } : b,
        ),
      );
    } catch {
      /* 무시 */
    }
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
        <PresetButton
          label="검토대기만"
          active={activePreset === "unreviewed"}
          onClick={() => applyPreset("unreviewed")}
        />
        <PresetButton
          label="적극 추천"
          active={activePreset === "recommended"}
          onClick={() => applyPreset("recommended")}
        />
        <PresetButton
          label="대형 1억+"
          active={activePreset === "big"}
          onClick={() => applyPreset("big")}
        />
        <div className="w-px h-5 bg-[#262626]" />

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="공고명, 발주처, 키워드 검색"
          className="w-[220px] bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-xs text-[#ededed] placeholder:text-[#5c5c5c]"
        />

        <select
          value={minBudget}
          onChange={(e) => setMinBudget(Number(e.target.value))}
          className="bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-xs text-[#ededed]"
        >
          {BUDGET_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>

        <AgencyTypeahead
          agencies={agencies}
          value={agency}
          onChange={setAgency}
        />

        {/* 관련성 */}
        <div className="flex items-center gap-1 bg-[#1c1c1c] rounded-lg p-0.5 border border-[#262626]">
          {["", "적극 추천", "보통"].map((r) => (
            <button
              key={r}
              onClick={() => setRelevanceFilter(r)}
              className={`px-2 py-1 rounded-md text-[10px] font-medium transition-colors ${
                relevanceFilter === r
                  ? "bg-[#3ecf8e] text-[#0f0f0f]"
                  : "text-[#5c5c5c] hover:text-[#8c8c8c]"
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
              <button
                onClick={resetFilters}
                className="text-[#3ecf8e] hover:underline"
              >
                초기화
              </button>
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
        <div className="flex items-center justify-center h-40">
          <p className="text-sm text-[#5c5c5c]">불러오는 중...</p>
        </div>
      ) : filteredBids.length === 0 ? (
        <EmptyState scope={scope} />
      ) : (
        <>
          <div className="rounded-lg border border-[#262626] bg-[#111111] overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#262626] bg-[#0f0f0f]">
                  <th className="text-center px-2 py-2.5 text-xs font-medium text-[#5c5c5c] w-8"></th>
                  <th className="text-center px-2 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">
                    단계
                  </th>
                  <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">
                    공고명
                  </th>
                  <th className="text-left px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">
                    발주처
                  </th>
                  <th className="text-right px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">
                    <select
                      value={budgetFilterType}
                      onChange={(e) =>
                        setBudgetFilterType(
                          e.target.value as "all" | "under100" | "over100",
                        )
                      }
                      className="bg-[#1c1c1c] border border-[#262626] rounded px-2 py-1 text-xs text-[#ededed] cursor-pointer hover:border-[#3ecf8e]/50 focus:outline-none focus:border-[#3ecf8e]"
                    >
                      <option value="all">전체</option>
                      <option value="under100">1억원 이하</option>
                      <option value="over100">1억원 초과</option>
                    </select>
                  </th>
                  <SortableHeader
                    label="마감일"
                    sortKey="days"
                    current={sortConfig}
                    onSort={handleSort}
                    className="text-center"
                  />
                  <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">
                    관련 팀
                  </th>
                  <SortableHeader
                    label="관련성"
                    sortKey="relevance"
                    current={sortConfig}
                    onSort={handleSort}
                    className="text-center"
                  />
                  <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">
                    공고문
                  </th>
                  <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">
                    제안요청서
                  </th>
                  <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">
                    과업지시서
                  </th>
                  <th className="text-center px-3 py-2.5 text-xs font-medium text-[#5c5c5c] whitespace-nowrap">
                    검토결과
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredBids.map((bid) => (
                  <BidRow
                    key={bid.bid_no}
                    bid={bid}
                    scope={scope}
                    onBookmark={handleBookmark}
                    onStatusChange={handleStatusChange}
                    onClick={() => {
                      sessionStorage.setItem(
                        `bid_monitor_${bid.bid_no}`,
                        JSON.stringify({
                          bid_no: bid.bid_no,
                          title: bid.bid_title,
                          agency: bid.agency,
                          budget: bid.budget_amount,
                          deadline: bid.deadline_date,
                        }),
                      );
                      router.push(`/monitoring/${bid.bid_no}/review`);
                    }}
                  />
                ))}
              </tbody>
            </table>
          </div>
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
  );
}

// ── 모니터링 행 ─────────────────────────────────────────

function classifyAttachment(
  name: string,
): "공고문" | "제안요청서" | "과업지시서" | null {
  const lower = name.toLowerCase();
  if (lower.includes("제안요청") || lower.includes("rfp")) return "제안요청서";
  if (
    lower.includes("과업지시") ||
    lower.includes("과업내용") ||
    lower.includes("사양서")
  )
    return "과업지시서";
  if (lower.includes("공고") || lower.includes("입찰")) return "공고문";
  return null;
}

function AttachmentLink({
  attachments,
  type,
}: {
  attachments: BidAttachment[];
  type: "공고문" | "제안요청서" | "과업지시서";
}) {
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

function formatDeadline(dateStr: string | null): {
  text: string;
  dday: string;
  color: string;
} {
  if (!dateStr) return { text: "-", dday: "", color: "text-[#8c8c8c]" };
  const d = new Date(dateStr);
  const text = d.toLocaleDateString("ko-KR", {
    month: "numeric",
    day: "numeric",
  });
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const diff = Math.ceil((d.getTime() - now.getTime()) / 86400000);
  const dday = diff <= 0 ? "마감" : `D-${diff}`;
  const color =
    diff <= 7
      ? "text-red-400"
      : diff <= 14
        ? "text-orange-400"
        : "text-[#8c8c8c]";
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
  onStatusChange: (
    bidNo: string,
    status: "검토중" | "제안착수" | "관련없음",
  ) => void;
  onClick: () => void;
}) {
  const deadline = formatDeadline(bid.deadline_date);
  const atts = bid.attachments || [];
  const relevanceColor: Record<string, string> = {
    "적극 추천": "text-[#3ecf8e] bg-emerald-950/60 border-emerald-900",
    보통: "text-yellow-400 bg-yellow-950/60 border-yellow-900",
    낮음: "text-[#5c5c5c] bg-[#1c1c1c] border-[#262626]",
  };
  const rel = bid.relevance || "낮음";
  const teams = bid.related_teams || [];

  return (
    <tr
      onClick={onClick}
      className="border-b border-[#1a1a1a] last:border-0 hover:bg-[#161616] transition-colors cursor-pointer"
    >
      <td className="px-2 py-3 text-center">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onBookmark(bid.bid_no);
          }}
          className={`text-base transition-colors ${bid.is_bookmarked ? "text-yellow-400" : "text-[#3c3c3c] hover:text-yellow-400"}`}
        >
          {bid.is_bookmarked ? "★" : "☆"}
        </button>
      </td>
      <td className="px-2 py-3 text-center">
        <span
          className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${bid.bid_stage === "사전공고" ? "text-blue-400 bg-blue-950/60 border border-blue-900" : "text-[#8c8c8c] bg-[#1c1c1c] border border-[#262626]"}`}
        >
          {bid.bid_stage === "사전공고" ? "사전" : "본공고"}
        </span>
      </td>
      <td className="px-3 py-3">
        <span className="text-sm text-[#ededed] leading-snug">
          {bid.bid_title}
        </span>
      </td>
      <td className="px-3 py-3 whitespace-nowrap">
        <span className="text-[11px] text-[#8c8c8c]">
          {bid.agency.length > 8 ? bid.agency.slice(0, 8) + "…" : bid.agency}
        </span>
      </td>
      <td className="px-3 py-3 text-right whitespace-nowrap">
        <span className="text-xs text-[#8c8c8c]">
          {formatBudget(bid.budget_amount)}
        </span>
      </td>
      <td className="px-3 py-3 text-center whitespace-nowrap">
        <div className="flex flex-col items-center">
          <span className="text-xs text-[#8c8c8c]">{deadline.text}</span>
          <span className={`text-[10px] font-bold ${deadline.color}`}>
            {deadline.dday}
          </span>
        </div>
      </td>
      <td className="px-3 py-3 text-center">
        {teams.length > 0 ? (
          <div className="flex flex-col items-center gap-0.5">
            {teams.map((t, i) => (
              <span
                key={i}
                className="text-[10px] text-[#8c8c8c] bg-[#1c1c1c] border border-[#262626] rounded px-1.5 py-0.5 whitespace-nowrap"
              >
                {t}
              </span>
            ))}
          </div>
        ) : (
          <span className="text-xs text-[#3c3c3c]">-</span>
        )}
      </td>
      <td className="px-3 py-3 text-center">
        <span
          className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${relevanceColor[rel]}`}
        >
          {rel}
        </span>
      </td>
      <td className="px-3 py-3 text-center text-xs">
        <AttachmentLink attachments={atts} type="공고문" />
      </td>
      <td className="px-3 py-3 text-center text-xs">
        <AttachmentLink attachments={atts} type="제안요청서" />
      </td>
      <td className="px-3 py-3 text-center text-xs">
        <AttachmentLink attachments={atts} type="과업지시서" />
      </td>
      <td className="px-3 py-3 text-center">
        {bid.proposal_status ? (
          <div className="flex flex-col items-center gap-0.5">
            <span
              className={`text-[10px] font-bold px-1.5 py-0.5 rounded border whitespace-nowrap ${
                bid.proposal_status === "제안결정" ||
                bid.proposal_status === "제안착수"
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
              }`}
            >
              {bid.proposal_status === "제안결정" && teams.length > 0
                ? `${teams[0]} 제안착수`
                : bid.proposal_status}
            </span>
            {bid.decided_by && (
              <span className="text-[11px] text-[#5c5c5c]">
                {bid.decided_by}
              </span>
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
  const messages: Record<Scope, { title: string; desc: string; icon: string }> =
    {
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
          href="/monitoring/settings"
          className="bg-[#3ecf8e] hover:bg-[#49e59e] text-black font-semibold rounded-lg px-5 py-2 text-sm transition-colors"
        >
          설정하기
        </Link>
      )}
    </div>
  );
}
