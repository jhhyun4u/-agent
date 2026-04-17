export type MessageType =
  | "proposal_status"
  | "monthly_trends"
  | "team_performance"
  | "notification"
  | "heartbeat"
  | "error";

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

type ConnectionState = "connecting" | "connected" | "disconnected" | "error";
type MessageHandler = (data: any) => void;
type StateChangeHandler = (state: ConnectionState) => void;

export class WebSocketClient {
  private static instance: WebSocketClient;
  private ws: WebSocket | null = null;
  private url: string;
  private state: ConnectionState = "disconnected";
  private messageHandlers: Map<MessageType, MessageHandler[]> = new Map();
  private stateChangeHandlers: StateChangeHandler[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;

  private constructor() {
    const apiUrl =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    this.url = apiUrl.replace(/^http/, "ws") + "/ws/dashboard";
  }

  static getInstance(): WebSocketClient {
    if (!WebSocketClient.instance) {
      WebSocketClient.instance = new WebSocketClient();
    }
    return WebSocketClient.instance;
  }

  async connect(token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        if (this.ws?.readyState === WebSocket.OPEN) {
          resolve();
          return;
        }

        this.setState("connecting");
        this.ws = new WebSocket(`${this.url}?token=${token}`);

        this.ws.onopen = () => {
          this.reconnectAttempts = 0;
          this.setState("connected");
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onerror = () => {
          this.setState("error");
          reject(new Error("WebSocket connection error"));
        };

        this.ws.onclose = () => {
          this.setState("disconnected");
          this.stopHeartbeat();
          this.attemptReconnect(token);
        };
      } catch (error) {
        this.setState("error");
        reject(error);
      }
    });
  }

  private handleMessage(data: string) {
    try {
      const message = JSON.parse(data);
      const type = message.type as MessageType;
      const handlers = this.messageHandlers.get(type) || [];

      for (const handler of handlers) {
        handler(message.data || message);
      }
    } catch (error) {
      console.error("[WebSocketClient] Message parse error:", error);
    }
  }

  private attemptReconnect(token: string) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.setState("error");
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;

    this.reconnectTimer = setTimeout(() => {
      this.connect(token).catch(() => {
        // Retry will be triggered by onclose
      });
    }, delay);
  }

  private startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "heartbeat" }));
      }
    }, 30000);
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private setState(newState: ConnectionState) {
    if (this.state === newState) return;
    this.state = newState;
    for (const handler of this.stateChangeHandlers) {
      handler(newState);
    }
  }

  subscribe(channel: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: "subscribe", channel }));
    }
  }

  unsubscribe(channel: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: "unsubscribe", channel }));
    }
  }

  on(type: MessageType, handler: MessageHandler): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type)!.push(handler);
  }

  onStateChange(handler: StateChangeHandler): void {
    this.stateChangeHandlers.push(handler);
  }

  disconnect(): void {
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.setState("disconnected");
  }

  getState(): ConnectionState {
    return this.state;
  }

  isConnected(): boolean {
    return this.state === "connected";
  }
}
