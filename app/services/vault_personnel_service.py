"""
Vault Personnel Service — 인사 데이터 관리
HR 데이터 동기화, 인력 검색, 역량 관리, 가용성 추적
"""

from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional, List, Dict, Any
import logging

from app.utils.supabase_client import supabase

logger = logging.getLogger(__name__)


class VaultPersonnelService:
    """인력 관리 및 HR 동기화 서비스"""

    # ============================================
    # 기본 CRUD
    # ============================================

    @staticmethod
    async def get_personnel(personnel_id: UUID) -> Dict[str, Any]:
        """
        인력 상세 조회

        Args:
            personnel_id: Personnel UUID

        Returns:
            Personnel record with all details

        Raises:
            ValueError: Personnel not found
        """
        try:
            response = supabase.table("vault_personnel").select(
                "*, manager:manager_id(id, name, email)"
            ).eq("id", str(personnel_id)).execute()

            if not response.data:
                raise ValueError("Personnel not found")

            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to get personnel: {str(e)}")
            raise

    @staticmethod
    async def get_personnel_by_user_id(user_id: UUID) -> Dict[str, Any]:
        """
        사용자 ID로 인력 조회

        Args:
            user_id: Supabase auth user ID

        Returns:
            Personnel record

        Raises:
            ValueError: Personnel not found
        """
        try:
            response = supabase.table("vault_personnel").select("*").eq(
                "user_id", str(user_id)
            ).execute()

            if not response.data:
                raise ValueError("Personnel record not found for user")

            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to get personnel by user_id: {str(e)}")
            raise

    @staticmethod
    async def search_personnel(
        org_id: UUID,
        query: Optional[str] = None,
        department: Optional[str] = None,
        role: Optional[str] = None,
        skill: Optional[str] = None,
        is_active: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        인력 검색 (다중 필터)

        Args:
            org_id: Organization ID
            query: Name/email 검색
            department: 부서 필터
            role: 직급 필터
            skill: 보유 기술 필터
            is_active: 활성 여부 필터
            limit: 결과 수 제한

        Returns:
            List of matching personnel
        """
        try:
            q = supabase.table("vault_personnel").select(
                "id, name, email, role, department, primary_expertise, skills, "
                "total_proposals, won_proposals, win_rate, current_project_count, "
                "max_concurrent_projects, years_in_company"
            ).eq("org_id", str(org_id))

            if is_active:
                q = q.eq("is_active", True).eq("employment_status", "employed")

            if department:
                q = q.eq("department", department)

            if role:
                q = q.eq("role", role)

            # Search by name or email
            if query:
                query_lower = query.lower()
                # Note: Using ilike for case-insensitive search
                q = q.filter("name", "ilike", f"%{query_lower}%")

            # Filter by skill (uses JSONB contains)
            if skill:
                q = q.filter("skills", "cs", f'[{{"skill":"{skill}"}}]')

            response = q.order("name").limit(limit).execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Failed to search personnel: {str(e)}")
            raise

    @staticmethod
    async def sync_from_supabase_auth(org_id: UUID) -> Dict[str, Any]:
        """
        Supabase auth.users에서 인력 데이터 동기화

        새로운 사용자는 자동으로 vault_personnel에 추가
        기존 사용자는 업데이트

        Args:
            org_id: Organization ID

        Returns:
            Sync result with counts
        """
        try:
            # Get all users in org from Supabase Auth
            users_response = supabase.table("users").select(
                "id, email, name, role"
            ).eq("org_id", str(org_id)).execute()

            users = users_response.data or []
            inserted = 0
            updated = 0
            errors = 0

            for user in users:
                try:
                    # Check if personnel record exists
                    existing = supabase.table("vault_personnel").select(
                        "id"
                    ).eq("user_id", user["id"]).execute()

                    if not existing.data:
                        # Insert new personnel
                        supabase.table("vault_personnel").insert({
                            "org_id": str(org_id),
                            "user_id": user["id"],
                            "name": user.get("name", ""),
                            "email": user.get("email", ""),
                            "role": user.get("role", "employee"),
                            "is_active": True,
                            "employment_status": "employed",
                            "last_synced_at": datetime.utcnow().isoformat()
                        }).execute()
                        inserted += 1
                    else:
                        # Update last_synced_at
                        supabase.table("vault_personnel").update({
                            "last_synced_at": datetime.utcnow().isoformat()
                        }).eq("user_id", user["id"]).execute()
                        updated += 1
                except Exception as e:
                    logger.error(f"Error syncing user {user['id']}: {str(e)}")
                    errors += 1

            return {
                "synced_at": datetime.utcnow().isoformat(),
                "total_users": len(users),
                "inserted": inserted,
                "updated": updated,
                "errors": errors
            }
        except Exception as e:
            logger.error(f"Failed to sync personnel from auth: {str(e)}")
            raise

    # ============================================
    # 역량 관리
    # ============================================

    @staticmethod
    async def update_skills(
        personnel_id: UUID,
        skills: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        인력의 기술/역량 업데이트

        Args:
            personnel_id: Personnel UUID
            skills: List of skills [{"skill": "제안서 작성", "proficiency": "expert", "years": 8}, ...]

        Returns:
            Updated personnel record
        """
        try:
            # Validate proficiency levels
            valid_proficiency = ["beginner", "intermediate", "advanced", "expert"]
            for skill in skills:
                if skill.get("proficiency", "intermediate") not in valid_proficiency:
                    raise ValueError(f"Invalid proficiency: {skill['proficiency']}")

            response = supabase.table("vault_personnel").update({
                "skills": skills,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(personnel_id)).execute()

            if not response.data:
                raise ValueError("Personnel not found")

            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to update skills: {str(e)}")
            raise

    @staticmethod
    async def get_expertise_inventory(org_id: UUID) -> Dict[str, Any]:
        """
        조직의 역량 인벤토리 조회
        전체 기술 분포, 전문가 수, 등급별 인력 수

        Args:
            org_id: Organization ID

        Returns:
            Expertise inventory with distribution
        """
        try:
            response = supabase.table("vault_personnel_expertise_inventory").select(
                "*"
            ).eq("org_id", str(org_id)).execute()

            if not response.data:
                return {
                    "org_id": str(org_id),
                    "all_skills": [],
                    "expert_count": 0,
                    "advanced_count": 0
                }

            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to get expertise inventory: {str(e)}")
            raise

    @staticmethod
    async def get_available_personnel(
        org_id: UUID,
        required_skill: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        가용한 인력 조회

        조건:
        - 활성 상태 (is_active = true)
        - 근무중 (employment_status = 'employed')
        - 가용 기간 내
        - 역량 활용 가능 (<100% utilization)
        - 특정 기술 보유 (optional)

        Args:
            org_id: Organization ID
            required_skill: 필요한 기술 (optional)
            limit: 결과 수 제한

        Returns:
            List of available personnel with utilization info
        """
        try:
            # Filter by status using join with vault_personnel
            personnel_response = supabase.table("vault_personnel").select(
                "id, name, email, role, primary_expertise, skills, "
                "total_proposals, won_proposals, win_rate, "
                "max_concurrent_projects, current_project_count"
            ).eq("org_id", str(org_id)).eq("is_active", True).eq(
                "employment_status", "employed"
            ).limit(limit).execute()

            personnel = personnel_response.data or []

            # Filter by required skill if specified
            if required_skill:
                personnel = [
                    p for p in personnel
                    if any(s.get("skill") == required_skill for s in p.get("skills", []))
                ]

            # Calculate utilization and filter
            available = []
            for p in personnel:
                utilization_percent = (
                    (p.get("current_project_count", 0) * 100.0) /
                    p.get("max_concurrent_projects", 3)
                ) if p.get("max_concurrent_projects", 0) > 0 else 0

                if utilization_percent < 100:  # Only return not-at-capacity
                    available.append({
                        **p,
                        "utilization_percent": round(utilization_percent, 1),
                        "capacity_status": (
                            "free" if utilization_percent == 0
                            else "available" if utilization_percent < 80
                            else "high-utilization"
                        )
                    })

            return available[:limit]
        except Exception as e:
            logger.error(f"Failed to get available personnel: {str(e)}")
            raise

    # ============================================
    # 성과 분석
    # ============================================

    @staticmethod
    async def get_top_contributors(
        org_id: UUID,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        상위 기여자 조회 (낙찰률 & 제안 수 기준)

        Args:
            org_id: Organization ID
            limit: 결과 수 제한

        Returns:
            Top contributors sorted by win_rate and proposal count
        """
        try:
            # Use view filtered by org
            response = supabase.table("vault_personnel_top_contributors").select(
                "*"
            ).eq("org_id", str(org_id)).limit(limit).execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get top contributors: {str(e)}")
            raise

    @staticmethod
    async def get_department_stats(org_id: UUID) -> List[Dict[str, Any]]:
        """
        부서별 인력 통계

        Args:
            org_id: Organization ID

        Returns:
            Department-level statistics with personnel counts and performance
        """
        try:
            response = supabase.table("vault_personnel_by_department").select(
                "department, total_count, active_count, avg_win_rate, "
                "avg_tenure, key_skills"
            ).eq("org_id", str(org_id)).execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get department stats: {str(e)}")
            raise

    @staticmethod
    async def get_personnel_performance(
        personnel_id: UUID,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        개인 성과 요약

        Args:
            personnel_id: Personnel UUID
            days: 조회 기간 (기본 90일)

        Returns:
            Performance summary including wins, losses, and trends
        """
        try:
            personnel = await VaultPersonnelService.get_personnel(personnel_id)

            # Get user_id for proposal queries
            user_id = personnel.get("user_id")

            # Query recent proposals
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

            proposals = supabase.table("proposal_participants").select(
                "proposal_id, role"
            ).eq("user_id", user_id).gte("created_at", cutoff_date).execute()

            proposal_ids = [p["proposal_id"] for p in proposals.data or []]

            if not proposal_ids:
                return {
                    "personnel_id": str(personnel_id),
                    "period_days": days,
                    "total_proposals": 0,
                    "won_proposals": 0,
                    "lost_proposals": 0,
                    "win_rate": 0,
                    "avg_bid_amount": 0
                }

            # Query proposal results
            results = supabase.table("proposals").select(
                "id, status, estimated_budget"
            ).in_("id", proposal_ids).execute()

            proposals_data = results.data or []
            won = sum(1 for p in proposals_data if p["status"] == "won")
            lost = sum(1 for p in proposals_data if p["status"] == "lost")
            total = len(proposals_data)

            return {
                "personnel_id": str(personnel_id),
                "period_days": days,
                "total_proposals": total,
                "won_proposals": won,
                "lost_proposals": lost,
                "pending_proposals": total - won - lost,
                "win_rate": round(won * 100.0 / total, 2) if total > 0 else 0,
                "lifetime_stats": {
                    "total_proposals": personnel.get("total_proposals", 0),
                    "total_wins": personnel.get("won_proposals", 0),
                    "lifetime_win_rate": float(personnel.get("win_rate", 0) or 0)
                }
            }
        except Exception as e:
            logger.error(f"Failed to get personnel performance: {str(e)}")
            raise

    # ============================================
    # 가용성 관리
    # ============================================

    @staticmethod
    async def update_availability(
        personnel_id: UUID,
        available_from: Optional[datetime] = None,
        available_until: Optional[datetime] = None,
        max_concurrent_projects: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        인력의 가용성 업데이트

        Args:
            personnel_id: Personnel UUID
            available_from: 가용 시작일
            available_until: 가용 종료일
            max_concurrent_projects: 최대 동시 프로젝트 수

        Returns:
            Updated personnel record
        """
        try:
            update_data = {"updated_at": datetime.utcnow().isoformat()}

            if available_from:
                update_data["available_from"] = available_from.isoformat()
            if available_until:
                update_data["available_until"] = available_until.isoformat()
            if max_concurrent_projects is not None:
                update_data["max_concurrent_projects"] = max_concurrent_projects

            response = supabase.table("vault_personnel").update(
                update_data
            ).eq("id", str(personnel_id)).execute()

            if not response.data:
                raise ValueError("Personnel not found")

            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to update availability: {str(e)}")
            raise

    @staticmethod
    async def get_utilization_report(org_id: UUID) -> List[Dict[str, Any]]:
        """
        조직 전체 인력 활용률 보고서

        Args:
            org_id: Organization ID

        Returns:
            List of personnel with utilization metrics
        """
        try:
            response = supabase.table("vault_personnel_utilization").select(
                "id, name, email, role, max_concurrent_projects, "
                "current_project_count, utilization_percent, capacity_status"
            ).eq("org_id", str(org_id)).order("utilization_percent", desc=True).execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get utilization report: {str(e)}")
            raise

    # ============================================
    # HR 관리
    # ============================================

    @staticmethod
    async def update_hr_info(
        personnel_id: UUID,
        department: Optional[str] = None,
        role: Optional[str] = None,
        position: Optional[str] = None,
        manager_id: Optional[UUID] = None,
        hr_notes: Optional[str] = None,
        employment_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        HR 정보 업데이트 (부서, 직급, 관리자 등)

        Args:
            personnel_id: Personnel UUID
            department: 부서명
            role: 직급
            position: 직책
            manager_id: 관리자 ID
            hr_notes: HR 메모
            employment_status: 근무 상태

        Returns:
            Updated personnel record
        """
        try:
            update_data = {"updated_at": datetime.utcnow().isoformat()}

            if department:
                update_data["department"] = department
            if role:
                update_data["role"] = role
            if position:
                update_data["position"] = position
            if manager_id:
                update_data["manager_id"] = str(manager_id)
            if hr_notes:
                update_data["hr_notes"] = hr_notes
            if employment_status:
                if employment_status not in ["employed", "leave", "retired", "terminated"]:
                    raise ValueError(f"Invalid employment_status: {employment_status}")
                update_data["employment_status"] = employment_status

            response = supabase.table("vault_personnel").update(
                update_data
            ).eq("id", str(personnel_id)).execute()

            if not response.data:
                raise ValueError("Personnel not found")

            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to update HR info: {str(e)}")
            raise

    @staticmethod
    async def set_primary_expertise(
        personnel_id: UUID,
        primary_expertise: str
    ) -> Dict[str, Any]:
        """
        주력 기술 영역 설정

        Args:
            personnel_id: Personnel UUID
            primary_expertise: 주력 기술명 (예: "제안서 작성", "기술평가")

        Returns:
            Updated personnel record
        """
        try:
            response = supabase.table("vault_personnel").update({
                "primary_expertise": primary_expertise,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(personnel_id)).execute()

            if not response.data:
                raise ValueError("Personnel not found")

            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to set primary expertise: {str(e)}")
            raise

    # ============================================
    # 데이터 삭제
    # ============================================

    @staticmethod
    async def delete_personnel(personnel_id: UUID) -> Dict[str, bool]:
        """
        인력 기록 soft delete

        Args:
            personnel_id: Personnel UUID

        Returns:
            Deletion confirmation
        """
        try:
            supabase.table("vault_personnel").update({
                "deleted_at": datetime.utcnow().isoformat(),
                "is_active": False
            }).eq("id", str(personnel_id)).execute()

            return {"deleted": True, "id": str(personnel_id)}
        except Exception as e:
            logger.error(f"Failed to delete personnel: {str(e)}")
            raise
