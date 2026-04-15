/**
 * Vault AI Chat Layout
 * Main container for Vault chat interface with sidebar and conversation view
 */

import { useState, useRef, useEffect } from "react";
import VaultSidebar from "./VaultSidebar";
import VaultChat from "./VaultChat";
import { ChatMessage } from "@/lib/api";

export interface Conversation {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message?: string;
}

export interface VaultLayoutProps {
  userId: string;
}

export default function VaultLayout({ userId }: VaultLayoutProps) {
  const [selectedConversationId, setSelectedConversationId] = useState<
    string | null
  >(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      setIsLoading(true);
      const response = await fetch("/api/vault/conversations", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to load conversations");
      }

      const data = await response.json();
      setConversations(data);
      setError(null);
    } catch (err) {
      console.error("Error loading conversations:", err);
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateConversation = async (title?: string) => {
    try {
      const response = await fetch("/api/vault/conversations", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ title }),
      });

      if (!response.ok) {
        throw new Error("Failed to create conversation");
      }

      const newConversation = await response.json();
      setConversations((prev) => [newConversation, ...prev]);
      setSelectedConversationId(newConversation.id);
    } catch (err) {
      console.error("Error creating conversation:", err);
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  };

  const handleDeleteConversation = async (conversationId: string) => {
    try {
      const response = await fetch(`/api/vault/conversations/${conversationId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to delete conversation");
      }

      setConversations((prev) =>
        prev.filter((conv) => conv.id !== conversationId)
      );

      if (selectedConversationId === conversationId) {
        setSelectedConversationId(null);
      }
    } catch (err) {
      console.error("Error deleting conversation:", err);
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  };

  return (
    <div className="flex h-full bg-[#1a1a1a]" data-testid="vault-layout">
      {/* Vault Sidebar */}
      <VaultSidebar
        conversations={conversations}
        selectedConversationId={selectedConversationId}
        onSelectConversation={setSelectedConversationId}
        onCreateConversation={handleCreateConversation}
        onDeleteConversation={handleDeleteConversation}
        isLoading={isLoading}
      />

      {/* Chat Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {error && (
          <div className="px-4 py-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}
        <VaultChat conversationId={selectedConversationId} userId={userId} />
      </div>
    </div>
  );
}
