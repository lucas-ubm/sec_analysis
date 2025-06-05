# SEC Filing Analysis Web Application

This is a web interface for the SEC Filing Analysis Tool that allows users to run their own analyses with custom keywords and configurations.

## Features

- User-friendly web interface for running SEC filing analyses
- Customizable keyword searches
- Configurable date ranges and filing types
- Real-time progress tracking
- Excel file download of results
- Background processing of analyses

## Deployment on Railway.app

1. Create a new project on Railway.app
2. Connect your GitHub repository
3. Add the following environment variables in Railway.app:
   - `PYTHON_VERSION`: 3.8
   - `PORT`: 8000 (Railway will set this automatically)

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the development server:
   ```bash
   uvicorn app:app --reload
   ```

3. Access the web interface at `http://localhost:8000`

## Usage

1. Enter your keywords (comma-separated)
2. Specify the date range for analysis
3. Choose filing types (e.g., 10-K, 10-Q)
4. Enter CIK/Ticker numbers for companies to analyze
5. Provide your user agent (name/email)
6. Click "Start Analysis"
7. Wait for the analysis to complete
8. Download the results as an Excel file

## Notes

- The analysis runs in the background and may take several minutes to complete
- Results are stored temporarily and should be downloaded promptly
- Each analysis gets a unique ID for tracking and downloading results
- The web interface automatically handles all the configuration and file management

## Security Considerations

- User agent information is required by SEC EDGAR
- All analyses are isolated with unique IDs
- Temporary files are stored in the `datasets` directory
- Results are only accessible through the download endpoint with the correct job ID 