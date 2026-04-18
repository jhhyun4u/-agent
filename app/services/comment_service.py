"""
Comment Service Layer

Handles CRUD operations, RLS enforcement, and notification dispatch.
All database operations are RLS-enforced via the Supabase client.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple, List

from app.models.comment_schemas import (
    CommentScope,
    CommentResponse,
    AuthorInfo,
)


logger = logging.getLogger(__name__)


class CommentService:
    """Service for managing proposal comments and reactions"""

    def __init__(self, db, user: dict):
        """
        Initialize service with RLS-enforced database client

        Args:
            db: Supabase async client with RLS enforced for current user
            user: Current authenticated user dict (from get_current_user)
        """
        self.db = db
        self.user = user
        self.user_id = user.get("id")
        self.org_id = user.get("org_id")

    # ============================================
    # Comment CRUD Operations
    # ============================================

    async def create_comment(
        self,
        proposal_id: str,
        scope: CommentScope,
        content: str,
        proposal_step: Optional[str] = None,
        inline_position: Optional[int] = None,
    ) -> CommentResponse:
        """
        Create a new comment

        Args:
            proposal_id: UUID of proposal
            scope: 'global' | 'step' | 'inline'
            content: Comment text (Markdown supported)
            proposal_step: Step name if scope is 'step'
            inline_position: Character offset if scope is 'inline'

        Returns:
            CommentResponse with created comment details

        Raises:
            ValueError: Invalid scope/position combination
            PermissionError: Not a proposal member
        """
        # Validate scope/position combination
        if scope == "step" and not proposal_step:
            raise ValueError("proposal_step required for step-scoped comments")
        if scope == "inline" and inline_position is None:
            raise ValueError("inline_position required for inline comments")

        # Verify user is proposal member
        await self._verify_proposal_member(proposal_id)

        # Insert comment
        response = await self.db.table("comments").insert({
            "proposal_id": proposal_id,
            "author_id": self.user_id,
            "org_id": self.org_id,
            "scope": scope.value,
            "proposal_step": proposal_step,
            "inline_position": inline_position,
            "content": content,
        }).execute()

        if not response.data:
            raise ValueError("Failed to create comment")

        comment_id = response.data[0]["id"]
        return await self._get_comment_with_reactions(comment_id)

    async def get_comments(
        self,
        proposal_id: str,
        scope: Optional[CommentScope] = None,
        proposal_step: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[CommentResponse], int]:
        """
        Get comments for a proposal with optional filtering

        Args:
            proposal_id: UUID of proposal
            scope: Filter by scope (optional)
            proposal_step: Filter by step (optional)
            offset: Pagination offset
            limit: Pagination limit

        Returns:
            Tuple of (comments list, total count)

        Raises:
            PermissionError: Not a proposal member
        """
        # Verify user can access proposal
        await self._verify_proposal_member(proposal_id)

        # Build query
        query = self.db.table("comments").select(
            "*",
            count="exact"
        ).eq("proposal_id", proposal_id).is_("deleted_at", "null").order_by(
            "created_at",
            desc=True
        ).range(offset, offset + limit - 1)

        # Apply scope filter
        if scope:
            query = query.eq("scope", scope.value)

        # Apply step filter
        if proposal_step and scope == CommentScope.STEP:
            query = query.eq("proposal_step", proposal_step)

        response = await query.execute()

        # Get reactions for each comment
        comments = []
        for comment_data in response.data:
            comment = await self._build_comment_response(comment_data)
            comments.append(comment)

        total = response.count or 0
        return comments, total

    async def update_comment(
        self,
        comment_id: str,
        proposal_id: str,
        content: str,
    ) -> CommentResponse:
        """
        Update comment content (author only)

        Args:
            comment_id: UUID of comment
            proposal_id: UUID of proposal
            content: New content

        Returns:
            CommentResponse with updated comment

        Raises:
            PermissionError: Not the comment author
            ValueError: Comment not found
        """
        # Verify user is comment author
        await self._verify_comment_author(comment_id)

        # Update comment
        response = await self.db.table("comments").update({
            "content": content,
            "edited_count": self.db.raw("edited_count + 1"),
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", comment_id).eq("proposal_id", proposal_id).execute()

        if not response.data:
            raise ValueError("Comment not found or already deleted")

        return await self._get_comment_with_reactions(comment_id)

    async def delete_comment(
        self,
        comment_id: str,
        proposal_id: str,
    ) -> None:
        """
        Soft delete a comment (author only)

        Args:
            comment_id: UUID of comment
            proposal_id: UUID of proposal

        Raises:
            PermissionError: Not the comment author
            ValueError: Comment not found
        """
        # Verify user is comment author
        await self._verify_comment_author(comment_id)

        # Soft delete
        response = await self.db.table("comments").update({
            "deleted_at": datetime.utcnow().isoformat(),
        }).eq("id", comment_id).eq("proposal_id", proposal_id).execute()

        if not response.data:
            raise ValueError("Comment not found")

    # ============================================
    # Emoji Reaction Operations
    # ============================================

    async def add_reaction(
        self,
        comment_id: str,
        proposal_id: str,
        emoji: str,
    ) -> dict:
        """
        Add emoji reaction to comment

        Args:
            comment_id: UUID of comment
            proposal_id: UUID of proposal
            emoji: Emoji character

        Returns:
            dict with reaction details

        Raises:
            ValueError: Comment not found or invalid emoji
        """
        # Verify comment exists and belongs to proposal
        await self._verify_comment_exists(comment_id, proposal_id)

        # Insert or ignore if already exists
        response = await self.db.table("emoji_reactions").insert({
            "comment_id": comment_id,
            "user_id": self.user_id,
            "org_id": self.org_id,
            "emoji": emoji,
        }, ignore_duplicates=True).execute()

        if not response.data:
            # Already exists, return success
            return {
                "comment_id": comment_id,
                "emoji": emoji,
                "message": "Reaction already exists",
            }

        return {
            "id": response.data[0].get("id"),
            "comment_id": comment_id,
            "emoji": emoji,
            "created_at": response.data[0].get("created_at"),
        }

    async def remove_reaction(
        self,
        comment_id: str,
        proposal_id: str,
        emoji: str,
    ) -> None:
        """
        Remove emoji reaction from comment (user's reaction only)

        Args:
            comment_id: UUID of comment
            proposal_id: UUID of proposal
            emoji: Emoji character to remove

        Raises:
            ValueError: Reaction not found
        """
        # Verify comment exists
        await self._verify_comment_exists(comment_id, proposal_id)

        # Delete reaction
        response = await self.db.table("emoji_reactions").delete().eq(
            "comment_id", comment_id
        ).eq("user_id", self.user_id).eq("emoji", emoji).execute()

        if not response.data:
            raise ValueError("Reaction not found")

    # ============================================
    # Helper Methods
    # ============================================

    async def _verify_proposal_member(self, proposal_id: str) -> None:
        """Verify current user is a member of the proposal"""
        # Check proposal exists and user has access
        response = await self.db.table("proposals").select("id").eq(
            "id", proposal_id
        ).limit(1).execute()

        if not response.data:
            raise PermissionError("Proposal not found or access denied")

    async def _verify_comment_exists(self, comment_id: str, proposal_id: str) -> None:
        """Verify comment exists and belongs to proposal"""
        response = await self.db.table("comments").select("id").eq(
            "id", comment_id
        ).eq("proposal_id", proposal_id).is_("deleted_at", "null").limit(1).execute()

        if not response.data:
            raise ValueError("Comment not found")

    async def _verify_comment_author(self, comment_id: str) -> None:
        """Verify current user is the comment author"""
        response = await self.db.table("comments").select("author_id").eq(
            "id", comment_id
        ).is_("deleted_at", "null").limit(1).execute()

        if not response.data:
            raise ValueError("Comment not found")

        if response.data[0]["author_id"] != self.user_id:
            raise PermissionError("Only comment author can perform this action")

    async def _get_comment_with_reactions(self, comment_id: str) -> CommentResponse:
        """Get full comment data with reactions"""
        response = await self.db.table("comments").select(
            "*, author:author_id(id, email, name)"
        ).eq("id", comment_id).limit(1).execute()

        if not response.data:
            raise ValueError("Comment not found")

        return await self._build_comment_response(response.data[0])

    async def _build_comment_response(self, comment_data: dict) -> CommentResponse:
        """Build CommentResponse from database row"""
        comment_id = comment_data.get("id")

        # Get reactions for this comment
        reactions_response = await self.db.table("emoji_reactions").select(
            "emoji, user_id"
        ).eq("comment_id", comment_id).execute()

        # Aggregate reactions by emoji
        reaction_map = {}
        for reaction in reactions_response.data or []:
            emoji = reaction.get("emoji")
            if emoji not in reaction_map:
                reaction_map[emoji] = {"emoji": emoji, "count": 0, "users": []}
            reaction_map[emoji]["count"] += 1

            # Get user email for user list
            user_id = reaction.get("user_id")
            user_response = await self.db.table("users").select(
                "email"
            ).eq("id", user_id).limit(1).execute()

            if user_response.data:
                user_email = user_response.data[0].get("email")
                if user_email:
                    reaction_map[emoji]["users"].append(user_email)

        reactions = list(reaction_map.values())

        # Build response
        author_data = comment_data.get("author")
        if isinstance(author_data, list) and author_data:
            author = AuthorInfo(**author_data[0])
        elif isinstance(author_data, dict):
            author = AuthorInfo(**author_data)
        else:
            author = AuthorInfo(id="unknown", email="unknown", name="Unknown")

        return CommentResponse(
            id=comment_data.get("id"),
            proposal_id=comment_data.get("proposal_id"),
            scope=CommentScope(comment_data.get("scope", "global")),
            proposal_step=comment_data.get("proposal_step"),
            inline_position=comment_data.get("inline_position"),
            author_id=comment_data.get("author_id"),
            author=author,
            content=comment_data.get("content", ""),
            reactions=reactions,
            reaction_count=len(reactions_response.data or []),
            edited=comment_data.get("edited_count", 0) > 0,
            edited_count=comment_data.get("edited_count", 0),
            deleted=comment_data.get("deleted_at") is not None,
            created_at=datetime.fromisoformat(
                comment_data.get("created_at", datetime.utcnow().isoformat())
            ),
            updated_at=datetime.fromisoformat(
                comment_data.get("updated_at", datetime.utcnow().isoformat())
            ),
        )
