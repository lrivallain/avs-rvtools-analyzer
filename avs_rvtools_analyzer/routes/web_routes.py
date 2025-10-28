"""
Web UI routes for AVS RVTools Analyzer.
"""

import json
from typing import Any

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from ..config import AppConfig
from ..helpers import clean_value_for_json, json_serializer
from ..services import AnalysisService, FileService


def setup_web_routes(
    app: FastAPI, templates: Jinja2Templates, config: AppConfig, host: str, port: int
) -> None:
    """Setup web UI routes for the FastAPI application."""

    # Initialize services
    file_service = FileService(config.files)
    analysis_service = AnalysisService()

    @app.get(
        "/",
        response_class=HTMLResponse,
        tags=["Web UI"],
        summary="Landing Page",
        description="Main web interface for RVTools analysis",
    )
    async def index(request: Request):
        """Enhanced landing page with API links using configuration."""
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "api_info": {
                    "host": host,
                    "port": port,
                    "endpoints": config.get_endpoint_urls(host, port),
                }
            },
        )

    @app.post(
        "/explore",
        response_class=HTMLResponse,
        tags=["Web UI"],
        summary="Explore RVTools File",
        description="Upload and explore RVTools Excel file contents",
    )
    async def explore_file(request: Request, file: UploadFile = File(...), filterPoweredOff: bool = Form(False)):
        """Upload and explore RVTools Excel file contents."""
        try:
            # Validate file
            file_service.validate_file(file)

            # Load Excel file directly from memory (no temp file)
            excel_data = await file_service.load_excel_file_from_memory(file, filter_powered_off=filterPoweredOff)

            # Extract sheets data
            sheets = file_service.get_excel_sheets_data(excel_data)

            return templates.TemplateResponse(
                request=request,
                name="explore.html",
                context={"sheets": sheets, "filename": file.filename},
            )

        except Exception as e:
            return templates.TemplateResponse(
                request=request, name="error.html", context={"message": str(e)}
            )

    @app.post(
        "/analyze",
        response_class=HTMLResponse,
        tags=["Web UI"],
        summary="Analyze Migration Risks",
        description="Upload and analyze RVTools file for migration risks and compatibility issues",
    )
    async def analyze_migration_risks(request: Request, file: UploadFile = File(...), filterPoweredOff: bool = Form(False)):
        """Upload and analyze RVTools file for migration risks and compatibility issues."""
        try:
            # Validate file
            file_service.validate_file(file)

            # Load Excel file directly from memory (no temp file)
            excel_data = await file_service.load_excel_file_from_memory(file, filter_powered_off=filterPoweredOff)

            # Validate Excel data for analysis
            analysis_service.validate_excel_data(excel_data)

            # Perform risk analysis
            risk_results = analysis_service.analyze_risks(
                excel_data, include_details=True, filter_zero_counts=True
            )

            return templates.TemplateResponse(
                request=request,
                name="analyze.html",
                context={
                    "filename": file.filename,
                    "risk_results": risk_results,
                },
            )

        except Exception as e:
            return templates.TemplateResponse(
                request=request, name="error.html", context={"message": str(e)}
            )

    @app.post(
        "/convert-to-json",
        tags=["Web UI"],
        summary="Convert to JSON",
        description="Upload and convert RVTools Excel file to JSON format for download",
    )
    async def convert_to_json(request: Request, file: UploadFile = File(...), filterPoweredOff: bool = Form(False)):
        """Upload and convert RVTools Excel file to JSON format for download."""
        try:
            # Validate file
            file_service.validate_file(file)

            # Load Excel file directly from memory (no temp file)
            excel_data = await file_service.load_excel_file_from_memory(file, filter_powered_off=filterPoweredOff)

            # Convert to JSON format - simplified output just like the API
            json_result = {}
            for sheet_name, sheet_info in excel_data.items():
                # Get the data from the sheet
                sheet_data = sheet_info.get("data", [])

                # Remove rows where all values are None/empty
                filtered_data = []
                for row in sheet_data:
                    if any(
                        value is not None and str(value).strip() != ""
                        for value in row.values()
                    ):
                        # Clean each value for JSON serialization
                        cleaned_row = {
                            k: clean_value_for_json(v) for k, v in row.items()
                        }
                        filtered_data.append(cleaned_row)

                # Store only the data for this sheet
                json_result[sheet_name] = filtered_data

            # Convert to JSON string with nice formatting
            json_content = json.dumps(
                json_result, indent=2, ensure_ascii=False, default=json_serializer
            )

            # Create filename based on original file
            original_name = (
                file.filename.rsplit(".", 1)[0] if file.filename else "rvtools_export"
            )
            json_filename = f"{original_name}.json"

            # Return as downloadable JSON file
            return Response(
                content=json_content,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={json_filename}"
                },
            )

        except Exception as e:
            return templates.TemplateResponse(
                request=request, name="error.html", context={"message": str(e)}
            )
