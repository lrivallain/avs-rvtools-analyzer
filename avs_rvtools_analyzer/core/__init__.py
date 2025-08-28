"""
Core package for application infrastructure.
"""

from .error_handlers import setup_error_handlers
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
    "setup_error_handlers",
]
