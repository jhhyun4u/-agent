"use client";

import { useState, useEffect } from "react";
import { ReviewProgressBanner } from "./ReviewProgressBanner";
import { HITLReviewStatusList } from "./HITLReviewStatusList";
import { HITLReviewModal } from "./HITLReviewModal";
import { FeedbackLoopWorkflow } from "./FeedbackLoopWorkflow";
import { GapAnalysisResultList } from "./GapAnalysisResultList";
import { api } from "@/lib/api";
import type { GapAnalysisResult, SectionDiagnostic } from "@/lib/api";

interface ReviewItemStatus {
  id: string;
  step_name: string;
  section_name: string;
  status: "pending" | "in_review" | "approved" | "rejected";
  created_at: string;
  updated_at?: string;
}

interface ReviewItem {
  id: string;
  step_name: string;
  section_name: string;
  artifact_content: string;
  artifact_type: "text" | "markdown";
  status: "pending" | "in_review" | "approved" | "rejected";
  feedback_history: Array<{
    id: string;
    feedback_text: string;
    submitted_by_name: string;
    submitted_at: string;
    decision?: "approved" | "rejected" | "pending";
  }>;
  diagnostics?: SectionDiagnostic | null;
}

interface ProposalDetailWithHITLReviewProps {
  proposalId: string;
  children: React.ReactNode;
  showReviewPanel?: boolean;
}

export function ProposalDetailWithHITLReview({
  proposalId,
  children,
  showReviewPanel = true,
}: ProposalDetailWithHITLReviewProps) {
  const [reviewItems, setReviewItems] = useState<ReviewItemStatus[]>([]);
  const [selectedReviewId, setSelectedReviewId] = useState<string | null>(null);
  const [selectedReviewDetail, setSelectedReviewDetail] = useState<ReviewItem | null>(null);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [isLoadingReviews, setIsLoadingReviews] = useState(true);
  const [gapAnalysis, setGapAnalysis] = useState<GapAnalysisResult | null>(null);
  const [diagnostics, setDiagnostics] = useState<SectionDiagnostic[]>([]);
  const [gapAnalysisLoading, setGapAnalysisLoading] = useState(false);
  const [reviewStats, setReviewStats] = useState({
    total: 0,
    pending: 0,
    in_review: 0,
    approved: 0,
    rejected: 0,
  });
  const [bannerCollapsed, setBannerCollapsed] = useState(false);

  // 검토 항목 조회
  useEffect(() => {
    const fetchReviewItems = async () => {
      setIsLoadingReviews(true);
      try {
        const response = await fetch(`/api/proposals/${proposalId}/review-items`);
        if (response.ok) {
          const data = await response.json();
          setReviewItems(data.items || []);
          setReviewStats(data.stats || {
            total: 0,
            pending: 0,
            in_review: 0,
            approved: 0,
            rejected: 0,
          });
        }
      } catch (err) {
        console.error("검토 항목 조회 실패:", err);
      } finally {
        setIsLoadingReviews(false);
      }
    };

    if (showReviewPanel) {
      fetchReviewItems();
    }
  }, [proposalId, showReviewPanel]);

  // 갭 분석 결과 및 진단 데이터 조회 (병렬)
  useEffect(() => {
    const fetchGapAnalysisAndDiagnostics = async () => {
      setGapAnalysisLoading(true);
      try {
        const [gapRes, diagRes] = await Promise.all([
          api.proposals.getGapAnalysis(proposalId),
          api.proposals.getDiagnostics(proposalId),
        ]);
        setGapAnalysis(gapRes.gap_analysis);
        setDiagnostics(diagRes.diagnostics || []);
      } catch (err) {
        // 갭 분석 또는 진단 데이터가 없을 수 있음 - 무시
        console.debug("갭 분석/진단 조회 실패:", err);
      } finally {
        setGapAnalysisLoading(false);
      }
    };

    if (showReviewPanel) {
      fetchGapAnalysisAndDiagnostics();
    }
  }, [proposalId, showReviewPanel]);

  // 검토 항목 상세 조회 (진단 데이터는 캐시에서 조회)
  const handleSelectReviewItem = async (reviewId: string) => {
    setSelectedReviewId(reviewId);
    try {
      const response = await fetch(
        `/api/proposals/${proposalId}/review-items/${reviewId}`
      );
      if (response.ok) {
        const data = await response.json();

        // 캐시된 진단 데이터에서 해당 섹션 찾기
        const sectionDiag = diagnostics.find(
          d => d.section_id === data.section_name || d.section_title === data.section_name
        );
        if (sectionDiag) {
          data.diagnostics = sectionDiag;
        }

        setSelectedReviewDetail(data);
        setReviewModalOpen(true);
      }
    } catch (err) {
      console.error("검토 항목 상세 조회 실패:", err);
    }
  };

  // 피드백 제출
  const handleSubmitFeedback = async (
    feedback: string,
    decision: "approved" | "rejected" | "pending"
  ) => {
    if (!selectedReviewId) return;

    try {
      const response = await fetch(
        `/api/proposals/${proposalId}/review-items/${selectedReviewId}/feedback`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            feedback_text: feedback,
            decision,
          }),
        }
      );

      if (response.ok) {
        // 검토 항목 상태 업데이트
        setReviewItems((items) =>
          items.map((item) =>
            item.id === selectedReviewId
              ? { ...item, status: decision === "rejected" ? "in_review" : decision }
              : item
          )
        );

        // 통계 업데이트
        setReviewStats((stats) => {
          const updated = { ...stats };
          const oldStatus = selectedReviewDetail?.status;

          if (oldStatus && oldStatus in stats) {
            updated[oldStatus as keyof typeof stats]--;
          }
          if (decision in stats) {
            updated[decision as keyof typeof stats]++;
          }

          return updated;
        });

        setReviewModalOpen(false);
      }
    } catch (err) {
      console.error("피드백 제출 실패:", err);
    }
  };

  if (!showReviewPanel) {
    return <>{children}</>;
  }

  return (
    <div className="flex flex-col h-screen bg-[#1c1c1c]">
      {/* 진행도 배너 */}
      <ReviewProgressBanner
        totalItems={reviewStats.total}
        pendingItems={reviewStats.pending}
        approvedItems={reviewStats.approved}
        rejectedItems={reviewStats.rejected}
        inReviewItems={reviewStats.in_review}
        isCollapsed={bannerCollapsed}
        onCollapse={setBannerCollapsed}
      />

      {/* 메인 콘텐츠 */}
      <div className="flex-1 overflow-hidden flex gap-4 p-4">
        {/* 왼쪽: 검토 항목 리스트 */}
        <div className="w-80 overflow-auto bg-[#0f0f0f] rounded-lg border border-[#262626] p-4">
          <HITLReviewStatusList
            items={reviewItems}
            selectedId={selectedReviewId || undefined}
            onSelectItem={handleSelectReviewItem}
            isLoading={isLoadingReviews}
          />
        </div>

        {/* 중앙: 메인 콘텐츠 */}
        <div className="flex-1 overflow-auto">
          <div className="space-y-6">
            {children}
            {gapAnalysis && !gapAnalysisLoading && (
              <div className="bg-[#0f0f0f] border border-[#262626] rounded-lg p-6">
                <h3 className="text-lg font-semibold text-[#ededed] mb-4">
                  갭 분석 결과
                </h3>
                <GapAnalysisResultList gapAnalysis={gapAnalysis} />
              </div>
            )}
          </div>
        </div>

        {/* 오른쪽: 피드백 루프 (선택된 항목이 있을 때만) */}
        {selectedReviewDetail && (
          <div className="w-96 overflow-auto">
            <FeedbackLoopWorkflow
              status={
                selectedReviewDetail.status === "rejected"
                  ? "rejected"
                  : selectedReviewDetail.status === "approved"
                    ? "completed"
                    : "pending"
              }
              rejectionReason={
                selectedReviewDetail.feedback_history[0]?.feedback_text
              }
              aiWorkProgress={50}
            />
          </div>
        )}
      </div>

      {/* HITL 검토 모달 */}
      <HITLReviewModal
        isOpen={reviewModalOpen}
        reviewItem={selectedReviewDetail}
        onClose={() => setReviewModalOpen(false)}
        onSubmitFeedback={handleSubmitFeedback}
      />
    </div>
  );
}
