# AVS RVTools Analyzer

A unified FastAPI application for analyzing RVTools data with both web interface and AI integration capabilities. Provides insights into Azure VMware Solution migration risks through an intuitive web UI and Model Context Protocol (MCP) server for AI tool integration.

## Features

- **Unified Server**: Single application providing both web interface and MCP API
- **Web Interface**: Upload and analyze RVTools Excel files through a user-friendly interface
- **AI Integration**: MCP server capabilities for AI assistants to analyze migration risks
- **Risk Assessment**: Comprehensive analysis of 14 migration risk categories:
  - vUSB devices (blocking)
  - Risky disks (blocking)
  - Non-dvSwitch networks (blocking)
  - High vCPU/memory VMs (blocking)
  - VM snapshots (warning)
  - Suspended VMs (warning)
  - dvPort configuration issues (warning)
  - Non-Intel hosts (warning)
  - CD-ROM devices (warning)
  - VMware Tools status (warning)
  - Large provisioned storage (warning)
  - Oracle VMs (info)
  - ESX version compatibility (dynamic)

## Installation and Usage

### Prerequisites

Make sure you have [uv](https://docs.astral.sh/uv/) installed:

```bash
# On Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Quick Start with uv

Run the unified application with both web UI and MCP API:

```bash
# Run directly from PyPI (latest published version)
uv tool run avs-rvtools-analyzer

# Or run from source (current development version)
uv run avs-rvtools-analyzer
```

The application provides:

- Web interface: `http://127.0.0.1:8000` (upload and analyze files)
- API documentation: `http://127.0.0.1:8000/docs` (interactive OpenAPI docs)
- MCP tools: Available at `/tools` endpoint for AI integration

### Development Setup

```bash
# Clone the repository
git clone https://github.com/lrivallain/avs-rvtools-analyzer.git
cd avs-rvtools-analyzer

# Install dependencies and run in development mode
uv sync --extra dev
uv run avs-rvtools-analyzer

# Or activate the virtual environment
uv shell
avs-rvtools-analyzer
```

### Traditional Installation Methods

#### From PyPI

You can install RVTools Analyzer directly from PyPI:

```bash
# Using uv (recommended)
uv tool install avs-rvtools-analyzer

# Using pip
pip install avs-rvtools-analyzer
```

#### From Source

```bash
git clone https://github.com/lrivallain/avs-rvtools-analyzer.git
cd avs-rvtools-analyzer

# Using uv (recommended)
uv build
uv tool install dist/avs_rvtools_analyzer-*.whl

# Using pip
pip install .
```

## Development

### Development Environment

```bash
# Install development dependencies
uv sync --extra dev

# Run in development mode
uv run avs-rvtools-analyzer --host 127.0.0.1 --port 8000
```

### Testing

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=rvtools_analyzer

# Run tests in watch mode (if pytest-watch is installed)
uv add --dev pytest-watch
uv run ptw
```

### Building and Publishing

```bash
# Build the package
uv build

# Publish to PyPI (requires authentication)
uv publish
```

## Usage

### Running the Application

Start the unified server with both web UI and MCP API:

```bash
# Default: runs on http://127.0.0.1:8000
uv run avs-rvtools-analyzer

# Custom host and port
uv run avs-rvtools-analyzer --host 0.0.0.0 --port 9000
```

### Available Interfaces

- **Web UI**: Upload RVTools files and view analysis results
- **API Documentation**: Interactive OpenAPI documentation at `/docs`
- **Health Check**: System status at `/health`
- **MCP Tools**: AI integration endpoints for automated analysis

### MCP Tools for AI Integration

The application exposes three MCP tools for AI assistants:

1. **`analyze_rvtools_file`**: Analyze uploaded RVTools files
2. **`get_available_risks`**: List all supported risk categories
3. **`get_risk_info`**: Get detailed information about specific risks

## Project Structure

```text
avs-rvtools-analyzer/
├── avs_rvtools_analyzer/      # Main application package
│   ├── __init__.py           # Package initialization
│   ├── main.py               # Unified FastAPI server (web UI + MCP API)
│   ├── risk_detection.py     # Risk detection logic and functions
│   ├── utils.py              # Utility functions and helpers
│   ├── static/               # Static assets (CSS, JS, JSON)
│   └── templates/            # Jinja2 templates
├── tests/                    # Test suite
├── test-data/               # Sample test data
├── pyproject.toml           # Project configuration and dependencies
├── README.md                # This file
└── .gitignore              # Git ignore rules
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `uv run pytest`
5. Opt. Run code quality checks: `uv run black . && uv run isort . && uv run flake8 .`
6. Commit your changes: `git commit -am 'Add some feature'`
7. Push to the branch: `git push origin feature-name`
8. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.
