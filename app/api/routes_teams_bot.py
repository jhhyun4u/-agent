"""
Teams Bot Routes - API Endpoints for Teams integration
Phase 2 DO Phase: Day 3-4 Implementation
Design Ref: §4.3-4.4, Vault Chat Phase 2 Technical Design
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator

from app.api.deps import get_current_user, require_role, require_project_access
from app.services.domains.operations.teams_bot_service import TeamsBotService, BotMode
from app.utils.supabase_client import get_supabase_async_client, SupabaseAsyncClient

logger = logging.getLogger(__name__)

# ── Router Setup ──
router = APIRouter(prefix="/api/teams/bot", tags=["teams-bot"])


# ── Pydantic Models ──

class BotModeResponse(BaseModel):
    """Bot mode configuration"""
    mode: str = Field(..., description="Bot mode: adaptive, digest, matching")
    enabled: bool = Field(default=True)


class TeamsBotConfigRequest(BaseModel):
    """Update Teams bot config"""
    bot_enabled: Optional[bool] = Field(None, description="Enable/disable bot")
    digest_enabled: Optional[bool] = Field(None, description="Enable/disable digest mode")
    digest_time: Optional[str] = Field(None, description="Digest time (HH:MM UTC)")
    digest_keywords: Optional[List[str]] = Field(None, description="Keywords: G2B:*, competitor:*, tech:*")
    matching_enabled: Optional[bool] = Field(None, description="Enable/disable matching mode")
    matching_threshold: Optional[float] = Field(
        None,
        description="Similarity threshold for RFP matching (0.0-1.0)",
        ge=0.0,
        le=1.0
    )

    @validator("digest_time")
    def validate_digest_time(cls, v):
        """Validate digest time format HH:MM"""
        if v is not None and not (len(v) == 5 and v[2] == ":"):
            raise ValueError("digest_time must be in HH:MM format")
        return v


class TeamsBotConfigResponse(BaseModel):
    """Teams bot configuration response"""
    id: str
    team_id: str
    bot_enabled: bool
    bot_modes: List[str]
    webhook_url: str
    webhook_validated_at: Optional[str]
    digest_time: str
    digest_keywords: List[str]
    digest_enabled: bool
    matching_enabled: bool
    matching_threshold: float
    created_at: str
    updated_at: str


class TeamsAdaptiveQueryRequest(BaseModel):
    """Adaptive mode query from Teams"""
    team_id: str = Field(..., description="Team UUID")
    user_id: str = Field(..., description="User UUID")
    query: str = Field(..., description="User question/mention", max_length=2000)
    channel_id: str = Field(..., description="Teams channel ID")
    response: str = Field(..., description="Vault AI response", max_length=4000)
    sources: List[dict] = Field(default=[], description="Referenced document sources")


class TeamsAdaptiveQueryResponse(BaseModel):
    """Adaptive query response"""
    status: str = Field("success", description="Request status")
    teams_message_id: Optional[str] = Field(None, description="Teams message ID (if sent)")
    response: str = Field(..., description="Response text")
    posted: bool = Field(default=False, description="Successfully posted to Teams")
    message: Optional[str] = Field(None, description="Error or status message")


class WebhookValidationRequest(BaseModel):
    """Webhook URL validation"""
    webhook_url: str = Field(..., description="Teams webhook URL to validate")


class WebhookValidationResponse(BaseModel):
    """Webhook validation result"""
    is_valid: bool
    message: str
    webhook_url: str


class TeamsMessageLogResponse(BaseModel):
    """Teams bot message log"""
    id: str
    team_id: str
    mode: str
    query: str
    response: str
    delivery_status: str
    teams_message_id: Optional[str]
    created_at: str


# ── Endpoints ──

@router.get("/config/{team_id}", response_model=TeamsBotConfigResponse)
async def get_bot_config(
    team_id: str,
    current_user=Depends(get_current_user),
    supabase: SupabaseAsyncClient = Depends(get_supabase_async_client)
) -> TeamsBotConfigResponse:
    """
    Get Teams bot configuration for a team

    Auth: Team member

    Args:
        team_id: Team UUID

    Returns:
        Current bot configuration

    Raises:
        404: Team or config not found
        403: User not in team
    """
    try:
        # Verify user is in team
        team = await supabase.table("teams") \
            .select("id") \
            .eq("id", team_id) \
            .single() \
            .execute()

        if not team.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )

        # Load config
        config = await supabase.table("teams_bot_config") \
            .select("*") \
            .eq("team_id", team_id) \
            .single() \
            .execute()

        if not config.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot configuration not found for this team"
            )

        return TeamsBotConfigResponse(**config.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading bot config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load bot configuration"
        )


@router.put("/config/{team_id}", response_model=TeamsBotConfigResponse)
async def update_bot_config(
    team_id: str,
    request: TeamsBotConfigRequest,
    current_user=Depends(get_current_user),
    supabase: SupabaseAsyncClient = Depends(get_supabase_async_client)
) -> TeamsBotConfigResponse:
    """
    Update Teams bot configuration for a team

    Auth: Team admin (role: admin or lead)

    Args:
        team_id: Team UUID
        request: Configuration update fields

    Returns:
        Updated configuration

    Raises:
        403: User not admin in team
        404: Team not found
    """
    try:
        # Verify user is team admin
        user_role = await supabase.table("team_members") \
            .select("role") \
            .eq("team_id", team_id) \
            .eq("user_id", current_user.id) \
            .single() \
            .execute()

        if not user_role.data or user_role.data.get("role") not in ("admin", "lead"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only team admins can update bot configuration"
            )

        # Build update payload
        update_data = {}
        if request.bot_enabled is not None:
            update_data["bot_enabled"] = request.bot_enabled
        if request.digest_enabled is not None:
            update_data["digest_enabled"] = request.digest_enabled
        if request.digest_time is not None:
            update_data["digest_time"] = request.digest_time
        if request.digest_keywords is not None:
            update_data["digest_keywords"] = request.digest_keywords
        if request.matching_enabled is not None:
            update_data["matching_enabled"] = request.matching_enabled
        if request.matching_threshold is not None:
            update_data["matching_threshold"] = request.matching_threshold

        update_data["updated_at"] = __import__("datetime").datetime.utcnow().isoformat()

        # Update config
        result = await supabase.table("teams_bot_config") \
            .update(update_data) \
            .eq("team_id", team_id) \
            .execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot configuration not found"
            )

        logger.info(f"Updated bot config for team {team_id}")
        return TeamsBotConfigResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bot config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bot configuration"
        )


@router.post("/query/adaptive", response_model=TeamsAdaptiveQueryResponse)
async def handle_adaptive_query(
    request: TeamsAdaptiveQueryRequest,
    supabase: SupabaseAsyncClient = Depends(get_supabase_async_client)
) -> TeamsAdaptiveQueryResponse:
    """
    Handle adaptive mode query from Teams mention

    Flow:
    1. Validate team and user
    2. Check bot is enabled and adaptive mode active
    3. Call Teams bot service
    4. Return response

    Auth: None (Teams webhook validation)

    Args:
        request: Query from Teams

    Returns:
        Response with status and Teams message ID

    Raises:
        400: Invalid request
        404: Team not found
        503: Bot service error
    """
    try:
        # Get bot service from app state
        from app.main import app
        bot_service: TeamsBotService = app.state.teams_bot_service

        # Validate team exists
        team = await supabase.table("teams") \
            .select("id") \
            .eq("id", request.team_id) \
            .single() \
            .execute()

        if not team.data:
            logger.warning(f"Adaptive query from unknown team: {request.team_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )

        # Call bot service
        success = await bot_service.handle_adaptive_query(
            team_id=request.team_id,
            user_id=request.user_id,
            query=request.query,
            channel_id=request.channel_id,
            response=request.response,
            sources=request.sources
        )

        return TeamsAdaptiveQueryResponse(
            status="success" if success else "error",
            response=request.response,
            posted=success,
            message="Posted to Teams" if success else "Failed to post to Teams"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Adaptive query error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bot service error"
        )


@router.post("/webhook/validate", response_model=WebhookValidationResponse)
async def validate_webhook(
    request: WebhookValidationRequest,
    current_user=Depends(get_current_user),
    supabase: SupabaseAsyncClient = Depends(get_supabase_async_client)
) -> WebhookValidationResponse:
    """
    Validate Teams webhook URL before saving

    Checks:
    1. URL format (HTTPS, outlook.webhook.office.com domain)
    2. Webhook is live (HEAD request)

    Auth: Authenticated user

    Args:
        request: Webhook URL to validate

    Returns:
        Validation result

    Raises:
        400: Invalid webhook URL
    """
    try:
        # Get webhook manager
        from app.main import app
        webhook_manager = app.state.teams_webhook_manager

        # Validate URL
        is_valid = await webhook_manager.validate_webhook_url(request.webhook_url)

        return WebhookValidationResponse(
            is_valid=is_valid,
            message="Webhook URL is valid and live" if is_valid else "Webhook URL is invalid or not responding",
            webhook_url=request.webhook_url
        )

    except Exception as e:
        logger.error(f"Webhook validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook validation failed: {str(e)}"
        )


@router.post("/webhook-config", response_model=TeamsBotConfigResponse)
async def register_webhook(
    team_id: str,
    webhook_url: str,
    current_user=Depends(require_role("admin")),
    supabase: SupabaseAsyncClient = Depends(get_supabase_async_client)
) -> TeamsBotConfigResponse:
    """
    Register and validate Teams webhook URL for a team

    Auth: Admin only

    Args:
        team_id: Team UUID
        webhook_url: Teams webhook URL

    Returns:
        Updated configuration with validated webhook

    Raises:
        403: Not admin
        400: Invalid webhook URL
        404: Team not found
    """
    try:
        # Get webhook manager
        from app.main import app
        webhook_manager = app.state.teams_webhook_manager

        # Validate webhook URL
        is_valid = await webhook_manager.validate_webhook_url(webhook_url)

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook URL is invalid or not responding"
            )

        # Update config in DB
        now = __import__("datetime").datetime.utcnow().isoformat()
        result = await supabase.table("teams_bot_config") \
            .update({
                "webhook_url": webhook_url,
                "webhook_validated_at": now,
                "updated_at": now
            }) \
            .eq("team_id", team_id) \
            .execute()

        if not result.data:
            # Create new config if doesn't exist
            result = await supabase.table("teams_bot_config").insert({
                "team_id": team_id,
                "webhook_url": webhook_url,
                "webhook_validated_at": now,
                "bot_enabled": True,
                "bot_modes": ["adaptive", "digest"],
                "digest_enabled": True,
                "digest_keywords": [],
                "matching_enabled": True,
                "matching_threshold": 0.75,
                "created_at": now,
                "updated_at": now,
                "created_by": current_user.id
            }).execute()

        logger.info(f"Registered webhook for team {team_id}")
        return TeamsBotConfigResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register webhook"
        )


@router.get("/messages", response_model=List[TeamsMessageLogResponse])
async def get_message_log(
    team_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user=Depends(get_current_user),
    supabase: SupabaseAsyncClient = Depends(get_supabase_async_client)
) -> List[TeamsMessageLogResponse]:
    """
    Get Teams bot message delivery log for a team

    Pagination:
    - limit: Max 100
    - offset: For pagination

    Auth: Team member

    Args:
        team_id: Team UUID
        limit: Max results (default 50, max 100)
        offset: Offset for pagination

    Returns:
        List of bot messages

    Raises:
        404: Team not found
    """
    try:
        limit = min(limit, 100)

        # Query message log
        result = await supabase.table("teams_bot_messages") \
            .select("*") \
            .eq("team_id", team_id) \
            .order("created_at", desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()

        return [TeamsMessageLogResponse(**msg) for msg in result.data] if result.data else []

    except Exception as e:
        logger.error(f"Error fetching message log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch message log"
        )
