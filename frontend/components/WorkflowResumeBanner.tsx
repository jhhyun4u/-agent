"use client";

/**
 * 워크플로 재진입 요약 배너
 *
 * 프로젝트 상세 페이지 진입 시 현재 작업 시점을 파악하여 표시:
 * - 리뷰 대기(interrupt): 현재 대기 단계 + 남은 단계 + 예상 시간
 * - 중단(on_hold/abandoned): 마지막 진행 시점 + 재개/포기 선택
 * - 비정상 정지: 워크플로 상태 불일치 감지 + 복구 안내
 */

import { useEffect, useState } from "react";
import { api, WORKFLOW_STEPS, type WorkflowState } from "@/lib/api";

// STEP별 평균 소요 시간 (분) — 경험 기반 추정치
const STEP_DURATION_MIN: Record<number, number> = {
  0: 2,
  1: 3,
  2: 4,
  3: 6,
  4: 12,
  5: 5,
};

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

const STEP_MAP: Record<string, number> = {
  review_search: 0,
  review_rfp: 1,
  review_gng: 1,
  review_strategy: 2,
  review_bid_plan: 2,
  review_plan: 3,
  review_section: 4,
  review_gap_analysis: 4,
  review_proposal: 4,
  review_ppt: 5,
};

// 노드명으로 STEP 번호 추정
const NODE_STEP_MAP: Record<string, number> = {
  rfp_analyze: 1,
  research_gather: 1,
  go_no_go: 1,
  strategy_generate: 2,
  bid_plan: 2,
  plan_team: 3,
  plan_assign: 3,
  plan_schedule: 3,
  plan_story: 3,
  plan_price: 3,
  plan_merge: 3,
  proposal_start_gate: 4,
  proposal_write_next: 4,
  section_quality_check: 4,
  storyline_gap_analysis: 4,
  self_review: 4,
  presentation_strategy: 5,
  ppt_toc: 5,
  ppt_visual_brief: 5,
  ppt_storyboard: 5,
};

function estimateStepFromPhase(phase: string): number {
  if (!phase) return 0;
  for (const [key, step] of Object.entries(NODE_STEP_MAP)) {
    if (phase.includes(key)) return step;
  }
  return 0;
}

interface Props {
  proposalId: string;
  proposalStatus: string;
  currentPhase: string | null;
  workflowState: WorkflowState | null;
  onResumeWorkflow?: () => void;
  onDismiss?: () => void;
}

export default function WorkflowResumeBanner({
  proposalId,
  proposalStatus,
  currentPhase,
  workflowState,
  onResumeWorkflow,
  onDismiss,
}: Props) {
  const [lastReview, setLastReview] = useState<{
    step: string;
    result: string;
    feedback?: string;
  } | null>(null);
  const [dismissed, setDismissed] = useState(false);

  // 워크플로 히스토리에서 마지막 리뷰 결과를 가져옴
  useEffect(() => {
    if (!workflowState) return;
    api.workflow
      .getHistory(proposalId)
      .then((history) => {
        const events = (
          history as {
            events?: Array<{
              node: string;
              action?: string;
              feedback?: string;
            }>;
          }
        )?.events;
        if (!events || events.length === 0) return;
        const lastReviewEvent = [...events]
          .reverse()
          .find((e) => e.node?.startsWith("review_") && e.action);
        if (lastReviewEvent) {
          setLastReview({
            step: lastReviewEvent.node,
            result: lastReviewEvent.action ?? "unknown",
            feedback: lastReviewEvent.feedback,
          });
        }
      })
      .catch(() => {});
  }, [proposalId, workflowState]);

  if (dismissed) return null;

  // ── 표시 조건 판단 ──

  // 1) 리뷰 대기 (interrupt)
  const isReviewPending = workflowState?.has_pending_interrupt === true;

  // 2) 중단/포기
  const isOnHold = proposalStatus === "on_hold";
  // Note: In unified state system, "abandoned" is a win_result value for status="closed", not a status itself
  const isAbandoned = proposalStatus === "closed" && (workflowState as any)?.win_result === "abandoned";
  const isStopped = isOnHold || isAbandoned;

  // 3) 워크플로 미시작/완료는 표시 안 함
  // Terminal statuses in unified state system (status="closed", "archived", "expired" are terminal)
  const terminalStatuses = [
    "completed",
    "submitted",
    "presentation",
    "closed",
    "archived",
    "expired",
  ];
  if (terminalStatuses.includes(proposalStatus)) return null;
  if (proposalStatus === "initialized" && !workflowState?.current_step)
    return null;

  // 어떤 표시 조건도 해당 없으면 숨김
  if (!isReviewPending && !isStopped) return null;

  // ── 공통 데이터 계산 ──
  const pendingNode = isReviewPending
    ? workflowState?.next_nodes.find((n) => REVIEW_LABELS[n])
    : null;

  const currentStepNum = pendingNode
    ? (STEP_MAP[pendingNode] ?? 0)
    : estimateStepFromPhase(currentPhase ?? workflowState?.current_step ?? "");

  const totalSteps = WORKFLOW_STEPS.length;
  const remainingSteps = totalSteps - currentStepNum - 1;

  let remainingMin = 0;
  for (let s = currentStepNum; s < totalSteps; s++) {
    remainingMin += STEP_DURATION_MIN[s] ?? 5;
  }

  const sectionInfo =
    workflowState?.current_section_index != null &&
    workflowState?.total_sections != null
      ? `${workflowState.current_section_index + 1}/${workflowState.total_sections} 섹션`
      : null;

  function handleDismiss() {
    setDismissed(true);
    onDismiss?.();
  }

  // ── 중단/포기 상태 배너 ──
  if (isStopped) {
    const STEP_LABELS = [
      "RFP 분석",
      "Go/No-Go",
      "전략 수립",
      "실행 계획",
      "제안서 작성",
      "PPT 생성",
    ];
    const stoppedAtLabel =
      STEP_LABELS[currentStepNum] ?? `STEP ${currentStepNum + 1}`;

    return (
      <div
        className={`border-b px-6 py-4 shrink-0 ${
          isAbandoned
            ? "bg-gradient-to-r from-red-500/10 via-[#111111] to-red-500/5 border-red-500/20"
            : "bg-gradient-to-r from-orange-500/10 via-[#111111] to-orange-500/5 border-orange-500/20"
        }`}
      >
        <div className="max-w-4xl mx-auto">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-3">
                <span
                  className={`w-2 h-2 rounded-full ${isAbandoned ? "bg-red-400" : "bg-orange-400"}`}
                />
                <h3
                  className={`text-xs font-semibold uppercase tracking-wider ${
                    isAbandoned ? "text-red-400" : "text-orange-400"
                  }`}
                >
                  {isAbandoned ? "제안 포기됨" : "작업 중단됨"}
                </h3>
              </div>

              <div className="grid grid-cols-3 gap-4">
                {/* 마지막 작업 시점 */}
                <div>
                  <p className="text-[10px] text-[#8c8c8c] mb-1">
                    마지막 작업 시점
                  </p>
                  <p className="text-xs font-medium text-[#ededed]">
                    STEP {currentStepNum + 1}: {stoppedAtLabel}
                  </p>
                  {sectionInfo && (
                    <p className="text-[10px] text-orange-400 mt-0.5">
                      {sectionInfo} 진행
                    </p>
                  )}
                </div>

                {/* 완료 현황 */}
                <div>
                  <p className="text-[10px] text-[#8c8c8c] mb-1">완료 현황</p>
                  <div className="flex items-center gap-2">
                    <p className="text-xs font-medium text-[#ededed]">
                      STEP {currentStepNum}/{totalSteps}
                    </p>
                    <div className="flex-1 h-1 bg-[#262626] rounded-full overflow-hidden max-w-[80px]">
                      <div
                        className={`h-full rounded-full ${isAbandoned ? "bg-red-400" : "bg-orange-400"}`}
                        style={{
                          width: `${(currentStepNum / totalSteps) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* 재개 시 예상 시간 */}
                <div>
                  <p className="text-[10px] text-[#8c8c8c] mb-1">
                    재개 시 예상 잔여 시간
                  </p>
                  <p className="text-xs font-medium text-[#ededed]">
                    약 {remainingMin}분
                  </p>
                </div>
              </div>

              {/* 이전 리뷰 결과 */}
              {lastReview && (
                <div className="mt-3 flex items-center gap-2 bg-[#111111] border border-[#262626] rounded-lg px-3 py-2">
                  <span className="text-[10px] text-[#8c8c8c]">
                    마지막 리뷰:
                  </span>
                  <span
                    className={`text-[10px] font-medium ${
                      lastReview.result === "approved"
                        ? "text-[#3ecf8e]"
                        : "text-red-400"
                    }`}
                  >
                    {lastReview.result === "approved"
                      ? "승인됨"
                      : "재작업 요청"}
                  </span>
                  {lastReview.feedback && (
                    <span className="text-[10px] text-[#8c8c8c] truncate max-w-[300px]">
                      — {lastReview.feedback}
                    </span>
                  )}
                </div>
              )}

              {/* 재개/포기 선택 */}
              {isOnHold && (
                <div className="mt-4 flex items-center gap-3">
                  <button
                    onClick={onResumeWorkflow}
                    className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#3ecf8e] text-[#0f0f0f] hover:bg-[#49e59e] transition-colors"
                  >
                    이 시점부터 작업 재개
                  </button>
                  <span className="text-[10px] text-[#8c8c8c]">
                    STEP {currentStepNum + 1}부터 이어서 진행합니다
                  </span>
                </div>
              )}
            </div>

            <button
              onClick={handleDismiss}
              className="text-[#8c8c8c] hover:text-[#ededed] p-1 shrink-0 transition-colors"
              title="배너 닫기"
            >
              <svg
                className="w-3.5 h-3.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── 리뷰 대기 배너 (기존) ──
  return (
    <div className="bg-gradient-to-r from-blue-500/10 via-[#111111] to-purple-500/10 border-b border-blue-500/20 px-6 py-4 shrink-0">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
              <h3 className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
                워크플로 진행 현황
              </h3>
            </div>

            {/* 3-컬럼 요약 */}
            <div className="grid grid-cols-3 gap-4">
              {/* 현재 대기 중 */}
              <div>
                <p className="text-[10px] text-[#8c8c8c] mb-1">현재 대기</p>
                <p className="text-xs font-medium text-[#ededed]">
                  {pendingNode
                    ? (REVIEW_LABELS[pendingNode] ?? pendingNode)
                    : workflowState?.current_step}
                </p>
                {sectionInfo && (
                  <p className="text-[10px] text-blue-400 mt-0.5">
                    {sectionInfo} 진행
                  </p>
                )}
              </div>

              {/* 남은 단계 */}
              <div>
                <p className="text-[10px] text-[#8c8c8c] mb-1">남은 단계</p>
                <div className="flex items-center gap-2">
                  <p className="text-xs font-medium text-[#ededed]">
                    STEP {currentStepNum + 1}/{totalSteps}
                  </p>
                  <div className="flex-1 h-1 bg-[#262626] rounded-full overflow-hidden max-w-[80px]">
                    <div
                      className="h-full bg-blue-400 rounded-full"
                      style={{
                        width: `${((currentStepNum + 1) / totalSteps) * 100}%`,
                      }}
                    />
                  </div>
                </div>
                <p className="text-[10px] text-[#8c8c8c] mt-0.5">
                  {remainingSteps}개 STEP 남음
                </p>
              </div>

              {/* 예상 시간 */}
              <div>
                <p className="text-[10px] text-[#8c8c8c] mb-1">
                  예상 잔여 시간
                </p>
                <p className="text-xs font-medium text-[#ededed]">
                  약 {remainingMin}분
                </p>
                <p className="text-[10px] text-[#8c8c8c] mt-0.5">
                  AI 생성 + 리뷰 포함
                </p>
              </div>
            </div>

            {/* 마지막 리뷰 결과 */}
            {lastReview && (
              <div className="mt-3 flex items-center gap-2 bg-[#111111] border border-[#262626] rounded-lg px-3 py-2">
                <span className="text-[10px] text-[#8c8c8c]">이전 리뷰:</span>
                <span
                  className={`text-[10px] font-medium ${
                    lastReview.result === "approved"
                      ? "text-[#3ecf8e]"
                      : lastReview.result === "rejected"
                        ? "text-red-400"
                        : "text-amber-400"
                  }`}
                >
                  {lastReview.result === "approved"
                    ? "승인됨"
                    : lastReview.result === "rejected"
                      ? "재작업 요청"
                      : lastReview.result}
                </span>
                {lastReview.feedback && (
                  <span className="text-[10px] text-[#8c8c8c] truncate max-w-[300px]">
                    — {lastReview.feedback}
                  </span>
                )}
              </div>
            )}
          </div>

          <button
            onClick={handleDismiss}
            className="text-[#8c8c8c] hover:text-[#ededed] p-1 shrink-0 transition-colors"
            title="배너 닫기"
          >
            <svg
              className="w-3.5 h-3.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
