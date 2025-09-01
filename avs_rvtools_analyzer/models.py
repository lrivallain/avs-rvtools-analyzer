"""
Data models and constants for RVTools risk detection.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, Enum):
    """Enumeration of risk levels."""

    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    BLOCKING = "blocking"
    EMERGENCY = "emergency"


class RiskInfo(BaseModel):
    """Model for risk information metadata."""

    description: str
    alert_message: Optional[str] = None


class RiskResult(BaseModel):
    """Base model for risk detection results."""

    count: int = Field(ge=0, description="Number of items found with this risk")
    data: Union[List[Dict[str, Any]], Dict[str, Any]] = Field(
        default_factory=list, description="Detailed data for each risk item"
    )
    risk_level: RiskLevel = Field(description="Severity level of the risk")
    function_name: str = Field(description="Name of the detection function")
    risk_info: RiskInfo = Field(description="Risk metadata")
    error: Optional[str] = Field(None, description="Error message if detection failed")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional details specific to the risk type"
    )

    model_config = ConfigDict(use_enum_values=True)


# Response Models for API Endpoints


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(description="Service status")
    timestamp: str = Field(description="Current timestamp")
    version: Optional[str] = Field(None, description="Application version")
    uptime: Optional[str] = Field(None, description="Service uptime")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2025-08-20T10:30:00Z",
                "version": "1.0.0",
                "uptime": "0:05:30",
            }
        }
    )


class FileUploadResponse(BaseModel):
    """Response model for file upload operations."""

    success: bool = Field(description="Whether the upload was successful")
    message: str = Field(description="Status message")
    file_id: Optional[str] = Field(
        None, description="Unique identifier for the uploaded file"
    )
    filename: Optional[str] = Field(None, description="Original filename")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    sheets_found: Optional[List[str]] = Field(
        None, description="List of sheet names found in Excel file"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "File uploaded successfully",
                "file_id": "temp_12345",
                "filename": "rvtools_export.xlsx",
                "file_size": 2048576,
                "sheets_found": ["vInfo", "vCPU", "vMemory", "vDisk", "vNetwork"],
            }
        }
    )


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""

    success: bool = Field(True, description="Whether the analysis was successful")
    message: Optional[str] = Field(None, description="Status message")
    risks: Dict[str, Any] = Field(description="Risk detection results")
    summary: Optional[Dict[str, Any]] = Field(None, description="Analysis summary")
    total_risks_found: Optional[int] = Field(
        None, description="Total number of risk types with findings"
    )
    analysis_timestamp: Optional[str] = Field(
        None, description="When the analysis was performed"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Analysis completed successfully",
                "risks": {
                    "powered_off_vms": {
                        "count": 5,
                        "risk_level": "warning",
                        "function_name": "detect_powered_off_vms",
                        "risk_info": {
                            "description": "VMs that are powered off",
                            "alert_message": (
                                "These VMs are consuming resources but not providing value"
                            ),
                        },
                    }
                },
                "total_risks_found": 1,
                "analysis_timestamp": "2025-08-20T10:30:00Z",
            }
        }
    )


class RiskTypeInfo(BaseModel):
    """Model for risk type information."""

    name: str = Field(description="Risk type name")
    function_name: str = Field(description="Detection function name")
    description: str = Field(description="Risk description")
    risk_level: RiskLevel = Field(description="Default risk level")
    alert_message: Optional[str] = Field(None, description="Alert message")
    category: Optional[str] = Field(None, description="Risk category")

    model_config = ConfigDict(use_enum_values=True)


class AvailableRisksResponse(BaseModel):
    """Response model for available risk types."""

    success: bool = Field(True, description="Whether the request was successful")
    message: Optional[str] = Field(None, description="Status message")
    total_risks: int = Field(description="Total number of available risk types")
    risks: List[RiskTypeInfo] = Field(description="List of available risk types")
    total_risk_types: Optional[int] = Field(
        None, description="Total number of available risk types (alias)"
    )
    risk_types: Optional[List[RiskTypeInfo]] = Field(
        None, description="List of available risk types (alias)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Retrieved available risk types",
                "total_risk_types": 14,
                "risk_types": [
                    {
                        "name": "powered_off_vms",
                        "function_name": "detect_powered_off_vms",
                        "description": "Virtual machines that are powered off",
                        "risk_level": "warning",
                        "alert_message": (
                            "These VMs consume resources without providing value"
                        ),
                    }
                ],
            }
        }
    )


class SKUInfo(BaseModel):
    """Model for SKU information based on sku.json structure."""

    name: str = Field(description="SKU name")
    cores: int = Field(description="Number of CPU cores")
    ram: int = Field(description="Memory in GB")
    cpu_model: str = Field(description="CPU model")
    cpu_architecture: str = Field(description="CPU architecture")
    cpu_speed_ghz: float = Field(description="CPU base speed in GHz")
    cpu_turbo_speed_ghz: float = Field(description="CPU turbo speed in GHz")
    cpu_number: int = Field(description="Number of CPUs")
    logical_threads_with_hyperthreading: int = Field(
        description="Total logical threads"
    )
    vsan_architecture: str = Field(description="vSAN architecture")
    vsan_cache_capacity_in_tb: float = Field(description="vSAN cache capacity in TB")
    vsan_cache_storage_technology: str = Field(
        description="vSAN cache storage technology"
    )
    vsan_capacity_tier_in_tb: float = Field(description="vSAN capacity tier in TB")
    vsan_capacity_tier_storage_technology: str = Field(
        description="vSAN capacity storage technology"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Standard_D32s_v3",
                "cpu_cores": 32,
                "memory_gb": 128,
                "storage_tb": 1.0,
                "max_vms": 50,
                "regions": ["East US", "West US", "North Europe"],
            }
        }
    )


# SKU capabilities response is just a list of SKUInfo objects
SKUCapabilitiesResponse = List[SKUInfo]


class ErrorResponse(BaseModel):
    """Standardized error response model."""

    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(description="Error type or category")
    message: str = Field(description="Human-readable error message")
    status_code: int = Field(description="HTTP status code")
    error_code: Optional[str] = Field(
        None, description="Error code for programmatic handling"
    )
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    timestamp: Optional[str] = Field(None, description="When the error occurred")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error_code": "FILE_VALIDATION_ERROR",
                "message": (
                    "Invalid file format. Only Excel files (.xlsx, .xls) are supported."
                ),
                "details": {
                    "filename": "document.pdf",
                    "allowed_extensions": ["xlsx", "xls"],
                },
                "timestamp": "2025-08-20T10:30:00Z",
            }
        }
    )


class APIInfoResponse(BaseModel):
    """Response model for API information."""

    name: str
    version: str
    description: str
    endpoints: Dict[str, str]
    documentation_url: Optional[str] = None
    openapi_url: Optional[str] = None
    mcp_enabled: bool = True


class ExcelSheetInfo(BaseModel):
    """Model for Excel sheet information in JSON conversion."""

    data: List[Dict[str, Any]] = Field(description="Sheet data as list of dictionaries")
    row_count: int = Field(description="Number of rows in the sheet")
    column_count: int = Field(description="Number of columns in the sheet")
    columns: List[str] = Field(description="List of column names")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": [
                    {"VM": "VM-001", "Power": "poweredOn", "CPUs": 4, "Memory": 8192},
                    {"VM": "VM-002", "Power": "poweredOff", "CPUs": 2, "Memory": 4096},
                ],
                "row_count": 2,
                "column_count": 4,
                "columns": ["VM", "Power", "CPUs", "Memory"],
            }
        }
    )


class ExcelToJsonResponse(BaseModel):
    """Response model for Excel to JSON conversion."""

    success: bool = Field(True, description="Whether the conversion was successful")
    message: str = Field(description="Status message")
    filename: str = Field(description="Original filename")
    sheets: List[str] = Field(description="List of sheet names")
    total_sheets: int = Field(description="Total number of sheets converted")
    conversion_timestamp: str = Field(description="When the conversion was performed")
    data: Dict[str, ExcelSheetInfo] = Field(
        description="Converted data organized by sheet name"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Successfully converted Excel file to JSON format",
                "filename": "rvtools_export.xlsx",
                "sheets": ["vInfo", "vCPU", "vMemory"],
                "total_sheets": 3,
                "conversion_timestamp": "2025-08-21T10:30:00Z",
                "data": {
                    "vInfo": {
                        "data": [{"VM": "VM-001", "Power": "poweredOn"}],
                        "row_count": 1,
                        "column_count": 2,
                        "columns": ["VM", "Power"],
                    }
                },
            }
        }
    )


# Constants
class ESXVersionThresholds:
    """ESX version thresholds for risk assessment."""

    WARNING_THRESHOLD = "7.0.0"
    ERROR_THRESHOLD = "6.5.0"


class StorageThresholds:
    """Storage-related thresholds."""

    LARGE_VM_PROVISIONED_TB = 10  # TB
    MIB_TO_TB_CONVERSION = 1.048576 / (1024 * 1024)


class PowerStates:
    """VM power states."""

    POWERED_ON = "poweredOn"
    SUSPENDED = "Suspended"


class GuestStates:
    """VM guest states."""

    NOT_RUNNING = "notRunning"


class NetworkConstants:
    """Network-related constants."""

    STANDARD_VSWITCH = "standard vSwitch"


class StorageConstants:
    """Storage-related constants."""

    INDEPENDENT_PERSISTENT = "independent_persistent"
    LARGE_VM_THRESHOLD_TB = 10


# Azure OpenAI Integration Models


class AISuggestionRequest(BaseModel):
    """Request model for AI risk analysis suggestions."""

    risk_name: str = Field(description="Name of the risk function")
    risk_description: str = Field(description="Description of the risk")
    risk_data: List[Dict[str, Any]] = Field(description="Risk data items")
    risk_level: str = Field(description="Risk severity level")


class AISuggestionResponse(BaseModel):
    """Response model for AI risk analysis suggestions."""

    success: bool = Field(
        description="Whether the suggestion generation was successful"
    )
    suggestion: Optional[str] = Field(None, description="AI-generated suggestion")
    error: Optional[str] = Field(None, description="Error message if failed")
    risk_name: str = Field(description="Name of the risk that was analyzed")
    tokens_used: Optional[int] = Field(
        None, description="Number of tokens used in the AI request"
    )
    input_tokens: Optional[int] = Field(
        None, description="Number of input tokens used in the AI request"
    )
    output_tokens: Optional[int] = Field(
        None, description="Number of output tokens generated by the AI"
    )
    carbon_footprint: Optional[float] = Field(
        None, description="Carbon footprint estimation data"
    )


class AzureOpenAIStatusResponse(BaseModel):
    """Response model for Azure OpenAI configuration status."""

    is_configured: bool = Field(
        description="Whether Azure OpenAI is configured via environment variables"
    )
    deployment_name: Optional[str] = Field(
        None, description="Deployment name if configured via env vars"
    )
