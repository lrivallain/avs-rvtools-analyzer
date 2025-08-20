"""
Utility functions and Jinja2 helpers for the RVTools Analyzer application.
"""

import logging

# Configure logging with uvicorn-style colored formatter
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored log levels like uvicorn."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        # Get color for log level
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Format like uvicorn: "INFO:     message"
        formatted_level = f"{color}{record.levelname}{reset}:"
        return f"{formatted_level:<15}    {record.getMessage()}"

def convert_mib_to_human_readable(value):
    """
    Convert MiB to human-readable format (MB, GB, TB).
    :param value: Value in MiB
    :return: Human-readable string
    """
    try:
        value = float(value)
        # 1 MiB = 1.048576 MB
        value_in_mb = value * 1.048576

        if value_in_mb >= 1024 * 1024:
            return f"{value_in_mb / (1024 * 1024):.2f} TB"
        elif value_in_mb >= 1024:
            return f"{value_in_mb / 1024:.2f} GB"
        else:
            return f"{value_in_mb:.2f} MB"
    except (ValueError, TypeError):
        return "Invalid input"


def get_risk_badge_class(risk_level):
    """Map risk levels to Bootstrap badge classes."""
    risk_mapping = {
        'info': 'text-bg-info',
        'warning': 'text-bg-warning',
        'danger': 'text-bg-danger',
        'blocking': 'text-bg-danger'
    }
    return risk_mapping.get(risk_level, 'text-bg-secondary')


def get_risk_display_name(risk_level):
    """Map risk levels to display names."""
    risk_mapping = {
        'info': 'Info',
        'warning': 'Warning',
        'danger': 'Blocking',
        'blocking': 'Blocking'
    }
    return risk_mapping.get(risk_level, 'Unknown')


def allowed_file(filename, allowed_extensions=None):
    """Check if uploaded file has an allowed extension."""
    if allowed_extensions is None:
        allowed_extensions = {'xlsx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def register_jinja_helpers(templates):
    """
    Register Jinja2 template helpers and filters.
    
    Args:
        templates: Jinja2Templates instance
    """
    from fastapi.templating import Jinja2Templates
    
    # Register filters
    templates.env.filters['convert_mib_to_human_readable'] = convert_mib_to_human_readable
    
    # Register global functions
    templates.env.globals['get_risk_badge_class'] = get_risk_badge_class
    templates.env.globals['get_risk_display_name'] = get_risk_display_name
    
    # Add version information if available
    try:
        # Try to get version from package metadata
        import importlib.metadata
        version = importlib.metadata.version("avs-rvtools-analyzer")
        templates.env.globals['version'] = version
    except Exception:
        # Fallback version
        templates.env.globals['version'] = "1.0.0"
