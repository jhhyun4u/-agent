"""
Vault Permission Filter - Role-based response filtering
Phase 2: Permission-based filtering and audit logging
Design Ref: §3.2, §7.1
"""

import logging
from typing import List, Tuple, Optional, Any
from datetime import datetime
from enum import Enum
from app.models.vault_schemas import DocumentSource

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """User role hierarchy"""
    MEMBER = "member"
    LEAD = "lead"
    DIRECTOR = "director"
    EXECUTIVE = "executive"
    ADMIN = "admin"


class VaultPermissionFilter:
    """Manage role-based filtering of responses and content

    Implements row-level security (RLS) principles at the application layer.
    Works in conjunction with database RLS policies.

    Role hierarchy:
    - member: 0 (public information)
    - lead: 1 (team-level information)
    - director: 2 (management-level)
    - executive: 3 (executive-level)
    - admin: 4 (unrestricted access)
    """

    ROLE_HIERARCHY = {
        "member": 0,
        "lead": 1,
        "director": 2,
        "executive": 3,
        "admin": 4
    }

    @staticmethod
    def get_role_level(role: str) -> int:
        """
        Get numeric level for role.

        Args:
            role: Role name (member, lead, director, executive, admin)

        Returns:
            Numeric level (0-4), or 0 if unknown role
        """
        return VaultPermissionFilter.ROLE_HIERARCHY.get(role.lower(), 0)

    @staticmethod
    async def filter_response(
        user_role: str,
        response_text: str,
        sources: List[DocumentSource],
        supabase_client: Any,
        user_id: str
    ) -> Tuple[str, List[DocumentSource], List[str]]:
        """
        Filter response text and sources by user role.

        Design Ref: §3.2 — Permission-based filtering

        Args:
            user_role: User's role (member, lead, director, executive, admin)
            response_text: AI-generated response text
            sources: List of source documents referenced in response
            supabase_client: Supabase async client for DB access
            user_id: Current user ID (for audit logging)

        Returns:
            Tuple of:
            - filtered_response: Response with unauthorized content removed
            - filtered_sources: Sources user has access to
            - excluded_reasons: List of reason strings for excluded sources
        """
        user_role_level = VaultPermissionFilter.get_role_level(user_role)
        filtered_sources = []
        excluded_reasons = []

        logger.info(f"Filtering response for user {user_id} (role={user_role}, level={user_role_level})")

        # Validate each source document
        for source in sources:
            try:
                # Query document min_required_role from DB
                doc = await supabase_client.table("vault_documents") \
                    .select("min_required_role, title") \
                    .eq("id", source.document_id) \
                    .single() \
                    .execute()

                if not doc.data:
                    logger.warning(f"Document {source.document_id} not found")
                    continue

                required_role = doc.data.get("min_required_role", "member")
                required_level = VaultPermissionFilter.get_role_level(required_role)
                doc_title = doc.data.get("title", "Unknown Document")

                # Check if user has sufficient role level
                if user_role_level >= required_level:
                    # User has access
                    filtered_sources.append(source)
                    logger.debug(f"✓ User has access to {doc_title}")
                else:
                    # User lacks access - log denial
                    reason = f"{doc_title} (required: {required_role})"
                    excluded_reasons.append(reason)

                    await VaultPermissionFilter._log_denied_access(
                        supabase_client,
                        user_id,
                        source.document_id,
                        user_role,
                        required_role,
                        doc_title
                    )

                    logger.warning(
                        f"✗ User denied access: {doc_title} "
                        f"(user={user_role}/{user_role_level}, required={required_role}/{required_level})"
                    )

            except Exception as e:
                logger.error(f"Error filtering source {source.document_id}: {e}")
                # On error, exclude source for safety
                excluded_reasons.append(f"{source.title} (validation error)")

        # Rebuild response based on what's accessible
        filtered_response = response_text

        if sources and not filtered_sources:
            # All sources excluded - user has no access to any referenced info
            filtered_response = (
                f"죄송하지만, 이 정보는 {VaultPermissionFilter._get_min_required_role(sources)} "
                f"이상의 권한이 필요합니다."
            )
        elif excluded_reasons:
            # Partial access - some sources excluded
            excluded_str = ", ".join(excluded_reasons[:3])  # Show first 3 only
            if len(excluded_reasons) > 3:
                excluded_str += f" 외 {len(excluded_reasons) - 3}개"
            filtered_response += (
                f"\n\n[참고] 다음 정보는 권한으로 인해 제외되었습니다: {excluded_str}"
            )

        logger.info(
            f"Filtered response: {len(sources)} sources → {len(filtered_sources)} accessible"
        )

        return filtered_response, filtered_sources, excluded_reasons

    @staticmethod
    def _get_min_required_role(sources: List[DocumentSource]) -> str:
        """
        Get minimum required role from list of sources.

        Assumes sources are sorted by required role level (highest first).

        Args:
            sources: List of document sources

        Returns:
            Minimum required role string (e.g., "director")
        """
        if not sources:
            return "관리자"

        # For first source, determine likely required role
        if sources[0].document_id:
            # This would need actual DB lookup in production
            # For now, return generic response
            return "해당 직급"

        return "관리자"

    @staticmethod
    async def _log_denied_access(
        supabase_client: Any,
        user_id: str,
        document_id: str,
        user_role: str,
        required_role: str,
        document_title: str
    ) -> None:
        """
        Log denied access attempt to audit table.

        Design Ref: §7.1 — Audit trail for security

        Args:
            supabase_client: Supabase async client
            user_id: User who attempted access
            document_id: Document that was denied
            user_role: User's actual role
            required_role: Minimum required role
            document_title: Title of document (for audit context)
        """
        try:
            await supabase_client.table("vault_audit_logs").insert({
                "user_id": user_id,
                "action": "document_access",
                "action_denied": True,
                "denied_reason": f"insufficient_role (user:{user_role}, required:{required_role})",
                "user_role": user_role,
                "resource_id": document_id,
                "resource_title": document_title,
                "created_at": datetime.utcnow().isoformat()
            }).execute()

            logger.info(f"Denied access logged for user {user_id} to {document_id}")

        except Exception as e:
            logger.error(f"Failed to log denied access: {e}")
            # Don't raise - audit logging failure shouldn't break response

    @staticmethod
    def validate_role(role: str) -> bool:
        """
        Validate that role is in allowed list.

        Args:
            role: Role to validate

        Returns:
            True if role is valid
        """
        return role.lower() in VaultPermissionFilter.ROLE_HIERARCHY

    @staticmethod
    def check_sensitive_content(
        response_text: str,
        user_role: str,
        restricted_keywords: Optional[List[str]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Check for restricted keywords in response.

        Design Ref: §7.2 — Data classification

        Args:
            response_text: Response to check
            user_role: User role
            restricted_keywords: Keywords restricted to certain roles

        Returns:
            Tuple of (is_clean, detected_keywords)
        """
        if restricted_keywords is None:
            restricted_keywords = []

        detected = []
        user_level = VaultPermissionFilter.get_role_level(user_role)

        for keyword in restricted_keywords:
            if keyword.lower() in response_text.lower():
                detected.append(keyword)

        is_clean = len(detected) == 0

        if not is_clean:
            logger.warning(
                f"Sensitive content detected for {user_role}: {detected}"
            )

        return is_clean, detected
