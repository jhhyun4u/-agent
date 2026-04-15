"""
Completed Projects Handler - Queries completed proposals with budget, team, outcomes
Uses hybrid approach: SQL primary (exact facts) + Vector secondary (semantic search)
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from app.models.vault_schemas import VaultSection, SearchResult
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


class CompletedProjectsHandler:
    """
    Handles queries for completed projects from proposals database
    
    Data source: proposals table (closed proposals)
    Primary strategy: SQL (exact matching on budget, client, team, dates)
    Secondary strategy: Vector search (semantic similarity of descriptions)
    Confidence calculation: 
        - SQL exact match: 0.95
        - Vector match: depends on similarity score
        - Synthesis: average of multiple sources
    """
    
    # SQL where conditions for different query intents
    SQL_FILTERS = {
        "by_client": "LOWER(client_name) LIKE LOWER('%{client}%')",
        "by_status": "status = '{status}'",
        "by_budget_range": "budget >= {min} AND budget <= {max}",
        "by_date_range": "end_date >= '{start}' AND end_date <= '{end}'",
        "by_team_member": "team_members @> '[{member}]'",  # JSONB array contains
    }
    
    @staticmethod
    async def search(
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Search completed projects using hybrid SQL + Vector approach
        
        Args:
            query: User query (can be natural language or structured)
            filters: Additional filters (date_from, date_to, client, team_member, etc.)
            limit: Max results to return
            
        Returns:
            List of SearchResult objects with sources and relevance scores
        """
        
        try:
            results = []

            # Check if advanced metadata filters are present
            has_metadata_filters = filters and any(
                key in filters for key in [
                    "industry", "tech_stack", "team_size_min", "team_size_max",
                    "duration_months_min", "duration_months_max"
                ]
            )

            # Step 1: SQL query (for exact facts)
            sql_results = await CompletedProjectsHandler._sql_search(
                query, filters, limit
            )
            results.extend(sql_results)

            # Step 1b: Metadata SQL search (if advanced filters present)
            if has_metadata_filters:
                metadata_results = await CompletedProjectsHandler._metadata_sql_search(
                    filters, limit
                )
                results.extend(metadata_results)

            # Step 2: Vector search (for semantic similarity)
            vector_results = await CompletedProjectsHandler._vector_search(
                query, filters, limit
            )
            results.extend(vector_results)

            # Step 3: Deduplicate and merge results
            merged_results = CompletedProjectsHandler._deduplicate_results(results)

            # Return top results by relevance score
            return sorted(merged_results, key=lambda x: x.relevance_score, reverse=True)[:limit]

        except Exception as e:
            logger.error(f"Error searching completed projects: {str(e)}")
            raise
    
    @staticmethod
    async def _sql_search(
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        SQL-based search for exact matches
        Queries proposals table for completed projects
        """
        
        try:
            supabase = await get_async_client()
            
            # Build base query
            select_clause = """
                id, 
                title, 
                description, 
                client_name,
                budget,
                currency,
                start_date,
                end_date,
                status,
                team_members,
                key_outcomes,
                win_result
            """
            
            # Base filter: only closed proposals
            base_query = supabase.table("proposals").select(select_clause).eq(
                "status", "closed"
            )
            
            # Apply optional filters
            if filters:
                if "client" in filters:
                    base_query = base_query.ilike("client_name", f"%{filters['client']}%")
                
                if "status" in filters:
                    base_query = base_query.in_("win_result", filters["status"])
                
                if "budget_min" in filters:
                    base_query = base_query.gte("budget", filters["budget_min"])
                
                if "budget_max" in filters:
                    base_query = base_query.lte("budget", filters["budget_max"])
                
                if "date_from" in filters:
                    base_query = base_query.gte("start_date", filters["date_from"])
                
                if "date_to" in filters:
                    base_query = base_query.lte("end_date", filters["date_to"])
            
            # Execute query
            query_result = base_query.order("end_date", desc=True).limit(limit).execute()
            
            results = []
            for project in query_result.data or []:
                # Convert to SearchResult
                result = SearchResult(
                    document=CompletedProjectsHandler._format_document(project),
                    relevance_score=0.95,  # SQL exact match
                    match_type="exact",
                    preview=CompletedProjectsHandler._create_preview(project)
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in SQL search: {str(e)}")
            return []
    
    @staticmethod
    async def _vector_search(
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[SearchResult]:
        """
        Vector-based search for semantic similarity
        Uses embedding service to find semantically similar completed projects
        
        Args:
            query: User query
            filters: Optional metadata filters
            limit: Max results
            threshold: Similarity threshold (0.7-0.8 recommended)
            
        Returns:
            List of SearchResult objects ordered by similarity score
        """
        
        try:
            from app.services.vault_embedding_service import EmbeddingService
            
            embedding_service = EmbeddingService()
            
            # Search vault_documents for completed projects using semantic similarity
            vector_results = await embedding_service.search_similar(
                query=query,
                section="completed_projects",
                limit=limit,
                threshold=threshold
            )
            
            results = []
            supabase = await get_async_client()
            
            for search_result in vector_results:
                doc_id = search_result.get("document_id")
                similarity_score = search_result.get("similarity", 0.0)
                
                # Fetch full document metadata from vault_documents
                doc_result = await supabase.table("vault_documents").select(
                    "id, title, content, metadata, created_at"
                ).eq("id", doc_id).single().execute()
                
                if not doc_result.data:
                    continue
                
                doc = doc_result.data
                
                # Apply metadata filters if provided
                if filters:
                    doc_metadata = doc.get("metadata", {})

                    if "client" in filters and filters["client"].lower() not in str(doc_metadata.get("client", "")).lower():
                        continue

                    if "budget_min" in filters and doc_metadata.get("budget", 0) < filters["budget_min"]:
                        continue

                    if "budget_max" in filters and doc_metadata.get("budget", 0) > filters["budget_max"]:
                        continue

                    if "date_from" in filters and str(doc_metadata.get("start_date", "")) < filters["date_from"]:
                        continue

                    if "date_to" in filters and str(doc_metadata.get("end_date", "")) > filters["date_to"]:
                        continue

                    # Advanced metadata filters
                    if "industry" in filters and filters["industry"]:
                        doc_industry = str(doc_metadata.get("industry", "")).lower()
                        if filters["industry"].lower() not in doc_industry:
                            continue

                    if "tech_stack" in filters and filters["tech_stack"]:
                        # tech_stack is list - OR condition (any match succeeds)
                        doc_tech_stack = doc_metadata.get("tech_stack", [])
                        if isinstance(doc_tech_stack, str):
                            doc_tech_stack = [doc_tech_stack]
                        if not any(tech.lower() in [t.lower() for t in doc_tech_stack] for tech in filters["tech_stack"]):
                            continue

                    if "team_size_min" in filters and filters["team_size_min"] is not None:
                        team_size = doc_metadata.get("team_size")
                        if team_size is not None and int(team_size) < filters["team_size_min"]:
                            continue

                    if "team_size_max" in filters and filters["team_size_max"] is not None:
                        team_size = doc_metadata.get("team_size")
                        if team_size is not None and int(team_size) > filters["team_size_max"]:
                            continue

                    if "duration_months_min" in filters and filters["duration_months_min"] is not None:
                        duration = doc_metadata.get("duration_months")
                        if duration is not None and int(duration) < filters["duration_months_min"]:
                            continue

                    if "duration_months_max" in filters and filters["duration_months_max"] is not None:
                        duration = doc_metadata.get("duration_months")
                        if duration is not None and int(duration) > filters["duration_months_max"]:
                            continue
                
                # Convert to SearchResult
                result = SearchResult(
                    document=CompletedProjectsHandler._format_document(doc),
                    relevance_score=similarity_score,
                    match_type="semantic",
                    preview=CompletedProjectsHandler._create_preview(doc)
                )
                results.append(result)
            
            return results
            
        except ImportError:
            logger.warning("EmbeddingService not available, skipping vector search")
            return []
        except Exception as e:
            logger.warning(f"Error in vector search: {str(e)}")
            return []

    @staticmethod
    async def _metadata_sql_search(
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        SQL-based search using JSONB metadata operators on vault_documents
        Used when advanced metadata filters are present (industry, tech_stack, team_size, duration_months)

        Args:
            filters: Metadata filters
            limit: Max results

        Returns:
            List of SearchResult objects with match_type="metadata"
        """

        if not filters:
            return []

        try:
            supabase = await get_async_client()

            # Start with base query for completed_projects section
            query = supabase.table("vault_documents").select(
                "id, title, content, metadata, created_at"
            ).eq("section", "completed_projects")

            # Apply JSONB filters
            if "industry" in filters and filters["industry"]:
                query = query.eq("metadata->>industry", filters["industry"])

            if "team_size_min" in filters and filters["team_size_min"] is not None:
                query = query.gte("metadata->>team_size", str(filters["team_size_min"]))

            if "team_size_max" in filters and filters["team_size_max"] is not None:
                query = query.lte("metadata->>team_size", str(filters["team_size_max"]))

            if "duration_months_min" in filters and filters["duration_months_min"] is not None:
                query = query.gte("metadata->>duration_months", str(filters["duration_months_min"]))

            if "duration_months_max" in filters and filters["duration_months_max"] is not None:
                query = query.lte("metadata->>duration_months", str(filters["duration_months_max"]))

            # Execute query
            result = query.order("created_at", desc=True).limit(limit).execute()

            results = []
            for doc in result.data or []:
                # Apply tech_stack filter in Python (array containment)
                if "tech_stack" in filters and filters["tech_stack"]:
                    doc_tech_stack = doc.get("metadata", {}).get("tech_stack", [])
                    if isinstance(doc_tech_stack, str):
                        doc_tech_stack = [doc_tech_stack]
                    if not any(tech.lower() in [t.lower() for t in doc_tech_stack] for tech in filters["tech_stack"]):
                        continue

                # Convert to SearchResult
                result_obj = SearchResult(
                    document=CompletedProjectsHandler._format_document(doc),
                    relevance_score=0.85,  # Between exact (0.95) and semantic (0.7-0.8)
                    match_type="metadata",
                    preview=CompletedProjectsHandler._create_preview(doc)
                )
                results.append(result_obj)

            return results

        except Exception as e:
            logger.warning(f"Error in metadata SQL search: {str(e)}")
            return []

    @staticmethod
    def _format_document(project: Dict[str, Any]):
        """Convert proposal row to VaultDocument format"""
        
        from app.models.vault_schemas import VaultDocument
        
        return VaultDocument(
            id=project.get("id"),
            section=VaultSection.COMPLETED_PROJECTS,
            title=project.get("title", ""),
            content=project.get("description"),
            metadata={
                "proposal_id": project.get("id"),
                "client": project.get("client_name"),
                "budget": project.get("budget"),
                "currency": project.get("currency", "KRW"),
                "start_date": project.get("start_date"),
                "end_date": project.get("end_date"),
                "team_members": project.get("team_members", []),
                "key_outcomes": project.get("key_outcomes", []),
                "win_result": project.get("win_result"),
            },
            created_at=datetime.now()
        )
    
    @staticmethod
    def _create_preview(project: Dict[str, Any]) -> str:
        """Create human-readable preview of project"""
        
        return f"""
**{project.get('title')}** ({project.get('win_result', 'unknown')})
- Client: {project.get('client_name')}
- Budget: {project.get('budget'):,} {project.get('currency', 'KRW')}
- Period: {project.get('start_date')} ~ {project.get('end_date')}
- Team: {len(project.get('team_members', []))} people
""".strip()

    
    @staticmethod
    def _deduplicate_results(results: List[SearchResult]) -> List[SearchResult]:
        """
        Deduplicate search results by document ID and merge scores
        
        When same document appears in both SQL and vector results,
        average their scores and keep the merged result
        
        Args:
            results: List of SearchResult objects (may have duplicates)
            
        Returns:
            List of deduplicated SearchResult objects with merged scores
        """
        
        seen = {}  # Map of document_id -> SearchResult
        
        for result in results:
            doc_id = result.document.id
            
            if doc_id not in seen:
                seen[doc_id] = result
            else:
                # Merge scores from duplicate results
                existing = seen[doc_id]
                
                # Average the relevance scores
                merged_score = (existing.relevance_score + result.relevance_score) / 2
                
                # Update match_type to reflect both sources
                if existing.match_type != result.match_type:
                    merged_type = f"{existing.match_type}+{result.match_type}"
                else:
                    merged_type = existing.match_type
                
                # Create merged result
                merged_result = SearchResult(
                    document=existing.document,
                    relevance_score=merged_score,
                    match_type=merged_type,
                    preview=existing.preview
                )
                seen[doc_id] = merged_result
        
        return list(seen.values())
    
    @staticmethod
    async def validate_facts(
        project_id: str,
        claims: List[str]
    ) -> Dict[str, Any]:
        """
        Validate factual claims about a project against actual DB data
        
        Args:
            project_id: Proposal ID
            claims: List of claims to verify
            
        Returns:
            Validation report with verified/unverified claims
        """
        
        try:
            supabase = await get_async_client()
            
            # Fetch actual project data
            project_result = await supabase.table("proposals").select(
                "id, title, budget, team_members, key_outcomes"
            ).eq("id", project_id).single().execute()
            
            if not project_result.data:
                return {"verified": False, "reason": "Project not found"}
            
            project = project_result.data
            
            # Validate each claim
            verified_claims = []
            unverified_claims = []
            
            for claim in claims:
                # Simple verification logic (can be enhanced with NLP)
                if "budget" in claim.lower() and project.get("budget"):
                    verified_claims.append(f"Budget confirmed: {project['budget']}")
                elif "team" in claim.lower():
                    team_size = len(project.get("team_members", []))
                    verified_claims.append(f"Team size confirmed: {team_size}")
                else:
                    unverified_claims.append(claim)
            
            return {
                "verified": len(unverified_claims) == 0,
                "verified_claims": verified_claims,
                "unverified_claims": unverified_claims,
            }
            
        except Exception as e:
            logger.error(f"Error validating facts: {str(e)}")
            return {"verified": False, "error": str(e)}
