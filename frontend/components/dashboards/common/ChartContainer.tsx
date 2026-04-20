/**
 * ChartContainer — 차트 래퍼 컴포넌트 (Day 3 frontend, ~80줄)
 *
 * - 로딩 상태 처리
 * - 에러 상태 처리
 * - 빈 상태 처리
 * - 반응형
 */

import React from "react";

interface ChartContainerProps {
  title?: string;
  isLoading?: boolean;
  isError?: boolean;
  isEmpty?: boolean;
  errorMessage?: string;
  emptyMessage?: string;
  children: React.ReactNode;
  className?: string;
}

export function ChartContainer({
  title,
  isLoading = false,
  isError = false,
  isEmpty = false,
  errorMessage = "데이터를 불러오는데 실패했습니다.",
  emptyMessage = "데이터가 없습니다.",
  children,
  className = "",
}: ChartContainerProps) {
  return (
    <div
      className={`bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5 ${className}`}
    >
      {title && (
        <h3 className="text-sm font-semibold text-[#ededed] mb-4">{title}</h3>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#3ecf8e] animate-pulse" />
            <p className="text-xs text-[#8c8c8c]">로딩 중...</p>
          </div>
        </div>
      )}

      {isError && !isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <p className="text-xs text-red-400 mb-1">오류</p>
            <p className="text-[11px] text-[#8c8c8c]">{errorMessage}</p>
          </div>
        </div>
      )}

      {isEmpty && !isLoading && !isError && (
        <div className="flex items-center justify-center py-12">
          <p className="text-xs text-[#8c8c8c]">{emptyMessage}</p>
        </div>
      )}

      {!isLoading && !isError && !isEmpty && <>{children}</>}
    </div>
  );
}
