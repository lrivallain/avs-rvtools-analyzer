import pytest
from rvtools_analyzer.main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_view(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'RVTools Analyzer' in response.data

def test_explore_view_no_file(client):
    response = client.post('/explore', data={})
    assert response.status_code == 302  # Redirect to index

def test_analyze_view_no_file(client):
    response = client.post('/analyze', data={})
    assert response.status_code == 302  # Redirect to index

def test_explore_view_with_fake_data(client, fake_excel_data):
    response = client.post('/explore', data={'file': (fake_excel_data, 'test.xlsx')})
    assert response.status_code == 200
    assert b'Exploring RVTools File' in response.data
    assert b'vHost' in response.data
    assert b'vUSB' in response.data
    assert b'vDisk' in response.data

def test_analyze_view_with_fake_data(client, fake_excel_data):
    response = client.post('/analyze', data={'file': (fake_excel_data, 'test.xlsx')})
    assert response.status_code == 200
    assert b'Migration Risks Analysis' in response.data
    assert b'vUSB Devices' in response.data
    assert b'Risky Disks' in response.data
    assert b'Non-Intel Hosts' in response.data

def test_analyze_view_with_all_risks(client, fake_excel_data):
    response = client.post('/analyze', data={'file': (fake_excel_data, 'test.xlsx')})
    assert response.status_code == 200
    assert b'Migration Risks Analysis' in response.data

    # Check for all risk categories
    assert b'vUSB Devices' in response.data
    assert b'Risky Disks' in response.data
    assert b'ESX Versions' in response.data
