#!/usr/bin/env python3
"""
Google Calendar Event Searcher with HTML Output
Pulls events from Google Calendar based on search criteria and generates a pretty HTML page.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying scopes, delete the token.json file.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Path configuration
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def authenticate():
    """Authenticate with Google Calendar API."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"Error: {CREDENTIALS_FILE} not found.")
                print("Please download it from Google Cloud Console and place it in the current directory.")
                sys.exit(1)
            
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    
    return creds


def search_events(service, calendar_id='primary', time_min=None, time_max=None, 
                  query=None, max_results=50, order_by='startTime', 
                  single_events=True, attendee_email=None, location=None, status=None):
    """
    Search for events in Google Calendar.
    
    Args:
        service: Google API service object
        calendar_id: Calendar ID (default: 'primary')
        time_min: Start of time range (datetime or ISO string)
        time_max: End of time range (datetime or ISO string)
        query: Free text search query
        max_results: Maximum number of events to return
        order_by: Order by 'startTime' or 'updated'
        single_events: Whether to expand recurring events
        attendee_email: Filter by attendee email
        location: Filter by location
        status: Filter by event status (confirmed, tentative, cancelled)
    
    Returns:
        List of events
    """
    try:
        # Build the request parameters
        request_params = {
            'calendarId': calendar_id,
            'maxResults': max_results,
            'singleEvents': single_events,
            'orderBy': order_by
        }
        
        # Add time filters
        if time_min:
            if isinstance(time_min, datetime):
                request_params['timeMin'] = time_min.isoformat() + 'Z'
            else:
                request_params['timeMin'] = time_min
        
        if time_max:
            if isinstance(time_max, datetime):
                request_params['timeMax'] = time_max.isoformat() + 'Z'
            else:
                request_params['timeMax'] = time_max
        
        # Add text search
        if query:
            request_params['q'] = query
        
        # Execute the request
        events_result = service.events().list(**request_params).execute()
        events = events_result.get('items', [])
        
        # Apply additional filters client-side
        filtered_events = []
        for event in events:
            # Filter by attendee
            if attendee_email:
                attendees = event.get('attendees', [])
                attendee_emails = [a.get('email', '').lower() for a in attendees]
                if attendee_email.lower() not in attendee_emails:
                    continue
            
            # Filter by location
            if location and location.lower() not in event.get('location', '').lower():
                continue
            
            # Filter by status
            if status and event.get('status', '').lower() != status.lower():
                continue
            
            filtered_events.append(event)
        
        return filtered_events
    
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def format_event_for_html(event):
    """Format an event for HTML display."""
    title = event.get('summary', 'No Title')
    description = event.get('description', '')
    location = event.get('location', '')
    status = event.get('status', 'confirmed')
    
    # Parse start and end times
    start = event.get('start', {})
    end = event.get('end', {})
    
    if 'dateTime' in start:
        start_dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
        start_str = start_dt.strftime('%Y-%m-%d %H:%M')
        is_all_day = False
    elif 'date' in start:
        start_dt = datetime.fromisoformat(start['date'])
        start_str = start_dt.strftime('%Y-%m-%d')
        is_all_day = True
    else:
        start_str = 'Unknown'
        is_all_day = False
    
    if 'dateTime' in end:
        end_dt = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
        end_str = end_dt.strftime('%Y-%m-%d %H:%M')
    elif 'date' in end:
        end_dt = datetime.fromisoformat(end['date'])
        end_str = end_dt.strftime('%Y-%m-%d')
    else:
        end_str = 'Unknown'
    
    # Get attendees
    attendees = event.get('attendees', [])
    attendee_list = [a.get('email', '') for a in attendees if a.get('email')]
    
    # Get organizer
    organizer = event.get('organizer', {})
    organizer_email = organizer.get('email', '')
    organizer_name = organizer.get('displayName', organizer_email)
    
    # Determine color based on status
    status_colors = {
        'confirmed': '#4CAF50',
        'tentative': '#FF9800',
        'cancelled': '#F44336'
    }
    status_color = status_colors.get(status.lower(), '#2196F3')
    
    return {
        'title': title,
        'description': description,
        'location': location,
        'start': start_str,
        'end': end_str,
        'is_all_day': is_all_day,
        'attendees': attendee_list,
        'organizer': organizer_name,
        'status': status,
        'status_color': status_color,
        'html_link': event.get('htmlLink', '')
    }


def generate_html(events_data, output_file='calendar_events.html', search_params=None):
    """Generate a pretty HTML page with events in dark mode."""
    
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Calendar Events</title>
    <style>
        :root {
            --bg-primary: #0f0f13;
            --bg-secondary: #1a1a24;
            --bg-card: #252533;
            --bg-hover: #2d2d3d;
            --text-primary: #ffffff;
            --text-secondary: #b8b8c9;
            --text-muted: #6b6b7b;
            --accent-primary: #6366f1;
            --accent-secondary: #8b5cf6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --border-color: #3a3a4a;
            --shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            --shadow-hover: 0 8px 30px rgba(99, 102, 241, 0.2);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, var(--bg-primary) 0%, #1a1a2e 100%);
            min-height: 100vh;
            padding: 20px;
            color: var(--text-primary);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-card) 100%);
            padding: 40px;
            border-radius: 20px;
            box-shadow: var(--shadow);
            margin-bottom: 30px;
            text-align: center;
            border: 1px solid var(--border-color);
            position: relative;
            overflow: hidden;
        }
        
        header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
        }
        
        h1 {
            color: var(--text-primary);
            margin-bottom: 15px;
            font-size: 2.5em;
            font-weight: 700;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .search-info {
            background: var(--bg-primary);
            padding: 20px;
            border-radius: 12px;
            margin-top: 20px;
            text-align: left;
            border: 1px solid var(--border-color);
        }
        
        .search-info p {
            margin: 8px 0;
            color: var(--text-secondary);
            font-size: 0.95em;
        }
        
        .search-info strong {
            color: var(--accent-primary);
            font-weight: 600;
        }
        
        .event-count {
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: white;
            padding: 12px 28px;
            border-radius: 30px;
            display: inline-block;
            margin-top: 20px;
            font-weight: 600;
            font-size: 1.1em;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        }
        
        .events-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 24px;
        }
        
        .event-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 28px;
            box-shadow: var(--shadow);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid var(--border-color);
            border-left: 4px solid var(--accent-primary);
            position: relative;
            overflow: hidden;
        }
        
        .event-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--border-color), transparent);
        }
        
        .event-card:hover {
            transform: translateY(-6px);
            box-shadow: var(--shadow-hover);
            border-color: var(--accent-primary);
        }
        
        .event-card.confirmed {
            border-left-color: var(--success);
        }
        
        .event-card.tentative {
            border-left-color: var(--warning);
        }
        
        .event-card.cancelled {
            border-left-color: var(--danger);
            opacity: 0.75;
        }
        
        .event-title {
            font-size: 1.35em;
            color: var(--text-primary);
            margin-bottom: 18px;
            font-weight: 600;
            line-height: 1.4;
            letter-spacing: -0.3px;
        }
        
        .event-time {
            background: var(--bg-primary);
            padding: 14px 18px;
            border-radius: 12px;
            margin-bottom: 18px;
            color: var(--accent-primary);
            font-weight: 500;
            border: 1px solid var(--border-color);
        }
        
        .event-time div {
            margin: 6px 0;
        }
        
        .event-details {
            margin-bottom: 18px;
        }
        
        .detail-row {
            display: flex;
            align-items: flex-start;
            margin-bottom: 12px;
            color: var(--text-secondary);
            font-size: 0.95em;
        }
        
        .detail-icon {
            margin-right: 12px;
            min-width: 20px;
            font-size: 1.1em;
        }
        
        .event-description {
            background: var(--bg-primary);
            padding: 18px;
            border-radius: 12px;
            margin-bottom: 18px;
            color: var(--text-secondary);
            line-height: 1.7;
            max-height: 140px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            font-size: 0.92em;
        }
        
        .event-description::-webkit-scrollbar {
            width: 6px;
        }
        
        .event-description::-webkit-scrollbar-track {
            background: var(--bg-primary);
            border-radius: 3px;
        }
        
        .event-description::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 3px;
        }
        
        .event-attendees {
            margin-top: 18px;
            padding-top: 18px;
            border-top: 1px solid var(--border-color);
        }
        
        .attendee-tag {
            display: inline-block;
            background: rgba(99, 102, 241, 0.15);
            color: var(--accent-primary);
            padding: 6px 14px;
            border-radius: 20px;
            margin: 4px;
            font-size: 0.82em;
            font-weight: 500;
            border: 1px solid rgba(99, 102, 241, 0.3);
            transition: all 0.2s ease;
        }
        
        .attendee-tag:hover {
            background: rgba(99, 102, 241, 0.25);
            border-color: var(--accent-primary);
        }
        
        .organizer-badge {
            background: rgba(245, 158, 11, 0.15);
            color: var(--warning);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.82em;
            font-weight: 500;
            display: inline-block;
            margin-top: 12px;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        
        .status-badge {
            display: inline-block;
            padding: 6px 16px;
            border-radius: 20px;
            color: white;
            font-weight: 600;
            font-size: 0.8em;
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .view-link {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: white;
            padding: 12px 24px;
            border-radius: 12px;
            text-decoration: none;
            margin-top: 18px;
            transition: all 0.3s ease;
            font-weight: 500;
            font-size: 0.92em;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        }
        
        .view-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
        }
        
        .no-events {
            background: var(--bg-card);
            padding: 60px 40px;
            border-radius: 20px;
            text-align: center;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
        }
        
        .no-events h2 {
            color: var(--text-secondary);
            margin-bottom: 15px;
            font-size: 1.8em;
        }
        
        .no-events p {
            color: var(--text-muted);
            font-size: 1.05em;
        }
        
        .empty-icon {
            font-size: 4em;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        footer {
            text-align: center;
            margin-top: 50px;
            color: var(--text-muted);
            padding: 30px;
            font-size: 0.9em;
            border-top: 1px solid var(--border-color);
        }
        
        @media (max-width: 768px) {
            .events-grid {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 1.9em;
            }
            
            header {
                padding: 30px 20px;
            }
            
            .event-card {
                padding: 22px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📅 Google Calendar Events</h1>
            <div class="event-count">{{EVENT_COUNT}} event(s) found</div>
            {{SEARCH_INFO}}
        </header>
        
        <div class="events-grid">
            {{EVENT_CARDS}}
        </div>
        
        {{NO_EVENTS}}
        
        <footer>
            <p>Generated on {{GENERATED_DATE}}</p>
        </footer>
    </div>
</body>
</html>
"""
    
    # Generate search info HTML
    search_info_html = ""
    if search_params:
        search_info_html = '<div class="search-info">'
        for key, value in search_params.items():
            if value:
                search_info_html += f'<p><strong>{key.replace("_", " ").title()}:</strong> {value}</p>'
        search_info_html += '</div>'
    
    # Generate event cards
    event_cards_html = ""
    if events_data:
        for event in events_data:
            status_class = event['status'].lower()
            attendees_html = ''.join([f'<span class="attendee-tag">{att}</span>' for att in event['attendees'][:5]])
            if len(event['attendees']) > 5:
                attendees_html += f'<span class="attendee-tag">+{len(event["attendees"]) - 5} more</span>'
            
            description_html = f'<div class="event-description">{event["description"]}</div>' if event['description'] else ''
            location_html = f'<div class="detail-row"><span class="detail-icon">📍</span><span>{event["location"]}</span></div>' if event['location'] else ''
            
            event_cards_html += f"""
            <div class="event-card {status_class}">
                <span class="status-badge" style="background: {event['status_color']}">{event['status'].title()}</span>
                <div class="event-title">{event['title']}</div>
                <div class="event-time">
                    <div>⏰ Start: {event['start']}</div>
                    <div>⏰ End: {event['end']}</div>
                    {"<div>(All-day event)</div>" if event['is_all_day'] else ''}
                </div>
                {location_html}
                {description_html}
                <div class="event-attendees">
                    <div class="detail-row">
                        <span class="detail-icon">👥</span>
                        <div>{attendees_html}</div>
                    </div>
                    <div class="organizer-badge">🎯 Organizer: {event['organizer']}</div>
                </div>
                <a href="{event['html_link']}" target="_blank" class="view-link">
                    🔗 View in Calendar
                </a>
            </div>
            """
    else:
        event_cards_html = ""
    
    # No events message
    no_events_html = ""
    if not events_data:
        no_events_html = """
        <div class="no-events">
            <div class="empty-icon">📭</div>
            <h2>No events found</h2>
            <p>Try adjusting your search criteria or date range.</p>
        </div>
        """
    
    # Replace placeholders
    html_content = html_template.replace('{{EVENT_COUNT}}', str(len(events_data)))
    html_content = html_content.replace('{{SEARCH_INFO}}', search_info_html)
    html_content = html_content.replace('{{EVENT_CARDS}}', event_cards_html)
    html_content = html_content.replace('{{NO_EVENTS}}', no_events_html)
    html_content = html_content.replace('{{GENERATED_DATE}}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML page generated successfully: {output_file}")
    return output_file


def main():
    parser = argparse.ArgumentParser(description='Search Google Calendar events and generate HTML report')
    
    # Authentication
    parser.add_argument('--calendar-id', default='primary', help='Calendar ID (default: primary)')
    
    # Date range
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD or ISO format)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD or ISO format)')
    parser.add_argument('--days', type=int, help='Number of days from today')
    
    # Search criteria
    parser.add_argument('-q', '--query', help='Free text search query')
    parser.add_argument('--attendee', help='Filter by attendee email')
    parser.add_argument('--location', help='Filter by location')
    parser.add_argument('--status', choices=['confirmed', 'tentative', 'cancelled'], help='Filter by event status')
    
    # Output options
    parser.add_argument('--max-results', type=int, default=50, help='Maximum number of events (default: 50)')
    parser.add_argument('--order-by', choices=['startTime', 'updated'], default='startTime', help='Order by field')
    parser.add_argument('--output', default='calendar_events.html', help='Output HTML file name')
    parser.add_argument('--json', action='store_true', help='Also output JSON file')
    
    args = parser.parse_args()
    
    # Calculate date range
    time_min = None
    time_max = None
    
    if args.start_date:
        try:
            time_min = datetime.fromisoformat(args.start_date)
        except ValueError:
            time_min = datetime.strptime(args.start_date, '%Y-%m-%d')
    
    if args.end_date:
        try:
            time_max = datetime.fromisoformat(args.end_date)
        except ValueError:
            time_max = datetime.strptime(args.end_date, '%Y-%m-%d')
    
    if args.days and not args.start_date:
        time_min = datetime.now()
        time_max = time_min + timedelta(days=args.days)
    elif args.days and args.start_date:
        if time_min is None:
            time_min = datetime.now()
        time_max = time_min + timedelta(days=args.days)
    
    # Authenticate
    print("Authenticating with Google Calendar...")
    creds = authenticate()
    service = build('calendar', 'v3', credentials=creds)
    
    # Search for events
    print("Searching for events...")
    events = search_events(
        service,
        calendar_id=args.calendar_id,
        time_min=time_min,
        time_max=time_max,
        query=args.query,
        max_results=args.max_results,
        order_by=args.order_by,
        attendee_email=args.attendee,
        location=args.location,
        status=args.status
    )
    
    # Format events for HTML
    events_data = [format_event_for_html(event) for event in events]
    
    # Prepare search params for display
    search_params = {
        'calendar_id': args.calendar_id,
        'start_date': args.start_date or (time_min.strftime('%Y-%m-%d') if time_min else None),
        'end_date': args.end_date or (time_max.strftime('%Y-%m-%d') if time_max else None),
        'query': args.query,
        'attendee': args.attendee,
        'location': args.location,
        'status': args.status,
        'max_results': args.max_results
    }
    
    # Generate HTML
    generate_html(events_data, args.output, search_params)
    
    # Optionally generate JSON
    if args.json:
        json_file = args.output.replace('.html', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(events_data, f, indent=2, ensure_ascii=False)
        print(f"JSON file generated: {json_file}")
    
    print(f"\nFound {len(events)} event(s)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
