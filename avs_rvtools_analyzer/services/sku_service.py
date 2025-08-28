"""
SKU service for Azure VMware Solution capabilities.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.exceptions import SKUDataError
from ..helpers import load_sku_data

logger = logging.getLogger(__name__)


class SKUService:
    """Service for handling Azure VMware Solution SKU data."""

    def __init__(self, sku_data_file: Path = None):
        self.sku_data_file = sku_data_file
        self._cached_sku_data = None

    def get_sku_capabilities(self) -> List[Dict[str, Any]]:
        """
        Get Azure VMware Solution SKU hardware capabilities and specifications.

        Returns:
            List of SKU data with hardware specifications

        Raises:
            SKUDataError: If SKU data cannot be loaded
        """
        try:
            if self._cached_sku_data is None:
                self._cached_sku_data = load_sku_data()

            return self._cached_sku_data

        except FileNotFoundError:
            logger.error("SKU data file not found")
            raise SKUDataError("SKU data file not found", operation="load")
        except Exception as e:
            logger.error(f"Error retrieving SKU information: {str(e)}")
            raise SKUDataError(
                f"Error retrieving SKU information: {str(e)}", operation="load"
            )

    def refresh_sku_data(self) -> None:
        """Refresh cached SKU data by reloading from file."""
        self._cached_sku_data = None
        logger.info("SKU data cache refreshed")
