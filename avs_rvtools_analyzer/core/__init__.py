"""
Core package for application infrastructure.
"""
from .exceptions import (
    RVToolsError,
    FileValidationError,
    AnalysisError,
    SKUDataError,
    ConfigurationError,
    ProtectedFileError,
    UnsupportedFileFormatError,
    InsufficientDataError,
    TemporaryFileError
)
from .error_handlers import setup_error_handlers

__all__ = [
    "RVToolsError",
    "FileValidationError",
    "AnalysisError",
    "SKUDataError",
    "ConfigurationError",
    "ProtectedFileError",
    "UnsupportedFileFormatError",
    "InsufficientDataError",
    "TemporaryFileError",
    "setup_error_handlers"
]
