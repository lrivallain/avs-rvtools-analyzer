"""
Routes package for AVS RVTools Analyzer.
"""

from .api_routes import setup_api_routes
from .web_routes import setup_web_routes

__all__ = ["setup_web_routes", "setup_api_routes"]
