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


## Installation

Follow these steps to set up and run the application:

### From PyPI

You can install RVTools Analyzer directly from PyPI using pip:
```bash
pip install avs-rvtools-analyzer
```

### From Source

If you prefer to install from the source, follow these steps:
```bash
git clone <repository-url>
cd rvtools-analyzer
```
Replace `<repository-url>` with the actual URL of the GitHub repository.

Install the required Python dependencies from the source:
```bash
pip install .
```
This will install the application and its dependencies as specified in `setup.py` and `requirements.txt`.

## Run the Application
Start the Flask application:
```bash
rvtools-analyzer
```
By default, the application will run on `http://127.0.0.1:5000`. Open this URL in your web browser to access the application.

## Development

If you want to make changes to the code, you can install the application in editable mode:
```bash
pip install -e .
```
This allows you to modify the source code and see the changes immediately without reinstalling.

## Testing

To run the tests, use:
```bash
pytest
```
This will execute all the test cases in the `tests/` directory.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
