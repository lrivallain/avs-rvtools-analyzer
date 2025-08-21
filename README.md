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

## AI integration disclaimer

The AI integration in RVTools Analyzer may produce unexpected behavior or inaccuracies in the analysis results. It is strongly recommended to review the output carefully and validate it against known data. Additionally, please ensure that data privacy and compliance requirements are taken into account when using AI tools, as submitted data will be shared with AI systems.

The provided tools **run locally** to generate an analysis report from the uploaded RVTools file. If integrated with AI models, the data is processed and analyzed to deliver deeper insights and recommendations. If your AI models are not running in a local or secure environment, it is essential to verify that data is handled appropriately and in compliance with applicable regulations and your organization’s policies.

## Installation and Usage

### Prerequisites

Make sure you have [`uv`](https://docs.astral.sh/uv/) installed:

```bash
# On Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Quick Start with `uv`

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
- MCP tools: Available at `/mcp` endpoint for AI integration

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
uv run avs-rvtools-analyzer # run the tool

# Using pip
pip install avs-rvtools-analyzer
avs-rvtools-analyzer # run the tool
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

The application exposes MCP tools for AI assistants:

1. **`analyze_file`**: Analyze RVTools file by providing a file path on the server.
2. **`analyze_uploaded_file`**: Upload and analyze RVTools Excel file.
3. **`list_available_risks`**: List all migration risks that can be assessed by this tool.
4. **`get_sku_capabilities`**: Get Azure VMware Solution (AVS) SKU hardware capabilities and specifications.

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
