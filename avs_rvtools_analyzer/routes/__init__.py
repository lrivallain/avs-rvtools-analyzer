"""
Routes package for AVS RVTools Analyzer.
"""
from .web_routes import setup_web_routes
from .api_routes import setup_api_routes

__all__ = ["setup_web_routes", "setup_api_routes"]
