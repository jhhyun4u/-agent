"use client";

/**
 * EvaluationRadar — Recharts 4축 레이더 차트 (§13-11)
 *
 * 4축: compliance / strategy / quality / trustworthiness
 * 현재 점수 + 목표 점수(85점) 이중 레이어
 */

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { EvaluatorScore } from "@/lib/api";

const AXIS_LABELS: Record<string, string> = {
  compliance: "적합성",
  strategy: "전략성",
  quality: "품질",
  trustworthiness: "신뢰성",
};

const TARGET_SCORE = 85;

interface EvaluationRadarProps {
  scores: EvaluatorScore;
  className?: string;
}

export default function EvaluationRadar({
  scores,
  className = "",
}: EvaluationRadarProps) {
  const data = Object.entries(AXIS_LABELS).map(([key, label]) => ({
    axis: label,
    score: scores[key as keyof EvaluatorScore] ?? 0,
    target: TARGET_SCORE,
  }));

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={280}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
          <PolarGrid stroke="#262626" />
          <PolarAngleAxis
            dataKey="axis"
            tick={{ fill: "#8c8c8c", fontSize: 11 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: "#5c5c5c", fontSize: 9 }}
            tickCount={5}
          />
          <Radar
            name="목표 (85점)"
            dataKey="target"
            stroke="#3ecf8e"
            fill="#3ecf8e"
            fillOpacity={0.05}
            strokeDasharray="4 4"
            strokeWidth={1}
          />
          <Radar
            name="현재 점수"
            dataKey="score"
            stroke="#3ecf8e"
            fill="#3ecf8e"
            fillOpacity={0.2}
            strokeWidth={2}
          />
          <Legend wrapperStyle={{ fontSize: 10, color: "#8c8c8c" }} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
