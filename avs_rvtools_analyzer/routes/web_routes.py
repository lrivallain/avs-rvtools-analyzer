"""
Web UI routes for AVS RVTools Analyzer.
"""
from typing import Any

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..services import FileService, AnalysisService
from ..config import AppConfig


def setup_web_routes(
    app: FastAPI,
    templates: Jinja2Templates,
    config: AppConfig,
    host: str,
    port: int
) -> None:
    """Setup web UI routes for the FastAPI application."""

    # Initialize services
    file_service = FileService(config.files)
    analysis_service = AnalysisService()

    @app.get("/", response_class=HTMLResponse, tags=["Web UI"], summary="Landing Page", description="Main web interface for RVTools analysis")
    async def index(request: Request):
        """Enhanced landing page with API links using configuration."""
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "api_info": {
                    "host": host,
                    "port": port,
                    "endpoints": config.get_endpoint_urls(host, port)
                }
            }
        )

    @app.post("/explore", response_class=HTMLResponse, tags=["Web UI"], summary="Explore RVTools File", description="Upload and explore RVTools Excel file contents")
    async def explore_file(request: Request, file: UploadFile = File(...)):
        """Upload and explore RVTools Excel file contents."""
        try:
            # Validate file
            file_service.validate_file(file)

            # Save uploaded file
            temp_file_path = await file_service.save_uploaded_file(file)

            try:
                # Load Excel file
                excel_data = file_service.load_excel_file(temp_file_path)

                # Extract sheets data
                sheets = file_service.get_excel_sheets_data(excel_data)

                return templates.TemplateResponse(
                    request=request,
                    name="explore.html",
                    context={
                        "sheets": sheets,
                        "filename": file.filename
                    }
                )

            finally:
                # Clean up temp file
                file_service.cleanup_temp_file(temp_file_path)

        except Exception as e:
            return templates.TemplateResponse(
                request=request,
                name="error.html",
                context={"message": str(e)}
            )

    @app.post("/analyze", response_class=HTMLResponse, tags=["Web UI"], summary="Analyze Migration Risks", description="Upload and analyze RVTools file for migration risks and compatibility issues")
    async def analyze_migration_risks(request: Request, file: UploadFile = File(...)):
        """Upload and analyze RVTools file for migration risks and compatibility issues."""
        try:
            # Validate file
            file_service.validate_file(file)

            # Save uploaded file
            temp_file_path = await file_service.save_uploaded_file(file)

            try:
                # Load Excel file
                excel_data = file_service.load_excel_file(temp_file_path)

                # Validate Excel data for analysis
                analysis_service.validate_excel_data(excel_data)

                # Perform risk analysis
                risk_results = analysis_service.analyze_risks(
                    excel_data,
                    include_details=True,
                    filter_zero_counts=True
                )

                return templates.TemplateResponse(
                    request=request,
                    name="analyze.html",
                    context={
                        "filename": file.filename,
                        "risk_results": risk_results,
                    }
                )

            finally:
                # Clean up temp file
                file_service.cleanup_temp_file(temp_file_path)

        except Exception as e:
            return templates.TemplateResponse(
                request=request,
                name="error.html",
                context={"message": str(e)}
            )
