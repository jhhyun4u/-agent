"use client";

/**
 * Vault Sidebar Navigation
 * Displays conversation list and allows conversation management
 */

import { useState } from "react";
import { Plus, Trash2, MessageSquare } from "lucide-react";
import { Conversation } from "./VaultLayout";

interface VaultSidebarProps {
  conversations: Conversation[];
  selectedConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onCreateConversation: (title?: string) => void;
  onDeleteConversation: (id: string) => void;
  isLoading: boolean;
}

export default function VaultSidebar({
  conversations,
  selectedConversationId,
  onSelectConversation,
  onCreateConversation,
  onDeleteConversation,
  isLoading,
}: VaultSidebarProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [newConversationTitle, setNewConversationTitle] = useState("");

  const handleCreateClick = async () => {
    if (isCreating && newConversationTitle.trim()) {
      await onCreateConversation(newConversationTitle);
      setNewConversationTitle("");
      setIsCreating(false);
    } else {
      setIsCreating(true);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return date.toLocaleTimeString("ko-KR", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else if (date.toDateString() === yesterday.toDateString()) {
      return "어제";
    } else if (date.getFullYear() === today.getFullYear()) {
      return date.toLocaleDateString("ko-KR", {
        month: "short",
        day: "numeric",
      });
    } else {
      return date.toLocaleDateString("ko-KR");
    }
  };

  return (
    <div className="w-64 bg-[#262626] border-r border-[#404040] flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-[#404040]">
        <button
          onClick={handleCreateClick}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-[#10a37f] hover:bg-[#1a9970] text-white rounded-lg font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          {isCreating ? "생성" : "새 채팅"}
        </button>
      </div>

      {/* New Conversation Input */}
      {isCreating && (
        <div className="p-3 border-b border-[#404040] bg-[#2d2d2d]">
          <input
            type="text"
            placeholder="제목 입력..."
            value={newConversationTitle}
            onChange={(e) => setNewConversationTitle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleCreateClick();
              }
              if (e.key === "Escape") {
                setIsCreating(false);
                setNewConversationTitle("");
              }
            }}
            className="w-full px-3 py-2 bg-[#1a1a1a] border border-[#404040] text-white rounded-lg text-sm focus:outline-none focus:border-[#10a37f]"
            autoFocus
          />
        </div>
      )}

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-[#b4b4b4] text-sm">
            로드 중...
          </div>
        ) : conversations.length === 0 ? (
          <div className="p-4 text-center text-[#b4b4b4] text-sm">
            채팅이 없습니다
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                className={`group flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                  selectedConversationId === conversation.id
                    ? "bg-[#404040]"
                    : "hover:bg-[#2d2d2d]"
                }`}
                onClick={() => onSelectConversation(conversation.id)}
              >
                <MessageSquare className="w-4 h-4 text-[#10a37f] flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-white text-sm font-medium truncate">
                    {conversation.title || "제목 없음"}
                  </div>
                  <div className="text-[#b4b4b4] text-xs truncate">
                    {conversation.last_message || "메시지 없음"}
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteConversation(conversation.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-600/20 rounded transition-all"
                  title="삭제"
                >
                  <Trash2 className="w-4 h-4 text-red-400" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-[#404040] p-3 text-[#b4b4b4] text-xs text-center">
        Vault AI Chat
      </div>
    </div>
  );
}
