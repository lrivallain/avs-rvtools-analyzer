"""
Analysis service for RVTools data processing.
"""

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd

from ..core.exceptions import AnalysisError, InsufficientDataError
from ..risk_detection import gather_all_risks, get_available_risks

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for handling RVTools data analysis and risk detection."""

    def __init__(self):
        pass

    def analyze_risks(
        self,
        excel_data: Dict[str, Any],
        include_details: bool = False,
        filter_zero_counts: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform risk analysis on RVTools data.

        Args:
            excel_data: Parsed Excel file data as dictionary from RVTools
            include_details: Whether to include detailed data in results
            filter_zero_counts: Whether to filter out risks with count = 0

        Returns:
            Dictionary containing risk analysis results

        Raises:
            AnalysisError: If analysis fails
            InsufficientDataError: If data is insufficient for analysis
        """
        try:
            # Validate input data
            if not excel_data or not isinstance(excel_data, dict):
                raise InsufficientDataError("No valid Excel data provided for analysis")

            # Check if we have any sheets
            if not excel_data:
                raise InsufficientDataError("Excel file contains no sheets")

            # Convert dictionary back to pandas ExcelFile format for compatibility
            # with existing risk detection functions
            excel_file = self._convert_dict_to_excel_file(excel_data)

            # Perform risk analysis
            risk_results = gather_all_risks(excel_file)

            # Validate results
            if not risk_results or "risks" not in risk_results:
                raise AnalysisError("Risk analysis returned invalid results")

            # Clean NaN values from the results
            cleaned_results = self._clean_nan_values(risk_results)

            # Filter out risks with count = 0 if requested
            if filter_zero_counts:
                filtered_risks = {
                    risk_name: risk_data
                    for risk_name, risk_data in cleaned_results["risks"].items()
                    if risk_data.get("count", 0) > 0
                }
                cleaned_results["risks"] = filtered_risks

            # Format results based on detail level
            if include_details:
                return cleaned_results
            else:
                return self._create_summary_results(cleaned_results)

        except (AnalysisError, InsufficientDataError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Error analyzing risks: {str(e)}")
            raise AnalysisError(f"Unexpected error during analysis: {str(e)}")

    def _convert_dict_to_excel_file(self, excel_data: Dict[str, Any]) -> pd.ExcelFile:
        """
        Convert dictionary format back to pandas ExcelFile for compatibility.

        Args:
            excel_data: Dictionary with sheet data

        Returns:
            Mock ExcelFile object with sheet_names property and parse method
        """
        import io

        class MockExcelFile:
            def __init__(self, data_dict):
                self._data = data_dict
                self.sheet_names = list(data_dict.keys())

            def parse(self, sheet_name: str, **kwargs) -> pd.DataFrame:
                """Parse a sheet and return as DataFrame."""
                if sheet_name not in self._data:
                    raise ValueError(f"Sheet '{sheet_name}' not found")

                sheet_data = self._data[sheet_name]
                if isinstance(sheet_data, dict) and "data" in sheet_data:
                    # Convert list of dictionaries to DataFrame
                    return pd.DataFrame(sheet_data["data"])
                else:
                    # Assume it's already in DataFrame format or can be converted
                    return pd.DataFrame(sheet_data)

        return MockExcelFile(excel_data)

    def get_available_risk_types(self) -> Dict[str, Any]:
        """
        Get information about all available risk detection capabilities.

        Returns:
            Dictionary containing available risk information

        Raises:
            AnalysisError: If retrieving risk information fails
        """
        try:
            return get_available_risks()

        except Exception as e:
            logger.error(f"Error retrieving risk information: {str(e)}")
            raise AnalysisError(f"Error retrieving risk information: {str(e)}")

    def _clean_nan_values(self, obj: Any) -> Any:
        """
        Recursively clean NaN values from nested dictionaries and lists.

        Args:
            obj: Object to clean (dict, list, or value)

        Returns:
            Cleaned object with NaN values replaced by None
        """
        if isinstance(obj, dict):
            return {key: self._clean_nan_values(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_nan_values(item) for item in obj]
        elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
            return None
        elif pd.isna(obj):
            return None
        else:
            return obj

    def _create_summary_results(self, full_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create simplified summary results without raw data.

        Args:
            full_results: Full analysis results with all data

        Returns:
            Simplified summary results
        """
        summary = {"summary": full_results["summary"], "risks": {}}

        for risk_name, risk_data in full_results["risks"].items():
            summary["risks"][risk_name] = {
                "count": risk_data["count"],
                "risk_level": risk_data.get("risk_level", "info"),
                "risk_info": risk_data.get("risk_info", {}),
                "has_data": len(risk_data.get("data", [])) > 0,
            }

        return summary

    def validate_excel_data(self, excel_data: Dict[str, Any]) -> None:
        """
        Validate that Excel data contains necessary sheets for analysis.

        Args:
            excel_data: Parsed Excel file data as dictionary to validate

        Raises:
            InsufficientDataError: If validation fails
        """
        required_sheets = ["vInfo"]  # Basic requirement for most analyses

        # excel_data is a dictionary with sheet names as keys
        if not isinstance(excel_data, dict):
            raise InsufficientDataError("Invalid Excel data format")

        available_sheets = list(excel_data.keys())

        missing_sheets = [
            sheet for sheet in required_sheets if sheet not in available_sheets
        ]

        if missing_sheets:
            logger.warning(f"Missing recommended sheets: {missing_sheets}")
            # Don't raise an error, just log a warning as some analyses might still work

        if not available_sheets:
            raise InsufficientDataError(
                "Excel file appears to be empty or corrupted - no sheets found"
            )

        logger.debug(
            f"Excel file validation passed. Available sheets: {available_sheets}"
        )

    def get_analysis_metadata(self, excel_data: pd.ExcelFile) -> Dict[str, Any]:
        """
        Get metadata about the Excel file for analysis context.

        Args:
            excel_data: Parsed Excel file

        Returns:
            Dictionary containing metadata about the file
        """
        try:
            metadata = {
                "total_sheets": len(excel_data.sheet_names),
                "sheet_names": excel_data.sheet_names,
                "file_type": "RVTools Export",
            }

            # Try to get basic VM count if vInfo sheet exists
            if "vInfo" in excel_data.sheet_names:
                try:
                    vinfo_data = excel_data.parse("vInfo")
                    metadata["total_vms"] = len(vinfo_data)

                    # Get unique host count if Host column exists
                    if "Host" in vinfo_data.columns:
                        metadata["total_hosts"] = vinfo_data["Host"].nunique()

                except Exception as e:
                    logger.debug(f"Could not extract VM metadata: {str(e)}")

            return metadata

        except Exception as e:
            logger.warning(f"Error extracting metadata: {str(e)}")
            return {
                "total_sheets": (
                    len(excel_data.sheet_names)
                    if hasattr(excel_data, "sheet_names")
                    else 0
                ),
                "sheet_names": getattr(excel_data, "sheet_names", []),
                "file_type": "Unknown",
            }
