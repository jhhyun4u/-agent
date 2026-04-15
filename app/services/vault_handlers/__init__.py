"""
Vault Section Handlers - Route-specific query handlers for each Vault section
"""

from .completed_projects import CompletedProjectsHandler
from .government_guidelines import GovernmentGuidelinesHandler

__all__ = [
    "CompletedProjectsHandler",
    "GovernmentGuidelinesHandler",
]
