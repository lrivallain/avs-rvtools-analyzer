"""
MCP Server for RVTools Analyzer with integrated web UI.
Exposes RVTools analysis capabilities through Model Context Protocol and web interface.
"""
import asyncio
import json
import tempfile
import os
from pathlib import Path
from typing import Any, Dict, List
from contextlib import asynccontextmanager
import numpy as np
import xlrd

import pandas as pd
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Optional
import logging

from .risk_detection import gather_all_risks, get_available_risks
from .helpers import load_sku_data
from .utils import (
    convert_mib_to_human_readable,
    allowed_file,
    get_risk_badge_class,
    get_risk_display_name,
    ColoredFormatter)
from .config import AppConfig
from .routes.web_routes import setup_web_routes
from .routes.api_routes import setup_api_routes
from .core.error_handlers import setup_error_handlers
from . import __version__ as calver_version

# Set up logger with custom formatter
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplication
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Create console handler with custom formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter())
logger.addHandler(console_handler)

# Prevent propagation to avoid duplicate logs
logger.propagate = False


class RVToolsAnalyzeServer:
    """HTTP/MCP API Server for AVS RVTools analysis capabilities with integrated web UI."""

    def __init__(self, config: AppConfig = None):
        self.config = config or AppConfig()
        self.temp_files = []  # Track temporary files for cleanup

        # Use configuration for paths
        self.base_dir = self.config.paths.base_dir
        self.templates_dir = self.config.paths.templates_dir
        self.static_dir = self.config.paths.static_dir

    def _clean_nan_values(self, obj):
        """Recursively clean NaN values from nested dictionaries and lists."""
        if isinstance(obj, dict):
            return {key: self._clean_nan_values(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_nan_values(item) for item in obj]
        elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
            return None
        elif pd.isna(obj):
            return None
        else:
            return obj

    async def run(self, host: str = None, port: int = None):
        """Run the HTTP/MCP API server with integrated web UI."""
        # Use config defaults if not provided
        host = host or self.config.server.host
        port = port or self.config.server.port

        # Initialize MCP app
        mcp = FastMCP(self.config.mcp.name)
        mcp_app = mcp.http_app(path='/')

        # Create FastAPI app with configuration
        app = FastAPI(
            title=self.config.fastapi.title,
            version=calver_version,
            description=self.config.fastapi.description,
            tags_metadata=self.config.fastapi.tags_metadata,
            lifespan=mcp_app.lifespan
        )

        # Mount MCP app
        app.mount(self.config.mcp.mount_path, mcp_app)

        # Setup Jinja2 templates
        templates = Jinja2Templates(directory=str(self.templates_dir))
        self._setup_jinja_templates(templates)

        # Setup static files if they exist
        if self.static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")

        # Add CORS middleware with configuration
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors.allow_origins,
            allow_credentials=self.config.cors.allow_credentials,
            allow_methods=self.config.cors.allow_methods,
            allow_headers=self.config.cors.allow_headers,
        )

        # Setup routes using modules
        setup_web_routes(app, templates, self.config, host, port)
        setup_api_routes(app, mcp, self.config)

        # Setup error handlers for custom exceptions
        setup_error_handlers(app, templates)

        # Log server startup information
        self._log_server_info(host, port)

        # Run the FastAPI server
        import uvicorn
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level=self.config.server.log_level,
            timeout_graceful_shutdown=self.config.server.timeout_graceful_shutdown
        )
        server = uvicorn.Server(config)
        await server.serve()

    def _setup_jinja_templates(self, templates: Jinja2Templates) -> None:
        """Setup Jinja2 template configuration."""
        templates.env.filters['convert_mib_to_human_readable'] = convert_mib_to_human_readable
        templates.env.globals['calver_version'] = calver_version
        templates.env.globals['get_risk_badge_class'] = get_risk_badge_class
        templates.env.globals['get_risk_display_name'] = get_risk_display_name

    def _log_server_info(self, host: str, port: int) -> None:
        """Log server startup information."""
        logger.info(f"🚀 AVS RVTools Analyzer server starting...")
        logger.info(f"  🌐 Web UI: http://{host}:{port}")
        logger.info(f"  📊 API docs: http://{host}:{port}/docs")
        logger.info(f"  💊 Health check: http://{host}:{port}/health")
        logger.info(f"  📄 OpenAPI JSON: http://{host}:{port}/openapi.json")
        logger.info(f"  🔗 MCP API: http://{host}:{port}/mcp")

async def server_main():
    """Main entry point for the MCP server."""
    import argparse

    # Create default config to get default values
    default_config = AppConfig()

    parser = argparse.ArgumentParser(description="AVS RVTools Analyzer")
    parser.add_argument("--host", default=default_config.server.host, help=f"Host to bind to (default: {default_config.server.host})")
    parser.add_argument("--port", type=int, default=default_config.server.port, help=f"Port to bind to (default: {default_config.server.port})")

    args = parser.parse_args()

    server = RVToolsAnalyzeServer()
    await server.run(host=args.host, port=args.port)


def main():
    """Entry point that can be called directly."""
    try:
        asyncio.run(server_main())
    except KeyboardInterrupt:
        logger.info("Shutting down server.")


if __name__ == "__main__":
    main()