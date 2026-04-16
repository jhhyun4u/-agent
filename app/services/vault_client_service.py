"""
Vault Client Service — 발주처 (Issuing Agency/Client) Management
Handles client information, performance tracking, and relationship management.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel

from app.utils.supabase_client import supabase

logger = logging.getLogger(__name__)


class ClientPerformanceMetrics(BaseModel):
    """Client performance metrics"""
    win_count: int = 0
    loss_count: int = 0
    total_bid_count: int = 0
    win_rate: Decimal = Decimal(0)
    avg_bid_amount: Optional[int] = None
    first_bid_date: Optional[str] = None
    last_bid_date: Optional[str] = None
    last_win_date: Optional[str] = None


class ClientInfo(BaseModel):
    """Client information with performance"""
    id: str
    agency_name: str
    agency_id: Optional[str] = None
    agency_code: Optional[str] = None
    agency_type: Optional[str] = None
    region: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    relationship_notes: Optional[str] = None
    lessons_learned: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    metrics: ClientPerformanceMetrics


class VaultClientService:
    """Service for managing vault clients"""

    AGENCY_TYPES = [
        "중앙부처",
        "지자체",
        "공기업",
        "민간기업",
        "기타"
    ]

    PERFORMANCE_TIERS = {
        "no_history": "제출 이력 없음",
        "excellent": "우수 (80%+ 낙찰)",
        "good": "양호 (60~79% 낙찰)",
        "fair": "보통 (40~59% 낙찰)",
        "poor": "미흡 (20~39% 낙찰)",
        "very_poor": "부진 (<20% 낙찰)"
    }

    @staticmethod
    async def get_client(
        client_id: UUID,
        include_history: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieve detailed client information.

        Args:
            client_id: Client UUID
            include_history: Whether to include proposal history

        Returns:
            Client info with metrics and optional history
        """
        try:
            response = supabase.table("vault_clients").select("*").eq("id", str(client_id)).execute()
            client = response.data[0] if response.data else None

            if not client:
                raise ValueError(f"Client not found: {client_id}")

            # Add performance tier
            tier = VaultClientService._calculate_performance_tier(
                client.get("win_rate", 0),
                client.get("total_bid_count", 0)
            )
            client["performance_tier"] = tier
            client["performance_tier_label"] = VaultClientService.PERFORMANCE_TIERS.get(tier, "알 수 없음")

            # Add proposal history if requested
            if include_history:
                history_response = supabase.table("proposals")\
                    .select("id,title,status,budget,created_at")\
                    .ilike("client_name", client["agency_name"])\
                    .order("created_at", desc=True)\
                    .limit(20)\
                    .execute()

                client["proposal_history"] = history_response.data or []

            logger.info(f"Retrieved client: {client['agency_name']} ({client_id})")
            return client

        except Exception as e:
            logger.error(f"Failed to get client: {str(e)}")
            raise

    @staticmethod
    async def search_clients(
        query: str,
        limit: int = 20,
        offset: int = 0,
        agency_type: Optional[str] = None,
        region: Optional[str] = None,
        min_win_rate: Optional[Decimal] = None,
        sort_by: str = "win_rate"  # win_rate, last_bid_date, agency_name
    ) -> Dict[str, Any]:
        """
        Search for clients with filters.

        Args:
            query: Search query (agency name, contact info)
            limit: Results per page
            offset: Pagination offset
            agency_type: Filter by agency type
            region: Filter by region
            min_win_rate: Filter by minimum win rate
            sort_by: Sort field (win_rate, last_bid_date, agency_name)

        Returns:
            Paginated search results
        """
        try:
            # Build query
            select_query = supabase.table("vault_clients").select("*")

            # Text search
            if query:
                select_query = select_query.or_(
                    f"agency_name.ilike.%{query}%,contact_person.ilike.%{query}%,contact_email.ilike.%{query}%"
                )

            # Filters
            if agency_type:
                select_query = select_query.eq("agency_type", agency_type)
            if region:
                select_query = select_query.eq("region", region)
            if min_win_rate is not None:
                select_query = select_query.gte("win_rate", float(min_win_rate))

            # Soft delete filter
            select_query = select_query.is_("deleted_at", "null")

            # Sort
            if sort_by == "win_rate":
                select_query = select_query.order("win_rate", desc=True)
            elif sort_by == "last_bid_date":
                select_query = select_query.order("last_bid_date", desc=True)
            else:
                select_query = select_query.order("agency_name", desc=False)

            # Pagination
            select_query = select_query.range(offset, offset + limit - 1)

            results = select_query.execute()
            clients = results.data or []

            # Add performance tier to each client
            for client in clients:
                client["performance_tier"] = VaultClientService._calculate_performance_tier(
                    client.get("win_rate", 0),
                    client.get("total_bid_count", 0)
                )

            # Count total
            count_response = supabase.table("vault_clients").select("id", count="exact")\
                .is_("deleted_at", "null")\
                .execute()

            return {
                "clients": clients,
                "total": count_response.count or 0,
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            logger.error(f"Client search failed: {str(e)}")
            raise

    @staticmethod
    async def get_client_by_name(agency_name: str) -> Optional[Dict[str, Any]]:
        """
        Get client by agency name (creates if not exists).

        Args:
            agency_name: Name of the issuing agency

        Returns:
            Client record or None
        """
        try:
            # Try to find existing client
            response = supabase.table("vault_clients")\
                .select("*")\
                .ilike("agency_name", agency_name)\
                .is_("deleted_at", "null")\
                .limit(1)\
                .execute()

            if response.data:
                return response.data[0]

            # Create new client if not found
            new_client = {
                "agency_name": agency_name,
                "created_at": datetime.now().isoformat()
            }

            create_response = supabase.table("vault_clients").insert(new_client).execute()
            client = create_response.data[0] if create_response.data else None

            logger.info(f"Created new client: {agency_name}")
            return client

        except Exception as e:
            logger.error(f"Failed to get/create client: {str(e)}")
            raise

    @staticmethod
    async def update_client_info(
        client_id: UUID,
        contact_person: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        relationship_notes: Optional[str] = None,
        lessons_learned: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        agency_type: Optional[str] = None,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update client information (manual fields).

        These are user-maintained fields, not auto-updated by triggers.
        """
        try:
            update_data = {}

            if contact_person is not None:
                update_data["contact_person"] = contact_person
            if contact_email is not None:
                update_data["contact_email"] = contact_email
            if contact_phone is not None:
                update_data["contact_phone"] = contact_phone
            if relationship_notes is not None:
                update_data["relationship_notes"] = relationship_notes
            if lessons_learned is not None:
                update_data["lessons_learned"] = lessons_learned
            if preferences is not None:
                update_data["preferences"] = preferences
            if agency_type is not None:
                update_data["agency_type"] = agency_type
            if region is not None:
                update_data["region"] = region

            update_data["updated_at"] = datetime.now().isoformat()

            response = supabase.table("vault_clients").update(update_data).eq("id", str(client_id)).execute()
            client = response.data[0] if response.data else None

            if not client:
                raise ValueError(f"Failed to update client: {client_id}")

            logger.info(f"Updated client info: {client_id}")
            return client

        except Exception as e:
            logger.error(f"Failed to update client info: {str(e)}")
            raise

    @staticmethod
    async def add_review(
        client_id: UUID,
        review_notes: str,
        reviewed_by: UUID
    ) -> Dict[str, Any]:
        """
        Add a review/audit note for the client relationship.

        Args:
            client_id: Client UUID
            review_notes: Review content
            reviewed_by: User ID who performed review

        Returns:
            Updated client record
        """
        try:
            update_data = {
                "review_notes": review_notes,
                "last_review_date": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            response = supabase.table("vault_clients").update(update_data).eq("id", str(client_id)).execute()
            client = response.data[0] if response.data else None

            logger.info(f"Added review for client: {client_id} by {reviewed_by}")
            return client

        except Exception as e:
            logger.error(f"Failed to add review: {str(e)}")
            raise

    @staticmethod
    async def get_client_proposals(
        client_id: UUID,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get all proposals for a client.

        Args:
            client_id: Client UUID
            status: Filter by proposal status (won, lost, submitted)
            limit: Results per page
            offset: Pagination offset

        Returns:
            List of proposals with pagination
        """
        try:
            client_response = supabase.table("vault_clients").select("agency_name").eq("id", str(client_id)).execute()
            client = client_response.data[0] if client_response.data else None

            if not client:
                raise ValueError(f"Client not found: {client_id}")

            agency_name = client["agency_name"]

            # Query proposals
            query = supabase.table("proposals")\
                .select("id,title,status,budget,created_at,updated_at")\
                .ilike("client_name", agency_name)

            if status:
                query = query.eq("status", status)

            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

            results = query.execute()
            proposals = results.data or []

            # Count total
            count_query = supabase.table("proposals")\
                .select("id", count="exact")\
                .ilike("client_name", agency_name)

            if status:
                count_query = count_query.eq("status", status)

            count_response = count_query.execute()

            return {
                "client_id": str(client_id),
                "agency_name": agency_name,
                "proposals": proposals,
                "total": count_response.count or 0,
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            logger.error(f"Failed to get client proposals: {str(e)}")
            raise

    @staticmethod
    async def get_top_clients(
        limit: int = 20,
        metric: str = "win_rate"  # win_rate, total_bid_count, avg_bid_amount
    ) -> List[Dict[str, Any]]:
        """
        Get top-performing clients by various metrics.

        Args:
            limit: Number of clients to return
            metric: Ranking metric (win_rate, total_bid_count, avg_bid_amount)

        Returns:
            Top clients sorted by metric
        """
        try:
            if metric == "win_rate":
                order_field = "win_rate"
            elif metric == "total_bid_count":
                order_field = "total_bid_count"
            elif metric == "avg_bid_amount":
                order_field = "avg_bid_amount"
            else:
                order_field = "win_rate"

            response = supabase.table("vault_clients")\
                .select("*")\
                .is_("deleted_at", "null")\
                .gt("total_bid_count", 0)\
                .order(order_field, desc=True)\
                .limit(limit)\
                .execute()

            clients = response.data or []

            # Add performance tier
            for client in clients:
                client["performance_tier"] = VaultClientService._calculate_performance_tier(
                    client.get("win_rate", 0),
                    client.get("total_bid_count", 0)
                )

            return clients

        except Exception as e:
            logger.error(f"Failed to get top clients: {str(e)}")
            raise

    @staticmethod
    async def get_regional_summary(region: str) -> Dict[str, Any]:
        """
        Get aggregated client statistics for a region.

        Args:
            region: Region code or name

        Returns:
            Regional statistics
        """
        try:
            response = supabase.table("vault_clients")\
                .select("*")\
                .eq("region", region)\
                .is_("deleted_at", "null")\
                .execute()

            clients = response.data or []

            total_win_count = sum(c.get("win_count", 0) for c in clients)
            total_bid_count = sum(c.get("total_bid_count", 0) for c in clients)
            total_avg_bid = sum(c.get("avg_bid_amount", 0) or 0 for c in clients) / len(clients) if clients else 0

            regional_win_rate = (total_win_count / total_bid_count * 100) if total_bid_count > 0 else 0

            return {
                "region": region,
                "client_count": len(clients),
                "total_win_count": total_win_count,
                "total_bid_count": total_bid_count,
                "regional_win_rate": round(regional_win_rate, 2),
                "avg_bid_amount": round(total_avg_bid, 0),
                "clients": clients
            }

        except Exception as e:
            logger.error(f"Failed to get regional summary: {str(e)}")
            raise

    @staticmethod
    async def delete_client(client_id: UUID) -> Dict[str, Any]:
        """
        Soft-delete a client record.

        Args:
            client_id: Client to delete

        Returns:
            Updated client with deletion timestamp
        """
        try:
            update_data = {"deleted_at": datetime.now().isoformat()}
            response = supabase.table("vault_clients").update(update_data).eq("id", str(client_id)).execute()
            client = response.data[0] if response.data else None

            logger.info(f"Deleted client: {client_id}")
            return client

        except Exception as e:
            logger.error(f"Failed to delete client: {str(e)}")
            raise

    @staticmethod
    def _calculate_performance_tier(win_rate: float, total_bid_count: int) -> str:
        """
        Calculate performance tier based on win rate and bid count.

        Returns:
            Performance tier: no_history, excellent, good, fair, poor, very_poor
        """
        if total_bid_count == 0:
            return "no_history"
        elif win_rate >= 80:
            return "excellent"
        elif win_rate >= 60:
            return "good"
        elif win_rate >= 40:
            return "fair"
        elif win_rate >= 20:
            return "poor"
        else:
            return "very_poor"
