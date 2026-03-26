"use client";

/**
 * 제안서 상세 페이지 — 중앙 패널 (워크플로 영역)
 * DocumentBrowser + PhaseGraph + WorkflowPanel + 상태바 + 실시간 로그
 */

import { useCallback, useState } from "react";
import PhaseGraph from "@/components/PhaseGraph";
import WorkflowPanel from "@/components/WorkflowPanel";
import WorkflowLogPanel from "@/components/WorkflowLogPanel";
import { api, type WorkflowState } from "@/lib/api";
import type { NodeProgress, StreamEvent } from "@/lib/hooks/useWorkflowStream";

const NODE_LABELS: Record<string, string> = {
  rfp_analyze: "RFP 분석", research_gather: "선행 리서치", go_no_go: "Go/No-Go 판정",
  strategy_generate: "전략 수립", bid_plan: "입찰가격 계획",
  plan_team: "팀 구성", plan_assign: "역할 배분", plan_schedule: "일정 수립",
  plan_story: "스토리라인 설계", plan_price: "예산 산정", plan_merge: "계획 통합",
  proposal_write_next: "섹션 작성", self_review: "자가진단",
  presentation_strategy: "발표 전략", ppt_toc: "PPT 목차", ppt_visual_brief: "시각 설계", ppt_storyboard: "슬라이드 작성",
};

interface DetailCenterPanelProps {
  proposalId: string;
  status: string;
  workflowState: WorkflowState | null;
  nodeProgress: Map<string, NodeProgress>;
  currentNode: string;
  isStreaming: boolean;
  streamEvents: StreamEvent[];
  selectedStep: number | null;
  onStepClick: (idx: number | null) => void;
  onStateChange: () => void;
  onStartWorkflow: () => void;
  isStarting: boolean;
  isProcessing: boolean;
  isFailed: boolean;
  isPaused: boolean;
  elapsed: string;
  phasesCompleted: number;
  error?: string;
  onAbort: () => void;
  onRetry: () => void;
  onRetryFromPhase: (phaseN: number) => void;
  aborting: boolean;
}

export default function DetailCenterPanel({
  proposalId,
  workflowState,
  nodeProgress,
  currentNode,
  isStreaming,
  streamEvents,
  selectedStep,
  onStepClick,
  onStateChange,
  onStartWorkflow,
  isStarting,
  isProcessing,
  isFailed,
  isPaused,
  elapsed,
  phasesCompleted,
  error,
  onAbort,
  onRetry,
  onRetryFromPhase,
  aborting,
}: DetailCenterPanelProps) {
  const [logCollapsed, setLogCollapsed] = useState(false);
  const [gateApproving, setGateApproving] = useState(false);
  const failedPhaseN = phasesCompleted + 1;

  const handleGateApprove = useCallback(async () => {
    setGateApproving(true);
    try {
      await api.workflow.resume(proposalId, { approved: true, quick_approve: true });
      onStateChange();
    } catch (e) {
      alert(e instanceof Error ? e.message : "승인 실패");
    } finally {
      setGateApproving(false);
    }
  }, [proposalId, onStateChange]);

  const isNotStarted = !workflowState || (!workflowState.current_step && !isProcessing && !isFailed);

  return (
    <div className="space-y-4">
      {/* 워크플로 시작 전 안내 */}
      {isNotStarted && (
        <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-6">
          <h2 className="text-sm font-semibold text-[#ededed] mb-3">AI 워크플로 안내</h2>
          <p className="text-xs text-[#8c8c8c] mb-4 leading-relaxed">
            워크플로를 시작하면 6단계를 자동으로 진행합니다.<br />
            각 단계 완료 후 <span className="text-amber-400">사용자 검토</span> 기회가 주어집니다.
          </p>
          <div className="grid grid-cols-3 gap-2 mb-5">
            {[
              { step: "1", label: "RFP 분석", hitl: "Go/No-Go 결정" },
              { step: "2", label: "전략 수립", hitl: "전략 검토" },
              { step: "3", label: "실행 계획", hitl: "계획서 검토" },
              { step: "4", label: "제안서 작성", hitl: "섹션별 검토" },
              { step: "5", label: "자가진단", hitl: "최종 검토" },
              { step: "6", label: "PPT 생성", hitl: "PPT 검토" },
            ].map((s) => (
              <div key={s.step} className="bg-[#111111] rounded-lg px-3 py-2.5 border border-[#262626]">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-[10px] font-bold text-[#3ecf8e] bg-[#3ecf8e]/10 rounded w-5 h-5 flex items-center justify-center">{s.step}</span>
                  <span className="text-xs font-medium text-[#ededed]">{s.label}</span>
                </div>
                <div className="flex items-center gap-1 text-[10px] text-amber-400/80">
                  <span>&#9995;</span>
                  <span>{s.hitl}</span>
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={onStartWorkflow}
            disabled={isStarting}
            className="w-full bg-[#3ecf8e] hover:bg-[#49e59e] disabled:opacity-50 text-[#0f0f0f] font-semibold rounded-xl py-3 text-sm transition-colors"
          >
            {isStarting ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-[#0f0f0f]/30 border-t-[#0f0f0f] rounded-full animate-spin" />
                워크플로 시작 중...
              </span>
            ) : (
              "AI 워크플로 시작"
            )}
          </button>
        </div>
      )}

      {/* 워크플로 그래프 — 미시작 시 숨김 */}
      {!isNotStarted && (
        <PhaseGraph
          workflowState={workflowState}
          nodeProgress={nodeProgress}
          currentNode={currentNode}
          selectedStep={selectedStep}
          onStepClick={(idx) => onStepClick(selectedStep === idx ? null : idx)}
          onStartStep={() => onStartWorkflow()}
          onGateApprove={handleGateApprove}
          isStarting={isStarting}
          isGateApproving={gateApproving}
          isPaused={isPaused}
          elapsed={elapsed}
          onAbort={onAbort}
          aborting={aborting}
        />
      )}

      {/* 워크플로 패널: Go/No-Go + 리뷰 + 병렬 진행 */}
      <div id="workflow-panel" />
      <WorkflowPanel
        proposalId={proposalId}
        workflowState={workflowState}
        onStateChange={onStateChange}
      />

      {/* 실패 상태 */}
      {isFailed && (
        <div className="flex items-center justify-between bg-[#1c1c1c] rounded-2xl border border-red-500/30 px-5 py-3">
          <span className="text-xs text-red-400">{error || "처리 중 오류 발생"}</span>
          <div className="flex items-center gap-2">
            <button onClick={onRetry} className="text-xs text-[#3ecf8e] hover:text-[#49e59e] border border-[#3ecf8e]/30 rounded-lg px-2.5 py-1 transition-colors">
              재시도
            </button>
            <button onClick={() => onRetryFromPhase(failedPhaseN)} className="text-xs text-red-400 hover:text-red-300 border border-red-500/30 rounded-lg px-2.5 py-1 transition-colors">
              Phase {failedPhaseN}부터 재시작
            </button>
          </div>
        </div>
      )}

      {/* 실시간 로그 패널 */}
      {(isProcessing || streamEvents.length > 0) && (
        <WorkflowLogPanel
          events={streamEvents}
          isStreaming={isStreaming}
          collapsed={logCollapsed}
          onToggle={() => setLogCollapsed(!logCollapsed)}
        />
      )}
    </div>
  );
}
