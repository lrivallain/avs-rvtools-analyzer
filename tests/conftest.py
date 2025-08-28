#!/usr/bin/env python3
"""
Test configuration and shared fixtures.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


sys.path.append(str(Path(__file__).parent))
from create_test_data import create_comprehensive_test_data


def ensure_test_data_exists(force_recreate: bool = False):
    """Ensure comprehensive test data exists before running tests.

    Args:
        force_recreate (bool): If True, will recreate the test data file even if it exists.

    Returns:
        Path: The path to the test data file.
    """
    test_data_path = (
        Path(__file__).parent / "test-data" / "comprehensive_test_data.xlsx"
    )

    # Test folder exists
    if not test_data_path.parent.exists():
        test_data_path.parent.mkdir(parents=True)

    # If file exists and not forced, return the existing file
    if test_data_path.exists() and not force_recreate:
        # Load existing test data
        return test_data_path

    # Create the test data
    print(f"Creating test data at {test_data_path}")
    create_comprehensive_test_data()

    return test_data_path


@pytest.fixture(scope="session", autouse=True)
def setup_test_data():
    """Automatically ensure test data exists before any tests run."""
    ensure_test_data_exists(force_recreate=True)


@pytest.fixture(scope="session")
def comprehensive_excel_data():
    """Load comprehensive test data for all tests."""
    test_data_path = ensure_test_data_exists()
    return pd.ExcelFile(test_data_path)
