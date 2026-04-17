"use client";

import { useEffect, useCallback, useRef } from "react";
import { useAuth } from "@/lib/hooks/useAuth";
import {
  useDashboardWsStore,
  selectIsConnected,
  selectConnectionState,
  selectChannels,
  selectProposalStatusMessages,
  selectNotificationMessages,
} from "@/lib/stores/dashboardWsStore";
import type { MessageType } from "@/lib/ws-client";

export interface UseDashboardWsReturn {
  isConnected: boolean;
  connectionState: "connecting" | "connected" | "disconnected" | "error";
  channels: string[];
  messageCount: number;
  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
  unsubscribeAll: () => void;
  getLatestProposalStatus: () => any;
  getProposalStatusUpdates: () => any[];
  getLatestNotification: () => any;
  getNotifications: () => any[];
  getLatestTeamPerformance: () => any;
  clearMessages: (type?: MessageType) => void;
  reconnect: () => Promise<void>;
  disconnect: () => void;
  isInitialized: boolean;
  error: Error | null;
}

export function useDashboardWs(): UseDashboardWsReturn {
  const { user, token } = useAuth();
  const isInitializedRef = useRef(false);
  const errorRef = useRef<Error | null>(null);

  const isConnected = useDashboardWsStore(selectIsConnected);
  const connectionState = useDashboardWsStore(selectConnectionState);
  const channels = useDashboardWsStore(selectChannels);
  const proposalMessages = useDashboardWsStore(selectProposalStatusMessages);
  const notificationMessages = useDashboardWsStore(selectNotificationMessages);

  const storeSubscribe = useDashboardWsStore((s) => s.subscribe);
  const storeUnsubscribe = useDashboardWsStore((s) => s.unsubscribe);
  const storeGetLatestProposalStatus = useDashboardWsStore(
    (s) => s.getLatestProposalStatus
  );
  const storeGetProposalStatusUpdates = useDashboardWsStore(
    (s) => s.getProposalStatusUpdates
  );
  const storeGetLatestNotification = useDashboardWsStore(
    (s) => s.getLatestNotification
  );
  const storeGetNotifications = useDashboardWsStore((s) => s.getNotifications);
  const storeGetLatestTeamPerformance = useDashboardWsStore(
    (s) => s.getLatestTeamPerformance
  );
  const storeClearMessages = useDashboardWsStore((s) => s.clearMessages);
  const storeDisconnect = useDashboardWsStore((s) => s._disconnect);
  const storeInitialize = useDashboardWsStore((s) => s._initialize);

  useEffect(() => {
    const initialize = async () => {
      try {
        if (isInitializedRef.current) return;
        if (!user || !token) return;

        isInitializedRef.current = true;
        await storeInitialize(token);
        errorRef.current = null;
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));
        errorRef.current = err;
        isInitializedRef.current = false;
      }
    };

    initialize();

    return () => {
      storeDisconnect();
      isInitializedRef.current = false;
    };
  }, [user, token, storeInitialize, storeDisconnect]);

  const subscribe = useCallback(
    (channel: string) => {
      if (!isConnected && connectionState !== "connecting") return;
      storeSubscribe(channel);
    },
    [isConnected, connectionState, storeSubscribe]
  );

  const unsubscribe = useCallback(
    (channel: string) => {
      storeUnsubscribe(channel);
    },
    [storeUnsubscribe]
  );

  const unsubscribeAll = useCallback(() => {
    for (const channel of channels) {
      storeUnsubscribe(channel);
    }
  }, [channels, storeUnsubscribe]);

  const reconnect = useCallback(async () => {
    try {
      if (!token) throw new Error("Token not available");
      await storeInitialize(token);
      errorRef.current = null;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      errorRef.current = err;
      throw err;
    }
  }, [token, storeInitialize]);

  const disconnect = useCallback(() => {
    storeDisconnect();
    isInitializedRef.current = false;
  }, [storeDisconnect]);

  const clearMessages = useCallback(
    (type?: MessageType) => {
      storeClearMessages(type);
    },
    [storeClearMessages]
  );

  const messageCount = proposalMessages.length + notificationMessages.length;

  return {
    isConnected,
    connectionState,
    channels,
    messageCount,
    subscribe,
    unsubscribe,
    unsubscribeAll,
    getLatestProposalStatus: storeGetLatestProposalStatus,
    getProposalStatusUpdates: storeGetProposalStatusUpdates,
    getLatestNotification: storeGetLatestNotification,
    getNotifications: storeGetNotifications,
    getLatestTeamPerformance: storeGetLatestTeamPerformance,
    clearMessages,
    reconnect,
    disconnect,
    isInitialized: isInitializedRef.current,
    error: errorRef.current,
  };
}

export function useDashboardWsSelector<T>(
  selector: (state: any) => T
): T {
  return useDashboardWsStore(selector);
}
