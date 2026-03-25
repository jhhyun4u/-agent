"use client";

/**
 * 제안서 상세 페이지 — 3-Panel 레이아웃
 * 중앙: 워크플로 (DetailCenterPanel)
 * 우측: 산출물+탭 (DetailRightPanel, 토글 가능)
 * 좌측 AppSidebar는 proposals/layout.tsx에서 제공
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, Comment_, ProposalFile, ProposalSummary, streamsApi, type StreamProgress, type WorkflowState } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import { usePhaseStatus } from "@/lib/hooks/usePhaseStatus";
import { useWorkflowStream } from "@/lib/hooks/useWorkflowStream";
import DetailCenterPanel from "@/components/DetailCenterPanel";
import DetailRightPanel from "@/components/DetailRightPanel";
import StepArtifactViewer from "@/components/StepArtifactViewer";
import StreamProgressHeader from "@/components/StreamProgressHeader";
import StreamTabBar, { type StreamTab } from "@/components/StreamTabBar";
import SubmissionDocsPanel from "@/components/SubmissionDocsPanel";
import BiddingWorkspace from "@/components/BiddingWorkspace";
import StreamDashboard from "@/components/StreamDashboard";
import WorkflowResumeBanner from "@/components/WorkflowResumeBanner";
import GuidedTour, { TOUR_PROPOSAL_DETAIL } from "@/components/GuidedTour";
import ProjectArchivePanel from "@/components/ProjectArchivePanel";

// ── 경과 시간 훅 ──
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

// ── 상태 배지 ──
const STATUS_BADGE_MAP: Record<string, { label: string; bg: string; text: string; border: string; pulse?: boolean }> = {
  processing:  { label: "진행중", bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30", pulse: true },
  initialized: { label: "대기중", bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30" },
  running:     { label: "진행중", bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30", pulse: true },
  searching:   { label: "진행중", bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30", pulse: true },
  analyzing:   { label: "진행중", bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30", pulse: true },
  strategizing:{ label: "진행중", bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30", pulse: true },
  completed:   { label: "완료",   bg: "bg-[#3ecf8e]/15", text: "text-[#3ecf8e]", border: "border-[#3ecf8e]/30" },
  won:         { label: "수주",   bg: "bg-[#3ecf8e]/15", text: "text-[#3ecf8e]", border: "border-[#3ecf8e]/30" },
  lost:        { label: "패찰",   bg: "bg-red-500/15", text: "text-red-400", border: "border-red-500/30" },
  submitted:   { label: "결과대기", bg: "bg-purple-500/15", text: "text-purple-400", border: "border-purple-500/30" },
  presented:   { label: "결과대기", bg: "bg-purple-500/15", text: "text-purple-400", border: "border-purple-500/30" },
  on_hold:     { label: "중단",   bg: "bg-orange-500/15", text: "text-orange-400", border: "border-orange-500/30" },
  abandoned:   { label: "포기",   bg: "bg-red-500/15", text: "text-red-400", border: "border-red-500/30" },
  no_go:       { label: "No-Go",  bg: "bg-red-500/15", text: "text-red-300", border: "border-red-500/30" },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_BADGE_MAP[status] ?? { label: status, bg: "bg-[#262626]", text: "text-[#8c8c8c]", border: "border-[#262626]" };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.bg} ${cfg.text} border ${cfg.border} ${cfg.pulse ? "animate-pulse" : ""}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.text.replace("text-", "bg-")}`} />
      {cfg.label}
    </span>
  );
}

// ── HITL 리뷰 게이트 라벨 ──
const REVIEW_LABELS: Record<string, string> = {
  review_search: "공고 검색 결과 검토",
  review_rfp: "RFP 분석 결과 검토",
  review_gng: "Go/No-Go 의사결정",
  review_strategy: "제안전략 검토",
  review_bid_plan: "입찰가격 계획 검토",
  review_plan: "제안계획서 검토",
  review_section: "섹션별 검토",
  review_proposal: "제안서 최종 검토",
  review_ppt: "PPT 검토",
};

// ── 메인 페이지 ──
export default function ProposalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { status, loading } = usePhaseStatus(id);

  // 3-Stream 탭
  const [activeTab, setActiveTab] = useState<StreamTab>("proposal");
  const [streamsData, setStreamsData] = useState<StreamProgress[]>([]);

  // 우측 패널 토글 + 리사이즈
  const [rightPanelOpen, setRightPanelOpen] = useState(true);
  const [rightPanelWidth, setRightPanelWidth] = useState(420);
  const resizingRef = useRef(false);

  // 우측 패널 리사이즈 핸들러
  function handleResizeStart(e: React.MouseEvent) {
    e.preventDefault();
    resizingRef.current = true;
    const startX = e.clientX;
    const startW = rightPanelWidth;

    function onMove(ev: MouseEvent) {
      if (!resizingRef.current) return;
      const delta = startX - ev.clientX; // 왼쪽으로 드래그 = 너비 증가
      const newW = Math.max(300, Math.min(800, startW + delta));
      setRightPanelWidth(newW);
    }
    function onUp() {
      resizingRef.current = false;
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    }
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }

  // 버전 드롭다운
  const [versions, setVersions] = useState<ProposalSummary[]>([]);
  const [versionOpen, setVersionOpen] = useState(false);
  const versionRef = useRef<HTMLDivElement>(null);

  // 댓글
  const [comments, setComments] = useState<Comment_[]>([]);
  const [currentUserId, setCurrentUserId] = useState("");

  // 파일
  const [files, setFiles] = useState<ProposalFile[]>([]);
  const [filesLoading, setFilesLoading] = useState(false);

  // 워크플로
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);
  const [downloadToken, setDownloadToken] = useState("");
  const [resultData, setResultData] = useState<Record<string, unknown> | null>(null);

  // SSE + 산출물
  const isRunning = !!status && (status.status === "processing" || status.status === "initialized" || status.status === "running");
  const { events: streamEvents, nodeProgress, isStreaming, currentNode } = useWorkflowStream(id, isRunning);
  const [selectedStep, setSelectedStep] = useState<number | null>(null);
  const [aborting, setAborting] = useState(false);
  const [starting, setStarting] = useState(false);

  const isProcessing = isRunning;
  const isCompleted = status?.status === "completed";
  const isFailed = status?.status === "failed";
  const isPaused = status?.status === "cancelled" && workflowState?.has_pending_interrupt === false;
  const elapsed = useElapsedTime(isProcessing);

  // HITL 리뷰 대기 감지
  const pendingReviewNode = workflowState?.has_pending_interrupt
    ? workflowState.next_nodes.find((n) => REVIEW_LABELS[n])
    : null;
  const pendingReviewLabel = pendingReviewNode ? REVIEW_LABELS[pendingReviewNode] : null;

  // W17: 리뷰 대기 시 우측 패널에 해당 STEP 산출물 자동 선택
  useEffect(() => {
    if (!pendingReviewNode) return;
    const reviewStepMap: Record<string, number> = {
      review_search: 0, review_rfp: 0, review_gng: 0,
      review_strategy: 1, review_bid_plan: 2,
      review_plan: 3, review_section: 4, review_proposal: 4,
      review_ppt: 5,
    };
    const stepIdx = reviewStepMap[pendingReviewNode];
    if (stepIdx !== undefined && selectedStep !== stepIdx) {
      setSelectedStep(stepIdx);
    }
  }, [pendingReviewNode]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── 초기 데이터 로드 ──
  useEffect(() => {
    createClient().auth.getUser().then(({ data }) => setCurrentUserId(data.user?.id ?? ""));
    createClient().auth.getSession().then(({ data }) => setDownloadToken(data.session?.access_token ?? ""));
  }, []);

  // 3-Stream 상태 폴링
  const fetchStreams = useCallback(async () => {
    try {
      const res = await streamsApi.getAll(id);
      setStreamsData(res.streams as StreamProgress[]);
    } catch { /* 스트림 미초기화 */ }
  }, [id]);

  // 워크플로 상태 폴링
  const fetchWorkflowState = useCallback(async () => {
    try { setWorkflowState(await api.workflow.getState(id)); } catch { /* 미시작 */ }
  }, [id]);

  const statusStr = status?.status;
  useEffect(() => {
    fetchWorkflowState();
    fetchStreams();
    const running = statusStr === "processing" || statusStr === "initialized" || statusStr === "running";
    if (running) {
      const t = setInterval(() => { fetchWorkflowState(); fetchStreams(); }, 5000);
      return () => clearInterval(t);
    }
    // 비실행 상태에서도 스트림 30초 폴링
    const st = setInterval(fetchStreams, 30000);
    return () => clearInterval(st);
  }, [fetchWorkflowState, fetchStreams, statusStr]);

  // BroadcastChannel — 편집 창에서 저장 시 새로고침
  useEffect(() => {
    const channel = new BroadcastChannel(`tenopa-proposal-${id}`);
    channel.onmessage = (ev) => {
      if (ev.data?.type === "saved") fetchWorkflowState();
    };
    return () => channel.close();
  }, [id, fetchWorkflowState]);

  // 버전 목록
  const fetchVersions = useCallback(async () => {
    try { setVersions((await (api.proposals as any).versions(id)) ?? []); } catch { /* 미구현 */ }
  }, [id]);
  useEffect(() => { fetchVersions(); }, [fetchVersions]);

  // 결과 데이터
  useEffect(() => {
    if (status?.status === "completed") {
      api.artifacts.get(id, "proposal").then((r) => setResultData(r as any)).catch(() => {});
    }
  }, [id, status?.status]);

  // 댓글
  const fetchComments = useCallback(async () => {
    try { setComments((await api.comments.list(id)).comments); } catch {}
  }, [id]);
  useEffect(() => { fetchComments(); }, [fetchComments]);

  // 파일
  const fetchFiles = useCallback(async () => {
    setFilesLoading(true);
    try { setFiles((await api.proposals.listFiles(id)).files); } catch {}
    finally { setFilesLoading(false); }
  }, [id]);
  useEffect(() => { fetchFiles(); }, [fetchFiles]);

  // 드롭다운 외부 클릭
  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (versionRef.current && !versionRef.current.contains(e.target as Node)) setVersionOpen(false);
    }
    if (versionOpen) document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [versionOpen]);

  // ── 액션 핸들러 ──
  async function handleStartWorkflow() {
    setStarting(true);
    try {
      await api.workflow.start(id);
      fetchWorkflowState();
    } catch (e) {
      alert(e instanceof Error ? e.message : "워크플로 시작 실패");
    } finally {
      setStarting(false);
    }
  }

  async function handleRetryFromPhase(phaseN: number) {
    try {
      const res = await (api.proposals as any).retryFromPhase(id, phaseN);
      if (res?.proposal_id) router.push(`/proposals/${res.proposal_id}`);
    } catch (e) { alert(e instanceof Error ? e.message : "재시작 실패"); }
  }

  async function handleNewVersion() {
    setVersionOpen(false);
    try {
      const res = await (api.proposals as any).newVersion(id);
      if (res?.proposal_id) router.push(`/proposals/${res.proposal_id}`);
    } catch (e) { alert(e instanceof Error ? e.message : "새 버전 생성 실패"); }
  }

  async function handleAbort() {
    setAborting(true);
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}/proposals/${id}/ai-abort`,
        { method: "POST", headers: { Authorization: `Bearer ${downloadToken}` } },
      );
      fetchWorkflowState();
    } catch {} finally { setAborting(false); }
  }

  async function handleRetry() {
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}/proposals/${id}/ai-retry`,
        { method: "POST", headers: { Authorization: `Bearer ${downloadToken}` } },
      );
      fetchWorkflowState();
    } catch {}
  }

  async function handleGoto(step: string) {
    try {
      await api.workflow.goto(id, step);
      fetchWorkflowState();
      setSelectedStep(null);
    } catch (e) { alert(e instanceof Error ? e.message : "복원 실패"); }
  }

  // ── 버전 라벨 ──
  function versionLabel(idx: number) { return `v${idx + 1}`; }
  function currentVersionLabel() {
    const idx = versions.findIndex((v) => v.id === id);
    if (idx === -1) return versions.length > 0 ? `v${versions.length}` : "v1";
    return versionLabel(idx);
  }

  // ── 로딩 ──
  if (loading || !status) {
    return (
      <div className="min-h-screen bg-[#0f0f0f] flex items-center justify-center text-[#8c8c8c] text-sm">
        불러오는 중...
      </div>
    );
  }

  // ── 렌더 ──
  return (
    <div className="h-screen flex flex-col overflow-hidden bg-[#0f0f0f] text-[#ededed]">
      {/* 헤더 */}
      <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 shrink-0 z-20">
        <div className="flex items-center gap-3">
          <Link
            href="/proposals"
            className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors shrink-0"
          >
            ← 목록
          </Link>

          <h1 className="text-sm font-semibold text-[#ededed] truncate flex-1 min-w-0">
            제안 작업 workflow
          </h1>

          <StatusBadge status={status.status} />

          {/* 3-Stream 진행 헤더 */}
          {streamsData.length > 0 && (
            <StreamProgressHeader
              streams={streamsData}
              onStreamClick={(stream) => {
                const tabMap: Record<string, StreamTab> = { proposal: "proposal", bidding: "bidding", documents: "documents" };
                setActiveTab(tabMap[stream] || "proposal");
              }}
            />
          )}

          {/* 전체 진행률 */}
          {!isCompleted && !isFailed && (
            <div className="flex items-center gap-2 shrink-0">
              <div className="w-20 h-1.5 bg-[#262626] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#3ecf8e] rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, ((status.phases_completed ?? 0) / 6) * 100)}%` }}
                />
              </div>
              <span className="text-[10px] text-[#8c8c8c]">
                {status.phases_completed ?? 0}/6
              </span>
            </div>
          )}

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
                  {versions.length === 0 && <p className="px-3 py-2 text-xs text-[#8c8c8c]">버전 없음</p>}
                  {versions.map((v, idx) => (
                    <button
                      key={v.id}
                      onClick={() => { setVersionOpen(false); router.push(`/proposals/${v.id}`); }}
                      className={`w-full text-left px-3 py-2 text-xs transition-colors ${
                        v.id === id ? "text-[#3ecf8e] bg-[#3ecf8e]/10" : "text-[#ededed] hover:bg-[#262626]"
                      }`}
                    >
                      {versionLabel(idx)}{v.id === id && <span className="ml-1 text-[#8c8c8c]">(현재)</span>}
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

          {/* 편집 버튼 — 별도 창 */}
          <button
            onClick={() => window.open(`/editor/${id}`, "_blank")}
            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#3ecf8e]/90 transition-colors shrink-0"
          >
            편집
          </button>

          {/* 우측 패널 토글 */}
          <button
            onClick={() => setRightPanelOpen((o) => !o)}
            className="p-1.5 rounded-lg text-[#8c8c8c] hover:text-[#ededed] hover:bg-[#262626] transition-colors shrink-0"
            title={rightPanelOpen ? "패널 접기" : "패널 펼치기"}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              {rightPanelOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" d="M11 19l-7-7 7-7M19 19l-7-7 7-7" />
              )}
            </svg>
          </button>
        </div>
      </header>

      {/* 워크플로 재진입 요약 배너 */}
      <WorkflowResumeBanner
        proposalId={id}
        proposalStatus={status.status}
        currentPhase={status.current_phase ?? null}
        workflowState={workflowState}
        onResumeWorkflow={handleStartWorkflow}
      />

      {/* HITL 리뷰 대기 배너 */}
      {pendingReviewLabel && (
        <div className="bg-amber-500/10 border-b border-amber-500/30 px-6 py-2.5 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
            <span className="text-xs font-medium text-amber-400">
              사용자 확인 필요: {pendingReviewLabel}
            </span>
          </div>
          <button
            onClick={() => document.getElementById("workflow-panel")?.scrollIntoView({ behavior: "smooth" })}
            className="text-xs text-amber-400 hover:text-amber-300 underline underline-offset-2 transition-colors"
          >
            아래에서 확인
          </button>
        </div>
      )}

      {/* 스트림 탭바 — Go 결정 이후(스트림 데이터 있을 때) 표시 */}
      {streamsData.length > 0 && (
        <StreamTabBar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          streams={streamsData}
        />
      )}

      {/* 3-Panel 본문 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 중앙 패널 */}
        <main className="flex-1 overflow-y-auto px-6 py-6">
          {/* 정성제안서 탭 (기본) — 기존 워크플로 UI */}
          {(activeTab === "proposal" || streamsData.length === 0) && (
          <div className="max-w-3xl mx-auto">
            <DetailCenterPanel
              proposalId={id}
              status={status.status}
              workflowState={workflowState}
              nodeProgress={nodeProgress}
              currentNode={currentNode}
              isStreaming={isStreaming}
              streamEvents={streamEvents}
              selectedStep={selectedStep}
              onStepClick={setSelectedStep}
              onStateChange={fetchWorkflowState}
              onStartWorkflow={handleStartWorkflow}
              isStarting={starting}
              isProcessing={isProcessing}
              isFailed={isFailed}
              isPaused={isPaused}
              elapsed={elapsed}
              phasesCompleted={status.phases_completed ?? 0}
              error={status.error}
              onAbort={handleAbort}
              onRetry={handleRetry}
              onRetryFromPhase={handleRetryFromPhase}
              aborting={aborting}
            />

            {/* STEP별 산출물 뷰어 (중앙에 표시 — 넓은 뷰 필요) */}
            {selectedStep !== null && (
              <div className="mt-5">
                <StepArtifactViewer
                  proposalId={id}
                  stepIndex={selectedStep}
                  onGoto={handleGoto}
                />
              </div>
            )}
          </div>
          )}

          {/* 비딩관리 탭 */}
          {activeTab === "bidding" && streamsData.length > 0 && (
            <BiddingWorkspace proposalId={id} />
          )}

          {/* 제출서류 탭 */}
          {activeTab === "documents" && streamsData.length > 0 && (
            <SubmissionDocsPanel proposalId={id} />
          )}

          {/* 통합현황 탭 */}
          {activeTab === "overview" && streamsData.length > 0 && (
            <StreamDashboard proposalId={id} deadline={status.current_phase} />
          )}

          {activeTab === "archive" && (
            <ProjectArchivePanel proposalId={id} className="p-4" />
          )}
        </main>

        {/* 우측 패널 — lg 이상 인라인 표시 + 리사이즈 */}
        {rightPanelOpen && (
          <div className="relative shrink-0 hidden lg:flex" style={{ width: rightPanelWidth }}>
            {/* 리사이즈 핸들 */}
            <div
              onMouseDown={handleResizeStart}
              className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize z-10 group hover:bg-[#3ecf8e]/30 active:bg-[#3ecf8e]/50 transition-colors"
            >
              <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-full bg-[#363636] group-hover:bg-[#3ecf8e] transition-colors" />
            </div>
          <aside className="flex-1 border-l border-[#262626] bg-[#111111] flex flex-col overflow-hidden">
            <DetailRightPanel
              proposalId={id}
              status={status.status}
              phasesCompleted={status.phases_completed ?? 0}
              error={status.error}
              rfpTitle={status.rfp_title}
              isProcessing={isProcessing}
              isCompleted={isCompleted}
              isFailed={isFailed}
              elapsed={elapsed}
              selectedStep={selectedStep}
              onGoto={handleGoto}
              downloadToken={downloadToken}
              versions={versions}
              currentVersionLabel={currentVersionLabel()}
              resultData={resultData}
              comments={comments}
              currentUserId={currentUserId}
              onFetchComments={fetchComments}
              files={files}
              filesLoading={filesLoading}
              onFetchFiles={fetchFiles}
              onRetryFromPhase={handleRetryFromPhase}
              workflowState={workflowState}
            />
          </aside>
          </div>
        )}
      </div>

      {/* 모바일 오버레이 (lg 미만) */}
      <div className={`lg:hidden fixed inset-0 z-40 ${rightPanelOpen ? "" : "hidden"}`}>
        <div className="absolute inset-0 bg-black/50" onClick={() => setRightPanelOpen(false)} />
        <aside className="absolute right-0 inset-y-0 w-[85vw] max-w-[420px] bg-[#111111] flex flex-col overflow-hidden">
          <DetailRightPanel
            proposalId={id}
            status={status.status}
            phasesCompleted={status.phases_completed ?? 0}
            error={status.error}
            rfpTitle={status.rfp_title}
            isProcessing={isProcessing}
            isCompleted={isCompleted}
            isFailed={isFailed}
            elapsed={elapsed}
            selectedStep={selectedStep}
            onGoto={handleGoto}
            downloadToken={downloadToken}
            versions={versions}
            currentVersionLabel={currentVersionLabel()}
            resultData={resultData}
            comments={comments}
            currentUserId={currentUserId}
            onFetchComments={fetchComments}
            files={files}
            filesLoading={filesLoading}
            onFetchFiles={fetchFiles}
            onRetryFromPhase={handleRetryFromPhase}
          />
        </aside>
      </div>

      {/* 권고 #2: 초보 사용자 가이드 투어 */}
      <GuidedTour tourId="proposal-detail" steps={TOUR_PROPOSAL_DETAIL} />

      {/* 모바일 플로팅 버튼 (lg 미만, 패널 닫혀있을 때) */}
      {!rightPanelOpen && (
        <button
          onClick={() => setRightPanelOpen(true)}
          className="lg:hidden fixed bottom-6 right-6 z-30 px-4 py-2.5 bg-[#3ecf8e] text-[#0f0f0f] text-xs font-semibold rounded-full shadow-lg hover:bg-[#3ecf8e]/90 transition-colors"
        >
          결과물
        </button>
      )}
    </div>
  );
}
