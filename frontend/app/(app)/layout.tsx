"use client";

/**
 * (app) 공유 레이아웃 — AppSidebar를 한 번만 렌더하여
 * 페이지 전환 시 사이드바가 유지되도록 함.
 */

import AppSidebar from "@/components/AppSidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-[#0f0f0f] overflow-hidden">
      <AppSidebar />
      <div className="flex-1 flex flex-col overflow-hidden">{children}</div>
    </div>
  );
}
