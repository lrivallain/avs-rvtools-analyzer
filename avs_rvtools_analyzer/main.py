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
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import uvicorn
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from .risk_detection import gather_all_risks, get_available_risks
from .utils import convert_mib_to_human_readable, register_jinja_helpers, allowed_file, get_risk_badge_class, get_risk_display_name
from . import __version__ as calver_version


# Request/Response models
class AnalyzeFileRequest(BaseModel):
    file_path: str
    include_details: Optional[bool] = False

class RVToolsAnalyzeServer:
    """HTTP/MCP API Server for AVS RVTools analysis capabilities with integrated web UI."""

    def __init__(self):
        self.temp_files = []  # Track temporary files for cleanup

        # Get the directory where this file is located
        self.base_dir = Path(__file__).parent
        self.templates_dir = self.base_dir / "templates"
        self.static_dir = self.base_dir / "static"

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

    async def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Run the HTTP/MCP API server with integrated web UI."""

        # Create FastAPI app with enhanced metadata
        app = FastAPI(
            title="AVS RVTools Analyzer",
            version=calver_version,
            description="A comprehensive tool for analyzing RVTools data with both web interface and RESTful API. Supports Model Context Protocol (MCP) for AI tool integration.",
            tags_metadata=[
                {
                    "name": "Web UI",
                    "description": "Web-based user interface for uploading, exploring, and analyzing RVTools files through an interactive dashboard."
                },
                {
                    "name": "API",
                    "description": "RESTful API endpoints for programmatic access, automation, and AI tool integration via Model Context Protocol (MCP)."
                }
            ]
        )

        # Setup Jinja2 templates
        templates = Jinja2Templates(directory=str(self.templates_dir))

        # Setup static files if they exist
        if self.static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Register Jinja2 helpers (we need to adapt this for FastAPI)
        # Add custom filters to Jinja2 environment
        templates.env.filters['convert_mib_to_human_readable'] = convert_mib_to_human_readable
        templates.env.globals['calver_version'] = calver_version
        templates.env.globals['get_risk_badge_class'] = get_risk_badge_class
        templates.env.globals['get_risk_display_name'] = get_risk_display_name

        # Web UI Routes
        @app.get("/", response_class=HTMLResponse, tags=["Web UI"], summary="Landing Page", description="Main web interface for RVTools analysis")
        async def index(request: Request):
            # Enhanced landing page with API links
            return templates.TemplateResponse("index.html", {
                "request": request,
                "api_info": {
                    "host": host,
                    "port": port,
                    "endpoints": {
                        "health": f"http://{host}:{port}/health",
                        "api_docs": f"http://{host}:{port}/docs",
                        "redoc": f"http://{host}:{port}/redoc",
                        "openapi_json": f"http://{host}:{port}/openapi.json",
                        "tools_list": f"http://{host}:{port}/tools",
                        "api_info": f"http://{host}:{port}/api/info"
                    }
                }
            })

        @app.post("/explore", response_class=HTMLResponse, tags=["Web UI"], summary="Explore RVTools File", description="Upload and explore RVTools Excel file contents")
        async def explore_file(request: Request, file: UploadFile = File(...)):
            if not file.filename:
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "message": "No file selected"
                })

            if not allowed_file(file.filename, {'xlsx'}):
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "message": "Invalid file format. Please upload an Excel file (.xlsx)"
                })

            try:
                # Read file content
                content = await file.read()

                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                temp_file.write(content)
                temp_file.close()

                # Parse the Excel file
                excel_data = pd.ExcelFile(temp_file.name)
                sheets = {}
                for sheet_name in excel_data.sheet_names:
                    sheets[sheet_name] = excel_data.parse(sheet_name).to_dict(orient='records')

                # Clean up temp file
                os.unlink(temp_file.name)

                return templates.TemplateResponse("explore.html", {
                    "request": request,
                    "sheets": sheets,
                    "filename": file.filename
                })

            except Exception as e:
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "message": f"Error processing file: {str(e)}"
                })

        @app.post("/analyze", response_class=HTMLResponse, tags=["Web UI"], summary="Analyze Migration Risks", description="Upload and analyze RVTools file for migration risks and compatibility issues")
        async def analyze_migration_risks(request: Request, file: UploadFile = File(...)):
            if not file.filename:
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "message": "No file selected"
                })

            if not allowed_file(file.filename, {'xlsx'}):
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "message": "Invalid file format. Please upload an Excel file (.xlsx)"
                })

            try:
                # Read file content
                content = await file.read()

                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                temp_file.write(content)
                temp_file.close()

                try:
                    excel_data = pd.ExcelFile(temp_file.name)
                except xlrd.biffh.XLRDError:
                    os.unlink(temp_file.name)
                    return templates.TemplateResponse("error.html", {
                        "request": request,
                        "message": "The uploaded file is protected. Please unprotect the file and try again."
                    })

                # Use the risk detection module
                risk_results = gather_all_risks(excel_data)

                # Clean up temp file
                os.unlink(temp_file.name)

                return templates.TemplateResponse("analyze.html", {
                    "request": request,
                    "filename": file.filename,
                    "risk_results": risk_results,
                })

            except Exception as e:
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "message": f"Error analyzing file: {str(e)}"
                })

        # API Routes (keep existing API functionality)
        @app.get("/api/info", tags=["API"], summary="Server Information", description="Get server information and available endpoints")
        async def api_info():
            return {
                "name": "AVS RVTools Analyzer",
                "version": calver_version,
                "description": "HTTP / MCP API for RVTools analysis capabilities",
                "endpoints": {
                    "web_ui": "/",
                    "analyze": "/api/analyze",
                    "analyze_upload": "/api/analyze-upload",
                    "available_risks": "/api/risks",
                    "health": "/health",
                    "tools": "/tools"
                }
            }

        @app.get("/health", tags=["API"], summary="Health Check", description="Check server health status")
        async def health():
            return {
                "status": "healthy",
                "server": "avs-rvtools-analyzer",
                "version": calver_version
            }

        @app.get("/tools", tags=["API"], summary="Available Tools", description="List available MCP tools and their capabilities")
        async def list_tools():
            return {
                "tools": [
                    {
                        "name": "analyze_rvtools_file",
                        "description": "Analyze RVTools Excel files for migration risks (file path)",
                        "endpoint": "/api/analyze"
                    },
                    {
                        "name": "analyze_uploaded_rvtools_file",
                        "description": "Analyze uploaded RVTools Excel files for migration risks (file upload)",
                        "endpoint": "/api/analyze-upload"
                    },
                    {
                        "name": "list_available_risks",
                        "description": "Get information about all migration risks that can be assessed",
                        "endpoint": "/api/risks"
                    }
                ]
            }

        @app.get("/api/risks", tags=["API"], summary="Available Risk Assessments", description="List all migration risks that can be assessed by this tool")
        async def list_available_risks():
            """Get information about all available risk detection capabilities."""
            try:
                risks_info = get_available_risks()
                return {
                    "success": True,
                    "data": risks_info,
                    "message": f"Found {risks_info['total_available_risks']} available risk assessments"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving risk information: {str(e)}")

        @app.post("/api/analyze", tags=["API"], summary="Analyze RVTools File (Path)", description="Analyze RVTools file by providing a file path on the server")
        async def analyze_file(request: AnalyzeFileRequest):
            """Analyze RVTools file endpoint."""
            try:
                result = await self._analyze_file({
                    "file_path": request.file_path,
                    "include_details": request.include_details
                })
                return {"success": True, "data": result}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @app.post("/api/analyze-upload", tags=["API"], summary="Analyze RVTools File (Upload)", description="Upload and analyze RVTools Excel file for migration risks and compatibility issues")
        async def analyze_uploaded_file(
            file: UploadFile = File(...),
            include_details: bool = Form(False)
        ):
            """Analyze uploaded RVTools file endpoint."""
            try:
                # Validate file type
                if not file.filename.endswith(('.xlsx', '.xls')):
                    raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")

                # Save uploaded file to temporary location
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                content = await file.read()
                temp_file.write(content)
                temp_file.close()

                # Track temp file for cleanup
                self.temp_files.append(temp_file.name)

                # Analyze the file
                result = await self._analyze_file({
                    "file_path": temp_file.name,
                    "include_details": include_details
                })

                # Clean up temp file
                try:
                    os.unlink(temp_file.name)
                    self.temp_files.remove(temp_file.name)
                except:
                    pass

                return {"success": True, "data": result}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        print(f"🚀 AVS RVTools Analyzer server starting on http://{host}:{port}")
        print(f"  🌐 Web UI: http://{host}:{port}")
        print(f"  📊 API docs: http://{host}:{port}/docs")
        print(f"  💊 Health check: http://{host}:{port}/health")
        print(f"  🔧 Tools list: http://{host}:{port}/tools")
        print(f"  📄 OpenAPI JSON: http://{host}:{port}/openapi.json")

        # Run the FastAPI server
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    async def _analyze_file(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze RVTools file."""
        file_path = arguments.get("file_path")
        include_details = arguments.get("include_details", False)

        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found at {file_path}")

        try:
            # Load Excel file
            excel_data = pd.ExcelFile(file_path)

            # Perform risk analysis
            risk_results = gather_all_risks(excel_data)

            # Clean NaN values from the results
            cleaned_results = self._clean_nan_values(risk_results)

            # Filter out risks with count = 0
            filtered_risks = {
                risk_name: risk_data
                for risk_name, risk_data in cleaned_results["risks"].items()
                if risk_data.get("count", 0) > 0
            }

            # Update the cleaned results with filtered risks
            cleaned_results["risks"] = filtered_risks

            # Format results
            if include_details:
                return cleaned_results
            else:
                # Simplified summary without raw data
                summary = {
                    "summary": cleaned_results["summary"],
                    "risks": {}
                }

                for risk_name, risk_data in cleaned_results["risks"].items():
                    summary["risks"][risk_name] = {
                        "count": risk_data["count"],
                        "risk_level": risk_data.get("risk_level", "info"),
                        "risk_info": risk_data.get("risk_info", {}),
                        "has_data": len(risk_data.get("data", [])) > 0
                    }

                return summary

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error analyzing file: {str(e)}")


async def server_main():
    """Main entry point for the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="AVS RVTools Analyzer")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")

    args = parser.parse_args()

    server = RVToolsAnalyzeServer()
    await server.run(host=args.host, port=args.port)


def main():
    """Entry point that can be called directly."""
    asyncio.run(server_main())


if __name__ == "__main__":
    main()
