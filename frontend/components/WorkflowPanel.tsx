"use client";

/**
 * WorkflowPanel — Go/No-Go + 리뷰 + 병렬 진행 통합 패널 (§13-4, §13-5, §13-7)
 *
 * 워크플로 상태에 따라 적절한 패널을 표시:
 * - Go/No-Go 의사결정 (STEP 1-②)
 * - 리뷰 승인/재작업 (STEP 2~5 체크포인트)
 * - 병렬 작업 진행 (STEP 3 fan-out)
 */

import { useState, useEffect } from "react";
import {
  api,
  WORKFLOW_STEPS,
  type WorkflowState,
  type WorkflowResumeData,
} from "@/lib/api";
import GoNoGoPanel from "@/components/GoNoGoPanel";

// ── 리뷰 게이트 정의 ──

const REVIEW_GATES: Record<
  string,
  { title: string; perspective: string; step: number }
> = {
  review_search: {
    title: "공고 검색 결과 검토",
    perspective: "이 공고들 중 관심 과제가 있는가?",
    step: 0,
  },
  review_rfp: {
    title: "RFP 분석 결과 검토",
    perspective: "분석 내용이 정확하고 빠뜨린 요구사항은 없는가?",
    step: 1,
  },
  review_gng: {
    title: "Go/No-Go 의사결정",
    perspective: "이 입찰에 자원을 투입할 가치가 있는가?",
    step: 1,
  },
  review_strategy: {
    title: "제안전략 검토",
    perspective: "이 전략으로 경쟁에서 이길 수 있는가?",
    step: 2,
  },
  review_plan: {
    title: "제안계획서 검토",
    perspective: "이 계획대로 실행 가능한가? 일정은 현실적인가?",
    step: 3,
  },
  review_section: {
    title: "섹션별 검토",
    perspective: "이 섹션의 내용이 요구사항을 충족하는가?",
    step: 4,
  },
  review_proposal: {
    title: "제안서 최종 검토",
    perspective: "전체 품질과 일관성이 확보되었는가?",
    step: 4,
  },
  review_ppt: {
    title: "PPT 검토",
    perspective: "발표 자료가 핵심을 효과적으로 전달하는가?",
    step: 5,
  },
};

// STEP 3 병렬 노드
const PARALLEL_NODES = [
  { key: "plan_team", label: "팀구성" },
  { key: "plan_assign", label: "담당자" },
  { key: "plan_schedule", label: "일정" },
  { key: "plan_story", label: "스토리라인" },
  { key: "plan_price", label: "입찰가격" },
];

// ── 컴포넌트 ──

interface WorkflowPanelProps {
  proposalId: string;
  workflowState: WorkflowState | null;
  onStateChange?: () => void;
  className?: string;
}

export default function WorkflowPanel({
  proposalId,
  workflowState,
  onStateChange,
  className = "",
}: WorkflowPanelProps) {
  if (!workflowState) return null;

  const { current_step, has_pending_interrupt, next_nodes, positioning } =
    workflowState;

  // paused 상태 (abort 후 interrupt 없이 멈춘 경우)
  const isPausedState = !has_pending_interrupt && !next_nodes.length && current_step && !current_step.includes("complete");
  if (isPausedState && current_step.includes("error")) {
    // 에러 상태는 상위에서 처리
  }

  // 리뷰 게이트 감지
  const activeReview = has_pending_interrupt
    ? next_nodes.find((n) => REVIEW_GATES[n])
    : null;

  // Go/No-Go 패널
  const isGoNoGo = activeReview === "review_gng";

  // 병렬 진행 감지 (STEP 3 노드가 현재 실행 중)
  const step3Nodes = WORKFLOW_STEPS.find(s => s.step === 3)?.nodes ?? [];
  const isParallelActive =
    !has_pending_interrupt &&
    step3Nodes.some(
      (n) => current_step.includes(n) || current_step === n
    );

  if (isGoNoGo) {
    return (
      <GoNoGoPanel
        proposalId={proposalId}
        workflowState={workflowState}
        onStateChange={onStateChange}
        className={className}
      />
    );
  }

  if (activeReview) {
    return (
      <ReviewPanel
        proposalId={proposalId}
        reviewNode={activeReview}
        workflowState={workflowState}
        onStateChange={onStateChange}
        className={className}
      />
    );
  }

  if (isParallelActive) {
    return (
      <ParallelProgress
        workflowState={workflowState}
        className={className}
      />
    );
  }

  return null;
}

// ── AI 이슈 플래그 타입 ──

interface AiIssue {
  section: string;
  score: number;
  issue: string;
}

// ── 리뷰 패널 (§13-5) ── AI 이슈 플래그 + 섹션별 인라인 피드백

function ReviewPanel({
  proposalId,
  reviewNode,
  workflowState,
  onStateChange,
  className,
}: {
  proposalId: string;
  reviewNode: string;
  workflowState: WorkflowState;
  onStateChange?: () => void;
  className: string;
}) {
  const gate = REVIEW_GATES[reviewNode];
  const [feedback, setFeedback] = useState("");
  const [reworkTargets, setReworkTargets] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  // W3: 산출물 요약 인라인
  const [artifactSummary, setArtifactSummary] = useState<string | null>(null);
  // W11: 산출물/이슈 영역 접기
  const [detailsCollapsed, setDetailsCollapsed] = useState(false);

  // AI 이슈 플래그 (자가진단 < 70점 항목)
  const [aiIssues, setAiIssues] = useState<AiIssue[]>([]);
  const [issuesLoaded, setIssuesLoaded] = useState(false);

  // 섹션별 인라인 피드백
  const [sectionFeedbacks, setSectionFeedbacks] = useState<
    Record<string, string>
  >({});
  const [expandedSections, setExpandedSections] = useState(false);

  // STEP 3 리뷰: 재작업 대상 선택
  const isStepPlan = gate?.step === 3;
  const reworkOptions = isStepPlan ? PARALLEL_NODES : [];

  // STEP 4 리뷰: AI 이슈 플래그 로드
  const isProposalReview =
    reviewNode === "review_proposal" || reviewNode === "review_section";

  // W3: 산출물 요약 로드 (리뷰 대상 단계의 산출물)
  useEffect(() => {
    const artifactMap: Record<string, string> = {
      review_rfp: "rfp_analysis",
      review_strategy: "strategy",
      review_bid_plan: "bid_plan",
      review_plan: "plan",
      review_proposal: "proposal",
      review_ppt: "ppt",
    };
    const artifactKey = artifactMap[reviewNode];
    if (!artifactKey) return;
    api.artifacts.get(proposalId, artifactKey).then((a) => {
      const d = a.data as Record<string, unknown>;
      // 요약 필드 우선순위: summary > recommendation > title
      const summary = (d.summary || d.recommendation || d.title || "") as string;
      if (summary) setArtifactSummary(typeof summary === "string" ? summary : JSON.stringify(summary).slice(0, 200));
    }).catch(() => {});
  }, [proposalId, reviewNode]);

  // 이슈 로드 (최초 1회)
  useEffect(() => {
    if (!isProposalReview || issuesLoaded) return;
    setIssuesLoaded(true);
    api.artifacts
      .get(proposalId, "self_review")
      .then((artifact) => {
        const data = artifact.data as Record<string, unknown>;
        const evalSim = data.evaluation_simulation as
          | { weaknesses?: AiIssue[] }
          | undefined;
        const sections = data.section_scores as
          | Array<{ section: string; score: number; issue?: string }>
          | undefined;

        const issues: AiIssue[] = [];

        // 섹션별 자가진단 점수에서 < 70점 항목 추출
        if (Array.isArray(sections)) {
          for (const s of sections) {
            if (s.score < 70) {
              issues.push({
                section: s.section,
                score: s.score,
                issue: s.issue ?? "자가진단 점수 미달",
              });
            }
          }
        }

        // 취약점에서도 추출
        if (evalSim?.weaknesses) {
          for (const w of (evalSim.weaknesses as unknown as Array<{
            area: string;
            description: string;
            related_section: string;
          }>)) {
            if (!issues.some((i) => i.section === w.related_section)) {
              issues.push({
                section: w.related_section || w.area,
                score: 0,
                issue: w.description,
              });
            }
          }
        }

        setAiIssues(issues);
      })
      .catch(() => {
        // 자가진단 데이터 없으면 무시
      });
  }, [isProposalReview, issuesLoaded, proposalId]);

  function toggleRework(key: string) {
    setReworkTargets((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  }

  function updateSectionFeedback(section: string, value: string) {
    setSectionFeedbacks((prev) => ({ ...prev, [section]: value }));
  }

  async function handleResume(approved: boolean, quickApprove = false) {
    setSubmitting(true);
    try {
      // 섹션별 피드백을 통합 피드백에 합침
      const sectionNotes = Object.entries(sectionFeedbacks)
        .filter(([, v]) => v.trim())
        .map(([sec, note]) => `[${sec}] ${note}`)
        .join("\n");
      const combinedFeedback = [feedback, sectionNotes]
        .filter(Boolean)
        .join("\n\n");

      const data: WorkflowResumeData = {
        approved,
        quick_approve: quickApprove,
        feedback: combinedFeedback || undefined,
        rework_targets: reworkTargets.length > 0 ? reworkTargets : undefined,
      };
      await api.workflow.resume(proposalId, data);
      onStateChange?.();
    } catch (e) {
      alert(e instanceof Error ? e.message : "요청 실패");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className={`bg-[#1c1c1c] rounded-2xl border border-amber-500/30 p-5 ${className}`}
    >
      {/* 헤더 */}
      <div className="flex items-center gap-2 mb-1">
        <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
        <h2 className="text-sm font-semibold text-[#ededed]">
          {gate?.title ?? "리뷰"}
        </h2>
        <span className="text-[10px] text-amber-400/80 bg-amber-500/10 px-2 py-0.5 rounded">
          STEP {gate?.step ?? "?"}
        </span>
      </div>
      <p className="text-xs text-[#8c8c8c] mb-2">{gate?.perspective}</p>

      {/* W9: 섹션 리뷰 진행률 */}
      {reviewNode === "review_section" && workflowState.current_section_index != null && workflowState.total_sections != null && (
        <div className="flex items-center gap-2 mb-3">
          <div className="flex-1 h-1.5 bg-[#262626] rounded-full overflow-hidden">
            <div
              className="h-full bg-[#3ecf8e] rounded-full transition-all duration-300"
              style={{ width: `${((workflowState.current_section_index + 1) / workflowState.total_sections) * 100}%` }}
            />
          </div>
          <span className="text-[10px] text-[#8c8c8c] shrink-0">
            {workflowState.current_section_index + 1}/{workflowState.total_sections} 섹션
          </span>
        </div>
      )}

      {/* AI 이슈 플래그 (§13-5 보강) */}
      {!detailsCollapsed && aiIssues.length > 0 && (
        <div className="mb-4">
          <p className="text-[10px] text-red-400 uppercase tracking-wider font-medium mb-2">
            AI 이슈 플래그 ({aiIssues.length}건)
          </p>
          <div className="space-y-1.5">
            {aiIssues.map((issue, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2 bg-red-500/5 border border-red-500/20 rounded-lg px-3 py-2"
              >
                <span className="text-red-400 text-[10px] font-bold shrink-0 mt-0.5">
                  {issue.score > 0 ? `${issue.score}점` : "!"}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] font-medium text-[#ededed]">
                    {issue.section}
                  </p>
                  <p className="text-[10px] text-[#8c8c8c]">{issue.issue}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* W11: 상세 접기/펼치기 */}
      {(artifactSummary || aiIssues.length > 0) && (
        <button
          onClick={() => setDetailsCollapsed(!detailsCollapsed)}
          className="text-[10px] text-[#5c5c5c] hover:text-[#8c8c8c] mb-2 transition-colors"
        >
          {detailsCollapsed ? "▸ AI 분석 상세 펼치기" : "▾ AI 분석 상세 접기"}
        </button>
      )}

      {/* W3: AI 산출물 요약 */}
      {!detailsCollapsed && artifactSummary && (
        <div className="mb-3 bg-[#111111] border border-[#262626] rounded-lg px-3 py-2.5">
          <p className="text-[10px] text-[#5c5c5c] uppercase tracking-wider mb-1">AI 산출물 요약</p>
          <p className="text-xs text-[#ededed] leading-relaxed">{artifactSummary}</p>
        </div>
      )}

      {/* 피드백 */}
      <textarea
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        placeholder="전체 피드백 (선택)"
        rows={2}
        className="w-full bg-[#111111] border border-[#262626] rounded-lg px-3 py-2 text-xs text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-amber-500/40 resize-none mb-3"
      />

      {/* 섹션별 인라인 피드백 (§13-5 보강) */}
      {isProposalReview && (
        <div className="mb-3">
          <button
            onClick={() => setExpandedSections(!expandedSections)}
            className="text-[10px] text-[#3ecf8e] hover:underline mb-2"
          >
            {expandedSections
              ? "▾ 섹션별 피드백 접기"
              : "▸ 섹션별 피드백 펼치기"}
          </button>
          {expandedSections && aiIssues.length > 0 && (
            <div className="space-y-2">
              {aiIssues.map((issue) => (
                <div key={issue.section}>
                  <label className="text-[10px] text-[#8c8c8c] mb-1 block">
                    {issue.section}
                  </label>
                  <textarea
                    value={sectionFeedbacks[issue.section] ?? ""}
                    onChange={(e) =>
                      updateSectionFeedback(issue.section, e.target.value)
                    }
                    placeholder={`${issue.section} 피드백...`}
                    rows={1}
                    className="w-full bg-[#111111] border border-[#262626] rounded px-2.5 py-1.5 text-[10px] text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:ring-1 focus:ring-amber-500/40 resize-none"
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 재작업 대상 선택 (STEP 3) */}
      {isStepPlan && reworkOptions.length > 0 && (
        <div className="mb-3">
          <p className="text-[10px] text-[#8c8c8c] mb-2">
            재작업 항목 선택 (선택 시 해당 항목만 재실행)
          </p>
          <div className="flex flex-wrap gap-1.5">
            {reworkOptions.map((opt) => (
              <button
                key={opt.key}
                onClick={() => toggleRework(opt.key)}
                className={`px-2.5 py-1 text-[10px] font-medium rounded border transition-colors ${
                  reworkTargets.includes(opt.key)
                    ? "bg-amber-500/15 text-amber-400 border-amber-500/40"
                    : "border-[#262626] text-[#8c8c8c] hover:border-[#3c3c3c]"
                }`}
              >
                {reworkTargets.includes(opt.key) ? "☑" : "☐"} {opt.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 버튼 */}
      <div className="flex gap-2">
        <button
          onClick={() => handleResume(false)}
          disabled={submitting}
          className="px-4 py-2 text-xs font-medium rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 disabled:opacity-40 transition-colors"
        >
          재작업 요청
        </button>
        <button
          onClick={() => handleResume(true, true)}
          disabled={submitting}
          title="피드백 없이 AI 결과를 그대로 사용합니다"
          className="px-4 py-2 text-xs font-medium rounded-lg border border-[#3ecf8e]/30 text-[#3ecf8e] hover:bg-[#3ecf8e]/10 disabled:opacity-40 transition-colors"
        >
          빠른 승인
        </button>
        <button
          onClick={() => handleResume(true)}
          disabled={submitting}
          className="px-4 py-2 text-xs font-bold rounded-lg bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#3ecf8e]/90 disabled:opacity-40 transition-colors"
        >
          승인
        </button>
      </div>
    </div>
  );
}

// ── 병렬 진행 표시 (§13-7) ──

function ParallelProgress({
  workflowState,
  className,
}: {
  workflowState: WorkflowState;
  className: string;
}) {
  const { current_step } = workflowState;

  // 각 병렬 노드의 상태 추정
  function getNodeStatus(nodeKey: string): "completed" | "active" | "pending" {
    // current_step이 이 노드이면 active
    if (current_step === nodeKey || current_step.includes(nodeKey)) {
      return "active";
    }
    // plan_merge에 도달했으면 모두 완료
    if (current_step === "plan_merge" || current_step.includes("review_plan")) {
      return "completed";
    }
    // 단순 휴리스틱: 노드 순서로 추정
    const idx = PARALLEL_NODES.findIndex((n) => n.key === nodeKey);
    const currentIdx = PARALLEL_NODES.findIndex(
      (n) => current_step === n.key || current_step.includes(n.key)
    );
    if (currentIdx >= 0 && idx < currentIdx) return "completed";
    return "pending";
  }

  const completedCount = PARALLEL_NODES.filter(
    (n) => getNodeStatus(n.key) === "completed"
  ).length;

  return (
    <div
      className={`bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5 ${className}`}
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-[#ededed]">
          STEP 3 병렬 작업 진행
        </h2>
        <span className="text-[10px] text-[#8c8c8c]">
          {completedCount}/{PARALLEL_NODES.length} 완료
        </span>
      </div>

      <div className="space-y-2.5">
        {PARALLEL_NODES.map((node) => {
          const status = getNodeStatus(node.key);
          return (
            <div key={node.key} className="flex items-center gap-3">
              {/* 프로그레스 바 */}
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span
                    className={`text-xs font-medium ${
                      status === "completed"
                        ? "text-[#3ecf8e]"
                        : status === "active"
                        ? "text-[#ededed]"
                        : "text-[#5c5c5c]"
                    }`}
                  >
                    {node.label}
                  </span>
                  <span className="text-[10px] text-[#8c8c8c]">
                    {status === "completed"
                      ? "완료"
                      : status === "active"
                      ? "진행 중"
                      : "대기"}
                  </span>
                </div>
                <div className="h-1.5 bg-[#262626] rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      status === "completed"
                        ? "bg-[#3ecf8e] w-full"
                        : status === "active"
                        ? "bg-[#3ecf8e]/60 w-2/3 animate-pulse"
                        : "w-0"
                    }`}
                  />
                </div>
              </div>

              {/* 상태 아이콘 */}
              <div className="w-5 h-5 shrink-0 flex items-center justify-center">
                {status === "completed" ? (
                  <svg
                    className="w-4 h-4 text-[#3ecf8e]"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={3}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                ) : status === "active" ? (
                  <div className="w-3 h-3 rounded-full border-2 border-[#3ecf8e] border-t-transparent animate-spin" />
                ) : (
                  <div className="w-2 h-2 rounded-full bg-[#363636]" />
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* AI 상태 표시 */}
      {PARALLEL_NODES.some((n) => getNodeStatus(n.key) === "active") && (
        <div className="mt-3 pt-3 border-t border-[#262626]">
          <div className="flex items-center gap-2 bg-[#111111] rounded-lg px-3 py-2">
            <div className="w-4 h-4 rounded-full border-2 border-[#3ecf8e] border-t-transparent animate-spin shrink-0" />
            <span className="text-[10px] text-[#8c8c8c]">
              Claude AI가 병렬로 계획을 수립하고 있습니다
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
