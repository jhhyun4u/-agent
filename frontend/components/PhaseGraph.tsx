"use client";

/**
 * PhaseGraph — 수평 워크플로 그래프 (§13-1-1)
 *
 * 6 STEP을 수평 노드로 표시. 현재 단계, 완료, 리뷰 대기, 미시작 상태를 시각적으로 구분.
 * 병렬 fan-out 구간(STEP 3)은 묶어 표시.
 */

import { WORKFLOW_STEPS, type WorkflowState } from "@/lib/api";

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

  // 현재 노드가 이 STEP에 속하는지
  const isActive = stepDef.nodes.some(
    (n) => currentStep.includes(n) || currentStep === n
  );

  // 리뷰 대기 (interrupt + next_nodes가 이 STEP 이후의 review)
  const reviewNodes = ["review_search", "review_rfp", "review_gng", "review_strategy", "review_plan", "review_section", "review_proposal", "review_ppt"];
  const isReviewPending = hasInterrupt && nextNodes.some((n) => reviewNodes.includes(n));

  // 이 STEP의 모든 노드가 완료되었는지 판별
  // 간단한 휴리스틱: current_step이 이후 STEP의 노드에 있으면 이전 STEP은 완료
  const currentStepIndex = WORKFLOW_STEPS.findIndex((s) =>
    s.nodes.some((n) => currentStep.includes(n) || currentStep === n)
  );

  if (currentStepIndex > stepIndex) return "completed";
  if (isActive && isReviewPending) return "review_pending";
  if (isActive) return "active";

  // 완료된 STEP 이전 모든 것은 completed
  if (stepIndex < currentStepIndex) return "completed";

  return "pending";
}

// ── 컴포넌트 ──

interface PhaseGraphProps {
  workflowState: WorkflowState | null;
  className?: string;
}

export default function PhaseGraph({ workflowState, className = "" }: PhaseGraphProps) {
  const currentStep = workflowState?.current_step ?? "";
  const nextNodes = workflowState?.next_nodes ?? [];
  const hasInterrupt = workflowState?.has_pending_interrupt ?? false;
  const tokenSummary = workflowState?.token_summary;

  return (
    <div className={`bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-[#ededed]">워크플로 진행</h2>
        {tokenSummary && tokenSummary.nodes_tracked > 0 && (
          <span className="text-[10px] text-[#8c8c8c] bg-[#262626] rounded px-2 py-0.5">
            ${tokenSummary.total_cost_usd.toFixed(4)} / {tokenSummary.nodes_tracked} nodes
          </span>
        )}
      </div>

      {/* 수평 그래프 */}
      <div className="flex items-start gap-0 overflow-x-auto pb-2">
        {WORKFLOW_STEPS.map((step, idx) => {
          const status = resolveStepStatus(idx, currentStep, nextNodes, hasInterrupt);
          const isLast = idx === WORKFLOW_STEPS.length - 1;

          return (
            <div key={step.step} className="flex items-start flex-shrink-0">
              {/* 노드 */}
              <div className="flex flex-col items-center w-[72px]">
                {/* 원형 노드 */}
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                    status === "completed"
                      ? "bg-[#3ecf8e] text-[#0f0f0f]"
                      : status === "active"
                      ? "bg-[#3ecf8e]/20 border-2 border-[#3ecf8e] text-[#3ecf8e]"
                      : status === "review_pending"
                      ? "bg-amber-500/20 border-2 border-amber-500 text-amber-400"
                      : "bg-[#262626] border border-[#363636] text-[#5c5c5c]"
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
                </div>

                {/* 라벨 */}
                <span
                  className={`mt-1.5 text-[10px] font-medium text-center leading-tight ${
                    status === "completed"
                      ? "text-[#3ecf8e]"
                      : status === "active"
                      ? "text-[#ededed]"
                      : status === "review_pending"
                      ? "text-amber-400"
                      : "text-[#5c5c5c]"
                  }`}
                >
                  {step.label}
                </span>

                {/* 병렬 표시 (STEP 3) */}
                {step.step === 3 && status === "active" && (
                  <span className="mt-0.5 text-[8px] text-[#3ecf8e]/60">5 병렬</span>
                )}

                {/* 리뷰 대기 뱃지 */}
                {status === "review_pending" && (
                  <span className="mt-0.5 text-[8px] text-amber-400/80">승인 대기</span>
                )}
              </div>

              {/* 연결선 */}
              {!isLast && (
                <div className="flex items-center mt-4 px-0.5">
                  <div
                    className={`h-[2px] w-4 ${
                      status === "completed"
                        ? "bg-[#3ecf8e]/40"
                        : "bg-[#262626]"
                    }`}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 범례 */}
      <div className="flex items-center gap-4 mt-3 pt-3 border-t border-[#262626]">
        {[
          { color: "bg-[#3ecf8e]", label: "완료" },
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
