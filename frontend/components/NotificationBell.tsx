"use client";

/**
 * NotificationBell — 알림 벨 + 드롭다운 (§13-17)
 *
 * - 안읽음 배지 카운트
 * - 최근 알림 드롭다운
 * - 읽음/전체읽음 처리
 * - 클릭 시 연관 페이지 이동
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type Notification } from "@/lib/api";

export default function NotificationBell() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchNotifications = useCallback(async () => {
    try {
      const res = await api.notifications.list({ limit: 10 });
      setItems(res.data);
      setUnreadCount(res.meta?.unread_count ?? 0);
    } catch {
      // silent
    }
  }, []);

  // 초기 로드 + 30초 폴링
  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30_000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  // 외부 클릭 시 닫기
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  async function handleMarkRead(id: string) {
    await api.notifications.markRead(id);
    setItems((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)),
    );
    setUnreadCount((c) => Math.max(0, c - 1));
  }

  async function handleMarkAllRead() {
    setLoading(true);
    try {
      await api.notifications.markAllRead();
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } finally {
      setLoading(false);
    }
  }

  function handleClick(notification: Notification) {
    if (!notification.is_read) handleMarkRead(notification.id);
    setOpen(false);
    if (notification.link) {
      router.push(notification.link);
    } else if (notification.proposal_id) {
      router.push(`/proposals/${notification.proposal_id}`);
    }
  }

  function formatTime(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60_000);
    if (mins < 1) return "방금";
    if (mins < 60) return `${mins}분 전`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}시간 전`;
    const days = Math.floor(hours / 24);
    return `${days}일 전`;
  }

  const TYPE_ICON: Record<string, string> = {
    approval_request: "📋",
    approval_result: "✅",
    deadline_alert: "⏰",
    ai_complete: "🤖",
  };

  return (
    <div ref={dropdownRef} className="relative">
      {/* 벨 버튼 */}
      <button
        onClick={() => {
          setOpen(!open);
          if (!open) fetchNotifications();
        }}
        className="relative p-1.5 rounded-md text-[#8c8c8c] hover:text-[#ededed] hover:bg-[#1a1a1a] transition-colors"
        aria-label="알림"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[14px] h-[14px] flex items-center justify-center rounded-full bg-red-500 text-white text-[8px] font-bold px-0.5">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* 드롭다운 */}
      {open && (
        <div className="absolute right-0 top-full mt-1.5 w-72 bg-[#1c1c1c] border border-[#262626] rounded-xl shadow-2xl z-50 overflow-hidden">
          {/* 헤더 */}
          <div className="flex items-center justify-between px-3 py-2.5 border-b border-[#262626]">
            <span className="text-xs font-semibold text-[#ededed]">
              알림
              {unreadCount > 0 && (
                <span className="ml-1.5 text-[10px] text-[#3ecf8e]">
                  {unreadCount}개 안읽음
                </span>
              )}
            </span>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                disabled={loading}
                className="text-[10px] text-[#3ecf8e] hover:underline disabled:opacity-50"
              >
                전체 읽음
              </button>
            )}
          </div>

          {/* 목록 */}
          <div className="max-h-80 overflow-y-auto">
            {items.length === 0 ? (
              <p className="py-8 text-center text-xs text-[#5c5c5c]">
                알림이 없습니다
              </p>
            ) : (
              items.map((n) => (
                <button
                  key={n.id}
                  onClick={() => handleClick(n)}
                  className={`w-full text-left px-3 py-2.5 border-b border-[#262626]/50 last:border-0 transition-colors hover:bg-[#262626]/30 ${
                    n.is_read ? "opacity-60" : ""
                  }`}
                >
                  <div className="flex gap-2">
                    <span className="text-sm shrink-0 mt-0.5">
                      {TYPE_ICON[n.type] ?? "🔔"}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        {!n.is_read && (
                          <span className="w-1.5 h-1.5 rounded-full bg-[#3ecf8e] shrink-0" />
                        )}
                        <p className="text-[11px] font-medium text-[#ededed] truncate">
                          {n.title}
                        </p>
                      </div>
                      <p className="text-[10px] text-[#8c8c8c] mt-0.5 line-clamp-2">
                        {n.body}
                      </p>
                      <p className="text-[9px] text-[#5c5c5c] mt-1">
                        {formatTime(n.created_at)}
                      </p>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
