# This file marks the avs_rvtools_analyzer directory as a Python package.
__version__ = '2025.8.3'

# For uv tool execution
def main():
    """Entry point for uv tool execution."""
    from avs_rvtools_analyzer.main import main as app_main
    app_main()
