"use client";

/**
 * AppSidebar — 앱 전체 공유 사이드바
 * 제안서 / 자료 관리 / 아카이브 / 팀 관리 네비게이션
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import NotificationBell from "@/components/NotificationBell";

const NAV = [
  { href: "/dashboard", label: "대시보드", icon: "◈" },
  { href: "/proposals", label: "제안서", icon: "☰" },
  { href: "/bids", label: "공고 추천", icon: "⊙" },
  { href: "/analytics", label: "분석", icon: "◇" },
  { href: "/kb/search", label: "KB 검색", icon: "⌕" },
  { href: "/kb/content", label: "콘텐츠", icon: "▦" },
  { href: "/kb/clients", label: "발주기관", icon: "▣" },
  { href: "/kb/competitors", label: "경쟁사", icon: "▩" },
  { href: "/kb/lessons", label: "교훈", icon: "▧" },
  { href: "/kb/labor-rates", label: "원가기준", icon: "▤" },
  { href: "/kb/market-prices", label: "낙찰가", icon: "▥" },
  { href: "/resources", label: "자료 관리", icon: "□" },
  { href: "/archive", label: "아카이브", icon: "≡" },
  { href: "/admin", label: "팀 관리", icon: "◎" },
];

export default function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [email, setEmail] = useState("");

  useEffect(() => {
    createClient()
      .auth.getUser()
      .then(({ data }) => {
        setEmail(data.user?.email ?? "");
      });
  }, []);

  async function signOut() {
    await createClient().auth.signOut();
    router.push("/login");
  }

  return (
    <aside className="w-52 shrink-0 flex flex-col border-r border-[#262626] bg-[#111111]">
      {/* 로고 */}
      <div className="px-4 py-4 border-b border-[#262626]">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-[#3ecf8e] flex items-center justify-center font-bold text-black text-[9px]">
            CW
          </div>
          <span className="text-sm font-semibold text-[#ededed]">
            용역제안 Coworker
          </span>
        </div>
      </div>

      {/* 네비게이션 */}
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {NAV.map(({ href, label, icon }) => {
          const active =
            href === "/proposals"
              ? pathname.startsWith("/proposals")
              : href === "/dashboard"
              ? pathname.startsWith("/dashboard")
              : href === "/bids"
              ? pathname.startsWith("/bids")
              : href === "/analytics"
              ? pathname.startsWith("/analytics")
              : href.startsWith("/kb/")
              ? pathname === href
              : pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors ${
                active
                  ? "bg-[#1c1c1c] text-[#ededed]"
                  : "text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed]"
              }`}
            >
              <span className="text-xs opacity-70">{icon}</span>
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      {/* 유저 + 알림 */}
      <div className="border-t border-[#262626] px-3 py-3 space-y-0.5">
        <div className="flex items-center justify-between px-3 py-1.5">
          <p className="text-xs text-[#5c5c5c] truncate flex-1">{email}</p>
          <NotificationBell />
        </div>
        <button
          onClick={signOut}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-sm text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed] transition-colors"
        >
          <span className="text-xs opacity-70">↪</span>
          <span>로그아웃</span>
        </button>
      </div>
    </aside>
  );
}
