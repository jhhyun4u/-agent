"use client";

/**
 * 교훈 아카이브 (§13 LessonsLearned)
 * /kb/lessons
 */

import { useCallback, useEffect, useState } from "react";
import { api, type KbLesson, type KbLessonDetail } from "@/lib/api";

const RESULT_OPTS = [
  { value: "", label: "전체" },
  { value: "수주", label: "수주" },
  { value: "패찰", label: "패찰" },
  { value: "유찰", label: "유찰" },
];

const POS_OPTS = [
  { value: "", label: "전체" },
  { value: "defensive", label: "수성형" },
  { value: "offensive", label: "공격형" },
  { value: "adjacent", label: "인접형" },
];

const RESULT_BADGE: Record<string, string> = {
  "수주": "bg-[#3ecf8e]/15 text-[#3ecf8e]",
  "패찰": "bg-red-500/15 text-red-400",
  "유찰": "bg-amber-500/15 text-amber-400",
};

export default function LessonsPage() {
  const [items, setItems] = useState<KbLesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterResult, setFilterResult] = useState("");
  const [filterPos, setFilterPos] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [detail, setDetail] = useState<KbLessonDetail | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filterResult) params.result = filterResult;
      if (filterPos) params.positioning = filterPos;
      const res = await api.kb.lessons.list(params);
      setItems(res.data);
    } catch { setItems([]); }
    finally { setLoading(false); }
  }, [filterResult, filterPos]);

  useEffect(() => { load(); }, [load]);

  async function toggleDetail(id: string) {
    if (expanded === id) {
      setExpanded(null);
      setDetail(null);
      return;
    }
    setExpanded(id);
    try {
      const d = await api.kb.lessons.get(id);
      setDetail(d);
    } catch { setDetail(null); }
  }

  return (
    <>
        <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 shrink-0">
          <h1 className="text-sm font-semibold text-[#ededed]">교훈 아카이브</h1>
        </header>

        <main className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
          {/* 필터 */}
          <div className="flex gap-2 flex-wrap">
            {RESULT_OPTS.map((r) => (
              <button key={r.value} onClick={() => setFilterResult(r.value)}
                className={`px-3 py-1 text-xs rounded-lg transition-colors ${filterResult === r.value ? "bg-[#3ecf8e] text-[#0f0f0f] font-semibold" : "bg-[#1c1c1c] text-[#8c8c8c] border border-[#262626]"}`}>
                {r.label}
              </button>
            ))}
            <div className="w-px bg-[#262626] mx-1" />
            {POS_OPTS.map((p) => (
              <button key={p.value} onClick={() => setFilterPos(p.value)}
                className={`px-3 py-1 text-xs rounded-lg transition-colors ${filterPos === p.value ? "bg-[#262626] text-[#ededed] font-semibold" : "text-[#5c5c5c] hover:text-[#8c8c8c]"}`}>
                {p.label}
              </button>
            ))}
          </div>

          {/* 목록 */}
          {loading ? (
            <p className="text-sm text-[#8c8c8c] py-8 text-center">로딩 중...</p>
          ) : items.length === 0 ? (
            <p className="text-sm text-[#5c5c5c] py-8 text-center">등록된 교훈이 없습니다.</p>
          ) : (
            <div className="space-y-2">
              {items.map((item) => (
                <div key={item.id} className="bg-[#1c1c1c] border border-[#262626] rounded-xl overflow-hidden">
                  <button onClick={() => toggleDetail(item.id)} className="w-full px-4 py-3 flex items-center gap-3 text-left hover:bg-[#262626]/30 transition-colors">
                    <svg className={`w-3 h-3 text-[#8c8c8c] shrink-0 transition-transform ${expanded === item.id ? "rotate-90" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-sm font-medium text-[#ededed] truncate">{item.strategy_summary || "교훈"}</span>
                        {item.result && <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${RESULT_BADGE[item.result] ?? "bg-[#262626] text-[#8c8c8c]"}`}>{item.result}</span>}
                        {item.positioning && <span className="text-[10px] text-[#5c5c5c]">{item.positioning}</span>}
                      </div>
                      <div className="flex gap-3 text-[10px] text-[#8c8c8c]">
                        {item.client_name && <span>{item.client_name}</span>}
                        {item.industry && <span>{item.industry}</span>}
                        {item.failure_category && <span>실패: {item.failure_category}</span>}
                        <span>{new Date(item.created_at).toLocaleDateString("ko-KR")}</span>
                      </div>
                    </div>
                  </button>

                  {expanded === item.id && detail && (
                    <div className="px-4 pb-4 pt-0 space-y-2 border-t border-[#262626]">
                      {detail.effective_points && (
                        <div className="pt-3">
                          <p className="text-[10px] text-[#3ecf8e] mb-1 uppercase tracking-wider font-medium">효과적이었던 점</p>
                          <p className="text-xs text-[#ededed] leading-relaxed">{detail.effective_points}</p>
                        </div>
                      )}
                      {detail.weak_points && (
                        <div>
                          <p className="text-[10px] text-amber-400 mb-1 uppercase tracking-wider font-medium">부족했던 점</p>
                          <p className="text-xs text-[#ededed] leading-relaxed">{detail.weak_points}</p>
                        </div>
                      )}
                      {detail.improvements && (
                        <div>
                          <p className="text-[10px] text-blue-400 mb-1 uppercase tracking-wider font-medium">개선 사항</p>
                          <p className="text-xs text-[#ededed] leading-relaxed">{detail.improvements}</p>
                        </div>
                      )}
                      {detail.failure_detail && (
                        <div>
                          <p className="text-[10px] text-red-400 mb-1 uppercase tracking-wider font-medium">실패 상세</p>
                          <p className="text-xs text-[#ededed] leading-relaxed">{detail.failure_detail}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </main>
    </>
  );
}
