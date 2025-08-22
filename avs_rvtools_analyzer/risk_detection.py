"""
Risk detection module for RVTools analysis.
Contains individual risk detection functions and a gatherer function.
"""
import re
from typing import Dict, List, Any
import pandas as pd

# Import from our new modules
from .models import RiskLevel, ESXVersionThresholds, PowerStates, GuestStates, NetworkConstants, StorageConstants
from .config import MigrationMethodsConfig
from .helpers import (
    load_sku_data, safe_sheet_access, create_empty_result,
    filter_dataframe_by_condition, get_risk_category, convert_mib_to_tb,
    clean_function_name_for_display
)
from .decorators import risk_info

import logging
logger = logging.getLogger(__name__)

########################################################################################################################
#                                                                                                                      #
#                                               Risk Detection Functions                                               #
#                                                                                                                      #
########################################################################################################################

@risk_info(
    level=RiskLevel.INFO,
    description='This shows the distribution of ESX versions found in the uploaded file.',
    alert_message="""Having multiple ESX versions in the environment can lead to compatibility issues and
    increased complexity during migration.<br><br>It's recommended to standardize on a single ESX version
    if possible."""
)
def detect_esx_versions(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect ESX versions and their risk levels."""
    vhost_data = safe_sheet_access(excel_data, 'vHost')
    if vhost_data is None:
        return create_empty_result()

    version_counts = vhost_data['ESX Version'].value_counts().to_dict()
    version_risks = {}
    card_risk = "info"

    for version_str in version_counts.keys():
        version_match = re.search(r'ESXi (\d+\.\d+\.\d+)', version_str)
        if version_match:
            version_num = version_match.group(1)
            if version_num < ESXVersionThresholds.ERROR_THRESHOLD:
                version_risks[version_str] = "blocking"
                card_risk = "danger"
            elif version_num < ESXVersionThresholds.WARNING_THRESHOLD:
                version_risks[version_str] = "warning"
                if card_risk != "danger":
                    card_risk = "warning"
            else:
                version_risks[version_str] = "info"

    return {
        'count': len(version_counts),
        'data': version_counts,
        'details': {
            'version_risks': version_risks,
            'card_risk': card_risk,
            'warning_threshold': ESXVersionThresholds.WARNING_THRESHOLD,
            'error_threshold': ESXVersionThresholds.ERROR_THRESHOLD
        }
    }


@risk_info(
    level=RiskLevel.BLOCKING,
    description='vUSB devices are USB devices that are connected to a virtual machine (VM) in a VMware environment.',
    alert_message="""Having vUSB devices connected to VMs can pose a risk during migration, as they cannot be
    transferred to an Azure Managed environment.<br><br>It's recommended to review the list of vUSB devices
    and ensure that they are necessary for the VM's operation before proceeding with the migration."""
)
def detect_vusb_devices(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect USB devices attached to VMs."""
    vusb_data = safe_sheet_access(excel_data, 'vUSB')
    if vusb_data is None:
        return create_empty_result()

    devices = vusb_data[['VM', 'Powerstate', 'Device Type', 'Connected']].to_dict(orient='records')

    return {
        'count': len(devices),
        'data': devices
    }


@risk_info(
    level='blocking',
    description='Risky disks are virtual disks that are configured in a way that may pose a risk during migration.',
    alert_message="""This can include disks that are set to "Independent" mode or configured with Raw Device
    Mapping capability.<br><br>It's recommended to review the list of risky disks and consider reconfiguring
    them before proceeding with the migration."""
)
def detect_risky_disks(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect disks with migration risks (raw or independent persistent)."""
    if 'vDisk' not in excel_data.sheet_names:
        return {'count': 0, 'data': []}

    vdisk_data = excel_data.parse('vDisk')

    # Filter using string comparison directly - no copy needed
    mask = (
        (vdisk_data['Raw'].astype(str).str.lower() == 'true') |
        (vdisk_data['Disk Mode'] == 'independent_persistent')
    )

    # Select only columns that exist in the data
    columns_to_return = ['VM', 'Powerstate', 'Disk', 'Capacity MiB', 'Raw', 'Disk Mode']
    available_columns = [col for col in columns_to_return if col in vdisk_data.columns]

    risky_disks = vdisk_data[mask][available_columns].to_dict(orient='records')

    return {
        'count': len(risky_disks),
        'data': risky_disks
    }


@risk_info(
    level='blocking',
    description='This shows the distribution of VMs and ports using dvSwitches or standard vSwitches.',
    alert_message="""HCX network extension functionality requires the use of distributed switches (dvSwitches).
    In case of standard vSwitches, the migration process will be more complex."""
)
def detect_non_dvs_switches(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect non-dvSwitch network interfaces."""
    if 'dvSwitch' not in excel_data.sheet_names or 'vNetwork' not in excel_data.sheet_names:
        return {'count': 0, 'data': {}}

    dvswitch_data = excel_data.parse('dvSwitch')
    vnetwork_data = excel_data.parse('vNetwork')

    dvswitch_list = dvswitch_data['Switch'].dropna().unique()
    vnetwork_data['Switch Type'] = vnetwork_data['Switch'].apply(
        lambda x: 'standard vSwitch' if x not in dvswitch_list else x
    )

    switch_statistics = vnetwork_data['Switch Type'].value_counts().to_dict()
    non_dvs_count = len(vnetwork_data[vnetwork_data['Switch Type'] == 'standard vSwitch'])

    return {
        'count': non_dvs_count,
        'data': switch_statistics
    }


@risk_info(
    level='warning',
    description='vSnapshots are virtual machine snapshots that capture the state of a VM at a specific point in time.',
    alert_message="""Having multiple vSnapshots can pose a risk during migration, as they can increase complexity
    and may lead to data loss if not handled properly.<br><br>It's recommended to review and consider
    consolidating or deleting unnecessary snapshots."""
)
def detect_snapshots(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect VM snapshots."""
    if 'vSnapshot' not in excel_data.sheet_names:
        return {'count': 0, 'data': []}

    vsnapshot_sheet = excel_data.parse('vSnapshot')
    snapshots = vsnapshot_sheet[
        ['VM', 'Powerstate', 'Name', 'Date / time', 'Size MiB (vmsn)', 'Description']
    ].to_dict(orient='records')

    return {
        'count': len(snapshots),
        'data': snapshots
    }


@risk_info(
    level='warning',
    description='Suspended VMs are virtual machines that are not currently running but have their state saved.',
    alert_message="""Suspended VMs can pose a risk during migration, as it will be necessary to power them on
    or off before proceeding.<br><br>It's recommended to review the list of suspended VMs and consider
    powering them on or off."""
)
def detect_suspended_vms(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect suspended VMs."""
    if 'vInfo' not in excel_data.sheet_names:
        return {'count': 0, 'data': []}

    vinfo_data = excel_data.parse('vInfo')
    suspended_vms = vinfo_data[vinfo_data['Powerstate'] == 'Suspended'][['VM']].to_dict(orient='records')

    return {
        'count': len(suspended_vms),
        'data': suspended_vms
    }


@risk_info(
    level='info',
    description='Oracle VMs are virtual machines specifically configured to run Oracle software.',
    alert_message="""Oracle VMs hosting in Azure VMware Solution is supported but may require costly licensing.
    <br><br>It's recommended to review the list of Oracle VMs and envision alternative hosting options to
    avoid unnecessary costs."""
)
def detect_oracle_vms(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect Oracle VMs."""
    if 'vInfo' not in excel_data.sheet_names:
        return {'count': 0, 'data': []}

    vinfo_data = excel_data.parse('vInfo')
    oracle_vms = vinfo_data[
        vinfo_data['OS according to the VMware Tools'].str.contains('Oracle', na=False)
    ][['VM', 'OS according to the VMware Tools', 'Powerstate', 'CPUs', 'Memory', 'Provisioned MiB', 'In Use MiB']].to_dict(orient='records')

    return {
        'count': len(oracle_vms),
        'data': oracle_vms
    }


@risk_info(
    level='warning',
    description='dvPort issues are related to the configuration of distributed virtual ports in a VMware environment.',
    alert_message="""Multiple dvPort issues can pose a risk during migration:
    <ul>
        <li>VLAN ID 0 or empty: they cannot be extended via HCX</li>
        <li>Allow Promiscuous mode enabled</li>
        <li>Mac Changes enabled</li>
        <li>Forged Transmits enabled</li>
    </ul>"""
)
def detect_dvport_issues(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect dvPort configuration issues."""
    if 'dvPort' not in excel_data.sheet_names:
        return {'count': 0, 'data': []}

    dvport_data = excel_data.parse('dvPort')

    # Store original VLAN nulls before filling
    vlan_is_null = dvport_data['VLAN'].isnull()
    dvport_data['VLAN'] = dvport_data['VLAN'].fillna(0).astype(int)

    # Filter using string comparison directly - no copy needed
    mask = (
        vlan_is_null |
        (dvport_data['Allow Promiscuous'].astype(str).str.lower() == 'true') |
        (dvport_data['Mac Changes'].astype(str).str.lower() == 'true') |
        (dvport_data['Forged Transmits'].astype(str).str.lower() == 'true')
    )

    # Return original values directly
    columns_to_return = ['Port', 'Switch', 'Object ID', 'VLAN', 'Allow Promiscuous', 'Mac Changes', 'Forged Transmits']
    available_columns = [col for col in columns_to_return if col in dvport_data.columns]

    issues = dvport_data[mask][available_columns].to_dict(orient='records')

    return {
        'count': len(issues),
        'data': issues
    }


@risk_info(
    level='warning',
    description='Hosts with CPU models that are not Intel may pose compatibility issues during migration.',
    alert_message="""As Azure VMware Solution is Intel based service, a cold migration strategy will be
    required for the workload in these hosts."""
)
def detect_non_intel_hosts(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect non-Intel CPU hosts."""
    if 'vHost' not in excel_data.sheet_names:
        return {'count': 0, 'data': []}

    vhost_data = excel_data.parse('vHost')
    non_intel_hosts = vhost_data[
        ~vhost_data['CPU Model'].str.contains('Intel', na=False)
    ][['Host', 'Datacenter', 'Cluster', 'CPU Model', '# VMs']].to_dict(orient='records')

    return {
        'count': len(non_intel_hosts),
        'data': non_intel_hosts
    }


@risk_info(
    level='warning',
    description='VMs that are powered on but their VMware Tools are not running.',
    alert_message="""VMs without VMware Tools running may not be able to use all the features of VMware HCX
    during migration.<br><br>It's recommended to ensure that VMware Tools are installed, running and
    up-to-date on all powered-on VMs."""
)
def detect_vmtools_not_running(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect VMs with VMware Tools not running."""
    if 'vInfo' not in excel_data.sheet_names:
        return {'count': 0, 'data': []}

    vinfo_data = excel_data.parse('vInfo')
    vmtools_issues = vinfo_data[
        (vinfo_data['Powerstate'] == 'poweredOn') &
        (vinfo_data['Guest state'] == 'notRunning')
    ][['VM', 'Powerstate', 'Guest state', 'OS according to the configuration file']].to_dict(orient='records')

    return {
        'count': len(vmtools_issues),
        'data': vmtools_issues
    }


@risk_info(
    level='warning',
    description='VMs have CD-ROM devices that are connected.',
    alert_message="""CD-ROM devices connected to VMs can cause issues during migration. It's recommended to
    review and disconnect unnecessary CD-ROM devices before proceeding."""
)
def detect_cdrom_issues(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect mounted CD/DVD drives."""
    if 'vCD' not in excel_data.sheet_names:
        return {'count': 0, 'data': []}

    vcd_data = excel_data.parse('vCD')

    # Filter using string comparison directly - no copy needed
    mask = vcd_data['Connected'].astype(str).str.lower() == 'true'

    # Select only columns that exist in the data
    columns_to_return = ['VM', 'Powerstate', 'Connected', 'Starts Connected', 'Device Type']
    available_columns = [col for col in columns_to_return if col in vcd_data.columns]

    cdrom_issues = vcd_data[mask][available_columns].to_dict(orient='records')

    return {
        'count': len(cdrom_issues),
        'data': cdrom_issues
    }


@risk_info(
    level=RiskLevel.WARNING,
    description='VMs have provisioned storage exceeding 10TB.',
    alert_message="""Large provisioned storage can lead to increased migration times and potential compatibility
    issues. It's recommended to review these VMs and optimize storage usage if possible."""
)
def detect_large_provisioned_vms(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect VMs with large provisioned disks (>10TB)."""
    vm_data = safe_sheet_access(excel_data, 'vInfo')
    if vm_data is None:
        return create_empty_result()

    vm_data['Provisioned MiB'] = pd.to_numeric(vm_data['Provisioned MiB'], errors='coerce')
    vm_data['In Use MiB'] = pd.to_numeric(vm_data['In Use MiB'], errors='coerce')
    vm_data['Provisioned TB'] = (vm_data['Provisioned MiB'] * 1.048576) / (1024 * 1024)

    large_vms = vm_data[vm_data['Provisioned TB'] > 10][
        ['VM', 'Provisioned MiB', 'In Use MiB', 'CPUs', 'Memory']
    ].to_dict(orient='records')

    return {
        'count': len(large_vms),
        'data': large_vms
    }


@risk_info(
    level=RiskLevel.BLOCKING,
    description='VMs have a vCPU count higher than the core count of available SKUs.',
    alert_message="""The VMs with more vCPUs configured than the available SKUs core count will not be able
    to run on the target hosts."""
)
def detect_high_vcpu_vms(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect VMs with high vCPU count."""
    vm_data = safe_sheet_access(excel_data, 'vInfo')
    if vm_data is None:
        return create_empty_result()

    # Load SKU data using cached function
    try:
        sku_data = load_sku_data()
    except FileNotFoundError:
        return {'count': 0, 'data': [], 'error': 'SKU data file not found'}

    vm_data['CPUs'] = pd.to_numeric(vm_data['CPUs'], errors='coerce')

    sku_cores = {sku['name']: sku['cores'] for sku in sku_data}
    min_cores = min(sku_cores.values())

    high_vcpu_vms = []
    for _, vm in vm_data.iterrows():
        if vm['CPUs'] > min_cores:
            vm_data_entry = {
                'VM': vm['VM'],
                'vCPU Count': vm['CPUs'],
                **{sku: '✘' if vm['CPUs'] > cores else '✓' for sku, cores in sku_cores.items()}
            }
            high_vcpu_vms.append(vm_data_entry)

    return {
        'count': len(high_vcpu_vms),
        'data': high_vcpu_vms
    }


@risk_info(
    level=RiskLevel.BLOCKING,
    description='VMs have memory usage exceeding the capabilities of available SKUs.',
    alert_message="""The VMs with more memory configured than the available capacity per node will not be able
    to run on the target hosts.<br><br>For performance best practices, it is also recommended not to exceed
    half of the available memory per node on a single VM."""
)
def detect_high_memory_vms(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect VMs with high memory allocation."""
    vm_data = safe_sheet_access(excel_data, 'vInfo')
    if vm_data is None:
        return create_empty_result()

    # Load SKU data using cached function
    try:
        sku_data = load_sku_data()
    except FileNotFoundError:
        return {'count': 0, 'data': [], 'error': 'SKU data file not found'}

    vm_data['Memory'] = pd.to_numeric(vm_data['Memory'], errors='coerce')

    min_memory = min(sku['ram'] * 1024 for sku in sku_data)

    high_memory_vms = []
    for _, vm in vm_data.iterrows():
        if vm['Memory'] > min_memory:
            vm_data_entry = {
                'VM': vm['VM'],
                'Memory (GB)': round(vm['Memory'] / 1024, 2),
                **{
                    sku['name']: '✘' if vm['Memory'] > sku['ram'] * 1024 else '✓'
                    for sku in sku_data
                }
            }
            high_memory_vms.append(vm_data_entry)

    return {
        'count': len(high_memory_vms),
        'data': high_memory_vms
    }


@risk_info(
    level=RiskLevel.BLOCKING,
    description="""Virtual machines with legacy hardware version have limited HCX migration capabilities to Azure VMware Solution.
    Hardware version determines the virtual machine's feature set and migration compatibility.""",
    alert_message="""You should consider upgrading the hardware version of these VMs before migration.
    This requires powering off the VM temporarily."""
)
def detect_hw_version_compatibility(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """Detect VMs with incompatible hardware versions for Azure VMware Solution migration."""
    vm_data = safe_sheet_access(excel_data, 'vInfo')
    if vm_data is None:
        return create_empty_result()

    # Check if HW version column exists
    if 'HW version' not in vm_data.columns:
        logger.warning("HW version column not found in vInfo sheet")
        return create_empty_result()

    # Filter VMs with hardware version issues
    incompatible_vms = []

    for _, vm in vm_data.iterrows():
        hw_version = vm.get('HW version')
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
                for method_name, min_hw_version in migration_config.migration_methods.items():
                    if hw_version_num < min_hw_version:
                        unsupported_methods.append(method_name)

            # Only include VMs with migration limitations
            if unsupported_methods:
                vm_info = {
                    'VM': vm.get('VM', 'Unknown'),
                    'HW Version': hw_version,
                    'Powerstate': vm.get('Powerstate', 'Unknown'),
                    'Unsupported migration methods': ', '.join(unsupported_methods)
                }
                incompatible_vms.append(vm_info)

        except (ValueError, TypeError) as e:
            logger.error(f"Could not parse hardware version '{hw_version}' for VM {vm.get('VM', 'Unknown')}: {e}")
            continue

    logger.info(f"Found {len(incompatible_vms)} VMs with hardware version compatibility issues")

    return {
        'count': len(incompatible_vms),
        'data': incompatible_vms
    }


########################################################################################################################
#                                                                                                                      #
#                                         End of Risk Detection Functions                                              #
#                                                                                                                      #
########################################################################################################################

def get_available_risks() -> Dict[str, Any]:
    """
    Get information about all available risk detection functions.

    Returns:
        Dictionary containing metadata about each risk detection function
    """
    risk_functions = [
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
    ]

    available_risks = {}
    risk_levels_count = {'info': 0, 'warning': 0, 'danger': 0, 'blocking': 0}

    for func in risk_functions:
        func_name = func.__name__
        risk_metadata = getattr(func, '_risk_info', {})

        # Clean up the function name for display
        # (now using helper function)

        available_risks[func_name] = {
            'name': func_name,
            'display_name': clean_function_name_for_display(func_name),
            'risk_level': risk_metadata.get('level', 'info'),
            'description': risk_metadata.get('description', 'No description available'),
            'alert_message': risk_metadata.get('alert_message', None),
            'category': get_risk_category(func_name)
        }

        # Count risk levels
        risk_level = risk_metadata.get('level', 'info')
        if risk_level in risk_levels_count:
            risk_levels_count[risk_level] += 1

    return {
        'total_available_risks': len(available_risks),
        'risk_levels_distribution': risk_levels_count,
        'risks': available_risks
    }

def gather_all_risks(excel_data: pd.ExcelFile) -> Dict[str, Any]:
    """
    Gather all risk detection results.

    Args:
        excel_data: Parsed Excel file from RVTools

    Returns:
        Dictionary containing all risk detection results
    """
    risk_functions = [
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
    ]

    results = {}
    summary = {'total_risks': 0, 'risk_levels': {'info': 0, 'warning': 0, 'danger': 0, 'blocking': 0}}

    for func in risk_functions:
        try:
            result = func(excel_data)
            function_name = result.get('function_name', func.__name__)
            risk_level_val = result.get('risk_level', 'info')

            results[function_name] = result

            if result['count'] > 0:
                summary['total_risks'] += result['count']
                summary['risk_levels'][risk_level_val] += result['count']

        except Exception as e:
            results[func.__name__] = {
                'count': 0,
                'data': [],
                'error': str(e),
                'risk_level': 'info',
                'function_name': func.__name__
            }

    return {
        'summary': summary,
        'risks': results
    }
