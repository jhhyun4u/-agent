"use client";

/**
 * 제안서 상세 페이지 — 3-Panel 레이아웃
 * 중앙: 워크플로 (DetailCenterPanel)
 * 우측: 산출물+탭 (DetailRightPanel, 토글 가능)
 * 좌측 AppSidebar는 proposals/layout.tsx에서 제공
 */

import { useCallback, useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { useParams, useRouter } from "next/navigation";
import {
  api,
  Comment_,
  ProposalFile,
  ProposalSummary,
  streamsApi,
  type StreamProgress,
  type WorkflowState,
} from "@/lib/api";
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
import ProjectContextHeader from "@/components/ProjectContextHeader";
import FileHubPanel from "@/components/FileHubPanel";
import ProjectDocumentsPanel from "@/components/ProjectDocumentsPanel";

// Lazy load STEP 8 Review Page
const Step8ReviewPage = dynamic(() => import("./step8-review/page"), {
  loading: () => (
    <div className="p-6 text-[#8c8c8c]">STEP 8 검토 로드 중...</div>
  ),
});

// ── 경과 시간 훅 ──
function useElapsedTime(running: boolean) {
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef(Date.now());
  useEffect(() => {
    if (!running) {
      setElapsed(0);
      startRef.current = Date.now();
      return;
    }
    startRef.current = Date.now();
    const t = setInterval(
      () => setElapsed(Math.floor((Date.now() - startRef.current) / 1000)),
      1000,
    );
    return () => clearInterval(t);
  }, [running]);
  const m = Math.floor(elapsed / 60),
    s = elapsed % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
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
  review_gap_analysis: "갭 분석 결과 검토",
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

  // 댓글
  const [comments, setComments] = useState<Comment_[]>([]);
  const [currentUserId, setCurrentUserId] = useState("");

  // 파일
  const [files, setFiles] = useState<ProposalFile[]>([]);
  const [filesLoading, setFilesLoading] = useState(false);

  // 워크플로
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(
    null,
  );
  const [downloadToken, setDownloadToken] = useState("");
  const [resultData, setResultData] = useState<Record<string, unknown> | null>(
    null,
  );

  // SSE + 산출물
  const isRunning =
    !!status &&
    (status.status === "processing" ||
      status.status === "initialized" ||
      status.status === "running");
  const {
    events: streamEvents,
    nodeProgress,
    isStreaming,
    currentNode,
  } = useWorkflowStream(id, isRunning);
  const [selectedStep, setSelectedStep] = useState<number | null>(null);
  const [aborting, setAborting] = useState(false);
  const [starting, setStarting] = useState(false);
  const [activeDocId, setActiveDocId] = useState<string | null>(null);

  const isProcessing = isRunning;
  const isCompleted = status?.status === "completed";
  const isFailed = status?.status === "failed";
  const isPaused =
    status?.status === "cancelled" &&
    workflowState?.has_pending_interrupt === false;
  const elapsed = useElapsedTime(isProcessing);

  // HITL 리뷰 대기 감지
  const pendingReviewNode = workflowState?.has_pending_interrupt
    ? workflowState.next_nodes.find((n) => REVIEW_LABELS[n])
    : null;
  const pendingReviewLabel = pendingReviewNode
    ? REVIEW_LABELS[pendingReviewNode]
    : null;

  // W17: 리뷰 대기 시 우측 패널에 해당 STEP 산출물 자동 선택
  useEffect(() => {
    if (!pendingReviewNode) return;
    const reviewStepMap: Record<string, number> = {
      review_search: 0,
      review_rfp: 0,
      review_gng: 0,
      review_strategy: 1,
      review_bid_plan: 2,
      review_plan: 3,
      review_section: 4,
      review_gap_analysis: 4,
      review_proposal: 4,
      review_ppt: 5,
    };
    const stepIdx = reviewStepMap[pendingReviewNode];
    if (stepIdx !== undefined && selectedStep !== stepIdx) {
      setSelectedStep(stepIdx);
    }
  }, [pendingReviewNode]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── 초기 데이터 로드 ──
  useEffect(() => {
    createClient()
      .auth.getUser()
      .then(({ data }) => setCurrentUserId(data.user?.id ?? ""));
    createClient()
      .auth.getSession()
      .then(({ data }) => setDownloadToken(data.session?.access_token ?? ""));
  }, []);

  // 3-Stream 상태 폴링
  const fetchStreams = useCallback(async () => {
    try {
      const res = await streamsApi.getAll(id);
      setStreamsData(res.streams as StreamProgress[]);
    } catch {
      /* 스트림 미초기화 */
    }
  }, [id]);

  // 워크플로 상태 폴링
  const fetchWorkflowState = useCallback(async () => {
    try {
      setWorkflowState(await api.workflow.getState(id));
    } catch {
      /* 미시작 */
    }
  }, [id]);

  const statusStr = status?.status;
  useEffect(() => {
    fetchWorkflowState();
    fetchStreams();
    const running =
      statusStr === "processing" ||
      statusStr === "initialized" ||
      statusStr === "running";
    if (running) {
      const t = setInterval(() => {
        fetchWorkflowState();
        fetchStreams();
      }, 5000);
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
    try {
      const result = await api.proposals.versions(id);
      const versionsArray = Array.isArray(result) ? result : [];
      setVersions(versionsArray);
    } catch {
      /* 미구현 — 엔드포인트 없음 */
      setVersions([]);
    }
  }, [id]);
  useEffect(() => {
    fetchVersions();
  }, [fetchVersions]);

  // 결과 데이터
  useEffect(() => {
    if (status?.status === "completed") {
      api.artifacts
        .get(id, "proposal")
        .then((r) => setResultData(r as any))
        .catch(() => {});
    }
  }, [id, status?.status]);

  // 댓글
  const fetchComments = useCallback(async () => {
    try {
      setComments((await api.comments.list(id)).comments);
    } catch {}
  }, [id]);
  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  // 파일
  const fetchFiles = useCallback(async () => {
    setFilesLoading(true);
    try {
      setFiles((await api.proposals.listFiles(id)).files);
    } catch {
    } finally {
      setFilesLoading(false);
    }
  }, [id]);
  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

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
    } catch (e) {
      alert(e instanceof Error ? e.message : "재시작 실패");
    }
  }

  async function handleNewVersion() {
    try {
      const res = await (api.proposals as any).newVersion(id);
      if (res?.proposal_id) router.push(`/proposals/${res.proposal_id}`);
    } catch (e) {
      alert(e instanceof Error ? e.message : "새 버전 생성 실패");
    }
  }

  async function handleAbort() {
    setAborting(true);
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}/proposals/${id}/ai-abort`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${downloadToken}` },
        },
      );
      fetchWorkflowState();
    } catch {
    } finally {
      setAborting(false);
    }
  }

  async function handleRetry() {
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"}/proposals/${id}/ai-retry`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${downloadToken}` },
        },
      );
      fetchWorkflowState();
    } catch {}
  }

  async function handleGoto(step: string) {
    try {
      await api.workflow.goto(id, step);
      fetchWorkflowState();
      setSelectedStep(null);
    } catch (e) {
      alert(e instanceof Error ? e.message : "복원 실패");
    }
  }

  // ── 버전 라벨 ──
  function versionLabel(idx: number) {
    return `v${idx + 1}`;
  }
  function currentVersionLabel() {
    if (!Array.isArray(versions)) return "v1";
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
      {/* ═══ 상단: 프로젝트 컨텍스트 헤더 ═══ */}
      <ProjectContextHeader
        proposalId={id}
        status={status}
        versions={versions}
        currentVersionLabel={currentVersionLabel}
        versionLabel={versionLabel}
        onNewVersion={handleNewVersion}
        rightPanelOpen={rightPanelOpen}
        onToggleRightPanel={() => setRightPanelOpen((o) => !o)}
      />

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
            onClick={() =>
              document
                .getElementById("workflow-panel")
                ?.scrollIntoView({ behavior: "smooth" })
            }
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

          {activeTab === "filehub" && (
            <div className="max-w-3xl mx-auto">
              <FileHubPanel
                proposalId={id}
                phasesCompleted={status.phases_completed ?? 0}
                onSelectArtifact={(stepIndex, artifactKey) => {
                  setActiveDocId(`artifact-${artifactKey}`);
                  setSelectedStep(stepIndex);
                  if (!rightPanelOpen) setRightPanelOpen(true);
                }}
                onSelectFile={(file) => {
                  setActiveDocId(`file-${file.id}`);
                  const viewable = ["pdf", "png", "jpg", "jpeg"];
                  if (
                    file.file_type &&
                    viewable.includes(file.file_type.toLowerCase())
                  ) {
                    if (!rightPanelOpen) setRightPanelOpen(true);
                  } else {
                    api.proposals
                      .getFileUrl(id, file.id)
                      .then((r) => window.open(r.url, "_blank"))
                      .catch(() => alert("다운로드 실패"));
                  }
                }}
              />
            </div>
          )}

          {/* 문서 탭 */}
          {activeTab === "kb" && (
            <div className="max-w-3xl mx-auto">
              <ProjectDocumentsPanel />
            </div>
          )}

          {/* STEP 8 검토 탭 */}
          {activeTab === "step8" && streamsData.length > 0 && (
            <Step8ReviewPage />
          )}
        </main>

        {/* 우측 패널 — lg 이상 인라인 표시 + 리사이즈 */}
        {rightPanelOpen && (
          <div
            className="relative shrink-0 hidden lg:flex"
            style={{ width: rightPanelWidth }}
          >
            {/* 리사이즈 핸들 */}
            <div
              onMouseDown={handleResizeStart}
              className="absolute left-0 top-0 bottom-0 w-[6px] cursor-col-resize z-10 group flex items-center justify-center hover:bg-[#3ecf8e]/20 active:bg-[#3ecf8e]/40 transition-colors"
              title="좌우 드래그로 패널 크기 조절"
            >
              <div className="flex flex-col gap-1 items-center">
                <span className="w-1 h-1 rounded-full bg-[#4a4a4a] group-hover:bg-[#3ecf8e] transition-colors" />
                <span className="w-1 h-1 rounded-full bg-[#4a4a4a] group-hover:bg-[#3ecf8e] transition-colors" />
                <span className="w-1 h-1 rounded-full bg-[#4a4a4a] group-hover:bg-[#3ecf8e] transition-colors" />
              </div>
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
      <div
        className={`lg:hidden fixed inset-0 z-40 ${rightPanelOpen ? "" : "hidden"}`}
      >
        <div
          className="absolute inset-0 bg-black/50"
          onClick={() => setRightPanelOpen(false)}
        />
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
