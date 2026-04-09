"use client";

import { cn } from "@/lib/utils";

type FeedbackLoopStatus = "pending" | "rejected" | "ai_working" | "completed" | "resubmitted";

interface FeedbackLoopWorkflowProps {
  status: FeedbackLoopStatus;
  rejectionReason?: string;
  aiWorkProgress?: number; // 0-100
  completedAt?: string;
  resubmittedAt?: string;
  isLoading?: boolean;
}

export function FeedbackLoopWorkflow({
  status,
  rejectionReason,
  aiWorkProgress = 0,
  completedAt,
  resubmittedAt,
  isLoading = false,
}: FeedbackLoopWorkflowProps) {
  const steps = [
    { id: "review", label: "검토", icon: "📋" },
    { id: "rejected", label: "거절", icon: "✗" },
    { id: "ai_working", label: "AI 수정", icon: "🤖" },
    { id: "completed", label: "수정완료", icon: "✓" },
    { id: "resubmitted", label: "재검토", icon: "🔄" },
  ];

  const getStepStatus = (stepId: string) => {
    const statusMap: Record<FeedbackLoopStatus, string[]> = {
      pending: ["review"],
      rejected: ["review", "rejected"],
      ai_working: ["review", "rejected", "ai_working"],
      completed: ["review", "rejected", "ai_working", "completed"],
      resubmitted: ["review", "rejected", "ai_working", "completed", "resubmitted"],
    };

    const completedSteps = statusMap[status] || [];
    return completedSteps.includes(stepId) ? "completed" : "pending";
  };

  const isStepActive = (stepId: string) => {
    const statusMap: Record<FeedbackLoopStatus, string> = {
      pending: "review",
      rejected: "rejected",
      ai_working: "ai_working",
      completed: "completed",
      resubmitted: "resubmitted",
    };

    return statusMap[status] === stepId;
  };

  return (
    <div className="bg-[#0f0f0f] border border-[#262626] rounded-lg p-6">
      {/* 워크플로 헤더 */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-[#ededed] mb-2">
          피드백 루프 진행 상황
        </h3>
        <p className="text-xs text-[#5c5c5c]">
          {status === "pending" && "검토 대기 중"}
          {status === "rejected" && "수정이 필요합니다"}
          {status === "ai_working" && "AI가 수정을 진행 중입니다"}
          {status === "completed" && "수정이 완료되었습니다"}
          {status === "resubmitted" && "재검토 대기 중입니다"}
        </p>
      </div>

      {/* 워크플로 스텝 */}
      <div className="flex items-center justify-between mb-6 gap-2">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center gap-2 flex-1">
            {/* 스텝 아이콘 */}
            <div
              className={cn(
                "flex items-center justify-center w-10 h-10 rounded-full text-lg font-medium flex-shrink-0 transition-all",
                isStepActive(step.id)
                  ? "bg-yellow-500/20 text-yellow-400 ring-2 ring-yellow-500/50"
                  : getStepStatus(step.id) === "completed"
                    ? "bg-[#3ecf8e]/20 text-[#3ecf8e]"
                    : "bg-[#262626] text-[#8c8c8c]"
              )}
            >
              {step.icon}
            </div>

            {/* 커넥터 라인 */}
            {index < steps.length - 1 && (
              <div
                className={cn(
                  "h-1 flex-1 rounded-full",
                  getStepStatus(steps[index + 1].id) === "completed"
                    ? "bg-[#3ecf8e]"
                    : "bg-[#262626]"
                )}
              />
            )}
          </div>
        ))}
      </div>

      {/* 스텝 라벨 */}
      <div className="flex justify-between gap-2 mb-6">
        {steps.map((step) => (
          <div
            key={step.id}
            className="flex-1 text-center"
          >
            <p className="text-[10px] font-medium text-[#ededed]">{step.label}</p>
          </div>
        ))}
      </div>

      {/* 상세 정보 */}
      <div className="space-y-3 pt-4 border-t border-[#262626]">
        {status === "rejected" && rejectionReason && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
            <p className="text-[10px] font-semibold text-red-400 mb-1">거절 사유</p>
            <p className="text-xs text-red-300 leading-relaxed">{rejectionReason}</p>
          </div>
        )}

        {status === "ai_working" && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <p className="text-[10px] font-semibold text-yellow-400">AI 수정 진행 중</p>
              <span className="text-xs text-yellow-300">{aiWorkProgress}%</span>
            </div>
            <div className="w-full h-1.5 bg-yellow-500/20 rounded-full overflow-hidden">
              <div
                className="h-full bg-yellow-400 transition-all duration-300"
                style={{ width: `${aiWorkProgress}%` }}
              />
            </div>
            <p className="text-[10px] text-yellow-300 mt-2">
              AI 엔진이 피드백을 기반으로 산출물을 수정하고 있습니다. 완료까지 약 2-5분이 소요됩니다.
            </p>
          </div>
        )}

        {status === "completed" && completedAt && (
          <div className="bg-[#3ecf8e]/10 border border-[#3ecf8e]/30 rounded-lg p-3">
            <p className="text-[10px] font-semibold text-[#3ecf8e] mb-1">수정 완료</p>
            <p className="text-xs text-[#5c5c5c]">
              {new Date(completedAt).toLocaleString("ko-KR")}
            </p>
          </div>
        )}

        {status === "resubmitted" && resubmittedAt && (
          <div className="bg-[#3ecf8e]/10 border border-[#3ecf8e]/30 rounded-lg p-3">
            <p className="text-[10px] font-semibold text-[#3ecf8e] mb-1">재검토 대기</p>
            <p className="text-xs text-[#5c5c5c]">
              재검토를 위해 재제출되었습니다. ({new Date(resubmittedAt).toLocaleString("ko-KR")})
            </p>
          </div>
        )}
      </div>

      {/* 다음 액션 */}
      <div className="mt-4 pt-4 border-t border-[#262626]">
        {status === "rejected" && (
          <button
            disabled={isLoading}
            className="w-full px-4 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 disabled:opacity-50 text-yellow-400 rounded-lg text-xs font-medium transition-colors"
          >
            AI 수정 시작
          </button>
        )}
        {status === "completed" && (
          <button
            disabled={isLoading}
            className="w-full px-4 py-2 bg-[#3ecf8e]/20 hover:bg-[#3ecf8e]/30 disabled:opacity-50 text-[#3ecf8e] rounded-lg text-xs font-medium transition-colors"
          >
            재검토 제출
          </button>
        )}
      </div>
    </div>
  );
}
