/**
 * DashboardLayout — 대시보드 레이아웃 (Day 3 frontend, ~150줄)
 *
 * - 4가지 탭: Individual | Team | Department | Executive
 * - Header: 제목 + 필터/액션 버튼
 * - Body: 메트릭 카드 + 차트 + 테이블
 * - Sidebar: 필터 패널
 * - Footer: 마지막 업데이트 시간 + 새로고침
 */

import { useState } from "react";
import type { DashboardType, DashboardFilters } from "@/lib/utils/dashboardTypes";

interface DashboardLayoutProps {
  title: string;
  dashboardType: DashboardType;
  onDashboardChange: (type: DashboardType) => void;
  isLoading: boolean;
  isCached: boolean;
  lastUpdated: string;
  onRefresh: () => void;
  children: React.ReactNode;
}

export function DashboardLayout({
  title,
  dashboardType,
  onDashboardChange,
  isLoading,
  isCached,
  lastUpdated,
  onRefresh,
  children,
}: DashboardLayoutProps) {
  const [showFilters, setShowFilters] = useState(false);

  const dashboardTabs: Array<{
    id: DashboardType;
    label: string;
    requiresRole: string;
  }> = [
    { id: "individual", label: "개인", requiresRole: "member" },
    { id: "team", label: "팀", requiresRole: "lead" },
    { id: "department", label: "본부", requiresRole: "director" },
    { id: "executive", label: "경영진", requiresRole: "executive" },
  ];

  return (
    <div className="flex flex-col h-screen bg-[#0f0f0f]">
      {/* ── 헤더 ── */}
      <header className="bg-[#1c1c1c] border-b border-[#262626] px-6 py-4 shrink-0">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-bold text-[#ededed]">{title}</h1>

          <div className="flex items-center gap-3">
            {/* 새로고침 버튼 */}
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="p-2 rounded-lg text-[#8c8c8c] hover:text-[#ededed] hover:bg-[#262626] transition-colors disabled:opacity-50"
              title="새로고침"
            >
              <svg
                className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </button>

            {/* 필터 버튼 */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="p-2 rounded-lg text-[#8c8c8c] hover:text-[#ededed] hover:bg-[#262626] transition-colors"
              title="필터"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* 탭 ── */}
        <div className="flex items-center gap-1 bg-[#0f0f0f] rounded-lg p-1 border border-[#262626]">
          {dashboardTabs.map(({ id, label }) => (
            <button
              key={id}
              onClick={() => onDashboardChange(id)}
              className={`px-4 py-2 rounded-md text-xs font-medium transition-colors ${
                dashboardType === id
                  ? "bg-[#3ecf8e] text-[#0f0f0f]"
                  : "text-[#8c8c8c] hover:text-[#ededed]"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      {/* ── 메인 콘텐츠 ── */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-6 py-6">
          {/* 캐시 상태 배지 */}
          {isCached && !isLoading && (
            <div className="mb-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#262626]/50 border border-[#3ecf8e]/30">
              <span className="w-2 h-2 rounded-full bg-[#3ecf8e]" />
              <span className="text-[10px] text-[#8c8c8c]">캐시된 데이터</span>
            </div>
          )}

          {/* 콘텐츠 */}
          {children}
        </div>
      </main>

      {/* ── 푸터 ── */}
      <footer className="bg-[#1c1c1c] border-t border-[#262626] px-6 py-3 shrink-0">
        <div className="flex items-center justify-between text-[10px] text-[#8c8c8c]">
          <div className="flex items-center gap-3">
            <span>마지막 업데이트: {lastUpdated}</span>
            {isCached && <span className="text-[#3ecf8e]">● 캐시됨</span>}
          </div>

          <div className="flex items-center gap-2">
            <span>자동 새로고침 간격: 5분</span>
          </div>
        </div>
      </footer>

      {/* ── 필터 사이드바 (모바일) ── */}
      {showFilters && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={() => setShowFilters(false)}
          />
          <div className="fixed right-0 top-0 bottom-0 w-80 bg-[#1c1c1c] border-l border-[#262626] z-50 p-6 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-[#ededed]">필터</h2>
              <button
                onClick={() => setShowFilters(false)}
                className="text-[#8c8c8c] hover:text-[#ededed]"
              >
                ✕
              </button>
            </div>
            {/* 필터 콘텐츠는 자식 컴포넌트에서 제공 */}
          </div>
        </>
      )}
    </div>
  );
}
