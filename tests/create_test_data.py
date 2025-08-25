#!/usr/bin/env python3
"""
Script to generate comprehensive test data for AVS RVTools Analyzer.
Creates an Excel file with all sheets and data needed to trigger all risk detections.
"""

import pandas as pd
from pathlib import Path

def create_comprehensive_test_data():
    """Create a comprehensive Excel file with data to trigger all risk detections."""

    # Define the data for each sheet
    sheets_data = {}

    # vHost sheet - for ESX versions and host-related risks
    sheets_data['vHost'] = pd.DataFrame({
        'ESX Version': [
            'VMware ESXi 6.5.0',     # Old version (blocking risk)
            'VMware ESXi 6.7.0',     # Old version (blocking risk)
            'VMware ESXi 7.0.3',     # Newer version
            'VMware ESXi 7.0.3',     # Duplicate version
            'VMware ESXi 8.0.1',     # Latest version
            'VMware ESXi 8.0.2',     # Latest version
        ],
        'CPU Model': [
            'AMD EPYC 7402P',         # Non-Intel host (risk)
            'AMD EPYC 7543',          # Non-Intel host (risk)
            'Intel Xeon Gold 6254',   # Intel host (good)
            'Intel Xeon Gold 6348',   # Intel host (good)
            'Intel Xeon Platinum 8380',  # Intel host (good)
            'Intel Xeon Platinum 8480+', # Intel host (good)
        ],
        'Host': ['esxi-host-01', 'esxi-host-02', 'esxi-host-03', 'esxi-host-04', 'esxi-host-05', 'esxi-host-06'],
        'Datacenter': ['DC-Primary', 'DC-Primary', 'DC-Primary', 'DC-Secondary', 'DC-Secondary', 'DC-Tertiary'],
        'Cluster': ['Cluster-01', 'Cluster-01', 'Cluster-01', 'Cluster-02', 'Cluster-02', 'Cluster-03'],
        '# VMs': [15, 12, 8, 6, 10, 4]
    })

    # vInfo sheet - main VM information for most risk detections
    sheets_data['vInfo'] = pd.DataFrame({
        'VM': [
            'vm-web-server-01',
            'vm-web-server-02',
            'vm-db-oracle-01',          # Oracle VM (risk)
            'vm-db-oracle-02',          # Oracle VM (risk)
            'vm-app-server-01',
            'vm-app-server-02',
            'vm-large-storage-01',      # Large provisioned (risk)
            'vm-large-storage-02',      # Large provisioned (risk)
            'vm-high-cpu-01',           # High vCPU (risk)
            'vm-high-cpu-02',           # High vCPU (risk)
            'vm-high-memory-01',        # High memory (risk)
            'vm-high-memory-02',        # High memory (risk)
            'vm-old-hw-01',             # Old hardware version (blocking risk)
            'vm-old-hw-02',             # Old hardware version (blocking risk)
            'vm-suspended-01',          # Suspended VM (blocking risk)
            'vm-suspended-02',          # Suspended VM (blocking risk)
            'vm-tools-issue-01',        # VMware Tools not running (risk)
            'vm-tools-issue-02',        # VMware Tools not running (risk)
            'vm-mixed-issues-01',       # Multiple risks in one VM
            'vm-baseline-good',         # Good VM for comparison
        ],
        'Powerstate': [
            'poweredOn', 'poweredOn', 'poweredOn', 'poweredOn',
            'poweredOn', 'poweredOn', 'poweredOn', 'poweredOn',
            'poweredOn', 'poweredOn', 'poweredOn', 'poweredOn',
            'poweredOff', 'poweredOff', 'Suspended', 'Suspended',
            'poweredOn', 'poweredOn', 'poweredOn', 'poweredOn'
        ],
        'Guest state': [
            'running', 'running', 'running', 'running',
            'running', 'running', 'running', 'running',
            'running', 'running', 'running', 'running',
            'notRunning', 'notRunning', 'notRunning', 'notRunning',
            'notRunning', 'notRunning', 'notRunning', 'running'  # VMware Tools not running (risk)
        ],
        'OS according to the VMware Tools': [
            'Microsoft Windows Server 2019', 'Microsoft Windows Server 2022',
            'Oracle Linux Server 8.5', 'Oracle Linux Server 9.1',  # Oracle OS (risk)
            'Ubuntu Linux 20.04', 'Ubuntu Linux 22.04',
            'Microsoft Windows Server 2022', 'CentOS Linux 8',
            'Red Hat Enterprise Linux 8.6', 'Red Hat Enterprise Linux 9.1',
            'Microsoft Windows Server 2016', 'Microsoft Windows Server 2019',
            'Microsoft Windows Server 2012', 'Microsoft Windows Server 2008',
            'Microsoft Windows 10', 'Microsoft Windows 11',
            'Ubuntu Linux 18.04', 'Debian GNU/Linux 11',
            'Oracle Linux Server 7.9', 'Microsoft Windows Server 2022'
        ],
        'OS according to the configuration file': [  # Required for detect_vmtools_not_running
            'Microsoft Windows Server 2019 (64-bit)', 'Microsoft Windows Server 2022 (64-bit)',
            'Oracle Linux 8 (64-bit)', 'Oracle Linux 9 (64-bit)',
            'Ubuntu Linux (64-bit)', 'Ubuntu Linux (64-bit)',
            'Microsoft Windows Server 2022 (64-bit)', 'CentOS 8 (64-bit)',
            'Red Hat Enterprise Linux 8 (64-bit)', 'Red Hat Enterprise Linux 9 (64-bit)',
            'Microsoft Windows Server 2016 (64-bit)', 'Microsoft Windows Server 2019 (64-bit)',
            'Microsoft Windows Server 2012 (64-bit)', 'Microsoft Windows Server 2008 (64-bit)',
            'Microsoft Windows 10 (64-bit)', 'Microsoft Windows 11 (64-bit)',
            'Ubuntu Linux (64-bit)', 'Debian GNU/Linux 11 (64-bit)',
            'Oracle Linux 7 (64-bit)', 'Microsoft Windows Server 2022 (64-bit)'
        ],
        'HW version': [
            13, 15, 14, 16, 17, 18, 13, 15,        # Mix of good versions
            14, 16, 17, 18, 6, 7, 11, 8,          # Old versions (risk)
            12, 10, 6, 17                          # Mix including very old
        ],
        'CPUs': [
            4, 8, 2, 4, 4, 2, 8, 4,               # Normal CPU counts
            72, 64, 8, 4, 2, 4, 4, 2,             # High CPU counts (risk)
            2, 4, 80, 8                            # Mix including very high
        ],
        'Memory': [
            8192, 16384, 4096, 8192, 8192, 4096, 8192, 16384,     # Normal memory
            8192, 8192, 1048576, 786432, 4096, 8192, 8192, 4096,  # High memory (risk)
            4096, 8192, 1572864, 16384                             # Mix including very high
        ],
        'Provisioned MiB': [
            102400, 204800, 51200, 102400, 102400, 51200, 10737418240, 10737418240,  # Large provisioned (risk)
            102400, 204800, 204800, 102400, 51200, 102400, 102400, 51200,
            102400, 204800, 10737418240, 102400
        ],
        'In Use MiB': [
            51200, 102400, 25600, 51200, 51200, 25600, 5368709120, 5368709120,
            51200, 102400, 102400, 51200, 25600, 51200, 51200, 25600,
            51200, 102400, 5368709120, 51200
        ],
        'Used MiB': [
            51200, 102400, 25600, 51200, 51200, 25600, 5368709120, 5368709120,
            51200, 102400, 102400, 51200, 25600, 51200, 51200, 25600,
            51200, 102400, 5368709120, 51200
        ],
        'Datacenter': [
            'DC-Primary', 'DC-Primary', 'DC-Primary', 'DC-Primary', 'DC-Primary', 'DC-Primary',
            'DC-Primary', 'DC-Secondary', 'DC-Secondary', 'DC-Secondary', 'DC-Secondary', 'DC-Secondary',
            'DC-Primary', 'DC-Primary', 'DC-Primary', 'DC-Secondary', 'DC-Tertiary', 'DC-Tertiary',
            'DC-Tertiary', 'DC-Primary'
        ],
        'Cluster': [
            'Cluster-01', 'Cluster-01', 'Cluster-01', 'Cluster-01', 'Cluster-01', 'Cluster-01',
            'Cluster-02', 'Cluster-02', 'Cluster-02', 'Cluster-02', 'Cluster-02', 'Cluster-02',
            'Cluster-01', 'Cluster-01', 'Cluster-01', 'Cluster-02', 'Cluster-03', 'Cluster-03',
            'Cluster-03', 'Cluster-01'
        ],
        'Host': [
            'esxi-host-01', 'esxi-host-01', 'esxi-host-02', 'esxi-host-02', 'esxi-host-01', 'esxi-host-03',
            'esxi-host-03', 'esxi-host-04', 'esxi-host-04', 'esxi-host-05', 'esxi-host-05', 'esxi-host-06',
            'esxi-host-01', 'esxi-host-02', 'esxi-host-02', 'esxi-host-04', 'esxi-host-06', 'esxi-host-06',
            'esxi-host-06', 'esxi-host-01'
        ]
    })

    # vUSB sheet - for USB device risks
    sheets_data['vUSB'] = pd.DataFrame({
        'VM': ['vm-web-server-01', 'vm-app-server-01', 'vm-db-oracle-01', 'vm-app-server-02', 'vm-mixed-issues-01'],
        'Powerstate': ['poweredOn', 'poweredOn', 'poweredOn', 'poweredOn', 'poweredOn'],
        'Device Type': ['USB Controller', 'USB Mass Storage', 'USB Smart Card Reader', 'USB Printer', 'USB Hub'],
        'Connected': [True, True, True, False, True],
        'Path': [
            '/vmfs/devices/usb/001/001',
            '/vmfs/devices/usb/002/001',
            '/vmfs/devices/usb/003/001',
            '/vmfs/devices/usb/004/001',
            '/vmfs/devices/usb/005/001'
        ]
    })

    # vDisk sheet - for risky disk configurations and shared disks
    sheets_data['vDisk'] = pd.DataFrame({
        'VM': [
            'vm-web-server-01', 'vm-web-server-02',
            'vm-db-oracle-01', 'vm-db-oracle-02',
            'vm-app-server-01', 'vm-app-server-02',
            'vm-large-storage-01', 'vm-large-storage-02',
            'vm-risky-disk-01', 'vm-risky-disk-02',     # Risky disk configurations
            'vm-mixed-issues-01', 'vm-baseline-good',
            # Shared disk VMs - 7 entries to match the 7 shared disk paths
            'vm-cluster-node-01', 'vm-cluster-node-02',  # Sharing disk path 1
            'vm-cluster-node-03', 'vm-cluster-node-04',  # Sharing disk path 2
            'vm-shared-storage-01', 'vm-shared-storage-02', 'vm-shared-storage-03',  # Sharing disk path 3
            # Additional VMs with individual shared bus configurations (not sharing paths)
            'vm-individual-shared-01', 'vm-individual-shared-02'  # Individual shared bus VMs
        ],
        'Powerstate': ['poweredOn'] * 21,
        'Disk': ['Hard disk 1'] * 21,
        'Capacity MiB': [51200, 102400, 102400, 204800, 25600, 51200, 10485760, 20971520, 51200, 102400, 51200, 25600,
                        512000, 512000, 1024000, 1024000, 2048000, 2048000, 2048000,
                        1024000, 512000],  # Additional capacity for new VMs
        'Raw': [False, False, False, False, False, False, False, False, True, True, False, False,
               False, False, False, False, False, False, False,
               False, False],  # Additional Raw values for new VMs
        'Disk Mode': [
            'persistent', 'persistent', 'persistent', 'persistent',
            'persistent', 'persistent', 'persistent', 'persistent',
            'independent_persistent', 'independent_persistent',  # Independent mode (risk)
            'independent_nonpersistent', 'persistent',
            'persistent', 'persistent', 'persistent', 'persistent', 'persistent', 'persistent', 'persistent',
            'persistent', 'persistent'  # Additional disk modes for new VMs
        ],
        'Path': [
            '[datastore1] vm-web-server-01/vm-web-server-01.vmdk',
            '[datastore1] vm-web-server-02/vm-web-server-02.vmdk',
            '[datastore2] vm-db-oracle-01/vm-db-oracle-01.vmdk',
            '[datastore2] vm-db-oracle-02/vm-db-oracle-02.vmdk',
            '[datastore1] vm-app-server-01/vm-app-server-01.vmdk',
            '[datastore1] vm-app-server-02/vm-app-server-02.vmdk',
            '[datastore3] vm-large-storage-01/vm-large-storage-01.vmdk',
            '[datastore3] vm-large-storage-02/vm-large-storage-02.vmdk',
            '[datastore1] vm-risky-disk-01/vm-risky-disk-01.vmdk',
            '[datastore1] vm-risky-disk-02/vm-risky-disk-02.vmdk',
            '[datastore1] vm-mixed-issues-01/vm-mixed-issues-01.vmdk',
            '[datastore1] vm-baseline-good/vm-baseline-good.vmdk',
            # Shared disk paths - multiple VMs sharing same path (risk)
            '[shared-datastore] cluster-shared-disk-01.vmdk',      # Shared by vm-cluster-node-01 and vm-cluster-node-02
            '[shared-datastore] cluster-shared-disk-01.vmdk',      # Same path as above
            '[shared-datastore] cluster-shared-disk-02.vmdk',      # Shared by vm-cluster-node-03 and vm-cluster-node-04
            '[shared-datastore] cluster-shared-disk-02.vmdk',      # Same path as above
            '[shared-datastore] multi-shared-storage.vmdk',        # Shared by 3 VMs
            '[shared-datastore] multi-shared-storage.vmdk',        # Same path as above
            '[shared-datastore] multi-shared-storage.vmdk',        # Same path as above
            # Individual shared bus VMs (unique paths but shared bus configuration)
            '[datastore4] vm-individual-shared-01/vm-individual-shared-01.vmdk',
            '[datastore4] vm-individual-shared-02/vm-individual-shared-02.vmdk'
        ],
        'Sharing mode': [
            'sharingNone', 'sharingNone', 'sharingNone',
            'sharingNone', 'sharingNone', 'sharingNone',
            'sharingNone', 'sharingNone', 'sharingNone',
            'sharingNone', 'sharingNone', 'sharingNone',
            'sharingMultiWriter', 'sharingMultiWriter',             # Multi-writer mode for shared disks
            'sharingMultiWriter', 'sharingMultiWriter',
            'sharingMultiWriter', 'sharingMultiWriter',
            'sharingMultiWriter',
            # Individual shared bus VMs
            'sharingMultiWriter', 'sharingMultiWriter'  # Different sharing modes for individual VMs
        ],
        'Write Through': [
            'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False',
            'True', 'True',                                       # Write through enabled
            '', '',
            '', '', '',
            # Individual shared bus VMs
            '', ''  # Write through settings for individual VMs
        ],
        'Shared Bus': [
            'noSharing', 'noSharing', 'noSharing', 'noSharing',
            'noSharing', 'noSharing', 'noSharing', 'noSharing',
            'noSharing', 'noSharing', 'noSharing', 'noSharing',
            'physicalSharing', 'physicalSharing',                     # Shared Bus
            'virtualSharing', 'virtualSharing',
            'physicalSharing', 'physicalSharing', 'physicalSharing',
            # Individual shared bus VMs (these should be detected by the new logic)
            'virtualSharing', 'physicalSharing'  # Individual VMs with shared bus configurations
        ]
    })

    # dvSwitch and vNetwork sheets - for network switch risks
    sheets_data['dvSwitch'] = pd.DataFrame({
        'Switch': ['dvSwitch-01', 'dvSwitch-02'],  # Note: Switch column not Name
        'Name': ['dvSwitch-01', 'dvSwitch-02'],
        'Type': ['Distributed Virtual Switch', 'Distributed Virtual Switch'],
        'Version': ['7.0.3', '8.0.1'],
        'Datacenter': ['DC-Primary', 'DC-Secondary']
    })

    sheets_data['vNetwork'] = pd.DataFrame({
        'VM': [
            'vm-standard-switch-01', 'vm-standard-switch-02', 'vm-standard-switch-03',
            'vm-web-server-01', 'vm-web-server-02', 'vm-db-oracle-01',
            'vm-app-server-01', 'vm-mixed-issues-01', 'vm-baseline-good'
        ],
        'Network Label': [
            'VM Network', 'Management Network', 'Storage Network',
            'Production-VLAN-100', 'Production-VLAN-200', 'Database-VLAN-300',
            'Application-VLAN-400', 'Legacy-Network', 'Modern-DVS-Network'
        ],
        'Switch': [
            'vSwitch0', 'vSwitch1', 'vSwitch2',  # Three standard vSwitches (risk)
            'dvSwitch-01', 'dvSwitch-01', 'dvSwitch-02',
            'dvSwitch-02', 'vSwitch0', 'dvSwitch-01'
        ],
        'Connected': [True] * 9,
        'Status': ['Connected'] * 9
    })

    # vSnapshot sheet - for snapshot risks
    sheets_data['vSnapshot'] = pd.DataFrame({
        'VM': [
            'vm-db-oracle-01', 'vm-db-oracle-02', 'vm-app-server-01', 'vm-app-server-02',
            'vm-web-server-01', 'vm-web-server-02', 'vm-large-storage-01', 'vm-mixed-issues-01'
        ],
        'Powerstate': ['poweredOn'] * 8,
        'Name': [
            'Pre-patch snapshot', 'Database backup point', 'Before upgrade', 'Performance baseline',
            'Backup point', 'Security update prep', 'Storage migration prep', 'Multi-snapshot-vm'
        ],
        'Description': [
            'Created before monthly patching',
            'Before database schema upgrade',
            'Before application upgrade',
            'Baseline before performance tuning',
            'Daily backup snapshot',
            'Before security patch installation',
            'Before storage vMotion',
            'Multiple snapshots for testing'
        ],
        'Date / time': [
            '2024-01-15 10:30:00', '2024-01-20 14:15:00', '2024-01-25 02:00:00', '2024-02-01 16:45:00',
            '2024-02-05 08:30:00', '2024-02-10 12:15:00', '2024-02-15 18:00:00', '2024-02-20 22:30:00'
        ],
        'Size MiB (vmsn)': [5120, 8192, 2048, 4096, 1024, 3072, 15360, 6144]
    })

    # dvPort sheet - for distributed virtual port issues
    sheets_data['dvPort'] = pd.DataFrame({
        'VM': [
            'vm-web-server-01', 'vm-db-oracle-01', 'vm-risky-port-01', 'vm-risky-port-02',
            'vm-app-server-01', 'vm-security-risk-01', 'vm-ephemeral-risk-01', 'vm-ephemeral-risk-02', 'vm-baseline-good'
        ],
        'Port': ['50000001', '50000002', '50000003', '50000004', '50000005', '50000006', '50000007', '50000008', '50000009'],
        'Switch': ['dvSwitch-01'] * 9,
        'Object ID': ['1001', '1002', '1003', '1004', '1005', '1006', '1007', '1008', '1009'],
        'Type': ['static', 'static', 'ephemeral', 'ephemeral', 'static', 'static', 'ephemeral', 'ephemeral', 'static'],  # Ephemeral types (HCX migration risk)
        'VLAN': [100, None, 200, None, 300, 400, 500, 600, 700],  # Null VLANs (risk)
        'Allow Promiscuous': ['False', 'True', 'False', 'False', 'False', 'True', 'False', 'False', 'False'],  # Promiscuous mode (risk)
        'Mac Changes': ['False', 'False', 'True', 'False', 'False', 'True', 'False', 'False', 'False'],  # MAC changes (risk)
        'Forged Transmits': ['False', 'True', 'False', 'True', 'False', 'True', 'False', 'False', 'False'],  # Forged transmits (risk)
        'Connected': [True, True, False, True, True, True, True, True, True],
        'Status': ['Connected', 'Connected', 'Disconnected', 'Connected', 'Connected', 'Connected', 'Connected', 'Connected', 'Connected']
    })

    # vCD sheet - for CD-ROM device risks
    sheets_data['vCD'] = pd.DataFrame({
        'VM': [
            'vm-app-server-01', 'vm-web-server-01', 'vm-db-oracle-01', 'vm-db-oracle-02',
            'vm-mixed-issues-01', 'vm-iso-mounted-01', 'vm-baseline-good'
        ],
        'Powerstate': ['poweredOn'] * 7,
        'Connected': ['True', 'False', 'True', 'True', 'True', 'True', 'False'],  # String values, risk when "True"
        'Starts Connected': ['True', 'False', 'True', 'True', 'True', 'False', 'False'],
        'ISO Path': [
            '[datastore1] iso/windows-server-2019.iso',
            '',
            '[datastore2] iso/oracle-linux-8.5.iso',
            '[datastore1] iso/oracle-database-19c.iso',
            '[datastore3] iso/mixed-tools.iso',
            '[datastore1] iso/vmware-tools.iso',
            ''
        ],
        'Device Type': ['CD/DVD drive'] * 7
    })

    # Create the Excel file
    output_path = Path(__file__).parent / 'test-data' / 'comprehensive_test_data.xlsx'

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet_name, df in sheets_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"✅ Created comprehensive test data file: {output_path}")
    print(f"📊 Created {len(sheets_data)} sheets with expanded data for better test coverage:")
    for sheet_name, df in sheets_data.items():
        print(f"   - {sheet_name}: {len(df)} rows")

    print("\n🎯 All 15 risk functions should be triggered with multiple instances:")
    risk_functions = [
        "detect_esx_versions (vHost - multiple old ESX versions)",
        "detect_vusb_devices (vUSB - different USB device types)",
        "detect_risky_disks (vDisk - raw/independent disks across VMs)",
        "detect_non_dvs_switches (vNetwork - standard vSwitches)",
        "detect_snapshots (vSnapshot - snapshots across VMs)",
        "detect_suspended_vms (vInfo - suspended VMs)",
        "detect_oracle_vms (vInfo - Oracle VMs)",
        "detect_dvport_issues (dvPort - multiple security issues)",
        "detect_non_intel_hosts (vHost - AMD hosts)",
        "detect_vmtools_not_running (vInfo - VMs with tools issues)",
        "detect_cdrom_issues (vCD - VMs with connected CD-ROMs)",
        "detect_large_provisioned_vms (vInfo - VMs >10TB)",
        "detect_high_vcpu_vms (vInfo - VMs with high CPU count)",
        "detect_high_memory_vms (vInfo - VMs with high memory)",
        "detect_hw_version_compatibility (vInfo - VMs with old HW versions)",
        "detect_shared_disks (vDisk - VMs with shared disks)"
    ]
    for i, risk in enumerate(risk_functions, 1):
        print(f"   {i:2d}. {risk}")
    return output_path

if __name__ == "__main__":
    create_comprehensive_test_data()
