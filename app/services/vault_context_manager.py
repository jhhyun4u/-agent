"""
Vault Context Manager - Extract and enhance context from conversation history
Module-2: A.1 Context Improvement
Design Ref: §5.1, §6.1
"""

import logging
from typing import List, Optional
from app.models.vault_schemas import ChatMessage

logger = logging.getLogger(__name__)


class VaultContextManager:
    """Manage context extraction and enhancement for better routing and responses"""

    CONTEXT_WINDOW = 6  # Last N turns to use as context
    TOPIC_LENGTH = 80   # Max chars for topic hint

    @staticmethod
    def extract_context(messages: List[ChatMessage]) -> List[ChatMessage]:
        """
        Extract last N conversation turns for context injection.

        Design Ref: §A.1 — Extend context from 3 to 6 turns

        Args:
            messages: Full conversation message history

        Returns:
            Last N messages (up to CONTEXT_WINDOW)
        """
        if not messages:
            return []

        # Return last 6 turns (or fewer if conversation is shorter)
        window_size = min(VaultContextManager.CONTEXT_WINDOW, len(messages))
        return messages[-window_size:]

    @staticmethod
    def detect_conversation_topic(messages: List[ChatMessage]) -> Optional[str]:
        """
        Extract conversation topic from first user message.

        Design Ref: §A.1 — Topic hint for routing accuracy

        Args:
            messages: Conversation message history

        Returns:
            Topic string (first 80 chars of first user message), or None
        """
        if not messages:
            return None

        # Find first user message
        for msg in messages:
            if msg.role == "user":
                # Extract first N characters as topic hint
                topic = msg.content[:VaultContextManager.TOPIC_LENGTH]
                if topic:
                    return f"[대화 주제: {topic}...]"

        return None

    @staticmethod
    def build_context_string(messages: List[ChatMessage]) -> str:
        """
        Format context messages as string for prompt injection.

        Design Ref: §A.1 — Formatted context for LLM

        Args:
            messages: Context messages (from extract_context)

        Returns:
            Formatted context string ready for prompt
        """
        if not messages:
            return ""

        context_parts = []
        for i, msg in enumerate(messages, 1):
            role_label = "사용자" if msg.role == "user" else "어시스턴트"
            context_parts.append(f"Turn {i}: {role_label}: {msg.content}")

        return "\n".join(context_parts)

    @staticmethod
    def build_user_message_with_context(
        message: str,
        context: List[ChatMessage],
    ) -> str:
        """
        Build enhanced user message with context and topic hint.

        Design Ref: §A.1 — Context-enhanced message for routing

        Args:
            message: Current user message
            context: Conversation context (from extract_context)

        Returns:
            Enhanced message with context prepended
        """
        parts = []

        # Add topic hint if available
        if context:
            topic = VaultContextManager.detect_conversation_topic(context)
            if topic:
                parts.append(topic)

            # Add context window
            context_str = VaultContextManager.build_context_string(context)
            if context_str:
                parts.append(f"\n대화 기록:\n{context_str}")

        # Add current message
        parts.append(f"\n현재 질문: {message}")

        return "\n".join(parts)
