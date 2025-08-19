import pytest
from avs_rvtools_analyzer.main import app
import pandas as pd
from io import BytesIO

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def fake_excel_data():
    # Create a fake Excel file with multiple sheets
    data = {
        'vHost': pd.DataFrame({
            'ESX Version': ['6.7.0', '7.0.0'],
            'CPU Model': ['Intel Xeon', 'AMD Ryzen'],
            'Host': ['Host1', 'Host2'],
            'Datacenter': ['DC1', 'DC2'],
            'Cluster': ['Cluster1', 'Cluster2'],
            '# VMs': [10, 5]
        }),
        'vUSB': pd.DataFrame({
            'VM': ['VM1', 'VM2'],
            'Powerstate': ['poweredOn', 'poweredOff'],
            'Device Type': ['USB Controller', 'USB Device'],
            'Connected': [True, False]
        }),
        'vDisk': pd.DataFrame({
            'VM': ['VM1', 'VM2'],
            'Powerstate': ['poweredOn', 'poweredOff'],
            'Disk': ['Disk1', 'Disk2'],
            'Capacity MiB': [1024, 2048],
            'Raw': [True, False],
            'Disk Mode': ['independent_persistent', 'persistent']
        })
    }

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    return output
