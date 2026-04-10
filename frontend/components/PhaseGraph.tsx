"use client";

/**
 * PhaseGraph v7 — 분기·통합 워크플로
 *
 * 1 ─□─ 2 ─┬─ A: 3A─□─4A─□─5A─□─6A ─┐─□─ 7
 *           └─ B: 3B─□─4B─□─5B─□─6B ─┘
 */

import { useEffect, useRef, useState } from "react";
import {
  HEAD_STEPS,
  PROPOSAL_STEPS,
  BIDDING_STEPS,
  TAIL_STEPS,
  WORKFLOW_STEPS,
  type WorkflowStepDef,
  type WorkflowState,
} from "@/lib/api";
import type { NodeProgress } from "@/lib/hooks/useWorkflowStream";

// ── 라벨 ──

const NL: Record<string, string> = {
  rfp_analyze: "RFP 분석",
  research_gather: "리서치",
  go_no_go: "Go/No-Go",
  strategy_generate: "전략 수립",
  plan_team: "팀구성",
  plan_assign: "역할배분",
  plan_schedule: "일정",
  plan_story: "스토리라인",
  plan_price: "예산산정",
  proposal_write_next: "섹션 작성",
  section_quality_check: "품질 진단",
  storyline_gap_analysis: "갭 분석",
  self_review: "자가진단",
  presentation_strategy: "발표전략",
  ppt_toc: "PPT 목차",
  ppt_visual_brief: "시각설계",
  ppt_storyboard: "슬라이드",
  bid_plan: "입찰가 결정",
  cost_sheet_generate: "산출내역서",
  submission_plan: "제출서류 계획",
  submission_checklist: "제출서류 확인",
  mock_evaluation: "모의 평가",
  eval_result: "평가결과",
  project_closing: "Closing",
};

const EST: Record<string, number> = {
  "RFP 분석": 120,
  "전략 수립": 180,
  "제안 계획": 300,
  "제안서 작성": 480,
  "PPT 생성": 180,
  "모의 평가": 120,
  "제출서류 계획": 60,
  "입찰가 결정": 120,
  산출내역서: 60,
  "제출서류 확인": 60,
  "평가결과·Closing": 60,
};

// ── Gate ──

interface GDef {
  id: string;
  label: string;
  rn: string[];
}

const HEAD_G: GDef[] = [
  { id: "g1", label: "검토", rn: ["review_rfp", "review_gng"] },
  { id: "g2", label: "검토", rn: ["review_strategy"] },
];
const A_G: GDef[] = [
  { id: "gA3", label: "검토", rn: ["review_plan"] },
  { id: "gA4", label: "검토", rn: ["review_section", "review_gap_analysis", "review_proposal"] },
  { id: "gA5", label: "검토", rn: ["review_ppt"] },
  { id: "gA6", label: "검토", rn: ["review_mock_eval"] },
];
const B_G: GDef[] = [
  { id: "gB3", label: "검토", rn: ["review_submission_plan"] },
  { id: "gB4", label: "검토", rn: ["review_bid_plan"] },
  { id: "gB5", label: "검토", rn: ["review_cost_sheet"] },
  { id: "gB6", label: "검토", rn: ["review_submission"] },
];
const TAIL_G: GDef[] = [
  { id: "g7", label: "확인", rn: ["review_eval_result"] },
];

const ALL_RN = [...HEAD_G, ...A_G, ...B_G, ...TAIL_G].flatMap((g) => g.rn);

// ── 상태 ──

type NS = "completed" | "active" | "review_pending" | "pending";
type GS = "passed" | "active" | "locked";

function rStep(
  s: WorkflowStepDef,
  cur: string,
  nxt: string[],
  intr: boolean,
): NS {
  const act = s.nodes.some((n) => cur.includes(n) || cur === n);
  const rp = intr && nxt.some((n) => ALL_RN.includes(n));
  const same = WORKFLOW_STEPS.filter((w) => w.path === s.path);
  const ci = same.findIndex((w) =>
    w.nodes.some((n) => cur.includes(n) || cur === n),
  );
  const mi = same.indexOf(s);
  // 같은 경로 내에서 앞 step이면 완료
  if (ci >= 0 && mi < ci) return "completed";
  // head가 모두 완료 + 분기 경로 진행 중이면 head는 completed
  if (s.path === "head") {
    const inBranch = WORKFLOW_STEPS.some(
      (w) =>
        (w.path === "proposal" || w.path === "bidding" || w.path === "tail") &&
        w.nodes.some((n) => cur.includes(n)),
    );
    if (inBranch) return "completed";
  }
  // tail 진행 중이면 분기 경로는 completed
  if (s.path === "proposal" || s.path === "bidding") {
    const inTail = TAIL_STEPS.some((t) => t.nodes.some((n) => cur.includes(n)));
    if (inTail) return "completed";
  }
  if (act && rp) return "review_pending";
  if (act) return "active";
  return "pending";
}

function rGate(g: GDef, prev: NS, nxt: string[], intr: boolean): GS {
  if (g.rn.length > 0 && intr && nxt.some((n) => g.rn.includes(n)))
    return "active";
  if (prev === "completed") return "passed";
  return "locked";
}

// ── SVG ──

function Ring({ p, sz = 38 }: { p: number; sz?: number }) {
  const s = 3,
    r = (sz - s) / 2,
    c = 2 * Math.PI * r;
  return (
    <svg
      className="absolute inset-0"
      width={sz}
      height={sz}
      style={{ transform: "rotate(-90deg)" }}
    >
      <circle
        cx={sz / 2}
        cy={sz / 2}
        r={r}
        fill="none"
        stroke="#262626"
        strokeWidth={s}
      />
      <circle
        cx={sz / 2}
        cy={sz / 2}
        r={r}
        fill="none"
        stroke="#3ecf8e"
        strokeWidth={s}
        strokeLinecap="round"
        strokeDasharray={c}
        strokeDashoffset={c - Math.min(p, 1) * c}
        className="transition-all duration-1000"
      />
    </svg>
  );
}

function useProg(a: boolean, e: number) {
  const [p, setP] = useState(0);
  const t = useRef(Date.now());
  useEffect(() => {
    if (!a) {
      setP(0);
      return;
    }
    t.current = Date.now();
    const id = setInterval(
      () => setP(Math.min((Date.now() - t.current) / 1000 / e, 0.95)),
      500,
    );
    return () => clearInterval(id);
  }, [a, e]);
  return p;
}

// ── Props ──

interface Props {
  workflowState: WorkflowState | null;
  nodeProgress?: Map<string, NodeProgress>;
  currentNode?: string;
  selectedStep?: number | null;
  onStepClick?: (i: number) => void;
  onStartStep?: (i: number) => void;
  onGateApprove?: (i: number) => void;
  onMoveToNode?: (nodeKey: string) => void;
  isStarting?: boolean;
  isGateApproving?: boolean;
  isPaused?: boolean;
  elapsed?: string;
  onAbort?: () => void;
  aborting?: boolean;
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
  onMoveToNode,
  isStarting = false,
  isGateApproving = false,
  isPaused = false,
  elapsed,
  onAbort,
  aborting = false,
  className = "",
}: Props) {
  const cur = workflowState?.current_step ?? "";
  const nxt = workflowState?.next_nodes ?? [];
  const intr = workflowState?.has_pending_interrupt ?? false;
  const [exp, setExp] = useState<number | null>(null);

  const hS = HEAD_STEPS.map((s) => rStep(s, cur, nxt, intr));
  const aS = PROPOSAL_STEPS.map((s) => rStep(s, cur, nxt, intr));
  const bS = BIDDING_STEPS.map((s) => rStep(s, cur, nxt, intr));
  const tS = TAIL_STEPS.map((s) => rStep(s, cur, nxt, intr));

  const hG = HEAD_G.map((g, i) => rGate(g, hS[i], nxt, intr));
  const aG = A_G.map((g, i) => rGate(g, aS[i], nxt, intr));
  const bG = B_G.map((g, i) => rGate(g, bS[i], nxt, intr));
  // convergence gate: A·B 트랙 모두 완료 시 passed
  const convergePrev: NS =
    aS[aS.length - 1] === "completed" && bS[bS.length - 1] === "completed"
      ? "completed"
      : "pending";
  const tG = TAIL_G.map((g) => rGate(g, convergePrev, nxt, intr));

  const allSt = [...hS, ...aS, ...bS, ...tS];
  const hasActive = allSt.some((s) => s === "active");
  const nextP = hasActive
    ? -1
    : (() => {
        for (const s of HEAD_STEPS)
          if (rStep(s, cur, nxt, intr) === "pending")
            return WORKFLOW_STEPS.indexOf(s);
        for (const s of PROPOSAL_STEPS)
          if (rStep(s, cur, nxt, intr) === "pending")
            return WORKFLOW_STEPS.indexOf(s);
        for (const s of TAIL_STEPS)
          if (rStep(s, cur, nxt, intr) === "pending")
            return WORKFLOW_STEPS.indexOf(s);
        return -1;
      })();

  function clk(i: number, s: NS) {
    if (s === "completed" || s === "review_pending") onStepClick?.(i);
    if (s === "active") setExp(exp === i ? null : i);
  }

  // 공통 offset (head 행의 실제 가로폭: 노드*50 + 렌더링 게이트*(Ln+Gt+Ln))
  const headW =
    HEAD_STEPS.length * 50 + Math.max(HEAD_STEPS.length - 1, 0) * 40 + 4;

  return (
    <div
      className={`bg-[#1c1c1c] rounded-2xl border border-[#262626] p-4 ${className}`}
    >
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-semibold text-[#ededed]">워크플로 진행</h2>
        {currentNode && (
          <span className="text-[10px] text-[#3ecf8e] bg-[#3ecf8e]/10 rounded px-2 py-0.5 animate-pulse">
            {NL[currentNode] || currentNode}
          </span>
        )}
      </div>

      {/* ═══ 그래프 ═══ */}
      <div className="overflow-x-auto pb-1">
        <div className="inline-flex flex-col min-w-max">
          {/* ── 1행: Head + A ── */}
          <div className="flex items-start">
            <Row
              steps={HEAD_STEPS}
              sts={hS}
              gates={HEAD_G}
              gs={hG}
              np={nextP}
              sel={selectedStep}
              st={isStarting}
              ap={isGateApproving}
              clk={clk}
              start={onStartStep}
              gate={onGateApprove}
              move={onMoveToNode}
            />
            {/* 분기선 → A */}
            <div className="flex items-center mt-[16px] mx-0.5 shrink-0">
              <div className="h-[2px] w-1.5 bg-[#363636]" />
            </div>
            <div className="flex items-center shrink-0 mr-0.5">
              <span className="text-[7px] text-blue-400 bg-blue-500/10 rounded px-1 py-px font-bold">
                A
              </span>
            </div>
            <div className="flex items-center mt-[16px] mr-0.5 shrink-0">
              <div className="h-[2px] w-1 bg-[#363636]" />
            </div>
            <Row
              steps={PROPOSAL_STEPS}
              sts={aS}
              gates={A_G}
              gs={aG}
              np={nextP}
              sel={selectedStep}
              st={isStarting}
              ap={isGateApproving}
              clk={clk}
              start={onStartStep}
              gate={onGateApprove}
              move={onMoveToNode}
            />
            {/* 통합선 + convergence gate → Tail */}
            <Ln ok={tG[0] === "passed"} />
            <Gt
              g={TAIL_G[0]}
              s={tG[0]}
              approve={() =>
                onGateApprove?.(WORKFLOW_STEPS.indexOf(TAIL_STEPS[0]))
              }
              ap={isGateApproving}
            />
            <Ln ok={tG[0] === "passed"} />
            <Row
              steps={TAIL_STEPS}
              sts={tS}
              gates={[]}
              gs={[]}
              np={nextP}
              sel={selectedStep}
              st={isStarting}
              ap={isGateApproving}
              clk={clk}
              start={onStartStep}
              gate={onGateApprove}
              move={onMoveToNode}
            />
          </div>

          {/* ── 분기 수직선 ── */}
          <div style={{ marginLeft: headW - 4 }} className="flex items-stretch">
            <div className="w-[2px] h-2 bg-[#363636]" />
          </div>

          {/* ── 2행: B (offset = headW) ── */}
          <div className="flex items-start" style={{ marginLeft: headW - 4 }}>
            <div className="flex items-center shrink-0 mr-0.5">
              <div className="h-[2px] w-1.5 bg-[#363636]" />
              <span className="text-[7px] text-amber-400 bg-amber-500/10 rounded px-1 py-px font-bold mx-0.5">
                B
              </span>
              <div className="h-[2px] w-1 bg-[#363636]" />
            </div>
            <Row
              steps={BIDDING_STEPS}
              sts={bS}
              gates={B_G}
              gs={bG}
              np={nextP}
              sel={selectedStep}
              st={isStarting}
              ap={isGateApproving}
              clk={clk}
              start={onStartStep}
              gate={onGateApprove}
              move={onMoveToNode}
            />
            {/* 통합 올라가는 선 */}
            <div className="flex items-center mt-[16px] ml-0.5 shrink-0">
              <div className="h-[2px] w-3 bg-[#363636]" />
              <div className="text-[8px] text-[#5c5c5c]">↗</div>
            </div>
          </div>
        </div>
      </div>

      {/* 세부 노드 */}
      {exp !== null && <Sub idx={exp} np={nodeProgress} cn={currentNode} />}

      {/* 상태 */}
      {isPaused && (
        <div className="flex items-center gap-2 bg-amber-500/5 border border-amber-500/20 rounded-xl px-4 py-2 mt-3">
          <span className="w-2 h-2 rounded-sm bg-amber-500" />
          <span className="text-xs font-medium text-amber-400">일시정지됨</span>
          <span className="text-[10px] text-[#8c8c8c]">{cur}</span>
        </div>
      )}
      {!isPaused && hasActive && elapsed && (
        <div className="flex items-center justify-between mt-3 px-1">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full border-2 border-[#3ecf8e] border-t-transparent animate-spin" />
            <span className="text-[10px] text-[#8c8c8c]">경과 {elapsed}</span>
          </div>
          {onAbort && (
            <button
              onClick={onAbort}
              disabled={aborting}
              className="text-[10px] text-amber-400 border border-amber-500/30 rounded-lg px-2 py-0.5 hover:text-amber-300 disabled:opacity-40 transition-colors"
            >
              {aborting ? "중단중..." : "일시정지"}
            </button>
          )}
        </div>
      )}

      {/* 범례 */}
      <div className="flex items-center gap-3 mt-3 pt-2 border-t border-[#262626] flex-wrap text-[9px] text-[#8c8c8c]">
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-[#3ecf8e]" />
          완료
        </span>
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-[#3ecf8e]/30 border border-[#3ecf8e]" />
          진행
        </span>
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500/30 border border-amber-500" />
          승인대기
        </span>
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-[#262626] border border-[#363636]" />
          미시작
        </span>
        <span className="ml-1 pl-2 border-l border-[#363636] flex items-center gap-1">
          <span className="text-blue-400 font-bold">A</span>제안서
        </span>
        <span className="flex items-center gap-1">
          <span className="text-amber-400 font-bold">B</span>입찰·제출
        </span>
        {onMoveToNode && (
          <span className="flex items-center gap-1 pl-2 border-l border-[#363636]">
            <span className="w-3 h-3 rounded-full bg-blue-500 text-white text-[7px] font-bold flex items-center justify-center">
              ↩
            </span>
            완료 노드 hover → 재이동
          </span>
        )}
      </div>
    </div>
  );
}

// ── Row ──

function Row({
  steps,
  sts,
  gates,
  gs,
  np,
  sel,
  st,
  ap,
  clk,
  start,
  gate,
  move,
}: {
  steps: readonly WorkflowStepDef[];
  sts: NS[];
  gates: GDef[];
  gs: GS[];
  np: number;
  sel: number | null;
  st: boolean;
  ap: boolean;
  clk: (i: number, s: NS) => void;
  start?: (i: number) => void;
  gate?: (i: number) => void;
  move?: (nodeKey: string) => void;
}) {
  return (
    <div className="flex items-start">
      {steps.map((step, i) => {
        const gi = WORKFLOW_STEPS.indexOf(step as WorkflowStepDef);
        const s = sts[i];
        const g = gates[i];
        const gst = gs[i];
        const last = i === steps.length - 1;
        return (
          <div
            key={`${step.path}-${step.stepLabel}`}
            className="flex items-start shrink-0"
          >
            <Dot
              step={step}
              gi={gi}
              s={s}
              sel={sel === gi}
              nxt={gi === np}
              st={st}
              clk={() => clk(gi, s)}
              start={start ? () => start(gi) : undefined}
              move={
                move ? () => move(step.nodes[0] ?? step.stepLabel) : undefined
              }
            />
            {!last && g && (
              <>
                <Ln ok={gst === "passed"} />
                <Gt g={g} s={gst} approve={() => gate?.(gi)} ap={ap} />
                <Ln ok={gst === "passed"} />
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}

function Ln({ ok }: { ok: boolean }) {
  return (
    <div className="flex items-center mt-[16px]">
      <div
        className={`h-[2px] w-1 ${ok ? "bg-[#3ecf8e]/40" : "bg-[#262626]"}`}
      />
    </div>
  );
}

// ── Dot ──

const SZ = 38;

function Dot({
  step,
  gi,
  s,
  sel,
  nxt,
  st,
  clk,
  start,
  move,
}: {
  step: WorkflowStepDef;
  gi: number;
  s: NS;
  sel: boolean;
  nxt: boolean;
  st: boolean;
  clk: () => void;
  start?: () => void;
  move?: () => void;
}) {
  const prog = useProg(s === "active", EST[step.label] ?? 120);
  const [hovered, setHovered] = useState(false);
  return (
    <div
      className="flex flex-col items-center w-[50px] relative"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div className="relative" style={{ width: SZ, height: SZ }}>
        {s === "active" && <Ring p={prog} sz={SZ} />}
        <button
          onClick={clk}
          aria-label={step.label}
          className={`absolute inset-[2px] rounded-full flex items-center justify-center text-[9px] font-bold transition-all ${
            sel
              ? "ring-2 ring-[#3ecf8e] ring-offset-1 ring-offset-[#1c1c1c]"
              : ""
          } ${
            s === "completed"
              ? "bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#49e59e] cursor-pointer"
              : s === "active"
                ? "bg-[#0f0f0f] text-[#3ecf8e] cursor-pointer"
                : s === "review_pending"
                  ? "bg-amber-500/20 border-2 border-amber-500 text-amber-400 cursor-pointer"
                  : "bg-[#262626] border border-[#363636] text-[#5c5c5c]"
          }`}
        >
          {s === "completed" ? (
            <Chk />
          ) : s === "active" ? (
            `${Math.round(prog * 100)}%`
          ) : s === "review_pending" ? (
            <Eye />
          ) : (
            step.stepLabel
          )}
        </button>
        {/* 이 노드로 이동 버튼 — 완료 노드 hover 시 표시 */}
        {s === "completed" && hovered && move && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              move();
            }}
            title="이 노드로 이동"
            className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-blue-500 text-white flex items-center justify-center text-[7px] font-bold hover:bg-blue-400 z-10 shadow"
          >
            ↩
          </button>
        )}
      </div>
      <span
        className={`mt-0.5 text-[8px] font-medium text-center leading-tight w-full truncate ${
          s === "completed"
            ? "text-[#3ecf8e]"
            : s === "active"
              ? "text-[#ededed]"
              : s === "review_pending"
                ? "text-amber-400"
                : "text-[#5c5c5c]"
        }`}
      >
        {step.label}
      </span>
      {s === "pending" && nxt && start && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            start();
          }}
          disabled={st}
          className="mt-0.5 px-1.5 py-px text-[7px] font-bold rounded-full bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#49e59e] disabled:opacity-50"
        >
          {st ? "..." : "Start"}
        </button>
      )}
      {s === "completed" && (
        <button
          onClick={clk}
          className="mt-0.5 px-1.5 py-px text-[7px] rounded-full bg-[#3ecf8e]/10 text-[#3ecf8e] hover:underline cursor-pointer"
        >
          결과보기
        </button>
      )}
    </div>
  );
}

// ── Gate ──

function Gt({
  g,
  s,
  approve,
  ap,
}: {
  g: GDef;
  s: GS;
  approve: () => void;
  ap: boolean;
}) {
  return (
    <div className="flex flex-col items-center mt-[4px] shrink-0">
      <div
        className={`relative flex flex-col items-center justify-center rounded px-1 py-0.5 min-w-[32px] transition-all ${
          s === "active"
            ? "bg-amber-500/15 border-2 border-amber-500"
            : s === "passed"
              ? "bg-[#3ecf8e]/10 border border-[#3ecf8e]/30"
              : "bg-[#111] border border-[#1e1e1e]"
        }`}
      >
        <div
          className={`w-3 h-3 flex items-center justify-center ${
            s === "active"
              ? "text-amber-400"
              : s === "passed"
                ? "text-[#3ecf8e]"
                : "text-[#4a4a4a]"
          }`}
        >
          {s === "passed" ? <Chk /> : s === "active" ? <Shield /> : <Lock />}
        </div>
        {s === "active" && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              approve();
            }}
            disabled={ap}
            className="mt-0.5 px-1.5 py-[1px] text-[6px] font-bold rounded bg-amber-500 text-[#0f0f0f] hover:bg-amber-400 disabled:opacity-50 whitespace-nowrap"
          >
            {ap ? "..." : "승인"}
          </button>
        )}
        {s === "active" && (
          <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-amber-500 animate-ping" />
        )}
      </div>
    </div>
  );
}

// ── Sub ──

function Sub({
  idx,
  np,
  cn,
}: {
  idx: number;
  np?: Map<string, NodeProgress>;
  cn: string;
}) {
  const s = WORKFLOW_STEPS[idx];
  if (!s) return null;
  return (
    <div className="mt-3 pt-3 border-t border-[#262626]">
      <p className="text-[10px] text-[#8c8c8c] mb-2">
        {s.stepLabel} {s.label} 세부
      </p>
      <div className="flex flex-wrap gap-1.5">
        {s.nodes.map((n) => {
          const c = cn === n,
            d = np?.get(n)?.status === "completed";
          return (
            <div
              key={n}
              className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] ${
                c
                  ? "bg-[#3ecf8e]/10 border border-[#3ecf8e]/30 text-[#3ecf8e]"
                  : d
                    ? "bg-[#262626] text-[#3ecf8e]"
                    : "bg-[#111] border border-[#262626] text-[#5c5c5c]"
              }`}
            >
              {c ? (
                <div className="w-2 h-2 rounded-full border border-[#3ecf8e] border-t-transparent animate-spin" />
              ) : d ? (
                <span>✓</span>
              ) : (
                <span className="w-1.5 h-1.5 rounded-full bg-[#363636]" />
              )}
              {NL[n] || n}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Icons ──

function Chk() {
  return (
    <svg
      className="w-3 h-3"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={3}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}
function Eye() {
  return (
    <svg
      className="w-3 h-3"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
      />
    </svg>
  );
}
function Shield() {
  return (
    <svg
      className="w-3 h-3"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
      />
    </svg>
  );
}
function Lock() {
  return (
    <svg
      className="w-2.5 h-2.5"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
      />
    </svg>
  );
}
