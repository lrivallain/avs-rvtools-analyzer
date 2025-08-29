# AI supercharged RVTools Analyzer for Azure VMware Solution

A unified FastAPI application for analyzing RVTools data with both web interface and AI integration capabilities.
Provides insights into Azure VMware Solution migration risks through an intuitive web UI and Model Context Protocol (MCP)
server for AI tool integration.

## Features

- **Unified Server**: Single application providing both web interface and MCP API
- **Web Interface**: Upload and analyze RVTools Excel files through a user-friendly interface
- **Azure OpenAI Integration**: AI-powered risk analysis suggestions with environment variable configuration
- **MCP Integration**: MCP server capabilities for AI assistants to analyze migration risks
- **Risk Assessment**: Comprehensive analysis of 14 migration risk categories:
  - vUSB devices (blocking)
  - Risky disks (dynamic)
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
  - VM Hardware version compatibility (blocking)
  - Shared disks (blocking)
  - Clear text passwords (emergency)
  - VMkernel networks (warning)
  - VM with Fault Tolerance (warning)

## AI integration disclaimer

The AI integration in RVTools Analyzer may produce unexpected behavior or inaccuracies in the analysis results.

⚠️ It is strongly recommended to review the output carefully and validate it against known data. Additionally, please ensure
that data privacy and compliance requirements are taken into account when using AI tools, as submitted data will be shared
with AI systems. ⚠️

The provided tools **run locally** to generate an analysis report from the uploaded RVTools file. If integrated with AI models,
the data is processed and analyzed to deliver deeper insights and recommendations. If your AI models are not running in a
local or secure environment, it is essential to verify that data is handled appropriately and in compliance with applicable
regulations and your organization’s policies.

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
uv run avs-rvtools-analyzer --reload --debug

# Or activate the virtual environment
uv shell
avs-rvtools-analyzer --reload --debug
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

## Azure OpenAI Integration

The application supports [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-foundry/models/openai/) integration for AI-powered
risk analysis suggestions. This feature provides intelligent recommendations for migration risks detected in your RVTools data.

### Prerequisites

To use Azure OpenAI integration, you need:

1. **Azure OpenAI Resource**: Create an Azure OpenAI resource in your Azure subscription
2. **Model Deployment**: Deploy a compatible model (e.g., GPT-4, GPT-3.5-turbo) in your Azure OpenAI resource
3. **API Access**: Obtain your endpoint URL and API key from the Azure portal

For detailed setup instructions, see [docs/azure-openai-integration.md](docs/azure-openai-integration.md).

### Configuration

Configure Azure OpenAI using environment variables (server-side only):

```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4.1"
```

**Using .env file (recommended for development):**

Create a `.env` file in the project root:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1
```

## Development

### Development Environment

```bash
# Install development dependencies
uv sync --extra dev

# Run in development mode
uv run avs-rvtools-analyzer --host 127.0.0.1 --port 8000 --reload --debug
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

#### API Endpoints

The application provides several REST API endpoints:

**Analysis Endpoints:**

- `POST /api/analyze` - Analyze RVTools file by server file path
- `POST /api/analyze-upload` - Upload and analyze RVTools Excel file
- `POST /api/analyze-json` - Analyze JSON data for migration risks

**Data Conversion:**

- `POST /api/convert-to-json` - Convert uploaded Excel file to JSON format

**Information Endpoints:**

- `GET /api/risks` - List all available risk assessments
- `GET /api/sku` - Get Azure VMware Solution SKU capabilities
- `GET /api/info` - Server information and available endpoints
- `GET /health` - Health check status

#### AI Integration Workflow

For AI models and automated analysis, the application supports a flexible workflow:

1. **Excel to JSON Conversion**: Use `/api/convert-to-json` to convert RVTools Excel files into structured JSON data
2. **JSON Data Analysis**: Use `/api/analyze-json` to analyze the converted JSON data for migration risks
3. **Direct Analysis**: Alternatively, use `/api/analyze-upload` for direct file analysis without conversion
4. **AI based suggestions**: Use `/api/ai-suggestions` to get AI-generated suggestions for a migration risks

This workflow enables AI models to process RVTools data in multiple formats and provides maximum flexibility for automated migration assessments.

### MCP Tools for AI Integration

The application exposes MCP tools for AI assistants:

1. **`analyze_file`**: Analyze RVTools file by providing a file path on the server.
2. **`analyze_uploaded_file`**: Upload and analyze RVTools Excel file.
3. **`analyze_json_data`**: Analyze JSON data for migration risks and compatibility issues.
4. **`convert_excel_to_json`**: Convert Excel file to JSON format for AI model consumption.
5. **`list_available_risks`**: List all migration risks that can be assessed by this tool.
6. **`get_sku_capabilities`**: Get Azure VMware Solution (AVS) SKU hardware capabilities and specifications.

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
