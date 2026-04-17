"""
Comment & Reaction Pydantic Schemas for Team Collaboration

Sprint 1 Phase 2: Team Comments & Feedback feature
"""

from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Enums
# ============================================

class CommentScope(str, Enum):
    """Comment scope: global (whole proposal), step (specific step), inline (specific position)"""
    GLOBAL = "global"
    STEP = "step"
    INLINE = "inline"


# ============================================
# Author Info (Nested)
# ============================================

class AuthorInfo(BaseModel):
    """Author information embedded in comment response"""
    id: str = Field(..., description="User ID (UUID)")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User display name")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Emoji Reaction Schemas
# ============================================

class EmojiReactionCreate(BaseModel):
    """Request to add emoji reaction to comment"""
    emoji: str = Field(
        ...,
        description="Emoji character (e.g., '👍', '❤️', '🎉')",
        min_length=1,
        max_length=10
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "emoji": "👍"
        }
    })


class EmojiReactionResponse(BaseModel):
    """Single emoji reaction in response"""
    id: str = Field(..., description="Reaction ID (UUID)")
    emoji: str = Field(..., description="Emoji character")
    created_at: datetime = Field(..., description="When reaction was added")

    model_config = ConfigDict(from_attributes=True)


class ReactionSummary(BaseModel):
    """Aggregated reaction counts by emoji"""
    emoji: str = Field(..., description="Emoji character")
    count: int = Field(..., description="Number of users who added this emoji")
    users: List[str] = Field(default_factory=list, description="List of user emails who reacted")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "emoji": "👍",
            "count": 3,
            "users": ["user1@tenopa.co.kr", "user2@tenopa.co.kr", "user3@tenopa.co.kr"]
        }
    })


# ============================================
# Comment Schemas
# ============================================

class CommentCreate(BaseModel):
    """Request to create new comment"""
    scope: CommentScope = Field(
        ...,
        description="Comment scope: 'global' | 'step' | 'inline'"
    )
    content: str = Field(
        ...,
        description="Comment content (Markdown supported)",
        min_length=1,
        max_length=5000
    )
    proposal_step: Optional[str] = Field(
        default=None,
        description="Step name for step-scoped comments (e.g., 'step_1', 'step_2')"
    )
    inline_position: Optional[int] = Field(
        default=None,
        description="Character offset for inline comments"
    )

    model_config = ConfigDict(json_schema_extra={
        "examples": {
            "global": {
                "scope": "global",
                "content": "# Overall Comment\n\nThis proposal looks good overall."
            },
            "step": {
                "scope": "step",
                "proposal_step": "step_1",
                "content": "Consider rewording this section for clarity."
            },
            "inline": {
                "scope": "inline",
                "proposal_step": "step_1",
                "inline_position": 150,
                "content": "This phrase is ambiguous."
            }
        }
    })


class CommentUpdate(BaseModel):
    """Request to update comment"""
    content: str = Field(
        ...,
        description="Updated comment content (Markdown supported)",
        min_length=1,
        max_length=5000
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "content": "# Updated Comment\n\nRevised feedback based on new information."
        }
    })


class CommentResponse(BaseModel):
    """Single comment in response"""
    id: str = Field(..., description="Comment ID (UUID)")
    proposal_id: str = Field(..., description="Proposal ID (UUID)")
    scope: CommentScope = Field(..., description="Comment scope")
    proposal_step: Optional[str] = Field(None, description="Step name if step-scoped")
    inline_position: Optional[int] = Field(None, description="Character offset if inline")

    author_id: str = Field(..., description="Author user ID")
    author: AuthorInfo = Field(..., description="Author information")
    content: str = Field(..., description="Comment content (Markdown)")

    reactions: List[ReactionSummary] = Field(
        default_factory=list,
        description="Emoji reactions on this comment"
    )
    reaction_count: int = Field(
        default=0,
        description="Total number of reactions"
    )

    edited: bool = Field(
        default=False,
        description="Whether comment has been edited"
    )
    edited_count: int = Field(
        default=0,
        description="Number of times edited"
    )
    deleted: bool = Field(
        default=False,
        description="Soft delete flag"
    )

    created_at: datetime = Field(..., description="When comment was created")
    updated_at: datetime = Field(..., description="When comment was last updated")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "proposal_id": "550e8400-e29b-41d4-a716-446655440001",
                "scope": "global",
                "proposal_step": None,
                "inline_position": None,
                "author_id": "550e8400-e29b-41d4-a716-446655440002",
                "author": {
                    "id": "550e8400-e29b-41d4-a716-446655440002",
                    "email": "user@tenopa.co.kr",
                    "name": "User Name"
                },
                "content": "# Feedback\n\nThis section needs stronger supporting evidence.",
                "reactions": [
                    {"emoji": "👍", "count": 2, "users": ["user1@tenopa.co.kr", "user2@tenopa.co.kr"]},
                    {"emoji": "🤔", "count": 1, "users": ["user3@tenopa.co.kr"]}
                ],
                "reaction_count": 3,
                "edited": False,
                "edited_count": 0,
                "deleted": False,
                "created_at": "2026-04-16T10:30:00Z",
                "updated_at": "2026-04-16T10:30:00Z"
            }
        }
    )


class CommentListResponse(BaseModel):
    """List of comments with metadata"""
    data: List[CommentResponse] = Field(..., description="List of comments")
    meta: Dict = Field(..., description="Pagination and metadata")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "data": [],
            "meta": {
                "total": 5,
                "offset": 0,
                "limit": 20,
                "timestamp": "2026-04-16T10:35:00Z"
            }
        }
    })


class CommentDetailResponse(BaseModel):
    """Single comment detail response"""
    data: CommentResponse = Field(..., description="Comment details")
    meta: Dict = Field(..., description="Response metadata")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "data": {},
            "meta": {"timestamp": "2026-04-16T10:35:00Z"}
        }
    })


# ============================================
# Statistics Schemas
# ============================================

class CommentStats(BaseModel):
    """Statistics for comments on a proposal"""
    proposal_id: str = Field(..., description="Proposal ID")
    total_comments: int = Field(..., description="Total comment count")
    unique_authors: int = Field(..., description="Number of unique commenters")
    global_count: int = Field(..., description="Global-scoped comments")
    step_count: int = Field(..., description="Step-scoped comments")
    inline_count: int = Field(..., description="Inline-scoped comments")
    total_reactions: int = Field(..., description="Total emoji reactions")
    last_comment_at: Optional[datetime] = Field(None, description="Timestamp of last comment")

    model_config = ConfigDict(from_attributes=True)
