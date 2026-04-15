"use client";

/**
 * useVaultChatStream — SSE 기반 Vault AI Chat 실시간 응답 스트림
 *
 * - POST /api/vault/chat/stream으로 SSE 요청 (EventSource 지원 안 하는 POST이므로 fetch + ReadableStream 사용)
 * - event: sources → 초기 출처 수집 발송
 * - event: token → 토큰 단위 응답 스트림
 * - event: done → 완료 + 최종 메타데이터
 * - event: error → 에러 발생 시
 * - AbortController로 취소 지원
 */

import { useCallback, useRef, useState } from "react";
import { DocumentSource } from "@/lib/api";

export interface VaultStreamState {
  streamingText: string;
  sources: DocumentSource[];
  isStreaming: boolean;
  isComplete: boolean;
  confidence?: number;
  validationPassed?: boolean;
  warnings: string[];
  messageId?: string;
  error?: string;
}

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export function useVaultChatStream() {
  const [state, setState] = useState<VaultStreamState>({
    streamingText: "",
    sources: [],
    isStreaming: false,
    isComplete: false,
    warnings: [],
    error: undefined,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * 스트리밍 시작
   */
  const startStream = useCallback(
    async (params: {
      message: string;
      conversationId: string;
      token?: string;
    }) => {
      // 기존 요청 취소
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      setState({
        streamingText: "",
        sources: [],
        isStreaming: true,
        isComplete: false,
        warnings: [],
        error: undefined,
      });

      try {
        const response = await fetch(`${BASE}/vault/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: params.message,
            conversation_id: params.conversationId,
          }),
          signal: abortController.signal,
        });

        if (!response.ok) {
          throw new Error(
            `HTTP ${response.status}: ${response.statusText}`
          );
        }

        if (!response.body) {
          throw new Error("Response body is null");
        }

        // ReadableStream으로 SSE 파싱
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            // 남은 버퍼가 있으면 처리
            if (buffer.trim()) {
              processLine(buffer);
            }
            break;
          }

          // 청크를 문자열로 변환
          buffer += decoder.decode(value, { stream: true });

          // 라인 단위로 처리
          const lines = buffer.split("\n");
          // 마지막 항목은 불완전할 수 있으므로 버퍼에 유지
          buffer = lines[lines.length - 1] || "";

          for (let i = 0; i < lines.length - 1; i++) {
            const line = lines[i].trim();
            if (line) {
              processLine(line);
            }
          }
        }

        // 취소되지 않았으면 완료 표시
        if (!abortController.signal.aborted) {
          setState((prev) => ({
            ...prev,
            isStreaming: false,
          }));
        }
      } catch (err: unknown) {
        if (
          err instanceof Error &&
          err.name !== "AbortError"
        ) {
          const errorMessage =
            err instanceof Error ? err.message : "Unknown error";
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            isComplete: false,
            error: errorMessage,
          }));
        }
      }
    },
    []
  );

  /**
   * SSE 라인 처리
   */
  const processLine = useCallback((line: string) => {
    try {
      const data = JSON.parse(line);

      if (data.event === "sources") {
        setState((prev) => ({
          ...prev,
          sources: data.sources || [],
        }));
      } else if (data.event === "token") {
        setState((prev) => ({
          ...prev,
          streamingText: prev.streamingText + (data.text || ""),
        }));
      } else if (data.event === "done") {
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          isComplete: true,
          confidence: data.confidence,
          validationPassed: data.validation_passed,
          warnings: data.warnings || [],
          messageId: data.message_id,
        }));
      } else if (data.event === "error") {
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          isComplete: false,
          error: data.message || "Unknown streaming error",
        }));
      }
    } catch {
      // JSON 파싱 실패 무시 (빈 라인 등)
    }
  }, []);

  /**
   * 스트림 리셋
   */
  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    setState({
      streamingText: "",
      sources: [],
      isStreaming: false,
      isComplete: false,
      warnings: [],
      error: undefined,
    });
  }, []);

  /**
   * 스트림 취소
   */
  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setState((prev) => ({
      ...prev,
      isStreaming: false,
    }));
  }, []);

  return {
    ...state,
    startStream,
    reset,
    cancel,
  };
}
