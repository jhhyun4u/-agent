"use client";

/**
 * PhaseGraph — 수평 워크플로 그래프 (§13-1-1, v2: 클릭 확장 + 세부 노드)
 *
 * 6 STEP을 수평 노드로 표시. 완료된 STEP 클릭 시 산출물 뷰어 표시.
 * 진행 중 STEP은 세부 노드 목록 표시.
 */

import { useState } from "react";
import { WORKFLOW_STEPS, type WorkflowState } from "@/lib/api";
import type { NodeProgress } from "@/lib/hooks/useWorkflowStream";

// ── 노드명 → 한글 매핑 ──

// ── W6: 예상 소요시간 (과거 평균 기반 추정) ──
const STEP_EST_MINUTES: Record<number, number> = {
  0: 2, 1: 3, 2: 2, 3: 5, 4: 8, 5: 3,
};

// ── W8: 완료 STEP 요약 (hover tooltip) ──
const STEP_COMPLETED_HINT: Record<number, string> = {
  0: "RFP 분석 완료 — 요구사항 추출됨",
  1: "Go/No-Go 결정 — 포지셔닝 확정됨",
  2: "전략 수립 완료 — Win Theme 정의됨",
  3: "실행 계획 완료 — 팀/일정/예산 확정",
  4: "제안서 작성 완료 — 전체 섹션 검토됨",
  5: "PPT 생성 완료 — 발표 자료 준비됨",
};

// ── HITL 마커: 각 STEP의 리뷰 포인트 ──
const STEP_HITL: Record<number, string> = {
  0: "검색 결과 확인",
  1: "Go/No-Go",
  2: "전략 검토",
  3: "계획 검토",
  4: "섹션·최종 검토",
  5: "PPT 검토",
};

const NODE_LABELS: Record<string, string> = {
  rfp_analyze: "RFP 분석",
  research_gather: "리서치", go_no_go: "Go/No-Go",
  strategy_generate: "전략 수립",
  plan_team: "팀구성", plan_assign: "역할배분", plan_schedule: "일정",
  plan_story: "스토리라인", plan_price: "예산",
  proposal_write_next: "섹션 작성", self_review: "자가진단",
  presentation_strategy: "발표전략", ppt_toc: "PPT 목차",
  ppt_visual_brief: "시각설계", ppt_storyboard: "슬라이드",
};

// ── 노드 상태 결정 ──

type NodeStatus = "completed" | "active" | "review_pending" | "pending";

function resolveStepStatus(
  stepIndex: number,
  currentStep: string,
  nextNodes: string[],
  hasInterrupt: boolean,
): NodeStatus {
  const stepDef = WORKFLOW_STEPS[stepIndex];
  if (!stepDef) return "pending";

  const isActive = stepDef.nodes.some(
    (n) => currentStep.includes(n) || currentStep === n
  );

  const reviewNodes = [
    "review_rfp", "review_gng", "review_strategy",
    "review_plan", "review_section", "review_proposal", "review_ppt",
  ];
  const isReviewPending = hasInterrupt && nextNodes.some((n) => reviewNodes.includes(n));

  const currentStepIndex = WORKFLOW_STEPS.findIndex((s) =>
    s.nodes.some((n) => currentStep.includes(n) || currentStep === n)
  );

  if (currentStepIndex > stepIndex) return "completed";
  if (isActive && isReviewPending) return "review_pending";
  if (isActive) return "active";
  if (stepIndex < currentStepIndex) return "completed";

  return "pending";
}

// ── 컴포넌트 ──

interface PhaseGraphProps {
  workflowState: WorkflowState | null;
  nodeProgress?: Map<string, NodeProgress>;
  currentNode?: string;
  selectedStep?: number | null;
  onStepClick?: (stepIndex: number) => void;
  className?: string;
}

export default function PhaseGraph({
  workflowState,
  nodeProgress,
  currentNode = "",
  selectedStep = null,
  onStepClick,
  className = "",
}: PhaseGraphProps) {
  const currentStep = workflowState?.current_step ?? "";
  const nextNodes = workflowState?.next_nodes ?? [];
  const hasInterrupt = workflowState?.has_pending_interrupt ?? false;
  const tokenSummary = workflowState?.token_summary;

  // 세부 노드 펼침 상태
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  function handleStepClick(idx: number, status: NodeStatus) {
    if (status === "completed" || status === "review_pending") {
      onStepClick?.(idx);
    }
    // 진행 중이면 세부 노드 토글
    if (status === "active") {
      setExpandedStep(expandedStep === idx ? null : idx);
    }
  }

  return (
    <div className={`bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-[#ededed]">워크플로 진행</h2>
        <div className="flex items-center gap-2">
          {currentNode && (
            <span className="text-[10px] text-[#3ecf8e] bg-[#3ecf8e]/10 rounded px-2 py-0.5 animate-pulse">
              {NODE_LABELS[currentNode] || currentNode}
            </span>
          )}
          {tokenSummary && tokenSummary.nodes_tracked > 0 && (
            <span className="text-[10px] text-[#8c8c8c] bg-[#262626] rounded px-2 py-0.5">
              ${tokenSummary.total_cost_usd.toFixed(4)} / {tokenSummary.nodes_tracked} nodes
            </span>
          )}
        </div>
      </div>

      {/* 수평 그래프 */}
      <div className="flex items-start gap-0 overflow-x-auto pb-2">
        {WORKFLOW_STEPS.map((step, idx) => {
          const status = resolveStepStatus(idx, currentStep, nextNodes, hasInterrupt);
          const isLast = idx === WORKFLOW_STEPS.length - 1;
          const isSelected = selectedStep === idx;

          return (
            <div key={step.step} className="flex items-start flex-shrink-0">
              {/* 노드 */}
              <div className="flex flex-col items-center w-[72px]">
                {/* 원형 노드 (클릭 가능) */}
                <button
                  onClick={() => handleStepClick(idx, status)}
                  title={status === "completed" ? STEP_COMPLETED_HINT[idx] : status === "pending" ? `예상 ~${STEP_EST_MINUTES[idx] ?? 3}분` : undefined}
                  className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                    isSelected
                      ? "ring-2 ring-[#3ecf8e] ring-offset-1 ring-offset-[#1c1c1c]"
                      : ""
                  } ${
                    status === "completed"
                      ? "bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#49e59e] cursor-pointer"
                      : status === "active"
                      ? "bg-[#3ecf8e]/20 border-2 border-[#3ecf8e] text-[#3ecf8e] cursor-pointer"
                      : status === "review_pending"
                      ? "bg-amber-500/20 border-2 border-amber-500 text-amber-400 cursor-pointer"
                      : "bg-[#262626] border border-[#363636] text-[#5c5c5c] cursor-default"
                  }`}
                >
                  {status === "completed" ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : status === "active" ? (
                    <div className="w-2.5 h-2.5 rounded-full border-2 border-[#3ecf8e] border-t-transparent animate-spin" />
                  ) : status === "review_pending" ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  ) : (
                    step.step
                  )}
                </button>

                {/* 라벨 */}
                <span
                  className={`mt-1.5 text-[10px] font-medium text-center leading-tight ${
                    status === "completed" ? "text-[#3ecf8e]"
                    : status === "active" ? "text-[#ededed]"
                    : status === "review_pending" ? "text-amber-400"
                    : "text-[#5c5c5c]"
                  }`}
                >
                  {step.label}
                </span>

                {/* 병렬 표시 */}
                {step.step === 3 && status === "active" && (
                  <span className="mt-0.5 text-[8px] text-[#3ecf8e]/60">5 병렬</span>
                )}
                {status === "review_pending" && (
                  <span className="mt-0.5 text-[8px] text-amber-400/80 animate-pulse">승인 대기</span>
                )}
                {/* W6: 활성 예상시간 */}
                {status === "active" && STEP_EST_MINUTES[idx] && (
                  <span className="mt-0.5 text-[8px] text-[#3ecf8e]/60">~{STEP_EST_MINUTES[idx]}분</span>
                )}
                {/* HITL 마커 (미완료+비활성 단계에 표시) */}
                {status === "pending" && STEP_HITL[idx] && (
                  <span className="mt-0.5 text-[8px] text-[#5c5c5c]" title={STEP_HITL[idx]}>
                    &#9995; {STEP_HITL[idx]}
                  </span>
                )}
              </div>

              {/* 연결선 */}
              {!isLast && (
                <div className="flex items-center mt-4 px-0.5">
                  <div className={`h-[2px] w-4 ${status === "completed" ? "bg-[#3ecf8e]/40" : "bg-[#262626]"}`} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 세부 노드 (진행 중 STEP 펼침) */}
      {expandedStep !== null && (
        <SubNodeList
          stepIndex={expandedStep}
          nodeProgress={nodeProgress}
          currentNode={currentNode}
        />
      )}

      {/* 범례 */}
      <div className="flex items-center gap-4 mt-3 pt-3 border-t border-[#262626]">
        {[
          { color: "bg-[#3ecf8e]", label: "완료 (클릭)" },
          { color: "bg-[#3ecf8e]/30 border border-[#3ecf8e]", label: "진행중" },
          { color: "bg-amber-500/30 border border-amber-500", label: "승인 대기" },
          { color: "bg-[#262626] border border-[#363636]", label: "미시작" },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className={`w-2 h-2 rounded-full ${color}`} />
            <span className="text-[10px] text-[#8c8c8c]">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── 세부 노드 목록 ──

function SubNodeList({
  stepIndex,
  nodeProgress,
  currentNode,
}: {
  stepIndex: number;
  nodeProgress?: Map<string, NodeProgress>;
  currentNode: string;
}) {
  const stepDef = WORKFLOW_STEPS[stepIndex];
  if (!stepDef) return null;

  return (
    <div className="mt-3 pt-3 border-t border-[#262626]">
      <p className="text-[10px] text-[#8c8c8c] mb-2">STEP {stepDef?.step ?? stepIndex} 세부 진행</p>
      <div className="flex flex-wrap gap-1.5">
        {stepDef.nodes.map((node) => {
          const progress = nodeProgress?.get(node);
          const isCurrent = currentNode === node;
          const isCompleted = progress?.status === "completed";

          return (
            <div
              key={node}
              className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] transition-colors ${
                isCurrent
                  ? "bg-[#3ecf8e]/10 border border-[#3ecf8e]/30 text-[#3ecf8e]"
                  : isCompleted
                  ? "bg-[#262626] text-[#3ecf8e]"
                  : "bg-[#111111] border border-[#262626] text-[#5c5c5c]"
              }`}
            >
              {isCurrent ? (
                <div className="w-2 h-2 rounded-full border border-[#3ecf8e] border-t-transparent animate-spin" />
              ) : isCompleted ? (
                <span className="text-[#3ecf8e]">✓</span>
              ) : (
                <span className="w-1.5 h-1.5 rounded-full bg-[#363636]" />
              )}
              {NODE_LABELS[node] || node}
            </div>
          );
        })}
      </div>
    </div>
  );
}
