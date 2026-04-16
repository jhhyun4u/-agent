"""
Vault Clients API — 발주처 (Issuing Agency/Client) Management Routes
Endpoints for managing client information, performance tracking, and relationships.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.models.user_schemas import UserInDB
from app.services.vault_client_service import VaultClientService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vault/clients", tags=["vault-clients"])


# ============================================
# Request/Response Models
# ============================================

class ClientPerformanceMetricsResponse(BaseModel):
    """Client performance metrics"""
    win_count: int
    loss_count: int
    total_bid_count: int
    win_rate: Decimal
    avg_bid_amount: Optional[int]
    first_bid_date: Optional[str]
    last_bid_date: Optional[str]
    last_win_date: Optional[str]


class ClientResponse(BaseModel):
    """Client record response"""
    id: str
    agency_name: str
    agency_id: Optional[str]
    agency_code: Optional[str]
    agency_type: Optional[str]
    region: Optional[str]
    contact_person: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    relationship_notes: Optional[str]
    lessons_learned: Optional[str]
    preferences: Optional[Dict[str, Any]]
    win_count: int
    loss_count: int
    total_bid_count: int
    win_rate: Decimal
    avg_bid_amount: Optional[int]
    performance_tier: Optional[str]
    performance_tier_label: Optional[str]
    last_bid_date: Optional[str]
    created_at: str
    updated_at: str


class ClientSearchRequest(BaseModel):
    """Client search request"""
    query: str = Field(..., min_length=1)
    agency_type: Optional[str] = None
    region: Optional[str] = None
    min_win_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    sort_by: str = Field("win_rate", regex="^(win_rate|last_bid_date|agency_name)$")
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class ClientUpdateRequest(BaseModel):
    """Update client information"""
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    relationship_notes: Optional[str] = None
    lessons_learned: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    agency_type: Optional[str] = None
    region: Optional[str] = None


class ClientReviewRequest(BaseModel):
    """Add review for client"""
    review_notes: str = Field(..., min_length=1, max_length=1000)


class ClientListResponse(BaseModel):
    """List clients response"""
    clients: list[ClientResponse]
    total: int
    limit: int
    offset: int


class ClientProposalsResponse(BaseModel):
    """List client's proposals response"""
    client_id: str
    agency_name: str
    proposals: list[Dict[str, Any]]
    total: int
    limit: int
    offset: int


class RegionalSummaryResponse(BaseModel):
    """Regional client statistics"""
    region: str
    client_count: int
    total_win_count: int
    total_bid_count: int
    regional_win_rate: Decimal
    avg_bid_amount: int
    clients: list[ClientResponse]


# ============================================
# Endpoints
# ============================================

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    include_history: bool = Query(False),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get detailed client information.

    Args:
        client_id: Client UUID
        include_history: Include 20 most recent proposals

    Returns:
        Client with performance metrics and optional history
    """
    try:
        client = await VaultClientService.get_client(
            UUID(client_id),
            include_history=include_history
        )
        return ClientResponse(**client)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch client: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch client")


@router.post("/search", response_model=ClientListResponse)
async def search_clients(
    request: ClientSearchRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Search for clients with filtering and sorting.

    Supports:
    - Text search on agency name, contact person, email
    - Filter by agency type, region, minimum win rate
    - Sort by win_rate, last_bid_date, or agency_name

    Returns:
        Paginated search results with performance metrics
    """
    try:
        result = await VaultClientService.search_clients(
            query=request.query,
            limit=request.limit,
            offset=request.offset,
            agency_type=request.agency_type,
            region=request.region,
            min_win_rate=request.min_win_rate,
            sort_by=request.sort_by
        )

        return ClientListResponse(**result)

    except Exception as e:
        logger.error(f"Client search failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/by-name/{agency_name}")
async def get_client_by_name(
    agency_name: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get or create client by agency name.

    If client exists, returns existing record.
    If not, creates new client with this name.

    Args:
        agency_name: Official name of the issuing agency

    Returns:
        Client record
    """
    try:
        client = await VaultClientService.get_client_by_name(agency_name)

        if not client:
            raise HTTPException(status_code=500, detail="Failed to get/create client")

        return ClientResponse(**client)

    except Exception as e:
        logger.error(f"Failed to get client by name: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get/create client")


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    request: ClientUpdateRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Update client information (manual fields).

    These are user-maintained fields (not auto-updated by triggers):
    - contact_person, contact_email, contact_phone
    - relationship_notes, lessons_learned
    - preferences, agency_type, region

    Args:
        client_id: Client UUID
        request: Fields to update

    Returns:
        Updated client record
    """
    try:
        client = await VaultClientService.update_client_info(
            UUID(client_id),
            contact_person=request.contact_person,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            relationship_notes=request.relationship_notes,
            lessons_learned=request.lessons_learned,
            preferences=request.preferences,
            agency_type=request.agency_type,
            region=request.region
        )

        return ClientResponse(**client)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update client: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update client")


@router.post("/{client_id}/review", response_model=ClientResponse)
async def add_client_review(
    client_id: str,
    request: ClientReviewRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Add review notes to client relationship.

    Used for audit trail and documenting observations about
    working relationship, preferences, or lessons learned.

    Args:
        client_id: Client UUID
        request: Review notes

    Returns:
        Updated client record
    """
    try:
        client = await VaultClientService.add_review(
            UUID(client_id),
            request.review_notes,
            UUID(current_user.id)
        )

        return ClientResponse(**client)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add review: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add review")


@router.get("/{client_id}/proposals", response_model=ClientProposalsResponse)
async def get_client_proposals(
    client_id: str,
    status: Optional[str] = Query(None, regex="^(won|lost|submitted)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get all proposals for a specific client.

    Returns all proposals (won, lost, submitted) grouped by client.
    Useful for historical analysis and win-loss trends.

    Args:
        client_id: Client UUID
        status: Filter by proposal status (won, lost, submitted)
        limit: Results per page
        offset: Pagination offset

    Returns:
        Paginated list of proposals for this client
    """
    try:
        result = await VaultClientService.get_client_proposals(
            UUID(client_id),
            status=status,
            limit=limit,
            offset=offset
        )

        return ClientProposalsResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get client proposals: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get proposals")


@router.get("/top/by-metric", response_model=list[ClientResponse])
async def get_top_clients(
    metric: str = Query("win_rate", regex="^(win_rate|total_bid_count|avg_bid_amount)$"),
    limit: int = Query(20, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get top-performing clients by various metrics.

    Metrics:
    - win_rate: Highest success rate on proposals
    - total_bid_count: Most proposals submitted to
    - avg_bid_amount: Highest average bid amounts

    Args:
        metric: Ranking metric
        limit: Number of clients to return

    Returns:
        Sorted list of top clients
    """
    try:
        clients = await VaultClientService.get_top_clients(limit=limit, metric=metric)
        return [ClientResponse(**c) for c in clients]

    except Exception as e:
        logger.error(f"Failed to get top clients: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get top clients")


@router.get("/region/{region}/summary", response_model=RegionalSummaryResponse)
async def get_regional_summary(
    region: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get aggregated client statistics for a region.

    Useful for understanding regional market dynamics and
    identifying which regions have highest win rates.

    Args:
        region: Region code or name (e.g., 서울, 경기, 부산)

    Returns:
        Regional summary with client statistics
    """
    try:
        summary = await VaultClientService.get_regional_summary(region)
        return RegionalSummaryResponse(**summary)

    except Exception as e:
        logger.error(f"Failed to get regional summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get regional summary")


@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Soft-delete a client record.

    Note: Records are soft-deleted (marked deleted_at) to preserve audit trail.

    Args:
        client_id: Client to delete

    Returns:
        Deletion confirmation
    """
    try:
        result = await VaultClientService.delete_client(UUID(client_id))

        if not result:
            raise HTTPException(status_code=404, detail="Client not found")

        return {"status": "deleted", "id": client_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete client: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete client")


@router.get("/types", response_model=list[str])
async def get_agency_types():
    """
    Get list of supported agency types.

    Returns:
        Valid agency_type values
    """
    return VaultClientService.AGENCY_TYPES
