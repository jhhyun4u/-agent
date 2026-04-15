"""
Vault Embedding Generation Service
Generates vector embeddings for vault_documents using OpenAI API
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
from openai import AsyncOpenAI

from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing vector embeddings"""
    
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        provider: str = "openai",
        batch_size: int = 100,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize embedding service
        
        Args:
            model: Embedding model name
            provider: Embedding provider (openai)
            batch_size: Number of documents to process at once
            similarity_threshold: Threshold for relevance (0-1)
        """
        self.model = model
        self.provider = provider
        self.batch_size = batch_size
        self.similarity_threshold = similarity_threshold
        self.openai_client: Optional[AsyncOpenAI] = None
    
    async def _init_openai(self):
        """Initialize OpenAI client"""
        if self.openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            from openai import AsyncOpenAI as OpenAIClient
            self.openai_client = OpenAIClient(api_key=api_key)
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            1536-dimensional embedding vector
        """
        try:
            await self._init_openai()
            
            # Clean text
            text = text.strip()
            if not text:
                raise ValueError("Cannot embed empty text")
            
            # Call OpenAI embedding API
            response = await self.openai_client.embeddings.create(
                input=text,
                model=self.model
            )
            
            # Extract embedding
            embedding = response.data[0].embedding
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    async def embed_documents_batch(
        self,
        limit: Optional[int] = None,
        document_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """
        Generate embeddings for documents needing them
        
        Args:
            limit: Maximum number of documents to process
            document_filter: Optional filter (e.g., {"section": "completed_projects"})
            
        Returns:
            Dict with counts: {"processed": n, "succeeded": n, "failed": n}
        """
        try:
            client = await get_async_client()
            
            # Get documents needing embeddings
            query = client.table("vault_documents").select(
                "id, content, section, document_type, created_at"
            ).is_("embedding", "null").order("created_at", desc=True)
            
            if document_filter:
                for key, value in document_filter.items():
                    query = query.eq(key, value)
            
            if limit:
                query = query.limit(limit)
            
            result = await query.execute()
            documents = result.data or []
            
            logger.info(f"Processing {len(documents)} documents needing embeddings")
            
            stats = {
                "processed": 0,
                "succeeded": 0,
                "failed": 0,
                "skipped": 0
            }
            
            # Process in batches
            for i in range(0, len(documents), self.batch_size):
                batch = documents[i:i + self.batch_size]
                
                for doc in batch:
                    try:
                        doc_id = doc["id"]
                        content = doc.get("content", "")
                        
                        if not content.strip():
                            logger.warning(f"Skipping document {doc_id}: empty content")
                            stats["skipped"] += 1
                            continue
                        
                        # Generate embedding
                        embedding = await self.embed_text(content)
                        
                        # Save embedding to database
                        await client.table("vault_documents").update({
                            "embedding": embedding,
                            "updated_at": datetime.now().isoformat()
                        }).eq("id", doc_id).execute()
                        
                        # Record success
                        await client.table("vault_embedding_audit").insert({
                            "document_id": doc_id,
                            "embedding_service": self.provider,
                            "embedding_model": self.model,
                            "status": "success",
                            "processed_at": datetime.now().isoformat()
                        }).execute()
                        
                        stats["succeeded"] += 1
                        stats["processed"] += 1
                        
                        logger.info(f"✓ Embedded document {doc_id} ({doc.get('section')}/{doc.get('document_type')})")
                        
                        # Rate limiting
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        stats["failed"] += 1
                        stats["processed"] += 1
                        
                        # Record failure
                        try:
                            await client.table("vault_embedding_audit").insert({
                                "document_id": doc["id"],
                                "embedding_service": self.provider,
                                "embedding_model": self.model,
                                "status": "error",
                                "error_message": str(e),
                                "processed_at": datetime.now().isoformat()
                            }).execute()
                        except Exception as audit_error:
                            logger.warning(f"Failed to record audit: {audit_error}")
                        
                        logger.error(f"✗ Failed to embed document {doc['id']}: {str(e)}")
            
            logger.info(f"Embedding batch complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in embed_documents_batch: {str(e)}")
            raise
    
    async def search_similar(
        self,
        query: str,
        section: Optional[str] = None,
        limit: int = 5,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity
        
        Args:
            query: Query text
            section: Optional section filter
            limit: Maximum results to return
            threshold: Similarity threshold (default: self.similarity_threshold)
            
        Returns:
            List of similar documents with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = await self.embed_text(query)
            
            # Search database
            client = await get_async_client()
            
            # Use vault_search_similar function if available, otherwise direct query
            try:
                # Attempt to use the stored function
                threshold = threshold or self.similarity_threshold
                
                # Direct RPC call to PostgreSQL function
                result = await client.rpc(
                    "vault_search_similar",
                    {
                        "query_embedding": query_embedding,
                        "similarity_threshold": threshold,
                        "limit_count": limit
                    }
                ).execute()
                
                documents = result.data or []
                
            except Exception as e:
                logger.warning(f"RPC search failed, falling back to direct query: {e}")
                
                # Fallback: direct search (less efficient)
                query_builder = client.table("vault_documents").select(
                    "id, document_id, section, title, content, metadata, created_at"
                ).is_("embedding", "not(null)").eq(
                    "deleted_at", "null"
                )
                
                if section:
                    query_builder = query_builder.eq("section", section)
                
                result = await query_builder.limit(limit * 2).execute()
                documents = result.data or []
            
            return documents
            
        except Exception as e:
            logger.error(f"Error in search_similar: {str(e)}")
            raise
    
    async def regenerate_embeddings_for_section(
        self,
        section: str,
        force: bool = False
    ) -> Dict[str, int]:
        """
        Regenerate embeddings for a specific section
        
        Args:
            section: Section to regenerate (e.g., "completed_projects")
            force: If True, regenerate even if embeddings exist
            
        Returns:
            Processing statistics
        """
        try:
            client = await get_async_client()
            
            # Clear existing embeddings if force=True
            if force:
                logger.info(f"Force regenerating embeddings for section: {section}")
                await client.table("vault_documents").update({
                    "embedding": None
                }).eq("section", section).execute()
            
            # Process documents
            return await self.embed_documents_batch(
                document_filter={"section": section}
            )
            
        except Exception as e:
            logger.error(f"Error regenerating embeddings: {str(e)}")
            raise
    
    async def get_embedding_status(self) -> Dict[str, Any]:
        """
        Get embedding generation status
        
        Returns:
            Status information
        """
        try:
            client = await get_async_client()
            
            # Count documents by embedding status
            total_result = await client.table("vault_documents").select(
                "id", count="exact"
            ).is_("deleted_at", "null").execute()
            
            embedded_result = await client.table("vault_documents").select(
                "id", count="exact"
            ).is_("embedding", "not(null)").is_(
                "deleted_at", "null"
            ).execute()
            
            pending_result = await client.table("vault_documents").select(
                "id", count="exact"
            ).is_("embedding", "null").is_(
                "deleted_at", "null"
            ).execute()
            
            # Get coverage by section
            section_result = await client.table("vault_documents").select(
                "section"
            ).is_("deleted_at", "null").execute()
            
            sections = {}
            for doc in section_result.data or []:
                section = doc.get("section", "unknown")
                sections[section] = sections.get(section, 0) + 1
            
            total = total_result.count or 0
            embedded = embedded_result.count or 0
            pending = pending_result.count or 0
            
            return {
                "total_documents": total,
                "embedded_documents": embedded,
                "pending_documents": pending,
                "completion_percentage": (embedded / total * 100) if total > 0 else 0,
                "by_section": sections,
                "model": self.model,
                "provider": self.provider
            }
            
        except Exception as e:
            logger.error(f"Error getting embedding status: {str(e)}")
            raise
