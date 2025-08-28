# This file marks the avs_rvtools_analyzer directory as a Python package.
import tomllib
from pathlib import Path


def _get_version():
    """Read version from pyproject.toml file."""
    try:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)
                return pyproject_data.get("project", {}).get("version", "unknown")
        return "unknown"
    except Exception:
        return "unknown"


__version__ = _get_version()


# For uv tool execution
def main():
    """Entry point for uv tool execution."""
    from avs_rvtools_analyzer.main import main as app_main

    app_main()
