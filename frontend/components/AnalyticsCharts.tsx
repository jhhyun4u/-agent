"use client";

/**
 * AnalyticsCharts — Recharts 래퍼 컴포넌트 모음 (§13-12)
 *
 * - FailureReasonsPie: 실패 원인 파이차트
 * - PositioningBar: 포지셔닝별 수주율 수평 바
 * - MonthlyTrendsLine: 월별 수주율 추이 라인차트
 * - ClientWinRateBar: 기관별 수주 현황 바차트
 */

import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LineChart,
  Line,
  ResponsiveContainer,
} from "recharts";
import type {
  FailureReasonsData,
  PositioningWinRateData,
  MonthlyTrendsData,
  ClientWinRateData,
} from "@/lib/api";

// ── 공통 ──

const COLORS = ["#3ecf8e", "#f59e0b", "#ef4444", "#6366f1", "#8b5cf6", "#ec4899"];

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center h-48 text-xs text-[#5c5c5c]">
      {message}
    </div>
  );
}

// ── 실패 원인 파이차트 ──

export function FailureReasonsPie({ data }: { data: FailureReasonsData | null }) {
  if (!data || data.reasons.length === 0) {
    return <EmptyState message="실패 데이터 없음" />;
  }

  const chartData = data.reasons.map((r) => ({
    name: r.reason,
    value: r.count,
    pct: r.percentage,
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={45}
            outerRadius={75}
            dataKey="value"
            paddingAngle={2}
          >
            {chartData.map((_, idx) => (
              <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "#1c1c1c",
              border: "1px solid #262626",
              borderRadius: 8,
              fontSize: 11,
              color: "#ededed",
            }}
            formatter={(value, name) => [`${value}건`, String(name)]}
          />
        </PieChart>
      </ResponsiveContainer>
      {/* 범례 */}
      <div className="flex flex-wrap gap-x-4 gap-y-1.5 mt-2">
        {chartData.map((d, idx) => (
          <div key={d.name} className="flex items-center gap-1.5">
            <div
              className="w-2 h-2 rounded-full shrink-0"
              style={{ background: COLORS[idx % COLORS.length] }}
            />
            <span className="text-[10px] text-[#8c8c8c]">
              {d.name} {d.pct}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── 포지셔닝별 수주율 ──

const POS_ICONS: Record<string, string> = {
  defensive: "🛡️ 수성형",
  offensive: "⚔️ 공격형",
  adjacent: "🔄 인접형",
};

export function PositioningBar({ data }: { data: PositioningWinRateData | null }) {
  if (!data || data.positioning.length === 0) {
    return <EmptyState message="포지셔닝 데이터 없음" />;
  }

  return (
    <div className="space-y-3">
      {data.positioning.map((p) => (
        <div key={p.type}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-[#ededed]">
              {POS_ICONS[p.type] ?? p.type}
            </span>
            <span className="text-[10px] text-[#8c8c8c]">
              {p.rate.toFixed(1)}% ({p.won}/{p.total})
            </span>
          </div>
          <div className="h-2 bg-[#262626] rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-[#3ecf8e] transition-all"
              style={{ width: `${Math.min(p.rate, 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

// ── 월별 수주율 추이 ──

export function MonthlyTrendsLine({ data }: { data: MonthlyTrendsData | null }) {
  if (!data || data.months.length === 0) {
    return <EmptyState message="월별 데이터 없음" />;
  }

  const chartData = data.months.map((m) => ({
    month: m.month,
    rate: Math.round(m.rate * 10) / 10,
    total: m.total,
    won: m.won,
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
        <XAxis
          dataKey="month"
          tick={{ fill: "#8c8c8c", fontSize: 10 }}
          axisLine={{ stroke: "#262626" }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: "#8c8c8c", fontSize: 10 }}
          axisLine={{ stroke: "#262626" }}
          tickLine={false}
          domain={[0, 100]}
          tickFormatter={(v) => `${v}%`}
        />
        <Tooltip
          contentStyle={{
            background: "#1c1c1c",
            border: "1px solid #262626",
            borderRadius: 8,
            fontSize: 11,
            color: "#ededed",
          }}
          formatter={(value) => [`${value}%`, "수주율"]}
        />
        <Line
          type="monotone"
          dataKey="rate"
          stroke="#3ecf8e"
          strokeWidth={2}
          dot={{ r: 4, fill: "#3ecf8e" }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

// ── 기관별 수주 현황 ──

export function ClientWinRateBar({ data }: { data: ClientWinRateData | null }) {
  if (!data || data.clients.length === 0) {
    return <EmptyState message="기관별 데이터 없음" />;
  }

  const chartData = data.clients.slice(0, 8).map((c) => ({
    agency: c.agency.length > 8 ? c.agency.slice(0, 8) + "…" : c.agency,
    rate: Math.round(c.rate * 10) / 10,
    total: c.total,
    won: c.won,
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke="#262626" horizontal={false} />
        <XAxis
          type="number"
          domain={[0, 100]}
          tick={{ fill: "#8c8c8c", fontSize: 10 }}
          axisLine={{ stroke: "#262626" }}
          tickLine={false}
          tickFormatter={(v) => `${v}%`}
        />
        <YAxis
          type="category"
          dataKey="agency"
          tick={{ fill: "#8c8c8c", fontSize: 10 }}
          axisLine={{ stroke: "#262626" }}
          tickLine={false}
          width={72}
        />
        <Tooltip
          contentStyle={{
            background: "#1c1c1c",
            border: "1px solid #262626",
            borderRadius: 8,
            fontSize: 11,
            color: "#ededed",
          }}
          formatter={(value) => [`${value}%`, "수주율"]}
        />
        <Bar dataKey="rate" fill="#3ecf8e" radius={[0, 4, 4, 0]} barSize={14} />
      </BarChart>
    </ResponsiveContainer>
  );
}
