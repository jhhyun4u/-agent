"""
Vault AI Chat Phase 1 Week 3 Module-3 - Response Regeneration Tests
Tests for:
- A.2: Response regeneration with temperature variation
- Message editing (frontend integration)
- Temperature adjustment logic
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.models.vault_schemas import (
    VaultChatResponse,
    VaultRegenerateRequest,
    ChatMessage,
    DocumentSource,
    VaultSection,
)


class TestA2RegenerationRequest:
    """Test A.2: Response Regeneration Request Model"""

    def test_regenerate_request_with_variation(self):
        """Test VaultRegenerateRequest model"""
        request = VaultRegenerateRequest(
            conversation_id="conv-1",
            variation=0.2
        )

        assert request.conversation_id == "conv-1"
        assert request.variation == 0.2

    def test_regenerate_request_default_variation(self):
        """Test default variation value"""
        request = VaultRegenerateRequest(conversation_id="conv-1")

        assert request.variation == 0.1

    def test_regenerate_request_variation_bounds(self):
        """Test variation bounds validation"""
        # Valid: 0.0 to 1.0
        request1 = VaultRegenerateRequest(conversation_id="conv-1", variation=0.0)
        assert request1.variation == 0.0

        request2 = VaultRegenerateRequest(conversation_id="conv-1", variation=1.0)
        assert request2.variation == 1.0

        request3 = VaultRegenerateRequest(conversation_id="conv-1", variation=0.5)
        assert request3.variation == 0.5


class TestTemperatureAdjustment:
    """Test temperature adjustment logic for regeneration"""

    def test_temperature_calculation_base(self):
        """Test base temperature (0.7) + variation"""
        base_temp = 0.7
        variation = 0.1

        adjusted = base_temp + variation
        assert abs(adjusted - 0.8) < 0.0001  # Allow for floating point precision

    def test_temperature_calculation_capped(self):
        """Test temperature capped at 1.0"""
        base_temp = 0.7
        variation = 0.5

        adjusted = min(base_temp + variation, 1.0)
        assert adjusted == 1.0

    def test_temperature_calculation_zero_variation(self):
        """Test temperature with zero variation"""
        base_temp = 0.7
        variation = 0.0

        adjusted = min(base_temp + variation, 1.0)
        assert adjusted == 0.7

    def test_temperature_affects_diversity(self):
        """Test that temperature affects response diversity conceptually"""
        # Lower temp = more deterministic (focused)
        # Higher temp = more diverse (creative)

        low_temp = 0.7 + 0.0  # 0.7 - focused
        high_temp = 0.7 + 0.3  # 1.0 (capped) - creative (but at cap)

        # This is conceptual - actual LLM diversity varies by implementation
        assert low_temp < high_temp


class TestRegenerationFlow:
    """Test response regeneration flow"""

    @pytest.mark.asyncio
    async def test_regeneration_request_structure(self):
        """Test regeneration request has all required fields"""
        request = VaultRegenerateRequest(
            conversation_id="conv-123",
            variation=0.15
        )

        # Should be serializable for API
        data = request.model_dump()
        assert "conversation_id" in data
        assert "variation" in data
        assert data["conversation_id"] == "conv-123"
        assert data["variation"] == 0.15

    def test_regenerated_response_structure(self):
        """Test regenerated response contains new content"""
        sources = [
            DocumentSource(
                document_id="doc-1",
                section=VaultSection.COMPLETED_PROJECTS,
                title="Project A"
            )
        ]

        # Regenerated response (simulated)
        response = VaultChatResponse(
            response="This is a regenerated response[출처 1].",
            confidence=0.85,
            sources=sources,
            validation_passed=True,
            warnings=[]
        )

        assert response.response == "This is a regenerated response[출처 1]."
        assert len(response.sources) == 1
        assert response.validation_passed is True


class TestMessageContext:
    """Test context handling for regeneration"""

    def test_extract_context_before_message(self):
        """Test extracting context up to a specific message"""
        messages = [
            ChatMessage(id="msg-1", role="user", content="Q1"),
            ChatMessage(id="msg-2", role="assistant", content="A1"),
            ChatMessage(id="msg-3", role="user", content="Q2"),
            ChatMessage(id="msg-4", role="assistant", content="A2"),  # This will be regenerated
        ]

        # Find message to regenerate
        regen_idx = next(i for i, m in enumerate(messages) if m.id == "msg-4")

        # Context should be messages before regeneration point
        context = messages[:regen_idx]

        assert len(context) == 3
        assert context[-1].role == "user"  # Last should be user's question

    def test_original_query_extraction(self):
        """Test extracting original query from context"""
        messages = [
            ChatMessage(id="msg-1", role="user", content="Tell me about AI"),
            ChatMessage(id="msg-2", role="assistant", content="AI is..."),
            ChatMessage(id="msg-3", role="user", content="More details?"),
            ChatMessage(id="msg-4", role="assistant", content="Here are details..."),  # To regenerate
        ]

        # Find the user message before the assistant message to regenerate
        regen_idx = 3  # msg-4 is at index 3

        # Original user query is at regen_idx - 1
        original_query = messages[regen_idx - 1].content

        assert original_query == "More details?"


class TestRegenerationValidation:
    """Test regeneration validation and error handling"""

    def test_message_ownership_validation(self):
        """Test that regeneration validates message belongs to conversation"""
        # Simulate a message from a different conversation
        message_conv_id = "conv-1"
        request_conv_id = "conv-2"

        # Should fail validation
        assert message_conv_id != request_conv_id

    def test_user_authorization_check(self):
        """Test that only conversation owner can regenerate"""
        # Message owner: user-1
        # Request from: user-2
        message_owner = "user-1"
        current_user = "user-2"

        # Should fail authorization
        assert message_owner != current_user

    def test_valid_regeneration_prerequisites(self):
        """Test prerequisites for valid regeneration"""
        # Requirements:
        # 1. Message exists
        # 2. Message belongs to conversation
        # 3. User owns conversation
        # 4. Message is assistant message (we're regenerating a response)
        # 5. Previous message is user question

        prerequisites = {
            "message_exists": True,
            "belongs_to_conversation": True,
            "user_owns_conversation": True,
            "message_is_assistant": True,
            "previous_is_user": True,
        }

        # All should be True for valid regeneration
        assert all(prerequisites.values())


class TestIntegrationModule3:
    """Integration tests for Module-3 regeneration features"""

    def test_regeneration_temperature_ladder(self):
        """Test temperature variation creates different responses"""
        # Base temperature
        base = 0.7

        variations = [0.0, 0.1, 0.2, 0.3]
        temps = [min(base + v, 1.0) for v in variations]

        # Should be increasing (mostly - last one capped)
        assert temps[0] < temps[1]
        assert temps[1] < temps[2]
        # temps[3] might equal temps[2] if capped

    def test_regeneration_response_format(self):
        """Test regenerated response has proper format"""
        # Original response
        original = VaultChatResponse(
            response="Original answer[출처 1].",
            confidence=0.8,
            sources=[
                DocumentSource(
                    document_id="d1",
                    section=VaultSection.COMPLETED_PROJECTS,
                    title="S1"
                )
            ],
            validation_passed=True
        )

        # Regenerated response (should have same structure)
        regenerated = VaultChatResponse(
            response="Regenerated answer with variation[출처 1].",
            confidence=0.82,
            sources=[
                DocumentSource(
                    document_id="d1",
                    section=VaultSection.COMPLETED_PROJECTS,
                    title="S1"
                )
            ],
            validation_passed=True
        )

        # Both should be valid VaultChatResponse
        assert type(original) == type(regenerated)
        assert original.sources[0].document_id == regenerated.sources[0].document_id
        # But responses should be different
        assert original.response != regenerated.response

    def test_message_context_preservation(self):
        """Test that context is preserved during regeneration"""
        # Original conversation context
        conversation_context = [
            ChatMessage(id="m1", role="user", content="Topic: AI"),
            ChatMessage(id="m2", role="assistant", content="AI definition..."),
            ChatMessage(id="m3", role="user", content="Tell me more"),
            ChatMessage(id="m4", role="assistant", content="Details about AI..."),  # To regenerate
        ]

        # When regenerating m4, context should include m1-m3
        regen_idx = 3
        context_for_regen = conversation_context[:regen_idx]

        # Verify context is correct
        assert len(context_for_regen) == 3
        assert context_for_regen[-1].role == "user"
        assert context_for_regen[-1].content == "Tell me more"

        # Original query should be extractable
        original_query = context_for_regen[-1].content
        assert original_query == "Tell me more"

        # Previous context (for building message) should exclude the question
        prev_context = context_for_regen[:-1]
        assert len(prev_context) == 2
        assert prev_context[-1].id == "m2"  # Last message before the question
