/**
 * DepartmentDashboard — 본부 대시보드 (Day 3 frontend, ~250줄)
 *
 * - 9개 KPI: 목표 vs 실적, 팀별 성과, 경쟁사 분석
 * - 4개 차트: 목표-실적 비교 + 팀별 성과 + 경쟁사 승률 + 분기별 추이
 * - 하단 테이블: 팀별 상세 성과
 * - useQuery: GET /api/dashboard/metrics/department
 */

"use client";

import { useMemo } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from "recharts";
import { useDepartmentDashboard } from "@/lib/hooks/useDashboard";
import { MetricCard, MetricCardGrid } from "./common/MetricCard";
import { ChartContainer } from "./common/ChartContainer";
import { StatsTable } from "./common/StatsTable";
import type { DashboardFilters, DepartmentMetrics } from "@/lib/utils/dashboardTypes";
import type { MetricCard as MetricCardType } from "@/lib/utils/dashboardTypes";
import { CHART_COLORS, formatPercent, formatCurrency } from "@/lib/utils/chartUtils";

interface DepartmentDashboardProps {
  filters?: DashboardFilters;
}

export function DepartmentDashboard({ filters }: DepartmentDashboardProps) {
  const { data, isLoading, isError, metrics, cacheHit } =
    useDepartmentDashboard(filters);

  // ── KPI 카드 생성 ──

  const kpiCards: MetricCardType[] = useMemo(() => {
    if (!metrics) return [];

    const achievementRate = metrics.target_vs_actual.percentage;

    return [
      {
        title: "목표 대비 달성률",
        value: achievementRate,
        format: "percent",
        status: achievementRate >= 1.0 ? "success" : achievementRate >= 0.8 ? "warning" : "danger",
      },
      {
        title: "목표금액",
        value: metrics.target_vs_actual.target,
        format: "currency",
      },
      {
        title: "실적금액",
        value: metrics.target_vs_actual.actual,
        format: "currency",
      },
      {
        title: "팀 수",
        value: metrics.team_performance.length,
      },
      {
        title: "평균 낙찰금액",
        value: metrics.avg_price,
        format: "currency",
      },
      {
        title: "포지셔닝 정확도",
        value: metrics.positioning_accuracy,
        format: "percent",
      },
      {
        title: "최고 수주율 팀",
        value: metrics.team_performance.length > 0
          ? Math.max(...metrics.team_performance.map(t => t.win_rate))
          : 0,
        format: "percent",
      },
      {
        title: "경쟁사 수",
        value: metrics.competitor_analysis.length,
      },
      {
        title: "시장 경쟁력",
        value:
          metrics.competitor_analysis.length > 0
            ? metrics.competitor_analysis.reduce((sum, c) => sum + c.win_rate, 0) /
              metrics.competitor_analysis.length
            : 0,
        format: "percent",
      },
    ];
  }, [metrics]);

  // ── 팀별 성과 데이터 ──

  const teamPerformanceData = useMemo(() => {
    if (!metrics?.team_performance) return [];
    return metrics.team_performance.map((t) => ({
      name: t.team_name,
      수주율: parseFloat((t.win_rate * 100).toFixed(1)),
      제안: t.proposals_count,
    }));
  }, [metrics?.team_performance]);

  // ── 경쟁사 비교 데이터 ──

  const competitorData = useMemo(() => {
    if (!metrics?.competitor_analysis) return [];
    return metrics.competitor_analysis.map((c) => ({
      name: c.competitor_name,
      수주율: parseFloat((c.win_rate * 100).toFixed(1)),
    }));
  }, [metrics?.competitor_analysis]);

  // ── 분기별 추이 데이터 ──

  const quarterlyData = useMemo(() => {
    if (!metrics?.quarterly_trend) return [];
    return metrics.quarterly_trend.map((q) => ({
      name: q.quarter,
      제안: q.proposals_count,
      수주: q.won_count,
    }));
  }, [metrics?.quarterly_trend]);

  // ── 팀별 상세 성과 테이블 ──

  const teamDetailData = useMemo(() => {
    if (!metrics?.team_details) return [];
    return metrics.team_details
      .sort((a, b) => b.win_rate - a.win_rate)
      .map((t) => ({
        name: t.team_name,
        win_rate: (t.win_rate * 100).toFixed(1),
        total_proposals: t.total_proposals,
        total_value: t.total_value,
        avg_cycle: t.avg_cycle_days,
      }));
  }, [metrics?.team_details]);

  const tableColumns = [
    { key: "name", header: "팀명", align: "left" as const },
    {
      key: "win_rate",
      header: "수주율",
      align: "right" as const,
      sortable: true,
      format: (v: unknown) => `${v}%`,
    },
    {
      key: "total_proposals",
      header: "총 제안",
      align: "right" as const,
      sortable: true,
      format: (v: unknown) => `${v}건`,
    },
    {
      key: "total_value",
      header: "수주금액",
      align: "right" as const,
      sortable: true,
      format: (v: unknown) => formatCurrency(typeof v === "number" ? v : 0),
    },
    {
      key: "avg_cycle",
      header: "평균 소요일",
      align: "right" as const,
      sortable: true,
      format: (v: unknown) => `${v}일`,
    },
  ];

  // ── 렌더 ──

  return (
    <div className="space-y-6">
      {/* KPI 카드 */}
      <MetricCardGrid cards={kpiCards} columns={3} />

      {/* 차트 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 팀별 성과 비교 */}
        <ChartContainer
          title="팀별 수주율 비교"
          isLoading={isLoading}
          isEmpty={teamPerformanceData.length === 0}
        >
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={teamPerformanceData}>
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
              <Bar dataKey="수주율" fill={CHART_COLORS.success} radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>

        {/* 경쟁사 승률 비교 */}
        <ChartContainer
          title="경쟁사 승률 비교"
          isLoading={isLoading}
          isEmpty={competitorData.length === 0}
        >
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={competitorData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
              <XAxis
                type="number"
                tick={{ fill: "#8c8c8c", fontSize: 11 }}
              />
              <YAxis
                dataKey="name"
                type="category"
                tick={{ fill: "#8c8c8c", fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{
                  background: "#1c1c1c",
                  border: "1px solid #262626",
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="수주율" fill={CHART_COLORS.warning} />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>

        {/* 분기별 추이 */}
        <ChartContainer
          title="분기별 제안 및 수주"
          isLoading={isLoading}
          isEmpty={quarterlyData.length === 0}
        >
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={quarterlyData}>
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
              <Bar dataKey="제안" fill={CHART_COLORS.info} />
              <Line
                type="monotone"
                dataKey="수주"
                stroke={CHART_COLORS.success}
                strokeWidth={2}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartContainer>

        {/* 목표 vs 실적 게이지 */}
        <ChartContainer title="목표 달성률" isLoading={isLoading}>
          <div className="flex flex-col items-center justify-center py-8">
            <div className="relative w-32 h-32 flex items-center justify-center">
              <svg
                viewBox="0 0 120 120"
                className="w-full h-full transform -rotate-90"
              >
                <circle
                  cx="60"
                  cy="60"
                  r="50"
                  fill="none"
                  stroke="#262626"
                  strokeWidth="8"
                />
                <circle
                  cx="60"
                  cy="60"
                  r="50"
                  fill="none"
                  stroke={CHART_COLORS.success}
                  strokeWidth="8"
                  strokeDasharray={`${(metrics?.target_vs_actual.percentage ?? 0) * 314}, 314`}
                />
              </svg>
              <div className="absolute text-center">
                <p className="text-2xl font-bold text-[#3ecf8e]">
                  {(metrics?.target_vs_actual.percentage ?? 0) * 100 > 100
                    ? "100+"
                    : ((metrics?.target_vs_actual.percentage ?? 0) * 100).toFixed(0)}
                  %
                </p>
              </div>
            </div>
          </div>
        </ChartContainer>
      </div>

      {/* 팀별 상세 성과 */}
      <ChartContainer
        title="팀별 상세 성과"
        isLoading={isLoading}
        isEmpty={teamDetailData.length === 0}
      >
        <StatsTable data={teamDetailData} columns={tableColumns} pageSize={10} />
      </ChartContainer>
    </div>
  );
}
