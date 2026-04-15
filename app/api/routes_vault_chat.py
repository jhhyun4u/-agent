"""
Vault AI Chat Routes - Main endpoints for Vault AI Chat system
Phase 1 implementation
"""

import logging
import time
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, StreamingResponse
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

from app.api.deps import get_current_user
from app.models.auth_schemas import CurrentUser
from app.models.vault_schemas import (
    VaultChatRequest,
    VaultChatResponse,
    ConversationCreate,
    ConversationSummary,
    ConversationDetail,
    ChatMessage,
    VaultSection,
    DocumentSource,
)
from app.utils.supabase_client import get_async_client
from app.services.vault_query_router import vault_router
from app.services.vault_validation import HallucinationValidator
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

def _build_system_prompt(sources_context: str) -> str:
    """Build system prompt with context from sources"""
    return f"""You are TENOPA Vault AI Assistant - an expert knowledge management assistant.

Available context from knowledge base:
{sources_context}

Guidelines:
- Answer based on provided sources whenever possible
- If information is not in sources, clearly state that
- For Korean queries, respond in Korean
- For government data, ensure absolute accuracy
- Cite sources when possible using [source] format
- Be concise but thorough"""


def _build_user_message(message: str, context: List[ChatMessage]) -> str:
    """Build user message with conversation context"""
    context_str = (
        chr(10).join(f'{msg.role}: {msg.content}' for msg in context[-3:])
        if context
        else 'No previous messages'
    )

    return f"""User question: {message}

Previous context (if any):
{context_str}

Please provide a helpful response based on available sources."""


async def _log_analytics(
    user_id: str,
    query: str,
    sections: List[str],
    result_count: int,
    response_time_ms: float,
    conversation_id: Optional[str] = None,
) -> None:
    """Log search analytics to vault_audit_logs table (fire-and-forget)"""
    try:
        client = await get_async_client()
        await client.table("vault_audit_logs").insert({
            "user_id": user_id,
            "action": "search",
            "query": query,
            "sections": sections,
            "result_count": result_count,
            "response_time_ms": response_time_ms,
            "conversation_id": conversation_id,
            "created_at": datetime.utcnow().isoformat(),
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
        
        # Step 3: Retrieve sources based on routed sections
        sources = []
        source_texts = []
        
        for section in routing_decision.sections:
            if section == VaultSection.COMPLETED_PROJECTS:
                handler_results = await CompletedProjectsHandler.search(
                    query=request.message,
                    filters=routing_decision.filters,
                    limit=5
                )
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
                        sources.append(doc_source)
                        if doc.content:
                            source_texts.append(doc.content)

            elif section == VaultSection.GOVERNMENT_GUIDELINES:
                handler_results = await GovernmentGuidelinesHandler.search(
                    query=request.message,
                    filters=routing_decision.filters,
                    limit=5
                )
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
                        sources.append(doc_source)
                        if doc.content:
                            source_texts.append(doc.content)
        
        # Step 4: Generate response using Claude Sonnet
        sources_context = "\n".join(source_texts) if source_texts else "No sources found"
        system_prompt = _build_system_prompt(sources_context)
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
            conversation_id=conversation_id,
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

            sources = []
            source_texts = []

            for section in routing_decision.sections:
                if section == VaultSection.COMPLETED_PROJECTS:
                    handler_results = await CompletedProjectsHandler.search(
                        query=request.message,
                        filters=routing_decision.filters,
                        limit=5
                    )
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
                            sources.append(doc_source)
                            if doc.content:
                                source_texts.append(doc.content)

                elif section == VaultSection.GOVERNMENT_GUIDELINES:
                    handler_results = await GovernmentGuidelinesHandler.search(
                        query=request.message,
                        filters=routing_decision.filters,
                        limit=5
                    )
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
                            sources.append(doc_source)
                            if doc.content:
                                source_texts.append(doc.content)

            # Emit sources event
            sources_event = json.dumps({
                "event": "sources",
                "sources": [s.model_dump(mode="json") for s in sources]
            })
            yield f"data: {sources_event}\n\n"

            # Build prompts
            sources_context = "\n".join(source_texts) if source_texts else "No sources found"
            system_prompt = _build_system_prompt(sources_context)
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
                conversation_id=conversation_id,
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
    """
    try:
        client = await get_async_client()
        
        # Get conversation
        conv_result = await client.table("vault_conversations").select(
            "id, user_id, title, created_at, updated_at"
        ).eq("id", conversation_id).eq(
            "user_id", current_user.id
        ).single().execute()
        
        if not conv_result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conv = conv_result.data
        
        # Get messages
        messages_result = await client.table("vault_messages").select(
            "id, role, content, sources, confidence, created_at"
        ).eq("conversation_id", conversation_id).order(
            "created_at", asc=True
        ).execute()
        
        messages = []
        for msg in messages_result.data:
            messages.append(ChatMessage(
                id=msg["id"],
                role=msg["role"],
                content=msg["content"],
                confidence=msg.get("confidence"),
                created_at=datetime.fromisoformat(msg["created_at"])
            ))
        
        return ConversationDetail(
            id=conv["id"],
            user_id=conv["user_id"],
            title=conv.get("title"),
            created_at=datetime.fromisoformat(conv["created_at"]),
            updated_at=datetime.fromisoformat(conv["updated_at"]),
            message_count=len(messages),
            messages=messages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load conversation")


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


# ============================================================================
# Helper Functions
# ============================================================================

async def _load_conversation_context(
    conversation_id: str,
    user_id: str,
    limit: int = 10
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


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vault-chat"}
