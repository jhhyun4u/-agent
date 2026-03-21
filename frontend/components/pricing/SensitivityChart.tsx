"use client";

/**
 * 민감도 곡선 — 낙찰률 vs 수주확률/기대수익 (Recharts AreaChart)
 */

import type { SensitivityPoint } from "@/lib/api";

interface Props {
  points: SensitivityPoint[];
  optimalRatio: number;
}

export default function SensitivityChart({ points, optimalRatio }: Props) {
  if (!points.length) {
    return <div className="text-sm text-[#8c8c8c] p-4">민감도 데이터 없음</div>;
  }

  // SVG 기반 차트 (Recharts 의존 없이 자체 구현)
  const W = 480;
  const H = 200;
  const PAD = { top: 20, right: 20, bottom: 30, left: 45 };
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;

  const minR = Math.min(...points.map(p => p.ratio));
  const maxR = Math.max(...points.map(p => p.ratio));
  const maxProb = Math.max(...points.map(p => p.win_prob), 0.01);

  const scaleX = (r: number) => PAD.left + ((r - minR) / (maxR - minR || 1)) * plotW;
  const scaleY = (prob: number) => PAD.top + plotH - (prob / maxProb) * plotH;

  // 확률 라인
  const probLine = points.map(p => `${scaleX(p.ratio)},${scaleY(p.win_prob)}`).join(" ");
  // 면적 채움
  const areaPath = `M ${scaleX(points[0].ratio)},${PAD.top + plotH} ` +
    points.map(p => `L ${scaleX(p.ratio)},${scaleY(p.win_prob)}`).join(" ") +
    ` L ${scaleX(points[points.length - 1].ratio)},${PAD.top + plotH} Z`;

  // 최적점
  const optPt = points.reduce((best, p) =>
    Math.abs(p.ratio - optimalRatio) < Math.abs(best.ratio - optimalRatio) ? p : best
  , points[0]);

  return (
    <div className="rounded-lg border border-[#262626] bg-[#161616] p-4 space-y-2">
      <h3 className="text-sm font-medium text-[#ededed]">민감도 곡선</h3>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: 220 }}>
        {/* 그리드 */}
        {[0, 0.25, 0.5, 0.75, 1].map(t => {
          const y = PAD.top + plotH - t * plotH;
          return (
            <g key={t}>
              <line x1={PAD.left} y1={y} x2={W - PAD.right} y2={y} stroke="#333" strokeDasharray="2,3" />
              <text x={PAD.left - 5} y={y + 4} fill="#666" fontSize={10} textAnchor="end">
                {Math.round(t * maxProb * 100)}%
              </text>
            </g>
          );
        })}

        {/* X축 레이블 */}
        {points.filter((_, i) => i % 4 === 0).map(p => (
          <text key={p.ratio} x={scaleX(p.ratio)} y={H - 5} fill="#666" fontSize={10} textAnchor="middle">
            {p.ratio.toFixed(0)}%
          </text>
        ))}

        {/* 면적 */}
        <path d={areaPath} fill="rgba(59,130,246,0.15)" />

        {/* 라인 */}
        <polyline points={probLine} fill="none" stroke="#3b82f6" strokeWidth={2} />

        {/* 최적점 */}
        <circle cx={scaleX(optPt.ratio)} cy={scaleY(optPt.win_prob)} r={5} fill="#f59e0b" stroke="#fff" strokeWidth={1.5} />
        <text x={scaleX(optPt.ratio)} y={scaleY(optPt.win_prob) - 10} fill="#f59e0b" fontSize={10} textAnchor="middle">
          {optPt.ratio.toFixed(1)}%
        </text>
      </svg>
      <div className="flex items-center gap-4 text-xs text-[#8c8c8c]">
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-blue-500 inline-block rounded" /> 수주확률
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 bg-amber-500 rounded-full inline-block" /> 최적점 {optPt.ratio.toFixed(1)}%
        </span>
      </div>
    </div>
  );
}
