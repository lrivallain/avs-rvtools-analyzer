"""
Utility functions and Jinja2 helpers for the RVTools Analyzer application.
"""

import logging
import re

import pandas as pd


# Configure logging with uvicorn-style colored formatter
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored log levels like uvicorn."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        # Get color for log level
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

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
        "info": "text-bg-info",
        "warning": "text-bg-warning",
        "danger": "text-bg-danger",
        "blocking": "text-bg-danger",
        "emergency": "text-bg-dark",  # Black badge for emergency
    }
    return risk_mapping.get(risk_level, "text-bg-secondary")


def get_risk_display_name(risk_level):
    """Map risk levels to display names."""
    risk_mapping = {
        "info": "Info",
        "warning": "Warning",
        "danger": "Blocking",
        "blocking": "Blocking",
        "emergency": "Emergency",
    }
    return risk_mapping.get(risk_level, "Unknown")


def allowed_file(filename, allowed_extensions=None):
    """Check if uploaded file has an allowed extension."""
    if allowed_extensions is None:
        allowed_extensions = {"xlsx"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def contains_password_reference(text):
    """
    Check if text contains password-related terms.

    Args:
        text: String to check for password references

    Returns:
        bool: True if password-related terms are found, False otherwise
    """
    if not text or pd.isna(text):
        return False

    # Password patterns to search for (case-insensitive)
    password_patterns = [
        r"\bpassword\b",
        r"\bpwd\b",
        r"\bpass\b",
        r"\bpasswd\b",
        r"\bpassphrase\b",
        r"\bpasskey\b",
        r"\bsecret\b",
        r"\bcredential\b",
    ]

    # Combine all patterns into a single regex
    combined_pattern = "|".join(password_patterns)
    password_regex = re.compile(combined_pattern, re.IGNORECASE)

    return bool(password_regex.search(str(text)))


def redact_password_content(text):
    """
    Redact password-containing text for security purposes.

    Args:
        text: Original text that may contain passwords

    Returns:
        str: Redacted message indicating content was hidden for security
    """
    if not text or pd.isna(text):
        return text

    if contains_password_reference(text):
        return "[CONTENT REDACTED - Password reference redacted for security]"

    return text
