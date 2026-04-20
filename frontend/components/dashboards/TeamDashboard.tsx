/**
 * TeamDashboard — 팀 대시보드 (Day 3 frontend, ~250줄)
 *
 * - 10개 KPI 카드
 * - 3개 차트: 팀 비교 바 + 월별 추이 라인 + 팀원 기여도 히트맵
 * - 하단 테이블: 팀원 성과 랭킹
 * - useQuery: GET /api/dashboard/metrics/team
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
} from "recharts";
import { useTeamDashboard } from "@/lib/hooks/useDashboard";
import { MetricCard, MetricCardGrid } from "./common/MetricCard";
import { ChartContainer } from "./common/ChartContainer";
import { StatsTable } from "./common/StatsTable";
import type { DashboardFilters, TeamMetrics } from "@/lib/utils/dashboardTypes";
import type { MetricCard as MetricCardType } from "@/lib/utils/dashboardTypes";
import { CHART_COLORS, formatPercent, formatCurrency, formatDays } from "@/lib/utils/chartUtils";

interface TeamDashboardProps {
  filters?: DashboardFilters;
}

export function TeamDashboard({ filters }: TeamDashboardProps) {
  const { data, isLoading, isError, metrics, cacheHit } =
    useTeamDashboard(filters);

  // ── KPI 카드 생성 ──

  const kpiCards: MetricCardType[] = useMemo(() => {
    if (!metrics) return [];

    return [
      {
        title: "팀 수주율",
        value: metrics.win_rate,
        format: "percent",
        status: metrics.win_rate >= 0.4 ? "success" : "warning",
      },
      {
        title: "총 제안",
        value: metrics.proposals_count,
        unit: "건",
      },
      {
        title: "평균 낙찰금액",
        value: metrics.avg_price,
        format: "currency",
      },
      {
        title: "팀 활용도",
        value: metrics.team_utilization,
        format: "percent",
        status: metrics.team_utilization >= 0.7 ? "success" : "warning",
      },
      {
        title: "포지셔닝 성공율",
        value: metrics.positioning_success,
        format: "percent",
      },
      {
        title: "평균 소요일",
        value: metrics.avg_cycle_time_days,
        unit: "일",
      },
      {
        title: "수주금액",
        value: metrics.value_won,
        format: "currency",
      },
      {
        title: "1건당 비용",
        value: metrics.cost_per_win,
        format: "currency",
      },
      {
        title: "품질 점수",
        value: metrics.quality_score,
        format: "percent",
      },
      {
        title: "위험도",
        value: metrics.risk_score,
        format: "percent",
        status: metrics.risk_score <= 0.3 ? "success" : "danger",
      },
    ];
  }, [metrics]);

  // ── 팀별 비교 데이터 ──

  const teamComparisonData = useMemo(() => {
    if (!metrics?.team_comparison) return [];
    return metrics.team_comparison.map((t) => ({
      name: t.team_name,
      수주율: parseFloat((t.win_rate * 100).toFixed(1)),
    }));
  }, [metrics?.team_comparison]);

  // ── 월별 추이 데이터 ──

  const monthlyTrendData = useMemo(() => {
    if (!metrics?.monthly_trend) return [];
    return metrics.monthly_trend.map((m) => ({
      name: m.month,
      수주: m.won,
      낙찰실패: m.failed,
    }));
  }, [metrics?.monthly_trend]);

  // ── 팀원 성과 테이블 ──

  const memberTableData = useMemo(() => {
    if (!metrics?.team_members) return [];
    return metrics.team_members
      .sort((a, b) => b.win_rate - a.win_rate)
      .map((m) => ({
        name: m.name,
        win_rate: (m.win_rate * 100).toFixed(1),
        proposals: m.proposals_count,
        contribution: (m.contribution_percentage * 100).toFixed(1),
      }));
  }, [metrics?.team_members]);

  const tableColumns = [
    { key: "name", header: "이름", align: "left" as const },
    {
      key: "win_rate",
      header: "수주율",
      align: "right" as const,
      sortable: true,
      format: (v: unknown) => `${v}%`,
    },
    {
      key: "proposals",
      header: "제안",
      align: "right" as const,
      sortable: true,
      format: (v: unknown) => `${v}건`,
    },
    {
      key: "contribution",
      header: "기여도",
      align: "right" as const,
      sortable: true,
      format: (v: unknown) => `${v}%`,
    },
  ];

  // ── 렌더 ──

  return (
    <div className="space-y-6">
      {/* KPI 카드 */}
      <MetricCardGrid cards={kpiCards} columns={5} />

      {/* 차트 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 팀별 수주율 비교 */}
        <ChartContainer
          title="팀별 수주율 비교"
          isLoading={isLoading}
          isEmpty={teamComparisonData.length === 0}
        >
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={teamComparisonData}>
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

        {/* 월별 수주/낙찰 추이 */}
        <ChartContainer
          title="월별 수주/낙찰 추이"
          isLoading={isLoading}
          isEmpty={monthlyTrendData.length === 0}
        >
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={monthlyTrendData}>
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
              <Line
                type="monotone"
                dataKey="수주"
                stroke={CHART_COLORS.success}
                strokeWidth={2}
                dot={{ fill: CHART_COLORS.success, r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="낙찰실패"
                stroke={CHART_COLORS.danger}
                strokeWidth={2}
                dot={{ fill: CHART_COLORS.danger, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </div>

      {/* 팀원 성과 랭킹 */}
      <ChartContainer
        title="팀원 성과 랭킹"
        isLoading={isLoading}
        isEmpty={memberTableData.length === 0}
      >
        <StatsTable
          data={memberTableData}
          columns={tableColumns}
          pageSize={10}
        />
      </ChartContainer>
    </div>
  );
}
