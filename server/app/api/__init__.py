"""
RemotDesk Server - API Routes Module
"""
from .devices import router as devices_router
from .sessions import router as sessions_router

__all__ = ["devices_router", "sessions_router"]
