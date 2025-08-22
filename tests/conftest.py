#!/usr/bin/env python3
"""
Test configuration and shared fixtures.
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def ensure_test_data_exists():
    """Ensure comprehensive test data exists before running tests."""
    test_data_path = Path(__file__).parent / "test-data" / "comprehensive_test_data.xlsx"

    if not test_data_path.exists():
        # Import and run the test data creation script
        sys.path.append(str(Path(__file__).parent))
        from create_test_data import create_comprehensive_test_data

        # Create the test data
        print(f"Creating test data at {test_data_path}")
        create_comprehensive_test_data()

    return test_data_path


@pytest.fixture(scope="session", autouse=True)
def setup_test_data():
    """Automatically ensure test data exists before any tests run."""
    ensure_test_data_exists()


@pytest.fixture(scope="session")
def comprehensive_excel_data():
    """Load comprehensive test data for all tests."""
    test_data_path = ensure_test_data_exists()
    return pd.ExcelFile(test_data_path)
