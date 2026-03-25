"use client";

/**
 * AppSidebar — 앱 전체 공유 사이드바
 * 대시보드 / 최근 작업 / 공고 / 제안 작업 / 지식 베이스 / 자료 / 아카이브 / Admin
 */

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { api, ProposalSummary } from "@/lib/api";
import NotificationBell from "@/components/NotificationBell";
import ThemeToggle from "@/components/ThemeToggle";

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
  analytics: "M18 20V10 M12 20V4 M6 20v-6",
  recent: "M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z M12 6v6l4 2",
  kb: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253",
  search: "M21 21l-6-6m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0z",
  content: "M4 6h16M4 12h16M4 18h7",
  clients: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75",
  competitors: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M20 8v6 M23 11h-6",
  lessons: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 1 1 7.072 0l-.548.547A3.374 3.374 0 0 0 14 18.469V19a2 2 0 1 1-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  qa: "M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01",
  labor: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M22 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75",
  market: "M3 3v18h18 M18.7 8l-5.1 5.2-2.8-2.7L7 14.3",
  resources: "M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-6l-2-2H5a2 2 0 0 0-2 2z",
  archive: "M21 8v13H3V8 M1 3h22v5H1z M10 12h4",
  admin: "M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z",
  org: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75",
  prompt: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
  experiment: "M9 3h6v2H9z M10 5v6l-4 7h12l-4-7V5",
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
  { href: "/monitoring", label: "공고 모니터링", icon: "bids" },
  { href: "/proposals", label: "제안 프로젝트", icon: "proposals" },
  { href: "/pricing", label: "가격 시뮬레이터", icon: "pricing" },
  {
    label: "지식 베이스", icon: "kb", basePath: "/kb",
    children: [
      { href: "/kb/search", label: "통합 검색", icon: "search" },
      { href: "/kb/content", label: "콘텐츠", icon: "content" },
      { href: "/kb/clients", label: "발주기관", icon: "clients" },
      { href: "/kb/competitors", label: "경쟁사", icon: "competitors" },
      { href: "/kb/lessons", label: "교훈", icon: "lessons" },
      { href: "/kb/qa", label: "Q&A", icon: "qa" },
      { href: "/kb/labor-rates", label: "노임단가", icon: "labor" },
      { href: "/kb/market-prices", label: "시장가격", icon: "market" },
    ],
  },
];

const ADMIN_GROUP: NavGroup = {
  label: "Admin",
  icon: "admin",
  basePath: "/admin",
  children: [
    { href: "/admin", label: "이용자 관리", icon: "org" },
    { href: "/admin/prompts", label: "프롬프트 관리", icon: "prompt" },
    { href: "/admin/prompts/experiments", label: "A/B 실험", icon: "experiment" },
  ],
};

const ACTIVE_STATUSES = new Set(["initialized", "processing", "running"]);

export default function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [userRole, setUserRole] = useState("");
  const [kbOpen, setKbOpen] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("sidebar-kb-expanded") === "true";
  });
  const [adminOpen, setAdminOpen] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("sidebar-admin-expanded") === "true";
  });
  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    // 좁은 화면이면 기본 접힘
    const saved = localStorage.getItem("sidebar-collapsed");
    if (saved !== null) return saved === "true";
    return window.innerWidth < 1024;
  });

  function toggleKb() {
    setKbOpen(prev => {
      const next = !prev;
      localStorage.setItem("sidebar-kb-expanded", String(next));
      return next;
    });
  }

  function toggleAdmin() {
    setAdminOpen(prev => {
      const next = !prev;
      localStorage.setItem("sidebar-admin-expanded", String(next));
      return next;
    });
  }

  // KB / Admin 하위 페이지에 있으면 자동 펼침
  useEffect(() => {
    if (pathname.startsWith("/kb")) {
      setKbOpen(true);
      localStorage.setItem("sidebar-kb-expanded", "true");
    }
    if (pathname.startsWith("/admin")) {
      setAdminOpen(true);
      localStorage.setItem("sidebar-admin-expanded", "true");
    }
  }, [pathname]);

  useEffect(() => {
    // DEV: Supabase 미연결 시 더미 데이터 사용
    if (process.env.NODE_ENV === "development") {
      setEmail("dev@tenopa.co.kr");
      setUserRole("admin");
      return;
    }
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

  // ── 최근 작업 ──
  const [recentProposals, setRecentProposals] = useState<ProposalSummary[]>([]);

  const fetchRecent = useCallback(async () => {
    try {
      const { items } = await api.proposals.list({ scope: "my" });
      setRecentProposals(
        items
          .filter(p => ACTIVE_STATUSES.has(p.status))
          .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
          .slice(0, 3)
      );
    } catch { /* 실패 시 빈 상태 유지 */ }
  }, []);

  useEffect(() => { fetchRecent(); }, [fetchRecent, pathname]);

  function calcDDay(deadline: string | null): number | null {
    if (!deadline) return null;
    const diff = Math.ceil((new Date(deadline).getTime() - Date.now()) / 86400000);
    return diff;
  }

  function dDayColor(d: number): string {
    if (d <= 3) return "text-red-400";
    if (d <= 14) return "text-yellow-400";
    return "text-[#8c8c8c]";
  }

  function isActive(href: string) {
    if (href === "/proposals") return pathname.startsWith("/proposals");
    if (href === "/dashboard") return pathname.startsWith("/dashboard");
    if (href === "/monitoring") return pathname.startsWith("/monitoring");
    if (href === "/pricing") return pathname.startsWith("/pricing");
    if (href === "/analytics") return pathname.startsWith("/analytics");
    // Admin 하위 메뉴: 정확 매칭 (그룹 하이라이트는 basePath로 처리)
    if (href === "/admin") return pathname === "/admin";
    if (href === "/admin/prompts") return pathname === "/admin/prompts";
    if (href === "/admin/prompts/experiments") return pathname.startsWith("/admin/prompts/experiments");
    return pathname === href;
  }

  const linkCls = (active: boolean) =>
    `flex items-center ${collapsed ? "justify-center" : "gap-2.5"} px-3 py-2 rounded-md text-sm transition-colors ${
      active ? "bg-[#1c1c1c] text-[#ededed]" : "text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed]"
    }`;

  const childLinkCls = (active: boolean) =>
    `flex items-center ${collapsed ? "justify-center" : "gap-2"} px-3 py-1.5 rounded-md text-[11px] transition-colors ${
      active ? "bg-[#1c1c1c] text-[#ededed]" : "text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed]"
    }`;


  return (
    <>
    <div className="flex shrink-0 relative group/sidebar">
      <aside className={`${collapsed ? "w-14" : "w-52"} flex flex-col border-r border-[#262626] bg-[#111111] transition-all duration-200`}>
      {/* 로고 */}
      <div className="px-3 py-4 border-b border-[#262626] flex items-center overflow-hidden">
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
      </div>

      {/* 네비게이션 */}
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {/* 대시보드 */}
        <Link href={(NAV[0] as NavItem).href} className={linkCls(isActive((NAV[0] as NavItem).href))} title={collapsed ? (NAV[0] as NavItem).label : undefined} aria-label={(NAV[0] as NavItem).label}>
          <SvgIcon d={ICONS[(NAV[0] as NavItem).icon] || ""} className="opacity-70 shrink-0" />
          {!collapsed && <span>{(NAV[0] as NavItem).label}</span>}
        </Link>

        {/* 최근 작업 — collapsed: 시계 아이콘, expanded: 목록 */}
        {collapsed ? (
          recentProposals.length > 0 && (
            <button
              title={`최근 작업 ${recentProposals.length}건`}
              onClick={() => router.push("/proposals")}
              className="relative w-full flex justify-center px-3 py-2 rounded-md text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed] transition-colors"
            >
              <SvgIcon d={ICONS.recent} className="opacity-70" />
              <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-[#3ecf8e] text-black text-[8px] font-bold flex items-center justify-center">{recentProposals.length}</span>
            </button>
          )
        ) : (
          recentProposals.length > 0 && (
            <div className="mt-2 mb-2">
              <p className="px-3 py-1 text-[10px] font-medium uppercase tracking-wider text-[#555]">최근 작업</p>
              {recentProposals.map(p => {
                const d = calcDDay(p.deadline);
                const dotColor = p.status === "initialized" ? "#f59e0b" : "#3ecf8e";
                return (
                  <Link key={p.id} href={`/proposals/${p.id}`}
                    className="flex items-start gap-2 px-3 py-1.5 rounded-md text-sm transition-colors text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed]"
                  >
                    <span className="mt-1.5 w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: dotColor }} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[#cdcdcd] text-[13px]">{p.title}</p>
                      <p className="text-[10px]">
                        {d !== null && <span className={dDayColor(d)}>D{d <= 0 ? d : `-${d}`}</span>}
                        {d !== null && " · "}
                        <span>Phase {p.phases_completed}/5</span>
                      </p>
                    </div>
                  </Link>
                );
              })}
            </div>
          )
        )}

        {/* 나머지 NAV (공고~아카이브) */}
        {NAV.slice(1).map((entry, i) => {
          if (isGroup(entry)) {
            const groupActive = pathname.startsWith(entry.basePath);
            return (
              <div key={i}>
                <button
                  onClick={() => collapsed ? router.push("/kb/search") : toggleKb()}
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
                      <Link key={child.href} href={child.href} className={childLinkCls(isActive(child.href))} title={collapsed ? child.label : undefined}>
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
            <Link key={(entry as NavItem).href} href={(entry as NavItem).href} className={linkCls(isActive((entry as NavItem).href))} title={collapsed ? (entry as NavItem).label : undefined} aria-label={(entry as NavItem).label}>
              <SvgIcon d={ICONS[(entry as NavItem).icon] || ""} className="opacity-70 shrink-0" />
              {!collapsed && <span>{(entry as NavItem).label}</span>}
            </Link>
          );
        })}

        {/* Admin (role 조건부, 접이식 하위 메뉴) */}
        {(userRole === "admin" || userRole === "manager") && (
          <div>
            <button
              onClick={() => collapsed ? router.push("/admin") : toggleAdmin()}
              className={`w-full flex items-center ${collapsed ? "justify-center" : "gap-2.5"} px-3 py-2 rounded-md text-sm transition-colors ${
                pathname.startsWith("/admin") && !adminOpen ? "bg-[#1c1c1c] text-[#ededed]" : "text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed]"
              }`}
              title={collapsed ? ADMIN_GROUP.label : undefined}
            >
              <SvgIcon d={ICONS[ADMIN_GROUP.icon] || ""} className="opacity-70 shrink-0" />
              {!collapsed && <span className="flex-1 text-left">{ADMIN_GROUP.label}</span>}
              {!collapsed && <span className="text-[10px] text-[#555]">{adminOpen ? "▾" : "▸"}</span>}
            </button>
            {adminOpen && !collapsed && (
              <div className="ml-3 mt-0.5 space-y-0.5">
                {ADMIN_GROUP.children.map(child => (
                  <Link key={child.href} href={child.href} className={childLinkCls(isActive(child.href))} title={collapsed ? child.label : undefined}>
                    <SvgIcon d={ICONS[child.icon] || ""} className="opacity-50 shrink-0 w-3.5 h-3.5" />
                    {!collapsed && <span>{child.label}</span>}
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}
      </nav>

      {/* 유저 + 테마 + 알림 */}
      <div className="border-t border-[#262626] px-3 py-3 space-y-0.5">
        <ThemeToggle collapsed={collapsed} />
        {collapsed ? (
          <div className="flex flex-col items-center gap-1">
            <NotificationBell />
            <button onClick={signOut} className="p-2 rounded-md text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed] transition-colors" title="로그아웃" aria-label="로그아웃">
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
              aria-label="로그아웃"
            >
              <SvgIcon d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4 M16 17l5-5-5-5 M21 12H9" className="opacity-70 shrink-0" />
              <span>로그아웃</span>
            </button>
          </>
        )}
      </div>
    </aside>
      {/* Claude Desktop 스타일 토글 — 사이드바 오른쪽 경계에 세로 핸들 */}
      <button
        onClick={() => {
          setCollapsed(prev => {
            const next = !prev;
            localStorage.setItem("sidebar-collapsed", String(next));
            return next;
          });
        }}
        className="absolute top-1/2 -translate-y-1/2 -right-3 z-10 w-6 h-12 flex items-center justify-center rounded-md bg-[#1c1c1c] border border-[#333] text-[#666] hover:text-[#ededed] hover:bg-[#262626] hover:border-[#444] transition-all duration-150 opacity-0 hover:opacity-100 group-hover/sidebar:opacity-100"
        title={collapsed ? "사이드바 펼치기" : "사이드바 접기"}
        aria-label={collapsed ? "사이드바 펼치기" : "사이드바 접기"}
      >
        <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          {collapsed
            ? <path d="M9 18l6-6-6-6" />
            : <path d="M15 18l-6-6 6-6" />
          }
        </svg>
      </button>
    </div>
    </>
  );
}
