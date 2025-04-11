# RVTools Analyzer

RVTools Analyzer is a Flask-based application for analyzing RVTools data. It provides insights into migration risks and allows users to explore the content of uploaded RVTools Excel files.

## Installation and Usage

Follow these steps to set up and run the application:

### 1. Clone the Repository
First, clone the repository from GitHub:
```bash
git clone <repository-url>
cd rvtools-analyzer
```
Replace `<repository-url>` with the actual URL of the GitHub repository.

### 2. Install Dependencies
Install the required Python dependencies from the source:
```bash
pip install .
```
This will install the application and its dependencies as specified in `setup.py` and `requirements.txt`.

### 3. Run the Application
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
