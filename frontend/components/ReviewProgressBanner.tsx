"use client";

import { cn } from "@/lib/utils";

interface ReviewProgressBannerProps {
  totalItems: number;
  pendingItems: number;
  approvedItems: number;
  rejectedItems: number;
  inReviewItems: number;
  isCollapsed?: boolean;
  onCollapse?: (collapsed: boolean) => void;
}

export function ReviewProgressBanner({
  totalItems,
  pendingItems,
  approvedItems,
  rejectedItems,
  inReviewItems,
  isCollapsed = false,
  onCollapse,
}: ReviewProgressBannerProps) {
  const progressPercentage = totalItems > 0 ? (approvedItems / totalItems) * 100 : 0;
  const remainingItems = pendingItems + inReviewItems + rejectedItems;

  const getProgressColor = () => {
    if (progressPercentage === 100) return "bg-[#3ecf8e]";
    if (progressPercentage >= 75) return "bg-[#3ecf8e]";
    if (progressPercentage >= 50) return "bg-yellow-400";
    return "bg-yellow-400";
  };

  if (isCollapsed) {
    return (
      <div className="bg-[#0f0f0f] border-b border-[#262626] px-4 py-2 flex items-center justify-between">
        <button
          onClick={() => onCollapse?.(false)}
          className="flex items-center gap-2 text-xs hover:text-[#3ecf8e] transition-colors"
        >
          <span className="text-[#5c5c5c]">📊</span>
          <span className="text-[#ededed]">검토 진행률 보기</span>
        </button>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-[#0f0f0f] to-[#1c1c1c] border-b border-[#262626] px-6 py-4">
      {/* 상단: 제목과 축소 버튼 */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-[#ededed]">📊 검토 진행 현황</h3>
        <button
          onClick={() => onCollapse?.(true)}
          className="text-[#5c5c5c] hover:text-[#ededed] transition-colors text-sm"
        >
          −
        </button>
      </div>

      {/* 진행도 바 */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex-1">
            <div className="flex items-baseline gap-2">
              <span className="text-lg font-bold text-[#ededed]">
                {approvedItems}
              </span>
              <span className="text-sm text-[#5c5c5c]">
                / {totalItems} 완료
              </span>
            </div>
          </div>
          <span className="text-xs font-medium text-[#5c5c5c]">
            {Math.round(progressPercentage)}%
          </span>
        </div>
        <div className="w-full h-2 bg-[#262626] rounded-full overflow-hidden">
          <div
            className={cn("h-full transition-all duration-300", getProgressColor())}
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* 상태별 카운트 */}
      <div className="grid grid-cols-4 gap-2">
        {/* 대기 */}
        <div className="bg-[#262626] rounded-lg p-3 text-center">
          <p className="text-[10px] text-[#8c8c8c] mb-1">대기</p>
          <p className="text-lg font-bold text-[#8c8c8c]">{pendingItems}</p>
        </div>

        {/* 진행중 */}
        <div className="bg-yellow-500/20 rounded-lg p-3 text-center">
          <p className="text-[10px] text-yellow-400 mb-1">진행중</p>
          <p className="text-lg font-bold text-yellow-400">{inReviewItems}</p>
        </div>

        {/* 거절 */}
        {rejectedItems > 0 && (
          <div className="bg-red-500/20 rounded-lg p-3 text-center">
            <p className="text-[10px] text-red-400 mb-1">거절</p>
            <p className="text-lg font-bold text-red-400">{rejectedItems}</p>
          </div>
        )}

        {/* 완료 */}
        <div className="bg-[#3ecf8e]/20 rounded-lg p-3 text-center">
          <p className="text-[10px] text-[#3ecf8e] mb-1">완료</p>
          <p className="text-lg font-bold text-[#3ecf8e]">{approvedItems}</p>
        </div>
      </div>

      {/* 남은 항목 알림 */}
      {remainingItems > 0 && (
        <div className="mt-4 pt-4 border-t border-[#262626]">
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 flex items-start gap-2">
            <span className="text-yellow-400 flex-shrink-0">⚠️</span>
            <div className="flex-1">
              <p className="text-xs font-medium text-yellow-400">
                남은 검토: {remainingItems}개
              </p>
              <p className="text-[10px] text-yellow-300 mt-1">
                {inReviewItems > 0 && `${inReviewItems}개 진행 중 · `}
                {rejectedItems > 0 && `${rejectedItems}개 수정 필요`}
                {pendingItems > 0 && `${pendingItems}개 대기 중`}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
