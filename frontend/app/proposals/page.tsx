"use client";

/**
 * F3: 제안서 목록 페이지
 * - 검색 (?q=), 상태 필터, 페이지네이션
 * - 제안서 0개일 때 EmptyState
 */

import { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, ProposalSummary } from "@/lib/api";

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  initialized: { label: "대기",    color: "bg-[#1c1c1c] text-[#8c8c8c] border border-[#262626]" },
  processing:  { label: "생성 중", color: "bg-blue-950/60 text-blue-400 border border-blue-900" },
  running:     { label: "생성 중", color: "bg-blue-950/60 text-blue-400 border border-blue-900" },
  completed:   { label: "완료",    color: "bg-emerald-950/60 text-emerald-400 border border-emerald-900" },
  failed:      { label: "실패",    color: "bg-red-950/60 text-red-400 border border-red-900" },
};

const WIN_LABELS: Record<string, string> = {
  won: "수주", lost: "낙찰 실패", pending: "결과 대기",
};

export default function ProposalsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [proposals, setProposals] = useState<ProposalSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState(searchParams.get("q") ?? "");
  const [status, setStatus] = useState(searchParams.get("status") ?? "");
  const [page, setPage] = useState(1);

  const fetchProposals = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.proposals.list({ q: q || undefined, status: status || undefined, page });
      setProposals(res.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [q, status, page]);

  useEffect(() => {
    fetchProposals();
  }, [fetchProposals]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    fetchProposals();
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#0f0f0f]">
      {/* 페이지 헤더 */}
      <div className="border-b border-[#262626] px-6 py-4 shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-sm font-semibold text-[#ededed]">제안서</h1>
            <p className="text-xs text-[#8c8c8c] mt-0.5">AI가 생성한 제안서 목록</p>
          </div>
          <Link
            href="/proposals/new"
            className="bg-[#3ecf8e] hover:bg-[#49e59e] text-black font-semibold rounded-lg px-4 py-2 text-xs transition-colors"
          >
            + 새 제안서
          </Link>
        </div>
      </div>

      {/* 검색 + 필터 */}
      <div className="border-b border-[#262626] px-6 py-3 shrink-0">
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="제안서 제목 검색..."
            className="flex-1 bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-1.5 text-sm text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] focus:border-[#3ecf8e] transition-colors"
          />
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            className="bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-1.5 text-sm text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] focus:border-[#3ecf8e] transition-colors"
          >
            <option value="">전체 상태</option>
            <option value="initialized">대기</option>
            <option value="processing">생성 중</option>
            <option value="completed">완료</option>
            <option value="failed">실패</option>
          </select>
          <button
            type="submit"
            className="bg-[#1c1c1c] hover:bg-[#262626] border border-[#262626] text-[#ededed] rounded-lg px-4 py-1.5 text-sm font-medium transition-colors"
          >
            검색
          </button>
        </form>
      </div>

      {/* 목록 */}
      <div className="flex-1 overflow-auto px-6 py-4">
        {loading ? (
          <div className="flex items-center justify-center h-40">
            <div className="text-sm text-[#5c5c5c]">불러오는 중...</div>
          </div>
        ) : proposals.length === 0 ? (
          <EmptyState q={q} />
        ) : (
          <>
            <div className="rounded-lg border border-[#262626] bg-[#111111] overflow-hidden">
              {/* 테이블 헤더 */}
              <div className="grid grid-cols-[1fr_120px_100px] gap-4 px-4 py-2.5 border-b border-[#262626] bg-[#0f0f0f]">
                <span className="text-xs font-medium text-[#5c5c5c] uppercase tracking-wider">제안서명</span>
                <span className="text-xs font-medium text-[#5c5c5c] uppercase tracking-wider">날짜</span>
                <span className="text-xs font-medium text-[#5c5c5c] uppercase tracking-wider">상태</span>
              </div>
              {proposals.map((p) => (
                <Link
                  key={p.id}
                  href={`/proposals/${p.id}`}
                  className="grid grid-cols-[1fr_120px_100px] gap-4 px-4 py-3.5 border-b border-[#1a1a1a] last:border-0 hover:bg-[#161616] transition-colors items-center"
                >
                  <div className="min-w-0">
                    <p className="text-sm text-[#ededed] truncate font-medium">{p.title}</p>
                    {p.win_result && (
                      <p className="text-xs text-[#8c8c8c] mt-0.5">
                        {WIN_LABELS[p.win_result] ?? p.win_result}
                        {p.bid_amount ? ` · ${p.bid_amount.toLocaleString()}원` : ""}
                      </p>
                    )}
                  </div>
                  <span className="text-xs text-[#5c5c5c]">
                    {new Date(p.created_at).toLocaleDateString("ko-KR")}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-md font-medium ${STATUS_LABELS[p.status]?.color ?? "bg-[#1c1c1c] text-[#8c8c8c]"}`}>
                      {STATUS_LABELS[p.status]?.label ?? p.status}
                    </span>
                    {(p.status === "processing" || p.status === "running") && (
                      <span className="text-xs text-[#5c5c5c]">{p.phases_completed}/5</span>
                    )}
                  </div>
                </Link>
              ))}
            </div>

            {/* 페이지네이션 */}
            {proposals.length === 20 && (
              <div className="flex items-center justify-center gap-2 mt-4">
                <button
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="px-3 py-1.5 text-xs border border-[#262626] rounded-lg text-[#8c8c8c] disabled:opacity-40 hover:bg-[#1c1c1c] hover:text-[#ededed] transition-colors"
                >
                  이전
                </button>
                <span className="px-3 py-1.5 text-xs text-[#8c8c8c]">{page}</span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1.5 text-xs border border-[#262626] rounded-lg text-[#8c8c8c] hover:bg-[#1c1c1c] hover:text-[#ededed] transition-colors"
                >
                  다음
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function EmptyState({ q }: { q: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-center">
      <div className="w-12 h-12 rounded-xl bg-[#1c1c1c] border border-[#262626] flex items-center justify-center text-2xl mb-4">
        📄
      </div>
      <h3 className="text-sm font-semibold text-[#ededed] mb-1">
        {q ? `"${q}" 검색 결과가 없습니다` : "아직 제안서가 없습니다"}
      </h3>
      <p className="text-xs text-[#8c8c8c] mb-6 max-w-xs">
        RFP 파일을 업로드하면 AI가 제안서를 자동으로 생성합니다.
      </p>
      {!q && (
        <Link
          href="/proposals/new"
          className="bg-[#3ecf8e] hover:bg-[#49e59e] text-black font-semibold rounded-lg px-5 py-2 text-sm transition-colors"
        >
          첫 제안서 만들기
        </Link>
      )}
    </div>
  );
}
