"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

interface ReviewFeedback {
  id: string;
  feedback_text: string;
  submitted_by_name: string;
  submitted_at: string;
  decision?: "approved" | "rejected" | "pending";
}

interface ReviewItem {
  id: string;
  step_name: string;
  section_name: string;
  artifact_content: string;
  artifact_type: "text" | "markdown";
  status: "pending" | "in_review" | "approved" | "rejected";
  feedback_history: ReviewFeedback[];
}

interface HITLReviewModalProps {
  isOpen: boolean;
  reviewItem: ReviewItem | null;
  onClose: () => void;
  onSubmitFeedback: (feedback: string, decision: "approved" | "rejected" | "pending") => Promise<void>;
  isSubmitting?: boolean;
}

export function HITLReviewModal({
  isOpen,
  reviewItem,
  onClose,
  onSubmitFeedback,
  isSubmitting = false,
}: HITLReviewModalProps) {
  const [feedbackText, setFeedbackText] = useState("");
  const [decision, setDecision] = useState<"approved" | "rejected" | "pending">("pending");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      setFeedbackText("");
      setDecision("pending");
    }
  }, [isOpen]);

  if (!isOpen || !reviewItem) return null;

  const handleSubmit = async (selectedDecision: "approved" | "rejected" | "pending") => {
    if (!feedbackText.trim() && selectedDecision !== "approved") {
      alert("피드백을 입력해주세요");
      return;
    }

    setIsLoading(true);
    try {
      await onSubmitFeedback(feedbackText, selectedDecision);
      setFeedbackText("");
      setDecision("pending");
      onClose();
    } catch (err) {
      console.error("피드백 제출 실패:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "approved":
        return "bg-[#3ecf8e]/15 text-[#3ecf8e]";
      case "rejected":
        return "bg-red-500/15 text-red-400";
      case "in_review":
        return "bg-yellow-500/15 text-yellow-400";
      default:
        return "bg-[#262626] text-[#8c8c8c]";
    }
  };

  return (
    <>
      {/* 배경 오버레이 */}
      <div
        className="fixed inset-0 bg-black/60 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* 모달 창 - 풀스크린 오버레이 */}
      <div className="fixed inset-0 z-50 flex flex-col">
        {/* 헤더 */}
        <div className="bg-[#0f0f0f] border-b border-[#262626] px-6 py-4 flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(reviewItem.status)}`}>
                {reviewItem.status === "approved"
                  ? "✓ 승인됨"
                  : reviewItem.status === "rejected"
                    ? "✗ 거절됨"
                    : reviewItem.status === "in_review"
                      ? "⏳ 검토 중"
                      : "대기 중"}
              </span>
            </div>
            <h2 className="text-lg font-semibold text-[#ededed]">
              {reviewItem.step_name} - {reviewItem.section_name} 검토
            </h2>
            <p className="text-xs text-[#5c5c5c] mt-1">
              {new Date().toLocaleDateString("ko-KR")} 검토 필요
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-[#5c5c5c] hover:text-[#ededed] transition-colors p-1 text-2xl"
          >
            ✕
          </button>
        </div>

        {/* 콘텐츠 영역 - 2 패널 레이아웃 */}
        <div className="flex-1 overflow-hidden flex gap-4 p-6 bg-[#1c1c1c]">
          {/* 왼쪽: 산출물 뷰어 */}
          <div className="flex-1 overflow-auto bg-[#0f0f0f] rounded-lg border border-[#262626] p-6">
            <div className="text-[#ededed] text-sm leading-relaxed whitespace-pre-wrap break-words">
              {reviewItem.artifact_content}
            </div>
          </div>

          {/* 오른쪽: 피드백 입력 + 히스토리 */}
          <div className="w-96 flex flex-col gap-4 overflow-hidden">
            {/* 피드백 입력 */}
            <div className="flex-shrink-0 bg-[#0f0f0f] rounded-lg border border-[#262626] p-4">
              <label className="text-xs font-semibold text-[#5c5c5c] mb-2 block">
                피드백 의견
              </label>
              <textarea
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                placeholder="검토 의견을 입력하세요. 개선할 점, 우려사항 등을 자유롭게 기술해주세요."
                disabled={isLoading || isSubmitting}
                className="w-full h-24 bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-2 text-xs text-[#ededed] placeholder-[#5c5c5c] focus:outline-none focus:border-[#3ecf8e] disabled:opacity-50"
              />
            </div>

            {/* 피드백 히스토리 */}
            <div className="flex-1 overflow-auto bg-[#0f0f0f] rounded-lg border border-[#262626] p-4">
              <p className="text-xs font-semibold text-[#5c5c5c] mb-3">
                이전 피드백 ({reviewItem.feedback_history.length})
              </p>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {reviewItem.feedback_history.length === 0 ? (
                  <p className="text-xs text-[#5c5c5c] py-2">이전 피드백이 없습니다</p>
                ) : (
                  reviewItem.feedback_history.map((feedback) => (
                    <div
                      key={feedback.id}
                      className="bg-[#1c1c1c] border border-[#262626] rounded-lg p-3 space-y-2"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="text-xs font-medium text-[#ededed]">
                            {feedback.submitted_by_name}
                          </p>
                          <p className="text-[10px] text-[#5c5c5c]">
                            {new Date(feedback.submitted_at).toLocaleString("ko-KR")}
                          </p>
                        </div>
                        {feedback.decision && (
                          <span
                            className={cn(
                              "px-2 py-0.5 rounded text-[10px] font-medium whitespace-nowrap",
                              feedback.decision === "approved"
                                ? "bg-[#3ecf8e]/20 text-[#3ecf8e]"
                                : feedback.decision === "rejected"
                                  ? "bg-red-500/20 text-red-400"
                                  : "bg-[#262626] text-[#8c8c8c]"
                            )}
                          >
                            {feedback.decision === "approved"
                              ? "✓ 승인"
                              : feedback.decision === "rejected"
                                ? "✗ 거절"
                                : "대기"}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[#ededed] leading-relaxed">
                        {feedback.feedback_text}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* 결정 버튼 */}
            <div className="flex-shrink-0 flex gap-2">
              <button
                onClick={() => handleSubmit("rejected")}
                disabled={isLoading || isSubmitting}
                className="flex-1 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 disabled:opacity-50 text-red-400 rounded-lg text-sm font-medium transition-colors"
              >
                {isLoading || isSubmitting ? "처리 중..." : "거절 & 수정요청"}
              </button>
              <button
                onClick={() => handleSubmit("pending")}
                disabled={isLoading || isSubmitting}
                className="flex-1 px-4 py-2 bg-[#262626] hover:bg-[#363636] disabled:opacity-50 text-[#ededed] rounded-lg text-sm font-medium transition-colors"
              >
                {isLoading || isSubmitting ? "처리 중..." : "보류"}
              </button>
              <button
                onClick={() => handleSubmit("approved")}
                disabled={isLoading || isSubmitting || !feedbackText.trim()}
                className="flex-1 px-4 py-2 bg-[#3ecf8e]/20 hover:bg-[#3ecf8e]/30 disabled:opacity-50 text-[#3ecf8e] rounded-lg text-sm font-medium transition-colors"
              >
                {isLoading || isSubmitting ? "처리 중..." : "승인"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
