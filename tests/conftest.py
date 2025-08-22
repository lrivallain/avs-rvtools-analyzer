import pytest
from pathlib import Path
import pandas as pd
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session", autouse=True)
def ensure_test_data_exists():
    """Ensure comprehensive test data exists before running any tests."""
    test_data_path = Path(__file__).parent / 'test-data' / 'comprehensive_test_data.xlsx'
    
    if not test_data_path.exists():
        # Create the test-data directory if it doesn't exist
        test_data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate test data
        from create_test_data import create_comprehensive_test_data
        print(f"Generating comprehensive test data at {test_data_path}...")
        create_comprehensive_test_data()
        print("Test data generated successfully!")
    
    return test_data_path


@pytest.fixture
def comprehensive_test_data_path():
    """Provide the path to comprehensive test data."""
    return Path(__file__).parent / 'test-data' / 'comprehensive_test_data.xlsx'
