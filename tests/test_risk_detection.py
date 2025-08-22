#!/usr/bin/env python3
"""
Comprehensive tests for all risk detection functions using the generated test data.
"""

import pytest
import pandas as pd
from pathlib import Path

# Import all risk detection functions
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


@pytest.fixture(scope="module")
def comprehensive_excel_data():
    """Load the comprehensive test data Excel file."""
    test_data_path = Path(__file__).parent / 'test-data' / 'comprehensive_test_data.xlsx'

    # The file should already exist due to the session-scoped fixture in conftest.py
    assert test_data_path.exists(), f"Test data file should exist at {test_data_path}"

    return pd.ExcelFile(test_data_path)


class TestESXVersions:
    """Test ESX version detection."""

    def test_detect_esx_versions_finds_old_versions(self, comprehensive_excel_data):
        """Test that old ESX versions are detected."""
        result = detect_esx_versions(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect ESX version issues"
        assert 'data' in result
        assert isinstance(result['data'], dict)

        # Should find old versions like 6.5.0 and 6.7.0
        version_data = result['data']
        assert any('6.5.0' in str(version) or '6.7.0' in str(version) for version in version_data.keys())

    def test_detect_esx_versions_structure(self, comprehensive_excel_data):
        """Test the structure of ESX version detection results."""
        result = detect_esx_versions(comprehensive_excel_data)

        assert 'count' in result
        assert 'data' in result
        assert isinstance(result['count'], int)


class TestUSBDevices:
    """Test USB device detection."""

    def test_detect_vusb_devices_finds_devices(self, comprehensive_excel_data):
        """Test that USB devices are detected."""
        result = detect_vusb_devices(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect USB devices"
        assert 'data' in result
        assert isinstance(result['data'], list)

        # Check that we have the expected USB devices
        usb_devices = result['data']
        assert len(usb_devices) >= 5, "Should find at least 5 USB devices from test data"

        # Verify structure of USB device data
        for device in usb_devices:
            assert 'VM' in device
            assert 'Device Type' in device
            assert 'Connected' in device

    def test_detect_vusb_devices_vm_names(self, comprehensive_excel_data):
        """Test that specific VMs with USB devices are detected."""
        result = detect_vusb_devices(comprehensive_excel_data)

        vm_names = [device['VM'] for device in result['data']]
        expected_vms = ['vm-web-server-01', 'vm-app-server-01', 'vm-db-oracle-01']

        for vm in expected_vms:
            assert vm in vm_names, f"Should detect USB device on {vm}"


class TestRiskyDisks:
    """Test risky disk detection."""

    def test_detect_risky_disks_finds_raw_disks(self, comprehensive_excel_data):
        """Test that raw device mapping disks are detected."""
        result = detect_risky_disks(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect risky disks"
        assert 'data' in result

        # Should find raw disks and independent disks
        risky_disks = result['data']
        raw_disks = [disk for disk in risky_disks if str(disk.get('Raw', '')).lower() == 'true']
        independent_disks = [disk for disk in risky_disks if 'independent' in str(disk.get('Disk Mode', '')).lower()]

        assert len(raw_disks) > 0, "Should find raw device mapping disks"
        assert len(independent_disks) > 0, "Should find independent mode disks"


class TestNetworkSwitches:
    """Test network switch detection."""

    def test_detect_non_dvs_switches_finds_standard_switches(self, comprehensive_excel_data):
        """Test that standard vSwitches are detected."""
        result = detect_non_dvs_switches(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect standard vSwitches"
        assert 'data' in result

        # Should find standard vSwitches (vSwitch0, vSwitch1, vSwitch2)
        switch_data = result['data']
        assert 'standard vSwitch' in switch_data, "Should categorize standard vSwitches"


class TestSnapshots:
    """Test snapshot detection."""

    def test_detect_snapshots_finds_snapshots(self, comprehensive_excel_data):
        """Test that VM snapshots are detected."""
        result = detect_snapshots(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect VM snapshots"
        assert 'data' in result
        assert isinstance(result['data'], list)

        # Should find multiple snapshots
        snapshots = result['data']
        assert len(snapshots) >= 8, "Should find at least 8 snapshots from test data"

        # Verify snapshot structure
        for snapshot in snapshots:
            assert 'VM' in snapshot
            assert 'Name' in snapshot
            assert 'Date / time' in snapshot


class TestSuspendedVMs:
    """Test suspended VM detection."""

    def test_detect_suspended_vms_finds_suspended(self, comprehensive_excel_data):
        """Test that suspended VMs are detected."""
        result = detect_suspended_vms(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect suspended VMs"
        assert 'data' in result

        # Should find suspended VMs
        suspended_vms = result['data']
        vm_names = [vm['VM'] for vm in suspended_vms]

        expected_suspended = ['vm-suspended-01', 'vm-suspended-02']
        for vm in expected_suspended:
            assert vm in vm_names, f"Should detect {vm} as suspended"


class TestOracleVMs:
    """Test Oracle VM detection."""

    def test_detect_oracle_vms_finds_oracle(self, comprehensive_excel_data):
        """Test that Oracle VMs are detected."""
        result = detect_oracle_vms(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect Oracle VMs"
        assert 'data' in result

        # Should find Oracle VMs
        oracle_vms = result['data']
        vm_names = [vm['VM'] for vm in oracle_vms]

        expected_oracle = ['vm-db-oracle-01', 'vm-db-oracle-02', 'vm-mixed-issues-01']
        for vm in expected_oracle:
            assert vm in vm_names, f"Should detect {vm} as Oracle VM"


class TestDVPortIssues:
    """Test distributed virtual port issues."""

    def test_detect_dvport_issues_finds_security_issues(self, comprehensive_excel_data):
        """Test that dvPort security issues are detected."""
        result = detect_dvport_issues(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect dvPort issues"
        assert 'data' in result

        # Should find ports with security issues
        dvport_issues = result['data']

        # Check for specific security issues - handle both string and boolean values
        promiscuous_issues = [issue for issue in dvport_issues if str(issue.get('Allow Promiscuous', '')).lower() == 'true']
        mac_change_issues = [issue for issue in dvport_issues if str(issue.get('Mac Changes', '')).lower() == 'true']
        forged_transmit_issues = [issue for issue in dvport_issues if str(issue.get('Forged Transmits', '')).lower() == 'true']

        assert len(promiscuous_issues) > 0, "Should find promiscuous mode issues"
        assert len(mac_change_issues) > 0, "Should find MAC change issues"
        assert len(forged_transmit_issues) > 0, "Should find forged transmit issues"


class TestNonIntelHosts:
    """Test non-Intel host detection."""

    def test_detect_non_intel_hosts_finds_amd(self, comprehensive_excel_data):
        """Test that non-Intel hosts are detected."""
        result = detect_non_intel_hosts(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect non-Intel hosts"
        assert 'data' in result

        # Should find AMD hosts
        non_intel_hosts = result['data']
        cpu_models = [host['CPU Model'] for host in non_intel_hosts]

        assert any('AMD' in cpu for cpu in cpu_models), "Should detect AMD hosts"


class TestVMToolsIssues:
    """Test VMware Tools detection."""

    def test_detect_vmtools_not_running_finds_issues(self, comprehensive_excel_data):
        """Test that VMware Tools issues are detected."""
        result = detect_vmtools_not_running(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect VMware Tools issues"
        assert 'data' in result

        # Should find VMs with tools not running
        vmtools_issues = result['data']

        # All should be powered on with guest state not running
        for issue in vmtools_issues:
            assert issue['Powerstate'] == 'poweredOn'
            assert issue['Guest state'] == 'notRunning'


class TestCDROMIssues:
    """Test CD-ROM device detection."""

    def test_detect_cdrom_issues_finds_connected_cdroms(self, comprehensive_excel_data):
        """Test that connected CD-ROM devices are detected."""
        result = detect_cdrom_issues(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect connected CD-ROM devices"
        assert 'data' in result

        # Should find VMs with connected CD-ROMs
        cdrom_issues = result['data']

        # All should have Connected = "True" (handle both string and boolean values)
        for issue in cdrom_issues:
            connected_value = str(issue['Connected']).lower()
            assert connected_value == 'true', f"Should only detect VMs with connected CD-ROMs, got: {issue['Connected']}"


class TestLargeProvisionedVMs:
    """Test large provisioned VM detection."""

    def test_detect_large_provisioned_vms_finds_large_vms(self, comprehensive_excel_data):
        """Test that large provisioned VMs are detected."""
        result = detect_large_provisioned_vms(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect large provisioned VMs"
        assert 'data' in result

        # Should find VMs with >10TB provisioned
        large_vms = result['data']

        expected_large_vms = ['vm-large-storage-01', 'vm-large-storage-02', 'vm-mixed-issues-01']
        vm_names = [vm['VM'] for vm in large_vms]

        for vm in expected_large_vms:
            assert vm in vm_names, f"Should detect {vm} as large provisioned VM"


class TestHighVCPUVMs:
    """Test high vCPU VM detection."""

    def test_detect_high_vcpu_vms_finds_high_cpu_vms(self, comprehensive_excel_data):
        """Test that high vCPU VMs are detected."""
        result = detect_high_vcpu_vms(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect high vCPU VMs"
        assert 'data' in result

        # Should find VMs with high CPU counts (72, 64, 80)
        high_vcpu_vms = result['data']

        expected_high_cpu_vms = ['vm-high-cpu-01', 'vm-high-cpu-02', 'vm-mixed-issues-01']
        vm_names = [vm['VM'] for vm in high_vcpu_vms]

        for vm in expected_high_cpu_vms:
            assert vm in vm_names, f"Should detect {vm} as high vCPU VM"


class TestHighMemoryVMs:
    """Test high memory VM detection."""

    def test_detect_high_memory_vms_finds_high_memory_vms(self, comprehensive_excel_data):
        """Test that high memory VMs are detected."""
        result = detect_high_memory_vms(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect high memory VMs"
        assert 'data' in result

        # Should find VMs with high memory (1TB+)
        high_memory_vms = result['data']

        expected_high_memory_vms = ['vm-high-memory-01', 'vm-high-memory-02', 'vm-mixed-issues-01']
        vm_names = [vm['VM'] for vm in high_memory_vms if 'VM' in vm]

        for vm in expected_high_memory_vms:
            assert vm in vm_names, f"Should detect {vm} as high memory VM"


class TestHWVersionCompatibility:
    """Test hardware version compatibility detection."""

    def test_detect_hw_version_compatibility_finds_old_hw(self, comprehensive_excel_data):
        """Test that old hardware versions are detected."""
        result = detect_hw_version_compatibility(comprehensive_excel_data)

        assert result['count'] > 0, "Should detect hardware version compatibility issues"
        assert 'data' in result

        # Should find VMs with old hardware versions (6, 7, 8)
        hw_issues = result['data']

        # Check for specific VMs with old hardware
        vm_names = [vm['VM'] for vm in hw_issues]
        expected_old_hw_vms = ['vm-old-hw-01', 'vm-old-hw-02', 'vm-mixed-issues-01']

        for vm in expected_old_hw_vms:
            assert vm in vm_names, f"Should detect {vm} as having old hardware version"

        # Verify migration method restrictions
        for issue in hw_issues:
            assert 'Unsupported migration methods' in issue
            assert len(issue['Unsupported migration methods']) > 0


class TestGatherAllRisks:
    """Test the main risk gathering function."""

    def test_gather_all_risks_finds_all_15_risks(self, comprehensive_excel_data):
        """Test that all 15 risk types are detected."""
        result = gather_all_risks(comprehensive_excel_data)

        assert 'summary' in result
        assert 'risks' in result

        # Should have results for all 15 risk functions
        risks = result['risks']
        assert len(risks) == 15, f"Should have 15 risk types, found {len(risks)}"

        # Check that each risk type has proper structure
        expected_risk_functions = [
            'detect_esx_versions', 'detect_vusb_devices', 'detect_risky_disks',
            'detect_non_dvs_switches', 'detect_snapshots', 'detect_suspended_vms',
            'detect_oracle_vms', 'detect_dvport_issues', 'detect_non_intel_hosts',
            'detect_vmtools_not_running', 'detect_cdrom_issues', 'detect_large_provisioned_vms',
            'detect_high_vcpu_vms', 'detect_high_memory_vms', 'detect_hw_version_compatibility'
        ]

        for func_name in expected_risk_functions:
            assert func_name in risks, f"Should have results for {func_name}"
            risk_result = risks[func_name]
            assert 'count' in risk_result
            assert 'data' in risk_result
            assert risk_result['count'] > 0, f"{func_name} should detect at least one risk"

    def test_gather_all_risks_summary_structure(self, comprehensive_excel_data):
        """Test the summary structure of gather_all_risks."""
        result = gather_all_risks(comprehensive_excel_data)

        summary = result['summary']
        assert 'total_risks' in summary
        assert 'risk_levels' in summary

        risk_levels = summary['risk_levels']
        assert 'info' in risk_levels
        assert 'warning' in risk_levels
        assert 'danger' in risk_levels
        assert 'blocking' in risk_levels

        # Should have total risks > 0
        assert summary['total_risks'] > 0, "Should detect multiple risks in test data"

        # Should have blocking risks (old HW versions, suspended VMs, USB devices)
        assert risk_levels['blocking'] > 0, "Should detect blocking risks"

    def test_gather_all_risks_no_errors(self, comprehensive_excel_data):
        """Test that no risk detection functions throw errors."""
        result = gather_all_risks(comprehensive_excel_data)

        risks = result['risks']

        # No risk function should have errors
        for func_name, risk_result in risks.items():
            assert 'error' not in risk_result or risk_result.get('error') is None, \
                f"{func_name} should not have errors: {risk_result.get('error', '')}"


class TestPerformanceAndEdgeCases:
    """Test performance and edge cases."""

    def test_risk_detection_performance(self, comprehensive_excel_data):
        """Test that risk detection completes in reasonable time."""
        import time

        start_time = time.time()
        result = gather_all_risks(comprehensive_excel_data)
        end_time = time.time()

        execution_time = end_time - start_time
        assert execution_time < 10.0, f"Risk detection should complete in <10 seconds, took {execution_time:.2f}s"

        # Should still find all risks
        assert len(result['risks']) == 15

    def test_comprehensive_test_data_coverage(self, comprehensive_excel_data):
        """Test that our comprehensive test data covers all required sheets."""
        expected_sheets = [
            'vHost', 'vInfo', 'vUSB', 'vDisk', 'dvSwitch',
            'vNetwork', 'vSnapshot', 'dvPort', 'vCD'
        ]

        available_sheets = comprehensive_excel_data.sheet_names

        for sheet in expected_sheets:
            assert sheet in available_sheets, f"Test data should include {sheet} sheet"
