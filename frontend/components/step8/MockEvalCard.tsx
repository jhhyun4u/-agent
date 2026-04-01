/**
 * MockEvalCard — STEP 8D Output Display
 *
 * Shows mock evaluation results: 5-dimension scoring (technical, team, cost,
 * schedule, risk) with win probability and risk assessment from the
 * mock_evaluation_analysis node.
 */

"use client";

import { useState } from "react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import type { MockEvalResult, ScoreComponent } from "@/lib/types/step8";

export interface MockEvalCardProps {
  data: MockEvalResult | null;
  isLoading?: boolean;
  error?: Error | null;
  onRevalidate?: () => void;
}

export function MockEvalCard({
  data,
  isLoading = false,
  error = null,
  onRevalidate,
}: MockEvalCardProps) {
  const [chartType, setChartType] = useState<"radar" | "bar">("radar");
  const [selectedDimension, setSelectedDimension] =
    useState<ScoreComponent | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-4 p-4 border rounded-lg bg-gradient-to-br from-purple-50 to-transparent">
        <div className="h-6 w-48 bg-purple-200 rounded animate-pulse" />
        <div className="h-64 bg-purple-100 rounded animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 border border-red-200 rounded-lg bg-red-50">
        <p className="text-sm text-red-700">
          Failed to load evaluation results
        </p>
        <p className="text-xs text-red-600 mt-1">{error.message}</p>
        {onRevalidate && (
          <button
            onClick={onRevalidate}
            className="mt-2 px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
        <p className="text-sm text-gray-600">No evaluation results available</p>
      </div>
    );
  }

  const getRiskColor = (risk: "high" | "medium" | "low"): string => {
    switch (risk) {
      case "high":
        return "bg-red-100 text-red-800 border-red-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "low":
        return "bg-green-100 text-green-800 border-green-200";
    }
  };

  const chartData = data.dimensions.map((d) => ({
    name: d.dimension.charAt(0).toUpperCase() + d.dimension.slice(1),
    score: d.score,
  }));

  const winProbabilityPercent = Math.round(data.win_probability * 100);

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-white">
      {/* Header & Risk */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Mock Evaluation
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            5-Dimension Scoring Analysis
          </p>
        </div>
        {onRevalidate && (
          <button
            onClick={onRevalidate}
            className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
            title="Re-run evaluation"
          >
            Refresh
          </button>
        )}
      </div>

      {/* Win Probability & Risk Summary */}
      <div className="grid grid-cols-2 gap-3 py-3 border rounded-lg bg-gradient-to-br from-purple-50 to-blue-50">
        <div className="text-center">
          <p className="text-xs font-semibold text-gray-600 uppercase">
            Win Probability
          </p>
          <div className="mt-2 relative w-32 h-32 mx-auto">
            {/* Circular gauge */}
            <svg
              className="w-full h-full transform -rotate-90"
              viewBox="0 0 100 100"
            >
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="8"
              />
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke={
                  winProbabilityPercent >= 70
                    ? "#16a34a"
                    : winProbabilityPercent >= 50
                      ? "#f59e0b"
                      : "#dc2626"
                }
                strokeWidth="8"
                strokeDasharray={`${(winProbabilityPercent / 100) * 251.2} 251.2`}
                strokeLinecap="round"
              />
              <text
                x="50"
                y="50"
                textAnchor="middle"
                dominantBaseline="central"
                className="text-lg font-bold fill-gray-900"
              >
                {winProbabilityPercent}%
              </text>
            </svg>
          </div>
        </div>

        <div className="flex flex-col justify-center space-y-3 px-4">
          <div>
            <p className="text-xs font-semibold text-gray-600 uppercase">
              Overall Score
            </p>
            <p className="text-2xl font-bold text-purple-600 mt-1">
              {data.total_score}
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-600 uppercase">
              Risk Level
            </p>
            <span
              className={`inline-block px-3 py-1 text-xs font-semibold rounded border mt-1 ${getRiskColor(
                data.pass_fail_risk,
              )}`}
            >
              {data.pass_fail_risk.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      {/* Chart Toggle */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setChartType("radar")}
          className={`px-3 py-2 text-sm font-medium border-b-2 transition ${
            chartType === "radar"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-600 hover:text-gray-900"
          }`}
        >
          Radar
        </button>
        <button
          onClick={() => setChartType("bar")}
          className={`px-3 py-2 text-sm font-medium border-b-2 transition ${
            chartType === "bar"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-600 hover:text-gray-900"
          }`}
        >
          Bar
        </button>
      </div>

      {/* Charts */}
      <div className="h-72 bg-gray-50 rounded-lg p-4">
        {chartType === "radar" ? (
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 30, bottom: 20 }}
            >
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="name" tick={{ fontSize: 12 }} />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fontSize: 11 }}
              />
              <Radar
                name="Score"
                dataKey="score"
                stroke="#7c3aed"
                fill="#7c3aed"
                fillOpacity={0.6}
              />
              <Legend wrapperStyle={{ paddingTop: "20px" }} />
            </RadarChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 10, right: 20, left: 0, bottom: 60 }}
            >
              <CartesianGrid stroke="#e5e7eb" />
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                height={80}
                tick={{ fontSize: 12 }}
              />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#f3f4f6",
                  border: "1px solid #e5e7eb",
                }}
              />
              <Bar dataKey="score" fill="#7c3aed" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Dimensions Detail */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-gray-700">
          Dimension Breakdown
        </h4>
        <div className="space-y-2 max-h-72 overflow-y-auto">
          {data.dimensions.map((dim: ScoreComponent, idx: number) => (
            <div
              key={idx}
              className="border rounded-lg p-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition"
              onClick={() =>
                setSelectedDimension(
                  selectedDimension?.dimension === dim.dimension ? null : dim,
                )
              }
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="font-medium text-sm text-gray-900">
                    {dim.dimension.charAt(0).toUpperCase() +
                      dim.dimension.slice(1)}
                  </p>
                  <p className="text-xs text-gray-600 mt-1 line-clamp-1">
                    {dim.rationale}
                  </p>
                </div>
                <div className="text-right ml-4">
                  <p className="text-lg font-bold text-purple-600">
                    {dim.score}
                  </p>
                  <div className="h-1 w-16 bg-gray-300 rounded mt-1 overflow-hidden">
                    <div
                      className="h-full bg-purple-600"
                      style={{ width: `${dim.score}%` }}
                    />
                  </div>
                </div>
              </div>

              {selectedDimension?.dimension === dim.dimension && (
                <div className="mt-3 pt-3 border-t space-y-2">
                  <div>
                    <p className="text-xs font-semibold text-green-600">
                      Strengths
                    </p>
                    <ul className="text-sm text-gray-700 mt-1 space-y-1">
                      {dim.strengths.map((s, i) => (
                        <li key={i} className="flex items-start">
                          <span className="text-green-600 mr-2">✓</span>
                          <span>{s}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-red-600">
                      Weaknesses
                    </p>
                    <ul className="text-sm text-gray-700 mt-1 space-y-1">
                      {dim.weaknesses.map((w, i) => (
                        <li key={i} className="flex items-start">
                          <span className="text-red-600 mr-2">✗</span>
                          <span>{w}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Key Differentiators & Risks */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t">
        <div>
          <h4 className="text-xs font-semibold text-green-600 uppercase">
            Differentiators
          </h4>
          <ul className="text-sm text-gray-700 mt-2 space-y-1">
            {data.key_differentiators.slice(0, 2).map((d, idx) => (
              <li key={idx} className="flex items-start">
                <span className="text-green-600 mr-2">•</span>
                <span>{d}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="text-xs font-semibold text-red-600 uppercase">
            Risks
          </h4>
          <ul className="text-sm text-gray-700 mt-2 space-y-1">
            {data.competitive_risks.slice(0, 2).map((r, idx) => (
              <li key={idx} className="flex items-start">
                <span className="text-red-600 mr-2">•</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Metadata */}
      <div className="pt-2 border-t text-xs text-gray-500">
        Created: {new Date(data.created_at).toLocaleString()}
      </div>
    </div>
  );
}
