"use client";

/**
 * SectionLibraryPanel — 성공 섹션 라이브러리 패널
 *
 * 현재 섹션 제목과 유형을 기준으로 수주 제안서의 유사 섹션을 자동 추천.
 * 학술연구용역 특화: TRACK_RECORD(수행실적) 섹션 우선 노출.
 */

import { useCallback, useEffect, useState } from "react";
import { sectionLibraryApi, type WinningSection } from "@/lib/api";

interface Props {
  sectionTitle: string;          // 현재 편집 중인 섹션 제목
  sectionCategory?: string;      // TRACK_RECORD | METHODOLOGY | PERSONNEL 등
  studyType?: string;            // 정책연구 | 기초조사 등 (RFP에서 감지)
  onInsert: (content: string) => void;
}

const CATEGORY_LABEL: Record<string, string> = {
  TRACK_RECORD: "수행실적",
  METHODOLOGY:  "연구방법",
  PERSONNEL:    "연구팀",
  UNDERSTAND:   "사업이해",
  MANAGEMENT:   "추진체계",
  STRATEGY:     "추진전략",
  ADDED_VALUE:  "기대효과",
  기타:          "기타",
};

const QUALITY_COLOR = (score: number | null) => {
  if (!score) return "text-[#5c5c5c]";
  if (score >= 75) return "text-[#3ecf8e]";
  if (score >= 55) return "text-amber-400";
  return "text-red-400";
};

export default function SectionLibraryPanel({
  sectionTitle,
  sectionCategory,
  studyType,
  onInsert,
}: Props) {
  const [results, setResults] = useState<WinningSection[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [insertingId, setInsertingId] = useState<string | null>(null);
  const [query, setQuery] = useState(sectionTitle);

  const search = useCallback(async (title: string) => {
    if (!title.trim()) return;
    setLoading(true);
    try {
      const res = await sectionLibraryApi.recommend({
        section_title: title,
        section_category: sectionCategory,
        study_type: studyType,
        top_k: 5,
      });
      setResults(res.data ?? []);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [sectionCategory, studyType]);

  // 섹션 제목 변경 시 자동 검색 (디바운스 800ms)
  useEffect(() => {
    setQuery(sectionTitle);
  }, [sectionTitle]);

  useEffect(() => {
    const t = setTimeout(() => { if (query) search(query); }, 800);
    return () => clearTimeout(t);
  }, [query, search]);

  async function handleInsert(item: WinningSection) {
    setInsertingId(item.id);
    try {
      const res = await sectionLibraryApi.getContent(item.id);
      onInsert(res.data?.body ?? "");
    } catch {
      // silent
    } finally {
      setInsertingId(null);
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* 검색바 */}
      <div className="px-3 py-2.5 border-b border-[#262626]">
        <div className="flex items-center gap-2 bg-[#111111] border border-[#262626] rounded-lg px-2 py-1.5">
          <svg className="w-3 h-3 text-[#5c5c5c] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && search(query)}
            placeholder="섹션 제목 검색..."
            className="flex-1 bg-transparent text-xs text-[#ededed] placeholder-[#5c5c5c] outline-none"
          />
          {loading && (
            <div className="w-3 h-3 border border-[#3ecf8e]/30 border-t-[#3ecf8e] rounded-full animate-spin shrink-0" />
          )}
        </div>
        {/* 필터 태그 */}
        <div className="flex gap-1 mt-1.5 flex-wrap">
          {studyType && (
            <span className="text-[9px] bg-blue-500/15 text-blue-400 px-1.5 py-0.5 rounded-full">
              {studyType}
            </span>
          )}
          {sectionCategory && CATEGORY_LABEL[sectionCategory] && (
            <span className="text-[9px] bg-[#3ecf8e]/10 text-[#3ecf8e] px-1.5 py-0.5 rounded-full">
              {CATEGORY_LABEL[sectionCategory]}
            </span>
          )}
        </div>
      </div>

      {/* 결과 목록 */}
      <div className="flex-1 overflow-y-auto">
        {results.length === 0 && !loading && (
          <div className="px-3 py-6 text-center">
            <p className="text-[10px] text-[#5c5c5c]">
              {query ? "관련 수주 섹션이 없습니다." : "섹션 제목을 입력하세요."}
            </p>
            <p className="text-[9px] text-[#3c3c3c] mt-1">
              수주 결과를 등록하면 자동으로 축적됩니다.
            </p>
          </div>
        )}

        <div className="divide-y divide-[#1e1e1e]">
          {results.map((item) => (
            <div key={item.id} className="px-3 py-2.5">
              {/* 헤더 */}
              <div className="flex items-start gap-1.5 mb-1">
                {/* 수주 배지 */}
                {item.is_winning && (
                  <span className="shrink-0 text-[8px] font-bold text-[#3ecf8e] bg-[#3ecf8e]/10 px-1 py-0.5 rounded mt-0.5">
                    수주
                  </span>
                )}
                <p className="text-xs font-medium text-[#ededed] leading-tight flex-1">
                  {item.title}
                </p>
              </div>

              {/* 메타 */}
              <div className="flex items-center gap-2 mb-1.5">
                {item.section_category && (
                  <span className="text-[9px] text-[#5c5c5c]">
                    {CATEGORY_LABEL[item.section_category] ?? item.section_category}
                  </span>
                )}
                {item.client_type && (
                  <span className="text-[9px] text-[#5c5c5c]">· {item.client_type}</span>
                )}
                {item.quality_score != null && (
                  <span className={`text-[9px] font-bold ml-auto ${QUALITY_COLOR(item.quality_score)}`}>
                    {Math.round(item.quality_score)}점
                  </span>
                )}
              </div>

              {/* 미리보기 */}
              <p className="text-[10px] text-[#8c8c8c] leading-relaxed line-clamp-2 mb-2">
                {item.preview}
              </p>

              {/* 액션 */}
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                  className="text-[9px] text-[#5c5c5c] hover:text-[#ededed] transition-colors"
                >
                  {expandedId === item.id ? "접기" : "더보기"}
                </button>
                <button
                  onClick={() => handleInsert(item)}
                  disabled={insertingId === item.id}
                  className="ml-auto text-[10px] font-semibold px-2.5 py-1 rounded-lg bg-[#3ecf8e]/15 text-[#3ecf8e] hover:bg-[#3ecf8e]/25 transition-colors disabled:opacity-50"
                >
                  {insertingId === item.id ? "로딩..." : "삽입 →"}
                </button>
              </div>

              {/* 확장 미리보기 */}
              {expandedId === item.id && (
                <div className="mt-2 p-2 bg-[#111111] rounded-lg border border-[#262626]">
                  <p className="text-[10px] text-[#8c8c8c] leading-relaxed whitespace-pre-wrap">
                    {item.preview}
                    {item.preview.length >= 200 && "…"}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 하단 안내 */}
      <div className="px-3 py-2 border-t border-[#262626] text-center">
        <p className="text-[9px] text-[#3c3c3c]">
          수주 완료 제안서의 섹션이 자동 축적됩니다
        </p>
      </div>
    </div>
  );
}
