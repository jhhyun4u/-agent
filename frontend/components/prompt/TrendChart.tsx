"use client";

/**
 * TrendChart — 월별 추이 라인 차트
 *
 * 수정율/품질/수주율 추이를 시각화. 버전 변경 마커 포함.
 */

interface TrendPoint {
  period: string;
  quality: number | null;
  edit_ratio: number | null;
  win_rate: number | null;
}

interface TrendChartProps {
  data: TrendPoint[];
  metric: "quality" | "edit_ratio" | "win_rate";
}

const METRIC_CONFIG = {
  quality: { label: "품질 점수", color: "#3ecf8e", suffix: "점", good: "high" },
  edit_ratio: {
    label: "수정율",
    color: "#ff6b6b",
    suffix: "%",
    good: "low",
    multiply: 100,
  },
  win_rate: { label: "수주율", color: "#60a5fa", suffix: "%", good: "high" },
} as const;

export default function TrendChart({ data, metric }: TrendChartProps) {
  const config = METRIC_CONFIG[metric];
  const multiply = "multiply" in config ? config.multiply : 1;

  const values = data
    .map((d) => {
      const raw = d[metric];
      return raw != null ? raw * multiply : null;
    })
    .filter((v): v is number => v != null);

  if (values.length < 2) {
    return (
      <div className="text-xs text-[#8c8c8c] p-4">
        추이 데이터 부족 (최소 2개월 필요)
      </div>
    );
  }

  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;

  return (
    <div className="space-y-2">
      <div className="text-xs font-semibold text-[#8c8c8c]">
        {config.label} 추이
      </div>
      <div className="space-y-1">
        {data.map((d, i) => {
          const raw = d[metric];
          const val = raw != null ? raw * multiply : null;
          if (val == null) return null;
          const pct = ((val - min) / range) * 100;
          const barWidth = Math.max(5, Math.min(100, pct));

          return (
            <div key={d.period} className="flex items-center gap-2 text-xs">
              <span className="w-16 text-[#8c8c8c] shrink-0">
                {d.period.slice(5)}
              </span>
              <div className="flex-1 h-4 bg-[#1a1a1a] rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${barWidth}%`,
                    backgroundColor: config.color,
                  }}
                />
              </div>
              <span className="w-12 text-right" style={{ color: config.color }}>
                {val.toFixed(metric === "edit_ratio" ? 0 : 1)}
                {config.suffix}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
