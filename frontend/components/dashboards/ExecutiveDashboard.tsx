/**
 * ExecutiveDashboard — 경영진 대시보드 (Day 3 frontend, ~200줄)
 *
 * - 4개 전사 KPI
 * - 3개 차트: 분기별 수주 추이 + 부서별 성과 + 포지셔닝 정확도 추이
 * - 상단 요약: 이번 달 주요 숫자 + YoY 비교
 * - useQuery: GET /api/dashboard/metrics/executive
 */

"use client";

import { useMemo } from "react";
import {
  BarChart,
  Bar,
  DoughnutChart,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from "recharts";
import { useExecutiveDashboard } from "@/lib/hooks/useDashboard";
import { MetricCard, MetricCardGrid } from "./common/MetricCard";
import { ChartContainer } from "./common/ChartContainer";
import type { DashboardFilters, ExecutiveMetrics } from "@/lib/utils/dashboardTypes";
import type { MetricCard as MetricCardType } from "@/lib/utils/dashboardTypes";
import { CHART_COLORS, formatPercent, formatCurrency } from "@/lib/utils/chartUtils";

interface ExecutiveDashboardProps {
  filters?: DashboardFilters;
}

export function ExecutiveDashboard({ filters }: ExecutiveDashboardProps) {
  const { data, isLoading, isError, metrics, cacheHit } =
    useExecutiveDashboard(filters);

  // ── 전사 KPI 카드 ──

  const kpiCards: MetricCardType[] = useMemo(() => {
    if (!metrics) return [];

    return [
      {
        title: "전사 수주율",
        value: metrics.company_win_rate,
        format: "percent",
        status: metrics.company_win_rate >= 0.4 ? "success" : "warning",
      },
      {
        title: "월간 제안",
        value: metrics.monthly_proposals_count,
        unit: "건",
      },
      {
        title: "평균 수주금액",
        value: metrics.avg_win_amount,
        format: "currency",
      },
      {
        title: "포지셔닝 정확도",
        value: metrics.positioning_accuracy,
        format: "percent",
      },
    ];
  }, [metrics]);

  // ── 분기별 추이 데이터 ──

  const quarterlyData = useMemo(() => {
    if (!metrics?.quarterly_trend) return [];
    return metrics.quarterly_trend.map((q) => ({
      name: q.quarter,
      제안: q.proposals_count,
      수주: q.won_count,
    }));
  }, [metrics?.quarterly_trend]);

  // ── 부서별 성과 데이터 ──

  const departmentData = useMemo(() => {
    if (!metrics?.department_performance) return [];
    return metrics.department_performance.map((d) => ({
      name: d.department_name,
      수주율: parseFloat((d.win_rate * 100).toFixed(1)),
      제안건수: d.proposals_count,
    }));
  }, [metrics?.department_performance]);

  // ── 포지셔닝 정확도 추이 ──

  const accuracyTrendData = useMemo(() => {
    if (!metrics?.positioning_accuracy_trend) return [];
    return metrics.positioning_accuracy_trend.map((t) => ({
      name: t.month,
      정확도: parseFloat((t.accuracy * 100).toFixed(1)),
    }));
  }, [metrics?.positioning_accuracy_trend]);

  // ── 이번 달 요약 ──

  const monthSummary = useMemo(() => {
    if (!metrics?.monthly_summary) return null;
    const prevMonth =
      metrics.quarterly_trend && metrics.quarterly_trend.length > 0
        ? metrics.quarterly_trend[metrics.quarterly_trend.length - 1]
        : null;
    return {
      proposals: metrics.monthly_summary.proposals_count,
      won: metrics.monthly_summary.won_count,
      change: metrics.monthly_summary.month_over_month_change,
    };
  }, [metrics?.monthly_summary, metrics?.quarterly_trend]);

  // ── 렌더 ──

  return (
    <div className="space-y-6">
      {/* 전사 KPI */}
      <MetricCardGrid cards={kpiCards} columns={4} />

      {/* 이번 달 요약 */}
      {monthSummary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
            <p className="text-xs text-[#8c8c8c] mb-3 uppercase tracking-wide">
              월간 제안
            </p>
            <div className="flex items-end gap-3">
              <p className="text-3xl font-bold text-[#ededed]">
                {monthSummary.proposals}
              </p>
              <p className="text-xs text-[#8c8c8c] mb-1">건</p>
            </div>
          </div>

          <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
            <p className="text-xs text-[#8c8c8c] mb-3 uppercase tracking-wide">
              이번 달 수주
            </p>
            <div className="flex items-end gap-3">
              <p className="text-3xl font-bold text-[#3ecf8e]">
                {monthSummary.won}
              </p>
              <p className="text-xs text-[#8c8c8c] mb-1">건</p>
            </div>
          </div>

          <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-5">
            <p className="text-xs text-[#8c8c8c] mb-3 uppercase tracking-wide">
              전월 대비
            </p>
            <div className="flex items-end gap-3">
              <p
                className={`text-3xl font-bold ${
                  monthSummary.change >= 0
                    ? "text-[#3ecf8e]"
                    : "text-red-400"
                }`}
              >
                {monthSummary.change >= 0 ? "+" : ""}
                {monthSummary.change.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 차트 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 분기별 제안/수주 스택 바 */}
        <ChartContainer
          title="분기별 수주 추이"
          isLoading={isLoading}
          isEmpty={quarterlyData.length === 0}
        >
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={quarterlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
              <XAxis
                dataKey="name"
                tick={{ fill: "#8c8c8c", fontSize: 11 }}
              />
              <YAxis tick={{ fill: "#8c8c8c", fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: "#1c1c1c",
                  border: "1px solid #262626",
                  borderRadius: 8,
                }}
              />
              <Legend wrapperStyle={{ paddingTop: "12px" }} />
              <Bar dataKey="수주" fill={CHART_COLORS.success} />
              <Bar dataKey="제안" fill={CHART_COLORS.info} />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>

        {/* 부서별 성과 비교 (도넛) */}
        <ChartContainer
          title="부서별 성과 분포"
          isLoading={isLoading}
          isEmpty={departmentData.length === 0}
        >
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={departmentData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={70}
                dataKey="제안건수"
                paddingAngle={2}
              >
                {departmentData.map((_, idx) => (
                  <Cell
                    key={idx}
                    fill={
                      [
                        CHART_COLORS.success,
                        CHART_COLORS.warning,
                        CHART_COLORS.danger,
                        CHART_COLORS.info,
                        CHART_COLORS.secondary,
                      ][idx] || CHART_COLORS.muted
                    }
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "#1c1c1c",
                  border: "1px solid #262626",
                  borderRadius: 8,
                }}
              />
            </PieChart>
          </ResponsiveContainer>

          {/* 범례 */}
          <div className="mt-3 flex flex-wrap gap-3">
            {departmentData.slice(0, 3).map((d, idx) => (
              <div key={d.name} className="flex items-center gap-1.5">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{
                    background: [
                      CHART_COLORS.success,
                      CHART_COLORS.warning,
                      CHART_COLORS.danger,
                    ][idx],
                  }}
                />
                <span className="text-[10px] text-[#8c8c8c]">
                  {d.name} ({d.제안건수})
                </span>
              </div>
            ))}
          </div>
        </ChartContainer>

        {/* 포지셔닝 정확도 추이 */}
        <ChartContainer
          title="포지셔닝 정확도 추이"
          isLoading={isLoading}
          isEmpty={accuracyTrendData.length === 0}
          className="lg:col-span-2"
        >
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={accuracyTrendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
              <XAxis
                dataKey="name"
                tick={{ fill: "#8c8c8c", fontSize: 11 }}
              />
              <YAxis tick={{ fill: "#8c8c8c", fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: "#1c1c1c",
                  border: "1px solid #262626",
                  borderRadius: 8,
                }}
              />
              <Line
                type="monotone"
                dataKey="정확도"
                stroke={CHART_COLORS.success}
                strokeWidth={2}
                dot={{ fill: CHART_COLORS.success, r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>
    </div>
  );
}
