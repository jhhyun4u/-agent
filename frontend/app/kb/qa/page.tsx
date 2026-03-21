"use client";

/**
 * PSM-16: KB Q&A 검색 페이지
 *
 * 조직 전체 Q&A를 시맨틱 + 키워드 검색.
 * 카테고리 필터, 유사도 점수, 출처 프로젝트 표시.
 */

import { useState } from "react";
import { api, type QASearchResult } from "@/lib/api";

const CATEGORIES = [
  { value: "", label: "전체" },
  { value: "technical", label: "기술" },
  { value: "management", label: "관리" },
  { value: "pricing", label: "가격/예산" },
  { value: "experience", label: "수행실적" },
  { value: "team", label: "투입인력" },
  { value: "general", label: "일반" },
];

function categoryLabel(value: string) {
  return CATEGORIES.find((c) => c.value === value)?.label ?? value;
}

export default function KbQaSearchPage() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [results, setResults] = useState<QASearchResult[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const res = await api.qa.search(query.trim(), category || undefined, 20);
      setResults(res.data);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-[#ededed]">
      <header className="bg-[#111111] border-b border-[#262626] px-6 py-3">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-sm font-semibold">Q&A 지식 검색</h1>
          <p className="text-xs text-[#8c8c8c] mt-0.5">
            과거 발표 Q&A에서 유사한 질의응답을 검색합니다
          </p>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-6 space-y-5">
        {/* 검색 폼 */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="검색어 입력 (예: 보안 체계, 프로젝트 관리 방법론)"
            className="flex-1 bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#8c8c8c] focus:outline-none focus:ring-2 focus:ring-[#3ecf8e]/40 focus:border-[#3ecf8e]/50 transition-colors"
          />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="bg-[#1c1c1c] border border-[#262626] rounded-lg px-2.5 py-2 text-xs text-[#ededed] focus:outline-none focus:ring-2 focus:ring-[#3ecf8e]/40"
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="bg-[#3ecf8e] hover:bg-[#3ecf8e]/90 disabled:opacity-40 text-[#0f0f0f] text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
          >
            {loading ? "..." : "검색"}
          </button>
        </form>

        {/* 결과 */}
        {loading && (
          <div className="text-sm text-[#8c8c8c] text-center py-8">
            검색 중...
          </div>
        )}

        {!loading && searched && results.length === 0 && (
          <div className="text-sm text-[#8c8c8c] text-center py-8">
            검색 결과가 없습니다.
          </div>
        )}

        <div className="space-y-3">
          {results.map((qa) => (
            <div
              key={qa.id}
              className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4 space-y-2 hover:border-[#3ecf8e]/20 transition-colors"
            >
              {/* 유사도 */}
              {qa.similarity != null && (
                <div className="flex items-center gap-1.5">
                  <div className="h-1 flex-1 bg-[#262626] rounded-full overflow-hidden max-w-[80px]">
                    <div
                      className="h-full bg-[#3ecf8e] rounded-full"
                      style={{ width: `${Math.round(qa.similarity * 100)}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-[#3ecf8e] font-medium">
                    {Math.round(qa.similarity * 100)}%
                  </span>
                </div>
              )}

              {/* Q&A 내용 */}
              <p className="text-sm font-medium text-[#ededed]">
                Q: {qa.question}
              </p>
              <p className="text-sm text-[#8c8c8c] whitespace-pre-wrap line-clamp-3">
                A: {qa.answer}
              </p>

              {/* 메타 */}
              <div className="flex items-center gap-2 text-[10px] text-[#8c8c8c] flex-wrap">
                <span className="px-1.5 py-0.5 rounded bg-[#262626]">
                  {categoryLabel(qa.category)}
                </span>
                {qa.proposal_name && (
                  <span title={qa.proposal_name}>
                    {qa.proposal_name}
                  </span>
                )}
                {qa.client && (
                  <span className="text-[#5c5c5c]">{qa.client}</span>
                )}
                <span className="ml-auto">
                  {new Date(qa.created_at).toLocaleDateString("ko-KR")}
                </span>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
