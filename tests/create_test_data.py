#!/usr/bin/env python3
"""
Simple data-driven test data generator for AVS RVTools Analyzer.
Uses pure data definitions with minimal code.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

# =============================================================================
# DATA DEFINITIONS - Just modify these to change test data
# =============================================================================

# Base VM definitions - simple list of VMs with their properties
VMS = [
    # Oracle VMs (risk)
    {
        "name": "vm-db-oracle-01",
        "type": "oracle",
        "os": "Oracle Linux Server 8.5",
        "os_config": "Oracle Linux 8 (64-bit)",
    },
    {
        "name": "vm-db-oracle-02",
        "type": "oracle",
        "os": "Oracle Linux Server 9.1",
        "os_config": "Oracle Linux 9 (64-bit)",
    },
    # Suspended VMs (blocking risk)
    {
        "name": "vm-suspended-01",
        "type": "suspended",
        "powerstate": "Suspended",
        "guest_state": "notRunning",
        "hw_version": 11,
    },
    {
        "name": "vm-suspended-02",
        "type": "suspended",
        "powerstate": "Suspended",
        "guest_state": "notRunning",
        "hw_version": 8,
    },
    # Old hardware VMs (blocking risk)
    {
        "name": "vm-old-hw-01",
        "type": "old_hw",
        "hw_version": 6,
        "powerstate": "poweredOff",
        "guest_state": "notRunning",
    },
    {
        "name": "vm-old-hw-02",
        "type": "old_hw",
        "hw_version": 7,
        "powerstate": "poweredOff",
        "guest_state": "notRunning",
    },
    # High CPU VMs (risk)
    {
        "name": "vm-high-cpu-01",
        "type": "high_cpu",
        "cpus": 72,
        "os": "Red Hat Enterprise Linux 8.6",
    },
    {
        "name": "vm-high-cpu-02",
        "type": "high_cpu",
        "cpus": 64,
        "os": "Red Hat Enterprise Linux 9.1",
    },
    # High memory VMs (risk)
    {"name": "vm-high-memory-01", "type": "high_memory", "memory": 1048576},  # 1TB
    {"name": "vm-high-memory-02", "type": "high_memory", "memory": 786432},  # 768GB
    # Large storage VMs (risk)
    {
        "name": "vm-large-storage-01",
        "type": "large_storage",
        "provisioned": 10737418240,
        "capacity": 10485760,
    },  # >10TB
    {
        "name": "vm-large-storage-02",
        "type": "large_storage",
        "provisioned": 20971520000,
        "capacity": 20971520,
    },  # >20TB
    # VMware Tools issues (risk)
    {
        "name": "vm-tools-issue-01",
        "type": "tools_issue",
        "guest_state": "notRunning",
        "os": "Ubuntu Linux 18.04",
    },
    {
        "name": "vm-tools-issue-02",
        "type": "tools_issue",
        "guest_state": "notRunning",
        "os": "Debian GNU/Linux 11",
    },
    # Shared disk VMs (risk)
    {"name": "vm-cluster-node-01", "type": "shared_disk", "shared_group": "cluster1"},
    {"name": "vm-cluster-node-02", "type": "shared_disk", "shared_group": "cluster1"},
    {"name": "vm-cluster-node-03", "type": "shared_disk", "shared_group": "cluster2"},
    {"name": "vm-cluster-node-04", "type": "shared_disk", "shared_group": "cluster2"},
    {
        "name": "vm-shared-storage-01",
        "type": "shared_disk",
        "shared_group": "multi_shared",
    },
    {
        "name": "vm-shared-storage-02",
        "type": "shared_disk",
        "shared_group": "multi_shared",
    },
    {
        "name": "vm-shared-storage-03",
        "type": "shared_disk",
        "shared_group": "multi_shared",
    },
    {"name": "vm-individual-shared-01", "type": "individual_shared"},
    {"name": "vm-individual-shared-02", "type": "individual_shared"},
    # Risky disk VMs
    {
        "name": "vm-risky-disk-01",
        "type": "raw_disk",
        "disk_raw": True,
        "disk_raw_mode": "physicalMode",
    },
    {
        "name": "vm-risky-disk-02",
        "type": "raw_disk",
        "disk_raw": True,
        "disk_raw_mode": "virtualMode",
    },
    {
        "name": "vm-risky-disk-03",
        "type": "raw_disk",
        "disk_raw": True,
        "disk_raw_mode": "physicalMode",
    },
    {
        "name": "vm-risky-disk-04",
        "type": "independent_disk",
        "disk_mode": "independent_persistent",
    },
    # Standard VMs (good)
    {"name": "vm-web-server-01", "type": "web"},
    {"name": "vm-web-server-02", "type": "web", "memory": 16384, "provisioned": 204800},
    # Password exposure VMs (critical security risk)
    {
        "name": "vm-password-exposed-01",
        "type": "web",
        "annotation": "Admin user password is admin123 - change after deployment",
    },
    {
        "name": "vm-password-exposed-02",
        "type": "web",
        "annotation": "Service account pwd: ServicePass456",
    },
    {
        "name": "vm-password-exposed-03",
        "type": "web",
        "annotation": "Contains secret key and credentials for DB access",
    },
    {
        "name": "vm-clean-annotation",
        "type": "web",
        "annotation": "Regular server configuration notes",
    },
    # VMkernel network VMs (warning risk - VMs connected to management networks)
    {
        "name": "vm-vmkernel-mgmt-01",
        "type": "vmkernel_risk",
        "vmkernel_network": "vMotion-Network",
    },
    {
        "name": "vm-vmkernel-mgmt-02",
        "type": "vmkernel_risk",
        "vmkernel_network": "Management-Network",
    },
    {
        "name": "vm-vmkernel-storage-01",
        "type": "vmkernel_risk",
        "vmkernel_network": "Storage-Network",
    },
    {"name": "vm-app-server-01", "type": "app", "os": "Ubuntu Linux 20.04"},
    {"name": "vm-app-server-02", "type": "app", "os": "Ubuntu Linux 22.04"},
    # Mixed issues VM
    {
        "name": "vm-mixed-issues-01",
        "type": "mixed",
        "os": "Oracle Linux Server 7.9",
        "hw_version": 6,
        "cpus": 80,
        "memory": 1572864,
        "provisioned": 10737418240,
    },
    # Baseline
    {"name": "vm-baseline-good", "type": "baseline"},
    # VM with Fault Tolerance enabled
    {
        "name": "vm-ft-enabled-01 (primary)",
        "type": "ft_enabled",
        "ft_state": "running",
        "ft_role": "1",
    },
    {
        "name": "vm-ft-enabled-01 (secondary)",
        "type": "ft_enabled",
        "ft_state": "running",
        "ft_role": "2",
    },
    {
        "name": "vm-ft-enabled-02 (primary)",
        "type": "ft_enabled",
        "ft_state": "needSecondary",
        "ft_role": "1",
    },
    {
        "name": "vm-ft-notenabled-01",
        "type": "ft_enabled",
        "ft_state": "notConfigured",
        "ft_role": "",
    },
]

# Host definitions
HOSTS = [
    {
        "name": "esxi-host-01",
        "esx_version": "VMware ESXi 6.5.0",
        "cpu_model": "AMD EPYC 7402P",
        "datacenter": "DC-Primary",
        "cluster": "Cluster-01",
    },
    {
        "name": "esxi-host-02",
        "esx_version": "VMware ESXi 6.7.0",
        "cpu_model": "AMD EPYC 7543",
        "datacenter": "DC-Primary",
        "cluster": "Cluster-01",
    },
    {
        "name": "esxi-host-03",
        "esx_version": "VMware ESXi 7.0.3",
        "cpu_model": "Intel Xeon Gold 6254",
        "datacenter": "DC-Primary",
        "cluster": "Cluster-01",
    },
    {
        "name": "esxi-host-04",
        "esx_version": "VMware ESXi 7.0.3",
        "cpu_model": "Intel Xeon Gold 6348",
        "datacenter": "DC-Secondary",
        "cluster": "Cluster-02",
    },
    {
        "name": "esxi-host-05",
        "esx_version": "VMware ESXi 8.0.1",
        "cpu_model": "Intel Xeon Platinum 8380",
        "datacenter": "DC-Secondary",
        "cluster": "Cluster-02",
    },
    {
        "name": "esxi-host-06",
        "esx_version": "VMware ESXi 8.0.2",
        "cpu_model": "Intel Xeon Platinum 8480+",
        "datacenter": "DC-Tertiary",
        "cluster": "Cluster-03",
    },
]

# USB devices - just VM names that have USB
USB_VMS = [
    {"vm": "vm-web-server-01", "device": "USB Controller", "connected": True},
    {"vm": "vm-app-server-01", "device": "USB Mass Storage", "connected": True},
    {"vm": "vm-db-oracle-01", "device": "USB Smart Card Reader", "connected": True},
    {"vm": "vm-app-server-02", "device": "USB Printer", "connected": False},
    {"vm": "vm-mixed-issues-01", "device": "USB Hub", "connected": True},
]

# Snapshots - just VM names that have snapshots
SNAPSHOTS = [
    {
        "vm": "vm-db-oracle-01",
        "name": "Pre-patch snapshot",
        "desc": "Created before monthly patching",
        "date": "2024-01-15 10:30:00",
        "size": 5120,
    },
    {
        "vm": "vm-db-oracle-02",
        "name": "Database backup point",
        "desc": "Before database schema upgrade",
        "date": "2024-01-20 14:15:00",
        "size": 8192,
    },
    {
        "vm": "vm-app-server-01",
        "name": "Before upgrade",
        "desc": "Before application upgrade",
        "date": "2024-01-25 02:00:00",
        "size": 2048,
    },
    {
        "vm": "vm-app-server-02",
        "name": "Performance baseline",
        "desc": "Baseline before performance tuning",
        "date": "2024-02-01 16:45:00",
        "size": 4096,
    },
    {
        "vm": "vm-web-server-01",
        "name": "Backup point",
        "desc": "Daily backup snapshot",
        "date": "2024-02-05 08:30:00",
        "size": 1024,
    },
    {
        "vm": "vm-web-server-02",
        "name": "Security update prep",
        "desc": "Before security patch installation",
        "date": "2024-02-10 12:15:00",
        "size": 3072,
    },
    {
        "vm": "vm-large-storage-01",
        "name": "Storage migration prep",
        "desc": "Before storage vMotion",
        "date": "2024-02-15 18:00:00",
        "size": 15360,
    },
    {
        "vm": "vm-mixed-issues-01",
        "name": "Multi-snapshot-vm",
        "desc": "Multiple snapshots for testing",
        "date": "2024-02-20 22:30:00",
        "size": 6144,
    },
    # Password exposure snapshots (critical security risk)
    {
        "vm": "vm-password-exposed-01",
        "name": "Password reset point",
        "desc": "Before password change - old password was SecretPass123",
        "date": "2024-02-25 09:00:00",
        "size": 2048,
    },
    {
        "vm": "vm-password-exposed-02",
        "name": "Credential backup",
        "desc": "Service credentials updated - passphrase stored in config",
        "date": "2024-02-26 11:30:00",
        "size": 1536,
    },
    {
        "vm": "vm-clean-annotation",
        "name": "Clean snapshot",
        "desc": "Regular maintenance snapshot without sensitive data",
        "date": "2024-02-27 14:00:00",
        "size": 1024,
    },
]

# CD-ROM devices - just VM names that have CD-ROMs
CDROMS = [
    {
        "vm": "vm-app-server-01",
        "connected": "True",
        "starts": "True",
        "iso": "[datastore1] iso/windows-server-2019.iso",
    },
    {"vm": "vm-web-server-01", "connected": "False", "starts": "False", "iso": ""},
    {
        "vm": "vm-db-oracle-01",
        "connected": "True",
        "starts": "True",
        "iso": "[datastore2] iso/oracle-linux-8.5.iso",
    },
    {
        "vm": "vm-db-oracle-02",
        "connected": "True",
        "starts": "True",
        "iso": "[datastore1] iso/oracle-database-19c.iso",
    },
    {
        "vm": "vm-mixed-issues-01",
        "connected": "True",
        "starts": "True",
        "iso": "[datastore3] iso/mixed-tools.iso",
    },
    {"vm": "vm-baseline-good", "connected": "False", "starts": "False", "iso": ""},
]

# Standard switch VMs (risk)
STANDARD_SWITCH_VMS = [
    {"vm": "vm-standard-switch-01", "label": "VM Network", "switch": "vSwitch0"},
    {
        "vm": "vm-standard-switch-02",
        "label": "Management Network",
        "switch": "vSwitch1",
    },
    {"vm": "vm-standard-switch-03", "label": "Storage Network", "switch": "vSwitch2"},
    {"vm": "vm-mixed-issues-01", "label": "Legacy-Network", "switch": "vSwitch0"},
]

# dvPort configurations
DVPORTS = [
    {
        "vm": "vm-web-server-01",
        "type": "earlyBinding",
        "vlan": 100,
        "promiscuous": "False",
        "mac": "False",
        "forge": "False",
    },
    {
        "vm": "vm-db-oracle-01",
        "type": "earlyBinding",
        "vlan": None,
        "promiscuous": "True",
        "mac": "False",
        "forge": "True",
    },
    {
        "vm": "vm-risky-port-01",
        "type": "ephemeral",
        "vlan": 200,
        "promiscuous": "False",
        "mac": "True",
        "forge": "False",
    },
    {
        "vm": "vm-risky-port-02",
        "type": "ephemeral",
        "vlan": None,
        "promiscuous": "False",
        "mac": "False",
        "forge": "True",
    },
    {
        "vm": "vm-app-server-01",
        "type": "earlyBinding",
        "vlan": 300,
        "promiscuous": "False",
        "mac": "False",
        "forge": "False",
    },
    {
        "vm": "vm-security-risk-01",
        "type": "earlyBinding",
        "vlan": 400,
        "promiscuous": "True",
        "mac": "True",
        "forge": "True",
    },
    {
        "vm": "vm-ephemeral-risk-01",
        "type": "ephemeral",
        "vlan": 500,
        "promiscuous": "False",
        "mac": "False",
        "forge": "False",
    },
    {
        "vm": "vm-ephemeral-risk-02",
        "type": "ephemeral",
        "vlan": 600,
        "promiscuous": "False",
        "mac": "False",
        "forge": "False",
    },
    {
        "vm": "vm-baseline-good",
        "type": "earlyBinding",
        "vlan": 700,
        "promiscuous": "False",
        "mac": "False",
        "forge": "False",
    },
]

# VMkernel network interfaces (for ESXi management traffic)
VMKERNEL_INTERFACES = [
    {
        "host": "esxi-host-01",
        "device": "vmk0",
        "network": "Management-Network",
        "ip": "192.168.10.101",
        "netmask": "255.255.255.0",
        "mtu": 1500,
        "services": "Management",
    },
    {
        "host": "esxi-host-01",
        "device": "vmk1",
        "network": "vMotion-Network",
        "ip": "192.168.20.101",
        "netmask": "255.255.255.0",
        "mtu": 9000,
        "services": "vMotion",
    },
    {
        "host": "esxi-host-01",
        "device": "vmk2",
        "network": "Storage-Network",
        "ip": "192.168.30.101",
        "netmask": "255.255.255.0",
        "mtu": 9000,
        "services": "",
    },
    {
        "host": "esxi-host-02",
        "device": "vmk0",
        "network": "Management-Network",
        "ip": "192.168.10.102",
        "netmask": "255.255.255.0",
        "mtu": 1500,
        "services": "Management",
    },
    {
        "host": "esxi-host-02",
        "device": "vmk1",
        "network": "vMotion-Network",
        "ip": "192.168.20.102",
        "netmask": "255.255.255.0",
        "mtu": 9000,
        "services": "vMotion",
    },
    {
        "host": "esxi-host-02",
        "device": "vmk2",
        "network": "Storage-Network",
        "ip": "192.168.30.102",
        "netmask": "255.255.255.0",
        "mtu": 9000,
        "services": "",
    },
    {
        "host": "esxi-host-03",
        "device": "vmk0",
        "network": "Management-Network",
        "ip": "192.168.10.103",
        "netmask": "255.255.255.0",
        "mtu": 1500,
        "services": "Management",
    },
    {
        "host": "esxi-host-03",
        "device": "vmk1",
        "network": "vMotion-Network",
        "ip": "192.168.20.103",
        "netmask": "255.255.255.0",
        "mtu": 9000,
        "services": "vMotion",
    },
]

# Shared disk groups
SHARED_DISK_GROUPS = {
    "cluster1": "[shared-datastore] cluster-shared-disk-01.vmdk",
    "cluster2": "[shared-datastore] cluster-shared-disk-02.vmdk",
    "multi_shared": "[shared-datastore] multi-shared-storage.vmdk",
}

# Default values for VMs
VM_DEFAULTS = {
    "powerstate": "poweredOn",
    "guest_state": "running",
    "os": "Microsoft Windows Server 2022",
    "os_config": "Microsoft Windows Server 2022 (64-bit)",
    "hw_version": 17,
    "cpus": 4,
    "memory": 8192,
    "provisioned": 102400,
    "datacenter": "DC-Primary",
    "cluster": "Cluster-01",
    "host": "esxi-host-01",
    "capacity": 51200,
}


# =============================================================================
# SIMPLE SHEET BUILDERS - Minimal code, just data transformation
# =============================================================================


def build_vhost_sheet() -> pd.DataFrame:
    """Build vHost sheet from host data."""
    data = []
    for host in HOSTS:
        vm_count = len(
            [vm for vm in VMS if vm.get("host", VM_DEFAULTS["host"]) == host["name"]]
        )
        data.append(
            {
                "Host": host["name"],
                "ESX Version": host["esx_version"],
                "CPU Model": host["cpu_model"],
                "Datacenter": host["datacenter"],
                "Cluster": host["cluster"],
                "# VMs": vm_count,
            }
        )
    return pd.DataFrame(data)


def build_vinfo_sheet() -> pd.DataFrame:
    """Build vInfo sheet from VM data."""
    data = []
    for vm in VMS:
        # Apply defaults and overrides
        vm_data = {**VM_DEFAULTS, **vm}

        # Calculate derived values
        in_use = vm_data["provisioned"] // 2

        data.append(
            {
                "VM": vm_data["name"],
                "Powerstate": vm_data["powerstate"],
                "Guest state": vm_data["guest_state"],
                "OS according to the VMware Tools": vm_data["os"],
                "OS according to the configuration file": vm_data["os_config"],
                "HW version": vm_data["hw_version"],
                "CPUs": vm_data["cpus"],
                "Memory": vm_data["memory"],
                "Provisioned MiB": vm_data["provisioned"],
                "In Use MiB": in_use,
                "Used MiB": in_use,
                "Datacenter": vm_data["datacenter"],
                "Cluster": vm_data["cluster"],
                "Host": vm_data["host"],
                "Annotation": vm_data.get("annotation", ""),
                "FT State": vm_data.get("ft_state", "notConfigured"),
                "FT Role": vm_data.get("ft_role", "primary"),
            }
        )
    return pd.DataFrame(data)


def build_vdisk_sheet() -> pd.DataFrame:
    """Build vDisk sheet from VM data."""
    data = []
    for vm in VMS:
        vm_data = {**VM_DEFAULTS, **vm}

        # Determine disk path
        disk_path = f"[datastore1] {vm_data['name']}/{vm_data['name']}.vmdk"
        if vm_data.get("shared_group"):
            disk_path = SHARED_DISK_GROUPS[vm_data["shared_group"]]

        # Determine sharing mode and shared bus
        sharing_mode = "sharingNone"
        shared_bus = "noSharing"
        write_through = "False"

        if vm_data.get("type") in ["shared_disk", "individual_shared"]:
            sharing_mode = "sharingMultiWriter"
            shared_bus = "physicalSharing"
            if vm_data.get("shared_group") in ["cluster1", "cluster2"]:
                write_through = "True"

        data.append(
            {
                "VM": vm_data["name"],
                "Powerstate": vm_data["powerstate"],
                "Disk": "Hard disk 1",
                "Capacity MiB": vm_data["capacity"],
                "Raw": vm_data.get("disk_raw", False),
                "Raw Com. Mode": vm_data.get("disk_raw_mode", ""),
                "Disk Mode": vm_data.get("disk_mode", "persistent"),
                "Path": disk_path,
                "Sharing mode": sharing_mode,
                "Write Through": write_through,
                "Shared Bus": shared_bus,
            }
        )
    return pd.DataFrame(data)


def build_vusb_sheet() -> pd.DataFrame:
    """Build vUSB sheet from USB data."""
    data = []
    for i, usb in enumerate(USB_VMS):
        data.append(
            {
                "VM": usb["vm"],
                "Powerstate": "poweredOn",
                "Device Type": usb["device"],
                "Connected": usb["connected"],
                "Path": f"/vmfs/devices/usb/{i+1:03d}/001",
            }
        )
    return pd.DataFrame(data)


def build_vsnapshot_sheet() -> pd.DataFrame:
    """Build vSnapshot sheet from snapshot data."""
    data = []
    for snap in SNAPSHOTS:
        data.append(
            {
                "VM": snap["vm"],
                "Powerstate": "poweredOn",
                "Name": snap["name"],
                "Description": snap["desc"],
                "Date / time": snap["date"],
                "Size MiB (vmsn)": snap["size"],
            }
        )
    return pd.DataFrame(data)


def build_vcd_sheet() -> pd.DataFrame:
    """Build vCD sheet from CD-ROM data."""
    data = []
    for cd in CDROMS:
        data.append(
            {
                "VM": cd["vm"],
                "Powerstate": "poweredOn",
                "Connected": cd["connected"],
                "Starts Connected": cd["starts"],
                "ISO Path": cd["iso"],
                "Device Type": "CD/DVD drive",
            }
        )
    return pd.DataFrame(data)


def build_vnetwork_sheet() -> pd.DataFrame:
    """Build vNetwork sheet from network data."""
    data = []

    # Add standard switch VMs (risks)
    for net in STANDARD_SWITCH_VMS:
        data.append(
            {
                "VM": net["vm"],
                "Powerstate": "poweredOn",
                "Network": net["label"],  # Using Network column as specified
                "Switch": net["switch"],
                "Connected": True,
                "Status": True,
                "Starts Connected": True,
                "IPv4 Address": "192.168.1.100",
                "Mac Address": "00:50:56:a6:27:ad",
            }
        )

    # Add some DVS VMs (good)
    dvs_vms = [
        "vm-web-server-01",
        "vm-web-server-02",
        "vm-db-oracle-01",
        "vm-app-server-01",
        "vm-baseline-good",
    ]
    for i, vm in enumerate(dvs_vms):
        network_label = f"Production-VLAN-{100 + i * 100}"
        data.append(
            {
                "VM": vm,
                "Powerstate": "poweredOn",
                "Network": network_label,  # Using Network column as specified
                "Switch": f"dvSwitch-{(i % 2) + 1:02d}",
                "Connected": True,
                "Starts Connected": True,
                "IPv4 Address": "192.168.1.100",
                "Mac Address": "00:50:56:a6:27:ad",
            }
        )

    # Add VMs connected to VMkernel networks (WARNING RISK!)
    vmkernel_vms = [
        {"vm": "vm-vmkernel-mgmt-01", "network": "Management-Network"},
        {"vm": "vm-vmkernel-mgmt-02", "network": "Management-Network"},
        {"vm": "vm-vmkernel-storage-01", "network": "Storage-Network"},
    ]

    for vm_data in vmkernel_vms:
        data.append(
            {
                "VM": vm_data["vm"],
                "Powerstate": "poweredOn",
                "Network": vm_data["network"],  # This will match VMkernel networks!
                "Switch": (
                    "vSwitch0"
                ),  # VMkernel networks typically on standard switches
                "Connected": True,
                "Starts Connected": True,
                "IPv4 Address": "192.168.1.100",
                "Mac Address": "00:50:56:a6:27:ad",
            }
        )

    return pd.DataFrame(data)


def build_vsc_vmk_sheet() -> pd.DataFrame:
    """Build vSC_VMK sheet (VMkernel network interfaces) from VMkernel data."""
    data = []

    for vmk in VMKERNEL_INTERFACES:
        data.append(
            {
                "Host": vmk["host"],
                "Device": vmk["device"],
                "Port Group": vmk["network"],  # This is the key column for detection
                "IP Address": vmk["ip"],
                "Subnet mask": vmk["netmask"],
                "MTU": vmk["mtu"],
                "Datacenter": "DC-Primary",
                "Cluster": "Cluster-01",
            }
        )

    return pd.DataFrame(data)


def build_dvport_sheet() -> pd.DataFrame:
    """Build dvPort sheet from dvPort data."""
    data = []
    for i, port in enumerate(DVPORTS):
        data.append(
            {
                "VM": port["vm"],
                "Port": str(50000001 + i),
                "Switch": "dvSwitch-01",
                "Object ID": str(1001 + i),
                "Type": port["type"],
                "VLAN": port["vlan"],
                "Allow Promiscuous": port["promiscuous"],
                "Mac Changes": port["mac"],
                "Forged Transmits": port["forge"],
                "Connected": i != 2,  # One disconnected
                "Status": "Connected" if i != 2 else "Disconnected",
            }
        )
    return pd.DataFrame(data)


def build_dvswitch_sheet() -> pd.DataFrame:
    """Build dvSwitch sheet."""
    return pd.DataFrame(
        [
            {
                "Switch": "dvSwitch-01",
                "Name": "dvSwitch-01",
                "Type": "Distributed Virtual Switch",
                "Version": "7.0.3",
                "Datacenter": "DC-Primary",
            },
            {
                "Switch": "dvSwitch-02",
                "Name": "dvSwitch-02",
                "Type": "Distributed Virtual Switch",
                "Version": "8.0.1",
                "Datacenter": "DC-Secondary",
            },
        ]
    )


# =============================================================================
# MAIN FUNCTION - Just orchestration
# =============================================================================


def create_comprehensive_test_data(output_path: Optional[Path] = None) -> Path:
    """Create comprehensive test data from the data definitions above."""

    print("🔄 Building test data from data definitions...")

    # Build all sheets
    sheets = {
        "vHost": build_vhost_sheet(),
        "vInfo": build_vinfo_sheet(),
        "vDisk": build_vdisk_sheet(),
        "vUSB": build_vusb_sheet(),
        "vSnapshot": build_vsnapshot_sheet(),
        "vCD": build_vcd_sheet(),
        "vNetwork": build_vnetwork_sheet(),
        "vSC_VMK": build_vsc_vmk_sheet(),
        "dvPort": build_dvport_sheet(),
        "dvSwitch": build_dvswitch_sheet(),
    }

    # Create output path
    if output_path is None:
        output_path = (
            Path(__file__).parent / "test-data" / "comprehensive_test_data.xlsx"
        )

    # Write to Excel
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"✅ Created test data file: {output_path}")
    print(f"📊 Created {len(sheets)} sheets:")
    for sheet_name, df in sheets.items():
        print(f"   - {sheet_name}: {len(df)} rows")

    return output_path


if __name__ == "__main__":
    create_comprehensive_test_data()
