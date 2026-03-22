"use client";

/**
 * 제안서 상세 페이지 — 우측 패널 (산출물 + 탭 영역)
 * StepArtifactViewer + 6개 탭 (결과물 / 댓글 / 수주결과 / 버전비교 / Q&A / 파일)
 */

import { useCallback, useEffect, useState } from "react";
import { api, Comment_, ProposalFile, ProposalSummary } from "@/lib/api";
import StepArtifactViewer from "@/components/StepArtifactViewer";
import CostSheetEditor from "@/components/pricing/CostSheetEditor";
import QaPanel from "@/components/QaPanel";
import VersionCompareModal from "@/components/VersionCompareModal";

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
  const [costSheetOpen, setCostSheetOpen] = useState(false);

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
  const [compareModalOpen, setCompareModalOpen] = useState(false);
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
  const ALLOWED_EXTS = new Set(["pdf","docx","hwp","hwpx","xlsx","pptx","png","jpg","jpeg"]);
  const MAX_FILE_SIZE_MB = 50;

  // 업로드 큐 상태
  interface UploadItem { file: File; progress: number; status: "pending"|"uploading"|"done"|"error"; error?: string; abort?: () => void }
  const [uploadQueue, setUploadQueue] = useState<UploadItem[]>([]);
  const [fileDragOver, setFileDragOver] = useState(false);
  const [fileSearch, setFileSearch] = useState("");
  const [fileSort, setFileSort] = useState<"name"|"date"|"size">("date");

  function validateFile(file: File): string | null {
    const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
    if (!ALLOWED_EXTS.has(ext)) return `허용되지 않는 형식: .${ext}`;
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) return `파일 크기 초과: ${(file.size / 1024 / 1024).toFixed(1)}MB (최대 ${MAX_FILE_SIZE_MB}MB)`;
    // 중복 감지 (#8)
    const dup = files.find(f => f.filename === file.name && f.file_size === file.size);
    if (dup) return `동일한 파일이 이미 존재합니다: ${file.name}`;
    return null;
  }

  async function processUploadQueue(newFiles: File[]) {
    const items: UploadItem[] = newFiles.map(f => ({ file: f, progress: 0, status: "pending" as const }));
    setUploadQueue(prev => [...prev, ...items]);

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      const validationError = validateFile(item.file);
      if (validationError) {
        item.status = "error";
        item.error = validationError;
        setUploadQueue(prev => [...prev]);
        continue;
      }
      item.status = "uploading";
      setUploadQueue(prev => [...prev]);

      try {
        const { promise, abort } = api.proposals.uploadFileWithProgress(
          proposalId, item.file,
          (pct) => { item.progress = pct; setUploadQueue(prev => [...prev]); },
        );
        item.abort = abort;
        setUploadQueue(prev => [...prev]);
        await promise;
        item.status = "done";
        item.progress = 100;
      } catch (err) {
        item.status = "error";
        item.error = err instanceof Error ? err.message : "업로드 실패";
      }
      setUploadQueue(prev => [...prev]);
    }
    onFetchFiles();
    // 3초 후 완료/에러 항목 자동 제거
    setTimeout(() => setUploadQueue(prev => prev.filter(u => u.status === "uploading")), 3000);
  }

  function handleMultiFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const fileList = e.target.files;
    if (!fileList || fileList.length === 0) return;
    processUploadQueue(Array.from(fileList));
    e.target.value = "";
  }

  function handleFileDrop(e: React.DragEvent) {
    e.preventDefault();
    setFileDragOver(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) processUploadQueue(droppedFiles);
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

  // 파일 미리보기 (#6)
  const [previewFile, setPreviewFile] = useState<{ url: string; filename: string; type: string } | null>(null);

  async function handleFilePreview(file: ProposalFile) {
    const previewTypes = ["png", "jpg", "jpeg", "pdf"];
    if (!file.file_type || !previewTypes.includes(file.file_type.toLowerCase())) {
      handleFileDownload(file.id);
      return;
    }
    try {
      const res = await api.proposals.getFileUrl(proposalId, file.id);
      setPreviewFile({ url: res.url, filename: file.filename, type: file.file_type.toLowerCase() });
    } catch (err) {
      alert(err instanceof Error ? err.message : "미리보기 실패");
    }
  }

  function formatFileSize(bytes: number | null): string {
    if (bytes == null) return "-";
    if (bytes === 0) return "0B";
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  }

  function formatDate(dateStr: string): string {
    const d = new Date(dateStr);
    return `${d.getMonth()+1}/${d.getDate()} ${d.getHours().toString().padStart(2,"0")}:${d.getMinutes().toString().padStart(2,"0")}`;
  }

  // 정렬 + 검색 (#7)
  function getFilteredSortedFiles(catFiles: ProposalFile[]): ProposalFile[] {
    let result = catFiles;
    if (fileSearch.trim()) {
      const q = fileSearch.trim().toLowerCase();
      result = result.filter(f => f.filename.toLowerCase().includes(q));
    }
    return result.sort((a, b) => {
      if (fileSort === "name") return a.filename.localeCompare(b.filename);
      if (fileSort === "size") return (b.file_size ?? 0) - (a.file_size ?? 0);
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });
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

                {/* 산출내역서 */}
                <button
                  onClick={() => setCostSheetOpen(true)}
                  className="flex items-center gap-3 px-3 py-2.5 bg-[#111111] hover:bg-[#262626] border border-[#262626] hover:border-amber-500/40 rounded-xl text-xs text-[#ededed] transition-colors w-full text-left"
                >
                  <span className="w-7 h-7 rounded-lg bg-amber-500/15 text-amber-400 flex items-center justify-center text-sm shrink-0">$</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium">산출내역서</p>
                    <p className="text-[10px] text-[#8c8c8c]">비용 편집 및 DOCX 다운로드</p>
                  </div>
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#555] shrink-0"><polyline points="9 18 15 12 9 6"/></svg>
                </button>
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
                      <div className="text-xs text-[#ededed] leading-relaxed break-words">
                        <SimpleMarkdown text={c.content} />
                      </div>
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
            <p className="text-[9px] text-[#5c5c5c] mt-1">**볼드**, `코드`, - 목록 지원</p>
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

            {/* 전체화면 비교 버튼 */}
            <button
              onClick={() => setCompareModalOpen(true)}
              className="text-[10px] text-[#3ecf8e] hover:underline"
            >
              전체화면 비교 (Side-by-side)
            </button>

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

            {/* 전체화면 비교 모달 */}
            <VersionCompareModal
              open={compareModalOpen}
              onClose={() => setCompareModalOpen(false)}
              proposalId={proposalId}
              versions={versions}
              currentVersionLabel={currentVersionLabel}
            />
          </div>
        )}

        {/* Q&A */}
        {activeTab === "qa" && (
          <QaPanel proposalId={proposalId} />
        )}

        {/* 파일 */}
        {activeTab === "files" && (
          <div>
            {/* 헤더: 제목 + 일괄다운로드 + 업로드 버튼 */}
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-semibold text-[#ededed]">
                파일 <span className="text-[#8c8c8c] font-normal">({files.length})</span>
              </h3>
              <div className="flex items-center gap-1.5">
                {files.length > 0 && (
                  <a
                    href={api.proposals.filesBundleUrl(proposalId)}
                    className="px-2.5 py-1 rounded-lg text-[10px] font-medium border border-[#262626] text-[#8c8c8c] hover:text-[#ededed] hover:border-[#3ecf8e]/40 transition-colors"
                    title="전체 ZIP 다운로드"
                  >
                    ZIP
                  </a>
                )}
                <label className="cursor-pointer px-2.5 py-1 rounded-lg text-[10px] font-medium bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#3ecf8e]/90 transition-colors">
                  추가
                  <input
                    type="file"
                    multiple
                    className="hidden"
                    onChange={handleMultiFileUpload}
                    accept=".pdf,.docx,.hwp,.hwpx,.xlsx,.pptx,.png,.jpg,.jpeg"
                  />
                </label>
              </div>
            </div>

            {/* 검색 + 정렬 (#7) */}
            {files.length > 0 && (
              <div className="flex gap-1.5 mb-2">
                <input
                  type="text"
                  value={fileSearch}
                  onChange={(e) => setFileSearch(e.target.value)}
                  placeholder="파일 검색..."
                  className="flex-1 bg-[#111111] border border-[#262626] rounded-lg px-2 py-1 text-[10px] text-[#ededed] placeholder-[#8c8c8c] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e]/40"
                />
                <select
                  value={fileSort}
                  onChange={(e) => setFileSort(e.target.value as "name"|"date"|"size")}
                  className="bg-[#111111] border border-[#262626] rounded-lg px-1.5 py-1 text-[10px] text-[#8c8c8c] focus:outline-none"
                >
                  <option value="date">최신순</option>
                  <option value="name">이름순</option>
                  <option value="size">크기순</option>
                </select>
              </div>
            )}

            {/* 업로드 큐 (프로그레스 바 #3 + GAP-1 aria-live) */}
            {uploadQueue.length > 0 && (
              <div className="space-y-1 mb-3" aria-live="polite" aria-label="업로드 진행 상태">
                {uploadQueue.map((item, idx) => (
                  <div key={idx} className="bg-[#111111] border border-[#262626] rounded-lg px-2 py-1.5">
                    <div className="flex items-center gap-2">
                      <p className="text-[10px] text-[#ededed] truncate flex-1">{item.file.name}</p>
                      <span className="text-[10px] text-[#8c8c8c] shrink-0">
                        {item.status === "uploading" ? `${item.progress}%` : item.status === "done" ? "완료" : item.status === "error" ? "실패" : "대기"}
                      </span>
                      {item.status === "uploading" && item.abort && (
                        <button onClick={item.abort} className="text-[10px] text-red-400/70 hover:text-red-400" aria-label={`${item.file.name} 업로드 취소`}>취소</button>
                      )}
                    </div>
                    {item.status === "uploading" && (
                      <div className="mt-1 h-1 bg-[#262626] rounded-full overflow-hidden">
                        <div className="h-full bg-[#3ecf8e] transition-all duration-200 rounded-full" style={{ width: `${item.progress}%` }} />
                      </div>
                    )}
                    {item.status === "error" && (
                      <p className="text-[10px] text-red-400 mt-0.5">{item.error}</p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* 드래그&드롭 영역 (#5) */}
            <div
              onDragOver={(e) => { e.preventDefault(); setFileDragOver(true); }}
              onDragLeave={() => setFileDragOver(false)}
              onDrop={handleFileDrop}
              className={`transition-colors rounded-lg ${fileDragOver ? "ring-2 ring-[#3ecf8e]/50 bg-[#3ecf8e]/5" : ""}`}
            >
              {filesLoading ? (
                <p className="text-xs text-[#8c8c8c] py-4 text-center">불러오는 중...</p>
              ) : files.length === 0 ? (
                <div className="border-2 border-dashed border-[#262626] rounded-lg py-8 text-center">
                  <p className="text-xs text-[#8c8c8c]">파일을 드래그하거나 추가 버튼을 눌러주세요</p>
                  <p className="text-[10px] text-[#8c8c8c]/60 mt-1">PDF, DOCX, HWP, HWPX, XLSX, PPTX, PNG, JPG (최대 50MB)</p>
                </div>
              ) : (
                <div className="space-y-1">
                  {(["rfp", "reference", "attachment"] as const).map((cat) => {
                    const catFiles = getFilteredSortedFiles(files.filter((f) => f.category === cat));
                    if (catFiles.length === 0) return null;
                    const catLabels = { rfp: "RFP 원본", reference: "참고자료", attachment: "G2B 첨부" };
                    return (
                      <div key={cat} className="mb-2">
                        <p className="text-[10px] font-semibold text-[#8c8c8c] uppercase tracking-wider mb-1">
                          {catLabels[cat]} ({catFiles.length})
                        </p>
                        <ul className="space-y-0.5">
                          {catFiles.map((f) => (
                            <li key={f.id} className="flex items-center gap-2 px-2 py-1.5 bg-[#111111] border border-[#262626] rounded-lg group hover:border-[#3ecf8e]/20 transition-colors">
                              {/* 확장자 아이콘 */}
                              <span className={`text-[10px] uppercase w-8 shrink-0 font-medium ${
                                f.file_type === "pdf" ? "text-red-400" :
                                f.file_type === "docx" ? "text-blue-400" :
                                f.file_type === "hwpx" || f.file_type === "hwp" ? "text-[#3ecf8e]" :
                                f.file_type === "pptx" ? "text-orange-400" :
                                f.file_type === "xlsx" ? "text-green-400" :
                                ["png","jpg","jpeg"].includes(f.file_type || "") ? "text-purple-400" :
                                "text-[#8c8c8c]"
                              }`}>
                                {f.file_type || "?"}
                              </span>
                              {/* 파일명 + 메타데이터 (#1) */}
                              <div className="flex-1 min-w-0">
                                <button
                                  onClick={() => handleFilePreview(f)}
                                  className="text-xs text-[#ededed] truncate block w-full text-left hover:text-[#3ecf8e] transition-colors"
                                  title={f.filename}
                                >
                                  {f.filename}
                                </button>
                                <p className="text-[10px] text-[#8c8c8c]/70 mt-0.5">
                                  {formatFileSize(f.file_size)}
                                  {f.created_at && <> · {formatDate(f.created_at)}</>}
                                  {f.description && <> · {f.description}</>}
                                </p>
                              </div>
                              {/* 액션 버튼 */}
                              <button
                                onClick={() => handleFileDownload(f.id)}
                                className="text-[10px] text-[#3ecf8e] hover:text-[#49e59e] opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                                title="다운로드"
                                aria-label={`${f.filename} 다운로드`}
                              >
                                DL
                              </button>
                              {f.category !== "rfp" && (
                                <button
                                  onClick={() => handleFileDelete(f.id)}
                                  className="text-[10px] text-red-400/70 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                                  title="삭제"
                                  aria-label={`${f.filename} 삭제`}
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

                  {/* 드래그&드롭 힌트 (파일 있을 때) */}
                  {fileDragOver && (
                    <div className="border-2 border-dashed border-[#3ecf8e]/50 rounded-lg py-4 text-center mt-2">
                      <p className="text-xs text-[#3ecf8e]">여기에 놓으세요</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 파일 미리보기 모달 (#6 + GAP-1 접근성) */}
            {previewFile && (
              <div
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
                role="dialog"
                aria-modal="true"
                aria-label={`파일 미리보기: ${previewFile.filename}`}
                onClick={() => setPreviewFile(null)}
                onKeyDown={(e) => { if (e.key === "Escape") setPreviewFile(null); }}
                tabIndex={-1}
                ref={(el) => el?.focus()}
              >
                <div className="bg-[#1a1a1a] border border-[#262626] rounded-xl max-w-3xl w-full mx-4 max-h-[85vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
                  <div className="flex items-center justify-between px-4 py-3 border-b border-[#262626]">
                    <p className="text-xs text-[#ededed] font-medium truncate">{previewFile.filename}</p>
                    <div className="flex items-center gap-2">
                      <a href={previewFile.url} target="_blank" rel="noopener noreferrer"
                        className="text-[10px] text-[#3ecf8e] hover:text-[#49e59e]">새 탭에서 열기</a>
                      <button onClick={() => setPreviewFile(null)} className="text-[#8c8c8c] hover:text-[#ededed] text-sm" aria-label="미리보기 닫기">X</button>
                    </div>
                  </div>
                  <div className="flex-1 overflow-auto p-4 flex items-center justify-center">
                    {["png","jpg","jpeg"].includes(previewFile.type) ? (
                      <img src={previewFile.url} alt={previewFile.filename} className="max-w-full max-h-[70vh] object-contain rounded" />
                    ) : previewFile.type === "pdf" ? (
                      <iframe src={previewFile.url} className="w-full h-[70vh] rounded" title={previewFile.filename} />
                    ) : null}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ═══ 산출내역서 슬라이드 패널 (Claude Desktop 스타일) ═══ */}
      <div
        className="fixed top-0 right-0 h-full flex transition-transform duration-300 ease-in-out"
        style={{
          zIndex: 50,
          transform: costSheetOpen ? "translateX(0)" : "translateX(100%)",
        }}
      >
        {/* 토글 핸들 — 패널 왼쪽 가장자리에 붙은 세로 탭 */}
        <button
          onClick={() => setCostSheetOpen((v) => !v)}
          className="relative -ml-8 self-center w-8 h-24 flex items-center justify-center group"
          aria-label={costSheetOpen ? "산출내역서 닫기" : "산출내역서 열기"}
        >
          {/* 탭 배경 */}
          <div className="absolute inset-y-0 right-0 w-7 rounded-l-xl bg-[#1c1c1c] border border-r-0 border-[#333] shadow-lg group-hover:bg-[#262626] group-hover:border-[#444] transition-colors" />
          {/* 화살표 아이콘 */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={`relative z-10 text-[#8c8c8c] group-hover:text-[#ededed] transition-all duration-300 ${
              costSheetOpen ? "rotate-0" : "rotate-180"
            }`}
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>

        {/* 패널 본체 */}
        <div className="w-[680px] max-w-[85vw] h-full bg-[#141414] border-l border-[#262626] shadow-2xl flex flex-col">
          {/* 헤더 */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-[#262626] shrink-0">
            <div className="flex items-center gap-2.5">
              <span className="w-6 h-6 rounded bg-amber-500/15 text-amber-400 flex items-center justify-center text-xs font-medium">$</span>
              <h2 className="text-sm font-semibold text-[#ededed]">산출내역서</h2>
            </div>
            <button
              onClick={() => setCostSheetOpen(false)}
              className="w-7 h-7 flex items-center justify-center rounded-lg text-[#8c8c8c] hover:text-[#ededed] hover:bg-[#262626] transition-colors"
              aria-label="닫기"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          {/* 본문 (스크롤) */}
          <div className="flex-1 overflow-y-auto p-5">
            {costSheetOpen && <CostSheetEditor proposalId={proposalId} />}
          </div>
        </div>
      </div>

      {/* 배경 딤 (열렸을 때만) */}
      {costSheetOpen && (
        <div
          className="fixed inset-0 bg-black/30 transition-opacity duration-300"
          style={{ zIndex: 49 }}
          onClick={() => setCostSheetOpen(false)}
        />
      )}
    </div>
  );
}

// ── 간이 마크다운 렌더러 ──
function SimpleMarkdown({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <>
      {lines.map((line, i) => {
        // 목록 항목
        if (line.trimStart().startsWith("- ")) {
          const content = line.replace(/^\s*-\s+/, "");
          return <li key={i} className="ml-3 list-disc">{renderInline(content)}</li>;
        }
        return <p key={i}>{renderInline(line) || "\u00A0"}</p>;
      })}
    </>
  );
}

function renderInline(text: string): React.ReactNode {
  // **볼드** 및 `코드` 변환
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} className="px-1 py-0.5 bg-[#262626] rounded text-[10px] font-mono">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}
