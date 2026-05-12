# Google Calendar Viewer - Dockerized

A containerized Flask application that pulls Google Calendar events and serves them as a modern dark-mode HTML page. The application runs a daily scheduled task to update the calendar view.

## Features

- **Daily Updates**: Automatically fetches calendar events once per day at 8:00 AM
- **Modern Dark Mode UI**: Clean, responsive design with color-coded event statuses
- **Search Filtering**: Filter events by keyword, date range, and status
- **Flask Web Server**: Serves the generated HTML page on port 5000
- **Docker Compose**: Easy deployment with persistent storage for tokens and output

## Prerequisites

1. **Google Calendar API Setup**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download `credentials.json`

2. **Directory Structure**:
   ```
   .
   ├── credentials/          # Place credentials.json here
   ├── output/              # Generated HTML pages stored here
   ├── token.json           # OAuth token (auto-generated)
   ├── calendar_searcher_html.py
   ├── app.py
   ├── Dockerfile
   ├── docker-compose.yml
   └── requirements.txt
   ```

## Quick Start

### 1. Setup Credentials

Place your `credentials.json` file in the `credentials/` directory:

```bash
mkdir -p credentials
cp /path/to/your/credentials.json credentials/
```

### 2. Build and Run with Docker Compose

```bash
docker-compose up --build
```

The application will:
- Build the Docker image
- Start the Flask server on port 5000
- Run the initial calendar fetch
- Schedule daily updates at 8:00 AM

### 3. First-Time Authentication

On first run, check the logs for an authentication URL:

```bash
docker-compose logs -f
```

Click the URL, authenticate with Google, and copy the authorization code back if needed. The OAuth token will be saved to `token.json` for subsequent runs.

### 4. View the Calendar

Open your browser to: http://localhost:5000

## Configuration

Environment variables can be set in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARCH_QUERY` | `moto` | Keyword to search for in events |
| `SEARCH_DAYS` | `30` | Number of days to look ahead |
| `TZ` | `America/New_York` | Timezone for scheduling |

## Manual Usage (Without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Flask app directly
python app.py

# Or run the calendar searcher manually
python calendar_searcher_html.py -q "moto" --days 30
```

## Customizing the Schedule

To change the daily run time, edit `app.py`:

```python
schedule.every().day.at("08:00").do(run_calendar_search)
# Change "08:00" to your preferred time (24-hour format)
```

## Persistent Storage

The following are persisted via Docker volumes:
- `./output/` - Generated HTML files
- `./token.json` - OAuth authentication token
- `./credentials/` - Google API credentials

## Troubleshooting

### No Events Showing
- Ensure `credentials.json` is in the `credentials/` folder
- Check that the Google Calendar API is enabled
- Verify the search query matches event titles
- Check logs for authentication errors

### Authentication Issues
- Delete `token.json` to force re-authentication
- Ensure OAuth consent screen is configured in Google Cloud Console
- Check that your Google account has access to the calendar

### Container Won't Start
```bash
docker-compose down
docker-compose up --build
```

## API Endpoints

- `GET /` - Serves the generated calendar HTML page
- `GET /static/<path>` - Serves static assets (if added)

## License

MIT
