"""
API and MCP routes for AVS RVTools Analyzer.
Combines both REST API endpoints and MCP tool definitions.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .. import __version__ as calver_version
from ..config import AppConfig
from ..helpers import clean_value_for_json
from ..models import (
    AISuggestionRequest,
    AISuggestionResponse,
    AnalysisResponse,
    APIInfoResponse,
    AvailableRisksResponse,
    AzureOpenAIStatusResponse,
    ErrorResponse,
    ExcelSheetInfo,
    ExcelToJsonResponse,
    HealthResponse,
    RiskTypeInfo,
    SKUCapabilitiesResponse,
    SKUInfo,
)
from ..services import AnalysisService, FileService, SKUService
from ..services.azure_openai_service import AzureOpenAIService

logger = logging.getLogger(__name__)


class AnalyzeFileRequest(BaseModel):
    """Request model for file analysis."""

    file_path: str
    include_details: Optional[bool] = False
    filter_powered_off: Optional[bool] = False


class AnalyzeJsonRequest(BaseModel):
    """Request model for JSON data analysis."""

    data: Dict[str, List[Dict[str, Any]]] = Field(
        description="JSON data organized by sheet name"
    )
    include_details: Optional[bool] = Field(
        default=False, description="Include detailed analysis results"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": {
                    "vInfo": [
                        {
                            "VM": "VM-001",
                            "Power": "poweredOn",
                            "CPUs": 4,
                            "Memory": 8192,
                        },
                        {
                            "VM": "VM-002",
                            "Power": "poweredOff",
                            "CPUs": 2,
                            "Memory": 4096,
                        },
                    ],
                    "vCPU": [
                        {"VM": "VM-001", "CPU Usage": "25%"},
                        {"VM": "VM-002", "CPU Usage": "0%"},
                    ],
                },
                "include_details": False,
            }
        }
    }


def setup_api_routes(app: FastAPI, mcp: FastMCP, config: AppConfig) -> None:
    """Setup API and MCP routes for the FastAPI application."""

    # Initialize services
    file_service = FileService(config.files)
    analysis_service = AnalysisService()
    sku_service = SKUService(config.paths.sku_data_file)
    azure_openai_service = AzureOpenAIService()

    # API Routes
    @app.get(
        "/api/info",
        tags=["API"],
        summary="Server Information",
        description="Get server information and available endpoints",
        response_model=APIInfoResponse,
    )
    async def api_info():
        """Get server information and available endpoints."""
        return APIInfoResponse(
            name=config.fastapi.title,
            version=calver_version,
            description="HTTP / MCP API for RVTools analysis capabilities",
            documentation_url=f"http://{config.server.host}:{config.server.port}/docs",
            openapi_url=f"http://{config.server.host}:{config.server.port}/openapi.json",
            mcp_enabled=True,
            endpoints={
                "web_ui": config.endpoints.web_ui,
                "analyze": config.endpoints.analyze,
                "analyze_upload": config.endpoints.analyze_upload,
                "analyze_json": config.endpoints.analyze_json,
                "convert_to_json": config.endpoints.convert_to_json,
                "available_risks": config.endpoints.available_risks,
                "sku_capabilities": config.endpoints.sku_capabilities,
                "health": config.endpoints.health,
            },
        )

    @app.get(
        "/health",
        tags=["API"],
        summary="Health Check",
        description="Check server health status",
        response_model=HealthResponse,
    )
    async def health():
        """Check server health status."""
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(UTC).isoformat() + "Z",
            version=calver_version,
        )

    # Combined API/MCP Routes
    @mcp.tool(
        name="list_available_risks",
        description="List all migration risks that can be assessed by this tool.",
        tags={"risks", "assessment"},
    )
    @app.get(
        "/api/risks",
        tags=["API"],
        summary="Available Risk Assessments",
        description="List all migration risks that can be assessed by this tool",
        response_model=AvailableRisksResponse,
    )
    async def list_available_risks():
        """Get information about all available risk detection capabilities."""
        risks_info = analysis_service.get_available_risk_types()

        # Transform the risks data to match our response model
        risk_types = []
        for risk_name, risk_data in risks_info.get("risks", {}).items():
            risk_types.append(
                RiskTypeInfo(
                    name=risk_name,
                    function_name=risk_data.get("function_name", risk_name),
                    description=risk_data.get("description", ""),
                    risk_level=risk_data.get("risk_level", "info"),
                    alert_message=risk_data.get("alert_message"),
                    category=risk_data.get("category"),
                )
            )

        return AvailableRisksResponse(
            success=True,
            message=f"Found {len(risk_types)} available risk assessments",
            total_risks=len(risk_types),
            risks=risk_types,
        )

    @mcp.tool(
        name="get_sku_capabilities",
        description="Get Azure VMware Solution (AVS) SKU hardware capabilities and specifications.",
        tags={"sku", "hardware", "capabilities"},
    )
    @app.get(
        "/api/sku",
        tags=["API"],
        summary="AVS SKU Capabilities",
        description="Get Azure VMware Solution (AVS) SKU hardware capabilities and specifications",
        response_model=SKUCapabilitiesResponse,
    )
    async def get_sku_capabilities():
        """Get AVS SKU hardware capabilities and specifications."""
        sku_data = sku_service.get_sku_capabilities()

        # Transform SKU data to match our response model
        skus = []
        for sku in sku_data:
            skus.append(SKUInfo(**sku))

        return skus

    @mcp.tool(
        name="analyze_file",
        description="Analyze RVTools file by providing a file path on the server.",
        tags={"analysis", "file", "local"},
    )
    @app.post(
        "/api/analyze",
        tags=["API"],
        summary="Analyze RVTools File (Path)",
        description="Analyze RVTools file by providing a file path on the server",
        response_model=AnalysisResponse,
    )
    async def analyze_file(request: AnalyzeFileRequest):
        """Analyze RVTools file by file path."""
        file_path = Path(request.file_path)

        # Load Excel file
        excel_data = file_service.load_excel_file(file_path, filter_powered_off=request.filter_powered_off)

        # Validate Excel data
        analysis_service.validate_excel_data(excel_data)

        # Perform analysis
        result = analysis_service.analyze_risks(
            excel_data, include_details=request.include_details, filter_zero_counts=True
        )

        return AnalysisResponse(
            success=True,
            message="Analysis completed successfully",
            risks=result.get("risks", {}),
            summary=result.get("summary"),
            total_risks_found=len(
                [r for r in result.get("risks", {}).values() if r.get("count", 0) > 0]
            ),
            analysis_timestamp=datetime.now(UTC).isoformat() + "Z",
        )

    @mcp.tool(
        name="analyze_uploaded_file",
        description="Upload and analyze RVTools Excel file for migration risks and compatibility issues.",
        tags={"analysis", "upload"},
    )
    @app.post(
        "/api/analyze-upload",
        tags=["API"],
        summary="Analyze RVTools File (Upload)",
        description="Upload and analyze RVTools Excel file for migration risks and compatibility issues",
        response_model=AnalysisResponse,
    )
    async def analyze_uploaded_file(
        file: UploadFile = File(...), include_details: bool = Form(False), filter_powered_off: bool = Form(False)
    ):
        """Analyze uploaded RVTools file."""
        # Validate file
        file_service.validate_file(file)

        # Load Excel file directly from memory (no temp file)
        excel_data = await file_service.load_excel_file_from_memory(file, filter_powered_off=filter_powered_off)

        # Validate Excel data
        analysis_service.validate_excel_data(excel_data)

        # Perform analysis
        result = analysis_service.analyze_risks(
            excel_data, include_details=include_details, filter_zero_counts=True
        )

        return AnalysisResponse(
            success=True,
            message="Analysis completed successfully",
            risks=result.get("risks", {}),
            summary=result.get("summary"),
            total_risks_found=len(
                [r for r in result.get("risks", {}).values() if r.get("count", 0) > 0]
            ),
            analysis_timestamp=datetime.now(UTC).isoformat() + "Z",
        )

    @mcp.tool(
        name="analyze_json_data",
        description="Analyze JSON data for migration risks and compatibility issues.",
        tags={"analysis", "json"},
    )
    @app.post(
        "/api/analyze-json",
        tags=["API"],
        summary="Analyze JSON Data",
        description="Analyze JSON data (e.g., from converted Excel) for migration risks and compatibility issues",
        response_model=AnalysisResponse,
    )
    async def analyze_json_data(request: AnalyzeJsonRequest):
        """Analyze JSON data for migration risks."""
        try:
            # Convert JSON data to the format expected by analysis service
            # The request.data should be in format: {"sheet_name": [{"col1": "val1", ...}, ...]}
            excel_data = {}
            for sheet_name, sheet_data in request.data.items():
                # Extract headers from first row if data exists
                headers = list(sheet_data[0].keys()) if sheet_data else []

                excel_data[sheet_name] = {
                    "headers": headers,
                    "data": sheet_data,
                    "row_count": len(sheet_data),
                }

            # Validate Excel data
            analysis_service.validate_excel_data(excel_data)

            # Perform analysis
            result = analysis_service.analyze_risks(
                excel_data,
                include_details=request.include_details,
                filter_zero_counts=True,
            )

            return AnalysisResponse(
                success=True,
                message="JSON data analysis completed successfully",
                risks=result.get("risks", {}),
                summary=result.get("summary"),
                total_risks_found=len(
                    [
                        r
                        for r in result.get("risks", {}).values()
                        if r.get("count", 0) > 0
                    ]
                ),
                analysis_timestamp=datetime.now(UTC).isoformat() + "Z",
            )

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error analyzing JSON data: {str(e)}"
            )

    @mcp.tool(
        name="convert_excel_to_json",
        description="Convert Excel file to JSON format for AI model consumption.",
        tags={"conversion", "json", "excel"},
    )
    @app.post(
        "/api/convert-to-json",
        tags=["API"],
        summary="Convert Excel to JSON",
        description="Convert uploaded Excel file to JSON format for AI model analysis",
    )
    async def convert_excel_to_json(
        file: UploadFile = File(...),
        include_empty_cells: bool = Form(False),
        max_rows_per_sheet: Optional[int] = Form(1000),
        filter_powered_off: bool = Form(False),
    ):
        """Convert Excel file to JSON format."""
        # Validate file
        file_service.validate_file(file)

        # Load Excel file directly from memory (no temp file)
        excel_data = await file_service.load_excel_file_from_memory(file, filter_powered_off=filter_powered_off)

        # Convert to simplified JSON format - just the data
        json_result = {}
        for sheet_name, sheet_info in excel_data.items():
            # Get the data from the sheet
            sheet_data = sheet_info.get("data", [])

            # Limit rows if specified
            if max_rows_per_sheet and len(sheet_data) > max_rows_per_sheet:
                sheet_data = sheet_data[:max_rows_per_sheet]

            # Process data based on include_empty_cells flag
            if not include_empty_cells:
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
                sheet_data = filtered_data
            else:
                # Still clean values even when including empty cells
                sheet_data = [
                    {k: clean_value_for_json(v) for k, v in row.items()}
                    for row in sheet_data
                ]

            # Store only the data for this sheet
            json_result[sheet_name] = sheet_data

        # Return simplified response with just the data
        return json_result

    # Azure OpenAI Integration Endpoints

    @app.post(
        "/api/ai-suggestion",
        tags=["AI Integration"],
        summary="Get AI Risk Analysis Suggestion",
        description="Get AI-powered suggestions for a specific migration risk using Azure OpenAI",
        response_model=AISuggestionResponse,
    )
    async def get_ai_suggestion(request: AISuggestionRequest):
        """Get AI-powered suggestions for a specific migration risk."""
        try:
            # Debug logging
            logger.debug(f"AI suggestion request for risk: {request.risk_name}")
            logger.debug(
                f"Risk data count: {len(request.risk_data) if request.risk_data else 0}"
            )
            logger.debug(
                f"Risk data sample: {request.risk_data[:3] if request.risk_data and len(request.risk_data) > 0 else 'Empty or None'}"
            )

            # Check if Azure OpenAI is configured via environment variables
            if not azure_openai_service.is_configured:
                return AISuggestionResponse(
                    success=False,
                    error="Azure OpenAI not configured via environment variables",
                    risk_name=request.risk_name,
                )

            # Get AI suggestion
            result = azure_openai_service.get_risk_analysis_suggestion(
                risk_name=request.risk_name,
                risk_description=request.risk_description,
                risk_data=request.risk_data,
                risk_level=request.risk_level,
            )

            if result:
                return AISuggestionResponse(
                    success=True,
                    suggestion=result["suggestion"],
                    risk_name=request.risk_name,
                    tokens_used=result["tokens_used"],
                    input_tokens=result["input_tokens"],
                    output_tokens=result["output_tokens"],
                    carbon_footprint=result["carbon_footprint"],
                )
            else:
                return AISuggestionResponse(
                    success=False,
                    error="Failed to generate AI suggestion",
                    risk_name=request.risk_name,
                )

        except Exception as e:
            return AISuggestionResponse(
                success=False,
                error=f"Error generating AI suggestion: {str(e)}",
                risk_name=request.risk_name,
            )

    @app.get(
        "/api/azure-openai-status",
        tags=["AI Integration"],
        summary="Get Azure OpenAI Configuration Status",
        description="Get the current configuration status of Azure OpenAI integration",
        response_model=AzureOpenAIStatusResponse,
    )
    async def get_azure_openai_status():
        """Get Azure OpenAI configuration status."""
        try:
            status = azure_openai_service.get_configuration_status()
            return AzureOpenAIStatusResponse(
                is_configured=status["is_configured"],
                deployment_name=status["deployment_name"],
            )
        except Exception as e:
            return AzureOpenAIStatusResponse(is_configured=False, deployment_name=None)
