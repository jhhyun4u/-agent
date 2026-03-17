"use client";

/**
 * 통합 KB 검색 (§13 KbSearchBar)
 * /kb/search
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import AppSidebar from "@/components/AppSidebar";
import { api, type KbSearchResult } from "@/lib/api";

const AREA_OPTS = [
  { value: "content", label: "콘텐츠" },
  { value: "client", label: "발주기관" },
  { value: "competitor", label: "경쟁사" },
  { value: "lesson", label: "교훈" },
  { value: "capability", label: "역량" },
];

export default function KbSearchPage() {
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

  const AREA_ROUTE: Record<string, string> = {
    content: "/kb/content",
    client: "/kb/clients",
    competitor: "/kb/competitors",
    lesson: "/kb/lessons",
    capability: "/kb/content",
  };

  return (
    <div className="flex h-screen bg-[#0f0f0f] overflow-hidden">
      <AppSidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 shrink-0">
          <h1 className="text-sm font-semibold text-[#ededed]">KB 통합 검색</h1>
        </header>

        <main className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
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
              {AREA_OPTS.map((a) => (
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
                const areaLabel = AREA_OPTS.find((a) => a.value === area)?.label ?? area;
                return (
                  <div key={area}>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-xs font-semibold text-[#ededed]">{areaLabel} ({items.length})</h3>
                      <button onClick={() => router.push(AREA_ROUTE[area] ?? "/kb/content")} className="text-[10px] text-[#3ecf8e] hover:underline">전체 보기</button>
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
        </main>
      </div>
    </div>
  );
}
