"use client";

/**
 * F5 + F6: 제안서 상세 페이지 (Phase B — Dark Theme)
 * - Header: 제목, 상태 배지, 버전 드롭다운
 * - Phase 진행 대시보드: 가로 스텝 + 진행률 바
 * - 탭: 결과물 / 댓글 / 수주결과
 * - Realtime 상태 구독: usePhaseStatus
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, Comment_, ProposalSummary, type WorkflowState } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import PhaseGraph from "@/components/PhaseGraph";
import WorkflowPanel from "@/components/WorkflowPanel";
import QaPanel from "@/components/QaPanel";
import StepArtifactViewer from "@/components/StepArtifactViewer";
import WorkflowLogPanel from "@/components/WorkflowLogPanel";
import { useWorkflowStream } from "@/lib/hooks/useWorkflowStream";

function useElapsedTime(running: boolean) {
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef(Date.now());
  useEffect(() => {
    if (!running) { setElapsed(0); startRef.current = Date.now(); return; }
    startRef.current = Date.now();
    const t = setInterval(() => setElapsed(Math.floor((Date.now() - startRef.current) / 1000)), 1000);
    return () => clearInterval(t);
  }, [running]);
  const m = Math.floor(elapsed / 60), s = elapsed % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}
import { usePhaseStatus } from "@/lib/hooks/usePhaseStatus";

// ── 상수 ─────────────────────────────────────────────────────────────

const PHASES = [
  {
    n: 1,
    name: "RFP 분석",
    key: "phase_1_research",
    doneDesc: "RFP 문서 구조 분석 및 핵심 요구사항 추출 완료",
    activeDesc: "RFP 문서를 읽고 사업 목적·범위·평가 기준을 분석하고 있습니다",
    activeSubs: ["문서 텍스트 추출", "사업명/발주처/기간 파악", "핵심 요구사항 정리", "나라장터 유사계약 조회"],
  },
  {
    n: 2,
    name: "경쟁 분석",
    key: "phase_2_analysis",
    doneDesc: "경쟁사 현황 분석 및 차별화 포인트 도출 완료",
    activeDesc: "유사 사업 수행이력을 바탕으로 경쟁사를 분석하고 있습니다",
    activeSubs: ["경쟁사 식별 및 강점 분석", "과거 수주 패턴 파악", "차별화 요소 도출"],
  },
  {
    n: 3,
    name: "전략 수립",
    key: "phase_3_plan",
    doneDesc: "수주 전략·가격 전략·리스크 대응 방안 수립 완료",
    activeDesc: "경쟁 분석 결과를 토대로 수주 전략을 설계하고 있습니다",
    activeSubs: ["Win Theme 설정", "섹션별 작성 전략 수립", "가격 전략 시나리오 구성", "리스크 및 대응책 정리"],
  },
  {
    n: 4,
    name: "본문 작성",
    key: "phase_4_implement",
    doneDesc: "제안서 전체 본문 및 DOCX·PPTX 문서 생성 완료",
    activeDesc: "Claude AI가 제안서 각 섹션의 본문을 작성하고 있습니다",
    activeSubs: ["사업 이해 및 추진 방법론 작성", "인력 구성·추진 일정 작성", "DOCX 문서 빌드", "PPTX 요약본 생성"],
  },
  {
    n: 5,
    name: "품질 검증",
    key: "phase_5_test",
    doneDesc: "품질 점수 산정 및 최종 검토 완료",
    activeDesc: "생성된 제안서의 완성도를 종합 검토하고 있습니다",
    activeSubs: ["섹션별 품질 점수 산정", "수주 확률 예측", "최종 문서 업로드"],
  },
];

type Tab = "result" | "comments" | "win" | "compare" | "qa";

// ── 색상 토큰 (Tailwind arbitrary) ────────────────────────────────────
// bg: #0f0f0f  surface: #111111  card: #1c1c1c  border: #262626
// text: #ededed  muted: #8c8c8c  accent: #3ecf8e

// ── 유틸 ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  if (status === "processing" || status === "initialized") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/15 text-blue-400 border border-blue-500/30 animate-pulse">
        <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
        처리중
      </span>
    );
  }
  if (status === "completed") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-[#3ecf8e]/15 text-[#3ecf8e] border border-[#3ecf8e]/30">
        <span className="w-1.5 h-1.5 rounded-full bg-[#3ecf8e]" />
        완료
      </span>
    );
  }
  if (status === "failed") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/15 text-red-400 border border-red-500/30">
        <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
        실패
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-[#262626] text-[#8c8c8c] border border-[#262626]">
      <span className="w-1.5 h-1.5 rounded-full bg-[#8c8c8c]" />
      초기화
    </span>
  );
}

// ── 메인 페이지 ───────────────────────────────────────────────────────

export default function ProposalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { status, loading } = usePhaseStatus(id);

  // 탭
  const [activeTab, setActiveTab] = useState<Tab>("result");

  // 버전 드롭다운
  const [versions, setVersions] = useState<ProposalSummary[]>([]);
  const [versionOpen, setVersionOpen] = useState(false);
  const versionRef = useRef<HTMLDivElement>(null);

  // 댓글
  const [comments, setComments] = useState<Comment_[]>([]);
  const [newComment, setNewComment] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);
  const [currentUserId, setCurrentUserId] = useState("");

  // 워크플로 상태 (PhaseGraph + WorkflowPanel)
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);

  // 다운로드 토큰 + result 추가 데이터
  const [downloadToken, setDownloadToken] = useState("");
  const [resultData, setResultData] = useState<{
    docx_path?: string;
    pptx_path?: string;
    hwpx_path?: string;
  } | null>(null);

  // 수주결과
  const [winForm, setWinForm] = useState({ win_result: "", bid_amount: "", notes: "" });
  const [winSaved, setWinSaved] = useState(false);

  // 버전 비교
  const [compareVersionId, setCompareVersionId] = useState<string | null>(null);
  const [compareData, setCompareData] = useState<{ artifacts: Record<string, unknown> } | null>(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [comparePhase, setComparePhase] = useState(1);

  // ── 초기 데이터 로드 ───────────────────────────────────────────────

  useEffect(() => {
    createClient().auth.getUser().then(({ data }) => {
      setCurrentUserId(data.user?.id ?? "");
    });
    createClient().auth.getSession().then(({ data }) => {
      setDownloadToken(data.session?.access_token ?? "");
    });
  }, []);

  // 워크플로 상태 폴링
  const fetchWorkflowState = useCallback(async () => {
    try {
      const ws = await api.workflow.getState(id);
      setWorkflowState(ws);
    } catch {
      // 워크플로 미시작 시 무시
    }
  }, [id]);

  const statusStr = status?.status;
  useEffect(() => {
    fetchWorkflowState();
    // 처리 중이면 5초마다 폴링
    const running = statusStr === "processing" || statusStr === "initialized" || statusStr === "running";
    if (running) {
      const t = setInterval(fetchWorkflowState, 5000);
      return () => clearInterval(t);
    }
  }, [fetchWorkflowState, statusStr]);

  // 버전 목록
  const fetchVersions = useCallback(async () => {
    try {
      const res = await (api.proposals as any).versions(id);
      setVersions(res ?? []);
    } catch {
      // 아직 API 미구현 시 무시
    }
  }, [id]);

  useEffect(() => {
    fetchVersions();
  }, [fetchVersions]);

  // result 데이터 (완료 시) — LangGraph artifacts API 사용
  useEffect(() => {
    if (status?.status === "completed") {
      api.artifacts.get(id, "proposal").then((r) => {
        setResultData(r as any);
      }).catch(() => {});
    }
  }, [id, status?.status]);

  // 비교 버전 result 로드
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

  // 드롭다운 외부 클릭 닫기
  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (versionRef.current && !versionRef.current.contains(e.target as Node)) {
        setVersionOpen(false);
      }
    }
    if (versionOpen) document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [versionOpen]);

  // ── 댓글 ──────────────────────────────────────────────────────────

  const fetchComments = useCallback(async () => {
    try {
      const res = await api.comments.list(id);
      setComments(res.comments);
    } catch {}
  }, [id]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

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

  // ── 수주결과 ───────────────────────────────────────────────────────

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

  // ── Phase 재시작 ───────────────────────────────────────────────────

  async function handleRetryFromPhase(phaseN: number) {
    try {
      const res = await (api.proposals as any).retryFromPhase(id, phaseN);
      if (res?.proposal_id) router.push(`/proposals/${res.proposal_id}`);
    } catch (e) {
      alert(e instanceof Error ? e.message : "재시작 실패");
    }
  }

  // ── 새 버전 ────────────────────────────────────────────────────────

  async function handleNewVersion() {
    setVersionOpen(false);
    try {
      const res = await (api.proposals as any).newVersion(id);
      if (res?.proposal_id) router.push(`/proposals/${res.proposal_id}`);
    } catch (e) {
      alert(e instanceof Error ? e.message : "새 버전 생성 실패");
    }
  }

  // ── 다운로드 URL ───────────────────────────────────────────────────

  // C-1 fix: fetch + blob 다운로드 (토큰을 URL에 노출하지 않음)
  async function handleDownload(type: "docx" | "pptx" | "hwpx") {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}/proposals/${id}/download/${type}`,
        { headers: { Authorization: `Bearer ${downloadToken}` } },
      );
      if (!res.ok) throw new Error("다운로드 실패");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `proposal-${id}.${type}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(e instanceof Error ? e.message : "다운로드 실패");
    }
  }

  // ── 버전 라벨 계산 ─────────────────────────────────────────────────

  function versionLabel(idx: number) {
    return `v${idx + 1}`;
  }

  function currentVersionLabel() {
    const idx = versions.findIndex((v) => v.id === id);
    if (idx === -1) return versions.length > 0 ? `v${versions.length}` : "v1";
    return versionLabel(idx);
  }

  // ── SSE 스트림 + 산출물 뷰어 + 로그 ──────────────────────────────

  const isRunning = !!status && (status.status === "processing" || status.status === "initialized" || status.status === "running");
  const { events: streamEvents, nodeProgress, isStreaming, currentNode } = useWorkflowStream(id, isRunning);
  const [selectedStep, setSelectedStep] = useState<number | null>(null);
  const [logCollapsed, setLogCollapsed] = useState(true);
  const [aborting, setAborting] = useState(false);

  // 중단
  async function handleAbort() {
    setAborting(true);
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}/proposals/${id}/ai-abort`,
        { method: "POST", headers: { Authorization: `Bearer ${downloadToken}` } },
      );
      fetchWorkflowState();
    } catch { /* ignore */ }
    finally { setAborting(false); }
  }

  // 재시도
  async function handleRetry() {
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}/proposals/${id}/ai-retry`,
        { method: "POST", headers: { Authorization: `Bearer ${downloadToken}` } },
      );
      fetchWorkflowState();
    } catch { /* ignore */ }
  }

  // 타임트래블
  async function handleGoto(step: string) {
    try {
      await api.workflow.goto(id, step);
      fetchWorkflowState();
      setSelectedStep(null);
    } catch (e) {
      alert(e instanceof Error ? e.message : "복원 실패");
    }
  }

  // ── 로딩 (훅은 모두 위에서 호출 후 여기서 early return) ───────────

  const isProcessing = isRunning;
  const isCompleted = status?.status === "completed";
  const isFailed = status?.status === "failed";
  const isPaused = status?.status === "cancelled" && workflowState?.has_pending_interrupt === false;
  const progressPct = Math.round(((status?.phases_completed ?? 0) / 5) * 100);
  const failedPhaseN = (status?.phases_completed ?? 0) + 1;
  const elapsed = useElapsedTime(isProcessing);

  if (loading || !status) {
    return (
      <div className="min-h-screen bg-[#0f0f0f] flex items-center justify-center text-[#8c8c8c] text-sm">
        불러오는 중...
      </div>
    );
  }

  // ── 렌더 ──────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-[#ededed]">

      {/* ── 헤더 ── */}
      <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 sticky top-0 z-20">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <Link
            href="/proposals"
            className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors shrink-0"
          >
            ← 목록
          </Link>

          <h1 className="text-sm font-semibold text-[#ededed] truncate flex-1 min-w-0">
            {status.rfp_title || "제안서"}
          </h1>

          <StatusBadge status={status.status} />

          {/* 버전 드롭다운 */}
          <div className="relative shrink-0" ref={versionRef}>
            <button
              onClick={() => setVersionOpen((o) => !o)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1c1c1c] border border-[#262626] text-xs text-[#ededed] hover:border-[#3ecf8e]/40 transition-colors"
            >
              {currentVersionLabel()}
              <svg className={`w-3 h-3 text-[#8c8c8c] transition-transform ${versionOpen ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {versionOpen && (
              <div className="absolute right-0 mt-1.5 w-40 bg-[#1c1c1c] border border-[#262626] rounded-xl shadow-xl overflow-hidden z-30">
                <div className="py-1">
                  {versions.length === 0 && (
                    <p className="px-3 py-2 text-xs text-[#8c8c8c]">버전 없음</p>
                  )}
                  {versions.map((v, idx) => (
                    <button
                      key={v.id}
                      onClick={() => {
                        setVersionOpen(false);
                        router.push(`/proposals/${v.id}`);
                      }}
                      className={`w-full text-left px-3 py-2 text-xs transition-colors ${
                        v.id === id
                          ? "text-[#3ecf8e] bg-[#3ecf8e]/10"
                          : "text-[#ededed] hover:bg-[#262626]"
                      }`}
                    >
                      {versionLabel(idx)}
                      {v.id === id && (
                        <span className="ml-1 text-[#8c8c8c]">(현재)</span>
                      )}
                    </button>
                  ))}
                </div>
                <div className="border-t border-[#262626]">
                  <button
                    onClick={handleNewVersion}
                    className="w-full text-left px-3 py-2 text-xs text-[#3ecf8e] hover:bg-[#3ecf8e]/10 transition-colors"
                  >
                    + 새 버전
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-6 space-y-5">

        {/* ── 워크플로 그래프 (§13-1-1, v2: 클릭 확장) ── */}
        <PhaseGraph
          workflowState={workflowState}
          nodeProgress={nodeProgress}
          currentNode={currentNode}
          selectedStep={selectedStep}
          onStepClick={(idx) => setSelectedStep(selectedStep === idx ? null : idx)}
        />

        {/* ── STEP별 산출물 뷰어 ── */}
        {selectedStep !== null && (
          <StepArtifactViewer
            proposalId={id}
            stepIndex={selectedStep}
            onGoto={handleGoto}
          />
        )}

        {/* ── 워크플로 패널: Go/No-Go + 리뷰 + 병렬 진행 (§13-4, §13-5, §13-7) ── */}
        <WorkflowPanel
          proposalId={id}
          workflowState={workflowState}
          onStateChange={fetchWorkflowState}
        />

        {/* 일시정지 상태 */}
        {isPaused && (
          <div className="flex items-center justify-between bg-[#1c1c1c] rounded-2xl border border-amber-500/30 px-5 py-3">
            <div className="flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <span className="text-xs text-amber-400">일시정지됨</span>
              <span className="text-[10px] text-[#8c8c8c]">
                현재 단계: {workflowState?.current_step || "알 수 없음"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleRetry}
                className="text-xs text-[#3ecf8e] hover:text-[#49e59e] border border-[#3ecf8e]/30 rounded-lg px-3 py-1.5 font-medium transition-colors"
              >
                재개
              </button>
              {selectedStep === null && (
                <button
                  onClick={() => setSelectedStep(
                    Math.max(0, (status?.phases_completed ?? 1) - 1)
                  )}
                  className="text-xs text-amber-400 hover:text-amber-300 border border-amber-500/30 rounded-lg px-3 py-1.5 transition-colors"
                >
                  산출물 확인
                </button>
              )}
            </div>
          </div>
        )}

        {/* 경과 시간 + 중단/재개/실패 */}
        {(isProcessing || isFailed) && (
          <div className="flex items-center justify-between bg-[#1c1c1c] rounded-2xl border border-[#262626] px-5 py-3">
            <div className="flex items-center gap-3">
              {isProcessing && (
                <>
                  <div className="w-3 h-3 rounded-full border-2 border-[#3ecf8e] border-t-transparent animate-spin" />
                  <span className="text-xs text-[#8c8c8c]">경과 {elapsed}</span>
                  {currentNode && (
                    <span className="text-[10px] text-[#3ecf8e]/80">
                      {currentNode}
                    </span>
                  )}
                </>
              )}
              {isFailed && (
                <span className="text-xs text-red-400">{status.error || "처리 중 오류 발생"}</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {isProcessing && (
                <button
                  onClick={handleAbort}
                  disabled={aborting}
                  className="text-xs text-amber-400 hover:text-amber-300 border border-amber-500/30 rounded-lg px-2.5 py-1 transition-colors disabled:opacity-40"
                >
                  {aborting ? "중단 중..." : "일시정지"}
                </button>
              )}
              {isFailed && (
                <>
                  <button
                    onClick={handleRetry}
                    className="text-xs text-[#3ecf8e] hover:text-[#49e59e] border border-[#3ecf8e]/30 rounded-lg px-2.5 py-1 transition-colors"
                  >
                    재시도
                  </button>
                  <button
                    onClick={() => handleRetryFromPhase(failedPhaseN)}
                    className="text-xs text-red-400 hover:text-red-300 border border-red-500/30 rounded-lg px-2.5 py-1 transition-colors"
                  >
                    Phase {failedPhaseN}부터 재시작
                  </button>
                </>
              )}
            </div>
          </div>
        )}

        {/* ── 탭 네비게이션 ── */}
        <div className="border-b border-[#262626]">
          <div className="flex">
            {(
              [
                { key: "result" as Tab, label: "결과물" },
                { key: "comments" as Tab, label: `댓글 ${comments.length > 0 ? `(${comments.length})` : ""}` },
                { key: "win" as Tab, label: "수주결과" },
                { key: "compare" as Tab, label: "버전 비교" },
                { key: "qa" as Tab, label: "Q&A" },
              ] as const
            ).map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
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

        {/* ── 탭: 결과물 ── */}
        {activeTab === "result" && (
          <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
            <h2 className="text-sm font-semibold text-[#ededed] mb-4">생성 결과물</h2>

            {isCompleted && (
              <div className="flex flex-col gap-2.5">
                <button
                  onClick={() => handleDownload("docx")}
                  className="flex items-center gap-3 px-4 py-3 bg-[#111111] hover:bg-[#262626] border border-[#262626] hover:border-blue-500/40 rounded-xl text-sm font-medium text-[#ededed] transition-colors group w-full text-left"
                >
                  <span className="w-9 h-9 rounded-lg bg-blue-500/15 text-blue-400 flex items-center justify-center text-base shrink-0">
                    📄
                  </span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-[#ededed]">DOCX 다운로드</p>
                    <p className="text-xs text-[#8c8c8c]">Word 제안서 문서</p>
                  </div>
                  <svg className="w-4 h-4 text-[#8c8c8c] group-hover:text-[#ededed] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </button>

                <button
                  onClick={() => handleDownload("pptx")}
                  className="flex items-center gap-3 px-4 py-3 bg-[#111111] hover:bg-[#262626] border border-[#262626] hover:border-indigo-500/40 rounded-xl text-sm font-medium text-[#ededed] transition-colors group w-full text-left"
                >
                  <span className="w-9 h-9 rounded-lg bg-indigo-500/15 text-indigo-400 flex items-center justify-center text-base shrink-0">
                    📊
                  </span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-[#ededed]">PPTX 다운로드</p>
                    <p className="text-xs text-[#8c8c8c]">PowerPoint 요약본</p>
                  </div>
                  <svg className="w-4 h-4 text-[#8c8c8c] group-hover:text-[#ededed] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </button>

                {((resultData as any)?.hwpx_path) && (
                  <button
                    onClick={() => handleDownload("hwpx")}
                    className="flex items-center gap-3 px-4 py-3 bg-[#111111] hover:bg-[#262626] border border-[#262626] hover:border-[#3ecf8e]/40 rounded-xl text-sm font-medium text-[#ededed] transition-colors group w-full text-left"
                  >
                    <span className="w-9 h-9 rounded-lg bg-[#3ecf8e]/15 text-[#3ecf8e] flex items-center justify-center text-base shrink-0">
                      📝
                    </span>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-[#ededed]">HWPX 다운로드</p>
                      <p className="text-xs text-[#8c8c8c]">한글 문서</p>
                    </div>
                    <svg className="w-4 h-4 text-[#8c8c8c] group-hover:text-[#ededed] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </button>
                )}
              </div>
            )}

            {isProcessing && (
              <div className="flex flex-col items-center justify-center py-10 gap-4 text-[#8c8c8c]">
                <div className="relative w-12 h-12">
                  <div className="absolute inset-0 rounded-full border-2 border-[#262626]" />
                  <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#3ecf8e] animate-spin" />
                  <div className="absolute inset-2 rounded-full border border-[#3ecf8e]/20 animate-ping" />
                </div>
                <div className="text-center">
                  <p className="text-sm text-[#ededed] font-medium">
                    Phase {status.phases_completed + 1}/5 — {
                      ["RFP 분석", "경쟁 분석", "전략 수립", "본문 작성", "품질 검증"][status.phases_completed] ?? "처리"
                    }
                  </p>
                  <p className="text-xs text-[#8c8c8c] mt-1">Claude AI가 제안서를 작성하는 중입니다</p>
                  <p className="text-xs text-[#5c5c5c] mt-0.5">경과 시간: {elapsed}</p>
                </div>
                <p className="text-[11px] text-[#5c5c5c]">5~15분 소요됩니다. 페이지를 닫아도 작업은 계속됩니다.</p>
              </div>
            )}

            {isFailed && (
              <div className="py-6 text-center">
                <p className="text-sm font-medium text-red-400 mb-1">생성 실패</p>
                {status.error && (
                  <p className="text-xs text-[#8c8c8c] mb-4 max-w-sm mx-auto">{status.error}</p>
                )}
                <button
                  onClick={() => handleRetryFromPhase(failedPhaseN)}
                  className="px-4 py-2 bg-red-500/15 hover:bg-red-500/25 text-red-400 text-sm font-medium rounded-lg border border-red-500/30 transition-colors"
                >
                  Phase {failedPhaseN}부터 재시작
                </button>
              </div>
            )}
          </section>
        )}

        {/* ── 탭: 댓글 ── */}
        {activeTab === "comments" && (
          <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
            <h2 className="text-sm font-semibold text-[#ededed] mb-4">
              댓글{" "}
              <span className="text-[#8c8c8c] font-normal">({comments.length})</span>
            </h2>

            {comments.length === 0 ? (
              <p className="text-sm text-[#8c8c8c] mb-4">아직 댓글이 없습니다.</p>
            ) : (
              <ul className="space-y-3 mb-4">
                {comments.map((c) => (
                  <li key={c.id} className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-[#262626] shrink-0 flex items-center justify-center text-xs text-[#8c8c8c] font-medium">
                      {c.user_id.slice(0, 2).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-[#ededed] leading-relaxed break-words">{c.content}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs text-[#8c8c8c]">
                          {new Date(c.created_at).toLocaleString("ko-KR")}
                        </span>
                        {c.user_id === currentUserId && (
                          <button
                            onClick={() => handleDeleteComment(c.id)}
                            className="text-xs text-red-400/70 hover:text-red-400 transition-colors"
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
                className="flex-1 bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#8c8c8c] focus:outline-none focus:ring-2 focus:ring-[#3ecf8e]/40 focus:border-[#3ecf8e]/50 transition-colors"
              />
              <button
                type="submit"
                disabled={submittingComment || !newComment.trim()}
                className="bg-[#3ecf8e] hover:bg-[#3ecf8e]/90 disabled:opacity-40 text-[#0f0f0f] text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
              >
                등록
              </button>
            </form>
          </section>
        )}

        {/* ── 탭: 수주결과 ── */}
        {activeTab === "win" && (
          <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
            <h2 className="text-sm font-semibold text-[#ededed] mb-4">수주결과 기록</h2>

            {winSaved && (
              <div className="mb-4 bg-[#3ecf8e]/10 border border-[#3ecf8e]/20 rounded-lg px-3 py-2">
                <p className="text-sm text-[#3ecf8e]">저장되었습니다.</p>
              </div>
            )}

            <div className="space-y-3">
              {/* 결과 선택 버튼 */}
              <div className="flex gap-2">
                {(
                  [
                    { value: "won", label: "수주", activeClass: "bg-[#3ecf8e]/15 text-[#3ecf8e] border-[#3ecf8e]/50" },
                    { value: "lost", label: "낙찰실패", activeClass: "bg-red-500/15 text-red-400 border-red-500/50" },
                    { value: "pending", label: "결과대기", activeClass: "bg-[#262626] text-[#8c8c8c] border-[#8c8c8c]/30" },
                  ] as const
                ).map(({ value, label, activeClass }) => (
                  <button
                    key={value}
                    onClick={() => {
                      setWinForm((f) => ({ ...f, win_result: value }));
                      setWinSaved(false);
                    }}
                    className={`flex-1 py-2 text-sm font-medium rounded-lg border transition-colors ${
                      winForm.win_result === value
                        ? activeClass
                        : "border-[#262626] text-[#8c8c8c] hover:border-[#8c8c8c]/40 hover:text-[#ededed]"
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
                className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#8c8c8c] focus:outline-none focus:ring-2 focus:ring-[#3ecf8e]/40 focus:border-[#3ecf8e]/50 transition-colors"
              />

              <textarea
                value={winForm.notes}
                onChange={(e) => setWinForm((f) => ({ ...f, notes: e.target.value }))}
                placeholder="비고 (선택)"
                rows={3}
                className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-sm text-[#ededed] placeholder-[#8c8c8c] focus:outline-none focus:ring-2 focus:ring-[#3ecf8e]/40 focus:border-[#3ecf8e]/50 resize-none transition-colors"
              />

              <button
                onClick={handleSaveWinResult}
                disabled={!winForm.win_result}
                className="w-full bg-[#3ecf8e] hover:bg-[#3ecf8e]/90 disabled:opacity-40 text-[#0f0f0f] font-semibold rounded-lg py-2.5 text-sm transition-colors"
              >
                저장
              </button>
            </div>
          </section>
        )}

        {/* ── 탭: 버전 비교 ── */}
        {activeTab === "compare" && (
          <section className="space-y-4">
            {/* 패널 헤더 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 좌측: 현재 버전 */}
              <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4">
                <p className="text-xs font-semibold text-[#ededed] mb-1">
                  현재 버전 {currentVersionLabel()}
                </p>
                <p className="text-[11px] text-[#8c8c8c] truncate">
                  {status.rfp_title || "제안서"}
                </p>
              </div>

              {/* 우측: 비교 버전 선택 */}
              <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4">
                <p className="text-xs font-semibold text-[#ededed] mb-2">비교 버전 선택</p>
                <select
                  value={compareVersionId ?? ""}
                  onChange={(e) => setCompareVersionId(e.target.value || null)}
                  className="w-full bg-[#111111] border border-[#262626] rounded-lg px-2.5 py-1.5 text-xs text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] focus:border-[#3ecf8e] transition-colors"
                >
                  <option value="">버전 선택...</option>
                  {versions
                    .filter((v) => v.id !== id)
                    .map((v, idx) => {
                      const allIdx = versions.findIndex((x) => x.id === v.id);
                      return (
                        <option key={v.id} value={v.id}>
                          {versionLabel(allIdx !== -1 ? allIdx : idx)}
                        </option>
                      );
                    })}
                </select>
              </div>
            </div>

            {/* Phase 탭 선택 */}
            <div className="flex gap-1">
              {PHASES.map((p) => (
                <button
                  key={p.n}
                  onClick={() => setComparePhase(p.n)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                    comparePhase === p.n
                      ? "bg-[#3ecf8e]/15 text-[#3ecf8e] border-[#3ecf8e]/40"
                      : "border-[#262626] text-[#8c8c8c] hover:border-[#3c3c3c] hover:text-[#ededed]"
                  }`}
                >
                  {p.name}
                </button>
              ))}
            </div>

            {/* 비교 콘텐츠 패널 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 좌측: 현재 버전 결과 */}
              <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4 min-h-[300px]">
                <p className="text-[11px] font-semibold text-[#8c8c8c] uppercase tracking-wider mb-3">
                  {currentVersionLabel()} — Phase {comparePhase}
                </p>
                {(resultData as any)?.artifacts?.[`phase_${comparePhase}`] ||
                 (resultData as any)?.artifacts?.[comparePhase] ||
                 (resultData as any)?.[`phase_${comparePhase}_result`] ? (
                  <pre className="text-xs text-[#ededed] whitespace-pre-wrap break-words leading-relaxed font-sans">
                    {String(
                      (resultData as any)?.artifacts?.[`phase_${comparePhase}`] ??
                      (resultData as any)?.artifacts?.[comparePhase] ??
                      (resultData as any)?.[`phase_${comparePhase}_result`] ??
                      ""
                    )}
                  </pre>
                ) : (
                  <p className="text-xs text-[#8c8c8c]">
                    {status.status !== "completed"
                      ? "제안서 생성이 완료되지 않았습니다."
                      : `Phase ${comparePhase} 결과가 없습니다.`}
                  </p>
                )}
              </div>

              {/* 우측: 비교 버전 결과 */}
              <div className="bg-[#1c1c1c] border border-[#262626] rounded-xl p-4 min-h-[300px]">
                {!compareVersionId ? (
                  <div className="flex items-center justify-center h-full min-h-[200px]">
                    <p className="text-xs text-[#8c8c8c] text-center">
                      비교할 버전을 선택하세요
                    </p>
                  </div>
                ) : compareLoading ? (
                  <div className="flex items-center justify-center h-full min-h-[200px]">
                    <div className="w-5 h-5 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin" />
                  </div>
                ) : (
                  <>
                    <p className="text-[11px] font-semibold text-[#8c8c8c] uppercase tracking-wider mb-3">
                      {versionLabel(versions.findIndex((v) => v.id === compareVersionId))} — Phase {comparePhase}
                    </p>
                    {compareData &&
                    ((compareData as any)?.artifacts?.[`phase_${comparePhase}`] ||
                     (compareData as any)?.artifacts?.[comparePhase] ||
                     (compareData as any)?.[`phase_${comparePhase}_result`]) ? (
                      <pre className="text-xs text-[#ededed] whitespace-pre-wrap break-words leading-relaxed font-sans">
                        {String(
                          (compareData as any)?.artifacts?.[`phase_${comparePhase}`] ??
                          (compareData as any)?.artifacts?.[comparePhase] ??
                          (compareData as any)?.[`phase_${comparePhase}_result`] ??
                          ""
                        )}
                      </pre>
                    ) : (
                      <p className="text-xs text-[#8c8c8c]">
                        {!compareData
                          ? "데이터를 불러올 수 없습니다."
                          : `Phase ${comparePhase} 결과가 없습니다.`}
                      </p>
                    )}
                  </>
                )}
              </div>
            </div>
          </section>
        )}

        {/* ── 탭: Q&A (PSM-16) ── */}
        {activeTab === "qa" && (
          <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
            <QaPanel proposalId={id} />
          </section>
        )}

        {/* ── 실시간 로그 패널 ── */}
        {(isProcessing || streamEvents.length > 0) && (
          <WorkflowLogPanel
            events={streamEvents}
            isStreaming={isStreaming}
            collapsed={logCollapsed}
            onToggle={() => setLogCollapsed(!logCollapsed)}
          />
        )}

      </main>
    </div>
  );
}
