#!/usr/bin/env python3
"""
Google Calendar Event Searcher

This application pulls Google Calendar events based on various search criteria
including date range, event title keywords, attendees, and location.

Setup Instructions:
1. Install dependencies: pip install -r requirements.txt
2. Set up Google Cloud credentials (see README.md)
3. Run: python calendar_searcher.py --help
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the token.json file.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class GoogleCalendarSearcher:
    """A class to search Google Calendar events based on various criteria."""

    def __init__(self, credentials_path: str = "credentials.json"):
        """
        Initialize the Google Calendar Searcher.

        Args:
            credentials_path: Path to the Google OAuth credentials JSON file
        """
        self.credentials_path = credentials_path
        self.service = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Google API and build the service."""
        creds = None
        token_path = "token.json"

        # Load existing credentials if available
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # Refresh or obtain new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for future use
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        # Build the Calendar API service
        self.service = build("calendar", "v3", credentials=creds)

    def search_events(
        self,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        query: Optional[str] = None,
        max_results: int = 250,
        calendar_id: str = "primary",
        single_events: bool = True,
        order_by: str = "startTime",
    ) -> List[Dict[str, Any]]:
        """
        Search for calendar events based on criteria.

        Args:
            time_min: Start of time range (ISO 8601 format, e.g., '2024-01-01T00:00:00Z')
            time_max: End of time range (ISO 8601 format, e.g., '2024-12-31T23:59:59Z')
            query: Free text search query (searches summary, description, location)
            max_results: Maximum number of events to return
            calendar_id: Calendar ID ('primary' for primary calendar)
            single_events: Whether to expand recurring events
            order_by: Order by 'startTime' or 'updated'

        Returns:
            List of event dictionaries
        """
        try:
            # Build request parameters
            request_params = {
                "calendarId": calendar_id,
                "maxResults": max_results,
                "singleEvents": single_events,
                "orderBy": order_by,
            }

            # Add optional parameters
            if time_min:
                request_params["timeMin"] = time_min
            if time_max:
                request_params["timeMax"] = time_max
            if query:
                request_params["q"] = query

            # Execute the request
            events_result = (
                self.service.events()
                .list(**request_params)
                .execute()
            )

            events = events_result.get("items", [])

            if not events:
                print("No events found matching the criteria.")
                return []

            return events

        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def filter_events(
        self,
        events: List[Dict[str, Any]],
        keyword: Optional[str] = None,
        attendee_email: Optional[str] = None,
        location_contains: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter events by additional criteria after retrieval.

        Args:
            events: List of event dictionaries
            keyword: Filter by keyword in summary/description
            attendee_email: Filter by attendee email
            location_contains: Filter by location substring
            status: Filter by event status (confirmed, tentative, cancelled)

        Returns:
            Filtered list of events
        """
        filtered = []

        for event in events:
            # Filter by keyword
            if keyword:
                summary = event.get("summary", "").lower()
                description = event.get("description", "").lower()
                if keyword.lower() not in summary and keyword.lower() not in description:
                    continue

            # Filter by attendee
            if attendee_email:
                attendees = event.get("attendees", [])
                has_attendee = any(
                    attendee_email.lower() in att.get("email", "").lower()
                    for att in attendees
                )
                if not has_attendee:
                    continue

            # Filter by location
            if location_contains:
                location = event.get("location", "")
                if location_contains.lower() not in location.lower():
                    continue

            # Filter by status
            if status:
                event_status = event.get("status", "").lower()
                if status.lower() != event_status:
                    continue

            filtered.append(event)

        return filtered

    def display_events(self, events: List[Dict[str, Any]], verbose: bool = False) -> None:
        """
        Display events in a formatted manner.

        Args:
            events: List of event dictionaries
            verbose: Whether to show detailed information
        """
        if not events:
            print("No events to display.")
            return

        print(f"\n{'='*60}")
        print(f"Found {len(events)} event(s)")
        print(f"{'='*60}\n")

        for i, event in enumerate(events, 1):
            start = event.get("start", {})
            end = event.get("end", {})

            # Handle different start/end formats
            if "dateTime" in start:
                start_time = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
                start_str = start_time.strftime("%Y-%m-%d %H:%M")
            elif "date" in start:
                start_str = start["date"]
            else:
                start_str = "Unknown"

            if "dateTime" in end:
                end_time = datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00"))
                end_str = end_time.strftime("%Y-%m-%d %H:%M")
            elif "date" in end:
                end_str = end["date"]
            else:
                end_str = "Unknown"

            print(f"{i}. {event.get('summary', 'No Title')}")
            print(f"   When: {start_str} - {end_str}")

            if verbose:
                if event.get("location"):
                    print(f"   Location: {event.get('location')}")
                if event.get("description"):
                    desc = event.get("description", "")[:200]
                    print(f"   Description: {desc}...")
                if event.get("attendees"):
                    attendees = [att.get("email") for att in event.get("attendees", [])]
                    print(f"   Attendees: {', '.join(attendees)}")
                if event.get("status"):
                    print(f"   Status: {event.get('status')}")

            print()


def parse_date(date_str: str) -> str:
    """
    Parse various date formats and return ISO 8601 format.

    Args:
        date_str: Date string in various formats

    Returns:
        ISO 8601 formatted date string
    """
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.isoformat() + "Z"
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date: {date_str}")


def main():
    """Main entry point for the calendar searcher."""
    parser = argparse.ArgumentParser(
        description="Search Google Calendar events with various criteria",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search events in the next 7 days
  python calendar_searcher.py --days 7

  # Search for events with "meeting" in the title
  python calendar_searcher.py --query "meeting" --days 30

  # Search events with specific attendee
  python calendar_searcher.py --attendee "john@example.com" --days 30

  # Search events in a date range
  python calendar_searcher.py --start "2024-01-01" --end "2024-01-31"

  # Verbose output with location filter
  python calendar_searcher.py --location "Conference Room" --verbose
        """,
    )

    # Authentication
    parser.add_argument(
        "--credentials",
        type=str,
        default="credentials.json",
        help="Path to Google OAuth credentials file (default: credentials.json)",
    )

    # Date range options
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument(
        "--days",
        type=int,
        help="Number of days from now to search",
    )
    date_group.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY-MM-DD or ISO format)",
    )

    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY-MM-DD or ISO format)",
    )

    # Search criteria
    parser.add_argument(
        "--query",
        type=str,
        help="Free text search (searches summary, description, location)",
    )
    parser.add_argument(
        "--keyword",
        type=str,
        help="Filter results by keyword in title/description",
    )
    parser.add_argument(
        "--attendee",
        type=str,
        help="Filter by attendee email address",
    )
    parser.add_argument(
        "--location",
        type=str,
        help="Filter by location substring",
    )
    parser.add_argument(
        "--status",
        type=str,
        choices=["confirmed", "tentative", "cancelled"],
        help="Filter by event status",
    )

    # Output options
    parser.add_argument(
        "--max-results",
        type=int,
        default=250,
        help="Maximum number of events to return (default: 250)",
    )
    parser.add_argument(
        "--calendar-id",
        type=str,
        default="primary",
        help="Calendar ID to search (default: primary)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed event information",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    # Initialize searcher
    try:
        searcher = GoogleCalendarSearcher(credentials_path=args.credentials)
    except FileNotFoundError:
        print(f"Error: Credentials file '{args.credentials}' not found.")
        print("\nTo get started:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a project and enable the Google Calendar API")
        print("3. Create OAuth 2.0 credentials (Desktop app)")
        print("4. Download the credentials JSON file")
        print("5. Rename it to 'credentials.json' or use --credentials flag")
        return 1
    except Exception as e:
        print(f"Error initializing searcher: {e}")
        return 1

    # Determine time range
    time_min = None
    time_max = None

    if args.days:
        time_min = datetime.utcnow().isoformat() + "Z"
        time_max = (datetime.utcnow() + timedelta(days=args.days)).isoformat() + "Z"
    elif args.start:
        try:
            time_min = parse_date(args.start)
            if args.end:
                time_max = parse_date(args.end)
            else:
                # Default to 7 days if only start is provided
                start_dt = datetime.fromisoformat(time_min.replace("Z", "+00:00"))
                time_max = (start_dt + timedelta(days=7)).isoformat() + "Z"
        except ValueError as e:
            print(f"Error parsing date: {e}")
            return 1

    # Search for events
    print("Searching calendar events...")
    events = searcher.search_events(
        time_min=time_min,
        time_max=time_max,
        query=args.query,
        max_results=args.max_results,
        calendar_id=args.calendar_id,
    )

    # Apply additional filters
    if args.keyword or args.attendee or args.location or args.status:
        events = searcher.filter_events(
            events,
            keyword=args.keyword,
            attendee_email=args.attendee,
            location_contains=args.location,
            status=args.status,
        )

    # Output results
    if args.json:
        print(json.dumps(events, indent=2))
    else:
        searcher.display_events(events, verbose=args.verbose)

    return 0


if __name__ == "__main__":
    exit(main())
