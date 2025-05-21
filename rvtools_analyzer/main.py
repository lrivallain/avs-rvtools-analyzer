from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
import pandas as pd
from flask import jsonify
import xlrd

from rvtools_analyzer import __version__ as calver_version

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}
WARNING_ESXI_VERSION_THRESHOLD = '7.0.0' # Version lower than this is considered a warning
ERROR_ESXI_VERSION_THRESHOLD = '6.5.0' # Version lower than this is considered an error

def convert_mib_to_human_readable(value):
    """
    Convert MiB to human-readable format (MB, GB, TB).
    :param value: Value in MiB
    :return: Human-readable string
    """
    try:
        value = float(value)
        # 1 MiB = 1.048576 MB
        value_in_mb = value * 1.048576

        if value_in_mb >= 1024 * 1024:
            return f"{value_in_mb / (1024 * 1024):.2f} TB"
        elif value_in_mb >= 1024:
            return f"{value_in_mb / 1024:.2f} GB"
        else:
            return f"{value_in_mb:.2f} MB"
    except (ValueError, TypeError):
        return "Invalid input"

# Register the function for Jinja2 templating
app.jinja_env.filters['convert_mib_to_human_readable'] = convert_mib_to_human_readable

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/explore', methods=['POST', 'GET'])
def explore_file():
    if request.method != 'POST':
        return render_template('error.html', message="Invalid request method. Please use the correct form to submit your file.")

    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        # Parse the uploaded file directly without saving
        excel_data = pd.ExcelFile(file)
        sheets = {}
        for sheet_name in excel_data.sheet_names:
            sheets[sheet_name] = excel_data.parse(sheet_name).to_dict(orient='records')

        return render_template('explore.html', sheets=sheets, filename=file.filename)

    return redirect(url_for('index'))

@app.route('/analyze', methods=['POST', 'GET'])
def analyze_migration_risks():
    if request.method != 'POST':
        return render_template('error.html', message="Invalid request method. Please use the correct form to submit your file.")

    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        try:
            excel_data = pd.ExcelFile(file)
        except xlrd.biffh.XLRDError:
            return render_template('error.html', message="The uploaded file is protected. Please unprotect the file and try again.")

        esx_version_counts = {}
        esx_version_risks = {}  # For storing version risk levels
        esx_version_card_risk = "info"  # Default risk level
        vusb_devices = []
        risky_disks = []
        switch_statistics = {}
        vsnapshot_data = []
        suspended_vms = []
        oracle_vms = []
        dvport_issues = []
        non_intel_hosts = []
        vmtools_not_running = []
        cdrom_issues = []
        large_provisioned_vms = []
        high_vcpu_vms = []
        high_memory_vms = []
        counts = {
            'esx_version_count': 0,
            'vusb_count': 0,
            'risky_disks_count': 0,
            'vsnapshot_count': 0,
            'non_dvs_switch_count': 0,
            'suspended_vms_count': 0,
            'oracle_vms_count': 0,
            'dvport_issues_count': 0,
            'non_intel_hosts_count': 0,
            'vmtools_not_running_count': 0,
            'cdrom_issues_count': 0,
            'large_provisioned_vms_count': 0
        }

        if 'vHost' in excel_data.sheet_names:
            vhost_data = excel_data.parse('vHost')
            esx_version_counts = vhost_data['ESX Version'].value_counts().to_dict()
            counts['esx_version_count'] = len(esx_version_counts)

            # Process and evaluate ESX versions for risk levels
            import re
            for version_str in esx_version_counts.keys():
                # Extract version number from string like "VMware ESXi 6.5.0 build-20502893"
                version_match = re.search(r'ESXi (\d+\.\d+\.\d+)', version_str)
                if version_match:
                    version_num = version_match.group(1)
                    # Check if version is lower than thresholds and assign risk
                    if version_num < ERROR_ESXI_VERSION_THRESHOLD:
                        esx_version_risks[version_str] = "blocking"
                        esx_version_card_risk = "danger"  # Set card risk to highest level
                    elif version_num < WARNING_ESXI_VERSION_THRESHOLD:
                        esx_version_risks[version_str] = "warning"
                        if esx_version_card_risk != "danger":
                            esx_version_card_risk = "warning"
                    else:
                        esx_version_risks[version_str] = "info"

            non_intel_hosts = vhost_data[~vhost_data['CPU Model'].str.contains('Intel', na=False)][['Host', 'Datacenter', 'Cluster', 'CPU Model', '# VMs']].to_dict(orient='records')
            counts['non_intel_hosts_count'] = len(non_intel_hosts)

        if 'vUSB' in excel_data.sheet_names:
            vusb_data = excel_data.parse('vUSB')
            vusb_devices = vusb_data[['VM', 'Powerstate', 'Device Type', 'Connected']].to_dict(orient='records')
            counts['vusb_count'] = len(vusb_devices)

        if 'vDisk' in excel_data.sheet_names:
            vdisk_data = excel_data.parse('vDisk')
            risky_disks = vdisk_data[(vdisk_data['Raw'] == True) | (vdisk_data['Disk Mode'] == 'independent_persistent')][['VM', 'Powerstate', 'Disk', 'Capacity MiB', 'Raw', 'Disk Mode']].to_dict(orient='records')
            counts['risky_disks_count'] = len(risky_disks)

        if 'dvSwitch' in excel_data.sheet_names and 'vNetwork' in excel_data.sheet_names:
            dvswitch_data = excel_data.parse('dvSwitch')
            vnetwork_data = excel_data.parse('vNetwork')

            dvswitch_list = dvswitch_data['Switch'].dropna().unique()
            vnetwork_data['Switch Type'] = vnetwork_data['Switch'].apply(lambda x: 'standard vSwitch' if x not in dvswitch_list else x)
            switch_statistics = vnetwork_data['Switch Type'].value_counts().to_dict()
            counts['non_dvs_switch_count'] = len(vnetwork_data[vnetwork_data['Switch Type'] == 'standard vSwitch'])

        if 'vSnapshot' in excel_data.sheet_names:
            vsnapshot_sheet = excel_data.parse('vSnapshot')
            vsnapshot_data = vsnapshot_sheet[['VM', 'Powerstate', 'Name', 'Date / time', 'Size MiB (vmsn)', 'Description']].to_dict(orient='records')
            counts['vsnapshot_count'] = len(vsnapshot_data)

        if 'vInfo' in excel_data.sheet_names:
            vinfo_data = excel_data.parse('vInfo')

            suspended_vms = vinfo_data[vinfo_data['Powerstate'] == 'Suspended'][['VM']].to_dict(orient='records')
            counts['suspended_vms_count'] = len(suspended_vms)

            oracle_vms = vinfo_data[vinfo_data['OS according to the VMware Tools'].str.contains('Oracle', na=False)][['VM', 'OS according to the VMware Tools', 'Powerstate', 'CPUs', 'Memory', 'Provisioned MiB', 'In Use MiB']].to_dict(orient='records')
            counts['oracle_vms_count'] = len(oracle_vms)

            vmtools_not_running = vinfo_data[(vinfo_data['Powerstate'] == 'poweredOn') & (vinfo_data['Guest state'] == 'notRunning')][['VM', 'Powerstate', 'Guest state', 'OS according to the configuration file']].to_dict(orient='records')
            counts['vmtools_not_running_count'] = len(vmtools_not_running)

            # Ensure 'Provisioned MiB' and 'In Use MiB' are numeric
            vinfo_data['Provisioned MiB'] = pd.to_numeric(vinfo_data['Provisioned MiB'], errors='coerce')
            vinfo_data['In Use MiB'] = pd.to_numeric(vinfo_data['In Use MiB'], errors='coerce')

            vinfo_data['Provisioned TB'] = (pd.to_numeric(vinfo_data['Provisioned MiB'], errors='coerce') * 1.048576) / (1024 * 1024)
            large_provisioned_vms = vinfo_data[vinfo_data['Provisioned TB'] > 10][['VM', 'Provisioned MiB', 'In Use MiB', 'CPUs', 'Memory']].to_dict(orient='records')
            counts['large_provisioned_vms_count'] = len(large_provisioned_vms)

            vinfo_data['CPUs'] = pd.to_numeric(vinfo_data['CPUs'], errors='coerce')

            # Load SKU data
            import json
            with open('rvtools_analyzer/static/sku.json') as f:
                sku_data = json.load(f)

            sku_cores = {sku['name']: sku['cores'] for sku in sku_data}

            for _, vm in vinfo_data.iterrows():
                if vm['CPUs'] > min(sku_cores.values()):
                    if not any(existing_vm['VM'] == vm['VM'] for existing_vm in high_vcpu_vms):
                        high_vcpu_vms.append({
                            'VM': vm['VM'],
                            'vCPU Count': vm['CPUs'],
                            **{sku: '✘' if vm['CPUs'] > cores else '✓' for sku, cores in sku_cores.items()}
                        })

            for _, vm in vinfo_data.iterrows():
                if vm['Memory'] > min(sku['ram'] * 1024 for sku in sku_data):
                    if not any(existing_vm['VM'] == vm['VM'] for existing_vm in high_memory_vms):
                        high_memory_vms.append({
                            'VM': vm['VM'],
                            'Memory (GB)': round(vm['Memory']/ 1024,2),
                            **{
                                sku['name']: '✘' if vm['Memory'] > sku['ram'] * 1024 else ('⚠️' if vm['Memory'] > (sku['ram'] * 1024) / 2 else '✓')
                                for sku in sku_data
                            }
                        })

        if 'dvPort' in excel_data.sheet_names:
            dvport_data = excel_data.parse('dvPort')
            dvport_data['VLAN'] = dvport_data['VLAN'].fillna(0).astype(int)
            dvport_issues = dvport_data[(dvport_data['VLAN'].isnull()) | (dvport_data['Allow Promiscuous'] == True) | (dvport_data['Mac Changes'] == True) | (dvport_data['Forged Transmits'] == True)][['Port', 'Switch', 'Object ID', 'VLAN', 'Allow Promiscuous', 'Mac Changes', 'Forged Transmits']].to_dict(orient='records')
            counts['dvport_issues_count'] = len(dvport_issues)

        if 'vCD' in excel_data.sheet_names:
            vcd_data = excel_data.parse('vCD')
            cdrom_issues = vcd_data[(vcd_data['Connected'] == True)][['VM', 'Powerstate', 'Connected', 'Starts Connected', 'Device Type']].to_dict(orient='records')
            counts['cdrom_issues_count'] = len(cdrom_issues)

        return render_template(
            'analyze.html',
            filename=file.filename,
            esx_version_data=esx_version_counts,
            esx_version_risks=esx_version_risks,
            esx_version_card_risk=esx_version_card_risk,
            WARNING_ESXI_VERSION_THRESHOLD=WARNING_ESXI_VERSION_THRESHOLD,
            ERROR_ESXI_VERSION_THRESHOLD=ERROR_ESXI_VERSION_THRESHOLD,
            vusb_devices=vusb_devices,
            risky_disks=risky_disks,
            switch_statistics=switch_statistics,
            vsnapshot_data=vsnapshot_data,
            suspended_vms=suspended_vms,
            oracle_vms=oracle_vms,
            dvport_issues=dvport_issues,
            non_intel_hosts=non_intel_hosts,
            vmtools_not_running=vmtools_not_running,
            cdrom_issues=cdrom_issues,
            large_provisioned_vms=large_provisioned_vms,
            high_vcpu_vms=high_vcpu_vms,
            high_memory_vms=high_memory_vms,
            counts=counts,
        )

    return redirect(url_for('index'))

@app.context_processor
def inject_calver_version():
    return dict(calver_version=calver_version)

def main():
    """
    Entry point for the rvtools-analyzer command.
    """
    app.run(debug=True)

if __name__ == '__main__':
    main()