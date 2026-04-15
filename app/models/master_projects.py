"""
Master Projects ORM Model

통합 마스터 프로젝트 SQLAlchemy 모델:
- 과거 프로젝트 (intranet_projects)
- 진행 중 제안 (active_proposal)
- 완료된 제안 (completed_proposal)
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Integer, Date, DateTime, Text, JSON, ARRAY, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class MasterProject(Base):
    """마스터 프로젝트 (SSOT)"""
    __tablename__ = "master_projects"

    # 기본 정보
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    org_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    project_name: Mapped[str] = mapped_column(String, nullable=False)
    project_year: Mapped[Optional[int]] = mapped_column(Integer)
    start_date: Mapped[Optional[datetime]] = mapped_column(Date)
    end_date: Mapped[Optional[datetime]] = mapped_column(Date)
    client_name: Mapped[Optional[str]] = mapped_column(String)

    # 요약/내용
    summary: Mapped[Optional[str]] = mapped_column(Text)  # 제안 최종 제출시점 입력
    description: Mapped[Optional[str]] = mapped_column(Text)

    # 재정
    budget_krw: Mapped[Optional[int]] = mapped_column(Integer)

    # 프로젝트 유형
    project_type: Mapped[str] = mapped_column(String, nullable=False)  # 'historical' | 'active_proposal' | 'completed_proposal'

    # 상태 (3개 독립 변수)
    proposal_status: Mapped[Optional[str]] = mapped_column(String)  # DRAFT | SUBMITTED | RESULT_ANNOUNCED
    result_status: Mapped[Optional[str]] = mapped_column(String)    # PENDING | WON | LOST (active_proposal만)
    execution_status: Mapped[Optional[str]] = mapped_column(String) # IN_PROGRESS | COMPLETED (result_status=WON인 경우만)

    # historical 전용 필드
    legacy_idx: Mapped[Optional[int]] = mapped_column(Integer)  # MSSQL idx_no
    legacy_code: Mapped[Optional[str]] = mapped_column(String)  # MSSQL pr_code

    # proposal 연동
    proposal_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("proposals.id"))

    # 참여자 정보 (두 그룹 분리)
    # 그룹 1: 용역수행팀 + 팀원
    actual_teams: Mapped[Optional[dict]] = mapped_column(JSONB)        # [{team_id, team_name}]
    actual_participants: Mapped[Optional[dict]] = mapped_column(JSONB) # [{name, role, team_id, years_involved}]

    # 그룹 2: 제안팀 + 제안작업참여자
    proposal_teams: Mapped[Optional[dict]] = mapped_column(JSONB)        # [{team_id, team_name}]
    proposal_participants: Mapped[Optional[dict]] = mapped_column(JSONB) # [{user_id, name, role, team_id}]

    # 문서/자료
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    archive_count: Mapped[int] = mapped_column(Integer, default=0)

    # 검색 필드
    keywords: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON)  # vector(1536) - OpenAI 임베딩

    # 감사
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 제약조건
    __table_args__ = (
        CheckConstraint(
            "project_type IN ('historical', 'active_proposal', 'completed_proposal')",
            name="check_project_type"
        ),
        CheckConstraint(
            "proposal_status IN ('DRAFT', 'SUBMITTED', 'RESULT_ANNOUNCED') OR proposal_status IS NULL",
            name="check_proposal_status"
        ),
        CheckConstraint(
            "result_status IN ('PENDING', 'WON', 'LOST') OR result_status IS NULL",
            name="check_result_status"
        ),
        CheckConstraint(
            "execution_status IN ('IN_PROGRESS', 'COMPLETED') OR execution_status IS NULL",
            name="check_execution_status"
        ),
    )

    def __repr__(self):
        return f"<MasterProject(id={self.id}, project_name={self.project_name}, type={self.project_type})>"
