import { GRID_LAYOUT_CLASS } from "@/lib/proposals-utils";

interface ProposalsTableSkeletonProps {
  rows?: number;
}

export function ProposalsTableSkeleton({ rows = 5 }: ProposalsTableSkeletonProps) {
  return (
    <div className="rounded-lg border border-[#262626] bg-[#111111] overflow-hidden">
      {[...Array(rows)].map((_, i) => (
        <div
          key={i}
          className={`grid ${GRID_LAYOUT_CLASS} gap-3 px-4 py-3.5 border-b border-[#1a1a1a] last:border-0 animate-pulse`}
        >
          {/* 프로젝트명 */}
          <div className="space-y-2">
            <div className="h-4 bg-[#1c1c1c] rounded w-3/4" />
            <div className="h-3 bg-[#1c1c1c] rounded w-1/2" />
          </div>

          {/* 포지셔닝 */}
          <div className="h-4 bg-[#1c1c1c] rounded w-12" />

          {/* 단계 */}
          <div className="space-y-1.5">
            <div className="h-3 bg-[#1c1c1c] rounded w-14" />
            <div className="flex gap-0.5">
              {[...Array(5)].map((_, j) => (
                <div key={j} className="w-3 h-1 bg-[#1c1c1c] rounded-full" />
              ))}
            </div>
          </div>

          {/* 예정가 */}
          <div className="h-4 bg-[#1c1c1c] rounded w-16" />

          {/* 입찰가 */}
          <div className="h-4 bg-[#1c1c1c] rounded w-16" />

          {/* 마감일 */}
          <div className="h-4 bg-[#1c1c1c] rounded w-16" />

          {/* 발주처 */}
          <div className="h-4 bg-[#1c1c1c] rounded w-14" />

          {/* 상태 */}
          <div className="h-4 bg-[#1c1c1c] rounded w-12" />

          {/* 메뉴 */}
          <div className="h-4 bg-[#1c1c1c] rounded w-6" />
        </div>
      ))}
    </div>
  );
}
