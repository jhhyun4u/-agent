"use client";

import { cn } from "@/lib/utils";

interface ReviewItemStatus {
  id: string;
  step_name: string;
  section_name: string;
  status: "pending" | "in_review" | "approved" | "rejected";
  created_at: string;
  updated_at?: string;
}

interface HITLReviewStatusListProps {
  items: ReviewItemStatus[];
  selectedId?: string;
  onSelectItem: (id: string) => void;
  isLoading?: boolean;
}

export function HITLReviewStatusList({
  items,
  selectedId,
  onSelectItem,
  isLoading = false,
}: HITLReviewStatusListProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "approved":
        return "✓";
      case "rejected":
        return "✗";
      case "in_review":
        return "⏳";
      default:
        return "•";
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

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "approved":
        return "완료";
      case "rejected":
        return "거절";
      case "in_review":
        return "진행중";
      default:
        return "대기";
    }
  };

  const approvedCount = items.filter((item) => item.status === "approved").length;
  const totalCount = items.length;
  const progressPercentage = totalCount > 0 ? (approvedCount / totalCount) * 100 : 0;

  return (
    <div className="flex flex-col gap-4">
      {/* 진행도 헤더 */}
      <div className="bg-[#0f0f0f] border border-[#262626] rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-[#5c5c5c]">
            검토 진행률
          </span>
          <span className="text-sm font-medium text-[#ededed]">
            {approvedCount} / {totalCount} 완료
          </span>
        </div>
        <div className="w-full h-2 bg-[#262626] rounded-full overflow-hidden">
          <div
            className="h-full bg-[#3ecf8e] transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* 검토 항목 리스트 */}
      <div className="space-y-2">
        {items.length === 0 ? (
          <div className="bg-[#0f0f0f] border border-[#262626] rounded-lg p-4 text-center">
            <p className="text-xs text-[#5c5c5c]">검토 항목이 없습니다</p>
          </div>
        ) : (
          items.map((item) => (
            <button
              key={item.id}
              onClick={() => onSelectItem(item.id)}
              disabled={isLoading}
              className={cn(
                "w-full text-left bg-[#0f0f0f] border rounded-lg p-4 transition-all disabled:opacity-50",
                selectedId === item.id
                  ? "border-[#3ecf8e] bg-[#3ecf8e]/5"
                  : "border-[#262626] hover:border-[#363636]"
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-[#5c5c5c]">{item.step_name}</span>
                    <span className="text-[10px] text-[#8c8c8c]">—</span>
                    <span className="text-xs font-medium text-[#ededed] truncate">
                      {item.section_name}
                    </span>
                  </div>
                  <p className="text-[10px] text-[#5c5c5c]">
                    생성: {new Date(item.created_at).toLocaleString("ko-KR", {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
                <div className="flex-shrink-0">
                  <span
                    className={cn(
                      "inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium",
                      getStatusColor(item.status)
                    )}
                  >
                    {getStatusIcon(item.status)}
                  </span>
                </div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
