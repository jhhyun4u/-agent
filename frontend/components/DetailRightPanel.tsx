"use client";

/**
 * 제안서 상세 페이지 — 우측 패널 (산출물 + 탭 영역)
 * StepArtifactViewer + 6개 탭 (결과물 / 댓글 / 수주결과 / 버전비교 / Q&A / 파일)
 */

import { useCallback, useEffect, useState } from "react";
import { api, Comment_, ProposalFile, ProposalSummary } from "@/lib/api";
import StepArtifactViewer from "@/components/StepArtifactViewer";
import QaPanel from "@/components/QaPanel";

// ── 상수 ──
const PHASES = [
  { n: 1, name: "RFP 분석" },
  { n: 2, name: "경쟁 분석" },
  { n: 3, name: "전략 수립" },
  { n: 4, name: "본문 작성" },
  { n: 5, name: "품질 검증" },
];

type Tab = "result" | "comments" | "win" | "compare" | "qa" | "files";

interface DetailRightPanelProps {
  proposalId: string;
  status: string;
  phasesCompleted: number;
  error?: string;
  rfpTitle?: string;
  isProcessing: boolean;
  isCompleted: boolean;
  isFailed: boolean;
  elapsed: string;
  selectedStep: number | null;
  onGoto: (step: string) => void;
  downloadToken: string;
  versions: ProposalSummary[];
  currentVersionLabel: string;
  resultData: Record<string, unknown> | null;
  comments: Comment_[];
  currentUserId: string;
  onFetchComments: () => void;
  files: ProposalFile[];
  filesLoading: boolean;
  onFetchFiles: () => void;
  onRetryFromPhase: (phaseN: number) => void;
}

export default function DetailRightPanel({
  proposalId,
  status,
  phasesCompleted,
  error,
  rfpTitle,
  isProcessing,
  isCompleted,
  isFailed,
  elapsed,
  selectedStep,
  onGoto,
  downloadToken,
  versions,
  currentVersionLabel,
  resultData,
  comments,
  currentUserId,
  onFetchComments,
  files,
  filesLoading,
  onFetchFiles,
  onRetryFromPhase,
}: DetailRightPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("result");

  // ── 댓글 ──
  const [newComment, setNewComment] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);

  async function handleComment(e: React.FormEvent) {
    e.preventDefault();
    if (!newComment.trim()) return;
    setSubmittingComment(true);
    try {
      await api.comments.create(proposalId, newComment.trim());
      setNewComment("");
      onFetchComments();
    } catch (err) {
      alert(err instanceof Error ? err.message : "댓글 작성 실패");
    } finally {
      setSubmittingComment(false);
    }
  }

  async function handleDeleteComment(commentId: string) {
    if (!confirm("댓글을 삭제하시겠습니까?")) return;
    try {
      await api.comments.delete(commentId);
      onFetchComments();
    } catch (err) {
      alert(err instanceof Error ? err.message : "삭제 실패");
    }
  }

  // ── 수주결과 ──
  const [winForm, setWinForm] = useState({ win_result: "", bid_amount: "", notes: "" });
  const [winSaved, setWinSaved] = useState(false);

  async function handleSaveWinResult() {
    if (!winForm.win_result) return;
    try {
      await api.proposals.updateWinResult(proposalId, {
        win_result: winForm.win_result,
        bid_amount: winForm.bid_amount ? parseInt(winForm.bid_amount) : undefined,
        notes: winForm.notes || undefined,
      });
      setWinSaved(true);
    } catch (err) {
      alert(err instanceof Error ? err.message : "저장 실패");
    }
  }

  // ── 버전 비교 (자체 완결) ──
  const [compareVersionId, setCompareVersionId] = useState<string | null>(null);
  const [compareData, setCompareData] = useState<{ artifacts: Record<string, unknown> } | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [comparePhase, setComparePhase] = useState(1);

  useEffect(() => {
    if (!compareVersionId) {
      setCompareData(null);
      return;
    }
    setCompareLoading(true);
    api.artifacts.get(compareVersionId, "proposal")
      .then((r) => setCompareData(r as any))
      .catch(() => setCompareData(null))
      .finally(() => setCompareLoading(false));
  }, [compareVersionId]);

  // ── 파일 업로드/다운로드/삭제 ──
  const [uploading, setUploading] = useState(false);

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await api.proposals.uploadFile(proposalId, file);
      onFetchFiles();
    } catch (err) {
      alert(err instanceof Error ? err.message : "업로드 실패");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function handleFileDownload(fileId: string) {
    try {
      const res = await api.proposals.getFileUrl(proposalId, fileId);
      window.open(res.url, "_blank");
    } catch (err) {
      alert(err instanceof Error ? err.message : "다운로드 실패");
    }
  }

  async function handleFileDelete(fileId: string) {
    if (!confirm("파일을 삭제하시겠습니까?")) return;
    try {
      await api.proposals.deleteFile(proposalId, fileId);
      onFetchFiles();
    } catch (err) {
      alert(err instanceof Error ? err.message : "삭제 실패");
    }
  }

  // ── 다운로드 ──
  async function handleDownload(type: "docx" | "pptx" | "hwpx") {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}/proposals/${proposalId}/download/${type}`,
        { headers: { Authorization: `Bearer ${downloadToken}` } },
      );
      if (!res.ok) throw new Error("다운로드 실패");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `proposal-${proposalId}.${type}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err instanceof Error ? err.message : "다운로드 실패");
    }
  }

  function versionLabel(idx: number) { return `v${idx + 1}`; }
  const failedPhaseN = phasesCompleted + 1;

  return (
    <div className="flex flex-col h-full">
      {/* STEP 산출물 뷰어 */}
      {selectedStep !== null && (
        <div className="border-b border-[#262626] p-4">
          <StepArtifactViewer
            proposalId={proposalId}
            stepIndex={selectedStep}
            onGoto={onGoto}
          />
        </div>
      )}

      {/* 탭 바 */}
      <div className="border-b border-[#262626] px-2 shrink-0">
        <div className="flex overflow-x-auto items-center">
          {/* 작업물 그룹 */}
          {(
            [
              { key: "result" as Tab, label: "결과물" },
              { key: "comments" as Tab, label: `댓글${comments.length > 0 ? ` (${comments.length})` : ""}` },
              { key: "qa" as Tab, label: "Q&A" },
            ] as const
          ).map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-3 py-2.5 text-xs font-medium transition-colors border-b-2 -mb-px whitespace-nowrap ${
                activeTab === key
                  ? "text-[#ededed] border-[#3ecf8e]"
                  : "text-[#8c8c8c] border-transparent hover:text-[#ededed]"
              }`}
            >
              {label}
            </button>
          ))}
          {/* 구분선 */}
          <div className="w-px h-4 bg-[#262626] mx-1 shrink-0" />
          {/* 관리 그룹 */}
          {(
            [
              { key: "win" as Tab, label: "수주결과" },
              { key: "compare" as Tab, label: "비교" },
              { key: "files" as Tab, label: `파일${files.length > 0 ? ` (${files.length})` : ""}` },
            ] as const
          ).map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-3 py-2.5 text-xs font-medium transition-colors border-b-2 -mb-px whitespace-nowrap ${
                activeTab === key
                  ? "text-[#ededed] border-[#3ecf8e]"
                  : "text-[#8c8c8c] border-transparent hover:text-[#ededed]"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* 탭 콘텐츠 */}
      <div className="flex-1 overflow-y-auto p-4">

        {/* 결과물 */}
        {activeTab === "result" && (
          <div>
            <h3 className="text-xs font-semibold text-[#ededed] mb-3">생성 결과물</h3>

            {isCompleted && (
              <div className="flex flex-col gap-2">
                <button
                  onClick={() => handleDownload("docx")}
                  className="flex items-center gap-3 px-3 py-2.5 bg-[#111111] hover:bg-[#262626] border border-[#262626] hover:border-blue-500/40 rounded-xl text-xs text-[#ededed] transition-colors w-full text-left"
                >
                  <span className="w-7 h-7 rounded-lg bg-blue-500/15 text-blue-400 flex items-center justify-center text-sm shrink-0">D</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium">DOCX</p>
                    <p className="text-[10px] text-[#8c8c8c]">Word 제안서</p>
                  </div>
                </button>
                <button
                  onClick={() => handleDownload("pptx")}
                  className="flex items-center gap-3 px-3 py-2.5 bg-[#111111] hover:bg-[#262626] border border-[#262626] hover:border-indigo-500/40 rounded-xl text-xs text-[#ededed] transition-colors w-full text-left"
                >
                  <span className="w-7 h-7 rounded-lg bg-indigo-500/15 text-indigo-400 flex items-center justify-center text-sm shrink-0">P</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium">PPTX</p>
                    <p className="text-[10px] text-[#8c8c8c]">PowerPoint 요약본</p>
                  </div>
                </button>
                {(resultData as any)?.hwpx_path && (
                  <button
                    onClick={() => handleDownload("hwpx")}
                    className="flex items-center gap-3 px-3 py-2.5 bg-[#111111] hover:bg-[#262626] border border-[#262626] hover:border-[#3ecf8e]/40 rounded-xl text-xs text-[#ededed] transition-colors w-full text-left"
                  >
                    <span className="w-7 h-7 rounded-lg bg-[#3ecf8e]/15 text-[#3ecf8e] flex items-center justify-center text-sm shrink-0">H</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium">HWPX</p>
                      <p className="text-[10px] text-[#8c8c8c]">한글 문서</p>
                    </div>
                  </button>
                )}
              </div>
            )}

            {isProcessing && (
              <div className="flex flex-col items-center justify-center py-8 gap-3 text-[#8c8c8c]">
                <div className="relative w-10 h-10">
                  <div className="absolute inset-0 rounded-full border-2 border-[#262626]" />
                  <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#3ecf8e] animate-spin" />
                </div>
                <div className="text-center">
                  <p className="text-xs text-[#ededed] font-medium">
                    Phase {phasesCompleted + 1}/5
                  </p>
                  <p className="text-[10px] text-[#8c8c8c] mt-0.5">경과: {elapsed}</p>
                </div>
              </div>
            )}

            {isFailed && (
              <div className="py-4 text-center">
                <p className="text-xs font-medium text-red-400 mb-1">생성 실패</p>
                {error && <p className="text-[10px] text-[#8c8c8c] mb-3">{error}</p>}
                <button
                  onClick={() => onRetryFromPhase(failedPhaseN)}
                  className="px-3 py-1.5 bg-red-500/15 hover:bg-red-500/25 text-red-400 text-xs font-medium rounded-lg border border-red-500/30 transition-colors"
                >
                  Phase {failedPhaseN}부터 재시작
                </button>
              </div>
            )}
          </div>
        )}

        {/* 댓글 */}
        {activeTab === "comments" && (
          <div>
            <h3 className="text-xs font-semibold text-[#ededed] mb-3">
              댓글 <span className="text-[#8c8c8c] font-normal">({comments.length})</span>
            </h3>

            {comments.length === 0 ? (
              <p className="text-xs text-[#8c8c8c] mb-3">아직 댓글이 없습니다.</p>
            ) : (
              <ul className="space-y-2.5 mb-3">
                {comments.map((c) => (
                  <li key={c.id} className="flex gap-2">
                    <div className="w-6 h-6 rounded-full bg-[#262626] shrink-0 flex items-center justify-center text-[10px] text-[#8c8c8c] font-medium">
                      {c.user_id.slice(0, 2).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-[#ededed] leading-relaxed break-words">{c.content}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] text-[#8c8c8c]">
                          {new Date(c.created_at).toLocaleString("ko-KR")}
                        </span>
                        {c.user_id === currentUserId && (
                          <button
                            onClick={() => handleDeleteComment(c.id)}
                            className="text-[10px] text-red-400/70 hover:text-red-400 transition-colors"
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

            <form onSubmit={handleComment} className="flex gap-1.5">
              <input
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="댓글 작성..."
                className="flex-1 bg-[#111111] border border-[#262626] rounded-lg px-2.5 py-1.5 text-xs text-[#ededed] placeholder-[#8c8c8c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40 transition-colors"
              />
              <button
                type="submit"
                disabled={submittingComment || !newComment.trim()}
                className="bg-[#3ecf8e] hover:bg-[#3ecf8e]/90 disabled:opacity-40 text-[#0f0f0f] text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
              >
                등록
              </button>
            </form>
          </div>
        )}

        {/* 수주결과 */}
        {activeTab === "win" && (
          <div>
            <h3 className="text-xs font-semibold text-[#ededed] mb-3">수주결과 기록</h3>

            {winSaved && (
              <div className="mb-3 bg-[#3ecf8e]/10 border border-[#3ecf8e]/20 rounded-lg px-2.5 py-1.5">
                <p className="text-xs text-[#3ecf8e]">저장되었습니다.</p>
              </div>
            )}

            <div className="space-y-2.5">
              <div className="flex gap-1.5">
                {(
                  [
                    { value: "won", label: "수주", activeClass: "bg-[#3ecf8e]/15 text-[#3ecf8e] border-[#3ecf8e]/50" },
                    { value: "lost", label: "낙찰실패", activeClass: "bg-red-500/15 text-red-400 border-red-500/50" },
                    { value: "pending", label: "대기", activeClass: "bg-[#262626] text-[#8c8c8c] border-[#8c8c8c]/30" },
                  ] as const
                ).map(({ value, label, activeClass }) => (
                  <button
                    key={value}
                    onClick={() => { setWinForm((f) => ({ ...f, win_result: value })); setWinSaved(false); }}
                    className={`flex-1 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                      winForm.win_result === value
                        ? activeClass
                        : "border-[#262626] text-[#8c8c8c] hover:text-[#ededed]"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              <input
                type="number"
                value={winForm.bid_amount}
                onChange={(e) => setWinForm((f) => ({ ...f, bid_amount: e.target.value }))}
                placeholder="낙찰 금액 (원)"
                className="w-full bg-[#111111] border border-[#262626] rounded-lg px-2.5 py-1.5 text-xs text-[#ededed] placeholder-[#8c8c8c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40 transition-colors"
              />

              <textarea
                value={winForm.notes}
                onChange={(e) => setWinForm((f) => ({ ...f, notes: e.target.value }))}
                placeholder="비고 (선택)"
                rows={2}
                className="w-full bg-[#111111] border border-[#262626] rounded-lg px-2.5 py-1.5 text-xs text-[#ededed] placeholder-[#8c8c8c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40 resize-none transition-colors"
              />

              <button
                onClick={handleSaveWinResult}
                disabled={!winForm.win_result}
                className="w-full bg-[#3ecf8e] hover:bg-[#3ecf8e]/90 disabled:opacity-40 text-[#0f0f0f] font-semibold rounded-lg py-2 text-xs transition-colors"
              >
                저장
              </button>
            </div>
          </div>
        )}

        {/* 버전 비교 */}
        {activeTab === "compare" && (
          <div className="space-y-3">
            <div className="space-y-2">
              <div className="bg-[#111111] border border-[#262626] rounded-lg p-2.5">
                <p className="text-[10px] font-semibold text-[#8c8c8c] mb-0.5">현재: {currentVersionLabel}</p>
                <p className="text-[10px] text-[#8c8c8c] truncate">{rfpTitle || "제안서"}</p>
              </div>
              <select
                value={compareVersionId ?? ""}
                onChange={(e) => setCompareVersionId(e.target.value || null)}
                className="w-full bg-[#111111] border border-[#262626] rounded-lg px-2.5 py-1.5 text-xs text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] transition-colors"
              >
                <option value="">비교 버전 선택...</option>
                {versions
                  .filter((v) => v.id !== proposalId)
                  .map((v) => {
                    const allIdx = versions.findIndex((x) => x.id === v.id);
                    return (
                      <option key={v.id} value={v.id}>
                        {versionLabel(allIdx !== -1 ? allIdx : 0)}
                      </option>
                    );
                  })}
              </select>
            </div>

            {/* Phase 탭 */}
            <div className="flex gap-1 flex-wrap">
              {PHASES.map((p) => (
                <button
                  key={p.n}
                  onClick={() => setComparePhase(p.n)}
                  className={`px-2 py-1 text-[10px] font-medium rounded-md border transition-colors ${
                    comparePhase === p.n
                      ? "bg-[#3ecf8e]/15 text-[#3ecf8e] border-[#3ecf8e]/40"
                      : "border-[#262626] text-[#8c8c8c] hover:text-[#ededed]"
                  }`}
                >
                  {p.name}
                </button>
              ))}
            </div>

            {/* 비교 콘텐츠 — 세로 배치 (패널 너비 제한) */}
            <div className="space-y-2">
              <div className="bg-[#111111] border border-[#262626] rounded-lg p-3 min-h-[120px]">
                <p className="text-[10px] font-semibold text-[#8c8c8c] uppercase tracking-wider mb-2">
                  {currentVersionLabel} — Phase {comparePhase}
                </p>
                {(resultData as any)?.artifacts?.[`phase_${comparePhase}`] ||
                 (resultData as any)?.artifacts?.[comparePhase] ? (
                  <pre className="text-[10px] text-[#ededed] whitespace-pre-wrap break-words leading-relaxed font-sans">
                    {String(
                      (resultData as any)?.artifacts?.[`phase_${comparePhase}`] ??
                      (resultData as any)?.artifacts?.[comparePhase] ?? ""
                    )}
                  </pre>
                ) : (
                  <p className="text-[10px] text-[#8c8c8c]">
                    {status !== "completed" ? "미완료" : "결과 없음"}
                  </p>
                )}
              </div>

              {compareVersionId && (
                <div className="bg-[#111111] border border-[#262626] rounded-lg p-3 min-h-[120px]">
                  {compareLoading ? (
                    <div className="flex items-center justify-center py-6">
                      <div className="w-4 h-4 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin" />
                    </div>
                  ) : (
                    <>
                      <p className="text-[10px] font-semibold text-[#8c8c8c] uppercase tracking-wider mb-2">
                        {versionLabel(versions.findIndex((v) => v.id === compareVersionId))} — Phase {comparePhase}
                      </p>
                      {compareData &&
                      ((compareData as any)?.artifacts?.[`phase_${comparePhase}`] ||
                       (compareData as any)?.artifacts?.[comparePhase]) ? (
                        <pre className="text-[10px] text-[#ededed] whitespace-pre-wrap break-words leading-relaxed font-sans">
                          {String(
                            (compareData as any)?.artifacts?.[`phase_${comparePhase}`] ??
                            (compareData as any)?.artifacts?.[comparePhase] ?? ""
                          )}
                        </pre>
                      ) : (
                        <p className="text-[10px] text-[#8c8c8c]">
                          {!compareData ? "불러올 수 없음" : "결과 없음"}
                        </p>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Q&A */}
        {activeTab === "qa" && (
          <QaPanel proposalId={proposalId} />
        )}

        {/* 파일 */}
        {activeTab === "files" && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-[#ededed]">
                파일 <span className="text-[#8c8c8c] font-normal">({files.length})</span>
              </h3>
              <label className={`cursor-pointer px-2.5 py-1 rounded-lg text-[10px] font-medium transition-colors ${
                uploading
                  ? "bg-[#262626] text-[#8c8c8c]"
                  : "bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#3ecf8e]/90"
              }`}>
                {uploading ? "업로드 중..." : "추가"}
                <input
                  type="file"
                  className="hidden"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  accept=".pdf,.docx,.hwp,.hwpx,.xlsx,.pptx,.png,.jpg,.jpeg"
                />
              </label>
            </div>

            {filesLoading ? (
              <p className="text-xs text-[#8c8c8c]">불러오는 중...</p>
            ) : files.length === 0 ? (
              <p className="text-xs text-[#8c8c8c]">등록된 파일이 없습니다.</p>
            ) : (
              <div className="space-y-1">
                {(["rfp", "reference", "attachment"] as const).map((cat) => {
                  const catFiles = files.filter((f) => f.category === cat);
                  if (catFiles.length === 0) return null;
                  const catLabels = { rfp: "RFP 원본", reference: "참고자료", attachment: "G2B 첨부" };
                  return (
                    <div key={cat} className="mb-2">
                      <p className="text-[10px] font-semibold text-[#8c8c8c] uppercase tracking-wider mb-1">
                        {catLabels[cat]}
                      </p>
                      <ul className="space-y-0.5">
                        {catFiles.map((f) => (
                          <li key={f.id} className="flex items-center gap-2 px-2 py-1.5 bg-[#111111] border border-[#262626] rounded-lg group">
                            <span className="text-[10px] text-[#8c8c8c] uppercase w-8 shrink-0">
                              {f.file_type || "?"}
                            </span>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs text-[#ededed] truncate">{f.filename}</p>
                            </div>
                            <button
                              onClick={() => handleFileDownload(f.id)}
                              className="text-[10px] text-[#3ecf8e] hover:text-[#49e59e] opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              DL
                            </button>
                            {f.category !== "rfp" && (
                              <button
                                onClick={() => handleFileDelete(f.id)}
                                className="text-[10px] text-red-400/70 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                              >
                                X
                              </button>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
