"""공유 Literal 타입 — 여러 스키마에서 import하여 사용."""

from typing import Literal

# ── 사용자/조직 ──
UserRole = Literal["member", "lead", "director", "executive", "admin"]
UserStatus = Literal["active", "inactive", "suspended"]

# ── 제안서 ──
ProposalStatus = Literal[
    "initialized", "running", "processing", "searching", "analyzing", "strategizing",
    "submitted", "presented", "won", "lost", "no_go", "on_hold",
    "expired", "abandoned", "retrospect", "completed",
]
ProposalResult = Literal["won", "lost", "void"]

# ── 범위/필터 ──
ScopeType = Literal["team", "division", "org"]
ImpactLevel = Literal["high", "medium", "low"]
Granularity = Literal["monthly", "quarterly", "yearly"]

# ── 교훈 ──
LessonCategory = Literal["strategy", "pricing", "team", "technical", "process", "other"]

# ── Q&A ──
QACategory = Literal[
    "technical", "management", "pricing", "experience", "team", "general"
]
EvaluatorReaction = Literal["positive", "neutral", "negative"]

# ── 프로젝트 참여자 ──
ProjectRole = Literal["member", "section_lead"]
