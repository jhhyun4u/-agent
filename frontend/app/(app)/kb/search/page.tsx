"use client";

/**
 * 지식 베이스 — 산출물 관리 + KB 텍스트 검색
 * /kb/search
 */

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type ArchiveItem, type KbSearchResult, type KbHealthResponse } from "@/lib/api";

// ── 상수 ──

const SCOPE_TABS = [
  { value: "company", label: "전체" },
  { value: "team", label: "팀" },
  { value: "personal", label: "개인" },
];

const WIN_FILTERS = [
  { value: "", label: "전체" },
  { value: "won", label: "수주" },
  { value: "lost", label: "패찰" },
  { value: "pending", label: "미정" },
];

const WIN_BADGE: Record<string, { label: string; cls: string }> = {
  won: { label: "수주", cls: "bg-[#3ecf8e]/15 text-[#3ecf8e]" },
  lost: { label: "패찰", cls: "bg-red-500/15 text-red-400" },
  pending: { label: "미정", cls: "bg-amber-500/15 text-amber-400" },
};

const KB_AREA_OPTS = [
  { value: "content", label: "콘텐츠" },
  { value: "client", label: "발주기관" },
  { value: "competitor", label: "경쟁사" },
  { value: "lesson", label: "교훈" },
  { value: "capability", label: "역량" },
];

const KB_AREA_ROUTE: Record<string, string> = {
  content: "/kb/content",
  client: "/kb/clients",
  competitor: "/kb/competitors",
  lesson: "/kb/lessons",
  capability: "/kb/content",
};

// ── 유틸 ──

function formatDate(iso: string | null): string {
  if (!iso) return "-";
  try { return new Date(iso).toISOString().slice(0, 10); }
  catch { return "-"; }
}

// ── 페이지 ──

type Tab = "artifacts" | "search";

export default function KbPage() {
  const [activeTab, setActiveTab] = useState<Tab>("artifacts");

  return (
    <>
      <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 shrink-0">
        <div className="flex items-center justify-between">
          <h1 className="text-sm font-semibold text-[#ededed]">지식 베이스</h1>
          <div className="flex items-center gap-1 bg-[#1c1c1c] rounded-lg p-1 border border-[#262626]">
            {([
              { key: "artifacts" as Tab, label: "산출물 관리" },
              { key: "search" as Tab, label: "KB 검색" },
            ]).map((t) => (
              <button
                key={t.key}
                onClick={() => setActiveTab(t.key)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  activeTab === t.key ? "bg-[#3ecf8e] text-[#0f0f0f]" : "text-[#8c8c8c] hover:text-[#ededed]"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-6 py-5">
        {activeTab === "artifacts" ? <ArtifactsView /> : <KbSearchView />}
      </main>
    </>
  );
}

// ══════════════════════════════════════════════════════════
// 산출물 관리 탭
// ══════════════════════════════════════════════════════════

function ArtifactsView() {
  const router = useRouter();
  const [items, setItems] = useState<ArchiveItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [scope, setScope] = useState("company");
  const [winResult, setWinResult] = useState("");
  const [query, setQuery] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // 디바운스
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(query), 300);
    return () => clearTimeout(t);
  }, [query]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.archive.list({
        scope,
        win_result: winResult || undefined,
        page,
        q: debouncedQ || undefined,
      });
      setItems(res.items);
      setTotalPages(res.pages);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [scope, winResult, page, debouncedQ]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { setPage(1); }, [scope, winResult, debouncedQ]);

  const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

  return (
    <div className="space-y-4">
      {/* 필터 바 */}
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="프로젝트명 또는 발주기관 검색"
          className="flex-1 min-w-[200px] bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40"
        />
        {/* 스코프 */}
        <div className="flex items-center gap-1 bg-[#1c1c1c] rounded-lg p-1 border border-[#262626]">
          {SCOPE_TABS.map((s) => (
            <button
              key={s.value}
              onClick={() => setScope(s.value)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                scope === s.value ? "bg-[#3ecf8e] text-[#0f0f0f]" : "text-[#8c8c8c] hover:text-[#ededed]"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
        {/* 수주결과 */}
        <div className="flex items-center gap-1 bg-[#1c1c1c] rounded-lg p-1 border border-[#262626]">
          {WIN_FILTERS.map((w) => (
            <button
              key={w.value}
              onClick={() => setWinResult(w.value)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                winResult === w.value ? "bg-[#3ecf8e] text-[#0f0f0f]" : "text-[#8c8c8c] hover:text-[#ededed]"
              }`}
            >
              {w.label}
            </button>
          ))}
        </div>
      </div>

      {/* 테이블 */}
      {loading ? (
        <div className="flex items-center justify-center py-20 text-[#8c8c8c] text-sm">
          <div className="w-5 h-5 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin mr-3" />
          로딩 중...
        </div>
      ) : items.length === 0 ? (
        <p className="text-sm text-[#5c5c5c] py-16 text-center">완료된 제안서가 없습니다.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[#8c8c8c] text-xs border-b border-[#262626]">
                <th className="pb-2 pr-4 font-medium">프로젝트명</th>
                <th className="pb-2 pr-4 font-medium">발주기관</th>
                <th className="pb-2 pr-4 font-medium">제출일</th>
                <th className="pb-2 pr-4 font-medium">결과</th>
                <th className="pb-2 pr-4 font-medium text-center">정성제안서</th>
                <th className="pb-2 pr-4 font-medium text-center">발표자료</th>
                <th className="pb-2 font-medium text-center">가격제안서</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const badge = WIN_BADGE[item.win_result ?? ""] ?? null;
                return (
                  <tr
                    key={item.id}
                    className="border-b border-[#1c1c1c] hover:bg-[#1a1a1a] transition-colors"
                  >
                    <td className="py-3 pr-4">
                      <button
                        onClick={() => router.push(`/proposals/${item.id}`)}
                        className="text-[#ededed] hover:text-[#3ecf8e] text-left font-medium transition-colors"
                      >
                        {item.title}
                      </button>
                    </td>
                    <td className="py-3 pr-4 text-[#8c8c8c]">{item.client_name ?? "-"}</td>
                    <td className="py-3 pr-4 text-[#8c8c8c] whitespace-nowrap">{formatDate(item.deadline)}</td>
                    <td className="py-3 pr-4">
                      {badge ? (
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium ${badge.cls}`}>
                          {badge.label}
                        </span>
                      ) : (
                        <span className="text-[#5c5c5c] text-xs">-</span>
                      )}
                    </td>
                    <td className="py-3 pr-4 text-center">
                      <DownloadLink href={`${BASE}/proposals/${item.id}/download/docx`} label="DOCX" />
                    </td>
                    <td className="py-3 pr-4 text-center">
                      <DownloadLink href={`${BASE}/proposals/${item.id}/download/pptx`} label="PPT" />
                    </td>
                    <td className="py-3 text-center">
                      <DownloadLink href={`${BASE}/proposals/${item.id}/download/cost-sheet`} label="가격" />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="px-3 py-1.5 text-xs rounded-lg bg-[#1c1c1c] border border-[#262626] text-[#8c8c8c] hover:text-[#ededed] disabled:opacity-30"
          >
            이전
          </button>
          <span className="text-xs text-[#8c8c8c]">{page} / {totalPages}</span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="px-3 py-1.5 text-xs rounded-lg bg-[#1c1c1c] border border-[#262626] text-[#8c8c8c] hover:text-[#ededed] disabled:opacity-30"
          >
            다음
          </button>
        </div>
      )}
    </div>
  );
}

function DownloadLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-medium rounded-md bg-[#1c1c1c] border border-[#262626] text-[#8c8c8c] hover:text-[#3ecf8e] hover:border-[#3ecf8e]/30 transition-colors"
    >
      <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="7 10 12 15 17 10" />
        <line x1="12" y1="15" x2="12" y2="3" />
      </svg>
      {label}
    </a>
  );
}

// ══════════════════════════════════════════════════════════
// KB 텍스트 검색 탭
// ══════════════════════════════════════════════════════════

function KbHealthWidget() {
  const [health, setHealth] = useState<KbHealthResponse | null>(null);
  const [reindexing, setReindexing] = useState(false);

  useEffect(() => {
    api.kb.health().then(setHealth).catch(() => {});
  }, []);

  async function handleReindex(areas: string[]) {
    setReindexing(true);
    try {
      await api.kb.reindex(areas);
      const h = await api.kb.health();
      setHealth(h);
    } catch {}
    finally { setReindexing(false); }
  }

  if (!health) return null;

  const areaLabels: Record<string, string> = {
    content: "콘텐츠", client: "발주기관", competitor: "경쟁사",
    lesson: "교훈", capability: "역량", qa: "Q&A",
  };
  const lowCoverageAreas = Object.entries(health)
    .filter(([, v]) => v.total > 0 && v.coverage < 90)
    .map(([k]) => k);

  return (
    <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-[#ededed]">KB 건강도</h3>
        {lowCoverageAreas.length > 0 && (
          <button
            onClick={() => handleReindex(lowCoverageAreas)}
            disabled={reindexing}
            className="text-[10px] px-2 py-1 rounded bg-[#3ecf8e]/15 text-[#3ecf8e] hover:bg-[#3ecf8e]/25 disabled:opacity-50"
          >
            {reindexing ? "인덱싱 중..." : `재인덱싱 (${lowCoverageAreas.length}개 영역)`}
          </button>
        )}
      </div>
      <div className="grid grid-cols-3 gap-2">
        {Object.entries(health).map(([area, data]) => (
          <div key={area} className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[#8c8c8c]">{areaLabels[area] || area}</span>
              <span className="text-[10px] text-[#ededed]">{data.total}건</span>
            </div>
            <div className="h-1.5 bg-[#262626] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${data.coverage >= 90 ? "bg-[#3ecf8e]" : data.coverage >= 50 ? "bg-amber-500" : "bg-red-500"}`}
                style={{ width: `${Math.min(data.coverage, 100)}%` }}
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[#5c5c5c]">{data.coverage}%</span>
              {data.avg_quality !== undefined && (
                <span className="text-[10px] text-[#8c8c8c]">품질 {data.avg_quality}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


function KbSearchView() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [areas, setAreas] = useState<string[]>([]);
  const [result, setResult] = useState<KbSearchResult | null>(null);
  const [loading, setLoading] = useState(false);

  function toggleArea(area: string) {
    setAreas((prev) => prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area]);
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const areasStr = areas.length > 0 ? areas.join(",") : undefined;
      const res = await api.kb.search(query, areasStr, 10);
      setResult(res);
    } catch { setResult(null); }
    finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      {/* KB 건강도 위젯 (D-4) */}
      <KbHealthWidget />

      {/* 검색 폼 */}
      <form onSubmit={handleSearch} className="space-y-3">
        <div className="flex gap-2">
          <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="검색어 입력 (시맨틱 + 키워드 하이브리드)"
            className="flex-1 bg-[#1c1c1c] border border-[#262626] rounded-xl px-4 py-3 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-2 focus:ring-[#3ecf8e]/40" />
          <button type="submit" disabled={loading || !query.trim()}
            className="px-5 py-3 rounded-xl bg-[#3ecf8e] text-[#0f0f0f] text-sm font-semibold hover:bg-[#3ecf8e]/90 disabled:opacity-50 transition-colors shrink-0">
            {loading ? "검색 중..." : "검색"}
          </button>
        </div>

        {/* 영역 필터 */}
        <div className="flex gap-2">
          <span className="text-xs text-[#5c5c5c] self-center">영역:</span>
          {KB_AREA_OPTS.map((a) => (
            <button key={a.value} type="button" onClick={() => toggleArea(a.value)}
              className={`px-3 py-1 text-xs rounded-lg transition-colors ${areas.includes(a.value) ? "bg-[#3ecf8e]/15 text-[#3ecf8e] border border-[#3ecf8e]/30" : "bg-[#1c1c1c] text-[#8c8c8c] border border-[#262626]"}`}>
              {a.label}
            </button>
          ))}
          {areas.length > 0 && (
            <button type="button" onClick={() => setAreas([])} className="text-[10px] text-[#5c5c5c] hover:text-[#8c8c8c]">초기화</button>
          )}
        </div>
      </form>

      {/* 결과 */}
      {result && (
        <div className="space-y-4">
          <p className="text-xs text-[#8c8c8c]">
            &quot;{result.query}&quot; 검색 결과: <span className="text-[#ededed] font-medium">{result.total}건</span>
          </p>

          {Object.entries(result.results).map(([area, items]) => {
            if (!items || items.length === 0) return null;
            const areaLabel = KB_AREA_OPTS.find((a) => a.value === area)?.label ?? area;
            return (
              <div key={area}>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-semibold text-[#ededed]">{areaLabel} ({items.length})</h3>
                  <button onClick={() => router.push(KB_AREA_ROUTE[area] ?? "/kb/content")} className="text-[10px] text-[#3ecf8e] hover:underline">전체 보기</button>
                </div>
                <div className="space-y-1.5">
                  {items.map((item, idx) => (
                    <div key={item.id ?? idx} className="bg-[#1c1c1c] border border-[#262626] rounded-xl px-4 py-3">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-[#ededed]">{item.title ?? item.id}</span>
                        {item.score != null && (
                          <span className="text-[10px] text-[#3ecf8e] bg-[#3ecf8e]/10 px-1.5 py-0.5 rounded">
                            {(item.score * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                      {item.summary && <p className="text-xs text-[#8c8c8c] line-clamp-2">{item.summary}</p>}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}

          {result.total === 0 && (
            <p className="text-sm text-[#5c5c5c] py-8 text-center">검색 결과가 없습니다.</p>
          )}
        </div>
      )}
    </div>
  );
}
