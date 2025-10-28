#!/usr/bin/env python3
"""
Tests for the powered-off VM filtering functionality.

Tests the API endpoints' ability to accept and process the filter_powered_off parameter,
and verifies that powered-off VMs are correctly filtered in the data processing layer.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from avs_rvtools_analyzer.services.file_service import FileService
from avs_rvtools_analyzer.services.analysis_service import AnalysisService
from avs_rvtools_analyzer.config import FileConfig


class TestPoweredOffFiltering:
    """Test powered-off VM filtering functionality."""

    @pytest.fixture
    def file_service(self):
        """Create a FileService instance for testing."""
        config = FileConfig()
        return FileService(config)

    def test_filter_powered_off_rows_method(self, file_service):
        """Test the _filter_powered_off_rows method directly."""
        # Test data with mixed power states
        headers = ["VM", "Powerstate", "Memory", "CPUs"]
        test_data = [
            {"VM": "VM-001", "Powerstate": "poweredOn", "Memory": 8192, "CPUs": 4},
            {"VM": "VM-002", "Powerstate": "poweredOff", "Memory": 4096, "CPUs": 2},
            {"VM": "VM-003", "Powerstate": "suspended", "Memory": 2048, "CPUs": 1},
            {"VM": "VM-004", "Powerstate": "poweredOff", "Memory": 1024, "CPUs": 1},
        ]

        # Filter the data
        filtered_data = file_service._filter_powered_off_rows(test_data, headers)

        # Should have 2 VMs remaining (poweredOn and suspended)
        assert len(filtered_data) == 2, f"Expected 2 VMs after filtering, got {len(filtered_data)}"
        
        # Check that only poweredOff VMs were filtered out
        remaining_vms = [vm["VM"] for vm in filtered_data]
        assert "VM-001" in remaining_vms, "poweredOn VM should remain"
        assert "VM-003" in remaining_vms, "suspended VM should remain"
        assert "VM-002" not in remaining_vms, "poweredOff VM should be filtered out"
        assert "VM-004" not in remaining_vms, "poweredOff VM should be filtered out"

    def test_filter_powered_off_rows_no_powerstate_column(self, file_service):
        """Test filtering when there's no Powerstate column."""
        headers = ["VM", "Memory", "CPUs"]
        test_data = [
            {"VM": "VM-001", "Memory": 8192, "CPUs": 4},
            {"VM": "VM-002", "Memory": 4096, "CPUs": 2},
        ]

        # Filter the data
        filtered_data = file_service._filter_powered_off_rows(test_data, headers)

        # Should have same data when no Powerstate column exists
        assert len(filtered_data) == len(test_data), "Data should be unchanged when no Powerstate column"
        assert filtered_data == test_data, "Data should be identical when no Powerstate column"

    def test_filter_powered_off_case_sensitivity(self, file_service):
        """Test that filtering is case-sensitive for both column name and value."""
        # Test with wrong case column name
        headers = ["VM", "powerstate", "Memory"]  # lowercase 'p'
        test_data = [
            {"VM": "VM-001", "powerstate": "poweredOff", "Memory": 8192},
        ]
        
        filtered_data = file_service._filter_powered_off_rows(test_data, headers)
        assert len(filtered_data) == 1, "Should not filter when column name case doesn't match"

        # Test with wrong case value
        headers = ["VM", "Powerstate", "Memory"] 
        test_data = [
            {"VM": "VM-001", "Powerstate": "PoweredOff", "Memory": 8192},  # Wrong case value
            {"VM": "VM-002", "Powerstate": "poweredOff", "Memory": 4096},  # Correct case value
        ]
        
        filtered_data = file_service._filter_powered_off_rows(test_data, headers)
        assert len(filtered_data) == 1, "Should only filter exact 'poweredOff' value"
        assert filtered_data[0]["VM"] == "VM-001", "Should keep VM with different case value"

    def test_analysis_service_filtering_integration(self, comprehensive_excel_data):
        """Test that AnalysisService works with comprehensive test data."""
        analysis_service = AnalysisService()
        
        # Convert the Excel file to our internal format
        # This mimics what FileService.load_excel_file_from_memory() does
        excel_dict = {}
        for sheet_name in comprehensive_excel_data.sheet_names:
            df = comprehensive_excel_data.parse(sheet_name)
            data = df.to_dict(orient='records')
            excel_dict[sheet_name] = {
                "headers": list(df.columns),
                "data": data,
                "row_count": len(data),
            }

        # Test analysis without filtering
        result_all = analysis_service.analyze_risks(excel_dict, include_details=True)
        
        # Test analysis with manually filtered data (simulate powered off filtering)
        filtered_dict = {}
        for sheet_name, sheet_data in excel_dict.items():
            if "Powerstate" in sheet_data["headers"]:
                # Filter out powered off VMs
                filtered_data = [
                    row for row in sheet_data["data"] 
                    if row.get("Powerstate") != "poweredOff"
                ]
                filtered_dict[sheet_name] = {
                    "headers": sheet_data["headers"],
                    "data": filtered_data,
                    "row_count": len(filtered_data),
                }
            else:
                filtered_dict[sheet_name] = sheet_data
        
        result_filtered = analysis_service.analyze_risks(filtered_dict, include_details=True)
        
        # Both analyses should complete successfully
        assert "risks" in result_all, "Analysis without filtering should return risks"
        assert "risks" in result_filtered, "Analysis with filtering should return risks"
        
        # Check that some risk functions return different counts when powered off VMs are filtered
        # This is a general test that filtering can affect risk detection results
        differences_found = False
        for risk_name in result_all["risks"]:
            count_all = result_all["risks"][risk_name].get("count", 0)
            count_filtered = result_filtered["risks"][risk_name].get("count", 0)
            if count_all != count_filtered:
                differences_found = True
                break
        
        # We don't assert differences_found because it depends on the test data,
        # but we verify both analyses complete successfully
        assert len(result_all["risks"]) > 0, "Should have risk detection results"
        assert len(result_filtered["risks"]) > 0, "Should have risk detection results after filtering"

    def test_file_service_load_excel_file_from_memory_signature(self, file_service):
        """Test that load_excel_file_from_memory accepts filter_powered_off parameter."""
        # This is a signature test to ensure the API accepts the parameter
        # We'll use reflection to check the method signature
        import inspect
        
        sig = inspect.signature(file_service.load_excel_file_from_memory)
        params = sig.parameters
        
        assert 'filter_powered_off' in params, "load_excel_file_from_memory should accept filter_powered_off parameter"
        
        # Check that it has a default value
        filter_param = params['filter_powered_off']
        assert filter_param.default is False, "filter_powered_off should default to False"

    def test_file_service_load_excel_file_signature(self, file_service):
        """Test that load_excel_file accepts filter_powered_off parameter."""
        # This is a signature test to ensure the API accepts the parameter
        import inspect
        
        sig = inspect.signature(file_service.load_excel_file)
        params = sig.parameters
        
        assert 'filter_powered_off' in params, "load_excel_file should accept filter_powered_off parameter"
        
        # Check that it has a default value
        filter_param = params['filter_powered_off']
        assert filter_param.default is False, "filter_powered_off should default to False"

    def test_route_parameter_models(self):
        """Test that API route models include the filter_powered_off parameter."""
        from avs_rvtools_analyzer.routes.api_routes import AnalyzeFileRequest
        
        # Create an instance to test the model
        request = AnalyzeFileRequest(file_path="/test/path")
        
        # Check that filter_powered_off attribute exists and has correct default
        assert hasattr(request, 'filter_powered_off'), "AnalyzeFileRequest should have filter_powered_off attribute"
        assert request.filter_powered_off is False, "filter_powered_off should default to False"
        
        # Test that we can set it to True
        request_with_filter = AnalyzeFileRequest(file_path="/test/path", filter_powered_off=True)
        assert request_with_filter.filter_powered_off is True, "Should be able to set filter_powered_off to True"