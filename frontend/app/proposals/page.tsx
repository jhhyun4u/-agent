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
import { createClient } from "@/lib/supabase/client";

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  initialized: { label: "대기", color: "bg-gray-100 text-gray-600" },
  processing:  { label: "생성 중", color: "bg-blue-100 text-blue-700" },
  completed:   { label: "완료", color: "bg-green-100 text-green-700" },
  failed:      { label: "실패", color: "bg-red-100 text-red-700" },
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
  const [userEmail, setUserEmail] = useState("");

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

  useEffect(() => {
    createClient().auth.getUser().then(({ data }) => {
      setUserEmail(data.user?.email ?? "");
    });
  }, []);

  async function handleSignOut() {
    await createClient().auth.signOut();
    router.push("/login");
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    fetchProposals();
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <h1 className="text-lg font-bold text-gray-900">Tenopa Proposer</h1>
          <div className="flex items-center gap-4">
            <Link href="/admin" className="text-sm text-gray-600 hover:text-gray-900">팀 관리</Link>
            <span className="text-sm text-gray-400">{userEmail}</span>
            <button onClick={handleSignOut} className="text-sm text-gray-500 hover:text-gray-900">
              로그아웃
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* 검색 + 필터 + 새 제안서 버튼 */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <form onSubmit={handleSearch} className="flex gap-2 flex-1">
            <input
              type="text"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="제안서 제목 검색..."
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <select
              value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1); }}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">전체 상태</option>
              <option value="initialized">대기</option>
              <option value="processing">생성 중</option>
              <option value="completed">완료</option>
              <option value="failed">실패</option>
            </select>
            <button
              type="submit"
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg px-4 py-2 text-sm font-medium"
            >
              검색
            </button>
          </form>

          <Link
            href="/proposals/new"
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg px-5 py-2 text-sm text-center whitespace-nowrap transition-colors"
          >
            + 새 제안서
          </Link>
        </div>

        {/* 목록 */}
        {loading ? (
          <div className="text-center py-16 text-gray-400">불러오는 중...</div>
        ) : proposals.length === 0 ? (
          <EmptyState q={q} />
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 divide-y divide-gray-100">
            {proposals.map((p) => (
              <Link
                key={p.id}
                href={`/proposals/${p.id}`}
                className="flex items-center px-6 py-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">{p.title}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {new Date(p.created_at).toLocaleDateString("ko-KR")}
                    {p.win_result && (
                      <span className="ml-2 font-medium text-gray-600">
                        · {WIN_LABELS[p.win_result] ?? p.win_result}
                        {p.bid_amount ? ` (${p.bid_amount.toLocaleString()}원)` : ""}
                      </span>
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-3 ml-4 shrink-0">
                  <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${STATUS_LABELS[p.status]?.color ?? "bg-gray-100 text-gray-600"}`}>
                    {STATUS_LABELS[p.status]?.label ?? p.status}
                  </span>
                  {p.status === "processing" && (
                    <span className="text-xs text-gray-400">Phase {p.phases_completed}/5</span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* 페이지네이션 */}
        {proposals.length === 20 && (
          <div className="flex justify-center gap-2 mt-6">
            <button
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              className="px-4 py-2 text-sm border rounded-lg disabled:opacity-40 hover:bg-gray-100"
            >
              이전
            </button>
            <span className="px-4 py-2 text-sm">{page}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-100"
            >
              다음
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

function EmptyState({ q }: { q: string }) {
  return (
    <div className="text-center py-20">
      <div className="text-5xl mb-4">📄</div>
      <h3 className="text-lg font-semibold text-gray-800 mb-1">
        {q ? `"${q}" 검색 결과가 없습니다` : "아직 제안서가 없습니다"}
      </h3>
      <p className="text-gray-500 text-sm mb-6">
        RFP 파일을 업로드하면 AI가 제안서를 자동으로 생성합니다.
      </p>
      {!q && (
        <Link
          href="/proposals/new"
          className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg px-6 py-2.5 text-sm transition-colors"
        >
          첫 제안서 만들기
        </Link>
      )}
    </div>
  );
}
