"""
MCP Server for RVTools Analyzer with integrated web UI.
Exposes RVTools analysis capabilities through Model Context Protocol and web interface.
"""

import asyncio
import json
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import xlrd
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastmcp import FastMCP
from pydantic import BaseModel

from . import __version__ as calver_version
from .config import AppConfig
from .core.error_handlers import setup_error_handlers
from .helpers import load_sku_data
from .risk_detection import gather_all_risks, get_available_risks
from .routes.api_routes import setup_api_routes
from .routes.web_routes import setup_web_routes
from .utils import (
    ColoredFormatter,
    allowed_file,
    convert_mib_to_human_readable,
    get_risk_badge_class,
    get_risk_display_name,
)


def setup_logging(debug: bool = False):
    """
    Configure logging for the entire application.

    Args:
        debug: If True, set log level to DEBUG, otherwise INFO
    """
    # Set the root logger level
    root_logger = logging.getLogger()
    log_level = logging.DEBUG if debug else logging.INFO
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplication
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with custom formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter())
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Configure specific loggers for our application modules
    app_logger = logging.getLogger("avs_rvtools_analyzer")
    app_logger.setLevel(log_level)

    # Silence noisy third-party loggers unless in debug mode
    if not debug:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)


# Set up logger with custom formatter
logger = logging.getLogger(__name__)

# Global app instance for reload functionality
app = None


def create_app(config: AppConfig = None, debug: bool = False) -> FastAPI:
    """Create and configure FastAPI application."""
    # Load environment variables from .env file
    load_dotenv()
    
    config = config or AppConfig()

    # Setup logging for the entire application
    setup_logging(debug=debug)

    # Use configuration for paths
    base_dir = config.paths.base_dir
    templates_dir = config.paths.templates_dir
    static_dir = config.paths.static_dir

    # Initialize MCP app
    mcp = FastMCP(config.mcp.name)
    mcp_app = mcp.http_app(path="/")

    # Create FastAPI app with configuration
    fastapi_app = FastAPI(
        title=config.fastapi.title,
        version=calver_version,
        description=config.fastapi.description,
        tags_metadata=config.fastapi.tags_metadata,
        lifespan=mcp_app.lifespan,
    )

    # Mount MCP app
    fastapi_app.mount(config.mcp.mount_path, mcp_app)

    # Setup Jinja2 templates
    templates = Jinja2Templates(directory=str(templates_dir))
    _setup_jinja_templates(templates)

    # Setup static files if they exist
    if static_dir.exists():
        fastapi_app.mount(
            "/static", StaticFiles(directory=str(static_dir)), name="static"
        )

    # Add CORS middleware with configuration
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allow_origins,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=config.cors.allow_methods,
        allow_headers=config.cors.allow_headers,
    )

    # Setup routes using modules
    setup_web_routes(
        fastapi_app, templates, config, config.server.host, config.server.port
    )
    setup_api_routes(fastapi_app, mcp, config)

    # Setup error handlers for custom exceptions
    setup_error_handlers(fastapi_app, templates)

    return fastapi_app


def _setup_jinja_templates(templates: Jinja2Templates) -> None:
    """Setup Jinja2 template configuration."""
    templates.env.filters["convert_mib_to_human_readable"] = (
        convert_mib_to_human_readable
    )
    templates.env.globals["calver_version"] = calver_version
    templates.env.globals["get_risk_badge_class"] = get_risk_badge_class
    templates.env.globals["get_risk_display_name"] = get_risk_display_name


class RVToolsAnalyzeServer:
    """HTTP/MCP API Server for AVS RVTools analysis capabilities with integrated web UI."""

    def __init__(self, config: AppConfig = None, debug: bool = False):
        self.config = config or AppConfig()
        self.debug = debug
        self.temp_files = []  # Track temporary files for cleanup

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

    async def run(self, host: str = None, port: int = None, reload: bool = False):
        """Run the HTTP/MCP API server with integrated web UI."""
        # Use config defaults if not provided
        host = host or self.config.server.host
        port = port or self.config.server.port

        # Log server startup information
        self._log_server_info(host, port)

        # Run the FastAPI server
        import uvicorn

        # Set uvicorn log level based on debug flag
        uvicorn_log_level = "debug" if self.debug else self.config.server.log_level

        if reload:
            logger.info(f"🔄 Reload enabled")
            # Use import string for reload functionality
            uvicorn.run(
                "avs_rvtools_analyzer.main:app",
                host=host,
                port=port,
                log_level=uvicorn_log_level,
                reload=True,
                factory=True,
            )
        else:
            # Create app directly for non-reload mode
            app = create_app(self.config, self.debug)
            config = uvicorn.Config(
                app,
                host=host,
                port=port,
                log_level=uvicorn_log_level,
                timeout_graceful_shutdown=self.config.server.timeout_graceful_shutdown,
            )
            server = uvicorn.Server(config)
            await server.serve()

    def _log_server_info(self, host: str, port: int) -> None:
        """Log server startup information."""
        logger.info(f"🚀 AVS RVTools Analyzer server starting...")
        logger.info(f"  🌐 Web UI: http://{host}:{port}")
        logger.info(f"  📊 API docs: http://{host}:{port}/docs")
        logger.info(f"  💊 Health check: http://{host}:{port}/health")
        logger.info(f"  📄 OpenAPI JSON: http://{host}:{port}/openapi.json")
        logger.info(f"  🔗 MCP API: http://{host}:{port}/mcp")


# Create global app instance for reload functionality
def app():
    """Factory function to create app for uvicorn reload."""
    return create_app()


async def server_main():
    """Main entry point for the MCP server."""
    import argparse

    # Create default config to get default values
    default_config = AppConfig()

    parser = argparse.ArgumentParser(description="AVS RVTools Analyzer")
    parser.add_argument(
        "--host",
        default=default_config.server.host,
        help=f"Host to bind to (default: {default_config.server.host})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=default_config.server.port,
        help=f"Port to bind to (default: {default_config.server.port})",
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging level"
    )

    args = parser.parse_args()

    server = RVToolsAnalyzeServer(debug=args.debug)
    await server.run(host=args.host, port=args.port, reload=args.reload)


def main():
    """Entry point that can be called directly."""
    try:
        asyncio.run(server_main())
    except KeyboardInterrupt:
        logger.info("Shutting down server.")


if __name__ == "__main__":
    main()
