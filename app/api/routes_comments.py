"""
Comments & Reactions API Routes

Sprint 1 Phase 2: Team Comments & Feedback

Endpoints:
- POST /proposals/{proposal_id}/comments — Create comment
- GET /proposals/{proposal_id}/comments — List comments (with filtering)
- PUT /proposals/{proposal_id}/comments/{comment_id} — Update comment
- DELETE /proposals/{proposal_id}/comments/{comment_id} — Delete comment
- POST /comments/{comment_id}/reactions — Add emoji reaction
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional

from app.api.deps import get_current_user, get_rls_client
from app.api.response import ok, ok_list
from app.models.comment_schemas import (
    CommentCreate,
    CommentUpdate,
    CommentListResponse,
    CommentDetailResponse,
    EmojiReactionCreate,
    CommentScope,
)
from app.services.comment_service import CommentService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/proposals", tags=["comments"])


# ============================================
# Helper Dependencies
# ============================================

async def get_comment_service(
    user: dict = Depends(get_current_user),
    db = Depends(get_rls_client)
) -> CommentService:
    """Get comment service instance with RLS-enforced database client"""
    return CommentService(db=db, user=user)


# ============================================
# API Endpoints
# ============================================

@router.post(
    "/{proposal_id}/comments",
    response_model=CommentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create comment",
    description="Create a new comment on proposal (global/step/inline scope)"
)
async def create_comment(
    proposal_id: str,
    req: CommentCreate,
    service: CommentService = Depends(get_comment_service),
) -> dict:
    """
    Create a new comment on a proposal.

    **Parameters:**
    - `proposal_id`: UUID of the proposal
    - `scope`: 'global' | 'step' | 'inline'
    - `content`: Comment text (Markdown supported)
    - `proposal_step` (optional): For step-scoped comments
    - `inline_position` (optional): For inline comments (character offset)

    **Returns:**
    - 201 Created with comment details

    **Errors:**
    - 401 Unauthorized: Missing/invalid auth token
    - 403 Forbidden: Not a proposal member
    - 404 Not Found: Proposal not found
    - 422 Unprocessable Entity: Invalid scope/position combination
    """
    try:
        comment = await service.create_comment(
            proposal_id=proposal_id,
            scope=req.scope,
            content=req.content,
            proposal_step=req.proposal_step,
            inline_position=req.inline_position,
        )
        return ok(data=comment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not a proposal member")
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create comment")


@router.get(
    "/{proposal_id}/comments",
    response_model=CommentListResponse,
    summary="List comments",
    description="Get all comments for a proposal (with optional scope filtering)"
)
async def list_comments(
    proposal_id: str,
    scope: Optional[CommentScope] = Query(None, description="Filter by scope: global|step|inline"),
    proposal_step: Optional[str] = Query(None, description="Filter by step (for step-scoped comments)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    service: CommentService = Depends(get_comment_service),
) -> dict:
    """
    Get comments for a proposal with optional filtering.

    **Parameters:**
    - `proposal_id`: UUID of the proposal
    - `scope` (optional): Filter by scope (global | step | inline)
    - `proposal_step` (optional): Filter by step
    - `offset`: Pagination offset (default 0)
    - `limit`: Pagination limit (default 20, max 100)

    **Returns:**
    - 200 OK with list of comments and metadata

    **Errors:**
    - 401 Unauthorized: Missing/invalid auth token
    - 404 Not Found: Proposal not found
    """
    try:
        comments, total = await service.get_comments(
            proposal_id=proposal_id,
            scope=scope,
            proposal_step=proposal_step,
            offset=offset,
            limit=limit,
        )
        return ok_list(
            items=comments,
            total=total,
            offset=offset,
            limit=limit,
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not a proposal member")
    except Exception as e:
        logger.error(f"Error listing comments: {e}")
        raise HTTPException(status_code=500, detail="Failed to list comments")


@router.put(
    "/{proposal_id}/comments/{comment_id}",
    response_model=CommentDetailResponse,
    summary="Update comment",
    description="Update comment content (author only)"
)
async def update_comment(
    proposal_id: str,
    comment_id: str,
    req: CommentUpdate,
    service: CommentService = Depends(get_comment_service),
) -> dict:
    """
    Update a comment (author only).

    **Parameters:**
    - `proposal_id`: UUID of the proposal
    - `comment_id`: UUID of the comment
    - `content`: New comment content (Markdown supported)

    **Returns:**
    - 200 OK with updated comment

    **Errors:**
    - 401 Unauthorized: Missing/invalid auth token
    - 403 Forbidden: Not the comment author
    - 404 Not Found: Comment not found
    """
    try:
        comment = await service.update_comment(
            comment_id=comment_id,
            proposal_id=proposal_id,
            content=req.content,
        )
        return ok(data=comment)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Only comment author can edit")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to update comment")


@router.delete(
    "/{proposal_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete comment",
    description="Delete comment (soft delete, author only)"
)
async def delete_comment(
    proposal_id: str,
    comment_id: str,
    service: CommentService = Depends(get_comment_service),
) -> None:
    """
    Delete a comment (soft delete, author only).

    **Parameters:**
    - `proposal_id`: UUID of the proposal
    - `comment_id`: UUID of the comment

    **Returns:**
    - 204 No Content

    **Errors:**
    - 401 Unauthorized: Missing/invalid auth token
    - 403 Forbidden: Not the comment author
    - 404 Not Found: Comment not found
    """
    try:
        await service.delete_comment(
            comment_id=comment_id,
            proposal_id=proposal_id,
        )
        return None
    except PermissionError:
        raise HTTPException(status_code=403, detail="Only comment author can delete")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete comment")


# ============================================
# Reaction Endpoints
# ============================================

@router.post(
    "/{proposal_id}/comments/{comment_id}/reactions",
    status_code=status.HTTP_201_CREATED,
    summary="Add emoji reaction",
    description="Add emoji reaction to comment"
)
async def add_reaction(
    proposal_id: str,
    comment_id: str,
    req: EmojiReactionCreate,
    service: CommentService = Depends(get_comment_service),
) -> dict:
    """
    Add emoji reaction to a comment.

    **Parameters:**
    - `proposal_id`: UUID of the proposal
    - `comment_id`: UUID of the comment
    - `emoji`: Emoji character (e.g., '👍', '❤️', '🎉')

    **Returns:**
    - 201 Created with reaction details

    **Errors:**
    - 401 Unauthorized: Missing/invalid auth token
    - 404 Not Found: Comment not found
    - 422 Unprocessable Entity: Invalid emoji
    """
    try:
        reaction = await service.add_reaction(
            comment_id=comment_id,
            proposal_id=proposal_id,
            emoji=req.emoji,
        )
        return ok(data=reaction, message="Reaction added")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding reaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to add reaction")


@router.delete(
    "/{proposal_id}/comments/{comment_id}/reactions/{emoji}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove emoji reaction",
    description="Remove emoji reaction from comment"
)
async def remove_reaction(
    proposal_id: str,
    comment_id: str,
    emoji: str,
    service: CommentService = Depends(get_comment_service),
) -> None:
    """
    Remove emoji reaction from a comment.

    **Parameters:**
    - `proposal_id`: UUID of the proposal
    - `comment_id`: UUID of the comment
    - `emoji`: Emoji character to remove

    **Returns:**
    - 204 No Content

    **Errors:**
    - 401 Unauthorized: Missing/invalid auth token
    - 404 Not Found: Reaction not found
    """
    try:
        await service.remove_reaction(
            comment_id=comment_id,
            proposal_id=proposal_id,
            emoji=emoji,
        )
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing reaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove reaction")
