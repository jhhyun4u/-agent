"use client";

/**
 * AppSidebar — VS Code / Claude Desktop 스타일 사이드바
 * - PA 로고 클릭: 열기/닫기 토글
 * - 우측 경계 드래그: 너비 조절 (180~360px)
 * - 우측 경계 더블클릭: 기본 너비로 리셋
 * - 모바일: 좌측 슬라이드 + 배경 클릭/Escape로 닫기
 * - 상태(접힘/너비/그룹 펼침)는 localStorage에 영속
 *
 * z-index 규약: 모바일오버레이=z-50, 햄버거=z-50, 데스크톱사이드바=z-30, 드래그핸들=z-40, 드래그오버레이=z-[9999]
 */

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { api, ProposalSummary } from "@/lib/api";
import NotificationBell from "@/components/NotificationBell";
import ThemeToggle from "@/components/ThemeToggle";

/* ── SVG 아이콘 ── */
function SvgIcon({ d, className = "" }: { d: string; className?: string }) {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      className={`w-4 h-4 ${className}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ color: "inherit" }}
    >
      <path d={d} />
    </svg>
  );
}

const ICONS: Record<string, string> = {
  dashboard: "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10",
  bids: "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z",
  proposals:
    "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8",
  kb: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253",
  search: "M21 21l-6-6m2-5a7 7 0 1 1-14 0 7 7 0 0 1 14 0z",
  content: "M4 6h16M4 12h16M4 18h7",
  clients:
    "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75",
  competitors:
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M20 8v6 M23 11h-6",
  lessons:
    "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 1 1 7.072 0l-.548.547A3.374 3.374 0 0 0 14 18.469V19a2 2 0 1 1-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  qa: "M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01",
  labor:
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M22 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75",
  market: "M3 3v18h18 M18.7 8l-5.1 5.2-2.8-2.7L7 14.3",
  admin:
    "M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z",
  org: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75",
  prompt: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
  experiment: "M9 3h6v2H9z M10 5v6l-4 7h12l-4-7V5",
  settings:
    "M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z",
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

// 대시보드를 명시적 변수로 분리 (인덱스 하드코딩 방지 — M-2)
const DASHBOARD: NavItem = {
  href: "/dashboard",
  label: "대시보드",
  icon: "dashboard",
};

const NAV_REST: NavEntry[] = [
  { href: "/monitoring", label: "공고 모니터링", icon: "bids" },
  { href: "/proposals", label: "제안 프로젝트", icon: "proposals" },
  {
    label: "지식 베이스",
    icon: "kb",
    basePath: "/kb",
    children: [
      { href: "/kb/content", label: "자료함", icon: "content" },
      { href: "/kb/market", label: "시장 분석", icon: "market" },
      { href: "/kb/pricing", label: "예산/단가 가이드", icon: "labor" },
    ],
  },
];

const ADMIN_GROUP: NavGroup = {
  label: "관리",
  icon: "admin",
  basePath: "/admin",
  children: [
    { href: "/admin", label: "이용자 관리", icon: "org" },
    { href: "/admin/prompts", label: "프롬프트 관리", icon: "prompt" },
    {
      href: "/admin/prompts/experiments",
      label: "A/B 실험",
      icon: "experiment",
    },
    { href: "/settings", label: "설정", icon: "settings" },
  ],
};

const ACTIVE_STATUSES = new Set(["initialized", "processing", "running"]);
const DEFAULT_WIDTH = 208;
const MIN_WIDTH = 180;
const MAX_WIDTH = 360;

/* ── localStorage 안전 헬퍼 (SSR/시크릿모드/스토리지 가득 참 방어) ── */
function safeGetItem(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}
function safeSetItem(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* 무시 */
  }
}

/* ── 스타일 헬퍼 ── */
const lCls = (active: boolean) =>
  `flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors ${
    active
      ? "bg-[#1c1c1c] text-[#ededed]"
      : "text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed]"
  }`;
const cLCls = (active: boolean) =>
  `flex items-center gap-2 px-3 py-1.5 rounded-md text-[11px] transition-colors ${
    active
      ? "bg-[#1c1c1c] text-[#ededed]"
      : "text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed]"
  }`;

export default function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [userRole, setUserRole] = useState("");
  const [mobileOpen, setMobileOpen] = useState(false);

  // ── SSR 안전: 초기값 기본 → 마운트 후 localStorage 복원 ──
  const [collapsed, setCollapsed] = useState<boolean | null>(null);
  const [sidebarWidth, setSidebarWidth] = useState(DEFAULT_WIDTH);
  const [kbOpen, setKbOpen] = useState(false);
  const [adminOpen, setAdminOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [dragging, setDragging] = useState(false);

  // 마운트 시 localStorage → state 복원
  useEffect(() => {
    if (typeof window === "undefined") return; // SSR 방어

    const savedCollapsed = safeGetItem("sidebar-collapsed");
    let initialCollapsed = false; // 기본값: 열려있음

    if (savedCollapsed !== null) {
      initialCollapsed = savedCollapsed === "true";
    } else if (window.innerWidth < 1024) {
      initialCollapsed = true; // 모바일이면 닫혀있음
    }

    setCollapsed(initialCollapsed);

    const savedWidth = safeGetItem("sidebar-width");
    if (savedWidth) {
      const w = Number(savedWidth);
      if (Number.isFinite(w))
        setSidebarWidth(Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, w)));
    }

    setKbOpen(safeGetItem("sidebar-kb-expanded") === "true");
    setAdminOpen(safeGetItem("sidebar-admin-expanded") === "true");
    setMounted(true);
  }, []);

  // ── 드래그 리사이즈 (C-3: body.pointerEvents 대신 오버레이 사용) ──
  const sidebarRef = useRef<HTMLDivElement>(null);
  const liveWidthRef = useRef(DEFAULT_WIDTH); // M-1: React 배치와 무관하게 실시간 너비 추적

  const handleDragMove = useCallback((ev: React.MouseEvent | MouseEvent) => {
    if (!sidebarRef.current) return;
    const rect = sidebarRef.current.getBoundingClientRect();
    const raw = ev.clientX - rect.left; // C-4: sidebar offset 보정
    if (!Number.isFinite(raw)) return; // L-7: NaN 방어
    const clamped = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, raw));
    liveWidthRef.current = clamped;
    setSidebarWidth(clamped);
  }, []);

  const handleDragEnd = useCallback(() => {
    setDragging(false);
    safeSetItem("sidebar-width", String(liveWidthRef.current)); // M-1: ref에서 읽어 배치 무관
  }, []);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      liveWidthRef.current = sidebarWidth;
      setDragging(true);
    },
    [sidebarWidth],
  );

  const handleDoubleClick = useCallback(() => {
    setSidebarWidth(DEFAULT_WIDTH);
    liveWidthRef.current = DEFAULT_WIDTH;
    safeSetItem("sidebar-width", String(DEFAULT_WIDTH));
  }, []);

  // ── 토글 함수들 (M-3: 일관되게 useCallback) ──
  const toggleSidebar = useCallback(() => {
    setCollapsed((prev) => {
      // null이면 닫혀있는 상태(true)로 시작
      if (prev === null) return true;
      // 그 후는 토글
      return !prev;
    });
  }, []);

  const toggleKb = useCallback(() => {
    setKbOpen((prev) => {
      const next = !prev;
      safeSetItem("sidebar-kb-expanded", String(next));
      return next;
    });
  }, []);

  const toggleAdmin = useCallback(() => {
    setAdminOpen((prev) => {
      const next = !prev;
      safeSetItem("sidebar-admin-expanded", String(next));
      return next;
    });
  }, []);

  // collapsed 상태 변경 → localStorage 저장
  useEffect(() => {
    if (collapsed === null) return; // 초기화 전 무시
    safeSetItem("sidebar-collapsed", String(collapsed));
  }, [collapsed]);

  // KB / Admin 하위 페이지 첫 진입 시만 자동 펼침 (M-4: 사용자 닫기 의도 존중)
  const prevPathRef = useRef(pathname);
  useEffect(() => {
    const wasInKb = prevPathRef.current.startsWith("/kb");
    const wasInAdmin = prevPathRef.current.startsWith("/admin");
    if (pathname.startsWith("/kb") && !wasInKb) {
      setKbOpen(true);
      safeSetItem("sidebar-kb-expanded", "true");
    }
    if (pathname.startsWith("/admin") && !wasInAdmin) {
      setAdminOpen(true);
      safeSetItem("sidebar-admin-expanded", "true");
    }
    prevPathRef.current = pathname;
  }, [pathname]);

  // 모바일: 페이지 이동 시 오버레이 닫기
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  // 모바일: Escape 키로 닫기 (L-3)
  useEffect(() => {
    if (!mobileOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [mobileOpen]);

  // ── 유저 정보 (M-6: mounted guard) ──
  useEffect(() => {
    let active = true;
    if (process.env.NODE_ENV === "development") {
      setEmail("dev@tenopa.co.kr");
      setUserRole("admin");
      return;
    }
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      if (active) setEmail(data.user?.email ?? "");
    });
    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    supabase.auth.getSession().then(({ data }) => {
      const token = data.session?.access_token;
      if (token) {
        fetch(`${apiBase}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
          .then((r) => (r.ok ? r.json() : null))
          .then((profile) => {
            if (active && profile?.role) setUserRole(profile.role);
          })
          .catch(() => {});
      }
    });
    return () => {
      active = false;
    };
  }, []);

  // ── 로그아웃 (M-5: 에러 처리) ──
  async function signOut() {
    try {
      await createClient().auth.signOut();
    } finally {
      router.push("/login");
    }
  }

  // ── 최근 작업 (C-5: AbortController) ──
  const [recentProposals, setRecentProposals] = useState<ProposalSummary[]>([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.proposals.list({ scope: "my" });
        if (!cancelled) {
          setRecentProposals(
            data
              .filter((p: ProposalSummary) => ACTIVE_STATUSES.has(p.status))
              .sort(
                (a: ProposalSummary, b: ProposalSummary) =>
                  new Date(b.updated_at).getTime() -
                  new Date(a.updated_at).getTime(),
              )
              .slice(0, 3),
          );
        }
      } catch {
        /* 실패 시 빈 상태 유지 */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [pathname]);

  // ── 헬퍼 ──
  function calcDDay(deadline: string | null): number | null {
    if (!deadline) return null;
    return Math.ceil((new Date(deadline).getTime() - Date.now()) / 86400000);
  }

  function formatDDay(d: number): string {
    if (d > 0) return `D-${d}`;
    if (d === 0) return "D-Day";
    return `D+${Math.abs(d)}`; // L-1: 마감 초과 표시 수정
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
    if (href === "/analytics") return pathname.startsWith("/analytics");
    if (href === "/admin") return pathname === "/admin";
    if (href === "/admin/prompts") return pathname === "/admin/prompts";
    if (href === "/admin/prompts/experiments")
      return pathname.startsWith("/admin/prompts/experiments");
    return pathname === href;
  }

  // ── 사이드바 공용 콘텐츠 ──
  function renderSidebarContent(forMobile: boolean) {
    return (
      <>
        {/* 로고 — 클릭으로 사이드바 토글 */}
        <div className="px-3 py-4 border-b border-[#262626] flex items-center overflow-hidden">
          <button
            onClick={forMobile ? () => setMobileOpen(false) : toggleSidebar}
            className="flex items-center gap-2 overflow-hidden group/logo"
            title={forMobile ? "메뉴 닫기" : "사이드바 열기/닫기"}
            aria-label={
              forMobile
                ? "메뉴 닫기"
                : collapsed
                  ? "사이드바 펼치기"
                  : "사이드바 접기"
            }
          >
            <div className="w-6 h-6 rounded bg-[#3ecf8e] flex items-center justify-center font-bold text-black text-[9px] shrink-0 group-hover/logo:bg-[#4fe0a0] transition-colors">
              PA
            </div>
            <span className="text-sm font-semibold text-[#ededed] whitespace-nowrap">
              Proposal Coworker
            </span>
          </button>
        </div>

        {/* 네비게이션 */}
        <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
          {/* 대시보드 */}
          <Link
            href={DASHBOARD.href}
            className={lCls(isActive(DASHBOARD.href))}
            aria-label={DASHBOARD.label}
          >
            <SvgIcon
              d={ICONS[DASHBOARD.icon] || ""}
              className="opacity-70 shrink-0"
            />
            <span>{DASHBOARD.label}</span>
          </Link>

          {/* 나머지 NAV (공고~지식 베이스) — M-8: basePath/href를 key로 사용 */}
          {NAV_REST.map((entry) => {
            if (isGroup(entry)) {
              const groupActive = pathname.startsWith(entry.basePath);
              const open = entry.basePath === "/kb" ? kbOpen : false;
              const toggle = entry.basePath === "/kb" ? toggleKb : () => {};
              return (
                <div key={entry.basePath}>
                  <button
                    onClick={toggle}
                    aria-expanded={open}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors ${
                      groupActive && !open
                        ? "bg-[#1c1c1c] text-[#ededed]"
                        : "text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed]"
                    }`}
                  >
                    <SvgIcon
                      d={ICONS[entry.icon] || ""}
                      className="opacity-70 shrink-0"
                    />
                    <span className="flex-1 text-left">{entry.label}</span>
                    <span className="text-[10px] text-[#555]">
                      {open ? "▾" : "▸"}
                    </span>
                  </button>
                  {open && (
                    <div className="ml-3 mt-0.5 space-y-0.5">
                      {entry.children.map((child) => (
                        <Link
                          key={child.href}
                          href={child.href}
                          className={cLCls(isActive(child.href))}
                        >
                          <SvgIcon
                            d={ICONS[child.icon] || ""}
                            className="opacity-50 shrink-0 w-3.5 h-3.5"
                          />
                          <span>{child.label}</span>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              );
            }
            return (
              <Link
                key={entry.href}
                href={entry.href}
                className={lCls(isActive(entry.href))}
                aria-label={entry.label}
              >
                <SvgIcon
                  d={ICONS[entry.icon] || ""}
                  className="opacity-70 shrink-0"
                />
                <span>{entry.label}</span>
              </Link>
            );
          })}

          {/* 최근 작업 — KB 아래로 이동 */}
          {recentProposals.length > 0 && (
            <div className="mt-2 mb-2">
              <p className="px-3 py-1 text-[10px] font-medium uppercase tracking-wider text-[#555]">
                최근 작업
              </p>
              {recentProposals.map((p) => {
                const d = calcDDay(p.deadline);
                const dotColor =
                  p.status === "initialized" ? "#f59e0b" : "#3ecf8e";
                return (
                  <Link
                    key={p.id}
                    href={`/proposals/${p.id}`}
                    className="flex items-start gap-2 px-3 py-1.5 rounded-md text-sm transition-colors text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed]"
                  >
                    <span
                      className="mt-1.5 w-2 h-2 rounded-full shrink-0"
                      style={{ backgroundColor: dotColor }}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[#cdcdcd] text-[13px]">
                        {p.title}
                      </p>
                      <p className="text-[10px]">
                        {d !== null && (
                          <span className={dDayColor(d)}>{formatDDay(d)}</span>
                        )}
                        {d !== null && " · "}
                        <span>Phase {p.phases_completed}/5</span>
                      </p>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </nav>

        {/* 하단: 유저 + 테마 + 알림 + Admin */}
        <div className="border-t border-[#262626] px-3 py-3 space-y-0.5">
          <ThemeToggle collapsed={false} />
          <div className="flex items-center justify-between px-3 py-1.5">
            <span className="text-xs text-[#5c5c5c] truncate flex-1">
              {email}
            </span>
            <NotificationBell />
          </div>

          {/* Admin 관리 메뉴 (하단) */}
          {(userRole === "admin" || userRole === "manager") && (
            <div className="mt-2 pt-2 border-t border-[#262626]">
              <button
                onClick={toggleAdmin}
                aria-expanded={adminOpen}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors ${
                  pathname.startsWith("/admin") && !adminOpen
                    ? "bg-[#1c1c1c] text-[#ededed]"
                    : "text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed]"
                }`}
              >
                <SvgIcon
                  d={ICONS[ADMIN_GROUP.icon] || ""}
                  className="opacity-70 shrink-0"
                />
                <span className="flex-1 text-left">{ADMIN_GROUP.label}</span>
                <span className="text-[10px] text-[#555]">
                  {adminOpen ? "▾" : "▸"}
                </span>
              </button>
              {adminOpen && (
                <div className="ml-3 mt-0.5 space-y-0.5">
                  {ADMIN_GROUP.children.map((child) => (
                    <Link
                      key={child.href}
                      href={child.href}
                      className={cLCls(isActive(child.href))}
                    >
                      <SvgIcon
                        d={ICONS[child.icon] || ""}
                        className="opacity-50 shrink-0 w-3.5 h-3.5"
                      />
                      <span>{child.label}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}

          <button
            onClick={signOut}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-sm text-[#8c8c8c] hover:bg-[#1a1a1a] hover:text-[#ededed] transition-colors"
            aria-label="로그아웃"
          >
            <SvgIcon
              d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4 M16 17l5-5-5-5 M21 12H9"
              className="opacity-70 shrink-0"
            />
            <span>로그아웃</span>
          </button>
        </div>
      </>
    );
  }

  const showCollapsed = collapsed === true; // collapsed가 true일 때만 닫혀있음
  const currentWidth = sidebarWidth;

  return (
    <>
      {/* 모바일 햄버거 (lg 미만) — L-5: DOM에서 제거하지 않고 토글 */}
      <button
        onClick={() => setMobileOpen((v) => !v)}
        className="lg:hidden fixed top-3 left-3 z-50 p-2 bg-[#1c1c1c] border border-[#262626] rounded-lg"
        aria-label={mobileOpen ? "메뉴 닫기" : "메뉴 열기"}
        aria-expanded={mobileOpen}
      >
        <SvgIcon d="M3 12h18M3 6h18M3 18h18" />
      </button>

      {/* 모바일 오버레이 (lg 미만) — 슬라이드, L-3: role + Escape */}
      <div
        role="presentation"
        aria-hidden={!mobileOpen}
        className={`lg:hidden fixed inset-0 z-50 transition-colors duration-300 ${
          mobileOpen
            ? "bg-[#0f0f0f]/60 pointer-events-auto"
            : "bg-transparent pointer-events-none"
        }`}
        onClick={() => setMobileOpen(false)}
      >
        <aside
          className={`w-64 h-full bg-[#111111] border-r border-[#262626] flex flex-col transition-transform duration-300 ease-in-out ${
            mobileOpen ? "translate-x-0" : "-translate-x-full"
          }`}
          onClick={(e) => e.stopPropagation()}
        >
          {renderSidebarContent(true)}
        </aside>
      </div>

      {/* 데스크톱 사이드바 (lg 이상) */}
      <div className="hidden lg:flex shrink-0 relative" ref={sidebarRef}>
        {/* 닫혀있을 때: PA 아이콘 미니바 */}
        {showCollapsed && (
          <div className="w-12 h-full flex flex-col items-center border-r border-[#262626] bg-[#111111] pt-4">
            <button
              onClick={toggleSidebar}
              className="w-7 h-7 rounded bg-[#3ecf8e] flex items-center justify-center font-bold text-black text-[9px] shrink-0 hover:bg-[#4fe0a0] transition-colors"
              title="사이드바 펼치기"
              aria-label="사이드바 펼치기"
            >
              PA
            </button>
          </div>
        )}

        {/* 열려있을 때: 전체 사이드바 */}
        {!showCollapsed && (
          <>
            <aside
              className="h-full flex flex-col border-r border-[#262626] bg-[#111111] overflow-hidden"
              style={{ width: currentWidth }}
            >
              {renderSidebarContent(false)}
            </aside>

            {/* 드래그 핸들 — 우측 경계 */}
            <div
              onMouseDown={handleMouseDown}
              onDoubleClick={handleDoubleClick}
              className="absolute top-0 -right-1 w-2 h-full cursor-col-resize z-40 group/resize"
              title="드래그로 너비 조절 · 더블클릭으로 초기화"
            >
              <div className="w-px h-full mx-auto bg-transparent group-hover/resize:bg-[#3ecf8e] transition-colors" />
            </div>
          </>
        )}
      </div>

      {/* C-3: 드래그 오버레이 — body.pointerEvents 대신 투명 오버레이 사용 */}
      {dragging && (
        <div
          className="fixed inset-0 z-[9999] cursor-col-resize"
          onMouseMove={handleDragMove}
          onMouseUp={handleDragEnd}
        />
      )}
    </>
  );
}
