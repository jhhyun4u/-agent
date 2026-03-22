"use client";

/**
 * 권고 #5: KB ↔ 제안서 양방향 링크
 *
 * KB 콘텐츠가 어떤 제안서에서 참조되었는지 사용 이력을 표시한다.
 * kb/content 페이지에서 각 콘텐츠 항목에 추가.
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

interface UsageRecord {
  proposal_id: string;
  proposal_title: string;
  section_title: string;
  used_at: string;
  status: string;
  win_result: string | null;
}

interface Props {
  contentId: string;
  contentTitle: string;
}

export default function KbUsageHistory({ contentId, contentTitle }: Props) {
  const [usages, setUsages] = useState<UsageRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open || !contentId) return;

    setLoading(true);
    // KB 검색으로 이 콘텐츠를 사용한 제안서를 검색
    api.kb.search(contentTitle, undefined, 20)
      .then((res) => {
        const results = ((res as unknown as { items?: Array<{ proposal_id?: string; proposal_title?: string; section_title?: string; updated_at?: string; status?: string; win_result?: string | null }> })?.items ?? []) as Array<{ proposal_id?: string; proposal_title?: string; section_title?: string; updated_at?: string; status?: string; win_result?: string | null }>;
        setUsages(
          results
            .filter((r) => r.proposal_id)
            .map((r) => ({
              proposal_id: r.proposal_id!,
              proposal_title: r.proposal_title ?? "제목 없음",
              section_title: r.section_title ?? "",
              used_at: r.updated_at ?? "",
              status: r.status ?? "unknown",
              win_result: r.win_result ?? null,
            }))
        );
      })
      .catch(() => setUsages([]))
      .finally(() => setLoading(false));
  }, [open, contentId, contentTitle]);

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-[10px] text-[#8c8c8c] hover:text-[#3ecf8e] transition-colors"
      >
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
        {open ? "사용 이력 접기" : "사용 이력 보기"}
      </button>

      {open && (
        <div className="mt-2 bg-[#111111] border border-[#262626] rounded-lg p-3">
          {loading ? (
            <p className="text-[10px] text-[#8c8c8c]">검색 중...</p>
          ) : usages.length === 0 ? (
            <p className="text-[10px] text-[#8c8c8c]">이 콘텐츠를 참조한 제안서가 없습니다.</p>
          ) : (
            <div className="space-y-1.5">
              <p className="text-[10px] text-[#8c8c8c] mb-2">
                {usages.length}건의 제안서에서 사용됨
              </p>
              {usages.map((u) => (
                <Link
                  key={`${u.proposal_id}-${u.section_title}`}
                  href={`/proposals/${u.proposal_id}`}
                  className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-[#1c1c1c] transition-colors group"
                >
                  {/* 수주 결과 */}
                  <span className={`text-[9px] font-bold shrink-0 w-5 text-center ${
                    u.win_result === "won" ? "text-[#3ecf8e]" :
                    u.win_result === "lost" ? "text-red-400" :
                    "text-[#8c8c8c]"
                  }`}>
                    {u.win_result === "won" ? "W" : u.win_result === "lost" ? "L" : "-"}
                  </span>

                  {/* 제안서 제목 */}
                  <span className="text-[10px] text-[#ededed] group-hover:text-[#3ecf8e] truncate flex-1 transition-colors">
                    {u.proposal_title}
                  </span>

                  {/* 사용 섹션 */}
                  {u.section_title && (
                    <span className="text-[9px] text-[#8c8c8c] shrink-0 truncate max-w-[120px]">
                      {u.section_title}
                    </span>
                  )}

                  {/* 날짜 */}
                  {u.used_at && (
                    <span className="text-[9px] text-[#8c8c8c] shrink-0">
                      {new Date(u.used_at).toLocaleDateString("ko-KR", { month: "numeric", day: "numeric" })}
                    </span>
                  )}
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
