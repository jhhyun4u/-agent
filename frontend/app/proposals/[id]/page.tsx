"use client";

/**
 * F5 + F6: 제안서 상세 페이지
 * - PhaseProgress: Supabase Realtime 실시간 진행 상태
 * - ResultViewer: 완료 시 요약 + 다운로드
 * - PhaseRetryButton: 실패 시 재시도
 * - CommentThread: 댓글 목록 + 작성
 * - WinResult: 수주결과 저장
 */

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, Comment_ } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import { usePhaseStatus } from "@/lib/hooks/usePhaseStatus";

const PHASES = [
  { n: 1, name: "RFP 분석 · 나라장터 조회" },
  { n: 2, name: "경쟁사 분석 · 가격 전략" },
  { n: 3, name: "제안 전략 수립" },
  { n: 4, name: "제안서 본문 작성" },
  { n: 5, name: "품질 검증 · 문서 생성" },
];

const PHASE_MINUTES = [2, 3, 3, 5, 2]; // 각 Phase 예상 소요시간

export default function ProposalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { status, loading } = usePhaseStatus(id);
  const [comments, setComments] = useState<Comment_[]>([]);
  const [newComment, setNewComment] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);
  const [winForm, setWinForm] = useState({ win_result: "", bid_amount: "", notes: "" });
  const [winSaved, setWinSaved] = useState(false);
  const [currentUserId, setCurrentUserId] = useState("");
  const [downloadToken, setDownloadToken] = useState("");

  const fetchComments = useCallback(async () => {
    try {
      const res = await api.comments.list(id);
      setComments(res.comments);
    } catch {}
  }, [id]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  useEffect(() => {
    createClient().auth.getUser().then(({ data }) => {
      setCurrentUserId(data.user?.id ?? "");
    });
    // 다운로드용 토큰 준비
    createClient().auth.getSession().then(({ data }) => {
      setDownloadToken(data.session?.access_token ?? "");
    });
  }, []);

  async function handleRetry() {
    try {
      await api.proposals.execute(id);
      // Realtime이 DB 변경을 자동 감지하므로 별도 refresh 불필요
    } catch (e) {
      alert(e instanceof Error ? e.message : "재시도 실패");
    }
  }

  async function handleComment(e: React.FormEvent) {
    e.preventDefault();
    if (!newComment.trim()) return;
    setSubmittingComment(true);
    try {
      await api.comments.create(id, newComment.trim());
      setNewComment("");
      fetchComments();
    } catch (e) {
      alert(e instanceof Error ? e.message : "댓글 작성 실패");
    } finally {
      setSubmittingComment(false);
    }
  }

  async function handleDeleteComment(commentId: string) {
    if (!confirm("댓글을 삭제하시겠습니까?")) return;
    try {
      await api.comments.delete(commentId);
      fetchComments();
    } catch (e) {
      alert(e instanceof Error ? e.message : "삭제 실패");
    }
  }

  async function handleSaveWinResult() {
    if (!winForm.win_result) return;
    try {
      await api.proposals.updateWinResult(id, {
        win_result: winForm.win_result,
        bid_amount: winForm.bid_amount ? parseInt(winForm.bid_amount) : undefined,
        notes: winForm.notes || undefined,
      });
      setWinSaved(true);
    } catch (e) {
      alert(e instanceof Error ? e.message : "저장 실패");
    }
  }

  function downloadUrl(type: "docx" | "pptx" | "hwpx") {
    return `${process.env.NEXT_PUBLIC_API_URL}/v3.1/proposals/${id}/download/${type}?token=${downloadToken}`;
  }

  if (loading || !status) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        불러오는 중...
      </div>
    );
  }

  const isProcessing = status.status === "processing" || status.status === "initialized";
  const isCompleted = status.status === "completed";
  const isFailed = status.status === "failed";

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <Link href="/proposals" className="text-gray-400 hover:text-gray-700 text-sm">
            ← 목록
          </Link>
          <h1 className="text-base font-semibold text-gray-900 truncate flex-1">
            {status.rfp_title || "제안서"}
          </h1>
          <span className="text-xs text-gray-400">{status.client_name}</span>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8 space-y-6">

        {/* ── Phase 진행 상태 ── */}
        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-900 mb-4">진행 상태</h2>

          {isFailed && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
              <p className="text-sm text-red-700 font-medium">생성 실패</p>
              {status.error && <p className="text-xs text-red-600 mt-1">{status.error}</p>}
              <button
                onClick={handleRetry}
                className="mt-3 bg-red-600 hover:bg-red-700 text-white text-xs font-medium px-4 py-1.5 rounded-lg transition-colors"
              >
                Phase {status.phases_completed + 1}부터 재시도
              </button>
            </div>
          )}

          <div className="space-y-3">
            {PHASES.map((phase) => {
              const done = status.phases_completed >= phase.n;
              const active =
                isProcessing && status.phases_completed === phase.n - 1;
              return (
                <div key={phase.n} className="flex items-center gap-3">
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                      done
                        ? "bg-green-500 text-white"
                        : active
                        ? "bg-blue-500 text-white animate-pulse"
                        : "bg-gray-100 text-gray-400"
                    }`}
                  >
                    {done ? "✓" : phase.n}
                  </div>
                  <div className="flex-1">
                    <p className={`text-sm ${done ? "text-gray-700" : active ? "text-blue-700 font-medium" : "text-gray-400"}`}>
                      {phase.name}
                    </p>
                    {active && (
                      <p className="text-xs text-gray-400 mt-0.5">
                        처리 중 · 예상 {PHASE_MINUTES[phase.n - 1]}분
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {isProcessing && (
            <p className="mt-4 text-xs text-gray-400 text-center">
              완료 시 이메일로 알림을 보내드립니다.
            </p>
          )}
        </section>

        {/* ── 결과 뷰어 ── */}
        {isCompleted && (
          <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 mb-4">생성 결과</h2>

            <div className="flex gap-3 mb-4">
              <a
                href={downloadUrl("docx")}
                className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg py-2.5 text-sm transition-colors"
              >
                📄 DOCX 다운로드
              </a>
              <a
                href={downloadUrl("pptx")}
                className="flex-1 flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg py-2.5 text-sm transition-colors"
              >
                📊 PPTX 다운로드
              </a>
              {status.hwpx_path && (
                <a
                  href={downloadUrl("hwpx")}
                  className="flex-1 flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-medium rounded-lg py-2.5 text-sm transition-colors"
                >
                  📝 HWPX 다운로드
                </a>
              )}
            </div>
          </section>
        )}

        {/* ── 수주결과 저장 ── */}
        {isCompleted && (
          <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 mb-4">수주결과 기록</h2>
            {winSaved && (
              <p className="mb-3 text-sm text-green-700 bg-green-50 rounded-lg px-3 py-2">저장되었습니다.</p>
            )}
            <div className="space-y-3">
              <div className="flex gap-2">
                {["won", "lost", "pending"].map((v) => (
                  <button
                    key={v}
                    onClick={() => setWinForm((f) => ({ ...f, win_result: v }))}
                    className={`flex-1 py-2 text-sm font-medium rounded-lg border transition-colors ${
                      winForm.win_result === v
                        ? v === "won"
                          ? "bg-green-600 text-white border-green-600"
                          : v === "lost"
                          ? "bg-red-500 text-white border-red-500"
                          : "bg-gray-600 text-white border-gray-600"
                        : "border-gray-300 text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    {v === "won" ? "수주" : v === "lost" ? "낙찰 실패" : "결과 대기"}
                  </button>
                ))}
              </div>
              <input
                type="number"
                value={winForm.bid_amount}
                onChange={(e) => setWinForm((f) => ({ ...f, bid_amount: e.target.value }))}
                placeholder="낙찰 금액 (원)"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <textarea
                value={winForm.notes}
                onChange={(e) => setWinForm((f) => ({ ...f, notes: e.target.value }))}
                placeholder="비고 (선택)"
                rows={2}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
              <button
                onClick={handleSaveWinResult}
                disabled={!winForm.win_result}
                className="w-full bg-gray-800 hover:bg-gray-900 disabled:opacity-40 text-white font-medium rounded-lg py-2 text-sm transition-colors"
              >
                저장
              </button>
            </div>
          </section>
        )}

        {/* ── 댓글 (F6) ── */}
        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-900 mb-4">
            댓글 <span className="text-gray-400 font-normal text-sm">({comments.length})</span>
          </h2>

          {comments.length === 0 ? (
            <p className="text-sm text-gray-400 mb-4">아직 댓글이 없습니다.</p>
          ) : (
            <ul className="space-y-3 mb-4">
              {comments.map((c) => (
                <li key={c.id} className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-gray-200 shrink-0 flex items-center justify-center text-xs text-gray-500">
                    {c.user_id.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-800 leading-relaxed">{c.content}</p>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-xs text-gray-400">
                        {new Date(c.created_at).toLocaleString("ko-KR")}
                      </span>
                      {c.user_id === currentUserId && (
                        <button
                          onClick={() => handleDeleteComment(c.id)}
                          className="text-xs text-red-400 hover:text-red-600"
                        >
                          삭제
                        </button>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}

          <form onSubmit={handleComment} className="flex gap-2">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="댓글 작성..."
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={submittingComment || !newComment.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              등록
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}
