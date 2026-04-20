/**
 * MetricCard — KPI 카드 컴포넌트 (Day 3 frontend, ~150줄)
 *
 * - 번호 + 제목 + 증감 화살표
 * - 상태 색상 (success/warning/danger)
 * - 트렌드 표시
 */

import type { MetricCard as MetricCardType } from "@/lib/utils/dashboardTypes";
import { formatMetricValue } from "@/lib/utils/chartUtils";

interface MetricCardProps {
  card: MetricCardType;
  className?: string;
}

export function MetricCard({ card, className = "" }: MetricCardProps) {
  // ── 상태 색상 결정 ──

  const statusColorMap: Record<string, string> = {
    success: "text-[#3ecf8e]",
    warning: "text-amber-400",
    danger: "text-red-400",
    neutral: "text-[#8c8c8c]",
  };

  const statusBgMap: Record<string, string> = {
    success: "bg-[#3ecf8e]/10",
    warning: "bg-amber-500/10",
    danger: "bg-red-500/10",
    neutral: "bg-[#262626]",
  };

  const statusColor = statusColorMap[card.status ?? "neutral"];
  const statusBg = statusBgMap[card.status ?? "neutral"];

  // ── 트렌드 아이콘 ──

  const trendIcon = card.trend
    ? card.trend.direction === "up"
      ? "▲"
      : card.trend.direction === "down"
        ? "▼"
        : "-"
    : null;

  const trendColor =
    card.trend?.direction === "up"
      ? "text-[#3ecf8e]"
      : card.trend?.direction === "down"
        ? "text-red-400"
        : "text-[#8c8c8c]";

  // ── 포맷된 값 ──

  const formattedValue = formatMetricValue(
    typeof card.value === "string" ? parseFloat(card.value) : card.value,
    card.format,
  );

  return (
    <div
      className={`bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5 hover:border-[#3ecf8e]/30 transition-colors ${className}`}
    >
      {/* 제목 */}
      <p className="text-xs text-[#8c8c8c] mb-3 uppercase tracking-wide font-medium">
        {card.title}
      </p>

      {/* 메인 값 + 단위 */}
      <div className="flex items-baseline gap-2 mb-4">
        <p className={`text-4xl font-bold ${statusColor}`}>
          {formattedValue}
        </p>
        {card.unit && (
          <p className="text-sm text-[#8c8c8c] font-medium">{card.unit}</p>
        )}
      </div>

      {/* 트렌드 표시 */}
      {card.trend && (
        <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg ${statusBg}`}>
          <span className={`text-sm font-bold ${trendColor}`}>
            {trendIcon}
          </span>
          <span className={`text-xs font-medium ${trendColor}`}>
            {card.trend.direction === "up" ? "+" : ""}
            {formatMetricValue(card.trend.value, "number")}
          </span>
        </div>
      )}
    </div>
  );
}

// ── 여러 카드 그룹 ──

interface MetricCardGridProps {
  cards: MetricCardType[];
  columns?: 1 | 2 | 3 | 4 | 5 | 6;
}

export function MetricCardGrid({
  cards,
  columns = 3,
}: MetricCardGridProps) {
  const gridMap: Record<number, string> = {
    1: "grid-cols-1",
    2: "grid-cols-1 md:grid-cols-2",
    3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
    5: "grid-cols-1 md:grid-cols-2 lg:grid-cols-5",
    6: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6",
  };

  return (
    <div className={`grid gap-4 ${gridMap[columns]}`}>
      {cards.map((card, idx) => (
        <MetricCard key={idx} card={card} />
      ))}
    </div>
  );
}
