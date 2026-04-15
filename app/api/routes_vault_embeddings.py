"""
Vault Embedding Management Routes
Endpoints for embedding generation, status, and management
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional

from app.api.deps import get_current_user
from app.models.auth_schemas import CurrentUser
from app.services.vault_embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vault/embeddings", tags=["vault-embeddings"])

# Create service instance
embedding_service = EmbeddingService()


# ============================================================================
# Embedding Management
# ============================================================================

@router.post("/generate")
async def generate_embeddings(
    section: Optional[str] = None,
    limit: Optional[int] = None,
    background_tasks: BackgroundTasks = None,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Generate embeddings for documents
    
    This endpoint triggers embedding generation for documents that need them.
    Can be run in background or synchronously.
    
    Args:
        section: Optional section filter (e.g., "completed_projects")
        limit: Maximum documents to process
        background_tasks: FastAPI background tasks (optional)
    """
    try:
        # Check authorization (admin only for now)
        if current_user.role not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Only admins can generate embeddings")
        
        # Prepare filter
        document_filter = {}
        if section:
            document_filter["section"] = section
        
        # Run embedding generation
        if background_tasks:
            # Run in background
            background_tasks.add_task(
                embedding_service.embed_documents_batch,
                limit=limit,
                document_filter=document_filter or None
            )
            return {
                "status": "processing",
                "message": "Embedding generation started in background",
                "section": section,
                "limit": limit
            }
        else:
            # Run synchronously
            stats = await embedding_service.embed_documents_batch(
                limit=limit,
                document_filter=document_filter or None
            )
            return {
                "status": "completed",
                "statistics": stats,
                "section": section
            }
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@router.post("/regenerate/{section}")
async def regenerate_section(
    section: str,
    force: bool = False,
    background_tasks: BackgroundTasks = None,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Regenerate embeddings for a specific section
    
    Args:
        section: Section name (e.g., "completed_projects", "government_guidelines")
        force: If true, regenerate even if embeddings exist
        background_tasks: FastAPI background tasks
    """
    try:
        # Check authorization
        if current_user.role not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Only admins can regenerate embeddings")
        
        if background_tasks:
            background_tasks.add_task(
                embedding_service.regenerate_embeddings_for_section,
                section=section,
                force=force
            )
            return {
                "status": "processing",
                "message": f"Regenerating embeddings for section: {section}",
                "force": force
            }
        else:
            stats = await embedding_service.regenerate_embeddings_for_section(
                section=section,
                force=force
            )
            return {
                "status": "completed",
                "section": section,
                "statistics": stats
            }
        
    except Exception as e:
        logger.error(f"Error regenerating embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")


@router.get("/status")
async def get_embedding_status(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get embedding generation status
    
    Returns information about:
    - Total documents
    - Embedded documents
    - Pending documents
    - Completion percentage
    - Coverage by section
    """
    try:
        status = await embedding_service.get_embedding_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get embedding status")


@router.post("/search")
async def search_embeddings(
    query: str,
    section: Optional[str] = None,
    limit: int = 5,
    threshold: Optional[float] = None,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Search for documents using vector similarity
    
    Args:
        query: Search query text
        section: Optional section filter
        limit: Maximum results (default: 5)
        threshold: Similarity threshold 0-1 (default: 0.7)
    """
    try:
        if not query or len(query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        results = await embedding_service.search_similar(
            query=query,
            section=section,
            limit=min(limit, 50),  # Cap at 50
            threshold=threshold
        )
        
        return {
            "query": query,
            "section": section,
            "results_count": len(results),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.post("/embed-text")
async def embed_single_text(
    text: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Generate embedding for a single text
    
    Useful for testing and debugging
    
    Args:
        text: Text to embed
    """
    try:
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        embedding = await embedding_service.embed_text(text)
        
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "embedding_dimension": len(embedding),
            "embedding_preview": embedding[:10],  # First 10 dimensions
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error embedding text: {str(e)}")
        raise HTTPException(status_code=500, detail="Embedding failed")


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check for embedding service"""
    return {
        "status": "healthy",
        "service": "vault-embeddings",
        "model": "text-embedding-3-small",
        "provider": "openai"
    }
