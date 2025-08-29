"""
Helper functions for RVTools risk detection.
"""

import functools
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


@functools.lru_cache(maxsize=1)
def load_sku_data() -> List[Dict]:
    """
    Load SKU data from JSON file with caching.

    Returns:
        List of SKU dictionaries as defined in sku.json

    Raises:
        FileNotFoundError: If the SKU data file is not found
    """
    sku_file_path = Path(__file__).parent / "static" / "sku.json"
    with open(sku_file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_sheet_access(
    excel_data: pd.ExcelFile, sheet_name: str
) -> Optional[pd.DataFrame]:
    """
    Safely access a sheet from Excel data.

    Args:
        excel_data: Excel file object
        sheet_name: Name of the sheet to access

    Returns:
        DataFrame if sheet exists, None otherwise
    """
    if sheet_name not in excel_data.sheet_names:
        return None
    return excel_data.parse(sheet_name)


def create_empty_result() -> Dict[str, Any]:
    """Create an empty result dictionary for when no data is found."""
    return {"count": 0, "data": []}


def filter_dataframe_by_condition(
    df: pd.DataFrame, condition, columns: List[str]
) -> List[Dict[str, Any]]:
    """
    Filter dataframe by condition and return selected columns as list of dictionaries.

    Args:
        df: DataFrame to filter
        condition: Boolean condition for filtering
        columns: List of column names to include in result

    Returns:
        List of dictionaries containing filtered data
    """
    if df is None or df.empty:
        return []

    filtered_df = df[condition]
    if filtered_df.empty:
        return []

    return filtered_df[columns].to_dict(orient="records")


def get_risk_category(func_name: str) -> str:
    """
    Categorize risk detection functions based on their name.

    Args:
        func_name: Name of the risk detection function

    Returns:
        Category string
    """
    if "esx" in func_name or "host" in func_name:
        return "Infrastructure"
    elif (
        "vm" in func_name
        or "memory" in func_name
        or "vcpu" in func_name
        or "provisioned" in func_name
    ):
        return "Virtual Machines"
    elif "disk" in func_name or "cdrom" in func_name or "snapshot" in func_name:
        return "Storage"
    elif "switch" in func_name or "dvport" in func_name:
        return "Networking"
    elif "usb" in func_name or "oracle" in func_name or "vmtools" in func_name:
        return "Compatibility"
    else:
        return "General"


def convert_mib_to_tb(mib_value: float) -> float:
    """
    Convert MiB to TB.

    Args:
        mib_value: Value in MiB

    Returns:
        Value in TB
    """
    from .models import StorageThresholds

    return mib_value * StorageThresholds.MIB_TO_TB_CONVERSION


def clean_function_name_for_display(func_name: str) -> str:
    """
    Clean up function name for display purposes.

    Args:
        func_name: Original function name

    Returns:
        Cleaned display name
    """
    return func_name.replace("detect_", "").replace("_", " ").title()


def clean_value_for_json(value) -> str:
    """Clean a single value for JSON serialization

    Args:
        value: The value to clean

    Returns:
        The cleaned value
    """
    if value is None:
        return ""
    elif isinstance(value, datetime):
        return value.isoformat()
    elif hasattr(
        value, "isoformat"
    ):  # Handle pandas Timestamp and other datetime-like objects
        return value.isoformat()
    elif isinstance(value, (int, float, str, bool)):
        return value
    else:
        # Convert other types to string
        return str(value)


def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code

    Args:
        obj: The object to serialize

    Returns:
        The serialized object
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(
        obj, "isoformat"
    ):  # Handle pandas Timestamp and other datetime-like objects
        return obj.isoformat()
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    else:
        return str(obj)
