"use client";

/**
 * Vault Chat Component
 * Displays chat messages and message input for selected conversation
 */

import { useState, useRef, useEffect, ReactNode } from "react";
import { Send, Loader2 } from "lucide-react";
import { ChatMessage } from "@/lib/api";
import { useVaultChatStream } from "@/lib/hooks/useVaultChatStream";

interface VaultChatProps {
  conversationId: string | null;
  userId: string;
}

// frontend/components/VaultChat.tsx 상단에 추가 또는 수정

interface Message {
  id: string;              // id 에러 해결
  role: 'user' | 'assistant'; // role 에러 해결
  content: string;         // content 에러 해결
  sources?: any[];         // sources 에러 해결
  confidence?: number;     // confidence 에러 해결
}

/**
 * Parse citation markers [출처 N] and convert to clickable superscripts
 * Returns JSX with <sup> elements that link to source cards
 */
function parseCitations(text: string): ReactNode {
  // Match [출처 N] pattern where N is a number
  const citationPattern = /\[출처\s+(\d+)\]/g;
  const parts: (string | ReactNode)[] = [];
  let lastIndex = 0;
  let match;

  while ((match = citationPattern.exec(text)) !== null) {
    // Add text before citation
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    // Add citation as clickable superscript
    const sourceNumber = match[1];
    parts.push(
      <sup key={`cite-${lastIndex}-${sourceNumber}`}>
        <button
          onClick={() => scrollToSource(sourceNumber)}
          className="text-[#10a37f] hover:underline cursor-pointer ml-0.5"
          data-testid={`citation-link-${sourceNumber}`}
          aria-label={`출처 ${sourceNumber}로 이동`}
        >
          [{sourceNumber}]
        </button>
      </sup>
    );

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

/**
 * Scroll to source card with given number
 */
function scrollToSource(sourceNumber: string): void {
  const sourceElement = document.getElementById(`source-${sourceNumber}`);
  if (sourceElement) {
    sourceElement.scrollIntoView({ behavior: "smooth", block: "nearest" });
    sourceElement.classList.add("ring-2", "ring-[#10a37f]");
    setTimeout(() => {
      sourceElement.classList.remove("ring-2", "ring-[#10a37f]");
    }, 2000);
  }
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

  const handleRegenerateMessage = async (messageId: string) => {
    if (!conversationId) return;

    const messageIndex = messages.findIndex((m) => m.id === messageId);
    if (messageIndex === -1) return;

    setError(null);

    try {
      const response = await fetch(`/api/vault/messages/${messageId}/regenerate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: conversationId,
          variation: 0.15,
        }),
      });

      if (!response.ok) {
        throw new Error("재생성에 실패했습니다");
      }

      const data = await response.json();

      // Update the message with regenerated response
      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId
            ? {
                ...m,
                content: data.response,
                sources: data.sources || [],
                confidence: data.confidence,
                timestamp: new Date().toISOString(),
              }
            : m
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "오류가 발생했습니다");
    }
  };

  const handleEditMessage = async (messageId: string) => {
    if (!conversationId) return;

    const messageIndex = messages.findIndex((m) => m.id === messageId);
    if (messageIndex === -1 || messages[messageIndex].role !== "user") return;

    const originalContent = messages[messageIndex].content;

    // Prompt for new text
    const newText = prompt("메시지를 편집하세요:", originalContent);
    if (!newText || newText === originalContent) return;

    try {
      // Remove the edited message and all subsequent messages
      setMessages((prev) => prev.slice(0, messageIndex));

      // Resend the message
      await handleSendMessage(newText);
    } catch (err) {
      setError(err instanceof Error ? err.message : "편집 중 오류가 발생했습니다");
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
        try {
          // Design Ref: §6.1 — Capture returned Promise value to avoid stale closure
          // Plan SC: SC-7 — Streaming response time <2s (not 60s timeout)
          const finalStreamState = await streamState.startStream({
            message: messageText,
            conversationId: conversationId,
          });

          // Streaming succeeded - add message from returned stream state (not component state)
          if (finalStreamState.streamingText) {
            setMessages((prev) => [
              ...prev.filter((m) => m.id !== userMessage.id),
              {
                id: `stream-${Date.now()}`,
                role: "assistant",
                content: finalStreamState.streamingText,
                timestamp: new Date().toISOString(),
                sources: finalStreamState.sources || [],
                confidence: finalStreamState.confidence,
              },
            ]);
          }
        } catch (streamErr) {
          setUseStreamingFallback(true);
          // Remove temp assistant message and retry with non-streaming
          setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
          streamState.reset();
          return handleSendMessage(messageText);
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
            className={`flex gap-4 group ${
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
                {message.role === "assistant" ? parseCitations(message.content) : message.content}
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
                      id={`source-${idx + 1}`}
                      className="text-xs bg-[#1a1a1a]/50 p-2 rounded border border-[#404040] transition-all"
                      data-testid="source-item"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
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
                        <div className="flex-shrink-0">
                          <span
                            className="inline-flex items-center justify-center w-5 h-5 bg-[#10a37f] text-white text-xs font-bold rounded-full"
                            data-testid={`source-badge-${idx + 1}`}
                          >
                            {idx + 1}
                          </span>
                        </div>
                      </div>
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

              {/* Hover menu buttons */}
              <div className="flex gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                {message.role === "assistant" && (
                  <button
                    onClick={() => handleRegenerateMessage(message.id!)}
                    disabled={streamState.isStreaming}
                    className="text-xs px-2 py-1 rounded bg-[#10a37f]/20 text-[#10a37f] hover:bg-[#10a37f]/30 disabled:opacity-50"
                    data-testid="regenerate-button"
                    aria-label="응답 재생성"
                  >
                    재생성
                  </button>
                )}
                {message.role === "user" && (
                  <button
                    onClick={() => handleEditMessage(message.id!)}
                    disabled={streamState.isStreaming}
                    className="text-xs px-2 py-1 rounded bg-[#10a37f]/20 text-[#10a37f] hover:bg-[#10a37f]/30 disabled:opacity-50"
                    data-testid="edit-button"
                    aria-label="메시지 편집"
                  >
                    편집
                  </button>
                )}
              </div>
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
