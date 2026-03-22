"use client";

/**
 * 권고 #1: 워크플로 재개 요약 배너
 *
 * 워크플로가 중단(interrupt/paused)된 상태에서 페이지 재진입 시
 * "마지막 리뷰 결과 + 남은 단계 + 예상 시간" 요약을 표시한다.
 */

import { useEffect, useState } from "react";
import { api, WORKFLOW_STEPS, type WorkflowState } from "@/lib/api";

// STEP별 평균 소요 시간 (분) — 경험 기반 추정치
const STEP_DURATION_MIN: Record<number, number> = {
  0: 2, // RFP 검색
  1: 3, // RFP 분석 + Go/No-Go
  2: 4, // 전략 수립
  3: 6, // 계획 (병렬)
  4: 12, // 제안서 작성 (순차 섹션)
  5: 5,  // PPT
};

interface Props {
  proposalId: string;
  workflowState: WorkflowState | null;
  onDismiss?: () => void;
}

export default function WorkflowResumeBanner({ proposalId, workflowState, onDismiss }: Props) {
  const [lastReview, setLastReview] = useState<{ step: string; result: string; feedback?: string } | null>(null);
  const [dismissed, setDismissed] = useState(false);

  // 워크플로 히스토리에서 마지막 리뷰 결과를 가져옴
  useEffect(() => {
    if (!workflowState?.has_pending_interrupt) return;
    api.workflow.getHistory(proposalId).then((history) => {
      const events = (history as { events?: Array<{ node: string; action?: string; feedback?: string }> })?.events;
      if (!events || events.length === 0) return;
      // 최근 리뷰 이벤트 찾기
      const lastReviewEvent = [...events].reverse().find(
        (e) => e.node?.startsWith("review_") && e.action
      );
      if (lastReviewEvent) {
        setLastReview({
          step: lastReviewEvent.node,
          result: lastReviewEvent.action ?? "unknown",
          feedback: lastReviewEvent.feedback,
        });
      }
    }).catch(() => {});
  }, [proposalId, workflowState?.has_pending_interrupt]);

  if (dismissed || !workflowState) return null;

  // 인터럽트 상태가 아니면 표시하지 않음
  if (!workflowState.has_pending_interrupt) return null;

  // 현재 대기 중인 리뷰 노드
  const pendingNode = workflowState.next_nodes.find((n) => n.startsWith("review_"));
  const REVIEW_LABELS: Record<string, string> = {
    review_search: "공고 검색 결과 검토",
    review_rfp: "RFP 분석 결과 검토",
    review_gng: "Go/No-Go 의사결정",
    review_strategy: "제안전략 검토",
    review_bid_plan: "입찰가격 계획 검토",
    review_plan: "제안계획서 검토",
    review_section: "섹션별 검토",
    review_proposal: "제안서 최종 검토",
    review_ppt: "PPT 검토",
  };

  // 현재 STEP 추정
  const currentStep = workflowState.current_step;
  const STEP_MAP: Record<string, number> = {
    review_search: 0, review_rfp: 1, review_gng: 1,
    review_strategy: 2, review_bid_plan: 2,
    review_plan: 3, review_section: 4, review_proposal: 4,
    review_ppt: 5,
  };
  const currentStepNum = pendingNode ? (STEP_MAP[pendingNode] ?? 0) : 0;

  // 남은 STEP 계산
  const totalSteps = WORKFLOW_STEPS.length;
  const remainingSteps = totalSteps - currentStepNum - 1;

  // 예상 남은 시간
  let remainingMin = 0;
  for (let s = currentStepNum; s < totalSteps; s++) {
    remainingMin += STEP_DURATION_MIN[s] ?? 5;
  }

  // 섹션 진행 상황 (STEP 4)
  const sectionInfo = workflowState.current_section_index != null && workflowState.total_sections != null
    ? `${workflowState.current_section_index + 1}/${workflowState.total_sections} 섹션`
    : null;

  function handleDismiss() {
    setDismissed(true);
    onDismiss?.();
  }

  return (
    <div className="bg-gradient-to-r from-blue-500/10 via-[#111111] to-purple-500/10 border-b border-blue-500/20 px-6 py-4 shrink-0">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-start justify-between gap-4">
          {/* 요약 정보 */}
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
                  {pendingNode ? REVIEW_LABELS[pendingNode] ?? pendingNode : currentStep}
                </p>
                {sectionInfo && (
                  <p className="text-[10px] text-blue-400 mt-0.5">{sectionInfo} 진행</p>
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
                      style={{ width: `${((currentStepNum + 1) / totalSteps) * 100}%` }}
                    />
                  </div>
                </div>
                <p className="text-[10px] text-[#8c8c8c] mt-0.5">
                  {remainingSteps}개 STEP 남음
                </p>
              </div>

              {/* 예상 시간 */}
              <div>
                <p className="text-[10px] text-[#8c8c8c] mb-1">예상 잔여 시간</p>
                <p className="text-xs font-medium text-[#ededed]">
                  약 {remainingMin}분
                </p>
                <p className="text-[10px] text-[#8c8c8c] mt-0.5">
                  AI 생성 + 리뷰 포함
                </p>
              </div>
            </div>

            {/* 마지막 리뷰 결과 (있으면) */}
            {lastReview && (
              <div className="mt-3 flex items-center gap-2 bg-[#111111] border border-[#262626] rounded-lg px-3 py-2">
                <span className="text-[10px] text-[#8c8c8c]">이전 리뷰:</span>
                <span className={`text-[10px] font-medium ${
                  lastReview.result === "approved" ? "text-[#3ecf8e]" :
                  lastReview.result === "rejected" ? "text-red-400" :
                  "text-amber-400"
                }`}>
                  {lastReview.result === "approved" ? "승인됨" :
                   lastReview.result === "rejected" ? "재작업 요청" :
                   lastReview.result}
                </span>
                {lastReview.feedback && (
                  <span className="text-[10px] text-[#8c8c8c] truncate max-w-[300px]">
                    — {lastReview.feedback}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* 닫기 버튼 */}
          <button
            onClick={handleDismiss}
            className="text-[#8c8c8c] hover:text-[#ededed] p-1 shrink-0 transition-colors"
            title="배너 닫기"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
