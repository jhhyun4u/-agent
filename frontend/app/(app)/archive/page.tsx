"use client";

/**
 * 종료 프로젝트(아카이브) 페이지 — 완료된 제안서 조회
 * - 11개 컬럼 테이블: 연도, 과제명, 키워드, 발주처, 결과, 작업시간, 토큰비용, 팀, 참여자, 낙찰가, 낙찰율
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

// ── 포맷팅 함수 ────────────────────────────────────────────────────────

function extractYear(iso: string): string {
  try {
    return new Date(iso).getFullYear().toString();
  } catch {
    return "-";
  }
}

function formatCurrency(value: number | null | undefined): string {
  if (!value || value <= 0) return "-";
  const billion = value / 1000000000;
  if (billion >= 1) {
    return `${(billion * 10).toFixed(0) === (Math.round(billion * 10) * 10).toString() ? Math.round(billion * 10) / 10 : billion.toFixed(1)}억원`;
  }
  return `-`;
}

function formatElapsedTime(seconds: number | null | undefined): string {
  if (!seconds || seconds <= 0) return "-";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m`;
  return `-`;
}

function formatTokenCost(cost: number | null | undefined): string {
  if (cost === null || cost === undefined || cost <= 0) return "-";
  return `$${cost.toFixed(2)}`;
}

function formatWinRate(bid: number | null | undefined, budget: number | null | undefined): string {
  if (!bid || !budget || budget <= 0) return "-";
  const rate = (bid / budget) * 100;
  return `${Math.round(rate)}%`;
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

// ── 페이지 컴포넌트 ────────────────────────────────────────────────────

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
        <h1 className="text-base font-semibold text-[#ededed]">종료 프로젝트</h1>
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
          <div className="border border-[#262626] rounded-xl overflow-hidden overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-[#262626] bg-[#111111]">
                  <th className="text-center px-3 py-3 text-xs font-medium text-[#8c8c8c] whitespace-nowrap w-16">
                    연도
                  </th>
                  <th className="text-left px-3 py-3 text-xs font-medium text-[#8c8c8c] whitespace-nowrap min-w-[180px]">
                    과제명
                  </th>
                  <th className="text-left px-3 py-3 text-xs font-medium text-[#8c8c8c] whitespace-nowrap min-w-[80px]">
                    키워드
                  </th>
                  <th className="text-left px-3 py-3 text-xs font-medium text-[#8c8c8c] whitespace-nowrap min-w-[80px]">
                    발주처
                  </th>
                  <th className="text-center px-3 py-3 text-xs font-medium text-[#8c8c8c] whitespace-nowrap w-16">
                    결과
                  </th>
                  <th className="text-right px-3 py-3 text-xs font-medium text-[#8c8c8c] whitespace-nowrap w-20">
                    작업시간
                  </th>
                  <th className="text-right px-3 py-3 text-xs font-medium text-[#8c8c8c] whitespace-nowrap w-20">
                    토큰비용
                  </th>
                  <th className="text-left px-3 py-3 text-xs font-medium text-[#8c8c8c] whitespace-nowrap min-w-[80px]">
                    팀
                  </th>
                  <th className="text-left px-3 py-3 text-xs font-medium text-[#8c8c8c] whitespace-nowrap min-w-[120px]">
                    참여자
                  </th>
                  <th className="text-right px-3 py-3 text-xs font-medium text-[#8c8c8c] whitespace-nowrap w-24">
                    낙찰가
                  </th>
                  <th className="text-center px-3 py-3 text-xs font-medium text-[#8c8c8c] whitespace-nowrap w-16">
                    낙찰율
                  </th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  [...Array(5)].map((_, i) => (
                    <tr key={i} className="border-b border-[#262626]">
                      <td colSpan={11} className="px-3 py-3">
                        <div className="h-4 bg-[#1c1c1c] rounded animate-pulse" />
                      </td>
                    </tr>
                  ))
                ) : items.length === 0 ? (
                  <tr>
                    <td
                      colSpan={11}
                      className="px-3 py-16 text-center text-sm text-[#5c5c5c]"
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
                      <td className="text-center px-3 py-3 text-[#8c8c8c] text-xs whitespace-nowrap">
                        {extractYear(item.created_at)}
                      </td>
                      <td className="px-3 py-3 text-[#ededed] font-medium truncate">
                        {item.title}
                      </td>
                      <td className="px-3 py-3 text-[#8c8c8c] text-xs truncate">
                        {item.positioning || "-"}
                      </td>
                      <td className="px-3 py-3 text-[#8c8c8c] text-xs truncate">
                        {item.client_name || "-"}
                      </td>
                      <td className="px-3 py-3 text-center">
                        <WinResultBadge value={item.win_result} />
                      </td>
                      <td className="text-right px-3 py-3 text-[#8c8c8c] text-xs whitespace-nowrap">
                        {formatElapsedTime(item.elapsed_seconds)}
                      </td>
                      <td className="text-right px-3 py-3 text-[#8c8c8c] text-xs whitespace-nowrap">
                        {formatTokenCost(item.total_token_cost)}
                      </td>
                      <td className="px-3 py-3 text-[#8c8c8c] text-xs truncate">
                        {item.team_name || "-"}
                      </td>
                      <td className="px-3 py-3 text-[#8c8c8c] text-xs truncate">
                        {item.participants?.join(", ") || "-"}
                      </td>
                      <td className="text-right px-3 py-3 text-[#8c8c8c] text-xs whitespace-nowrap">
                        {formatCurrency(item.bid_amount)}
                      </td>
                      <td className="text-center px-3 py-3 text-[#8c8c8c] text-xs whitespace-nowrap">
                        {formatWinRate(item.bid_amount, item.budget)}
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
              <p className="text-xs text-[#5c5c5c]">총 {total}개</p>
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
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
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
