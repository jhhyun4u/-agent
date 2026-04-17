import { create } from "zustand";
import { subscribeWithSelector } from "zustand/react";
import { WebSocketClient } from "@/lib/ws-client";
import type {
  ProposalStatusData,
  NotificationData,
  TeamPerformanceData,
  MessageType,
} from "@/lib/ws-client";

interface DashboardWsState {
  connectionState: "connecting" | "connected" | "disconnected" | "error";
  subscribedChannels: string[];
  proposalStatusMessages: ProposalStatusData[];
  notificationMessages: NotificationData[];
  teamPerformanceMessages: TeamPerformanceData[];
  error: Error | null;

  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
  addMessage: (type: MessageType, data: any) => void;
  clearMessages: (type?: MessageType) => void;
  getProposalStatusCount: () => number;
  getNotificationCount: () => number;
  getTeamPerformanceCount: () => number;
  getLatestProposalStatus: () => ProposalStatusData | null;
  getProposalStatusUpdates: () => ProposalStatusData[];
  getLatestNotification: () => NotificationData | null;
  getNotifications: () => NotificationData[];
  getLatestTeamPerformance: () => TeamPerformanceData | null;

  _initialize: (token: string) => Promise<void>;
  _disconnect: () => void;
}

const MAX_STORED_MESSAGES = 50;

export const useDashboardWsStore = create<DashboardWsState>()(
  subscribeWithSelector((set, get) => ({
    connectionState: "disconnected",
    subscribedChannels: [],
    proposalStatusMessages: [],
    notificationMessages: [],
    teamPerformanceMessages: [],
    error: null,

    subscribe: (channel: string) => {
      const state = get();
      if (state.subscribedChannels.includes(channel)) return;
      set({
        subscribedChannels: [...state.subscribedChannels, channel],
      });
    },

    unsubscribe: (channel: string) => {
      const state = get();
      set({
        subscribedChannels: state.subscribedChannels.filter(
          (c) => c !== channel
        ),
      });
    },

    addMessage: (type: MessageType, data: any) => {
      const state = get();
      const key =
        type === "proposal_status"
          ? "proposalStatusMessages"
          : type === "notification"
            ? "notificationMessages"
            : type === "team_performance"
              ? "teamPerformanceMessages"
              : null;

      if (!key) return;

      set({
        [key]: [
          data,
          ...((state as any)[key] || []),
        ].slice(0, MAX_STORED_MESSAGES),
      });
    },

    clearMessages: (type?: MessageType) => {
      if (type === "proposal_status") {
        set({ proposalStatusMessages: [] });
      } else if (type === "notification") {
        set({ notificationMessages: [] });
      } else if (type === "team_performance") {
        set({ teamPerformanceMessages: [] });
      } else {
        set({
          proposalStatusMessages: [],
          notificationMessages: [],
          teamPerformanceMessages: [],
        });
      }
    },

    getProposalStatusCount: () => get().proposalStatusMessages.length,
    getNotificationCount: () => get().notificationMessages.length,
    getTeamPerformanceCount: () => get().teamPerformanceMessages.length,

    getLatestProposalStatus: () => {
      const msgs = get().proposalStatusMessages;
      return msgs.length > 0 ? msgs[0] : null;
    },

    getProposalStatusUpdates: () => get().proposalStatusMessages,

    getLatestNotification: () => {
      const msgs = get().notificationMessages;
      return msgs.length > 0 ? msgs[0] : null;
    },

    getNotifications: () => get().notificationMessages,

    getLatestTeamPerformance: () => {
      const msgs = get().teamPerformanceMessages;
      return msgs.length > 0 ? msgs[0] : null;
    },

    _initialize: async (token: string) => {
      set({ connectionState: "connecting" });
      try {
        const client = WebSocketClient.getInstance();
        await client.connect(token);
        set({ connectionState: "connected", error: null });

        client.on("proposal_status", (data) => {
          get().addMessage("proposal_status", data);
        });

        client.on("notification", (data) => {
          get().addMessage("notification", data);
        });

        client.on("team_performance", (data) => {
          get().addMessage("team_performance", data);
        });

        client.onStateChange((state) => {
          set({ connectionState: state });
        });
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));
        set({ connectionState: "error", error: err });
        throw err;
      }
    },

    _disconnect: () => {
      try {
        const client = WebSocketClient.getInstance();
        client.disconnect();
      } catch (error) {
        console.error("[dashboardWsStore] Disconnect error:", error);
      }
      set({ connectionState: "disconnected" });
    },
  }))
);

export const selectIsConnected = (state: DashboardWsState) =>
  state.connectionState === "connected";
export const selectConnectionState = (state: DashboardWsState) =>
  state.connectionState;
export const selectChannels = (state: DashboardWsState) =>
  state.subscribedChannels;
export const selectProposalStatusMessages = (state: DashboardWsState) =>
  state.proposalStatusMessages;
export const selectNotificationMessages = (state: DashboardWsState) =>
  state.notificationMessages;
export const selectTeamPerformanceMessages = (state: DashboardWsState) =>
  state.teamPerformanceMessages;
