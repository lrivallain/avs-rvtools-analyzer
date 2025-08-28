#!/usr/bin/env python3
"""
Integration Tests

Tests global app behavior and risk gathering functionality.
"""

import pytest

from avs_rvtools_analyzer.risk_detection import (
    gather_all_risks,
    get_total_risk_functions_count,
)


class TestRiskGatheringIntegration:
    """Test global app behavior and risk gathering functionality."""

    def test_gather_all_risks_finds_all_risks(self, comprehensive_excel_data):
        """Test that all risk types are detected."""
        result = gather_all_risks(comprehensive_excel_data)

        assert "summary" in result
        assert "risks" in result

        # Should have results for all risk functions (dynamic count)
        risks = result["risks"]
        expected_count = get_total_risk_functions_count()
        assert (
            len(risks) == expected_count
        ), f"Should have {expected_count} risk types, found {len(risks)}"

        # Check that each risk type has proper structure
        expected_risk_functions = [
            "detect_esx_versions",
            "detect_vusb_devices",
            "detect_risky_disks",
            "detect_non_dvs_switches",
            "detect_snapshots",
            "detect_suspended_vms",
            "detect_oracle_vms",
            "detect_dvport_issues",
            "detect_non_intel_hosts",
            "detect_vmtools_not_running",
            "detect_cdrom_issues",
            "detect_large_provisioned_vms",
            "detect_high_vcpu_vms",
            "detect_high_memory_vms",
            "detect_hw_version_compatibility",
            "detect_shared_disks",
        ]

        for func_name in expected_risk_functions:
            assert func_name in risks, f"Should have results for {func_name}"
            risk_result = risks[func_name]
            assert "count" in risk_result
            assert "data" in risk_result
            assert (
                risk_result["count"] > 0
            ), f"{func_name} should detect at least one risk"

    def test_gather_all_risks_summary_structure(self, comprehensive_excel_data):
        """Test the summary structure of gather_all_risks."""
        result = gather_all_risks(comprehensive_excel_data)

        summary = result["summary"]
        assert "total_risks" in summary
        assert "risk_levels" in summary

        risk_levels = summary["risk_levels"]
        assert "info" in risk_levels
        assert "warning" in risk_levels
        assert "danger" in risk_levels
        assert "blocking" in risk_levels

        # Should have total risks > 0
        assert summary["total_risks"] > 0, "Should detect multiple risks in test data"

        # Should have blocking risks (old HW versions, suspended VMs, USB devices)
        assert risk_levels["blocking"] > 0, "Should detect blocking risks"

    def test_gather_all_risks_no_errors(self, comprehensive_excel_data):
        """Test that no risk detection functions throw errors."""
        result = gather_all_risks(comprehensive_excel_data)

        risks = result["risks"]

        # No risk function should have errors
        for func_name, risk_result in risks.items():
            assert (
                "error" not in risk_result or risk_result.get("error") is None
            ), f"{func_name} should not have errors: {risk_result.get('error', '')}"

    def test_comprehensive_test_data_coverage(self, comprehensive_excel_data):
        """Test that our comprehensive test data covers all required sheets."""
        expected_sheets = [
            "vHost",
            "vInfo",
            "vUSB",
            "vDisk",
            "dvSwitch",
            "vNetwork",
            "vSnapshot",
            "dvPort",
            "vCD",
        ]

        available_sheets = comprehensive_excel_data.sheet_names

        for sheet in expected_sheets:
            assert sheet in available_sheets, f"Test data should include {sheet} sheet"
