# AVS RVTools Analyzer

AVS RVTools Analyzer is a Flask-based application for analyzing RVTools data. It provides insights into migration risks and allows users to explore the content of uploaded RVTools Excel files.

## Features
- Upload RVTools Excel files for analysis.
- View detailed information about the contents of the uploaded files.
- Analyze migration risks based on the data in the files:
  - USB devices
  - Disks with migration risks
  - Non dvSwitch network interfaces
  - Snapshots
  - Suspended VMs
  - dvPort issues
  - non Intel CPUs
  - Mounted CD/DVD drives
  - Oracle VMs
  - Large provisioned disks
  - VMs with high vCPU count
  - VMs with high memory allocation

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

The fastest way to run the application is using uv's tool runner:

```bash
# Run directly from PyPI (latest published version)
uv tool run avs-rvtools-analyzer

# Or run from source (current development version)
uv run avs-rvtools-analyzer
```

### Development Setup

If you want to work on the code or contribute to the project:

```bash
# Clone the repository
git clone <repository-url>
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
git clone <repository-url>
cd avs-rvtools-analyzer

# Using uv (recommended)
uv build
uv tool install dist/avs_rvtools_analyzer-*.whl

# Using pip
pip install .
```

## Development

### Setting up the development environment

```bash
# Install development dependencies
uv sync --extra dev

# Run the application in development mode
uv run avs-rvtools-analyzer

# Or activate the shell and run commands
uv shell
avs-rvtools-analyzer
```

### Code Quality Tools

This project uses several code quality tools that can be run with uv:

```bash
# Format code with black
uv run black rvtools_analyzer/ tests/

# Sort imports with isort
uv run isort rvtools_analyzer/ tests/

# Lint with flake8
uv run flake8 rvtools_analyzer/ tests/

# Type checking with mypy
uv run mypy rvtools_analyzer/

# Run all quality checks at once
uv run black . && uv run isort . && uv run flake8 . && uv run mypy .
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

## Running the Application

Once installed, start the Flask application:

```bash
avs-rvtools-analyzer
```

By default, the application will run on `http://127.0.0.1:5000`. Open this URL in your web browser to access the application.

### Configuration

You can configure the application using environment variables:

- `FLASK_ENV`: Set to `development` for development mode
- `FLASK_DEBUG`: Set to `1` to enable debug mode
- `FLASK_PORT`: Change the port (default: 5000)
- `FLASK_HOST`: Change the host (default: 127.0.0.1)

Example:
```bash
# Using uv
FLASK_DEBUG=1 FLASK_PORT=8080 uv run avs-rvtools-analyzer

# If installed as a tool
FLASK_DEBUG=1 FLASK_PORT=8080 avs-rvtools-analyzer
```

## Project Structure

```
rvtools-analyzer/
├── rvtools_analyzer/          # Main application package
│   ├── __init__.py           # Package initialization
│   ├── main.py               # Flask application and entry point
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
5. Run code quality checks: `uv run black . && uv run isort . && uv run flake8 .`
6. Commit your changes: `git commit -am 'Add some feature'`
7. Push to the branch: `git push origin feature-name`
8. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.
