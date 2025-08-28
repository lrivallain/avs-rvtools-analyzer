"""
Decorators for RVTools risk detection functions.
"""

from functools import wraps
from typing import Any, Callable, Dict, Union

from .models import RiskLevel


def risk_info(
    level: Union[RiskLevel, str], description: str, alert_message: str = None
):
    """
    Decorator to assign risk levels and info to detection functions.

    Args:
        level: Risk level (RiskLevel enum or string)
        description: Description of the risk
        alert_message: Alert message with recommendations (optional)
    """
    # Convert string to enum if needed
    if isinstance(level, str):
        level = RiskLevel(level)

    def decorator(func: Callable) -> Callable:
        # Store metadata on the original function
        func._risk_info = {
            "level": level.value,
            "description": description,
            "alert_message": alert_message,
        }

        @wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            try:
                result = func(*args, **kwargs)

                # Ensure result follows the expected structure
                if isinstance(result, dict):
                    # Check if there's a dynamic card_risk in details that should override the decorator level
                    effective_risk_level = level.value
                    if result.get("details") and "card_risk" in result["details"]:
                        effective_risk_level = result["details"]["card_risk"]

                    # Create a proper RiskResult structure
                    risk_result = {
                        "count": result.get("count", 0),
                        "data": result.get("data", []),
                        "risk_level": effective_risk_level,
                        "function_name": func.__name__,
                        "risk_info": {
                            "description": description,
                            "alert_message": alert_message,
                        },
                        "details": result.get("details"),
                    }

                    # Add any extra fields from the original result
                    for key, value in result.items():
                        if key not in risk_result:
                            risk_result[key] = value

                    return risk_result

                return result

            except Exception as e:
                # Return error result in consistent format
                return {
                    "count": 0,
                    "data": [],
                    "risk_level": level.value,
                    "function_name": func.__name__,
                    "risk_info": {
                        "description": description,
                        "alert_message": alert_message,
                    },
                    "error": str(e),
                }

        # Copy the metadata to the wrapper as well
        wrapper._risk_info = func._risk_info
        return wrapper

    return decorator
