/**
 * FilterBar — 필터 UI 컴포넌트 (Day 3 frontend, ~120줄)
 *
 * - 기간 선택 (YTD/MTD/Custom)
 * - 팀 선택
 * - 메트릭 필터
 * - 적용 버튼
 */

import { useState } from "react";
import type { DashboardFilters } from "@/lib/utils/dashboardTypes";

interface FilterBarProps {
  onFiltersChange: (filters: DashboardFilters) => void;
  canFilterByTeam?: boolean;
  canFilterByMetric?: boolean;
  teamOptions?: Array<{ id: string; name: string }>;
  metricOptions?: Array<{ id: string; name: string }>;
}

export function FilterBar({
  onFiltersChange,
  canFilterByTeam = false,
  canFilterByMetric = false,
  teamOptions = [],
  metricOptions = [],
}: FilterBarProps) {
  const [period, setPeriod] = useState<"ytd" | "mtd" | "custom">("ytd");
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const [selectedTeam, setSelectedTeam] = useState("");
  const [selectedMetric, setSelectedMetric] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);

  const handleApply = () => {
    const filters: DashboardFilters = {
      period,
      custom_start_date: period === "custom" ? customStart : undefined,
      custom_end_date: period === "custom" ? customEnd : undefined,
      team_id: selectedTeam || undefined,
      metric: selectedMetric || undefined,
    };

    onFiltersChange(filters);
    setIsExpanded(false);
  };

  const handleReset = () => {
    setPeriod("ytd");
    setCustomStart("");
    setCustomEnd("");
    setSelectedTeam("");
    setSelectedMetric("");
    onFiltersChange({ period: "ytd" });
  };

  return (
    <div className="bg-[#1c1c1c] border border-[#262626] rounded-2xl p-4">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-0">
        <h3 className="text-sm font-semibold text-[#ededed]">필터</h3>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-xs text-[#8c8c8c] hover:text-[#ededed] transition-colors"
        >
          {isExpanded ? "축소" : "펼치기"}
        </button>
      </div>

      {/* 필터 콘텐츠 */}
      {isExpanded && (
        <div className="mt-4 space-y-4 border-t border-[#262626] pt-4">
          {/* 기간 선택 */}
          <div>
            <label className="block text-xs text-[#8c8c8c] mb-2 font-medium">
              기간
            </label>
            <div className="flex gap-2">
              {(["ytd", "mtd", "custom"] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    period === p
                      ? "bg-[#3ecf8e] text-[#0f0f0f]"
                      : "bg-[#262626] text-[#8c8c8c] hover:text-[#ededed]"
                  }`}
                >
                  {p === "ytd"
                    ? "올해"
                    : p === "mtd"
                      ? "이번달"
                      : "커스텀"}
                </button>
              ))}
            </div>
          </div>

          {/* 커스텀 날짜 */}
          {period === "custom" && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-[#8c8c8c] mb-2 font-medium">
                  시작일
                </label>
                <input
                  type="date"
                  value={customStart}
                  onChange={(e) => setCustomStart(e.target.value)}
                  className="w-full bg-[#262626] border border-[#3c3c3c] rounded-lg px-3 py-2 text-xs text-[#ededed] focus:outline-none focus:ring-2 focus:ring-[#3ecf8e]/40"
                />
              </div>
              <div>
                <label className="block text-xs text-[#8c8c8c] mb-2 font-medium">
                  종료일
                </label>
                <input
                  type="date"
                  value={customEnd}
                  onChange={(e) => setCustomEnd(e.target.value)}
                  className="w-full bg-[#262626] border border-[#3c3c3c] rounded-lg px-3 py-2 text-xs text-[#ededed] focus:outline-none focus:ring-2 focus:ring-[#3ecf8e]/40"
                />
              </div>
            </div>
          )}

          {/* 팀 선택 */}
          {canFilterByTeam && teamOptions.length > 0 && (
            <div>
              <label className="block text-xs text-[#8c8c8c] mb-2 font-medium">
                팀
              </label>
              <select
                value={selectedTeam}
                onChange={(e) => setSelectedTeam(e.target.value)}
                className="w-full bg-[#262626] border border-[#3c3c3c] rounded-lg px-3 py-2 text-xs text-[#ededed] focus:outline-none focus:ring-2 focus:ring-[#3ecf8e]/40"
              >
                <option value="">모든 팀</option>
                {teamOptions.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* 메트릭 필터 */}
          {canFilterByMetric && metricOptions.length > 0 && (
            <div>
              <label className="block text-xs text-[#8c8c8c] mb-2 font-medium">
                메트릭
              </label>
              <select
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value)}
                className="w-full bg-[#262626] border border-[#3c3c3c] rounded-lg px-3 py-2 text-xs text-[#ededed] focus:outline-none focus:ring-2 focus:ring-[#3ecf8e]/40"
              >
                <option value="">모든 메트릭</option>
                {metricOptions.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* 버튼 */}
          <div className="flex gap-2 pt-2">
            <button
              onClick={handleApply}
              className="flex-1 px-4 py-2 bg-[#3ecf8e] hover:bg-[#3ecf8e]/90 text-[#0f0f0f] text-xs font-semibold rounded-lg transition-colors"
            >
              적용
            </button>
            <button
              onClick={handleReset}
              className="flex-1 px-4 py-2 bg-[#262626] hover:bg-[#333] text-[#8c8c8c] text-xs font-semibold rounded-lg transition-colors"
            >
              초기화
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
