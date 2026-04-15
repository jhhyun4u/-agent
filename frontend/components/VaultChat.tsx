"use client";

/**
 * Vault Chat Component
 * Displays chat messages and message input for selected conversation
 */

import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { ChatMessage } from "@/lib/api";
import { useVaultChatStream } from "@/lib/hooks/useVaultChatStream";

interface VaultChatProps {
  conversationId: string | null;
  userId: string;
}

interface Message extends ChatMessage {
  timestamp?: string;
}

export default function VaultChat({ conversationId, userId }: VaultChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamState = useVaultChatStream();
  const [useStreamingFallback, setUseStreamingFallback] = useState(false);

  // Load messages when conversation changes
  useEffect(() => {
    if (conversationId) {
      loadMessages(conversationId);
    } else {
      setMessages([]);
    }
  }, [conversationId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadMessages = async (convId: string) => {
    try {
      const response = await fetch(
        `/api/vault/conversations/${convId}/messages`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error("메시지를 불러올 수 없습니다");
      }

      const data = await response.json();
      setMessages(data);
      setError(null);
    } catch (err) {
      console.error("Error loading messages:", err);
      setError(err instanceof Error ? err.message : "오류가 발생했습니다");
    }
  };

  const handleSendMessage = async (messageTextOverride?: string) => {
    const messageText = messageTextOverride || inputValue.trim();

    if (!messageText || !conversationId) {
      return;
    }

    if (streamState.isStreaming) {
      return;
    }

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: messageText,
      timestamp: new Date().toISOString(),
    };

    try {
      // Only clear input if not a fallback attempt
      if (!messageTextOverride) {
        setInputValue("");
        setMessages((prev) => [...prev, userMessage]);
      }
      setError(null);

      // Try streaming first
      if (!useStreamingFallback) {
        await streamState.startStream({
          message: messageText,
          conversationId: conversationId,
        });

        // Wait for streaming to complete
        let streamComplete = false;
        const maxWait = 60000; // 60 seconds max
        const startTime = Date.now();

        while (!streamComplete && Date.now() - startTime < maxWait) {
          await new Promise((resolve) => setTimeout(resolve, 100));
          if (streamState.isComplete || streamState.error) {
            streamComplete = true;
          }
        }

        // Check if streaming failed
        if (streamState.error) {
          console.warn("Streaming failed, falling back to non-streaming:", streamState.error);
          setUseStreamingFallback(true);
          // Remove temp assistant message and retry with non-streaming
          setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
          streamState.reset();
          return handleSendMessage(messageText);
        }

        // Streaming succeeded - add message from stream state
        if (streamState.streamingText) {
          setMessages((prev) => [
            ...prev.filter((m) => m.id !== userMessage.id),
            {
              id: `stream-${Date.now()}`,
              role: "assistant",
              content: streamState.streamingText,
              timestamp: new Date().toISOString(),
              sources: streamState.sources || [],
              confidence: streamState.confidence,
            },
          ]);
        }
      } else {
        // Use non-streaming fallback
        const response = await fetch("/api/vault/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            conversation_id: conversationId,
            message: messageText,
            user_id: userId,
          }),
        });

        if (!response.ok) {
          throw new Error("메시지 전송에 실패했습니다");
        }

        const data = await response.json();

        setMessages((prev) => [
          ...prev.filter((m) => m.id !== userMessage.id),
          {
            id: data.message_id,
            role: "assistant",
            content: data.response,
            timestamp: new Date().toISOString(),
            sources: data.sources || [],
            confidence: data.confidence,
          },
        ]);
      }
    } catch (err) {
      console.error("Error sending message:", err);
      setError(err instanceof Error ? err.message : "오류가 발생했습니다");
      // Remove temporary message on error
      setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
    } finally {
      streamState.reset();
    }
  };

  if (!conversationId) {
    return (
      <div className="flex-1 flex items-center justify-center text-[#b4b4b4]">
        <div className="text-center space-y-4">
          <div className="text-lg font-medium">채팅을 시작하려면</div>
          <div className="text-sm">좌측에서 채팅을 선택하거나 새로 만드세요</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[#1a1a1a]" data-testid="chat-container">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" data-testid="messages-area">
        {(error || streamState.error) && (
          <div
            className="px-4 py-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg"
            data-testid="error-notification"
          >
            {error || streamState.error}
          </div>
        )}

        {messages.length === 0 && !streamState.isStreaming && (
          <div className="flex items-center justify-center h-full text-[#b4b4b4]">
            <div className="text-center space-y-4">
              <div className="text-lg font-medium">대화를 시작하세요</div>
              <div className="text-sm max-w-sm">
                질문을 입력하면 조직의 지식 기반에서 관련 정보를 검색하여 답변합니다
              </div>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-4 ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
            data-testid="chat-message"
          >
            <div
              className={`max-w-md px-4 py-3 rounded-lg ${
                message.role === "user"
                  ? "bg-[#10a37f] text-white"
                  : "bg-[#2d2d2d] text-[#e5e5e5]"
              }`}
              data-testid={message.role === "user" ? "message-user" : "message-assistant"}
            >
              <div className="text-sm whitespace-pre-wrap" data-testid="message-content">
                {message.content}
              </div>

              {/* Sources */}
              {message.sources && message.sources.length > 0 && (
                <div
                  className="mt-3 pt-3 border-t border-[#404040] space-y-2"
                  data-testid="message-sources"
                >
                  <div className="text-xs font-medium text-[#b4b4b4]">
                    출처:
                  </div>
                  {message.sources.map((source, idx) => (
                    <div
                      key={idx}
                      className="text-xs bg-[#1a1a1a]/50 p-2 rounded border border-[#404040]"
                      data-testid="source-item"
                    >
                      <div className="font-medium text-[#10a37f]" data-testid="source-title">
                        {source.section}
                      </div>
                      <div className="text-[#b4b4b4] mt-1 truncate">
                        {source.snippet || ""}
                      </div>
                      {source.confidence !== undefined && (
                        <div className="text-[#888888] mt-1" data-testid="relevance-score">
                          신뢰도: {Math.round(source.confidence * 100)}%
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {message.timestamp && (
                <div className="text-xs text-[#888888] mt-2">
                  {new Date(message.timestamp).toLocaleTimeString("ko-KR")}
                </div>
              )}

              {message.confidence !== undefined && (
                <div className="text-xs text-[#888888] mt-1" data-testid="confidence-score">
                  신뢰도: {Math.round(message.confidence * 100)}%
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Streaming assistant response in progress */}
        {streamState.isStreaming && (
          <div className="flex gap-4 justify-start" data-testid="chat-message">
            <div
              className="max-w-md px-4 py-3 rounded-lg bg-[#2d2d2d] text-[#e5e5e5]"
              data-testid="message-assistant"
            >
              <div className="text-sm whitespace-pre-wrap" data-testid="message-content">
                {streamState.streamingText}
                <span className="animate-pulse">│</span>
              </div>

              {/* Sources during streaming */}
              {streamState.sources && streamState.sources.length > 0 && (
                <div
                  className="mt-3 pt-3 border-t border-[#404040] space-y-2"
                  data-testid="message-sources"
                >
                  <div className="text-xs font-medium text-[#b4b4b4]">
                    출처:
                  </div>
                  {streamState.sources.map((source, idx) => (
                    <div
                      key={idx}
                      className="text-xs bg-[#1a1a1a]/50 p-2 rounded border border-[#404040]"
                      data-testid="source-item"
                    >
                      <div className="font-medium text-[#10a37f]" data-testid="source-title">
                        {source.section}
                      </div>
                      <div className="text-[#b4b4b4] mt-1 truncate">
                        {source.snippet || ""}
                      </div>
                      {source.confidence !== undefined && (
                        <div className="text-[#888888] mt-1" data-testid="relevance-score">
                          신뢰도: {Math.round(source.confidence * 100)}%
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Legacy loading spinner for non-streaming */}
        {!streamState.isStreaming &&
          messages.length > 0 &&
          messages[messages.length - 1]?.role === "user" &&
          !streamState.streamingText && (
            <div
              className="flex gap-4 justify-start"
              data-testid="chat-loading"
            >
              <div className="bg-[#2d2d2d] px-4 py-3 rounded-lg">
                <Loader2 className="w-5 h-5 text-[#10a37f] animate-spin" />
              </div>
            </div>
          )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-[#404040] p-4 bg-[#0d0d0d]">
        <div className="flex gap-3">
          <input
            type="text"
            placeholder="질문을 입력하세요..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            disabled={streamState.isStreaming}
            data-testid="chat-input"
            className="flex-1 px-4 py-3 bg-[#2d2d2d] border border-[#404040] text-white rounded-lg focus:outline-none focus:border-[#10a37f] disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={!inputValue.trim() || streamState.isStreaming}
            data-testid="send-button"
            className="px-4 py-3 bg-[#10a37f] hover:bg-[#1a9970] text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
