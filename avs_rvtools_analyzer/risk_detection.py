"""
Risk detection module for RVTools analysis.
Contains individual risk detection functions and a gatherer function.
"""

import logging
import re
from typing import Any, Dict, List

import pandas as pd

from .config import MigrationMethodsConfig
from .decorators import risk_info
from .helpers import (
    clean_function_name_for_display,
    convert_mib_to_tb,
    create_empty_result,
    filter_dataframe_by_condition,
    get_risk_category,
    load_sku_data,
    safe_sheet_access,
)

# Import from our new modules
from .models import (
    ESXVersionThresholds,
    GuestStates,
    NetworkConstants,
    PowerStates,
    RiskLevel,
    StorageConstants,
)
from .utils import contains_password_reference, redact_password_content

logger = logging.getLogger(__name__)

########################################################################################################################
#                                                                                                                      #
#                                               Risk Detection Functions                                               #
#                                                                                                                      #
########################################################################################################################


@risk_info(
    level=RiskLevel.INFO,
    description="This shows the distribution of ESX versions found in the uploaded file.",
    alert_message="""Having multiple ESX versions in the environment can lead to compatibility issues and
    increased complexity during migration.<br><br>It's recommended to standardize on a single ESX version
    if possible.""",
)
def detect_esx_versions(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect ESX versions and their risk levels."""
    vhost_data = safe_sheet_access(excel_data, "vHost")
    if vhost_data is None:
        logger.warning("detect_esx_versions: No vHost sheet found")
        return create_empty_result()

    version_counts = vhost_data["ESX Version"].value_counts()
    version_risks = {}
    card_risk = "info"

    # Convert to list of dictionaries format for consistent API response
    version_data = []
    for version_str, count in version_counts.items():
        risk_level = "info"  # Default risk level

        version_match = re.search(r"ESXi (\d+\.\d+\.\d+)", version_str)
        if version_match:
            version_num = version_match.group(1)
            if version_num < ESXVersionThresholds.ERROR_THRESHOLD:
                risk_level = "blocking"
                card_risk = "danger"
            elif version_num < ESXVersionThresholds.WARNING_THRESHOLD:
                risk_level = "warning"
                if card_risk != "danger":
                    card_risk = "warning"

        version_risks[version_str] = risk_level
        version_data.append(
            {"ESX Version": version_str, "Count": count, "Risk Level": risk_level}
        )

    logger.info(
        f"detect_esx_versions: Found {len(version_counts)} ESX versions with overall risk level: {card_risk}"
    )
    return {
        "count": len(version_counts),
        "data": version_data,
        "details": {
            "version_risks": version_risks,
            "card_risk": card_risk,
            "warning_threshold": ESXVersionThresholds.WARNING_THRESHOLD,
            "error_threshold": ESXVersionThresholds.ERROR_THRESHOLD,
        },
    }


@risk_info(
    level=RiskLevel.BLOCKING,
    description="vUSB devices are USB devices that are connected to a virtual machine (VM) in a VMware environment.",
    alert_message="""Having vUSB devices connected to VMs can pose a risk during migration, as they cannot be
    transferred to an Azure Managed environment.<br><br>It's recommended to review the list of vUSB devices
    and ensure that they are necessary for the VM's operation before proceeding with the migration.""",
)
def detect_vusb_devices(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect USB devices attached to VMs."""
    vusb_data = safe_sheet_access(excel_data, "vUSB")
    if vusb_data is None:
        logger.warning("detect_vusb_devices: No vUSB sheet found")
        return create_empty_result()

    devices = vusb_data[["VM", "Powerstate", "Device Type", "Connected"]].to_dict(
        orient="records"
    )

    logger.info(
        f"detect_vusb_devices: Found {len(devices)} USB devices attached to VMs"
    )
    return {"count": len(devices), "data": devices}


@risk_info(
    level="warning",  # Changed to warning as base level since we now have dynamic risk levels
    description="Risky disks are virtual disks that are configured in a way that may pose a risk during migration.",
    alert_message="""This can include disks that are set to "Independent" mode or configured with Raw Device
    Mapping capability:<br>
    <ul>
        <li>Raw Device Mapping in physicalMode: Blocking risk — cannot be migrated</li>
        <li>Raw Device Mapping in virtualMode: Warning — bulk migration possible with disk conversion</li>
        <li>Independent persistent mode: Warning — requires special consideration</li>
    </ul>
    It's recommended to review the list of risky disks and consider reconfiguring them before proceeding with the migration.""",
)
def detect_risky_disks(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect disks with migration risks (raw or independent persistent)."""
    if "vDisk" not in excel_data.sheet_names:
        logger.info("detect_risky_disks: No vDisk sheet found")
        return {"count": 0, "data": []}

    vdisk_data = excel_data.parse("vDisk")

    # Filter using string comparison directly - no copy needed
    mask = (vdisk_data["Raw"].astype(str).str.lower() == "true") | (
        vdisk_data["Disk Mode"] == "independent_persistent"
    )

    # Select only columns that exist in the data
    columns_to_return = [
        "VM",
        "Powerstate",
        "Disk",
        "Capacity MiB",
        "Raw",
        "Disk Mode",
        "Raw Com. Mode",
    ]
    available_columns = [col for col in columns_to_return if col in vdisk_data.columns]

    risky_disks_df = vdisk_data[mask][available_columns].copy()

    # Add dynamic risk level based on Raw Com. Mode
    def determine_risk_level(row):
        # Handle Raw column - convert to string for comparison
        raw_value = str(row.get("Raw", "")).lower()
        if raw_value == "true":
            raw_com_mode = str(row.get("Raw Com. Mode", "")).lower()
            if raw_com_mode == "physicalmode":
                return "blocking"
            elif raw_com_mode == "virtualmode":
                return "warning"
            else:
                return "warning"  # Default for raw disks without specified mode
        elif row.get("Disk Mode") == "independent_persistent":
            return "warning"
        else:
            return "warning"  # Default fallback

    risky_disks_df["Risk Level"] = risky_disks_df.apply(determine_risk_level, axis=1)

    risky_disks = risky_disks_df.to_dict(orient="records")

    # Count blocking vs warning risks
    blocking_count = len(
        [disk for disk in risky_disks if disk.get("Risk Level") == "blocking"]
    )
    warning_count = len(
        [disk for disk in risky_disks if disk.get("Risk Level") == "warning"]
    )

    # Determine overall card risk level based on highest severity found
    card_risk = "warning"  # Default since base level is warning
    if blocking_count > 0:
        card_risk = "blocking"

    logger.info(
        f"detect_risky_disks: Found {len(risky_disks)} risky disks (raw or independent persistent)"
    )
    return {
        "count": len(risky_disks),
        "data": risky_disks,
        "details": {
            "blocking_risks": blocking_count,
            "warning_risks": warning_count,
            "has_physical_mode_rdm": blocking_count > 0,
            "card_risk": card_risk,
        },
    }


@risk_info(
    level="blocking",
    description="This shows the distribution of VMs and ports using dvSwitches or standard vSwitches.",
    alert_message="""HCX network extension functionality requires the use of distributed switches (dvSwitches).
    In case of standard vSwitches, the migration process will be more complex.""",
)
def detect_non_dvs_switches(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect non-dvSwitch network interfaces."""
    if "vNetwork" not in excel_data.sheet_names:
        logger.warning("detect_non_dvs_switches: No vNetwork sheet found")
        return {"count": 0, "data": []}

    vnetwork_data = excel_data.parse("vNetwork")

    # Filter out rows with empty or null Switch values
    vnetwork_data = vnetwork_data[
        vnetwork_data["Switch"].notna() & (vnetwork_data["Switch"] != "")
    ]

    # Get list of distributed switches (empty list if no dvSwitch sheet exists)
    dvswitch_list = []
    if "dvSwitch" in excel_data.sheet_names:
        dvswitch_data = excel_data.parse("dvSwitch")
        if "Switch" in dvswitch_data.columns:
            dvswitch_list = dvswitch_data["Switch"].dropna().unique()

    # Add Switch Type classification
    vnetwork_data["Switch Type"] = vnetwork_data["Switch"].apply(
        lambda x: "Standard" if x not in dvswitch_list else "Distributed"
    )

    # Count ports per switch with switch type
    switch_summary = (
        vnetwork_data.groupby(["Switch", "Switch Type"])
        .size()
        .reset_index(name="Port Count")
    )

    # Convert to list of dictionaries for consistent API response
    switch_data = switch_summary.to_dict(orient="records")

    # Count VMs using non-distributed switches (individual ports/VMs)
    non_dvs_vm_count = len(vnetwork_data[vnetwork_data["Switch Type"] == "Standard"])

    logger.info(
        f"detect_non_dvs_switches: Found {non_dvs_vm_count} VMs using standard switches"
    )
    if non_dvs_vm_count > 0:
        return {
            "count": non_dvs_vm_count,  # Count of VMs using standard switches
            "data": switch_data,  # Summary data by switch
        }
    else:
        return {"count": 0, "data": []}


@risk_info(
    level="warning",
    description="vSnapshots are virtual machine snapshots that capture the state of a VM at a specific point in time.",
    alert_message="""Having multiple vSnapshots can pose a risk during migration, as they can increase complexity
    and may lead to data loss if not handled properly.<br><br>It's recommended to review and consider
    consolidating or deleting unnecessary snapshots.""",
)
def detect_snapshots(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect VM snapshots with password redaction for security."""
    if "vSnapshot" not in excel_data.sheet_names:
        logger.warning("detect_snapshots: No vSnapshot sheet found")
        return {"count": 0, "data": []}

    vsnapshot_sheet = excel_data.parse("vSnapshot")

    # Process snapshots and redact any descriptions containing passwords
    snapshots = []
    for _, row in vsnapshot_sheet.iterrows():
        # Convert date/time to string if it's a pandas Timestamp
        date_time_value = row.get("Date / time", "")
        if hasattr(date_time_value, "isoformat"):
            date_time_value = date_time_value.isoformat()
        elif date_time_value and date_time_value != "":
            date_time_value = str(date_time_value)

        snapshot_data = {
            "VM": row.get("VM", ""),
            "Powerstate": row.get("Powerstate", ""),
            "Name": row.get("Name", ""),
            "Date / time": date_time_value,
            "Size MiB (vmsn)": row.get("Size MiB (vmsn)", ""),
            "Description": redact_password_content(row.get("Description", "")),
        }
        snapshots.append(snapshot_data)

    logger.info(f"detect_snapshots: Found {len(snapshots)} VM snapshots")
    return {"count": len(snapshots), "data": snapshots}


@risk_info(
    level="warning",
    description="Suspended VMs are virtual machines that are not currently running but have their state saved.",
    alert_message="""Suspended VMs can pose a risk during migration, as it will be necessary to power them on
    or off before proceeding.<br><br>It's recommended to review the list of suspended VMs and consider
    powering them on or off.""",
)
def detect_suspended_vms(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect suspended VMs."""
    if "vInfo" not in excel_data.sheet_names:
        logger.warning("detect_suspended_vms: No vInfo sheet found")
        return {"count": 0, "data": []}

    vinfo_data = excel_data.parse("vInfo")
    suspended_vms = vinfo_data[vinfo_data["Powerstate"] == "Suspended"][["VM"]].to_dict(
        orient="records"
    )

    logger.info(f"detect_suspended_vms: Found {len(suspended_vms)} suspended VMs")
    return {"count": len(suspended_vms), "data": suspended_vms}


@risk_info(
    level="info",
    description="Oracle VMs are virtual machines specifically configured to run Oracle software.",
    alert_message="""Oracle VMs hosting in Azure VMware Solution is supported but may require costly licensing.
    <br><br>It's recommended to review the list of Oracle VMs and envision alternative hosting options to
    avoid unnecessary costs.""",
)
def detect_oracle_vms(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect Oracle VMs."""
    if "vInfo" not in excel_data.sheet_names:
        logger.warning("detect_oracle_vms: No vInfo sheet found")
        return {"count": 0, "data": []}

    vinfo_data = excel_data.parse("vInfo")
    oracle_vms = vinfo_data[
        vinfo_data["OS according to the VMware Tools"].str.contains("Oracle", na=False)
    ][
        [
            "VM",
            "OS according to the VMware Tools",
            "Powerstate",
            "CPUs",
            "Memory",
            "Provisioned MiB",
            "In Use MiB",
        ]
    ].to_dict(
        orient="records"
    )

    logger.info(f"detect_oracle_vms: Found {len(oracle_vms)} Oracle VMs")
    return {"count": len(oracle_vms), "data": oracle_vms}


@risk_info(
    level="warning",
    description="dvPort issues are related to the configuration of distributed virtual ports in a VMware environment.",
    alert_message="""Multiple dvPort issues can pose a risk during migration:
    <ul>
        <li>VLAN ID 0 or empty — they cannot be extended via HCX.</li>
        <li>Allow Promiscuous mode enabled — This configuration may require additional setup on destination side.</li>
        <li>Mac Changes enabled — This configuration may require additional setup on destination side.</li>
        <li>Forged Transmits enabled — This configuration may require additional setup on destination side.</li>
        <li>Ephemeral binding — VMs will be migrated with NIC being disconnected.</li>
    </ul>""",
)
def detect_dvport_issues(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect dvPort configuration issues."""
    if "dvPort" not in excel_data.sheet_names:
        logger.warning("detect_dvport_issues: No dvPort sheet found")
        return {"count": 0, "data": []}

    dvport_data = excel_data.parse("dvPort")

    # Store original VLAN nulls before filling
    vlan_is_null = dvport_data["VLAN"].isnull()
    dvport_data["VLAN"] = dvport_data["VLAN"].fillna(0).astype(int)

    # Filter using string comparison directly - no copy needed
    mask = (
        vlan_is_null
        | (dvport_data["Allow Promiscuous"].astype(str).str.lower() == "true")
        | (dvport_data["Mac Changes"].astype(str).str.lower() == "true")
        | (dvport_data["Forged Transmits"].astype(str).str.lower() == "true")
        | (dvport_data["Type"].astype(str).str.lower() == "ephemeral")
    )

    # Return original values directly
    columns_to_return = [
        "Port",
        "Switch",
        "Object ID",
        "VLAN",
        "Allow Promiscuous",
        "Mac Changes",
        "Forged Transmits",
        "Type",
    ]
    available_columns = [col for col in columns_to_return if col in dvport_data.columns]

    issues = dvport_data[mask][available_columns].to_dict(orient="records")

    logger.info(
        f"detect_dvport_issues: Found {len(issues)} dvPort configuration issues"
    )
    return {"count": len(issues), "data": issues}


@risk_info(
    level="warning",
    description="Hosts with CPU models that are not Intel may pose compatibility issues during migration.",
    alert_message="""As Azure VMware Solution is Intel based service, a cold migration strategy will be
    required for the workload in these hosts.""",
)
def detect_non_intel_hosts(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect non-Intel CPU hosts."""
    if "vHost" not in excel_data.sheet_names:
        logger.warning("detect_non_intel_hosts: No vHost sheet found")
        return {"count": 0, "data": []}

    vhost_data = excel_data.parse("vHost")
    non_intel_hosts = vhost_data[
        ~vhost_data["CPU Model"].str.lower().str.contains("intel", na=False)
    ][["Host", "Datacenter", "Cluster", "CPU Model", "# VMs"]].to_dict(orient="records")

    logger.info(f"detect_non_intel_hosts: Found {len(non_intel_hosts)} non-Intel hosts")
    return {"count": len(non_intel_hosts), "data": non_intel_hosts}


@risk_info(
    level="warning",
    description="VMs that are powered on but their VMware Tools are not running.",
    alert_message="""VMs without VMware Tools running may not be able to use all the features of VMware HCX
    during migration.<br><br>It's recommended to ensure that VMware Tools are installed, running and
    up-to-date on all powered-on VMs.""",
)
def detect_vmtools_not_running(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect VMs with VMware Tools not running."""
    if "vInfo" not in excel_data.sheet_names:
        logger.warning("detect_vmtools_not_running: No vInfo sheet found")
        return {"count": 0, "data": []}

    vinfo_data = excel_data.parse("vInfo")
    vmtools_issues = vinfo_data[
        (vinfo_data["Powerstate"] == "poweredOn")
        & (vinfo_data["Guest state"] == "notRunning")
    ][
        ["VM", "Powerstate", "Guest state", "OS according to the configuration file"]
    ].to_dict(
        orient="records"
    )

    logger.info(
        f"detect_vmtools_not_running: Found {len(vmtools_issues)} VMs with VMware Tools not running"
    )
    return {"count": len(vmtools_issues), "data": vmtools_issues}


@risk_info(
    level="warning",
    description="VMs have CD-ROM devices that are connected.",
    alert_message="""CD-ROM devices connected to VMs can cause issues during migration. It's recommended to
    review and disconnect unnecessary CD-ROM devices before proceeding.""",
)
def detect_cdrom_issues(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect mounted CD/DVD drives."""
    if "vCD" not in excel_data.sheet_names:
        logger.warning("detect_cdrom_issues: No vCD sheet found")
        return {"count": 0, "data": []}

    vcd_data = excel_data.parse("vCD")

    # Filter using string comparison directly - no copy needed
    mask = vcd_data["Connected"].astype(str).str.lower() == "true"

    # Select only columns that exist in the data
    columns_to_return = [
        "VM",
        "Powerstate",
        "Connected",
        "Starts Connected",
        "Device Type",
    ]
    available_columns = [col for col in columns_to_return if col in vcd_data.columns]

    cdrom_issues = vcd_data[mask][available_columns].to_dict(orient="records")

    logger.info(
        f"detect_cdrom_issues: Found {len(cdrom_issues)} VMs with connected CD-ROM devices"
    )
    return {"count": len(cdrom_issues), "data": cdrom_issues}


@risk_info(
    level=RiskLevel.WARNING,
    description="VMs have provisioned storage exceeding 10TB.",
    alert_message="""Large provisioned storage can lead to increased migration times and potential compatibility
    issues. It's recommended to review these VMs and optimize storage usage if possible.""",
)
def detect_large_provisioned_vms(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect VMs with large provisioned disks (>10TB)."""
    vm_data = safe_sheet_access(excel_data, "vInfo")
    if vm_data is None:
        logger.warning("detect_large_provisioned_vms: No vInfo sheet found")
        return create_empty_result()

    vm_data["Provisioned MiB"] = pd.to_numeric(
        vm_data["Provisioned MiB"], errors="coerce"
    )
    vm_data["In Use MiB"] = pd.to_numeric(vm_data["In Use MiB"], errors="coerce")
    vm_data["Provisioned TB"] = (vm_data["Provisioned MiB"] * 1.048576) / (1024 * 1024)

    large_vms = vm_data[vm_data["Provisioned TB"] > 10][
        ["VM", "Provisioned MiB", "In Use MiB", "CPUs", "Memory"]
    ].to_dict(orient="records")

    logger.info(
        f"detect_large_provisioned_vms: Found {len(large_vms)} VMs with >10TB provisioned storage"
    )
    return {"count": len(large_vms), "data": large_vms}


@risk_info(
    level=RiskLevel.BLOCKING,
    description="VMs have a vCPU count higher than the core count of available SKUs.",
    alert_message="""The VMs with more vCPUs configured than the available SKUs core count will not be able
    to run on the target hosts.""",
)
def detect_high_vcpu_vms(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect VMs with high vCPU count."""
    vm_data = safe_sheet_access(excel_data, "vInfo")
    if vm_data is None:
        logger.warning("detect_high_vcpu_vms: No vInfo sheet found")
        return create_empty_result()

    # Load SKU data using cached function
    try:
        sku_data = load_sku_data()
    except FileNotFoundError:
        logger.warning("detect_high_vcpu_vms: SKU data file not found")
        return {"count": 0, "data": [], "error": "SKU data file not found"}

    vm_data["CPUs"] = pd.to_numeric(vm_data["CPUs"], errors="coerce")

    sku_cores = {sku["name"]: sku["cores"] for sku in sku_data}
    min_cores = min(sku_cores.values())

    high_vcpu_vms = []
    for _, vm in vm_data.iterrows():
        if vm["CPUs"] > min_cores:
            vm_data_entry = {
                "VM": vm["VM"],
                "vCPU Count": vm["CPUs"],
                **{
                    sku: False if vm["CPUs"] > cores else True
                    for sku, cores in sku_cores.items()
                },
            }
            high_vcpu_vms.append(vm_data_entry)

    logger.info(
        f"detect_high_vcpu_vms: Found {len(high_vcpu_vms)} VMs with high vCPU count (>{min_cores} cores)"
    )
    return {"count": len(high_vcpu_vms), "data": high_vcpu_vms}


@risk_info(
    level=RiskLevel.BLOCKING,
    description="VMs have memory usage exceeding the capabilities of available SKUs.",
    alert_message="""The VMs with more memory configured than the available capacity per node will not be able
    to run on the target hosts.<br><br>For performance best practices, it is also recommended not to exceed
    half of the available memory per node on a single VM.""",
)
def detect_high_memory_vms(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect VMs with high memory allocation."""
    vm_data = safe_sheet_access(excel_data, "vInfo")
    if vm_data is None:
        logger.warning("detect_high_memory_vms: No vInfo sheet found")
        return create_empty_result()

    # Load SKU data using cached function
    try:
        sku_data = load_sku_data()
    except FileNotFoundError:
        logger.error("detect_high_memory_vms: SKU data file not found")
        return {"count": 0, "data": [], "error": "SKU data file not found"}

    vm_data["Memory"] = pd.to_numeric(vm_data["Memory"], errors="coerce")

    min_memory = min(sku["ram"] * 1024 for sku in sku_data)

    high_memory_vms = []
    for _, vm in vm_data.iterrows():
        if vm["Memory"] > min_memory:
            vm_data_entry = {
                "VM": vm["VM"],
                "Memory (GB)": round(vm["Memory"] / 1024, 2),
                **{
                    sku["name"]: False if vm["Memory"] > sku["ram"] * 1024 else True
                    for sku in sku_data
                },
            }
            high_memory_vms.append(vm_data_entry)

    logger.info(
        f"detect_high_memory_vms: Found {len(high_memory_vms)} VMs with high memory allocation (>{min_memory / 1024} GB)"
    )
    return {"count": len(high_memory_vms), "data": high_memory_vms}


@risk_info(
    level=RiskLevel.BLOCKING,
    description="""Virtual machines with legacy hardware version have limited HCX migration capabilities to Azure VMware Solution.
    Hardware version determines the virtual machine's feature set and migration compatibility.""",
    alert_message="""You should consider upgrading the hardware version of these VMs before migration.
    This requires powering off the VM temporarily.""",
)
def detect_hw_version_compatibility(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect VMs with incompatible hardware versions for Azure VMware Solution migration."""
    vm_data = safe_sheet_access(excel_data, "vInfo")
    if vm_data is None:
        logger.warning("detect_hw_version_compatibility: No vInfo sheet found")
        return create_empty_result()

    # Check if HW version column exists
    if "HW version" not in vm_data.columns:
        logger.warning(
            "detect_hw_version_compatibility: HW version column not found in vInfo sheet"
        )
        return create_empty_result()

    # Filter VMs with hardware version issues
    incompatible_vms = []

    for _, vm in vm_data.iterrows():
        hw_version = vm.get("HW version")
        if pd.isna(hw_version):
            continue

        try:
            # Convert to numeric value
            hw_version_num = int(hw_version)

            # Get migration configuration
            migration_config = MigrationMethodsConfig()

            # Determine unsupported migration methods based on HW version
            unsupported_methods = []

            # Check if HW version is below minimum supported version
            if hw_version_num < migration_config.minimum_supported_hw_version:
                unsupported_methods = [migration_config.all_methods_unsupported_message]
            else:
                # Check each migration method against its minimum requirement
                for (
                    method_name,
                    min_hw_version,
                ) in migration_config.migration_methods.items():
                    if hw_version_num < min_hw_version:
                        unsupported_methods.append(method_name)

            # Only include VMs with migration limitations
            if unsupported_methods:
                vm_info = {
                    "VM": vm.get("VM", "Unknown"),
                    "HW Version": hw_version,
                    "Powerstate": vm.get("Powerstate", "Unknown"),
                    "Unsupported migration methods": ", ".join(unsupported_methods),
                }
                incompatible_vms.append(vm_info)

        except (ValueError, TypeError) as e:
            logger.error(
                f"Could not parse hardware version '{hw_version}' for VM {vm.get('VM', 'Unknown')}: {e}"
            )
            continue

    logger.info(
        f"detect_hw_version_compatibility: Found {len(incompatible_vms)} VMs with hardware version compatibility issues"
    )
    return {"count": len(incompatible_vms), "data": incompatible_vms}


@risk_info(
    level=RiskLevel.BLOCKING,
    description="VMs sharing disks with the same path cannot be migrated.",
    alert_message="""Virtual machines cannot be migrated while they are using a shared SCSI bus,
    flagged for multi-writer, or configured for shared VMDK disk sharing.""",
)
def detect_shared_disks(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect VMs with shared disk configurations."""
    vdisk_data = safe_sheet_access(excel_data, "vDisk")
    if vdisk_data is None:
        logger.warning("detect_shared_disks: No vDisk sheet found")
        return create_empty_result()

    # Check if required columns exist
    required_columns = ["VM", "Path"]
    if not all(col in vdisk_data.columns for col in required_columns):
        logger.warning(
            "detect_shared_disks: Required columns not found in vDisk sheet for shared disk detection"
        )
        return create_empty_result()

    # Filter out rows with null or empty paths
    vdisk_data = vdisk_data[vdisk_data["Path"].notna() & (vdisk_data["Path"] != "")]

    # Group by path to find shared disks (same path used by multiple VMs)
    path_groups = vdisk_data.groupby("Path")

    shared_disk_groups = []
    detected_paths = set()  # Track paths already detected to avoid duplicates

    # First, detect VMs sharing the same disk path
    for path, group in path_groups:
        unique_vms = group["VM"].unique()
        if len(unique_vms) > 1:  # Multiple VMs sharing the same path
            # Create a summary for this shared disk group
            shared_disk_info = {
                "Path": path,
                "VM Count": len(unique_vms),
                "VMs": ", ".join(sorted(unique_vms)),
            }

            # Add Path to detected set
            detected_paths.add(path)

            # Add optional information if available
            if "Sharing mode" in group.columns:
                sharing_modes = group["Sharing mode"].dropna()
                if len(sharing_modes) > 0:
                    # Take the first non-empty value as example
                    shared_disk_info["Sharing mode"] = str(sharing_modes.iloc[0])
                else:
                    shared_disk_info["Sharing mode"] = ""

            if "Write Through" in group.columns:
                write_through_values = group["Write Through"].dropna()
                if len(write_through_values) > 0:
                    # Take the first non-empty value as example
                    shared_disk_info["Write Through"] = str(
                        write_through_values.iloc[0]
                    )
                else:
                    shared_disk_info["Write Through"] = ""

            if "Shared Bus" in group.columns:
                shared_bus_values = group["Shared Bus"].dropna()
                if len(shared_bus_values) > 0:
                    # Take the first non-empty value as example
                    shared_disk_info["Shared Bus"] = str(shared_bus_values.iloc[0])
                else:
                    shared_disk_info["Shared Bus"] = ""

            shared_disk_groups.append(shared_disk_info)

    # Second, detect Paths with Shared Bus != "noSharing" that weren't already detected
    if "Shared Bus" in vdisk_data.columns:
        # Filter for VMs with sharing bus configurations that are not "noSharing"
        sharing_bus_mask = (
            vdisk_data["Shared Bus"].notna()
            & (vdisk_data["Shared Bus"] != "")
            & (vdisk_data["Shared Bus"].astype(str).str.lower() != "nosharing")
        )

        sharing_bus_vms = vdisk_data[sharing_bus_mask]

        for _, row in sharing_bus_vms.iterrows():
            path_name = row["Path"]
            if path_name not in detected_paths: # Avoid duplicates
                shared_disk_info = {"Path": path_name, "VM Count": 1, "VMs": row["VM"]}

                # Add the specific sharing information in the correct order
                if "Sharing mode" in row.index:
                    shared_disk_info["Sharing mode"] = (
                        str(row["Sharing mode"])
                        if pd.notna(row["Sharing mode"])
                        else ""
                    )

                if "Write Through" in row.index:
                    shared_disk_info["Write Through"] = (
                        str(row["Write Through"])
                        if pd.notna(row["Write Through"])
                        else ""
                    )

                shared_disk_info["Shared Bus"] = str(row["Shared Bus"])
                shared_disk_groups.append(shared_disk_info)
                detected_paths.add(path)
    logger.info(
        f"detect_shared_disks: Found {len(shared_disk_groups)} shared disk configurations"
    )
    return {"count": len(shared_disk_groups), "data": shared_disk_groups}


@risk_info(
    level=RiskLevel.EMERGENCY,
    description="Critical security risk: Clear text passwords detected in VM annotations or snapshot descriptions.",
    alert_message="""<strong>CRITICAL SECURITY ALERT:</strong> Clear text passwords have been detected in your VMware environment!
                    This poses a significant security risk. Passwords may have been found in:
                    <ul>
                        <li>VM Annotations (vInfo sheet)</li>
                        <li>Snapshot Descriptions (vSnapshot sheet)</li>
                    </ul>
                    <strong>IMPORTANT:</strong> This RVTools file has NOT been stored on our server and was analyzed in memory only.
                    However, you should immediately:
                    <ul>
                        <li>Remove all clear text passwords from VM annotations and snapshot descriptions</li>
                        <li>Rotate any exposed passwords</li>
                        <li>Implement secure password management practices</li>
                        <li>Review access to your vCenter environment</li>
                    </ul>""",
)
def detect_clear_text_passwords(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """
    Detect clear text passwords in VM annotations and snapshot descriptions.

    This is a critical security risk detection that scans for any form of "password"
    in VM annotations (vInfo sheet) and snapshot descriptions (vSnapshot sheet).

    Args:
        excel_data: Parsed Excel file from RVTools

    Returns:
        Dictionary with count and data about VMs/snapshots containing passwords
    """
    password_exposures = []

    # Check vInfo sheet for passwords in Annotation column
    vinfo_data = safe_sheet_access(excel_data, "vInfo")
    if not vinfo_data.empty and "Annotation" in vinfo_data.columns:
        # Filter rows where Annotation contains password-like terms
        vinfo_with_annotations = vinfo_data[
            vinfo_data["Annotation"].notna() & (vinfo_data["Annotation"] != "")
        ]

        for _, row in vinfo_with_annotations.iterrows():
            annotation = str(row["Annotation"])
            if contains_password_reference(annotation):
                password_exposures.append(
                    {
                        "Source": "VM Annotation",
                        "VM Name": row.get("VM", "Unknown"),
                        "Snapshot Name": "",  # N/A for VM annotations
                        "Location Type": "vInfo Sheet",
                        "Risk Level": "emergency",
                        "Details": f"Password reference found in VM annotations.",
                    }
                )

    # Check vSnapshot sheet for passwords in Description column
    vsnapshot_data = safe_sheet_access(excel_data, "vSnapshot")
    if not vsnapshot_data.empty and "Description" in vsnapshot_data.columns:
        # Filter rows where Description contains password-like terms
        vsnapshot_with_descriptions = vsnapshot_data[
            vsnapshot_data["Description"].notna()
            & (vsnapshot_data["Description"] != "")
        ]

        for _, row in vsnapshot_with_descriptions.iterrows():
            description = str(row["Description"])
            if contains_password_reference(description):
                password_exposures.append(
                    {
                        "Source": "Snapshot Description",
                        "VM Name": row.get("VM", "Unknown"),
                        "Snapshot Name": row.get("Snapshot", "Unknown"),
                        "Location Type": "vSnapshot Sheet",
                        "Risk Level": "emergency",
                        "Details": f"Password reference found in snapshot description.",
                    }
                )

    return {"count": len(password_exposures), "data": password_exposures}


@risk_info(
    level=RiskLevel.WARNING,
    description="VMs connected to ESXi VMkernel networks instead of standard VM networks.",
    alert_message="""VMkernel networks are designed for ESXi management traffic (vMotion, storage, management, etc.)
    and should not be used for virtual machine network connectivity.<br><br>VMkernel networks cannot be extended with
    HCX.
    <br><br>It's recommended to move these VMs to dedicated VM networks before migration.""",
)
def detect_vmkernel_network_vms(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """
    Detect VMs connected to ESXi VMkernel networks.

    VMkernel networks are intended for ESXi host management traffic like vMotion,
    storage, and management. VMs should not be connected to these networks as it
    can cause network conflicts and operational issues.

    Args:
        excel_data: Parsed Excel file from RVTools

    Returns:
        Dictionary with count and data about VMs on VMkernel networks
    """
    vmkernel_vms = []

    # First, get all VMkernel networks from vSC_VMK sheet
    vmk_data = safe_sheet_access(excel_data, "vSC_VMK")
    vmkernel_networks = set()

    if not vmk_data.empty and "Port Group" in vmk_data.columns:
        # Get all unique network names from VMkernel interfaces
        vmkernel_networks = set(vmk_data["Port Group"].dropna().unique())
        logger.debug(
            f"Found {len(vmkernel_networks)} VMkernel networks: {vmkernel_networks}"
        )

    if not vmkernel_networks:
        logger.info("detect_vmkernel_network_vms: No VMkernel networks found")
        return {"count": 0, "data": []}

    # Now check vNetwork sheet for VMs connected to these networks
    vnetwork_data = safe_sheet_access(excel_data, "vNetwork")

    if vnetwork_data.empty or "Network" not in vnetwork_data.columns:
        logger.warning(
            "detect_vmkernel_network_vms: No vNetwork sheet or Network column found"
        )
        return {"count": 0, "data": []}

    # Find VMs connected to VMkernel networks
    for _, row in vnetwork_data.iterrows():
        network_name = row.get("Network", "")
        vm_name = row.get("VM", "Unknown")

        if network_name in vmkernel_networks:
            vmkernel_vms.append(
                {
                    "VM": vm_name,
                    "Powerstate": row.get("Powerstate", ""),
                    "Network": network_name,
                    "Switch": row.get("Switch", ""),
                    "Connected": row.get("Connected", ""),
                    "IPv4 Address": row.get("IPv4 Address", ""),
                }
            )

    logger.info(
        f"detect_vmkernel_network_vms: Found {len(vmkernel_vms)} VMs connected to VMkernel networks"
    )
    return {"count": len(vmkernel_vms), "data": vmkernel_vms}


@risk_info(
    level=RiskLevel.WARNING,
    description="VMs with Fault Tolerance enabled",
    alert_message="""Fault Tolerance (FT) is a feature that provides continuous availability for VMs by creating a live shadow instance.
    However, Virtual machines cannot be migrated while they are Fault Tolerance enabled.
    <br><br>To migrate FT-enabled VMs: <ol>
        <li><strong>Temporarily</strong> turn off Fault Tolerance,</li>
        <li>Perform migration,</li>
        <li>When this operation is complete, turn Fault Tolerance back on</li>
    </ol>""",
)
def detect_fault_tolerance_vms(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """
    Detect VMs with Fault Tolerance enabled.

    Fault Tolerance (FT) is a feature that provides continuous availability for VMs by creating a live shadow instance.
    However, Virtual machines cannot be migrated while they are Fault Tolerance enabled.

    Args:
        excel_data: Parsed Excel file from RVTools

    Returns:
        Dictionary with count and data about VMs with Fault Tolerance enabled
    """
    ft_vms = []

    # Check vInfo sheet for VMs with FT enabled
    vm_data = safe_sheet_access(excel_data, "vInfo")

    if vm_data.empty or "FT State" not in vm_data.columns:
        logger.warning(
            "detect_fault_tolerance_vms: No vInfo sheet or FT State column found"
        )
        return {"count": 0, "data": []}

    # Find VMs with FT enabled
    for _, row in vm_data.iterrows():
        vm_name = row.get("VM", "Unknown")
        ft_enabled = row.get("FT State", "notConfigured")

        if ft_enabled != "notConfigured":
            ft_vms.append(
                {
                    "VM": vm_name,
                    "Powerstate": row.get("Powerstate", ""),
                    "FT State": row.get("FT State", ""),
                    "FT Role": row.get("FT Role", ""),
                }
            )

    logger.info(
        f"detect_fault_tolerance_vms: Found {len(ft_vms)} VMs with Fault Tolerance enabled"
    )
    return {"count": len(ft_vms), "data": ft_vms}


########################################################################################################################
#                                                                                                                      #
#                                         End of Risk Detection Functions                                              #
#                                                                                                                      #
########################################################################################################################


def get_risk_functions_list() -> List:
    """
    Get the centralized list of all risk detection functions.

    Returns:
        List of risk detection functions
    """
    return [
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
        detect_shared_disks,
        detect_clear_text_passwords,
        detect_vmkernel_network_vms,
        detect_fault_tolerance_vms,
    ]


def get_total_risk_functions_count() -> int:
    """
    Get the total number of available risk detection functions.

    Returns:
        Integer count of risk detection functions
    """
    return len(get_risk_functions_list())


def get_available_risks() -> Dict[str, Any]:
    """
    Get information about all available risk detection functions.

    Returns:
        Dictionary containing metadata about each risk detection function
    """
    risk_functions = get_risk_functions_list()

    available_risks = {}
    risk_levels_count = {
        "info": 0,
        "warning": 0,
        "danger": 0,
        "blocking": 0,
        "emergency": 0,
    }

    for func in risk_functions:
        func_name = func.__name__
        risk_metadata = getattr(func, "_risk_info", {})

        # Clean up the function name for display
        # (now using helper function)

        available_risks[func_name] = {
            "name": func_name,
            "display_name": clean_function_name_for_display(func_name),
            "risk_level": risk_metadata.get("level", "info"),
            "description": risk_metadata.get("description", "No description available"),
            "alert_message": risk_metadata.get("alert_message", None),
            "category": get_risk_category(func_name),
        }

        # Count risk levels
        risk_level = risk_metadata.get("level", "info")
        if risk_level in risk_levels_count:
            risk_levels_count[risk_level] += 1

    return {
        "total_available_risks": len(available_risks),
        "risk_levels_distribution": risk_levels_count,
        "risks": available_risks,
    }


def gather_all_risks(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """
    Gather all risk detection results.

    Args:
        excel_data: Parsed Excel file from RVTools

    Returns:
        Dictionary containing all risk detection results
    """
    risk_functions = get_risk_functions_list()

    results = {}
    summary = {
        "total_risks": 0,
        "risk_levels": {
            "info": 0,
            "warning": 0,
            "danger": 0,
            "blocking": 0,
            "emergency": 0,
        },
    }

    for func in risk_functions:
        try:
            result = func(excel_data)
            function_name = result.get("function_name", func.__name__)
            risk_level_val = result.get("risk_level", "info")

            results[function_name] = result

            if result["count"] > 0:
                summary["total_risks"] += result["count"]
                summary["risk_levels"][risk_level_val] += result["count"]

        except Exception as e:
            results[func.__name__] = {
                "count": 0,
                "data": [],
                "error": str(e),
                "risk_level": "info",
                "function_name": func.__name__,
            }

    return {"summary": summary, "risks": results}
