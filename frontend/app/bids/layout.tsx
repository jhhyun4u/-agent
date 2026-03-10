"use client";

import AppSidebar from "@/components/AppSidebar";

export default function BidsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-[#0f0f0f] overflow-hidden">
      <AppSidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        {children}
      </div>
    </div>
  );
}
