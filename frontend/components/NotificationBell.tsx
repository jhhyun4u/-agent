"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useDashboardWs } from "@/lib/hooks/useDashboardWs";
import type { NotificationData } from "@/lib/ws-client";

interface NotificationItem extends NotificationData {
  localId: string;
  isRead: boolean;
  receivedAt: number;
}

export interface NotificationBellProps {
  maxStoredNotifications?: number;
  autoHideDuration?: number;
  onNotificationClick?: (notification: NotificationItem) => void;
  className?: string;
  showToast?: boolean;
  toastDuration?: number;
}

function Toast({
  message,
  type,
  duration,
  onClose,
}: {
  message: string;
  type: "info" | "success" | "warning" | "error";
  duration: number;
  onClose: () => void;
}) {
  useEffect(() => {
    if (duration <= 0) return;
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const bgColor = {
    info: "bg-blue-900/60",
    success: "bg-green-900/60",
    warning: "bg-yellow-900/60",
    error: "bg-red-900/60",
  }[type];

  return (
    <div
      className={`fixed bottom-4 right-4 px-4 py-3 rounded-lg border ${bgColor} text-sm max-w-sm`}
    >
      {message}
    </div>
  );
}

export function NotificationBell({
  maxStoredNotifications = 20,
  autoHideDuration = 0,
  onNotificationClick,
  className = "",
  showToast = true,
  toastDuration = 4000,
}: NotificationBellProps) {
  const { isConnected, subscribe, getNotifications, clearMessages } =
    useDashboardWs();

  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [toast, setToast] = useState<{
    message: string;
    type: "info" | "success" | "warning" | "error";
  } | null>(null);
  const bellRef = useRef<HTMLDivElement>(null);
  const autoHideTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!isConnected) return;
    subscribe("company:default");
  }, [isConnected, subscribe]);

  useEffect(() => {
    const wsNotifications = getNotifications();
    if (wsNotifications.length === 0) return;

    const existingIds = new Set(notifications.map((n) => n.notification_id));
    const newNotifications = wsNotifications.filter(
      (n) => !existingIds.has(n.notification_id)
    );

    if (newNotifications.length > 0) {
      const items: NotificationItem[] = newNotifications.map((n) => ({
        ...n,
        localId: `${n.notification_id}-${Date.now()}`,
        isRead: false,
        receivedAt: Date.now(),
      }));

      setNotifications((prev) => {
        const all = [...items, ...prev];
        return all.slice(0, maxStoredNotifications);
      });

      if (showToast && newNotifications.length > 0) {
        const first = newNotifications[0];
        setToast({
          message: `${first.title}: ${first.message}`,
          type: first.type === "warning" ? "warning" : "info",
        });
      }
    }
  }, [getNotifications, notifications, maxStoredNotifications, showToast]);

  useEffect(() => {
    if (!isOpen || autoHideDuration <= 0) {
      if (autoHideTimerRef.current) {
        clearTimeout(autoHideTimerRef.current);
      }
      return;
    }

    autoHideTimerRef.current = setTimeout(() => {
      setIsOpen(false);
    }, autoHideDuration);

    return () => {
      if (autoHideTimerRef.current) {
        clearTimeout(autoHideTimerRef.current);
      }
    };
  }, [isOpen, autoHideDuration]);

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (bellRef.current && !bellRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const handleMarkAsRead = useCallback((localId: string) => {
    setNotifications((prev) =>
      prev.map((n) =>
        n.localId === localId ? { ...n, isRead: true } : n
      )
    );
  }, []);

  const handleDelete = useCallback((localId: string) => {
    setNotifications((prev) => prev.filter((n) => n.localId !== localId));
  }, []);

  const handleClearAll = useCallback(() => {
    setNotifications([]);
    clearMessages("notification");
  }, [clearMessages]);

  const unreadCount = notifications.filter((n) => !n.isRead).length;
  const hasUnread = unreadCount > 0;

  return (
    <>
      <div ref={bellRef} className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`relative p-2 rounded-lg text-[#8c8c8c] hover:text-[#ededed] hover:bg-[#1c1c1c] transition-colors ${
            isOpen ? "bg-[#1c1c1c] text-[#ededed]" : ""
          } ${className}`}
          title="알림"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>

          {hasUnread && (
            <div className="absolute top-0 right-0 w-5 h-5 rounded-full bg-red-500 border-2 border-[#0f0f0f] flex items-center justify-center text-white text-[10px] font-bold">
              {unreadCount > 9 ? "9+" : unreadCount}
            </div>
          )}

          {!isConnected && (
            <div className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-yellow-500 border border-[#0f0f0f]" />
          )}
        </button>

        {isOpen && (
          <div className="absolute right-0 mt-2 w-80 bg-[#1c1c1c] border border-[#262626] rounded-lg shadow-xl z-50">
            <div className="flex items-center justify-between px-4 py-3 border-b border-[#262626]">
              <div>
                <p className="text-sm font-semibold text-[#ededed]">알림</p>
                {unreadCount > 0 && (
                  <p className="text-xs text-[#8c8c8c]">
                    읽지 않은 {unreadCount}개
                  </p>
                )}
              </div>
              <button
                onClick={handleClearAll}
                disabled={notifications.length === 0}
                className="text-[10px] text-[#5c5c5c] hover:text-[#8c8c8c] disabled:opacity-40"
              >
                모두 삭제
              </button>
            </div>

            <div className="max-h-96 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="px-4 py-8 text-center">
                  <p className="text-xs text-[#5c5c5c]">알림이 없습니다</p>
                </div>
              ) : (
                <div className="divide-y divide-[#262626]">
                  {notifications.map((notif) => (
                    <div
                      key={notif.localId}
                      className={`px-4 py-3 hover:bg-[#262626] transition-colors cursor-pointer ${
                        !notif.isRead ? "bg-[#0f0f0f]" : ""
                      }`}
                      onClick={() => {
                        handleMarkAsRead(notif.localId);
                        onNotificationClick?.(notif);
                      }}
                    >
                      <div className="flex items-start gap-3">
                        {!notif.isRead ? (
                          <div className="w-2 h-2 rounded-full bg-[#3ecf8e] mt-1.5 shrink-0" />
                        ) : (
                          <div className="w-2 h-2 rounded-full bg-[#262626] mt-1.5 shrink-0" />
                        )}

                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-[#ededed]">
                            {notif.title}
                          </p>
                          <p className="text-xs text-[#8c8c8c] mt-0.5">
                            {notif.message}
                          </p>
                          {notif.link && (
                            <a
                              href={notif.link}
                              className="text-xs text-[#3ecf8e] hover:underline mt-1 inline-block"
                              onClick={(e) => e.stopPropagation()}
                            >
                              자세히 보기 →
                            </a>
                          )}
                          <p className="text-[10px] text-[#5c5c5c] mt-1">
                            방금 전
                          </p>
                        </div>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(notif.localId);
                          }}
                          className="text-[#5c5c5c] hover:text-red-400 transition-colors shrink-0"
                        >
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M6 18L18 6M6 6l12 12"
                            />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {notifications.length > 0 && (
              <div className="px-4 py-2 border-t border-[#262626] text-center">
                <p className="text-[10px] text-[#5c5c5c]">
                  총 {notifications.length}개 알림
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={toastDuration}
          onClose={() => setToast(null)}
        />
      )}
    </>
  );
}

export function useNotificationCount(): number {
  const { getNotifications } = useDashboardWs();
  const [count, setCount] = useState(0);

  useEffect(() => {
    const notifications = getNotifications();
    setCount(notifications.length);
  }, [getNotifications]);

  return count;
}
