"use client";

import { useEffect, useCallback, useRef, useState } from "react";
import { useDashboardWs } from "@/lib/hooks/useDashboardWs";
import type { ProposalStatusData, TeamPerformanceData } from "@/lib/ws-client";

export interface DashboardWithRealtimeProps {
  teamId?: string;
  divisionId?: string;
  scope?: "team" | "division" | "company";
  onProposalStatusChange?: (update: ProposalStatusData) => void;
  onTeamPerformanceUpdate?: (update: TeamPerformanceData) => void;
  onNotificationReceived?: (message: string) => void;
}

export function useProposalListWithRealtime(
  proposals: any[],
  setProposals: (proposals: any[]) => void,
  teamId?: string,
  divisionId?: string
) {
  const { isConnected, subscribe, getProposalStatusUpdates } = useDashboardWs();
  const lastUpdateRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!isConnected) return;

    const channels: string[] = [];
    if (teamId) channels.push(`team:${teamId}`);
    if (divisionId) channels.push(`division:${divisionId}`);
    if (channels.length === 0) channels.push("company:default");

    for (const channel of channels) {
      subscribe(channel);
    }
  }, [isConnected, teamId, divisionId, subscribe]);

  useEffect(() => {
    const updates = getProposalStatusUpdates();
    const updateIds = new Set(updates.map((u) => u.proposal_id));

    if (updateIds.size === lastUpdateRef.current.size) return;

    setProposals(
      proposals.map((proposal) => {
        const update = updates.find((u) => u.proposal_id === proposal.id);
        if (update) {
          return {
            ...proposal,
            status: update.new_status,
            updated_at: update.timestamp,
          };
        }
        return proposal;
      })
    );

    lastUpdateRef.current = updateIds;
  }, [getProposalStatusUpdates, proposals, setProposals]);
}

export function useTeamPerformanceRealtime(
  onUpdate?: (data: TeamPerformanceData) => void
) {
  const { isConnected, subscribe, getLatestTeamPerformance } = useDashboardWs();

  useEffect(() => {
    if (!isConnected) return;
    subscribe("company:default");
  }, [isConnected, subscribe]);

  useEffect(() => {
    const latestPerformance = getLatestTeamPerformance();
    if (latestPerformance && onUpdate) {
      onUpdate(latestPerformance);
    }
  }, [getLatestTeamPerformance, onUpdate]);
}

export function useNotificationListener(
  onNotification?: (title: string, message: string, type: string) => void
) {
  const { isConnected, subscribe, getNotifications } = useDashboardWs();
  const processedRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!isConnected) return;
    subscribe("company:default");
  }, [isConnected, subscribe]);

  useEffect(() => {
    const notifications = getNotifications();
    for (const notif of notifications) {
      if (!processedRef.current.has(notif.notification_id)) {
        processedRef.current.add(notif.notification_id);
        if (onNotification) {
          onNotification(notif.title, notif.message, notif.type);
        }
      }
    }
  }, [getNotifications, onNotification]);
}

export function DashboardWithRealtime({
  teamId,
  divisionId,
  scope = "team",
  onProposalStatusChange,
  onTeamPerformanceUpdate,
  onNotificationReceived,
}: DashboardWithRealtimeProps) {
  const {
    isConnected,
    connectionState,
    messageCount,
    subscribe,
    getProposalStatusUpdates,
  } = useDashboardWs();

  const [recentUpdates, setRecentUpdates] = useState<ProposalStatusData[]>([]);

  useEffect(() => {
    if (!isConnected) return;

    const channels = [
      ...(teamId ? [`team:${teamId}`] : []),
      ...(divisionId ? [`division:${divisionId}`] : []),
      "company:default",
    ];

    for (const channel of channels) {
      subscribe(channel);
    }
  }, [isConnected, teamId, divisionId, subscribe]);

  useEffect(() => {
    const updates = getProposalStatusUpdates();
    if (updates.length > 0) {
      setRecentUpdates(updates.slice(-5));
      const latest = updates[updates.length - 1];
      onProposalStatusChange?.(latest);
    }
  }, [getProposalStatusUpdates, onProposalStatusChange]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 p-2 bg-[#1c1c1c] rounded-lg border border-[#262626]">
        <div
          className={`w-2 h-2 rounded-full transition-colors ${
            isConnected ? "bg-green-500" : "bg-yellow-500"
          }`}
        />
        <span className="text-xs text-[#8c8c8c]">
          {connectionState === "connected"
            ? "실시간 업데이트 활성화"
            : connectionState === "connecting"
              ? "연결 중..."
              : "연결 끊김"}
        </span>
        {messageCount > 0 && (
          <span className="ml-auto text-xs text-[#3ecf8e] font-semibold">
            {messageCount} 업데이트
          </span>
        )}
      </div>

      {recentUpdates.length > 0 && (
        <div className="p-4 bg-[#141414] rounded-lg border border-[#262626] space-y-2">
          <p className="text-xs font-semibold text-[#8c8c8c] uppercase tracking-wider">
            실시간 업데이트
          </p>
          <div className="space-y-1">
            {recentUpdates.map((update) => (
              <div
                key={update.proposal_id}
                className="flex items-center gap-3 p-2 rounded-lg bg-[#1c1c1c] text-xs"
              >
                <div className="w-2 h-2 rounded-full bg-[#3ecf8e] shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-[#ededed] truncate">{update.title}</p>
                  <p className="text-[#5c5c5c]">
                    {update.old_status} → {update.new_status}
                  </p>
                </div>
                <span className="text-[#5c5c5c] text-[10px] shrink-0">
                  방금 전
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="p-4 bg-blue-950/20 rounded-lg border border-blue-900/40 text-xs text-blue-300">
        <p className="font-semibold mb-1">💡 실시간 통합 가이드</p>
        <p className="text-blue-400/80">
          다른 컴포넌트에서도 useDashboardWs 훅을 사용하여 실시간 업데이트를 받을 수
          있습니다.
        </p>
      </div>
    </div>
  );
}
