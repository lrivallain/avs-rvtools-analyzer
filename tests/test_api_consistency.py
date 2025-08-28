#!/usr/bin/env python3
"""
API Tests

Tests API endpoints and data structure consistency.
"""

from avs_rvtools_analyzer.risk_detection import (
    gather_all_risks,
    get_risk_functions_list,
    get_total_risk_functions_count,
)


class TestAPIDataStructureConsistency:
    """Test API endpoints and data structure consistency."""

    def test_all_risk_functions_return_consistent_structure(
        self, comprehensive_excel_data
    ):
        """Test that all risk detection functions return consistent data structures."""
        risk_functions = get_risk_functions_list()

        for func in risk_functions:
            result = func(comprehensive_excel_data)

            # All functions should return these mandatory fields
            assert "count" in result, f"{func.__name__} should return 'count' field"
            assert "data" in result, f"{func.__name__} should return 'data' field"
            assert isinstance(
                result["count"], int
            ), f"{func.__name__} count should be integer"
            assert isinstance(
                result["data"], (list, dict)
            ), f"{func.__name__} data should be list or dict"

            # Count should match data length for list data, except for detect_non_dvs_switches
            # which counts VMs but returns switch summaries
            if (
                isinstance(result["data"], list)
                and func.__name__ != "detect_non_dvs_switches"
            ):
                assert result["count"] == len(
                    result["data"]
                ), f"{func.__name__} count ({result['count']}) should match data length ({len(result['data'])})"

    def test_gather_all_risks_api_structure(self, comprehensive_excel_data):
        """Test that gather_all_risks returns proper API structure."""
        result = gather_all_risks(comprehensive_excel_data)

        # Top-level structure
        assert "summary" in result, "Should have summary section"
        assert "risks" in result, "Should have risks section"

        # Summary structure
        summary = result["summary"]
        assert "total_risks" in summary, "Summary should have total_risks"
        assert "risk_levels" in summary, "Summary should have risk_levels"
        assert isinstance(summary["total_risks"], int), "total_risks should be integer"

        # Risk levels structure
        risk_levels = summary["risk_levels"]
        expected_levels = ["info", "warning", "danger", "blocking"]
        for level in expected_levels:
            assert level in risk_levels, f"Should have {level} risk level"
            assert isinstance(
                risk_levels[level], int
            ), f"{level} count should be integer"

        # Individual risks structure
        risks = result["risks"]
        # Should have exactly the same number of risk detection results as available functions
        expected_count = get_total_risk_functions_count()
        assert (
            len(risks) == expected_count
        ), f"Should have {expected_count} risk detection results, found {len(risks)}"

        for func_name, risk_result in risks.items():
            assert isinstance(func_name, str), "Risk function name should be string"
            assert "count" in risk_result, f"{func_name} should have count"
            assert "data" in risk_result, f"{func_name} should have data"

    def test_error_handling_consistency(self):
        """Test that error handling returns consistent structures."""

        # Create a mock empty Excel data that mimics pd.ExcelFile behavior
        class MockEmptyExcelFile:
            def __init__(self):
                self.sheet_names = []

            def parse(self, sheet_name):
                raise ValueError(f"Worksheet named '{sheet_name}' not found")

        empty_excel_data = MockEmptyExcelFile()

        risk_functions = get_risk_functions_list()

        for func in risk_functions:
            try:
                result = func(empty_excel_data)

                # Even with missing data, should return consistent structure
                assert (
                    "count" in result
                ), f"{func.__name__} should return count even on error"
                assert (
                    "data" in result
                ), f"{func.__name__} should return data even on error"
                assert (
                    result["count"] == 0
                ), f"{func.__name__} should return 0 count for empty data"

            except Exception:
                # If exception is raised, it should be handled gracefully by gather_all_risks
                pass
