/**
 * IndividualDashboard — 개인 대시보드 (Day 3 frontend, ~200줄)
 *
 * - 6개 KPI 카드
 * - 2개 차트: 월별 라인차트 + 포지셔닝 파이차트
 * - 하단 테이블: 진행 중 제안서
 * - useQuery: GET /api/dashboard/metrics/individual
 */

"use client";

import { useMemo } from "react";
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useIndividualDashboard } from "@/lib/hooks/useDashboard";
import { MetricCard, MetricCardGrid } from "./common/MetricCard";
import { ChartContainer } from "./common/ChartContainer";
import { StatsTable } from "./common/StatsTable";
import type { DashboardFilters, IndividualMetrics } from "@/lib/utils/dashboardTypes";
import type { MetricCard as MetricCardType } from "@/lib/utils/dashboardTypes";
import { CHART_COLORS, formatPercent, formatCurrency, formatDays } from "@/lib/utils/chartUtils";

interface IndividualDashboardProps {
  filters?: DashboardFilters;
}

export function IndividualDashboard({ filters }: IndividualDashboardProps) {
  const { data, isLoading, isError, metrics, cacheHit } =
    useIndividualDashboard(filters);

  // ── KPI 카드 생성 ──

  const kpiCards: MetricCardType[] = useMemo(() => {
    if (!metrics) return [];

    return [
      {
        title: "수주율",
        value: metrics.win_rate,
        format: "percent",
        status: metrics.win_rate >= 0.4 ? "success" : "warning",
        trend: { value: 5, direction: "up" },
      },
      {
        title: "총 제안",
        value: metrics.proposals_count,
        unit: "건",
        status: metrics.proposals_count > 0 ? "success" : "neutral",
      },
      {
        title: "평균 소요일",
        value: metrics.avg_cycle_time_days,
        unit: "일",
        format: "number",
        status: metrics.avg_cycle_time_days < 30 ? "success" : "warning",
      },
      {
        title: "성공률",
        value: metrics.success_rate,
        format: "percent",
        status: metrics.success_rate >= 0.5 ? "success" : "warning",
      },
      {
        title: "수주금액",
        value: metrics.total_value_won,
        format: "currency",
        status: "success",
      },
      {
        title: "포지셔닝 정확도",
        value: metrics.positioning_accuracy,
        format: "percent",
        status: metrics.positioning_accuracy >= 0.7 ? "success" : "warning",
      },
    ];
  }, [metrics]);

  // ── 월별 데이터 ──

  const monthlyChartData = useMemo(() => {
    if (!metrics?.monthly_proposals) return [];
    return metrics.monthly_proposals.map((d) => ({
      name: d.month,
      제안: d.count,
    }));
  }, [metrics?.monthly_proposals]);

  // ── 포지셔닝 분포 ──

  const positioningData = useMemo(() => {
    if (!metrics?.positioning_distribution) return [];
    const labels: Record<string, string> = {
      defensive: "수성형",
      offensive: "공격형",
      adjacent: "인접형",
    };
    return metrics.positioning_distribution.map((d) => ({
      name: labels[d.type] || d.type,
      value: d.count,
    }));
  }, [metrics?.positioning_distribution]);

  // ── 진행 중 제안서 테이블 ──

  const tableData = useMemo(() => {
    if (!metrics?.in_progress_proposals) return [];
    return metrics.in_progress_proposals.map((p) => ({
      title: p.title,
      status: p.status,
      deadline: new Date(p.deadline).toLocaleDateString("ko-KR"),
      value: p.value,
    }));
  }, [metrics?.in_progress_proposals]);

  const tableColumns = [
    { key: "title", header: "제안서", align: "left" as const },
    { key: "status", header: "상태", align: "left" as const },
    {
      key: "deadline",
      header: "마감일",
      align: "left" as const,
      sortable: true,
    },
    {
      key: "value",
      header: "예상금액",
      align: "right" as const,
      sortable: true,
      format: (v: unknown) =>
        formatCurrency(typeof v === "number" ? v : 0),
    },
  ];

  // ── 렌더 ──

  return (
    <div className="space-y-6">
      {/* KPI 카드 */}
      <MetricCardGrid cards={kpiCards} columns={3} />

      {/* 차트 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 월별 제안 */}
        <ChartContainer
          title="월별 제안 건수"
          isLoading={isLoading}
          isEmpty={monthlyChartData.length === 0}
        >
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={monthlyChartData}>
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
                labelStyle={{ color: "#ededed" }}
              />
              <Line
                type="monotone"
                dataKey="제안"
                stroke={CHART_COLORS.success}
                strokeWidth={2}
                dot={{ fill: CHART_COLORS.success, r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>

        {/* 포지셔닝 분포 */}
        <ChartContainer
          title="포지셔닝 분포"
          isLoading={isLoading}
          isEmpty={positioningData.length === 0}
        >
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={positioningData}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={70}
                dataKey="value"
                paddingAngle={2}
              >
                {positioningData.map((_, idx) => (
                  <Cell
                    key={idx}
                    fill={
                      [CHART_COLORS.success, CHART_COLORS.warning, CHART_COLORS.danger][idx] ||
                      CHART_COLORS.muted
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
            {positioningData.map((d, idx) => (
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
                  {d.name} ({d.value})
                </span>
              </div>
            ))}
          </div>
        </ChartContainer>
      </div>

      {/* 진행 중 제안서 테이블 */}
      <ChartContainer
        title="진행 중인 제안서"
        isLoading={isLoading}
        isEmpty={tableData.length === 0}
      >
        <StatsTable data={tableData} columns={tableColumns} pageSize={5} />
      </ChartContainer>
    </div>
  );
}
