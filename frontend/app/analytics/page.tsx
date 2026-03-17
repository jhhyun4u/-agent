"use client";

/**
 * 분석 대시보드 페이지 (§13-12)
 *
 * /analytics
 * 4개 차트 패널: 실패 원인, 포지셔닝별 수주율, 월별 추이, 기관별 수주 현황
 * 기간 필터 지원
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  api,
  type AnalyticsParams,
  type FailureReasonsData,
  type PositioningWinRateData,
  type MonthlyTrendsData,
  type ClientWinRateData,
} from "@/lib/api";
import {
  FailureReasonsPie,
  PositioningBar,
  MonthlyTrendsLine,
  ClientWinRateBar,
} from "@/components/AnalyticsCharts";

// ── 기간 프리셋 ──

const PERIOD_OPTIONS = [
  { value: "1Q", label: "2026 1Q" },
  { value: "4Q", label: "2025 4Q" },
  { value: "3Q", label: "2025 3Q" },
  { value: "all", label: "전체" },
];

export default function AnalyticsPage() {
  const [period, setPeriod] = useState("1Q");
  const [loading, setLoading] = useState(true);

  const [failureData, setFailureData] = useState<FailureReasonsData | null>(null);
  const [positioningData, setPositioningData] = useState<PositioningWinRateData | null>(null);
  const [trendsData, setTrendsData] = useState<MonthlyTrendsData | null>(null);
  const [clientData, setClientData] = useState<ClientWinRateData | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    const params: AnalyticsParams = { period };

    const results = await Promise.allSettled([
      api.analytics.failureReasons(params),
      api.analytics.positioningWinRate(params),
      api.analytics.monthlyTrends(params),
      api.analytics.clientWinRate(params),
    ]);

    setFailureData(results[0].status === "fulfilled" ? results[0].value : null);
    setPositioningData(results[1].status === "fulfilled" ? results[1].value : null);
    setTrendsData(results[2].status === "fulfilled" ? results[2].value : null);
    setClientData(results[3].status === "fulfilled" ? results[3].value : null);
    setLoading(false);
  }, [period]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-[#ededed]">
      {/* 헤더 */}
      <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 sticky top-0 z-20">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors"
            >
              ← 대시보드
            </Link>
            <h1 className="text-sm font-semibold text-[#ededed]">
              제안 분석 대시보드
            </h1>
          </div>

          {/* 기간 필터 */}
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="bg-[#1c1c1c] border border-[#262626] rounded-lg px-3 py-1.5 text-xs text-[#ededed] focus:outline-none focus:ring-1 focus:ring-[#3ecf8e] transition-colors"
          >
            {PERIOD_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-6">
        {loading && (
          <div className="flex items-center justify-center py-20 text-[#8c8c8c] text-sm">
            <div className="w-5 h-5 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin mr-3" />
            데이터 로딩 중...
          </div>
        )}

        {!loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* 실패 원인 분석 */}
            <ChartPanel title="실패 원인 분석" icon="📉">
              <FailureReasonsPie data={failureData} />
            </ChartPanel>

            {/* 포지셔닝별 수주율 */}
            <ChartPanel title="포지셔닝별 수주율" icon="📊">
              <PositioningBar data={positioningData} />
            </ChartPanel>

            {/* 월별 수주율 추이 */}
            <ChartPanel title="월별 수주율 추이" icon="📈">
              <MonthlyTrendsLine data={trendsData} />
            </ChartPanel>

            {/* 기관별 수주 현황 */}
            <ChartPanel title="기관별 수주 현황" icon="📋">
              <ClientWinRateBar data={clientData} />
            </ChartPanel>
          </div>
        )}
      </main>
    </div>
  );
}

// ── 차트 패널 래퍼 ──

function ChartPanel({
  title,
  icon,
  children,
}: {
  title: string;
  icon: string;
  children: React.ReactNode;
}) {
  return (
    <section className="bg-[#1c1c1c] rounded-2xl border border-[#262626] p-5">
      <h2 className="text-sm font-semibold text-[#ededed] mb-4">
        {icon} {title}
      </h2>
      {children}
    </section>
  );
}
