#!/usr/bin/env python3
"""
Performance Tests

Tests execution time and resource usage.
"""

import time
from avs_rvtools_analyzer.risk_detection import (
    detect_esx_versions,
    detect_vusb_devices,
    detect_risky_disks,
    detect_non_dvs_switches,
    detect_snapshots,
    detect_suspended_vms,
    detect_oracle_vms,
    detect_dvport_issues,
    detect_non_intel_hosts,
    detect_vmtools_not_running,
    detect_cdrom_issues,
    detect_large_provisioned_vms,
    detect_high_vcpu_vms,
    detect_high_memory_vms,
    detect_hw_version_compatibility,
    gather_all_risks
)


class TestPerformanceAndBenchmarks:
    """Test execution time and resource usage."""

    def test_risk_detection_performance(self, comprehensive_excel_data):
        """Test that risk detection completes in reasonable time."""
        start_time = time.time()
        result = gather_all_risks(comprehensive_excel_data)
        end_time = time.time()

        execution_time = end_time - start_time
        assert execution_time < 10.0, f"Risk detection should complete in <10 seconds, took {execution_time:.2f}s"

        # Should still find all risks
        assert len(result['risks']) == 15

    def test_individual_function_performance(self, comprehensive_excel_data):
        """Test that individual risk detection functions are reasonably fast."""
        risk_functions = [
            detect_esx_versions, detect_vusb_devices, detect_risky_disks,
            detect_non_dvs_switches, detect_snapshots, detect_suspended_vms,
            detect_oracle_vms, detect_dvport_issues, detect_non_intel_hosts,
            detect_vmtools_not_running, detect_cdrom_issues, detect_large_provisioned_vms,
            detect_high_vcpu_vms, detect_high_memory_vms, detect_hw_version_compatibility
        ]

        for func in risk_functions:
            start_time = time.time()
            result = func(comprehensive_excel_data)
            end_time = time.time()

            execution_time = end_time - start_time
            assert execution_time < 2.0, f"{func.__name__} should complete in <2 seconds, took {execution_time:.2f}s"
            assert 'count' in result, f"{func.__name__} should return valid result structure"
