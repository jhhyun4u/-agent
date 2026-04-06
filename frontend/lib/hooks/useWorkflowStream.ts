"use client";

/**
 * useWorkflowStream — SSE 기반 워크플로 실시간 노드 진행 스트림
 *
 * - GET /proposals/{id}/stream SSE 연결
 * - on_chain_start → 노드 시작
 * - on_chain_end → 노드 완료 + 산출물 요약
 * - SSE 끊김 시 자동 재연결 (3초)
 */

import { useCallback, useEffect, useRef, useState } from "react";

export interface StreamEvent {
  timestamp: string;
  event: string; // on_chain_start | on_chain_end | done | error
  name: string; // 노드명
  current_step?: string;
  output_summary?: string; // on_chain_end 시 산출물 1줄 요약
  message?: string;
}

export interface NodeProgress {
  node: string;
  status: "running" | "completed" | "error";
  startedAt: string;
  completedAt?: string;
}

interface UseWorkflowStreamResult {
  events: StreamEvent[];
  nodeProgress: Map<string, NodeProgress>;
  isStreaming: boolean;
  currentNode: string;
}

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
const MAX_EVENTS = 200;
const RECONNECT_MS = 3000;

export function useWorkflowStream(
  proposalId: string,
  enabled: boolean,
): UseWorkflowStreamResult {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [nodeProgress, setNodeProgress] = useState<Map<string, NodeProgress>>(
    new Map(),
  );
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentNode, setCurrentNode] = useState("");
  const esRef = useRef<EventSource | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (!proposalId || !enabled) return;
    if (esRef.current) {
      esRef.current.close();
    }

    const url = `${BASE}/proposals/${proposalId}/stream`;
    const es = new EventSource(url);
    esRef.current = es;
    setIsStreaming(true);

    es.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data) as StreamEvent;
        const now = new Date().toISOString();
        const evt: StreamEvent = { ...data, timestamp: data.timestamp || now };

        // 이벤트 추가 (최대 200개)
        setEvents((prev) => {
          const next = [...prev, evt];
          return next.length > MAX_EVENTS ? next.slice(-MAX_EVENTS) : next;
        });

        // 노드 진행 업데이트
        if (data.event === "on_chain_start" && data.name) {
          setCurrentNode(data.name);
          setNodeProgress((prev) => {
            const next = new Map(prev);
            next.set(data.name, {
              node: data.name,
              status: "running",
              startedAt: now,
            });
            return next;
          });
        } else if (data.event === "on_chain_end" && data.name) {
          setNodeProgress((prev) => {
            const next = new Map(prev);
            const existing = next.get(data.name);
            next.set(data.name, {
              node: data.name,
              status: "completed",
              startedAt: existing?.startedAt || now,
              completedAt: now,
            });
            return next;
          });
        } else if (data.event === "error") {
          setCurrentNode("");
        } else if (data.event === "done") {
          setIsStreaming(false);
          setCurrentNode("");
          es.close();
        }
      } catch {
        // JSON 파싱 실패 무시
      }
    };

    es.onerror = () => {
      es.close();
      setIsStreaming(false);
      // 자동 재연결
      if (enabled) {
        reconnectRef.current = setTimeout(connect, RECONNECT_MS);
      }
    };
  }, [proposalId, enabled]);

  useEffect(() => {
    if (enabled) {
      connect();
    }
    return () => {
      if (esRef.current) esRef.current.close();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      setIsStreaming(false);
    };
  }, [connect, enabled]);

  return { events, nodeProgress, isStreaming, currentNode };
}
