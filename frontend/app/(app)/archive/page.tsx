"use client";

/**
 * 아카이브 페이지 — 완료된 제안서 조회
 * - 스코프: 전체 / 우리 팀 / 나의
 * - 수주결과 필터: 전체 / 수주 / 낙찰실패 / 대기
 * - 페이지네이션
 */

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ArchiveItem } from "@/lib/api";

// ── 상수 ──────────────────────────────────────────────────────────────

const SCOPE_TABS = [
  { value: "company", label: "전체" },
  { value: "team", label: "우리 팀" },
  { value: "personal", label: "나의" },
];

const WIN_RESULT_FILTERS = [
  { value: "", label: "전체" },
  { value: "won", label: "수주" },
  { value: "lost", label: "낙찰실패" },
  { value: "pending", label: "대기" },
];

// ── 유틸 ──────────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  try {
    return new Date(iso).toISOString().slice(0, 10);
  } catch {
    return "-";
  }
}

function WinResultBadge({ value }: { value: string | null }) {
  if (value === "won") {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-[#3ecf8e]/15 text-[#3ecf8e]">
        수주
      </span>
    );
  }
  if (value === "lost") {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-red-500/15 text-red-400">
        낙찰실패
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-[#262626] text-[#8c8c8c]">
      {value === "pending" ? "대기" : "-"}
    </span>
  );
}

// ── 페이지 컴포넌트 ───────────────────────────────────────────────────

export default function ArchivePage() {
  const router = useRouter();
  const [items, setItems] = useState<ArchiveItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [scope, setScope] = useState("company");
  const [winResult, setWinResult] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const loadItems = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.archive.list({
        scope,
        win_result: winResult || undefined,
        page,
      });
      setItems(res.data);
      setTotalPages(res.meta?.pages ?? 1);
      setTotal(res.meta?.total ?? 0);
    } catch (e) {
      setError(e instanceof Error ? e.message : "목록 로드 실패");
    } finally {
      setLoading(false);
    }
  }, [scope, winResult, page]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  // 필터 변경 시 첫 페이지로 리셋
  function changeScope(v: string) {
    setScope(v);
    setPage(1);
  }

  function changeWinResult(v: string) {
    setWinResult(v);
    setPage(1);
  }

  return (
    <>
        {/* 헤더 */}
        <header className="border-b border-[#262626] px-6 py-4 bg-[#111111] shrink-0">
          <h1 className="text-base font-semibold text-[#ededed]">아카이브</h1>
        </header>

        {/* 필터 바 */}
        <div className="border-b border-[#262626] px-6 py-3 bg-[#111111] shrink-0 flex items-center gap-4 flex-wrap">
          {/* 스코프 탭 */}
          <div className="flex border border-[#262626] rounded-md overflow-hidden">
            {SCOPE_TABS.map((t) => (
              <button
                key={t.value}
                onClick={() => changeScope(t.value)}
                className={`px-3 py-1.5 text-xs transition-colors ${
                  scope === t.value
                    ? "bg-[#1c1c1c] text-[#ededed]"
                    : "text-[#8c8c8c] hover:text-[#ededed]"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* 수주결과 필터 */}
          <div className="flex gap-1.5">
            {WIN_RESULT_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => changeWinResult(f.value)}
                className={`px-3 py-1.5 text-xs rounded-md border transition-colors ${
                  winResult === f.value
                    ? "bg-[#1c1c1c] border-[#3c3c3c] text-[#ededed]"
                    : "border-[#262626] text-[#8c8c8c] hover:border-[#3c3c3c] hover:text-[#ededed]"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* 테이블 영역 */}
        <div className="flex-1 overflow-y-auto">
          {error && (
            <div className="mx-6 mt-4 bg-red-400/10 border border-red-400/20 rounded-md px-4 py-3">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          <div className="px-6 py-4">
            {/* 테이블 */}
            <div className="border border-[#262626] rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#262626] bg-[#111111]">
                    <th className="text-left px-4 py-3 text-xs font-medium text-[#8c8c8c] w-full">
                      제목
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-[#8c8c8c] whitespace-nowrap">
                      날짜
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-[#8c8c8c] whitespace-nowrap">
                      결과
                    </th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-[#8c8c8c] whitespace-nowrap">
                      단계
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    [...Array(5)].map((_, i) => (
                      <tr key={i} className="border-b border-[#262626]">
                        <td colSpan={4} className="px-4 py-3">
                          <div className="h-4 bg-[#1c1c1c] rounded animate-pulse" />
                        </td>
                      </tr>
                    ))
                  ) : items.length === 0 ? (
                    <tr>
                      <td
                        colSpan={4}
                        className="px-4 py-16 text-center text-sm text-[#5c5c5c]"
                      >
                        완료된 제안서가 없습니다
                      </td>
                    </tr>
                  ) : (
                    items.map((item) => (
                      <tr
                        key={item.id}
                        onClick={() => router.push(`/proposals/${item.id}`)}
                        className="border-b border-[#262626] last:border-0 hover:bg-[#1c1c1c] cursor-pointer transition-colors"
                      >
                        <td className="px-4 py-3 text-[#ededed] font-medium">
                          <span className="truncate block max-w-xs">
                            {item.title}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-[#8c8c8c] whitespace-nowrap text-xs">
                          {formatDate(item.updated_at)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <WinResultBadge value={item.win_result} />
                        </td>
                        <td className="px-4 py-3 text-[#8c8c8c] whitespace-nowrap text-xs">
                          {item.current_phase ?? "-"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* 페이지네이션 */}
            {!loading && total > 0 && (
              <div className="flex items-center justify-between mt-4">
                <p className="text-xs text-[#5c5c5c]">
                  총 {total}개
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="px-3 py-1.5 text-xs border border-[#262626] rounded-md text-[#8c8c8c] hover:text-[#ededed] hover:border-[#3c3c3c] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    이전
                  </button>
                  <span className="text-xs text-[#8c8c8c]">
                    {page} / {totalPages}
                  </span>
                  <button
                    onClick={() =>
                      setPage((p) => Math.min(totalPages, p + 1))
                    }
                    disabled={page >= totalPages}
                    className="px-3 py-1.5 text-xs border border-[#262626] rounded-md text-[#8c8c8c] hover:text-[#ededed] hover:border-[#3c3c3c] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    다음
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
    </>
  );
}
