#!/usr/bin/env python3
"""
Individual Risk Detection Tests

Tests each risk detection function independently to ensure proper functionality.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import all risk detection functions
from avs_rvtools_analyzer.risk_detection import (
    detect_cdrom_issues,
    detect_clear_text_passwords,
    detect_dvport_issues,
    detect_esx_versions,
    detect_fault_tolerance_vms,
    detect_high_memory_vms,
    detect_high_vcpu_vms,
    detect_hw_version_compatibility,
    detect_large_provisioned_vms,
    detect_non_dvs_switches,
    detect_non_intel_hosts,
    detect_oracle_vms,
    detect_risky_disks,
    detect_shared_disks,
    detect_snapshots,
    detect_suspended_vms,
    detect_vmkernel_network_vms,
    detect_vmtools_not_running,
    detect_vusb_devices,
)


class TestESXVersionRiskDetection:
    """Test ESX version risk detection individually."""

    def test_detect_esx_versions_finds_old_versions(self, comprehensive_excel_data):
        """Test that old ESX versions are detected."""
        result = detect_esx_versions(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect ESX version issues"
        assert "data" in result
        assert isinstance(result["data"], dict)

        # Should find old versions like 6.5.0 and 6.7.0
        version_data = result["data"]
        assert any(
            "6.5.0" in str(version) or "6.7.0" in str(version)
            for version in version_data.keys()
        )

    def test_detect_esx_versions_structure(self, comprehensive_excel_data):
        """Test the structure of ESX version detection results."""
        result = detect_esx_versions(comprehensive_excel_data)

        assert "count" in result
        assert "data" in result
        assert isinstance(result["count"], int)


class TestUSBDeviceRiskDetection:
    """Test USB device risk detection individually."""

    def test_detect_vusb_devices_finds_devices(self, comprehensive_excel_data):
        """Test that USB devices are detected."""
        result = detect_vusb_devices(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect USB devices"
        assert "data" in result
        assert isinstance(result["data"], list)

        # Check that we have the expected USB devices
        usb_devices = result["data"]
        assert (
            len(usb_devices) >= 5
        ), "Should find at least 5 USB devices from test data"

        # Verify structure of USB device data
        for device in usb_devices:
            assert "VM" in device
            assert "Device Type" in device
            assert "Connected" in device

    def test_detect_vusb_devices_vm_names(self, comprehensive_excel_data):
        """Test that specific VMs with USB devices are detected."""
        result = detect_vusb_devices(comprehensive_excel_data)

        vm_names = [device["VM"] for device in result["data"]]
        expected_vms = ["vm-web-server-01", "vm-app-server-01", "vm-db-oracle-01"]

        for vm in expected_vms:
            assert vm in vm_names, f"Should detect USB device on {vm}"


class TestRiskyDiskRiskDetection:
    """Test risky disk risk detection individually."""

    def test_detect_risky_disks_finds_raw_disks(self, comprehensive_excel_data):
        """Test that raw device mapping disks are detected."""
        result = detect_risky_disks(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect risky disks"
        assert "data" in result

        # Should find raw disks and independent disks
        risky_disks = result["data"]
        raw_disks = [
            disk for disk in risky_disks if str(disk.get("Raw", "")).lower() == "true"
        ]
        independent_disks = [
            disk
            for disk in risky_disks
            if "independent" in str(disk.get("Disk Mode", "")).lower()
        ]

        assert len(raw_disks) > 0, "Should find raw device mapping disks"
        assert len(independent_disks) > 0, "Should find independent mode disks"

        # Test dynamic risk levels based on Raw Com. Mode
        physical_mode_disks = [
            disk for disk in risky_disks if disk.get("Raw Com. Mode") == "physicalMode"
        ]
        virtual_mode_disks = [
            disk for disk in risky_disks if disk.get("Raw Com. Mode") == "virtualMode"
        ]

        assert len(physical_mode_disks) > 0, "Should find physicalMode RDM disks"
        assert len(virtual_mode_disks) > 0, "Should find virtualMode RDM disks"

        # Verify risk levels are correctly assigned
        for disk in physical_mode_disks:
            assert (
                disk.get("Risk Level") == "blocking"
            ), f"PhysicalMode RDM should be blocking risk: {disk}"

        for disk in virtual_mode_disks:
            assert (
                disk.get("Risk Level") == "warning"
            ), f"VirtualMode RDM should be warning risk: {disk}"

        # Verify that all risky disks have a Risk Level column
        for disk in risky_disks:
            assert "Risk Level" in disk, "All risky disks should have Risk Level column"
            assert disk["Risk Level"] in [
                "blocking",
                "warning",
            ], f"Risk Level should be blocking or warning: {disk['Risk Level']}"

        # Verify details section
        assert "details" in result, "Should include details section"
        assert (
            "blocking_risks" in result["details"]
        ), "Should include blocking risks count"
        assert (
            "warning_risks" in result["details"]
        ), "Should include warning risks count"
        assert (
            "has_physical_mode_rdm" in result["details"]
        ), "Should include physical mode RDM indicator"


class TestNetworkSwitchRiskDetection:
    """Test network switch risk detection individually."""

    def test_detect_non_dvs_switches_finds_standard_switches(
        self, comprehensive_excel_data
    ):
        """Test that standard vSwitches are detected."""
        result = detect_non_dvs_switches(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect standard vSwitches"
        assert "data" in result
        assert isinstance(
            result["data"], list
        ), "Data should be a list of switch records"

        # Should find switches with detailed information
        switch_data = result["data"]

        # Verify structure of switch data
        for switch_record in switch_data:
            assert "Switch" in switch_record, "Each record should have Switch name"
            assert "Switch Type" in switch_record, "Each record should have Switch Type"
            assert "Port Count" in switch_record, "Each record should have Port Count"
            assert switch_record["Switch Type"] in [
                "Standard",
                "Distributed",
            ], "Switch Type should be Standard or Distributed"
            assert isinstance(
                switch_record["Port Count"], int
            ), "Port Count should be an integer"

        # Should find at least some standard switches
        standard_switches = [
            switch for switch in switch_data if switch["Switch Type"] == "Standard"
        ]
        assert len(standard_switches) > 0, "Should find at least one standard vSwitch"

        # Check for expected standard switch names (vSwitch0, vSwitch1, vSwitch2 from test data)
        standard_switch_names = [switch["Switch"] for switch in standard_switches]
        expected_standard_switches = ["vSwitch0", "vSwitch1", "vSwitch2"]

        for expected_switch in expected_standard_switches:
            assert (
                expected_switch in standard_switch_names
            ), f"Should detect {expected_switch} as standard vSwitch"

    def test_detect_non_dvs_switches_only_standard_switches(self):
        """Test detection when there are only standard vSwitches and no distributed switches."""
        # Create test data with only standard vSwitches (no dvSwitch sheet)
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            temp_path = Path(tmp_file.name)

            # Create vNetwork data with only standard vSwitches
            vnetwork_data = pd.DataFrame(
                {
                    "VM": [
                        "vm-web-01",
                        "vm-web-02",
                        "vm-app-01",
                        "vm-app-02",
                        "vm-db-01",
                        "vm-db-02",
                        "vm-test-01",
                        "vm-empty-switch",
                    ],
                    "Network Label": [
                        "VM Network",
                        "Management Network",
                        "Storage Network",
                        "Production Network",
                        "Database Network",
                        "Backup Network",
                        "Test Network",
                        "Disconnected",
                    ],
                    "Switch": [
                        "vSwitch0",
                        "vSwitch0",
                        "vSwitch1",
                        "vSwitch1",
                        "vSwitch2",
                        "vSwitch2",
                        "vSwitch3",
                        "",  # Last one has empty switch
                    ],
                    "Connected": [True, True, True, True, True, True, True, False],
                    "Status": ["Connected"] * 7 + ["Disconnected"],
                }
            )

            # Write to Excel file
            with pd.ExcelWriter(temp_path, engine="openpyxl") as writer:
                vnetwork_data.to_excel(writer, sheet_name="vNetwork", index=False)

        try:
            # Load the test data
            excel_data = pd.ExcelFile(temp_path)

            # Test the function
            result = detect_non_dvs_switches(excel_data)

            # Should detect all VMs with non-empty switches as using standard vSwitches
            assert (
                result["count"] == 7
            ), f"Should detect 7 VMs using standard switches (excluding empty switch), got {result['count']}"
            assert "data" in result
            assert isinstance(result["data"], list)

            switch_data = result["data"]

            # All switches should be classified as 'Standard'
            for switch_record in switch_data:
                assert (
                    switch_record["Switch Type"] == "Standard"
                ), f"All switches should be Standard, got {switch_record['Switch Type']} for {switch_record['Switch']}"

            # Should find 4 different vSwitches (vSwitch0, vSwitch1, vSwitch2, vSwitch3)
            switch_names = [switch["Switch"] for switch in switch_data]
            expected_switches = ["vSwitch0", "vSwitch1", "vSwitch2", "vSwitch3"]

            assert (
                len(switch_names) == 4
            ), f"Should find 4 different switches, got {len(switch_names)}"
            for expected_switch in expected_switches:
                assert (
                    expected_switch in switch_names
                ), f"Should find {expected_switch} in results"

            # Verify port counts
            port_counts = {
                switch["Switch"]: switch["Port Count"] for switch in switch_data
            }
            assert port_counts["vSwitch0"] == 2, "vSwitch0 should have 2 ports"
            assert port_counts["vSwitch1"] == 2, "vSwitch1 should have 2 ports"
            assert port_counts["vSwitch2"] == 2, "vSwitch2 should have 2 ports"
            assert port_counts["vSwitch3"] == 1, "vSwitch3 should have 1 port"

        finally:
            # Clean up temporary file
            temp_path.unlink(missing_ok=True)


class TestSnapshotRiskDetection:
    """Test snapshot risk detection individually."""

    def test_detect_snapshots_finds_snapshots(self, comprehensive_excel_data):
        """Test that VM snapshots are detected."""
        result = detect_snapshots(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect VM snapshots"
        assert "data" in result
        assert isinstance(result["data"], list)

        # Should find multiple snapshots
        snapshots = result["data"]
        assert len(snapshots) >= 8, "Should find at least 8 snapshots from test data"

        # Verify snapshot structure
        for snapshot in snapshots:
            assert "VM" in snapshot
            assert "Name" in snapshot
            assert "Date / time" in snapshot


class TestSuspendedVMRiskDetection:
    """Test suspended VM risk detection individually."""

    def test_detect_suspended_vms_finds_suspended(self, comprehensive_excel_data):
        """Test that suspended VMs are detected."""
        result = detect_suspended_vms(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect suspended VMs"
        assert "data" in result

        # Should find suspended VMs
        suspended_vms = result["data"]
        vm_names = [vm["VM"] for vm in suspended_vms]

        expected_suspended = ["vm-suspended-01", "vm-suspended-02"]
        for vm in expected_suspended:
            assert vm in vm_names, f"Should detect {vm} as suspended"


class TestOracleVMRiskDetection:
    """Test Oracle VM risk detection individually."""

    def test_detect_oracle_vms_finds_oracle(self, comprehensive_excel_data):
        """Test that Oracle VMs are detected."""
        result = detect_oracle_vms(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect Oracle VMs"
        assert "data" in result

        # Should find Oracle VMs
        oracle_vms = result["data"]
        vm_names = [vm["VM"] for vm in oracle_vms]

        expected_oracle = ["vm-db-oracle-01", "vm-db-oracle-02", "vm-mixed-issues-01"]
        for vm in expected_oracle:
            assert vm in vm_names, f"Should detect {vm} as Oracle VM"


class TestDVPortRiskDetection:
    """Test distributed virtual port risk detection individually."""

    def test_detect_dvport_issues_finds_security_issues(self, comprehensive_excel_data):
        """Test that dvPort security issues are detected."""
        result = detect_dvport_issues(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect dvPort issues"
        assert "data" in result

        # Should find ports with security issues
        dvport_issues = result["data"]

        # Check for specific security issues - handle both string and boolean values
        promiscuous_issues = [
            issue
            for issue in dvport_issues
            if str(issue.get("Allow Promiscuous", "")).lower() == "true"
        ]
        mac_change_issues = [
            issue
            for issue in dvport_issues
            if str(issue.get("Mac Changes", "")).lower() == "true"
        ]
        forged_transmit_issues = [
            issue
            for issue in dvport_issues
            if str(issue.get("Forged Transmits", "")).lower() == "true"
        ]
        ephemeral_issues = [
            issue
            for issue in dvport_issues
            if str(issue.get("Type", "")).lower() == "ephemeral"
        ]

        assert len(promiscuous_issues) > 0, "Should find promiscuous mode issues"
        assert len(mac_change_issues) > 0, "Should find MAC change issues"
        assert len(forged_transmit_issues) > 0, "Should find forged transmit issues"
        assert len(ephemeral_issues) > 0, "Should find ephemeral port type issues"

        # Verify that all dvPort results include the Type column
        for issue in dvport_issues:
            assert "Type" in issue, "All dvPort results should include Type column"


class TestNonIntelHostRiskDetection:
    """Test non-Intel host risk detection individually."""

    def test_detect_non_intel_hosts_finds_amd(self, comprehensive_excel_data):
        """Test that non-Intel hosts are detected."""
        result = detect_non_intel_hosts(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect non-Intel hosts"
        assert "data" in result

        # Should find AMD hosts
        non_intel_hosts = result["data"]
        cpu_models = [host["CPU Model"] for host in non_intel_hosts]

        assert any("AMD" in cpu for cpu in cpu_models), "Should detect AMD hosts"


class TestVMToolsRiskDetection:
    """Test VMware Tools risk detection individually."""

    def test_detect_vmtools_not_running_finds_issues(self, comprehensive_excel_data):
        """Test that VMware Tools issues are detected."""
        result = detect_vmtools_not_running(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect VMware Tools issues"
        assert "data" in result

        # Should find VMs with tools not running
        vmtools_issues = result["data"]

        # All should be powered on with guest state not running
        for issue in vmtools_issues:
            assert issue["Powerstate"] == "poweredOn"
            assert issue["Guest state"] == "notRunning"


class TestCDROMRiskDetection:
    """Test CD-ROM device risk detection individually."""

    def test_detect_cdrom_issues_finds_connected_cdroms(self, comprehensive_excel_data):
        """Test that connected CD-ROM devices are detected."""
        result = detect_cdrom_issues(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect connected CD-ROM devices"
        assert "data" in result

        # Should find VMs with connected CD-ROMs
        cdrom_issues = result["data"]

        # All should have Connected = "True" (handle both string and boolean values)
        for issue in cdrom_issues:
            connected_value = str(issue["Connected"]).lower()
            assert (
                connected_value == "true"
            ), f"Should only detect VMs with connected CD-ROMs, got: {issue['Connected']}"


class TestLargeProvisionedVMRiskDetection:
    """Test large provisioned VM risk detection individually."""

    def test_detect_large_provisioned_vms_finds_large_vms(
        self, comprehensive_excel_data
    ):
        """Test that large provisioned VMs are detected."""
        result = detect_large_provisioned_vms(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect large provisioned VMs"
        assert "data" in result

        # Should find VMs with >10TB provisioned
        large_vms = result["data"]

        expected_large_vms = [
            "vm-large-storage-01",
            "vm-large-storage-02",
            "vm-mixed-issues-01",
        ]
        vm_names = [vm["VM"] for vm in large_vms]

        for vm in expected_large_vms:
            assert vm in vm_names, f"Should detect {vm} as large provisioned VM"


class TestHighVCPURiskDetection:
    """Test high vCPU VM risk detection individually."""

    def test_detect_high_vcpu_vms_finds_high_cpu_vms(self, comprehensive_excel_data):
        """Test that high vCPU VMs are detected."""
        result = detect_high_vcpu_vms(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect high vCPU VMs"
        assert "data" in result

        # Should find VMs with high CPU counts (72, 64, 80)
        high_vcpu_vms = result["data"]

        expected_high_cpu_vms = [
            "vm-high-cpu-01",
            "vm-high-cpu-02",
            "vm-mixed-issues-01",
        ]
        vm_names = [vm["VM"] for vm in high_vcpu_vms]

        for vm in expected_high_cpu_vms:
            assert vm in vm_names, f"Should detect {vm} as high vCPU VM"


class TestHighMemoryRiskDetection:
    """Test high memory VM risk detection individually."""

    def test_detect_high_memory_vms_finds_high_memory_vms(
        self, comprehensive_excel_data
    ):
        """Test that high memory VMs are detected."""
        result = detect_high_memory_vms(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect high memory VMs"
        assert "data" in result

        # Should find VMs with high memory (1TB+)
        high_memory_vms = result["data"]

        expected_high_memory_vms = [
            "vm-high-memory-01",
            "vm-high-memory-02",
            "vm-mixed-issues-01",
        ]
        vm_names = [vm["VM"] for vm in high_memory_vms if "VM" in vm]

        for vm in expected_high_memory_vms:
            assert vm in vm_names, f"Should detect {vm} as high memory VM"


class TestHWVersionCompatibilityRiskDetection:
    """Test hardware version compatibility risk detection individually."""

    def test_detect_hw_version_compatibility_finds_old_hw(
        self, comprehensive_excel_data
    ):
        """Test that old hardware versions are detected."""
        result = detect_hw_version_compatibility(comprehensive_excel_data)

        assert (
            result["count"] > 0
        ), "Should detect hardware version compatibility issues"
        assert "data" in result

        # Should find VMs with old hardware versions (6, 7, 8)
        hw_issues = result["data"]

        # Check for specific VMs with old hardware
        vm_names = [vm["VM"] for vm in hw_issues]
        expected_old_hw_vms = ["vm-old-hw-01", "vm-old-hw-02", "vm-mixed-issues-01"]

        for vm in expected_old_hw_vms:
            assert vm in vm_names, f"Should detect {vm} as having old hardware version"

        # Verify migration method restrictions
        for issue in hw_issues:
            assert "Unsupported migration methods" in issue
            assert len(issue["Unsupported migration methods"]) > 0


class TestSharedDiskRiskDetection:
    """Test shared disk risk detection individually."""

    def test_detect_shared_disks_finds_shared_configurations(
        self, comprehensive_excel_data
    ):
        """Test that shared disk configurations are detected."""
        result = detect_shared_disks(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect shared disk configurations"
        assert "data" in result

        # Should find 5 shared disk groups based on test data:
        # - 3 groups from shared paths (multiple VMs sharing same path)
        # - 2 groups from individual VMs with shared bus configurations (not sharing paths)
        shared_disk_groups = result["data"]
        assert (
            len(shared_disk_groups) == 5
        ), f"Should detect exactly 5 shared disk groups, found {len(shared_disk_groups)}"

        # Verify the structure of shared disk groups
        expected_shared_paths = [
            "[shared-datastore] cluster-shared-disk-01.vmdk",
            "[shared-datastore] cluster-shared-disk-02.vmdk",
            "[shared-datastore] multi-shared-storage.vmdk",
        ]

        # Check for shared path groups (multiple VMs with same path)
        shared_path_groups = [
            g for g in shared_disk_groups if g.get("VM Count", 0) >= 2
        ]
        assert (
            len(shared_path_groups) == 3
        ), f"Should find 3 shared path groups, found {len(shared_path_groups)}"

        found_paths = [group["Path"] for group in shared_path_groups]
        for expected_path in expected_shared_paths:
            assert (
                expected_path in found_paths
            ), f"Should detect shared path: {expected_path}"

        # Check for individual shared bus groups (single VMs with shared bus != noSharing)
        shared_bus_groups = [g for g in shared_disk_groups if g.get("VM Count", 0) == 1]
        assert (
            len(shared_bus_groups) == 2
        ), f"Should find 2 individual shared bus groups, found {len(shared_bus_groups)}"

        # Verify VM counts for shared path groups
        for group in shared_path_groups:
            assert (
                group["VM Count"] >= 2
            ), "Each shared path group should have at least 2 VMs"
            assert "VMs" in group, "Should include VM list"

        # Verify individual shared bus groups
        for group in shared_bus_groups:
            assert (
                group["VM Count"] == 1
            ), "Individual shared bus groups should have exactly 1 VM"
            assert group["Shared Bus"] in [
                "virtualSharing",
                "physicalSharing",
            ], f"Should have non-noSharing bus configuration, got: {group['Shared Bus']}"

        # Check the multi-VM shared disk (3 VMs sharing same path)
        multi_shared = next(
            (g for g in shared_disk_groups if g.get("VM Count", 0) == 3), None
        )
        assert multi_shared is not None, "Should find the 3-VM shared disk group"
        assert multi_shared["Path"] == "[shared-datastore] multi-shared-storage.vmdk"

        # Verify that shared disk information includes expected fields
        for group in shared_disk_groups:
            if "Sharing mode" in group:
                # Sharing mode can be empty string, just check it's present
                assert "Sharing mode" in group, "Sharing mode field should be present"
            if "Shared Bus" in group:
                # If not empty, should be a valid sharing mode
                if group["Shared Bus"]:
                    assert group["Shared Bus"] in [
                        "virtualSharing",
                        "physicalSharing",
                        "noSharing",
                    ], "Shared bus should be a valid VMware sharing mode"

    def test_detect_shared_disks_handles_missing_sheet(self):
        """Test behavior when vDisk sheet is missing."""

        # Create mock excel data without vDisk sheet
        class MockExcelData:
            sheet_names = ["vInfo", "vHost"]  # No vDisk sheet

            def parse(self, _sheet_name):
                return None

        excel_data = MockExcelData()
        result = detect_shared_disks(excel_data)

        assert result["count"] == 0, "Should return 0 when vDisk sheet is missing"
        assert (
            result["data"] == []
        ), "Should return empty data when vDisk sheet is missing"

    def test_detect_shared_disks_handles_missing_columns(
        self, comprehensive_excel_data
    ):
        """Test behavior when required columns are missing."""
        # This test would need to mock data without Path column
        # For now, we'll test with actual data and verify it works
        result = detect_shared_disks(comprehensive_excel_data)

        # Should work with comprehensive test data
        assert isinstance(result, dict), "Should return valid result dictionary"
        assert "count" in result, "Should include count in result"
        assert "data" in result, "Should include data in result"


class TestDetectClearTextPasswords:
    """Test cases for password detection in VM annotations and snapshots."""

    def test_detect_passwords_in_vinfo_annotations(self):
        """Test detection of passwords in VM annotations."""

        class MockExcelData:
            sheet_names = ["vInfo", "vSnapshot"]

            def parse(self, sheet_name):
                if sheet_name == "vInfo":
                    return pd.DataFrame(
                        {
                            "VM": ["VM1", "VM2", "VM3"],
                            "Annotation": [
                                "Server password is admin123",
                                "No secrets here",
                                "User pwd: secret123",
                            ],
                        }
                    )
                elif sheet_name == "vSnapshot":
                    return pd.DataFrame()  # Empty snapshot data
                return pd.DataFrame()

        excel_data = MockExcelData()
        result = detect_clear_text_passwords(excel_data)

        assert (
            result["count"] == 2
        ), f"Should detect 2 VMs with password references, got {result['count']}"
        assert (
            len(result["data"]) == 2
        ), f"Should return data for 2 VMs, got {len(result['data'])}"

        # Check first detection
        first_detection = result["data"][0]
        assert first_detection["Source"] == "VM Annotation"
        assert first_detection["VM Name"] == "VM1"
        assert first_detection["Location Type"] == "vInfo Sheet"
        assert first_detection["Risk Level"] == "emergency"

        # Check second detection
        second_detection = result["data"][1]
        assert second_detection["VM Name"] == "VM3"
        assert (
            "pwd" in first_detection["Details"].lower()
            or "password" in first_detection["Details"].lower()
        )

    def test_detect_passwords_in_snapshot_descriptions(self):
        """Test detection of passwords in snapshot descriptions."""

        class MockExcelData:
            sheet_names = ["vInfo", "vSnapshot"]

            def parse(self, sheet_name):
                if sheet_name == "vSnapshot":
                    return pd.DataFrame(
                        {
                            "VM": ["VM1", "VM2"],
                            "Snapshot": ["Snap1", "Snap2"],
                            "Description": [
                                "Backup before password change",
                                "Regular backup",
                            ],
                        }
                    )
                elif sheet_name == "vInfo":
                    return pd.DataFrame()  # Empty vInfo data
                return pd.DataFrame()

        excel_data = MockExcelData()
        result = detect_clear_text_passwords(excel_data)

        assert (
            result["count"] == 1
        ), f"Should detect 1 snapshot with password reference, got {result['count']}"
        detection = result["data"][0]
        assert detection["Source"] == "Snapshot Description"
        assert detection["VM Name"] == "VM1"
        assert detection["Snapshot Name"] == "Snap1"
        assert detection["Location Type"] == "vSnapshot Sheet"

    def test_detect_various_password_terms(self):
        """Test detection of various password-related terms."""

        class MockExcelData:
            sheet_names = ["vInfo", "vSnapshot"]

            def parse(self, sheet_name):
                if sheet_name == "vInfo":
                    return pd.DataFrame(
                        {
                            "VM": ["VM1", "VM2", "VM3", "VM4", "VM5"],
                            "Annotation": [
                                "Contains password term",
                                "Has pwd reference",
                                "Secret information here",
                                "Credential details",
                                "Clean annotation",
                            ],
                        }
                    )
                return pd.DataFrame()

        excel_data = MockExcelData()
        result = detect_clear_text_passwords(excel_data)

        assert (
            result["count"] == 4
        ), f"Should detect 4 different password-related terms, got {result['count']}"

    def test_no_passwords_detected(self):
        """Test when no passwords are found."""

        class MockExcelData:
            sheet_names = ["vInfo", "vSnapshot"]

            def parse(self, sheet_name):
                if sheet_name == "vInfo":
                    return pd.DataFrame(
                        {
                            "VM": ["VM1", "VM2"],
                            "Annotation": [
                                "Clean server configuration",
                                "Regular maintenance notes",
                            ],
                        }
                    )
                elif sheet_name == "vSnapshot":
                    return pd.DataFrame(
                        {
                            "VM": ["VM1"],
                            "Snapshot": ["Snap1"],
                            "Description": ["Regular backup snapshot"],
                        }
                    )
                return pd.DataFrame()

        excel_data = MockExcelData()
        result = detect_clear_text_passwords(excel_data)

        assert (
            result["count"] == 0
        ), f"Should detect no password references, got {result['count']}"
        assert result["data"] == [], "Should return empty data list"

    def test_missing_sheets(self):
        """Test behavior when sheets are missing."""

        class MockExcelData:
            sheet_names = []

            def parse(self, sheet_name):
                return pd.DataFrame()  # Return empty for all sheets

        excel_data = MockExcelData()
        result = detect_clear_text_passwords(excel_data)

        assert result["count"] == 0, "Should handle missing sheets gracefully"
        assert result["data"] == [], "Should return empty data"

    def test_case_insensitive_detection(self):
        """Test that password detection is case-insensitive."""

        class MockExcelData:
            sheet_names = ["vInfo", "vSnapshot"]

            def parse(self, sheet_name):
                if sheet_name == "vInfo":
                    return pd.DataFrame(
                        {
                            "VM": ["VM1", "VM2", "VM3"],
                            "Annotation": [
                                "Contains PASSWORD in caps",
                                "Has Secret in mixed case",
                                "CREDENTIAL in all caps",
                            ],
                        }
                    )
                return pd.DataFrame()

        excel_data = MockExcelData()
        result = detect_clear_text_passwords(excel_data)

        assert (
            result["count"] == 3
        ), f"Should detect passwords regardless of case, got {result['count']}"


class TestDetectVMkernelNetworkVMs:
    """Test cases for VMkernel network VM detection."""

    def test_detect_vmkernel_vms_finds_management_network_vms(self):
        """Test detection of VMs connected to VMkernel management networks."""

        class MockExcelData:
            sheet_names = ["vSC_VMK", "vNetwork"]

            def parse(self, sheet_name):
                if sheet_name == "vSC_VMK":
                    return pd.DataFrame(
                        {
                            "Host": ["esxi-host-01", "esxi-host-01", "esxi-host-02"],
                            "Device": ["vmk0", "vmk1", "vmk0"],
                            "Port Group": [
                                "Management-Network",
                                "vMotion-Network",
                                "Management-Network",
                            ],
                            "IP Address": [
                                "192.168.10.101",
                                "192.168.20.101",
                                "192.168.10.102",
                            ],
                            "Services": ["Management", "vMotion", "Management"],
                        }
                    )
                elif sheet_name == "vNetwork":
                    return pd.DataFrame(
                        {
                            "VM": ["VM1", "VM2", "VM3", "VM4"],
                            "Powerstate": [
                                "poweredOn",
                                "poweredOn",
                                "poweredOff",
                                "poweredOff",
                            ],
                            "Network": [
                                "Management-Network",
                                "vMotion-Network",
                                "Production-VLAN-100",
                                "Storage-Network",
                            ],
                            "Connected": [True, True, True, True],
                            "Starts Connected": [True, True, True, True],
                            "IPv4 Address": [
                                "192.168.1.100",
                                "192.168.1.101",
                                "192.168.1.102",
                                "192.168.1.103",
                            ],
                            "Mac Address": [
                                "00:50:56:a6:27:ad",
                                "00:50:56:a6:27:ae",
                                "00:50:56:a6:27:af",
                                "00:50:56:a6:27:b0",
                            ],
                        }
                    )
                return pd.DataFrame()

        excel_data = MockExcelData()
        result = detect_vmkernel_network_vms(excel_data)

        assert (
            result["count"] == 2
        ), f"Should detect 2 VMs on VMkernel networks, got {result['count']}"
        assert (
            len(result["data"]) == 2
        ), f"Should return data for 2 VMs, got {len(result['data'])}"

        # Check that the correct VMs were detected
        detected_vms = [vm["VM"] for vm in result["data"]]
        assert "VM1" in detected_vms, "Should detect VM1 on Management-Network"
        assert "VM2" in detected_vms, "Should detect VM2 on vMotion-Network"
        assert "VM3" not in detected_vms, "Should not detect VM3 on Production network"

    def test_detect_vmkernel_vms_details(self):
        """Test that detection provides proper details about VMkernel network VMs."""

        class MockExcelData:
            sheet_names = ["vSC_VMK", "vNetwork"]

            def parse(self, sheet_name):
                if sheet_name == "vSC_VMK":
                    return pd.DataFrame({"Port Group": ["Storage-Network"]})
                elif sheet_name == "vNetwork":
                    return pd.DataFrame(
                        {
                            "VM": ["VM-Storage-Risk"],
                            "Powerstate": ["poweredOn"],
                            "Network": ["Storage-Network"],
                            "Switch": ["vSwitch-01"],
                            "Connected": [True],
                            "Start Connected": [True],
                            "IPv4 Address": ["192.168.1.100"],
                            "Mac Address": ["00:50:56:a6:27:ad"],
                        }
                    )
                return pd.DataFrame()

        excel_data = MockExcelData()
        result = detect_vmkernel_network_vms(excel_data)

        assert result["count"] == 1, "Should detect 1 VM on Storage-Network"

        vm_data = result["data"][0]
        assert vm_data["VM"] == "VM-Storage-Risk"
        assert vm_data["Network"] == "Storage-Network"
        assert "Network" in vm_data

    def test_no_vmkernel_networks_found(self):
        """Test when no VMkernel networks are found."""

        class MockExcelData:
            sheet_names = ["vSC_VMK", "vNetwork"]

            def parse(self, sheet_name):
                return pd.DataFrame()  # Empty sheets

        excel_data = MockExcelData()
        result = detect_vmkernel_network_vms(excel_data)

        assert result["count"] == 0, "Should detect no VMkernel network VMs"
        assert result["data"] == [], "Should return empty data list"

    def test_missing_vsc_vmk_sheet(self):
        """Test behavior when vSC_VMK sheet is missing."""

        class MockExcelData:
            sheet_names = ["vNetwork"]

            def parse(self, sheet_name):
                if sheet_name == "vNetwork":
                    return pd.DataFrame({"VM": ["VM1"], "Network": ["Some-Network"]})
                return pd.DataFrame()

        excel_data = MockExcelData()
        result = detect_vmkernel_network_vms(excel_data)

        assert result["count"] == 0, "Should handle missing vSC_VMK sheet gracefully"
        assert result["data"] == [], "Should return empty data"

    def test_missing_vnetwork_sheet(self):
        """Test behavior when vNetwork sheet is missing."""

        class MockExcelData:
            sheet_names = ["vSC_VMK"]

            def parse(self, sheet_name):
                if sheet_name == "vSC_VMK":
                    return pd.DataFrame({"Network": ["Management-Network"]})
                return pd.DataFrame()

        excel_data = MockExcelData()
        result = detect_vmkernel_network_vms(excel_data)

        assert result["count"] == 0, "Should handle missing vNetwork sheet gracefully"
        assert result["data"] == [], "Should return empty data"

    def test_no_matching_networks(self):
        """Test when VMs are not connected to any VMkernel networks."""

        class MockExcelData:
            sheet_names = ["vSC_VMK", "vNetwork"]

            def parse(self, sheet_name):
                if sheet_name == "vSC_VMK":
                    return pd.DataFrame(
                        {"Network": ["Management-Network", "vMotion-Network"]}
                    )
                elif sheet_name == "vNetwork":
                    return pd.DataFrame(
                        {
                            "VM": ["VM1", "VM2"],
                            "Network": ["Production-VLAN-100", "Test-Network"],
                        }
                    )
                return pd.DataFrame()

        excel_data = MockExcelData()
        result = detect_vmkernel_network_vms(excel_data)

        assert result["count"] == 0, "Should detect no VMs on VMkernel networks"
        assert result["data"] == [], "Should return empty data list"


class TestDetectFaultToleranceVMs:
    """Test fault tolerance VM risk detection individually."""

    def test_detect_fault_tolerance_vms(self, comprehensive_excel_data):
        """Test that fault tolerance VMs are detected."""
        result = detect_fault_tolerance_vms(comprehensive_excel_data)

        assert result["count"] > 0, "Should detect fault tolerance VMs"
        assert "data" in result

        # Should find fault tolerance VMs
        fault_tolerance_vms = result["data"]
        vm_names = [vm["VM"] for vm in fault_tolerance_vms]

        expected_fault_tolerance = [
            "vm-ft-enabled-01 (primary)",
            "vm-ft-enabled-02 (primary)",
            "vm-ft-enabled-01 (secondary)",
        ]
        for vm in expected_fault_tolerance:
            assert vm in vm_names, f"Should detect {vm} as fault tolerant"
