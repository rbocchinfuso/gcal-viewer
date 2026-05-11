# Google Calendar Event Searcher

A Python application to search and retrieve Google Calendar events using various criteria.

## Features

- Search events by date range (relative or absolute)
- Free-text search across event summary, description, and location
- Filter by attendee email
- Filter by location substring
- Filter by event status (confirmed, tentative, cancelled)
- Output in human-readable format or JSON
- Support for multiple calendars

## Installation

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Set up Google Cloud credentials:**

   a. Go to [Google Cloud Console](https://console.cloud.google.com/)
   
   b. Create a new project or select an existing one
   
   c. Enable the Google Calendar API:
      - Navigate to "APIs & Services" > "Library"
      - Search for "Google Calendar API" and enable it
   
   d. Create OAuth 2.0 credentials:
      - Go to "APIs & Services" > "Credentials"
      - Click "Create Credentials" > "OAuth client ID"
      - Select "Desktop app" as the application type
      - Download the credentials JSON file
   
   e. Save the credentials file as `credentials.json` in the same directory as this script, or specify its path using the `--credentials` flag.

3. **First-time authentication:**

   When you run the script for the first time, it will open a browser window asking you to authorize the application. Follow the prompts to grant access to your calendar.

## Usage

### Basic Examples

**Search events in the next 7 days:**
```bash
python calendar_searcher.py --days 7
```

**Search for events with specific keyword:**
```bash
python calendar_searcher.py --query "team meeting" --days 30
```

**Search events with a specific attendee:**
```bash
python calendar_searcher.py --attendee "john@example.com" --days 30
```

**Search events in a date range:**
```bash
python calendar_searcher.py --start "2024-01-01" --end "2024-01-31"
```

**Filter by location:**
```bash
python calendar_searcher.py --location "Conference Room" --days 30 --verbose
```

### Advanced Options

**Output as JSON:**
```bash
python calendar_searcher.py --days 7 --json
```

**Search a specific calendar:**
```bash
python calendar_searcher.py --calendar-id "your-calendar-id@group.calendar.google.com" --days 30
```

**Filter by event status:**
```bash
python calendar_searcher.py --status confirmed --days 7
```

**Verbose output with all details:**
```bash
python calendar_searcher.py --days 7 --verbose
```

### Command-Line Arguments

| Argument | Description |
|----------|-------------|
| `--credentials PATH` | Path to Google OAuth credentials file (default: credentials.json) |
| `--days N` | Number of days from now to search |
| `--start DATE` | Start date (YYYY-MM-DD or ISO format) |
| `--end DATE` | End date (YYYY-MM-DD or ISO format) |
| `--query TEXT` | Free text search (searches summary, description, location) |
| `--keyword TEXT` | Filter results by keyword in title/description |
| `--attendee EMAIL` | Filter by attendee email address |
| `--location TEXT` | Filter by location substring |
| `--status STATUS` | Filter by event status (confirmed, tentative, cancelled) |
| `--max-results N` | Maximum number of events to return (default: 250) |
| `--calendar-id ID` | Calendar ID to search (default: primary) |
| `--verbose` | Show detailed event information |
| `--json` | Output results as JSON |

## Date Formats

The application accepts various date formats:
- `YYYY-MM-DD` (e.g., `2024-01-15`)
- `YYYY-MM-DDTHH:MM:SS` (e.g., `2024-01-15T09:00:00`)
- `YYYY-MM-DD HH:MM:SS` (e.g., `2024-01-15 09:00:00`)
- `DD/MM/YYYY` (e.g., `15/01/2024`)
- `MM/DD/YYYY` (e.g., `01/15/2024`)

## Security Notes

- The `token.json` file contains your OAuth refresh token. Keep it secure and do not share it.
- The application requests read-only access to your calendar.
- You can revoke access at any time from your Google Account settings.

## Troubleshooting

**Error: Credentials file not found**
- Ensure `credentials.json` is in the current directory or specify the path with `--credentials`

**Error: Token expired**
- Delete `token.json` and re-run the application to re-authenticate

**Error: Insufficient permissions**
- Make sure you've enabled the Google Calendar API in your Google Cloud project
- Verify that your OAuth credentials have the correct scopes

## License

This project is provided as-is for educational purposes.
