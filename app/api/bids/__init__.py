"""
Bid API module - handles all bidding-related endpoints.

Architecture:
- routes.py: Router configuration (21 endpoints)
- handlers.py: Endpoint handler functions
- helpers.py: Helper/support functions for handlers
- utils.py: Utility functions and constants
"""

from .routes import router

__all__ = ["router"]
