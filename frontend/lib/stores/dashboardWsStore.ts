/**
 * Dashboard WebSocket Store — Zustand 상태 관리
 *
 * 실시간 업데이트 메시지, 연결 상태, 구독 채널, 통계 관리
 * 컴포넌트 최적화 재렌더링 위한 selector 제공
 */

"use client";

import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import {
  getWebSocketClient,
  MessageType,
  WsMessage,
  ProposalStatusData,
  NotificationData,
  TeamPerformanceData,
} from "@/lib/ws-client";

// ── Message Storage Types ──
export interface StoredMessage {
  message: WsMessage;
  receivedAt: number; // timestamp ms
}

// Limit recent messages per type to avoid memory bloat
const MAX_STORED_MESSAGES_PER_TYPE = 50;

// ── Connection Stats ──
export interface ConnectionStats {
  connectedAt: number | null; // timestamp ms
  disconnectedAt: number | null;
  reconnectAttempts: number;
  totalMessagesReceived: number;
  lastMessageAt: number | null;
}

// ── Store State ──
export interface DashboardWsStoreState {
  // Connection state
  connectionState: "connecting" | "connected" | "disconnected" | "error";
  isConnected: boolean;

  // Channels
  subscribedChannels: string[];

  // Recent messages by type
  recentMessages: {
    proposal_status: StoredMessage[];
    monthly_trends: StoredMessage[];
    team_performance: StoredMessage[];
    notification: StoredMessage[];
  };

  // Connection stats
  stats: ConnectionStats;

  // Typed getters for specific message types
  getLatestProposalStatus: () => ProposalStatusData | null;
  getLatestTeamPerformance: () => TeamPerformanceData | null;
  getLatestNotification: () => NotificationData | null;
  getProposalStatusUpdates: () => ProposalStatusData[];
  getNotifications: () => NotificationData[];

  // Channel management
  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
  getChannels: () => string[];

  // Message management
  clearMessages: (type?: MessageType) => void;
  getMessageCount: (type?: MessageType) => number;

  // Connection stats
  getStats: () => ConnectionStats;
  resetStats: () => void;

  // Internal: Called by hook/component during setup
  _initialize: (token: string) => Promise<void>;
  _disconnect: () => void;
  _addMessage: (message: WsMessage) => void;
  _setConnectionState: (state: "connecting" | "connected" | "disconnected" | "error") => void;
  _incrementReconnectAttempts: () => void;
}

/**
 * Zustand store with selector middleware for optimized re-renders
 */
export const useDashboardWsStore = create<DashboardWsStoreState>()(
  subscribeWithSelector((set, get) => ({
    // ── Initial State ──
    connectionState: "disconnected",
    isConnected: false,
    subscribedChannels: [],
    recentMessages: {
      proposal_status: [],
      monthly_trends: [],
      team_performance: [],
      notification: [],
    },
    stats: {
      connectedAt: null,
      disconnectedAt: null,
      reconnectAttempts: 0,
      totalMessagesReceived: 0,
      lastMessageAt: null,
    },

    // ── Typed Message Getters ──
    getLatestProposalStatus: () => {
      const messages = get().recentMessages.proposal_status;
      if (messages.length === 0) return null;
      return (messages[messages.length - 1].message.data as ProposalStatusData) ?? null;
    },

    getLatestTeamPerformance: () => {
      const messages = get().recentMessages.team_performance;
      if (messages.length === 0) return null;
      return (messages[messages.length - 1].message.data as TeamPerformanceData) ?? null;
    },

    getLatestNotification: () => {
      const messages = get().recentMessages.notification;
      if (messages.length === 0) return null;
      return (messages[messages.length - 1].message.data as NotificationData) ?? null;
    },

    getProposalStatusUpdates: () => {
      return get().recentMessages.proposal_status.map(
        (m) => m.message.data as ProposalStatusData
      );
    },

    getNotifications: () => {
      return get().recentMessages.notification.map(
        (m) => m.message.data as NotificationData
      );
    },

    // ── Channel Management ──
    subscribe: (channel: string) => {
      const client = getWebSocketClient();
      client.subscribe(channel);

      set((state) => {
        if (!state.subscribedChannels.includes(channel)) {
          return {
            subscribedChannels: [...state.subscribedChannels, channel],
          };
        }
        return state;
      });
    },

    unsubscribe: (channel: string) => {
      const client = getWebSocketClient();
      client.unsubscribe(channel);

      set((state) => ({
        subscribedChannels: state.subscribedChannels.filter((c) => c !== channel),
      }));
    },

    getChannels: () => {
      return get().subscribedChannels;
    },

    // ── Message Management ──
    clearMessages: (type?: MessageType) => {
      set((state) => {
        if (type) {
          // Clear messages for specific type
          const types: Array<keyof typeof state.recentMessages> = [\n            "proposal_status",
            "monthly_trends",
            "team_performance",
            "notification",
          ];\n          if (types.includes(type as any)) {
            return {
              recentMessages: {
                ...state.recentMessages,
                [type]: [],
              },
            };
          }
          return state;
        } else {
          // Clear all messages
          return {
            recentMessages: {
              proposal_status: [],
              monthly_trends: [],
              team_performance: [],
              notification: [],
            },
          };
        }
      });
    },

    getMessageCount: (type?: MessageType) => {
      const state = get();
      if (type) {
        const types: Array<keyof typeof state.recentMessages> = [
          "proposal_status",
          "monthly_trends",
          "team_performance",
          "notification",
        ];
        if (types.includes(type as any)) {
          return state.recentMessages[type as any].length;
        }
        return 0;
      } else {
        // Total count across all types
        return Object.values(state.recentMessages).reduce(
          (sum, msgs) => sum + msgs.length,
          0
        );
      }
    },

    // ── Connection Stats ──
    getStats: () => {
      return get().stats;
    },

    resetStats: () => {
      set({
        stats: {
          connectedAt: null,
          disconnectedAt: null,
          reconnectAttempts: 0,
          totalMessagesReceived: 0,
          lastMessageAt: null,
        },
      });
    },

    // ── Internal Methods (Called by useDashboardWs hook) ──

    _initialize: async (token: string) => {
      const client = getWebSocketClient();

      // Listen to state changes
      client.onStateChange((state) => {
        get()._setConnectionState(state);
      });

      // Listen to messages
      client.on("proposal_status", (msg) => {
        get()._addMessage(msg);
      });

      client.on("monthly_trends", (msg) => {
        get()._addMessage(msg);
      });

      client.on("team_performance", (msg) => {
        get()._addMessage(msg);
      });

      client.on("notification", (msg) => {
        get()._addMessage(msg);
      });

      // Connect
      await client.connect(token);

      // Update initial connected state
      if (client.isConnected()) {
        set({
          connectionState: "connected",
          isConnected: true,
          stats: {
            connectedAt: Date.now(),
            disconnectedAt: null,
            reconnectAttempts: 0,
            totalMessagesReceived: 0,
            lastMessageAt: null,
          },
        });
      }
    },

    _disconnect: () => {
      const client = getWebSocketClient();
      client.disconnect();

      set({
        connectionState: "disconnected",
        isConnected: false,
        subscribedChannels: [],
        stats: {
          connectedAt: null,
          disconnectedAt: Date.now(),
          reconnectAttempts: 0,
          totalMessagesReceived: 0,
          lastMessageAt: null,
        },
      });
    },

    _addMessage: (message: WsMessage) => {
      set((state) => {
        const messageType = message.type as keyof typeof state.recentMessages;

        if (!state.recentMessages[messageType]) {
          return state;
        }

        const stored: StoredMessage = {
          message,
          receivedAt: Date.now(),
        };

        const updated = [
          ...state.recentMessages[messageType],
          stored,
        ];

        // Keep only the most recent MAX_STORED_MESSAGES_PER_TYPE
        if (updated.length > MAX_STORED_MESSAGES_PER_TYPE) {
          updated.shift();
        }

        return {
          recentMessages: {
            ...state.recentMessages,
            [messageType]: updated,
          },
          stats: {
            ...state.stats,
            totalMessagesReceived: state.stats.totalMessagesReceived + 1,
            lastMessageAt: Date.now(),
          },
        };
      });
    },

    _setConnectionState: (state: "connecting" | "connected" | "disconnected" | "error") => {
      set({
        connectionState: state,
        isConnected: state === "connected",
        stats: {
          connectedAt: state === "connected" ? Date.now() : get().stats.connectedAt,
          disconnectedAt: state === "disconnected" ? Date.now() : get().stats.disconnectedAt,
          reconnectAttempts:
            state === "disconnected"
              ? get().stats.reconnectAttempts + 1
              : get().stats.reconnectAttempts,
          totalMessagesReceived: get().stats.totalMessagesReceived,
          lastMessageAt: get().stats.lastMessageAt,
        },
      });
    },

    _incrementReconnectAttempts: () => {
      set((state) => ({
        stats: {
          ...state.stats,
          reconnectAttempts: state.stats.reconnectAttempts + 1,
        },
      }));
    },
  }))
);

// ── Optimized Selectors for Component Re-renders ──

/**
 * Select only connection state (true/false)
 * Use in components that only care about connected/disconnected
 */
export const selectIsConnected = (state: DashboardWsStoreState) => state.isConnected;

/**
 * Select connection state enum (connecting/connected/disconnected/error)
 */
export const selectConnectionState = (state: DashboardWsStoreState) => state.connectionState;

/**
 * Select subscribed channels
 */
export const selectChannels = (state: DashboardWsStoreState) => state.subscribedChannels;

/**
 * Select only proposal status messages (for proposal list updates)
 */
export const selectProposalStatusMessages = (state: DashboardWsStoreState) =>
  state.recentMessages.proposal_status;

/**
 * Select only notification messages (for notification bell)
 */
export const selectNotificationMessages = (state: DashboardWsStoreState) =>
  state.recentMessages.notification;

/**
 * Select only team performance messages (for dashboard cards)
 */
export const selectTeamPerformanceMessages = (state: DashboardWsStoreState) =>
  state.recentMessages.team_performance;

/**
 * Select connection stats (for debug/monitoring)
 */
export const selectStats = (state: DashboardWsStoreState) => state.stats;

/**
 * Select message counts for UI indicators
 */
export const selectMessageCounts = (state: DashboardWsStoreState) => ({
  proposals: state.recentMessages.proposal_status.length,
  notifications: state.recentMessages.notification.length,
  teamPerformance: state.recentMessages.team_performance.length,
  total: Object.values(state.recentMessages).reduce((sum, msgs) => sum + msgs.length, 0),
});
