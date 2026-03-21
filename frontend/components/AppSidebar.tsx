"use client";

/**
 * AppSidebar — 앱 전체 공유 사이드바
 * 대시보드 / 공고 / 제안 작업 / 지식 베이스 / 자료 / 아카이브 / Admin
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import NotificationBell from "@/components/NotificationBell";

/* ── SVG 아이콘 (접근성 + 시각적 명확성) ── */
function SvgIcon({ d, className = "" }: { d: string; className?: string }) {
  return (
    <svg className={`w-4 h-4 ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  );
}

const ICONS: Record<string, string> = {
  dashboard: "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10",
  bids: "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z",
  proposals: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8",
  pricing: "M12 1v22 M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6",
  kb: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253",
  search: "M21 21l-6-6m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0z",
  content: "M4 6h16M4 12h16M4 18h7",
  clients: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75",
  lessons: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 1 1 7.072 0l-.548.547A3.374 3.374 0 0 0 14 18.469V19a2 2 0 1 1-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  resources: "M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-6l-2-2H5a2 2 0 0 0-2 2z",
  archive: "M21 8v13H3V8 M1 3h22v5H1z M10 12h4",
  admin: "M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z",
};

interface NavItem {
  href: string;
  label: string;
  icon: string;
}

interface NavGroup {
  label: string;
  icon: string;
  basePath: string;
  children: NavItem[];
}

type NavEntry = NavItem | NavGroup;

function isGroup(e: NavEntry): e is NavGroup {
  return "children" in e;
}

const NAV: NavEntry[] = [
  { href: "/dashboard", label: "대시보드", icon: "dashboard" },
  { href: "/bids", label: "공고 모니터링", icon: "bids" },
  { href: "/proposals", label: "제안 프로젝트", icon: "proposals" },
  { href: "/pricing", label: "가격 시뮬레이터", icon: "pricing" },
  {
    label: "지식 베이스", icon: "kb", basePath: "/kb",
    children: [
      { href: "/kb/search", label: "검색", icon: "search" },
      { href: "/kb/content", label: "콘텐츠", icon: "content" },
      { href: "/kb/clients", label: "발주기관", icon: "clients" },
      { href: "/kb/lessons", label: "교훈", icon: "lessons" },
    ],
  },
  { href: "/resources", label: "자료 관리", icon: "resources" },
  { href: "/archive", label: "아카이브", icon: "archive" },
  { href: "/admin", label: "Admin", icon: "admin" },
];

export default function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [userRole, setUserRole] = useState("");
  const [kbOpen, setKbOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  // KB 하위 페이지에 있으면 자동 펼침
  useEffect(() => {
    if (pathname.startsWith("/kb")) setKbOpen(true);
  }, [pathname]);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      setEmail(data.user?.email ?? "");
    });
    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
    supabase.auth.getSession().then(({ data }) => {
      const token = data.session?.access_token;
      if (token) {
        fetch(`${apiBase}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
          .then(r => r.ok ? r.json() : null)
          .then(profile => { if (profile?.role) setUserRole(profile.role); })
          .catch(() => {});
      }
    });
  }, []);

  async function signOut() {
    await createClient().auth.signOut();
    router.push("/login");
  }

  function isActive(href: string) {
    if (href === "/proposals") return pathname.startsWith("/proposals");
    if (href === "/dashboard") return pathname.startsWith("/dashboard");
    if (href === "/bids") return pathname.startsWith("/bids");
    if (href === "/admin") return pathname.startsWith("/admin");
    if (href === "/pricing") return pathname.startsWith("/pricing");
    return pathname === href;
  }

  const linkCls = (active: boolean) =>
    `flex items-center ${collapsed ? "justify-center" : "gap-2.5"} px-3 py-2 rounded-md text-sm transition-colors ${
      active ? "bg-[#1c1c1c] text-[#ededed]" : "text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed]"
    }`;

  return (
    <aside className={`${collapsed ? "w-14" : "w-52"} shrink-0 flex flex-col border-r border-[#262626] bg-[#111111] transition-all duration-200`}>
      {/* 로고 + 접기 토글 */}
      <div className="px-3 py-4 border-b border-[#262626] flex items-center justify-between">
        <div className="flex items-center gap-2 overflow-hidden">
          <div className="w-6 h-6 rounded bg-[#3ecf8e] flex items-center justify-center font-bold text-black text-[9px] shrink-0">
            PA
          </div>
          {!collapsed && (
            <span className="text-sm font-semibold text-[#ededed] whitespace-nowrap">
              Proposal Architect
            </span>
          )}
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-[#5c5c5c] hover:text-[#ededed] text-xs transition-colors shrink-0 ml-1"
          title={collapsed ? "사이드바 펼치기" : "사이드바 접기"}
        >
          {collapsed ? "▸" : "◂"}
        </button>
      </div>

      {/* 네비게이션 */}
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {NAV.map((entry, i) => {
          if (isGroup(entry)) {
            const groupActive = pathname.startsWith(entry.basePath);
            return (
              <div key={i}>
                <button
                  onClick={() => collapsed ? router.push("/kb/search") : setKbOpen(prev => !prev)}
                  className={`w-full flex items-center ${collapsed ? "justify-center" : "gap-2.5"} px-3 py-2 rounded-md text-sm transition-colors ${
                    groupActive && !kbOpen ? "bg-[#1c1c1c] text-[#ededed]" : "text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed]"
                  }`}
                  title={collapsed ? entry.label : undefined}
                >
                  <SvgIcon d={ICONS[entry.icon] || ""} className="opacity-70 shrink-0" />
                  {!collapsed && <span className="flex-1 text-left">{entry.label}</span>}
                  {!collapsed && <span className="text-[10px] text-[#555]">{kbOpen ? "▾" : "▸"}</span>}
                </button>
                {kbOpen && !collapsed && (
                  <div className="ml-3 mt-0.5 space-y-0.5">
                    {entry.children.map(child => (
                      <Link key={child.href} href={child.href} className={linkCls(isActive(child.href))} title={collapsed ? child.label : undefined}>
                        <SvgIcon d={ICONS[child.icon] || ""} className="opacity-50 shrink-0 w-3.5 h-3.5" />
                        {!collapsed && <span>{child.label}</span>}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            );
          }
          return (
            <Link key={entry.href} href={entry.href} className={linkCls(isActive(entry.href))} title={collapsed ? entry.label : undefined} aria-label={entry.label}>
              <SvgIcon d={ICONS[entry.icon] || ""} className="opacity-70 shrink-0" />
              {!collapsed && <span>{entry.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* 유저 + 알림 */}
      <div className="border-t border-[#262626] px-3 py-3 space-y-0.5">
        {collapsed ? (
          <div className="flex flex-col items-center gap-1">
            <NotificationBell />
            <button onClick={signOut} className="p-2 rounded-md text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed] transition-colors" title="로그아웃">
              <SvgIcon d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4 M16 17l5-5-5-5 M21 12H9" className="opacity-70 shrink-0" />
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between px-3 py-1.5">
              <p className="text-xs text-[#5c5c5c] truncate flex-1">{email}</p>
              <NotificationBell />
            </div>
            <button
              onClick={signOut}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-sm text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed] transition-colors"
            >
              <SvgIcon d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4 M16 17l5-5-5-5 M21 12H9" className="opacity-70 shrink-0" />
              <span>로그아웃</span>
            </button>
          </>
        )}
      </div>
    </aside>
  );
}
