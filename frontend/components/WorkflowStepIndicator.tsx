"use client";

/**
 * WorkflowStepIndicator — 제안서 상세 페이지 상단 스티키 진행 바
 *
 * Head(1,2) → Path(3-6) → Tail(7) 순서로 표시.
 * 현재 노드를 기준으로 완료/진행/대기/미진행 상태를 색으로 구분.
 */

import {
  WORKFLOW_STEPS,
  BIDDING_STEPS,
  type WorkflowState,
  type WorkflowStepDef,
} from "@/lib/api";

interface Props {
  workflowState: WorkflowState | null;
  phasesCompleted: number;
  onStepClick?: (step: WorkflowStepDef) => void;
}

// ── 리뷰 노드 → 해당 스텝 번호 매핑 ─────────────────────────────────
const REVIEW_TO_STEP: Record<string, number> = {
  review_search: 1, review_rfp: 1, review_gng: 1,
  review_strategy: 2,
  review_plan: 3,
  review_bid_plan: 4,
  review_section: 4, review_gap_analysis: 4, review_proposal: 4,
  review_ppt: 5,
};

// ── 현재 노드에서 스텝 번호 추론 ─────────────────────────────────────
function resolveCurrentStep(currentNode: string | undefined): number {
  if (!currentNode) return 0;
  const match = WORKFLOW_STEPS.find((s) => s.nodes.includes(currentNode));
  if (match) return match.step;
  return REVIEW_TO_STEP[currentNode] ?? 0;
}

// ── 경로 감지 (proposal vs bidding) ──────────────────────────────────
function detectPath(currentNode: string | undefined): "proposal" | "bidding" {
  if (!currentNode) return "proposal";
  const isBidding = BIDDING_STEPS.some((s) => s.nodes.includes(currentNode));
  return isBidding ? "bidding" : "proposal";
}

// ── 표시할 스텝 목록 구성 ─────────────────────────────────────────────
function buildStepList(path: "proposal" | "bidding"): WorkflowStepDef[] {
  return WORKFLOW_STEPS.filter(
    (s) => s.path === "head" || s.path === path || s.path === "tail",
  ).sort((a, b) => {
    if (a.step !== b.step) return a.step - b.step;
    return a.stepLabel.localeCompare(b.stepLabel);
  });
}

// ── 스텝 상태 ────────────────────────────────────────────────────────
type StepState = "completed" | "active" | "waiting" | "upcoming";

function getStepState(
  step: WorkflowStepDef,
  currentStepNum: number,
  currentNode: string | undefined,
  hasPendingInterrupt: boolean,
): StepState {
  const isCurrentStep =
    step.nodes.includes(currentNode ?? "") ||
    step.step === currentStepNum;

  if (isCurrentStep) {
    return hasPendingInterrupt ? "waiting" : "active";
  }
  if (step.step < currentStepNum) return "completed";
  return "upcoming";
}

// ── 색상 맵 ──────────────────────────────────────────────────────────
const STATE_STYLE: Record<StepState, { circle: string; text: string; line: string }> = {
  completed: {
    circle: "bg-[#3ecf8e] border-[#3ecf8e] text-[#0f0f0f]",
    text: "text-[#3ecf8e]",
    line: "bg-[#3ecf8e]",
  },
  active: {
    circle: "bg-blue-500 border-blue-500 text-white ring-2 ring-blue-500/30",
    text: "text-blue-400",
    line: "bg-[#262626]",
  },
  waiting: {
    circle: "bg-amber-500 border-amber-500 text-white ring-2 ring-amber-500/30",
    text: "text-amber-400",
    line: "bg-[#262626]",
  },
  upcoming: {
    circle: "bg-[#1c1c1c] border-[#404040] text-[#8c8c8c]",
    text: "text-[#8c8c8c]",
    line: "bg-[#262626]",
  },
};

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────
export default function WorkflowStepIndicator({
  workflowState,
  phasesCompleted,
  onStepClick,
}: Props) {
  const currentNode = workflowState?.current_step;
  const hasPendingInterrupt = workflowState?.has_pending_interrupt ?? false;

  const path = detectPath(currentNode);
  const currentStepNum = resolveCurrentStep(currentNode) || phasesCompleted;
  const steps = buildStepList(path);

  return (
    <div className="bg-[#0f0f0f] border-b border-[#1e1e1e] px-4 py-2.5 shrink-0">
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-1 overflow-x-auto scrollbar-hide">
        {steps.map((step, idx) => {
          const state = getStepState(step, currentStepNum, currentNode, hasPendingInterrupt);
          const style = STATE_STYLE[state];
          const isLast = idx === steps.length - 1;

          return (
            <div key={step.stepLabel} className="flex items-center shrink-0">
              {/* 스텝 */}
              <button
                onClick={() => onStepClick?.(step)}
                disabled={state === "upcoming"}
                className="flex flex-col items-center gap-1 group"
                title={`STEP ${step.stepLabel}: ${step.label}`}
              >
                {/* 원 */}
                <div
                  className={`w-6 h-6 rounded-full border flex items-center justify-center text-[10px] font-bold transition-all
                    ${style.circle}
                    ${state !== "upcoming" ? "cursor-pointer group-hover:scale-110" : "cursor-default"}
                    ${state === "active" ? "animate-[pulse_2s_ease-in-out_infinite]" : ""}
                    ${state === "waiting" ? "animate-[pulse_1s_ease-in-out_infinite]" : ""}
                  `}
                >
                  {state === "completed" ? (
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    step.stepLabel
                  )}
                </div>

                {/* 라벨 */}
                <span className={`text-[9px] font-medium whitespace-nowrap leading-tight ${style.text}`}>
                  {step.label}
                  {state === "waiting" && (
                    <span className="ml-0.5 text-amber-400">•</span>
                  )}
                </span>
              </button>

              {/* 연결선 */}
              {!isLast && (
                <div className={`h-px w-4 mx-1 mt-[-10px] transition-colors ${style.line}`} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
