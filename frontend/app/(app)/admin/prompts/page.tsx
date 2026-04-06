"use client";

/**
 * 프롬프트 학습 대시보드 (v2.0)
 *
 * /admin/prompts
 * - 전체 건강 지표 (수주율/품질/수정율 추이)
 * - 개선 필요 TOP N (자동 분석)
 * - 추이 차트
 * - 최근 학습 이력
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, type LearningDashboard } from "@/lib/api";
import TrendChart from "@/components/prompt/TrendChart";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";

const PRIORITY_STYLE: Record<
  string,
  { label: string; color: string; bg: string }
> = {
  high: {
    label: "HIGH",
    color: "#ff6b6b",
    bg: "bg-[#2a1a1a] border-[#4a2020]",
  },
  medium: {
    label: "MED",
    color: "#f5a623",
    bg: "bg-[#2a2a1a] border-[#4a4020]",
  },
  low: { label: "LOW", color: "#3ecf8e", bg: "bg-[#1a2a1a] border-[#204a20]" },
};

export default function PromptLearningDashboard() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<LearningDashboard | null>(null);
  const [trendMetric, setTrendMetric] = useState<
    "quality" | "edit_ratio" | "win_rate"
  >("edit_ratio");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.prompts.learningDashboard();
      setData(result);
    } catch {
      // 개발 모드: 빈 상태 표시
      setData(null);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-[#ededed]">
      <header className="bg-[#111111] border-b border-[#262626] px-6 py-3 sticky top-0 z-20">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/admin"
              className="text-[#8c8c8c] hover:text-[#ededed] text-sm transition-colors"
            >
              &larr; 관리자
            </Link>
            <h1 className="text-sm font-semibold">프롬프트 학습 현황</h1>
          </div>
          <div className="flex gap-2">
            <Link
              href="/admin/prompts/catalog"
              className="px-3 py-1.5 bg-[#262626] hover:bg-[#333] rounded-lg text-xs transition-colors"
            >
              카탈로그
            </Link>
            <Link
              href="/admin/prompts/experiments"
              className="px-3 py-1.5 bg-[#262626] hover:bg-[#333] rounded-lg text-xs transition-colors"
            >
              A/B 실험
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6 space-y-6">
        {loading && (
          <div className="flex items-center justify-center py-20 text-[#8c8c8c] text-sm">
            <div className="w-5 h-5 border-2 border-[#262626] border-t-[#3ecf8e] rounded-full animate-spin mr-3" />
            분석 중...
          </div>
        )}

        {!loading && !data && (
          <Card>
            <CardBody className="p-8 text-center">
              <div className="text-[#8c8c8c] text-sm mb-4">
                프롬프트 사용 데이터가 아직 축적되지 않았습니다.
              </div>
              <div className="text-xs text-[#666]">
                제안서를 2건 이상 작성하면 학습 분석이 시작됩니다.
              </div>
              <Link
                href="/admin/prompts/catalog"
                className="inline-block mt-4 px-4 py-2 bg-[#262626] hover:bg-[#333] rounded-lg text-xs transition-colors"
              >
                프롬프트 카탈로그 보기
              </Link>
            </CardBody>
          </Card>
        )}

        {!loading && data && (
          <>
            {/* 전체 건강 지표 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <HealthCard
                label="평균 수주율"
                value={`${data.overview.avg_win_rate || 0}%`}
                delta={data.overview.delta?.win_rate}
                good="high"
              />
              <HealthCard
                label="평균 품질"
                value={`${data.overview.avg_quality || 0}점`}
                delta={data.overview.delta?.quality}
                good="high"
              />
              <HealthCard
                label="평균 수정율"
                value={`${((data.overview.avg_edit_ratio || 0) * 100).toFixed(0)}%`}
                delta={
                  data.overview.delta?.edit_ratio
                    ? data.overview.delta.edit_ratio * 100
                    : undefined
                }
                good="low"
              />
              <HealthCard
                label="진행 중 실험"
                value={`${data.overview.running_experiments}건`}
              />
            </div>

            {/* 개선 필요 TOP N */}
            <Card>
              <CardHeader title="개선 필요 프롬프트" />
              <CardBody className="px-5 pb-5">
                {data.top_needs_improvement.length === 0 ? (
                  <div className="text-xs text-[#8c8c8c] py-4">
                    현재 개선이 필요한 프롬프트가 없습니다. 데이터가 더 축적되면
                    자동 분석됩니다.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {data.top_needs_improvement.map((item, i) => {
                      const ps =
                        PRIORITY_STYLE[item.priority] || PRIORITY_STYLE.low;
                      return (
                        <div
                          key={item.prompt_id}
                          className={`rounded-xl border p-4 ${ps.bg}`}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className="text-lg font-bold text-[#8c8c8c]">
                                {i + 1}.
                              </span>
                              <div>
                                <div className="text-sm font-semibold">
                                  {item.label}
                                </div>
                                <div className="text-xs text-[#8c8c8c] font-mono">
                                  {item.prompt_id}
                                </div>
                              </div>
                            </div>
                            <span
                              className="text-[10px] px-2 py-0.5 rounded-full font-bold"
                              style={{
                                color: ps.color,
                                backgroundColor: `${ps.color}15`,
                              }}
                            >
                              {ps.label}
                            </span>
                          </div>

                          <div className="flex flex-wrap gap-4 text-xs text-[#8c8c8c] mb-3">
                            <span>
                              수정율:{" "}
                              <span
                                style={{
                                  color:
                                    (item.metrics.edit_ratio || 0) > 0.5
                                      ? "#ff6b6b"
                                      : "#ededed",
                                }}
                              >
                                {((item.metrics.edit_ratio || 0) * 100).toFixed(
                                  0,
                                )}
                                %
                              </span>
                            </span>
                            <span>품질: {item.metrics.quality || "-"}점</span>
                            <span>수주율: {item.metrics.win_rate || "-"}%</span>
                          </div>

                          {item.top_pattern && (
                            <div className="text-xs text-[#f5a623] mb-2">
                              패턴: &quot;{item.top_pattern.pattern}&quot;{" "}
                              {item.top_pattern.count}건
                            </div>
                          )}
                          {item.feedback_theme && (
                            <div className="text-xs text-[#8c8c8c] mb-3">
                              피드백: &quot;{item.feedback_theme}&quot;
                            </div>
                          )}

                          <Link
                            href={`/admin/prompts/${encodeURIComponent(item.prompt_id)}/improve`}
                            className="inline-block px-4 py-1.5 bg-[#3ecf8e] text-black rounded-lg text-xs font-medium hover:bg-[#35b87d] transition-colors"
                          >
                            개선 시작하기
                          </Link>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardBody>
            </Card>

            {/* 추이 차트 */}
            <Card>
              <CardBody className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="card-title">추이 (최근 6개월)</h3>
                  <div className="flex gap-1 bg-[#111] rounded-lg p-0.5">
                    {(["edit_ratio", "quality", "win_rate"] as const).map(
                      (m) => (
                        <button
                          key={m}
                          onClick={() => setTrendMetric(m)}
                          className={`px-2 py-0.5 rounded text-[10px] transition-colors ${
                            trendMetric === m
                              ? "bg-[#262626] text-[#ededed]"
                              : "text-[#8c8c8c]"
                          }`}
                        >
                          {
                            {
                              edit_ratio: "수정율",
                              quality: "품질",
                              win_rate: "수주율",
                            }[m]
                          }
                        </button>
                      ),
                    )}
                  </div>
                </div>
                <TrendChart
                  data={(data.trend || []).map((t) => ({
                    period: t.period,
                    quality: t.avg_quality,
                    edit_ratio: t.avg_edit_ratio,
                    win_rate: t.avg_win_rate,
                  }))}
                  metric={trendMetric}
                />
                {(!data.trend || data.trend.length === 0) && (
                  <div className="text-xs text-[#8c8c8c] text-center py-4">
                    분석 데이터가 축적되면 추이 차트가 표시됩니다.
                  </div>
                )}
              </CardBody>
            </Card>

            {/* 최근 학습 이력 */}
            <Card>
              <CardHeader title="최근 학습 이력" />
              <CardBody className="px-5 pb-5">
                {!data.recent_learnings ||
                data.recent_learnings.length === 0 ? (
                  <div className="text-xs text-[#8c8c8c] py-2">
                    A/B 실험 승격·롤백 이력이 표시됩니다.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {data.recent_learnings.map((item, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-3 py-2 border-b border-[#1a1a1a] last:border-0 text-xs"
                      >
                        <span className="text-[#8c8c8c] min-w-[70px]">
                          {item.date}
                        </span>
                        <Link
                          href={`/admin/prompts/${encodeURIComponent(item.prompt_id)}/improve`}
                          className="text-[#60a5fa] hover:underline"
                        >
                          {item.prompt_id.split(".").pop()?.replace("_", " ")}
                        </Link>
                        <span
                          className={
                            item.event === "승격"
                              ? "text-[#3ecf8e]"
                              : item.event === "롤백"
                                ? "text-[#ff6b6b]"
                                : "text-[#f5a623]"
                          }
                        >
                          {item.event}
                        </span>
                        {item.experiment_name && (
                          <span className="text-[#8c8c8c]">
                            ({item.experiment_name})
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardBody>
            </Card>
          </>
        )}
      </main>
    </div>
  );
}

function HealthCard({
  label,
  value,
  delta,
  good,
}: {
  label: string;
  value: string;
  delta?: number;
  good?: "high" | "low";
}) {
  const isPositive =
    delta != null &&
    ((good === "low" && delta < 0) || (good !== "low" && delta > 0));
  const isNegative =
    delta != null &&
    ((good === "low" && delta > 0) || (good !== "low" && delta < 0));

  return (
    <Card>
      <CardBody className="p-4">
        <div className="text-[#8c8c8c] text-xs">{label}</div>
        <div className="text-2xl font-bold mt-1">{value}</div>
        {delta != null && delta !== 0 && (
          <div
            className={`text-xs mt-0.5 ${isPositive ? "text-[#3ecf8e]" : isNegative ? "text-[#ff6b6b]" : "text-[#8c8c8c]"}`}
          >
            {delta > 0 ? "+" : ""}
            {typeof delta === "number" ? delta.toFixed(1) : delta}
            {isPositive ? " ↑" : isNegative ? " ↓" : ""}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
