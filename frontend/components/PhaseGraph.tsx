"use client";

/**
 * PhaseGraph — 수평 워크플로 그래프 (v4)
 *
 * [Step 원 + Start/Finish] ─ [Gate 네모 + 승인] ─ [Step 원] ─ ...
 *
 * - 원: SVG 원주 위에 예상 시간 대비 진행률 표시 (active 상태)
 * - 원 하단: Start(대기) / Finish(완료) 버튼
 * - Gate 네모: 승인 버튼 → 누르면 다음 step 자동 시작
 */

import { useEffect, useRef, useState } from "react";
import { WORKFLOW_STEPS, type WorkflowState } from "@/lib/api";
import type { NodeProgress } from "@/lib/hooks/useWorkflowStream";

// ── 상수 ──

const STEP_EST_SECONDS: Record<number, number> = {
  0: 120, 1: 180, 2: 120, 3: 300, 4: 480, 5: 180,
};

const STEP_COMPLETED_HINT: Record<number, string> = {
  0: "RFP 분석 완료 — 요구사항 추출됨",
  1: "Go/No-Go 결정 — 포지셔닝 확정됨",
  2: "전략 수립 완료 — Win Theme 정의됨",
  3: "실행 계획 완료 — 팀/일정/예산 확정",
  4: "제안서 작성 완료 — 전체 섹션 검토됨",
  5: "PPT 생성 완료 — 발표 자료 준비됨",
};

const NODE_LABELS: Record<string, string> = {
  rfp_analyze: "RFP 분석", research_gather: "리서치", go_no_go: "Go/No-Go",
  strategy_generate: "전략 수립",
  plan_team: "팀구성", plan_assign: "역할배분", plan_schedule: "일정",
  plan_story: "스토리라인", plan_price: "예산",
  proposal_write_next: "섹션 작성", self_review: "자가진단",
  presentation_strategy: "발표전략", ppt_toc: "PPT 목차",
  ppt_visual_brief: "시각설계", ppt_storyboard: "슬라이드",
};

// ── Gate 정의 ──

interface GateDef {
  id: string;
  shortLabel: string;
  reviewNodes: string[];
}

const STEP_GATES: GateDef[] = [
  { id: "gate_rfp",      shortLabel: "분석 검토",  reviewNodes: ["review_rfp", "review_gng"] },
  { id: "gate_strategy",  shortLabel: "전략 검토",  reviewNodes: ["review_strategy"] },
  { id: "gate_bid_plan",  shortLabel: "가격 검토",  reviewNodes: ["review_bid_plan"] },
  { id: "gate_plan",      shortLabel: "계획 검토",  reviewNodes: ["review_plan"] },
  { id: "gate_proposal",  shortLabel: "제안서 검토", reviewNodes: ["review_section", "review_proposal"] },
  { id: "gate_ppt",       shortLabel: "PPT 검토",  reviewNodes: ["review_ppt"] },
];

// ── 상태 타입 ──

type NodeStatus = "completed" | "active" | "review_pending" | "pending";
type GateStatus = "passed" | "active" | "locked";

// ── 상태 판별 ──

function resolveStepStatus(
  stepIndex: number, currentStep: string, nextNodes: string[], hasInterrupt: boolean,
): NodeStatus {
  const stepDef = WORKFLOW_STEPS[stepIndex];
  if (!stepDef) return "pending";
  const isActive = stepDef.nodes.some((n) => currentStep.includes(n) || currentStep === n);
  const reviewNodes = ["review_rfp", "review_gng", "review_strategy", "review_bid_plan", "review_plan", "review_section", "review_proposal", "review_ppt"];
  const isReviewPending = hasInterrupt && nextNodes.some((n) => reviewNodes.includes(n));
  const currentStepIndex = WORKFLOW_STEPS.findIndex((s) => s.nodes.some((n) => currentStep.includes(n) || currentStep === n));
  if (currentStepIndex > stepIndex) return "completed";
  if (isActive && isReviewPending) return "review_pending";
  if (isActive) return "active";
  if (stepIndex < currentStepIndex) return "completed";
  return "pending";
}

function resolveGateStatus(
  gateIndex: number, stepStatuses: NodeStatus[], nextNodes: string[], hasInterrupt: boolean,
): GateStatus {
  const gate = STEP_GATES[gateIndex];
  if (!gate) return "locked";
  if (hasInterrupt && nextNodes.some((n) => gate.reviewNodes.includes(n))) return "active";
  const nextStepIdx = gateIndex + 1;
  if (nextStepIdx < stepStatuses.length) {
    const ns = stepStatuses[nextStepIdx];
    if (ns === "completed" || ns === "active" || ns === "review_pending") return "passed";
  }
  if (stepStatuses[gateIndex] === "completed") return "passed";
  return "locked";
}

// ── 진행률 원 (SVG) ──

function ProgressCircle({ progress, size = 44, stroke = 3 }: { progress: number; size?: number; stroke?: number }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (Math.min(progress, 1) * c);
  return (
    <svg className="absolute inset-0" width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
      {/* 배경 트랙 */}
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#262626" strokeWidth={stroke} />
      {/* 진행 아크 */}
      <circle
        cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke="#3ecf8e" strokeWidth={stroke} strokeLinecap="round"
        strokeDasharray={c} strokeDashoffset={offset}
        className="transition-all duration-1000"
      />
      {/* 진행 위치 마커 (원주 위의 점) */}
      {progress > 0 && progress < 1 && (
        <circle
          cx={size / 2 + r * Math.cos(2 * Math.PI * Math.min(progress, 1))}
          cy={size / 2 + r * Math.sin(2 * Math.PI * Math.min(progress, 1))}
          r={stroke + 1} fill="#3ecf8e"
        />
      )}
    </svg>
  );
}

// ── 경과 시간 기반 진행률 훅 ──

function useStepProgress(isActive: boolean, estSeconds: number) {
  const [progress, setProgress] = useState(0);
  const startRef = useRef(Date.now());

  useEffect(() => {
    if (!isActive) { setProgress(0); return; }
    startRef.current = Date.now();
    const t = setInterval(() => {
      const elapsed = (Date.now() - startRef.current) / 1000;
      setProgress(Math.min(elapsed / estSeconds, 0.95)); // 최대 95%까지 (완료 전)
    }, 500);
    return () => clearInterval(t);
  }, [isActive, estSeconds]);

  return progress;
}

// ── Props ──

interface PhaseGraphProps {
  workflowState: WorkflowState | null;
  nodeProgress?: Map<string, NodeProgress>;
  currentNode?: string;
  selectedStep?: number | null;
  onStepClick?: (stepIndex: number) => void;
  onStartStep?: (stepIndex: number) => void;
  onGateApprove?: (gateIndex: number) => void;
  isStarting?: boolean;
  className?: string;
}

export default function PhaseGraph({
  workflowState,
  nodeProgress,
  currentNode = "",
  selectedStep = null,
  onStepClick,
  onStartStep,
  onGateApprove,
  isStarting = false,
  className = "",
}: PhaseGraphProps) {
  const currentStep = workflowState?.current_step ?? "";
  const nextNodes = workflowState?.next_nodes ?? [];
  const hasInterrupt = workflowState?.has_pending_interrupt ?? false;
  const tokenSummary = workflowState?.token_summary;

  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  const stepStatuses: NodeStatus[] = WORKFLOW_STEPS.map((_, idx) =>
    resolveStepStatus(idx, currentStep, nextNodes, hasInterrupt)
  );
  const gateStatuses: GateStatus[] = STEP_GATES.map((_, idx) =>
    resolveGateStatus(idx, stepStatuses, nextNodes, hasInterrupt)
  );

  // 다음 시작 가능한 대기 단계
  const nextPendingStepIdx = (() => {
    if (stepStatuses.some((s) => s === "active")) return -1;
    return stepStatuses.findIndex((s) => s === "pending");
  })();

  function handleStepClick(idx: number, status: NodeStatus) {
    if (status === "completed" || status === "review_pending") onStepClick?.(idx);
    if (status === "active") setExpandedStep(expandedStep === idx ? null : idx);
  }

  return (
    <div className={`bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5 ${className}`}>
      {/* 헤더 */}
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
              ${tokenSummary.total_cost_usd.toFixed(4)}
            </span>
          )}
        </div>
      </div>

      {/* 수평 그래프 */}
      <div className="flex items-start gap-0 overflow-x-auto pb-2">
        {WORKFLOW_STEPS.map((step, idx) => {
          const status = stepStatuses[idx];
          const isSelected = selectedStep === idx;
          const gateStatus = gateStatuses[idx];
          const gate = STEP_GATES[idx];
          const isLast = idx === WORKFLOW_STEPS.length - 1;

          return (
            <div key={step.step} className="flex items-start flex-shrink-0">
              {/* Step 노드 */}
              <StepNode
                step={step}
                idx={idx}
                status={status}
                isSelected={isSelected}
                isStarting={isStarting}
                isNextPending={idx === nextPendingStepIdx}
                onStepClick={() => handleStepClick(idx, status)}
                onStartStep={onStartStep ? () => onStartStep(idx) : undefined}
              />

              {/* 연결선 + Gate + 연결선 */}
              {!isLast && gate && (
                <>
                  <div className="flex items-center mt-[18px]">
                    <div className={`h-[2px] w-2 ${gateStatus === "passed" ? "bg-[#3ecf8e]/40" : "bg-[#262626]"}`} />
                  </div>
                  <GateBox gate={gate} status={gateStatus} onApprove={() => onGateApprove?.(idx)} />
                  <div className="flex items-center mt-[18px]">
                    <div className={`h-[2px] w-2 ${gateStatus === "passed" ? "bg-[#3ecf8e]/40" : "bg-[#262626]"}`} />
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>

      {/* 세부 노드 펼침 */}
      {expandedStep !== null && (
        <SubNodeList stepIndex={expandedStep} nodeProgress={nodeProgress} currentNode={currentNode} />
      )}

      {/* 범례 */}
      <div className="flex items-center gap-3 mt-3 pt-3 border-t border-[#262626] flex-wrap">
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
        <div className="flex items-center gap-1.5 ml-1 pl-2 border-l border-[#363636]">
          <div className="w-3 h-2.5 rounded-sm bg-amber-500/20 border border-amber-500/50" />
          <span className="text-[10px] text-[#8c8c8c]">Gate</span>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// Step 원형 노드 (SVG 진행률 아크 포함)
// ══════════════════════════════════════════════════════════

const CIRCLE_SIZE = 44;

function StepNode({
  step,
  idx,
  status,
  isSelected,
  isStarting,
  isNextPending,
  onStepClick,
  onStartStep,
}: {
  step: { step: number; label: string };
  idx: number;
  status: NodeStatus;
  isSelected: boolean;
  isStarting: boolean;
  isNextPending: boolean;
  onStepClick: () => void;
  onStartStep?: () => void;
}) {
  const estSec = STEP_EST_SECONDS[idx] ?? 180;
  const progress = useStepProgress(status === "active", estSec);
  const pctText = status === "active" ? `${Math.round(progress * 100)}%` : null;

  return (
    <div className="flex flex-col items-center w-[72px]">
      {/* 원 + SVG 진행률 */}
      <div className="relative" style={{ width: CIRCLE_SIZE, height: CIRCLE_SIZE }}>
        {/* 진행 아크 (active 상태) */}
        {status === "active" && <ProgressCircle progress={progress} size={CIRCLE_SIZE} />}

        {/* 원형 버튼 */}
        <button
          onClick={onStepClick}
          title={status === "completed" ? STEP_COMPLETED_HINT[idx] : undefined}
          aria-label={`STEP ${step.step}: ${step.label}`}
          className={`absolute inset-[3px] rounded-full flex items-center justify-center text-xs font-bold transition-all ${
            isSelected ? "ring-2 ring-[#3ecf8e] ring-offset-1 ring-offset-[#1c1c1c]" : ""
          } ${
            status === "completed"
              ? "bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#49e59e] cursor-pointer"
              : status === "active"
              ? "bg-[#0f0f0f] border-0 text-[#3ecf8e] cursor-pointer"
              : status === "review_pending"
              ? "bg-amber-500/20 border-2 border-amber-500 text-amber-400 cursor-pointer"
              : "bg-[#262626] border border-[#363636] text-[#5c5c5c] cursor-default"
          }`}
        >
          {status === "completed" ? (
            <CheckIcon />
          ) : status === "active" ? (
            <span className="text-[10px] font-bold text-[#3ecf8e]">{pctText}</span>
          ) : status === "review_pending" ? (
            <EyeIcon />
          ) : (
            step.step
          )}
        </button>
      </div>

      {/* 라벨 */}
      <span className={`mt-1 text-[10px] font-medium text-center leading-tight ${
        status === "completed" ? "text-[#3ecf8e]"
        : status === "active" ? "text-[#ededed]"
        : status === "review_pending" ? "text-amber-400"
        : "text-[#5c5c5c]"
      }`}>
        {step.label}
      </span>

      {/* 하단 버튼: Start / Finish */}
      {status === "pending" && isNextPending && onStartStep && (
        <button
          onClick={(e) => { e.stopPropagation(); onStartStep(); }}
          disabled={isStarting}
          className="mt-1 px-3 py-1 text-[9px] font-bold rounded-full bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#49e59e] disabled:opacity-50 transition-colors"
        >
          {isStarting ? "..." : "Start"}
        </button>
      )}
      {status === "completed" && (
        <span className="mt-1 px-3 py-1 text-[9px] font-medium rounded-full bg-[#3ecf8e]/10 text-[#3ecf8e] border border-[#3ecf8e]/20">
          Finish
        </span>
      )}
      {status === "active" && (
        <span className="mt-1 text-[8px] text-[#3ecf8e]/60">
          ~{Math.round((STEP_EST_SECONDS[idx] ?? 180) / 60)}분
        </span>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// Gate 승인 박스
// ══════════════════════════════════════════════════════════

function GateBox({ gate, status, onApprove }: { gate: GateDef; status: GateStatus; onApprove: () => void }) {
  return (
    <div className="flex flex-col items-center mt-[4px] flex-shrink-0">
      <div className={`relative flex flex-col items-center justify-center rounded-lg px-2 py-1.5 min-w-[54px] transition-all ${
        status === "active"
          ? "bg-amber-500/15 border-2 border-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.15)]"
          : status === "passed"
          ? "bg-[#3ecf8e]/10 border border-[#3ecf8e]/30"
          : "bg-[#111111] border border-[#262626]"
      }`}>
        <div className={`w-5 h-5 flex items-center justify-center ${
          status === "active" ? "text-amber-400" : status === "passed" ? "text-[#3ecf8e]" : "text-[#5c5c5c]"
        }`}>
          {status === "passed" ? <CheckIcon /> : status === "active" ? <GateIcon /> : <LockIcon />}
        </div>
        <span className={`text-[8px] font-medium text-center leading-tight mt-0.5 ${
          status === "active" ? "text-amber-400" : status === "passed" ? "text-[#3ecf8e]/70" : "text-[#5c5c5c]"
        }`}>
          {gate.shortLabel}
        </span>

        {status === "active" && (
          <button
            onClick={(e) => { e.stopPropagation(); onApprove(); }}
            className="mt-1 px-2.5 py-[3px] text-[8px] font-bold rounded bg-amber-500 text-[#0f0f0f] hover:bg-amber-400 transition-colors whitespace-nowrap"
          >
            승인
          </button>
        )}
        {status === "active" && (
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-amber-500 animate-ping" />
        )}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// 세부 노드 목록
// ══════════════════════════════════════════════════════════

function SubNodeList({ stepIndex, nodeProgress, currentNode }: {
  stepIndex: number; nodeProgress?: Map<string, NodeProgress>; currentNode: string;
}) {
  const stepDef = WORKFLOW_STEPS[stepIndex];
  if (!stepDef) return null;
  return (
    <div className="mt-3 pt-3 border-t border-[#262626]">
      <p className="text-[10px] text-[#8c8c8c] mb-2">STEP {stepDef.step} 세부 진행</p>
      <div className="flex flex-wrap gap-1.5">
        {stepDef.nodes.map((node) => {
          const progress = nodeProgress?.get(node);
          const isCurrent = currentNode === node;
          const isCompleted = progress?.status === "completed";
          return (
            <div key={node} className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] transition-colors ${
              isCurrent ? "bg-[#3ecf8e]/10 border border-[#3ecf8e]/30 text-[#3ecf8e]"
              : isCompleted ? "bg-[#262626] text-[#3ecf8e]"
              : "bg-[#111111] border border-[#262626] text-[#5c5c5c]"
            }`}>
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

// ══════════════════════════════════════════════════════════
// SVG 아이콘
// ══════════════════════════════════════════════════════════

function CheckIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}

function EyeIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  );
}

function GateIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
    </svg>
  );
}
