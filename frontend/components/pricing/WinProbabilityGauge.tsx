"use client";

/**
 * 수주확률 게이지 (0-100%)
 * 반원형 게이지 + 신뢰도 배지
 */

interface Props {
  probability: number; // 0.0 ~ 1.0
  confidence: string; // high | medium | low
}

const CONF_COLORS: Record<string, string> = {
  high: "text-green-400 bg-green-400/10",
  medium: "text-yellow-400 bg-yellow-400/10",
  low: "text-red-400 bg-red-400/10",
};
const CONF_LABELS: Record<string, string> = {
  high: "높음",
  medium: "보통",
  low: "낮음",
};

export default function WinProbabilityGauge({
  probability,
  confidence,
}: Props) {
  const pct = Math.round(probability * 100);
  // 게이지 바 — 10칸
  const filled = Math.round(pct / 10);

  // 색상 결정
  const color =
    pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-yellow-500" : "bg-red-500";
  const textColor =
    pct >= 70
      ? "text-green-400"
      : pct >= 40
        ? "text-yellow-400"
        : "text-red-400";

  return (
    <div className="space-y-2">
      <div className="flex items-baseline gap-2">
        <span className={`text-3xl font-bold ${textColor}`}>{pct}%</span>
        <span className="text-sm text-[#8c8c8c]">수주확률</span>
      </div>
      <div className="flex gap-0.5">
        {Array.from({ length: 10 }).map((_, i) => (
          <div
            key={i}
            className={`h-2 flex-1 rounded-sm ${i < filled ? color : "bg-[#333]"}`}
          />
        ))}
      </div>
      <span
        className={`inline-block text-xs px-2 py-0.5 rounded ${CONF_COLORS[confidence] || CONF_COLORS.low}`}
      >
        신뢰도: {CONF_LABELS[confidence] || confidence}
      </span>
    </div>
  );
}
