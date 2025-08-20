"""
Data models and constants for RVTools risk detection.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class RiskLevel(str, Enum):
    """Enumeration of risk levels."""
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    BLOCKING = "blocking"


class RiskInfo(BaseModel):
    """Model for risk information metadata."""
    description: str
    alert_message: Optional[str] = None


class RiskResult(BaseModel):
    """Base model for risk detection results."""
    count: int = Field(ge=0, description="Number of items found with this risk")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed data for each risk item")
    risk_level: RiskLevel = Field(description="Severity level of the risk")
    function_name: str = Field(description="Name of the detection function")
    risk_info: RiskInfo = Field(description="Risk metadata")
    error: Optional[str] = Field(None, description="Error message if detection failed")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details specific to the risk type")

    class Config:
        use_enum_values = True


# Constants
class ESXVersionThresholds:
    """ESX version thresholds for risk assessment."""
    WARNING_THRESHOLD = '7.0.0'
    ERROR_THRESHOLD = '6.5.0'


class StorageThresholds:
    """Storage-related thresholds."""
    LARGE_VM_PROVISIONED_TB = 10  # TB
    MIB_TO_TB_CONVERSION = 1.048576 / (1024 * 1024)


class PowerStates:
    """VM power states."""
    POWERED_ON = 'poweredOn'
    SUSPENDED = 'Suspended'


class GuestStates:
    """VM guest states."""
    NOT_RUNNING = 'notRunning'


class NetworkConstants:
    """Network-related constants."""
    STANDARD_VSWITCH = 'standard vSwitch'


class StorageConstants:
    """Storage-related constants."""
    INDEPENDENT_PERSISTENT = 'independent_persistent'
    LARGE_VM_THRESHOLD_TB = 10
