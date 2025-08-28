"""
Error handlers for FastAPI application.
"""

import logging
from typing import Union

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .exceptions import (
    AnalysisError,
    ConfigurationError,
    FileValidationError,
    InsufficientDataError,
    ProtectedFileError,
    RVToolsError,
    SKUDataError,
    TemporaryFileError,
    UnsupportedFileFormatError,
)

logger = logging.getLogger(__name__)


def setup_error_handlers(app, templates: Jinja2Templates = None):
    """Setup custom error handlers for the FastAPI application."""

    @app.exception_handler(FileValidationError)
    async def file_validation_error_handler(request: Request, exc: FileValidationError):
        """Handle file validation errors."""
        logger.warning(f"File validation error: {exc.message}")

        if _is_api_request(request):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": exc.to_dict(),
                    "message": exc.message,
                },
            )
        else:
            # Web UI request
            if templates:
                return templates.TemplateResponse(
                    request=request,
                    name="error.html",
                    context={"message": exc.message},
                    status_code=400,
                )
            else:
                return HTMLResponse(
                    content=f"<h1>File Validation Error</h1><p>{exc.message}</p>",
                    status_code=400,
                )

    @app.exception_handler(ProtectedFileError)
    async def protected_file_error_handler(request: Request, exc: ProtectedFileError):
        """Handle protected file errors."""
        logger.warning(f"Protected file error: {exc.message}")

        if _is_api_request(request):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": exc.to_dict(),
                    "message": exc.message,
                    "suggestion": "Please unprotect the Excel file and try again.",
                },
            )
        else:
            # Web UI request
            if templates:
                return templates.TemplateResponse(
                    request=request,
                    name="error.html",
                    context={
                        "message": exc.message,
                        "suggestion": "Please unprotect the Excel file and try again.",
                    },
                    status_code=400,
                )
            else:
                return HTMLResponse(
                    content=f"<h1>Protected File Error</h1><p>{exc.message}</p><p>Please unprotect the Excel file and try again.</p>",
                    status_code=400,
                )

    @app.exception_handler(AnalysisError)
    async def analysis_error_handler(request: Request, exc: AnalysisError):
        """Handle analysis errors."""
        logger.error(f"Analysis error: {exc.message}")

        if _is_api_request(request):
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": exc.to_dict(),
                    "message": exc.message,
                },
            )
        else:
            # Web UI request
            if templates:
                return templates.TemplateResponse(
                    request=request,
                    name="error.html",
                    context={"message": f"Analysis failed: {exc.message}"},
                    status_code=500,
                )
            else:
                return HTMLResponse(
                    content=f"<h1>Analysis Error</h1><p>{exc.message}</p>",
                    status_code=500,
                )

    @app.exception_handler(SKUDataError)
    async def sku_data_error_handler(request: Request, exc: SKUDataError):
        """Handle SKU data errors."""
        logger.error(f"SKU data error: {exc.message}")

        return JSONResponse(
            status_code=500 if exc.sku_name else 404,
            content={"success": False, "error": exc.to_dict(), "message": exc.message},
        )

    @app.exception_handler(InsufficientDataError)
    async def insufficient_data_error_handler(
        request: Request, exc: InsufficientDataError
    ):
        """Handle insufficient data errors."""
        logger.warning(f"Insufficient data error: {exc.message}")

        if _is_api_request(request):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": exc.to_dict(),
                    "message": exc.message,
                    "missing_sheets": exc.missing_sheets,
                },
            )
        else:
            # Web UI request
            missing_info = (
                f" Missing sheets: {', '.join(exc.missing_sheets)}"
                if exc.missing_sheets
                else ""
            )
            if templates:
                return templates.TemplateResponse(
                    request=request,
                    name="error.html",
                    context={
                        "message": exc.message + missing_info,
                        "suggestion": (
                            "Please ensure your RVTools export contains all required data."
                        ),
                    },
                    status_code=400,
                )
            else:
                return HTMLResponse(
                    content=f"<h1>Insufficient Data</h1><p>{exc.message}{missing_info}</p>",
                    status_code=400,
                )

    @app.exception_handler(ConfigurationError)
    async def configuration_error_handler(request: Request, exc: ConfigurationError):
        """Handle configuration errors."""
        logger.error(f"Configuration error: {exc.message}")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": exc.to_dict(),
                "message": "Server configuration error. Please contact administrator.",
            },
        )

    @app.exception_handler(RVToolsError)
    async def general_rvtools_error_handler(request: Request, exc: RVToolsError):
        """Handle general RVTools errors."""
        logger.error(f"RVTools error: {exc.message}")

        if _is_api_request(request):
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": exc.to_dict(),
                    "message": exc.message,
                },
            )
        else:
            # Web UI request
            if templates:
                return templates.TemplateResponse(
                    request=request,
                    name="error.html",
                    context={"message": exc.message},
                    status_code=500,
                )
            else:
                return HTMLResponse(
                    content=f"<h1>Error</h1><p>{exc.message}</p>", status_code=500
                )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions."""
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")

        if _is_api_request(request):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "error": {
                        "error": "HTTPException",
                        "message": exc.detail,
                        "status_code": exc.status_code,
                    },
                    "message": exc.detail,
                },
            )
        else:
            # Web UI request
            if templates:
                return templates.TemplateResponse(
                    request=request,
                    name="error.html",
                    context={"message": exc.detail},
                    status_code=exc.status_code,
                )
            else:
                return HTMLResponse(
                    content=f"<h1>Error {exc.status_code}</h1><p>{exc.detail}</p>",
                    status_code=exc.status_code,
                )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.exception(f"Unexpected error: {str(exc)}")

        if _is_api_request(request):
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "error": "InternalServerError",
                        "message": "An unexpected error occurred",
                        "error_type": exc.__class__.__name__,
                    },
                    "message": (
                        "An unexpected error occurred. Please try again or contact support."
                    ),
                },
            )
        else:
            # Web UI request
            if templates:
                return templates.TemplateResponse(
                    request=request,
                    name="error.html",
                    context={
                        "message": "An unexpected error occurred. Please try again."
                    },
                    status_code=500,
                )
            else:
                return HTMLResponse(
                    content="<h1>Internal Server Error</h1><p>An unexpected error occurred. Please try again.</p>",
                    status_code=500,
                )


def _is_api_request(request: Request) -> bool:
    """Check if the request is for an API endpoint."""
    return (
        request.url.path.startswith("/api/")
        or request.url.path.startswith("/mcp/")
        or "application/json" in request.headers.get("accept", "").lower()
    )
