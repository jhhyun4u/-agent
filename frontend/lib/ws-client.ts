/**
 * WebSocket Client — 실시간 대시보드 업데이트
 *
 * Connection management, auto-reconnect, channel subscription, message routing
 * Based on app/services/ws_manager.py + app/api/routes_ws.py
 */

"use client";

export type MessageType =
  | "proposal_status"
  | "monthly_trends"
  | "team_performance"
  | "notification"
  | "heartbeat"
  | "error";

export interface WsMessage {
  type: MessageType;
  channel: string;
  data: Record<string, any>;
  timestamp: string;
}

export interface WsSubscribeMessage {
  action: "subscribe" | "unsubscribe";
  channel: string;
}

export interface ProposalStatusData {
  proposal_id: string;
  old_status: string;
  new_status: string;
  title: string;
  timestamp: string;
}

export interface NotificationData {
  notification_id: string;
  type: string;
  title: string;
  message: string;
  link?: string;
}

export interface TeamPerformanceData {
  team_id: string;
  win_rate: number;
  total_proposals: number;
  won_count: number;
  timestamp: string;
}

export interface WsErrorData {
  code: string;
  message: string;
  details?: string;
}

export type MessageHandler = (message: WsMessage) => void;

export interface WsClientConfig {
  maxReconnectAttempts?: number;
  initialReconnectDelaySeconds?: number;
  maxReconnectDelaySeconds?: number;
  heartbeatIntervalSeconds?: number;
  url?: string;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private token: string | null = null;
  private channels: Set<string> = new Set();
  private messageHandlers: Map<MessageType, MessageHandler[]> = new Map();
  private stateHandlers: ((state: "connecting" | "connected" | "disconnected" | "error") => void)[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts: number;
  private initialReconnectDelay: number;
  private maxReconnectDelay: number;
  private currentReconnectDelay: number;
  private heartbeatInterval: number;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private state: "connecting" | "connected" | "disconnected" | "error" = "disconnected";

  constructor(config: WsClientConfig = {}) {
    this.maxReconnectAttempts = config.maxReconnectAttempts ?? 20;
    this.initialReconnectDelay = (config.initialReconnectDelaySeconds ?? 1) * 1000;
    this.maxReconnectDelay = (config.maxReconnectDelaySeconds ?? 30) * 1000;
    this.currentReconnectDelay = this.initialReconnectDelay;
    this.heartbeatInterval = (config.heartbeatIntervalSeconds ?? 30) * 1000;

    // Determine WebSocket URL from API URL
    if (config.url) {
      this.url = config.url;
    } else {
      const apiUrl = typeof window !== "undefined" ? process.env.NEXT_PUBLIC_API_URL : "";
      if (!apiUrl) {
        throw new Error("NEXT_PUBLIC_API_URL environment variable not set");
      }
      // Convert http://localhost:8000/api to ws://localhost:8000/api/ws/dashboard
      const baseUrl = apiUrl.replace(/\/api\/?$/, "");
      const protocol = baseUrl.startsWith("https") ? "wss" : "ws";
      const host = baseUrl.replace(/^https?:\/\//, "");
      this.url = `${protocol}://${host}/api/ws/dashboard`;
    }
  }

  /**
   * Connect to WebSocket server with JWT token
   */
  async connect(token: string): Promise<void> {
    if (this.state === "connected" || this.state === "connecting") {
      console.warn("[WS] Already connecting or connected");
      return;
    }

    this.token = token;
    this.setState("connecting");

    try {
      const wsUrl = `${this.url}?token=${encodeURIComponent(token)}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log("[WS] Connected");
        this.reconnectAttempts = 0;
        this.currentReconnectDelay = this.initialReconnectDelay;
        this.setState("connected");
        this.startHeartbeat();

        // Re-subscribe to channels
        for (const channel of this.channels) {
          this.sendSubscribe(channel);
        }
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(event.data);
      };

      this.ws.onerror = (event) => {
        console.error("[WS] WebSocket error", event);
        this.setState("error");
      };

      this.ws.onclose = () => {
        console.log("[WS] Disconnected");
        this.stopHeartbeat();
        this.setState("disconnected");

        // Auto-reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error("[WS] Connection error:", error);
      this.setState("error");
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.channels.clear();
    this.setState("disconnected");
  }

  /**
   * Subscribe to a channel
   */
  subscribe(channel: string): void {
    if (!this.channels.has(channel)) {
      this.channels.add(channel);

      if (this.state === "connected") {
        this.sendSubscribe(channel);
      }
    }
  }

  /**
   * Unsubscribe from a channel
   */
  unsubscribe(channel: string): void {
    if (this.channels.has(channel)) {
      this.channels.delete(channel);

      if (this.state === "connected") {
        this.sendUnsubscribe(channel);
      }
    }
  }

  /**
   * Register message handler for a specific type
   */
  on(type: MessageType, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type)!.push(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(type);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      }
    };
  }

  /**
   * Register state change handler
   */
  onStateChange(
    handler: (state: "connecting" | "connected" | "disconnected" | "error") => void
  ): () => void {
    this.stateHandlers.push(handler);

    // Return unsubscribe function
    return () => {
      const index = this.stateHandlers.indexOf(handler);
      if (index > -1) {
        this.stateHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Get current connection state
   */
  getState(): typeof this.state {
    return this.state;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.state === "connected";
  }

  /**
   * Get subscribed channels
   */
  getChannels(): string[] {
    return Array.from(this.channels);
  }

  // ── Private Methods ──

  private sendSubscribe(channel: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message: WsSubscribeMessage = {
        action: "subscribe",
        channel,
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  private sendUnsubscribe(channel: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message: WsSubscribeMessage = {
        action: "unsubscribe",
        channel,
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  private handleMessage(data: string): void {
    try {
      const message: WsMessage = JSON.parse(data);

      // Skip heartbeat messages
      if (message.type === "heartbeat") {
        return;
      }

      // Dispatch to handlers
      const handlers = this.messageHandlers.get(message.type);
      if (handlers) {
        for (const handler of handlers) {
          try {
            handler(message);
          } catch (error) {
            console.error(`[WS] Handler error for ${message.type}:`, error);
          }
        }
      }
    } catch (error) {
      console.error("[WS] Message parse error:", error);
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        // Server sends heartbeat, we just keep the connection alive
        // No action needed on client side
      }
    }, this.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.currentReconnectDelay,
      this.maxReconnectDelay
    );

    console.log(
      `[WS] Reconnecting in ${delay / 1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (this.token) {
        this.connect(this.token).catch((error) => {
          console.error("[WS] Reconnect failed:", error);
        });
      }
    }, delay);

    // Exponential backoff: 1s → 2s → 4s → 8s → ... → 30s max
    this.currentReconnectDelay = Math.min(
      this.currentReconnectDelay * 2,
      this.maxReconnectDelay
    );
  }

  private setState(
    newState: "connecting" | "connected" | "disconnected" | "error"
  ): void {
    if (this.state !== newState) {
      this.state = newState;
      console.log(`[WS] State: ${newState}`);

      for (const handler of this.stateHandlers) {
        try {
          handler(newState);
        } catch (error) {
          console.error("[WS] State handler error:", error);
        }
      }
    }
  }
}

// Singleton instance
let wsClient: WebSocketClient | null = null;

export function getWebSocketClient(config?: WsClientConfig): WebSocketClient {
  if (!wsClient) {
    wsClient = new WebSocketClient(config);
  }
  return wsClient;
}

export function resetWebSocketClient(): void {
  if (wsClient) {
    wsClient.disconnect();
    wsClient = null;
  }
}
