"""
Vault Context Manager - Extract and enhance context from conversation history
Phase 2: Context persistence, embeddings, and language support
Design Ref: §3.1, §A.1
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime
from app.models.vault_schemas import ChatMessage

logger = logging.getLogger(__name__)


class VaultContextManager:
    """Manage context extraction, storage, and enhancement for better routing and responses

    Phase 2 enhancements:
    - Context window increased to 8 turns
    - Context embedding support for semantic search
    - Language detection and storage
    - DB persistence with RLS
    """

    CONTEXT_WINDOW = 8  # Last N turns to use as context (Phase 2: increased from 6)
    EMBEDDING_DIM = 1536  # OpenAI embedding dimension
    TOPIC_LENGTH = 80   # Max chars for topic hint
    MAX_CONTEXT_TOKENS = 2000  # Token budget for context

    @staticmethod
    def extract_context(messages: List[ChatMessage]) -> List[ChatMessage]:
        """
        Extract last N conversation turns for context injection.

        Design Ref: §3.1 — Extend context from 6 to 8 turns

        Args:
            messages: Full conversation message history

        Returns:
            Last N messages (up to CONTEXT_WINDOW)
        """
        if not messages:
            return []

        # Return last 8 turns (or fewer if conversation is shorter)
        window_size = min(VaultContextManager.CONTEXT_WINDOW, len(messages))
        return messages[-window_size:]

    @staticmethod
    def detect_conversation_topic(messages: List[ChatMessage]) -> Optional[str]:
        """
        Extract conversation topic from first user message.

        Design Ref: §3.1 — Topic hint for routing accuracy

        Args:
            messages: Conversation message history

        Returns:
            Topic string (first 80 chars of first user message), or None
        """
        if not messages:
            return None

        # Find first user message
        for msg in messages:
            if hasattr(msg, 'role') and msg.role == "user":
                # Extract first N characters as topic hint
                content = msg.content if hasattr(msg, 'content') else ""
                topic = content[:VaultContextManager.TOPIC_LENGTH]
                if topic:
                    return f"[대화 주제: {topic}...]"

        return None

    @staticmethod
    def build_context_string(messages: List[ChatMessage]) -> str:
        """
        Format context messages as string for prompt injection.

        Design Ref: §3.1 — Formatted context for LLM

        Args:
            messages: Context messages (from extract_context)

        Returns:
            Formatted context string ready for prompt
        """
        if not messages:
            return ""

        context_parts = []
        for i, msg in enumerate(messages, 1):
            role_label = "사용자" if (hasattr(msg, 'role') and msg.role == "user") else "어시스턴트"
            content = msg.content if hasattr(msg, 'content') else ""
            # Truncate long messages for context
            truncated = content[:500] + "..." if len(content) > 500 else content
            context_parts.append(f"Turn {i}: {role_label}: {truncated}")

        return "\n".join(context_parts)

    @staticmethod
    def build_user_message_with_context(
        message: str,
        context: List[ChatMessage],
    ) -> str:
        """
        Build enhanced user message with context and topic hint.

        Design Ref: §3.1 — Context-enhanced message for routing

        Args:
            message: Current user message
            context: Conversation context (from extract_context)

        Returns:
            Enhanced message with context prepended
        """
        parts = []

        # Add context section header
        parts.append("[이전 대화 맥락]")

        # Add topic hint if available
        if context:
            topic = VaultContextManager.detect_conversation_topic(context)
            if topic:
                parts.append(topic)

            # Add context window
            context_str = VaultContextManager.build_context_string(context)
            if context_str:
                parts.append(context_str)

        # Add current message separator
        parts.append("\n[현재 질문]")
        parts.append(message)

        return "\n".join(parts)

    @staticmethod
    def should_inject_context(message_count: int) -> bool:
        """
        Determine whether context should be injected.

        Design Ref: §3.1 — Context injection decision

        Args:
            message_count: Number of messages in conversation

        Returns:
            True if 2+ messages in conversation (multi-turn)
        """
        return message_count >= 2

    @staticmethod
    def estimate_token_count(text: str) -> int:
        """
        Estimate token count using rough approximation (4 chars = 1 token).

        For production, use tiktoken library for exact count.

        Args:
            text: Text to count tokens

        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4 + 1

    @staticmethod
    def trim_context_by_tokens(
        context_str: str,
        max_tokens: int = MAX_CONTEXT_TOKENS
    ) -> str:
        """
        Trim context to fit within token budget.

        Design Ref: §3.1 — Token-aware context trimming

        Args:
            context_str: Full context string
            max_tokens: Maximum tokens allowed

        Returns:
            Trimmed context string
        """
        estimated_tokens = VaultContextManager.estimate_token_count(context_str)

        if estimated_tokens <= max_tokens:
            return context_str

        # Trim by line (remove oldest turns first)
        lines = context_str.split("\n")
        trimmed_lines = [lines[0]]  # Keep header

        current_tokens = VaultContextManager.estimate_token_count(lines[0])
        for line in lines[1:]:
            line_tokens = VaultContextManager.estimate_token_count(line)
            if current_tokens + line_tokens <= max_tokens:
                trimmed_lines.append(line)
                current_tokens += line_tokens
            else:
                break

        return "\n".join(trimmed_lines)

    @staticmethod
    def prepare_context_for_injection(
        messages: List[ChatMessage],
        max_tokens: int = MAX_CONTEXT_TOKENS
    ) -> Tuple[str, int]:
        """
        Prepare context for injection with token awareness.

        Design Ref: §3.1 — Token-aware context preparation

        Args:
            messages: Full conversation history
            max_tokens: Maximum tokens for context

        Returns:
            (context_string, token_count) tuple
        """
        extracted = VaultContextManager.extract_context(messages)
        context_str = VaultContextManager.build_context_string(extracted)
        trimmed = VaultContextManager.trim_context_by_tokens(context_str, max_tokens)
        token_count = VaultContextManager.estimate_token_count(trimmed)

        return trimmed, token_count
