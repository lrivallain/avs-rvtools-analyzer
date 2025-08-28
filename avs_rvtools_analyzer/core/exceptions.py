"""
Custom exceptions for AVS RVTools Analyzer.
"""

from typing import Any, Dict, Optional


class RVToolsError(Exception):
    """Base exception for RVTools analyzer."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


class FileValidationError(RVToolsError):
    """Raised when file validation fails."""

    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        allowed_extensions: Optional[list] = None,
    ):
        super().__init__(message, error_code="FILE_VALIDATION_ERROR")
        self.filename = filename
        self.allowed_extensions = allowed_extensions or []

        if filename:
            self.details["filename"] = filename
        if allowed_extensions:
            self.details["allowed_extensions"] = allowed_extensions


class AnalysisError(RVToolsError):
    """Raised when analysis operations fail."""

    def __init__(
        self,
        message: str,
        analysis_type: Optional[str] = None,
        file_path: Optional[str] = None,
    ):
        super().__init__(message, error_code="ANALYSIS_ERROR")
        self.analysis_type = analysis_type
        self.file_path = file_path

        if analysis_type:
            self.details["analysis_type"] = analysis_type
        if file_path:
            self.details["file_path"] = file_path


class SKUDataError(RVToolsError):
    """Raised when SKU data operations fail."""

    def __init__(
        self,
        message: str,
        sku_name: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        super().__init__(message, error_code="SKU_DATA_ERROR")
        self.sku_name = sku_name
        self.operation = operation

        if sku_name:
            self.details["sku_name"] = sku_name
        if operation:
            self.details["operation"] = operation


class ConfigurationError(RVToolsError):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, error_code="CONFIGURATION_ERROR")
        self.config_key = config_key

        if config_key:
            self.details["config_key"] = config_key


class ProtectedFileError(FileValidationError):
    """Raised when trying to process a protected Excel file."""

    def __init__(self, message: str = "File is protected and cannot be processed"):
        super().__init__(message)
        self.error_code = "PROTECTED_FILE_ERROR"


class UnsupportedFileFormatError(FileValidationError):
    """Raised when file format is not supported."""

    def __init__(self, message: str, file_extension: Optional[str] = None):
        super().__init__(message)
        self.error_code = "UNSUPPORTED_FORMAT_ERROR"
        self.file_extension = file_extension

        if file_extension:
            self.details["file_extension"] = file_extension


class InsufficientDataError(AnalysisError):
    """Raised when there's insufficient data for analysis."""

    def __init__(self, message: str, missing_sheets: Optional[list] = None):
        super().__init__(message)
        self.error_code = "INSUFFICIENT_DATA_ERROR"
        self.missing_sheets = missing_sheets or []

        if missing_sheets:
            self.details["missing_sheets"] = missing_sheets


class TemporaryFileError(RVToolsError):
    """Raised when temporary file operations fail."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        super().__init__(message, error_code="TEMP_FILE_ERROR")
        self.file_path = file_path
        self.operation = operation

        if file_path:
            self.details["file_path"] = file_path
        if operation:
            self.details["operation"] = operation
