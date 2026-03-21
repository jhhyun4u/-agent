"use client";

/**
 * 제안서 상세 페이지 — 중앙 패널 (워크플로 영역)
 * PhaseGraph + WorkflowPanel + 상태바 + 실시간 로그
 */

import { useState } from "react";
import PhaseGraph from "@/components/PhaseGraph";
import WorkflowPanel from "@/components/WorkflowPanel";
import WorkflowLogPanel from "@/components/WorkflowLogPanel";
import type { WorkflowState } from "@/lib/api";
import type { NodeProgress, StreamEvent } from "@/lib/hooks/useWorkflowStream";

// ── 다음 리뷰 포인트 예측 ──
const REVIEW_SEQUENCE = [
  { after: "rfp_analyze", label: "RFP 분석 검토" },
  { after: "go_no_go", label: "Go/No-Go 결정" },
  { after: "strategy_generate", label: "전략 검토" },
  { after: "bid_plan", label: "입찰가격 검토" },
  { after: "plan_merge", label: "계획서 검토" },
  { after: "proposal_write_next", label: "섹션 검토" },
  { after: "self_review", label: "최종 검토" },
  { after: "ppt_storyboard", label: "PPT 검토" },
];

function getNextReview(currentStep: string): string | null {
  const idx = REVIEW_SEQUENCE.findIndex((r) =>
    currentStep.includes(r.after) || currentStep === r.after
  );
  // 현재 단계의 리뷰가 다음 포인트
  if (idx >= 0) return REVIEW_SEQUENCE[idx].label;
  // 현재 이전 단계면 다음 리뷰 반환
  for (const r of REVIEW_SEQUENCE) {
    if (!currentStep.includes(r.after)) return r.label;
  }
  return null;
}

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
  const failedPhaseN = phasesCompleted + 1;

  // 워크플로 미시작 안내
  const isNotStarted = !workflowState || (!workflowState.current_step && !isProcessing && !isFailed);

  return (
    <div className="space-y-5">
      {/* 워크플로 시작 전 안내 */}
      {isNotStarted && (
        <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-6">
          <h2 className="text-sm font-semibold text-[#ededed] mb-3">AI 워크플로 안내</h2>
          <p className="text-xs text-[#8c8c8c] mb-4 leading-relaxed">
            워크플로를 시작하면 6단계를 자동으로 진행합니다.<br />
            각 단계 완료 후 <span className="text-amber-400">사용자 검토</span> 기회가 주어집니다.
          </p>
          <div className="grid grid-cols-3 gap-2">
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
        </div>
      )}

      {/* 워크플로 그래프 */}
      <PhaseGraph
        workflowState={workflowState}
        nodeProgress={nodeProgress}
        currentNode={currentNode}
        selectedStep={selectedStep}
        onStepClick={(idx) => onStepClick(selectedStep === idx ? null : idx)}
      />

      {/* 워크플로 패널: Go/No-Go + 리뷰 + 병렬 진행 */}
      <div id="workflow-panel" />
      <WorkflowPanel
        proposalId={proposalId}
        workflowState={workflowState}
        onStateChange={onStateChange}
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
              onClick={onRetry}
              className="text-xs text-[#3ecf8e] hover:text-[#49e59e] border border-[#3ecf8e]/30 rounded-lg px-3 py-1.5 font-medium transition-colors"
            >
              재개
            </button>
            {selectedStep === null && (
              <button
                onClick={() => onStepClick(Math.max(0, phasesCompleted - 1))}
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
                  <span className="text-xs text-[#3ecf8e] font-medium">
                    {NODE_LABELS[currentNode] || currentNode}
                  </span>
                )}
                {workflowState?.current_step && (() => {
                  const next = getNextReview(workflowState.current_step);
                  return next ? (
                    <span className="text-[10px] text-amber-400/70 ml-2">
                      &#9995; 다음 확인: {next}
                    </span>
                  ) : null;
                })()}
              </>
            )}
            {isFailed && (
              <span className="text-xs text-red-400">{error || "처리 중 오류 발생"}</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {isProcessing && (
              <button
                onClick={onAbort}
                disabled={aborting}
                className="text-xs text-amber-400 hover:text-amber-300 border border-amber-500/30 rounded-lg px-2.5 py-1 transition-colors disabled:opacity-40"
              >
                {aborting ? "중단 중..." : "일시정지"}
              </button>
            )}
            {isFailed && (
              <>
                <button
                  onClick={onRetry}
                  className="text-xs text-[#3ecf8e] hover:text-[#49e59e] border border-[#3ecf8e]/30 rounded-lg px-2.5 py-1 transition-colors"
                >
                  재시도
                </button>
                <button
                  onClick={() => onRetryFromPhase(failedPhaseN)}
                  className="text-xs text-red-400 hover:text-red-300 border border-red-500/30 rounded-lg px-2.5 py-1 transition-colors"
                >
                  Phase {failedPhaseN}부터 재시작
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* W18: 워크플로 리뷰 히스토리 */}
      {workflowState?.review_history && workflowState.review_history.length > 0 && (
        <div className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
          <h2 className="text-sm font-semibold text-[#ededed] mb-3">리뷰 히스토리</h2>
          <div className="space-y-2">
            {workflowState.review_history.map((h, i) => (
              <div key={i} className="flex items-center gap-3 text-xs">
                <span className={`w-2 h-2 rounded-full shrink-0 ${h.approved ? "bg-[#3ecf8e]" : "bg-red-400"}`} />
                <span className="text-[#8c8c8c] w-20 shrink-0">
                  {new Date(h.timestamp).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })}
                </span>
                <span className="text-[#ededed] font-medium">
                  {NODE_LABELS[h.node] || h.node}
                </span>
                <span className={h.approved ? "text-[#3ecf8e]" : "text-red-400"}>
                  {h.approved ? "승인" : "재작업"}
                </span>
                {h.feedback && (
                  <span className="text-[#5c5c5c] truncate flex-1" title={h.feedback}>
                    — {h.feedback}
                  </span>
                )}
              </div>
            ))}
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
