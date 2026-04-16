"""
Vault AI Chat Routes - Main endpoints for Vault AI Chat system
Phase 1 implementation
"""

import logging
import time
import json
import secrets
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.responses import StreamingResponse
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

from app.api.deps import get_current_user
from app.models.auth_schemas import CurrentUser
from app.models.vault_schemas import (
    VaultChatRequest,
    VaultChatResponse,
    VaultRegenerateRequest,
    ConversationCreate,
    ConversationUpdate,
    ConversationSummary,
    ConversationDetail,
    ConversationShareResponse,
    BookmarkCreate,
    BookmarkResponse,
    ChatMessage,
    VaultSection,
    DocumentSource,
)
from app.utils.supabase_client import get_async_client
from app.services.vault_query_router import vault_router
from app.services.vault_validation import HallucinationValidator
from app.services.vault_cache_service import VaultCacheService
from app.services.vault_context_manager import VaultContextManager
from app.services.vault_citation_service import VaultCitationService
from app.services.vault_handlers.completed_projects import CompletedProjectsHandler
from app.services.vault_handlers.government_guidelines import GovernmentGuidelinesHandler
from app.services.claude_client import claude_generate, claude_generate_streaming

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vault", tags=["vault-chat"])


# ============================================================================
# Rate Limiting
# ============================================================================

class RateLimiter:
    """Simple in-memory rate limiter for API endpoints"""
    
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict = defaultdict(list)  # user_id -> list of timestamps
        self._cleanup_lock = asyncio.Lock()
    
    async def is_allowed(self, user_id: str) -> bool:
        """Check if user has requests remaining"""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        async with self._cleanup_lock:
            self.requests[user_id] = [
                ts for ts in self.requests[user_id] 
                if ts > window_start
            ]
        
        # Check limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[user_id].append(now)
        return True


# Create rate limiters for different endpoints
chat_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)  # 30 requests per minute


# ============================================================================
# Helper Functions
# ============================================================================

def _format_numbered_sources(source_texts: List[str]) -> str:
    """Format sources with numbering for citation purposes"""
    if not source_texts:
        return "No sources found"

    numbered_sources = []
    for i, text in enumerate(source_texts, 1):
        # Limit each source to 500 chars to avoid token bloat
        limited_text = text[:500] if len(text) > 500 else text
        numbered_sources.append(f"[출처 {i}]\n{limited_text}")

    return "\n\n---\n\n".join(numbered_sources)


def _build_system_prompt(sources_context: str, source_count: int = 0) -> str:
    """Build system prompt with context from sources and citation instructions

    Design Ref: §A.3 — Citation-enhanced system prompt
    """
    base_prompt = f"""You are TENOPA Vault AI Assistant - an expert knowledge management assistant.

Available context from knowledge base:
{sources_context}

Guidelines:
- Answer based on provided sources whenever possible
- If information is not in sources, clearly state that
- For Korean queries, respond in Korean
- For government data, ensure absolute accuracy

- Be concise but thorough"""

    # Add citation instructions using VaultCitationService
    if source_count > 0:
        enhanced_prompt = VaultCitationService.inject_citation_instructions(
            base_prompt,
            source_count=source_count
        )
        return enhanced_prompt

    return base_prompt


async def _search_sections_parallel(
    sections: List[VaultSection],
    query: str,
    filters: Dict[str, Any],
    limit: int = 5,
) -> tuple[List[DocumentSource], List[str]]:
    """
    Search multiple sections in parallel using asyncio.gather.
    Returns (sources, source_texts).
    """
    async def search_section(section: VaultSection) -> tuple[List[DocumentSource], List[str]]:
        """Search a single section and return results."""
        section_sources = []
        section_texts = []

        try:
            if section == VaultSection.COMPLETED_PROJECTS:
                handler_results = await CompletedProjectsHandler.search(
                    query=query,
                    filters=filters,
                    limit=limit
                )
            elif section == VaultSection.GOVERNMENT_GUIDELINES:
                handler_results = await GovernmentGuidelinesHandler.search(
                    query=query,
                    filters=filters,
                    limit=limit
                )
            else:
                # Unknown section - return empty
                return ([], [])

            for result in handler_results:
                if result.document:
                    doc = result.document
                    doc_source = DocumentSource(
                        document_id=doc.id,
                        section=doc.section,
                        title=doc.title,
                        snippet=(doc.content or "")[:300] if doc.content else None,
                        confidence=result.relevance_score,
                        metadata=doc.metadata,
                    )
                    section_sources.append(doc_source)
                    if doc.content:
                        section_texts.append(doc.content)
        except Exception as e:
            logger.warning(f"Error searching section {section}: {str(e)}")

        return (section_sources, section_texts)

    # Run all searches in parallel
    results = await asyncio.gather(
        *[search_section(section) for section in sections],
        return_exceptions=False
    )

    # Flatten results
    all_sources = []
    all_texts = []
    for section_sources, section_texts in results:
        all_sources.extend(section_sources)
        all_texts.extend(section_texts)

    return (all_sources, all_texts)


def _build_user_message(message: str, context: List[ChatMessage]) -> str:
    """Build user message with conversation context

    Design Ref: §A.1 — Context-enhanced message for routing
    """
    # Extract recent context (last 6 turns)
    recent_context = VaultContextManager.extract_context(context)

    # Build enhanced message with context and topic hint
    enhanced_message = VaultContextManager.build_user_message_with_context(
        message=message,
        context=recent_context
    )

    return enhanced_message


async def _log_analytics(
    user_id: str,
    query: str,
    sections: List[str],
    result_count: int,
    response_time_ms: float,
) -> None:
    """Log search analytics to vault_audit_logs table (fire-and-forget)"""
    try:
        client = await get_async_client()
        # Combine multiple sections into a single string (comma-separated)
        section_str = ",".join(sections) if sections else None
        await client.table("vault_audit_logs").insert({
            "user_id": user_id,
            "action": "search",
            "query": query,
            "section": section_str,
            "result_count": result_count,
            "response_time_ms": int(response_time_ms),
        }).execute()
    except Exception as e:
        logger.warning(f"Failed to log analytics: {str(e)}")


# ============================================================================
# Chat Endpoints
# ============================================================================

@router.post("/chat", response_model=VaultChatResponse)
async def vault_chat(
    request: VaultChatRequest,
    current_user: CurrentUser = Depends(get_current_user)
) -> VaultChatResponse:
    """
    Main Vault AI Chat endpoint
    
    Workflow:
    1. Check rate limit
    2. Load conversation context
    3. Detect intent & route to handler
    4. Retrieve sources from DB
    5. Generate LLM response using Claude Sonnet
    6. Validate response (3-point gate)
    7. Save to conversation history
    8. Return response with metadata
    """
    
    start_time = time.monotonic()
    try:
        # Step 0: Check rate limit
        if not await chat_rate_limiter.is_allowed(current_user.id):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Maximum 30 requests per minute."
            )
        # Step 1: Load conversation context
        conversation_id = request.conversation_id
        conversation_context: List[ChatMessage] = []
        
        if conversation_id:
            conversation_context = await _load_conversation_context(
                conversation_id, 
                current_user.id
            )
        
        # Step 2: Detect intent and route using vault_router
        routing_decision = await vault_router.route(
            query=request.message,
            conversation_context=conversation_context
        )
        
        # Step 3: Retrieve sources from all sections (with caching)
        # Generate cache key for this search
        section_names = [s.value if hasattr(s, 'value') else str(s) for s in routing_decision.sections]
        search_cache_key = VaultCacheService._make_cache_key(
            query=request.message,
            sections=section_names,
            filters=routing_decision.filters
        )

        # Try cache first
        cached_sources = await VaultCacheService.get_search(
            cache_key=search_cache_key,
            sections=section_names
        )

        if cached_sources:
            sources = cached_sources
            source_texts = [s.snippet or "" for s in sources if s.snippet]
            logger.info(f"Cache hit for search: {search_cache_key[:8]}...")
        else:
            # Cache miss - perform actual search
            sources, source_texts = await _search_sections_parallel(
                sections=routing_decision.sections,
                query=request.message,
                filters=routing_decision.filters,
                limit=5
            )

            # Cache the results
            await VaultCacheService.set_search(
                cache_key=search_cache_key,
                results=sources,
                sections=section_names,
                ttl=VaultCacheService.SEARCH_TTL
            )

        # Step 4: Generate response using Claude Sonnet
        sources_context = _format_numbered_sources(source_texts)
        system_prompt = _build_system_prompt(sources_context, source_count=len(sources))
        user_message = _build_user_message(request.message, conversation_context)
        
        llm_response = await claude_generate(
            prompt=user_message,
            system_prompt=system_prompt,
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            temperature=0.7,
            response_format="text"
        )
        
        response_text = llm_response.get("text", "")
        initial_confidence = routing_decision.confidence if routing_decision else 0.5
        
        # Step 5: Validate response using 3-point gate
        validation_result = await HallucinationValidator.validate(
            response=response_text,
            sources=sources,
            confidence=initial_confidence,
            source_texts=source_texts
        )
        
        validation_passed = validation_result.get("passed", False)
        final_confidence = validation_result.get("confidence", initial_confidence)
        
        # Step 6: Save to conversation
        if not conversation_id:
            conversation_id = await _create_conversation(current_user.id)
        
        await _save_message(
            conversation_id,
            role="user",
            content=request.message,
            user_id=current_user.id
        )
        
        response_id = await _save_message(
            conversation_id,
            role="assistant",
            content=response_text,
            sources_json=[s.model_dump(mode="json") for s in sources],
            confidence=final_confidence,
            user_id=current_user.id
        )
        
        # Step 7: Log analytics (fire-and-forget)
        response_time_ms = (time.monotonic() - start_time) * 1000
        section_names = [s.value if hasattr(s, 'value') else str(s) for s in routing_decision.sections]
        asyncio.create_task(_log_analytics(
            user_id=current_user.id,
            query=request.message,
            sections=section_names,
            result_count=len(sources),
            response_time_ms=response_time_ms,
        ))

        # Step 8: Return response
        return VaultChatResponse(
            response=response_text,
            confidence=final_confidence,
            sources=sources,
            validation_passed=validation_passed,
            message_id=response_id
        )

    except Exception as e:
        logger.error(f"Error in vault_chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI Chat service error: {str(e)}")


@router.post("/chat/stream")
async def vault_chat_stream(
    request: VaultChatRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Streaming Vault AI Chat endpoint - returns Server-Sent Events (SSE)

    Event sequence:
    1. sources event - initial sources found
    2. token events - streamed response text chunks
    3. done event - completion with metadata

    Use with fetch() + ReadableStream for browser clients
    """

    async def event_generator():
        start_time = time.monotonic()
        try:
            # Rate limit
            if not await chat_rate_limiter.is_allowed(current_user.id):
                error_event = json.dumps({"event": "error", "message": "Rate limit exceeded"})
                yield f"data: {error_event}\n\n"
                return

            # Load conversation context
            conversation_id = request.conversation_id
            conversation_context: List[ChatMessage] = []

            if conversation_id:
                conversation_context = await _load_conversation_context(
                    conversation_id,
                    current_user.id
                )

            # Route and retrieve sources
            routing_decision = await vault_router.route(
                query=request.message,
                conversation_context=conversation_context
            )

            # Retrieve sources from all sections (with caching)
            section_names = [s.value if hasattr(s, 'value') else str(s) for s in routing_decision.sections]
            search_cache_key = VaultCacheService._make_cache_key(
                query=request.message,
                sections=section_names,
                filters=routing_decision.filters
            )

            # Try cache first
            cached_sources = await VaultCacheService.get_search(
                cache_key=search_cache_key,
                sections=section_names
            )

            if cached_sources:
                sources = cached_sources
                source_texts = [s.snippet or "" for s in sources if s.snippet]
                logger.info(f"Cache hit for stream: {search_cache_key[:8]}...")
            else:
                # Cache miss - perform actual search
                sources, source_texts = await _search_sections_parallel(
                    sections=routing_decision.sections,
                    query=request.message,
                    filters=routing_decision.filters,
                    limit=5
                )

                # Cache the results
                await VaultCacheService.set_search(
                    cache_key=search_cache_key,
                    results=sources,
                    sections=section_names,
                    ttl=VaultCacheService.SEARCH_TTL
                )

            # Emit sources event
            sources_event = json.dumps({
                "event": "sources",
                "sources": [s.model_dump(mode="json") for s in sources]
            })
            yield f"data: {sources_event}\n\n"

            # Build prompts
            sources_context = _format_numbered_sources(source_texts)
            system_prompt = _build_system_prompt(sources_context, source_count=len(sources))
            user_message = _build_user_message(request.message, conversation_context)

            # Stream response tokens
            full_response = ""
            initial_confidence = routing_decision.confidence if routing_decision else 0.5

            async for token_chunk in claude_generate_streaming(
                prompt=user_message,
                system_prompt=system_prompt,
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                temperature=0.7,
            ):
                full_response += token_chunk
                token_event = json.dumps({"event": "token", "text": token_chunk})
                yield f"data: {token_event}\n\n"

            # Validate complete response
            validation_result = await HallucinationValidator.validate(
                response=full_response,
                sources=sources,
                confidence=initial_confidence,
                source_texts=source_texts
            )

            validation_passed = validation_result.get("passed", False)
            final_confidence = validation_result.get("confidence", initial_confidence)

            # Save messages
            if not conversation_id:
                conversation_id = await _create_conversation(current_user.id)

            await _save_message(
                conversation_id,
                role="user",
                content=request.message,
                user_id=current_user.id
            )

            response_id = await _save_message(
                conversation_id,
                role="assistant",
                content=full_response,
                sources_json=[s.model_dump(mode="json") for s in sources],
                confidence=final_confidence,
                user_id=current_user.id
            )

            # Emit done event
            done_event = json.dumps({
                "event": "done",
                "confidence": final_confidence,
                "validation_passed": validation_passed,
                "warnings": validation_result.get("warnings", []),
                "message_id": response_id
            })
            yield f"data: {done_event}\n\n"

            # Log analytics
            response_time_ms = (time.monotonic() - start_time) * 1000
            section_names = [s.value if hasattr(s, 'value') else str(s) for s in routing_decision.sections]
            asyncio.create_task(_log_analytics(
                user_id=current_user.id,
                query=request.message,
                sections=section_names,
                result_count=len(sources),
                response_time_ms=response_time_ms,
            ))

        except Exception as e:
            logger.error(f"Error in vault_chat_stream: {str(e)}")
            error_event = json.dumps({"event": "error", "message": str(e)})
            yield f"data: {error_event}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


# ============================================================================
# Conversation Management
# ============================================================================

@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    current_user: CurrentUser = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
) -> List[ConversationSummary]:
    """
    List user's conversations
    """
    try:
        client = await get_async_client()
        
        conversations = await client.table("vault_conversations").select(
            "id, title, created_at, updated_at"
        ).eq("user_id", current_user.id).order(
            "updated_at", desc=True
        ).range(offset, offset + limit).execute()
        
        results = []
        for conv in conversations.data:
            # Get last message
            messages = await client.table("vault_messages").select(
                "content"
            ).eq("conversation_id", conv["id"]).order(
                "created_at", desc=True
            ).limit(1).execute()
            
            last_message = messages.data[0]["content"] if messages.data else None
            
            # Count messages
            count_result = await client.table("vault_messages").select(
                "id", count="exact"
            ).eq("conversation_id", conv["id"]).execute()
            
            results.append(ConversationSummary(
                id=conv["id"],
                user_id=current_user.id,
                title=conv.get("title"),
                created_at=datetime.fromisoformat(conv["created_at"]),
                updated_at=datetime.fromisoformat(conv["updated_at"]),
                last_message=last_message,
                message_count=count_result.count or 0
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load conversations")


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_user)
) -> ConversationDetail:
    """
    Get conversation detail with full message history
    """
    try:
        client = await get_async_client()

        # Verify conversation ownership
        conv_result = await client.table("vault_conversations").select(
            "*"
        ).eq("id", conversation_id).eq("user_id", current_user.id).single().execute()

        if not conv_result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get messages
        messages_result = await client.table("vault_messages").select(
            "*"
        ).eq("conversation_id", conversation_id).order("created_at", desc=False).execute()

        return ConversationDetail(
            id=conv_result.data["id"],
            title=conv_result.data["title"],
            created_at=conv_result.data["created_at"],
            updated_at=conv_result.data["updated_at"],
            messages=[ChatMessage(**msg) for msg in messages_result.data or []]
        )
    except Exception as e:
        logger.error(f"Error retrieving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation")


@router.get("/conversations/{conversation_id}/messages", response_model=List[ChatMessage])
async def get_conversation_messages(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
) -> List[ChatMessage]:
    """
    Get messages from a conversation
    """
    try:
        client = await get_async_client()
        
        # Verify conversation ownership
        conv_result = await client.table("vault_conversations").select(
            "user_id"
        ).eq("id", conversation_id).single().execute()
        
        if not conv_result.data or conv_result.data["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Get messages
        messages_result = await client.table("vault_messages").select(
            "id, role, content, sources, confidence, created_at"
        ).eq("conversation_id", conversation_id).order(
            "created_at", asc=True
        ).range(offset, offset + limit).execute()
        
        messages = []
        for msg in messages_result.data:
            messages.append(ChatMessage(
                id=msg["id"],
                role=msg["role"],
                content=msg["content"],
                confidence=msg.get("confidence"),
                created_at=datetime.fromisoformat(msg["created_at"])
            ))
        
        return messages
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load messages")


@router.post("/conversations", response_model=ConversationSummary)
async def create_conversation(
    body: ConversationCreate,
    current_user: CurrentUser = Depends(get_current_user)
) -> ConversationSummary:
    """
    Create new conversation
    """
    try:
        client = await get_async_client()
        
        now = datetime.now().isoformat()
        
        result = await client.table("vault_conversations").insert({
            "user_id": current_user.id,
            "title": body.title,
            "created_at": now,
            "updated_at": now
        }).execute()
        
        conv = result.data[0]
        
        return ConversationSummary(
            id=conv["id"],
            user_id=conv["user_id"],
            title=conv.get("title"),
            created_at=datetime.fromisoformat(conv["created_at"]),
            updated_at=datetime.fromisoformat(conv["updated_at"]),
            message_count=0
        )
        
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Delete conversation (only owner can delete)
    """
    try:
        client = await get_async_client()
        
        # Verify ownership
        conv_result = await client.table("vault_conversations").select(
            "user_id"
        ).eq("id", conversation_id).single().execute()
        
        if not conv_result.data or conv_result.data["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Delete messages first
        await client.table("vault_messages").delete().eq(
            "conversation_id", conversation_id
        ).execute()
        
        # Delete conversation
        await client.table("vault_conversations").delete().eq(
            "id", conversation_id
        ).execute()
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")


@router.post("/messages/{message_id}/regenerate", response_model=VaultChatResponse)
async def regenerate_message(
    message_id: str,
    body: VaultRegenerateRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Regenerate a message response with temperature variation.

    Design Ref: §A.2 — Regenerate response with adjusted temperature

    Args:
        message_id: ID of assistant message to regenerate
        body: VaultRegenerateRequest with conversation_id and variation
    """
    try:
        client = await get_async_client()

        # Load original message and verify it belongs to current user
        msg_result = await client.table("vault_messages").select(
            "id,conversation_id,role,content"
        ).eq("id", message_id).single().execute()

        if not msg_result.data:
            raise HTTPException(status_code=404, detail="Message not found")

        message = msg_result.data
        if message["conversation_id"] != body.conversation_id:
            raise HTTPException(status_code=400, detail="Message does not belong to conversation")

        # Verify conversation ownership
        conv_result = await client.table("vault_conversations").select(
            "user_id"
        ).eq("id", body.conversation_id).single().execute()

        if not conv_result.data or conv_result.data["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Load conversation context (messages before this one)
        context = await _load_conversation_context(
            body.conversation_id,
            current_user.id,
            limit=20
        )

        # Filter context to only messages before the one being regenerated
        before_msg_idx = None
        for i, msg in enumerate(context):
            if msg.id == message_id:
                before_msg_idx = i
                break

        if before_msg_idx is None:
            context_for_regen = context
        else:
            context_for_regen = context[:before_msg_idx]

        # Get the user's original question (the message immediately before)
        if not context_for_regen or context_for_regen[-1].role != "user":
            raise HTTPException(status_code=400, detail="Cannot find user question for regeneration")

        original_query = context_for_regen[-1].content
        user_message = _build_user_message(original_query, context_for_regen[:-1])  # Context without the original question

        # Re-run search (use cache if available)
        routing_decision = await vault_router.route(original_query, context_hint="regeneration")
        section_names = [s.value for s in routing_decision.sections]
        search_cache_key = VaultCacheService._make_cache_key(
            original_query,
            section_names,
            routing_decision.filters
        )

        # Search sections (from cache or fresh)
        cached_sources = await VaultCacheService.get_search(
            cache_key=search_cache_key,
            sections=section_names
        )

        if cached_sources:
            sources = cached_sources
            source_texts = [s.snippet or "" for s in sources if s.snippet]
        else:
            # Cache miss - perform search
            sources, source_texts = await _search_sections_parallel(
                sections=routing_decision.sections,
                query=original_query,
                filters=routing_decision.filters,
                limit=5
            )

            # Cache results
            await VaultCacheService.set_search(
                cache_key=search_cache_key,
                results=sources,
                sections=section_names,
                ttl=VaultCacheService.SEARCH_TTL
            )

        # Generate response with adjusted temperature
        sources_context = _format_numbered_sources(source_texts)
        system_prompt = _build_system_prompt(sources_context, source_count=len(sources))

        base_temperature = 0.7
        adjusted_temperature = base_temperature + (body.variation or 0.1)
        adjusted_temperature = min(adjusted_temperature, 1.0)

        llm_response = await claude_generate(
            prompt=user_message,
            system_prompt=system_prompt,
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            temperature=adjusted_temperature
        )

        # Validate response
        validator = HallucinationValidator()
        validation_passed, warnings = validator.validate(
            llm_response,
            sources=sources
        )

        # Update message in database with new response
        confidence = routing_decision.confidence if routing_decision else 0.7

        await client.table("vault_messages").update({
            "content": llm_response,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", message_id).execute()

        # Log regeneration
        await _log_analytics(
            user_id=current_user.id,
            query=f"regenerate:{message_id}",
            sections=section_names,
            result_count=len(sources),
            response_time_ms=0.0
        )

        return VaultChatResponse(
            response=llm_response,
            confidence=confidence,
            sources=sources,
            validation_passed=validation_passed,
            warnings=warnings if warnings else []
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to regenerate message")


# ============================================================================
# Helper Functions
# ============================================================================

async def _load_conversation_context(
    conversation_id: str,
    user_id: str,
    limit: int = 20
) -> List[ChatMessage]:
    """Load recent messages from conversation for context"""
    try:
        client = await get_async_client()
        
        messages_result = await client.table("vault_messages").select(
            "id, role, content, created_at"
        ).eq("conversation_id", conversation_id).order(
            "created_at", desc=True
        ).limit(limit).execute()
        
        messages = []
        for msg in reversed(messages_result.data):  # Reverse to chronological order
            messages.append(ChatMessage(
                id=msg["id"],
                role=msg["role"],
                content=msg["content"],
                created_at=datetime.fromisoformat(msg["created_at"])
            ))
        
        return messages
        
    except Exception as e:
        logger.warning(f"Failed to load conversation context: {str(e)}")
        return []


async def _create_conversation(user_id: str) -> str:
    """Create new conversation and return ID"""
    try:
        client = await get_async_client()
        
        now = datetime.now().isoformat()
        
        result = await client.table("vault_conversations").insert({
            "user_id": user_id,
            "title": None,
            "created_at": now,
            "updated_at": now
        }).execute()
        
        return result.data[0]["id"]
        
    except Exception as e:
        logger.error(f"Failed to create conversation: {str(e)}")
        raise


async def _save_message(
    conversation_id: str,
    role: str,
    content: str,
    user_id: str,
    sources_json: Optional[list] = None,
    confidence: Optional[float] = None
) -> str:
    """Save message to conversation and return message ID"""
    try:
        client = await get_async_client()
        
        result = await client.table("vault_messages").insert({
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "sources": sources_json,
            "confidence": confidence,
            "created_at": datetime.now().isoformat()
        }).execute()
        
        return result.data[0]["id"]
        
    except Exception as e:
        logger.error(f"Failed to save message: {str(e)}")
        raise


@router.get("/suggestions", response_model=List[str])
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    limit: int = Query(5, ge=1, le=10, description="Max suggestions"),
    current_user: CurrentUser = Depends(get_current_user)
) -> List[str]:
    """
    Get search suggestions based on recent queries and document titles.

    Design Ref: §C.1 — Search suggestions/autocomplete

    Args:
        q: Search query (1-100 chars)
        limit: Maximum suggestions to return (1-10, default 5)
        current_user: Current authenticated user

    Returns:
        List of unique suggestion strings
    """
    try:
        client = await get_async_client()
        suggestions = set()

        # Step 1: Get recent queries from audit logs (limit//2)
        try:
            recent_queries_result = await client.table("vault_audit_logs").select(
                "query"
            ).eq("user_id", current_user.id).ilike(
                "query", f"%{q}%"
            ).order("created_at", desc=True).limit(
                max(1, limit // 2)
            ).execute()

            if recent_queries_result.data:
                for row in recent_queries_result.data:
                    if row.get("query"):
                        suggestions.add(row["query"])
        except Exception as e:
            logger.warning(f"Error fetching recent queries: {str(e)}")

        # Step 2: Get document titles (limit//2)
        try:
            docs_result = await client.table("vault_documents").select(
                "title"
            ).ilike("title", f"%{q}%").order(
                "created_at", desc=True
            ).limit(max(1, limit // 2)).execute()

            if docs_result.data:
                for row in docs_result.data:
                    if row.get("title"):
                        suggestions.add(row["title"])
        except Exception as e:
            logger.warning(f"Error fetching document titles: {str(e)}")

        # Return unique suggestions, limited to requested count
        result = sorted(list(suggestions))[:limit]

        logger.info(f"Returned {len(result)} suggestions for query '{q}'")
        return result

    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")


# ============================================================================
# Conversation Management — C.2 Sharing
# ============================================================================

@router.patch("/conversations/{conversation_id}", response_model=ConversationSummary)
async def update_conversation(
    conversation_id: str,
    body: ConversationUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update conversation title

    Design Ref: §C.2 — Conversation Sharing
    """
    try:
        client = await get_async_client()

        # Verify ownership
        conv = await client.table("vault_conversations").select("user_id").eq("id", conversation_id).single().execute()
        if conv.data["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")

        # Update title
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        if body.title is not None:
            update_data["title"] = body.title

        result = await client.table("vault_conversations").update(update_data).eq("id", conversation_id).execute()

        return ConversationSummary(
            id=result.data[0]["id"],
            user_id=result.data[0]["user_id"],
            title=result.data[0].get("title"),
            created_at=datetime.fromisoformat(result.data[0]["created_at"]),
            updated_at=datetime.fromisoformat(result.data[0]["updated_at"]),
            message_count=result.data[0].get("message_count", 0),
            last_message=result.data[0].get("last_message")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update conversation")


@router.post("/conversations/{conversation_id}/share", response_model=ConversationShareResponse)
async def share_conversation(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Generate share token and make conversation public

    Design Ref: §C.2 — Conversation Sharing
    """
    try:
        client = await get_async_client()

        # Verify ownership
        conv = await client.table("vault_conversations").select("user_id").eq("id", conversation_id).single().execute()
        if conv.data["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")

        # Generate unique share token
        share_token = secrets.token_urlsafe(16)

        # Update conversation with share token
        await client.table("vault_conversations").update({
            "share_token": share_token,
            "is_public": True,
            "shared_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", conversation_id).execute()

        return ConversationShareResponse(
            share_url=f"/vault/shared/{share_token}",
            share_token=share_token,
            is_public=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to share conversation")


@router.get("/shared/{share_token}", response_model=ConversationDetail)
async def get_shared_conversation(share_token: str):
    """Retrieve public shared conversation (no auth required)

    Design Ref: §C.2 — Conversation Sharing
    """
    try:
        client = await get_async_client()

        # Find public conversation by share token
        conv = await client.table("vault_conversations").select(
            "id, user_id, title, created_at, updated_at, message_count"
        ).eq("share_token", share_token).eq("is_public", True).single().execute()

        if not conv.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Load messages
        messages_result = await client.table("vault_messages").select(
            "id, role, content, created_at"
        ).eq("conversation_id", conv.data["id"]).order("created_at").execute()

        messages = [
            ChatMessage(
                id=m["id"],
                role=m["role"],
                content=m["content"],
                created_at=datetime.fromisoformat(m["created_at"])
            )
            for m in messages_result.data
        ]

        return ConversationDetail(
            id=conv.data["id"],
            user_id=conv.data["user_id"],
            title=conv.data.get("title"),
            created_at=datetime.fromisoformat(conv.data["created_at"]),
            updated_at=datetime.fromisoformat(conv.data["updated_at"]),
            message_count=conv.data.get("message_count", 0),
            messages=messages
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving shared conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation")


@router.get("/conversations/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    format: str = Query("markdown", regex="^(markdown|json)$"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Export conversation to markdown or JSON

    Design Ref: §C.2 — Conversation Sharing
    """
    try:
        client = await get_async_client()

        # Verify ownership
        conv = await client.table("vault_conversations").select("user_id, title").eq("id", conversation_id).single().execute()
        if conv.data["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")

        # Load messages
        messages_result = await client.table("vault_messages").select(
            "id, role, content, created_at"
        ).eq("conversation_id", conversation_id).order("created_at").execute()

        if format == "json":
            # Return as JSON
            return {
                "title": conv.data.get("title", "Untitled"),
                "created_at": datetime.utcnow().isoformat(),
                "messages": [
                    {
                        "id": m["id"],
                        "role": m["role"],
                        "content": m["content"],
                        "created_at": m["created_at"]
                    }
                    for m in messages_result.data
                ]
            }

        # Default: markdown format
        markdown = f"# {conv.data.get('title', 'Untitled')}\n\n"
        markdown += f"*Exported on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"

        for m in messages_result.data:
            role_label = "**User**" if m["role"] == "user" else "**Assistant**"
            markdown += f"{role_label}:\n\n{m['content']}\n\n---\n\n"

        from starlette.responses import Response
        return Response(
            content=markdown,
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=conversation.md"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export conversation")


# ============================================================================
# Bookmarks — C.3
# ============================================================================

@router.get("/bookmarks", response_model=List[BookmarkResponse])
async def list_bookmarks(
    bookmark_type: Optional[str] = Query(None, regex="^(message|document|conversation)$"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """List user's bookmarks with optional type filter

    Design Ref: §C.3 — Bookmarks
    """
    try:
        client = await get_async_client()

        # Build query
        query = client.table("vault_bookmarks").select(
            "id, bookmark_type, target_id, note, created_at"
        ).eq("user_id", current_user.id).order("created_at", desc=True)

        # Optional filter by type
        if bookmark_type:
            query = query.eq("bookmark_type", bookmark_type)

        result = await query.execute()

        return [
            BookmarkResponse(
                id=b["id"],
                bookmark_type=b["bookmark_type"],
                target_id=b["target_id"],
                note=b.get("note"),
                created_at=datetime.fromisoformat(b["created_at"])
            )
            for b in result.data
        ]
    except Exception as e:
        logger.error(f"Error listing bookmarks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list bookmarks")


@router.post("/bookmarks", response_model=BookmarkResponse)
async def create_bookmark(
    body: BookmarkCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create a bookmark

    Design Ref: §C.3 — Bookmarks
    """
    try:
        client = await get_async_client()

        # Create bookmark
        result = await client.table("vault_bookmarks").insert({
            "user_id": current_user.id,
            "bookmark_type": body.bookmark_type,
            "target_id": body.target_id,
            "note": body.note,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create bookmark")

        b = result.data[0]
        return BookmarkResponse(
            id=b["id"],
            bookmark_type=b["bookmark_type"],
            target_id=b["target_id"],
            note=b.get("note"),
            created_at=datetime.fromisoformat(b["created_at"])
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bookmark: {str(e)}")
        # Likely a unique constraint violation (duplicate bookmark)
        if "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail="Bookmark already exists")
        raise HTTPException(status_code=500, detail="Failed to create bookmark")


@router.delete("/bookmarks/{bookmark_id}")
async def delete_bookmark(
    bookmark_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete a bookmark

    Design Ref: §C.3 — Bookmarks
    """
    try:
        client = await get_async_client()

        # Verify ownership
        bookmark = await client.table("vault_bookmarks").select("user_id").eq("id", bookmark_id).single().execute()
        if bookmark.data["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")

        # Delete bookmark
        await client.table("vault_bookmarks").delete().eq("id", bookmark_id).execute()

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bookmark: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete bookmark")


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vault-chat"}
