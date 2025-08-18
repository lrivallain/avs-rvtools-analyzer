# This file marks the rvtools_analyzer directory as a Python package.
__version__ = '2025.5.0'

# For uv tool execution
def main():
    """Entry point for uv tool execution."""
    from rvtools_analyzer.main import main as app_main
    app_main()
