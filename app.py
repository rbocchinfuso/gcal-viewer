from flask import Flask, send_from_directory
import os
import subprocess
import schedule
import threading
import time

app = Flask(__name__)

HTML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(HTML_DIR, exist_ok=True)

def run_calendar_search():
    """Runs the calendar searcher script."""
    print("Running calendar search...")
    # Adjust query as needed, or pass via environment variable
    query = os.getenv('SEARCH_QUERY', 'moto')
    days = os.getenv('SEARCH_DAYS', '30')
    
    cmd = [
        'python', 'calendar_searcher_html.py',
        '-q', query,
        '--days', days,
        '--output', os.path.join(HTML_DIR, 'index.html')
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Calendar search completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running calendar search: {e}")

def scheduler_thread():
    """Background thread to run the scheduler."""
    # Run once immediately on startup
    run_calendar_search()
    
    # Schedule daily runs
    schedule.every().day.at("08:00").do(run_calendar_search)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

@app.route('/')
def serve_html():
    return send_from_directory(HTML_DIR, 'index.html')

@app.route('/static/<path:path>')
def send_static(path):
    # If you add CSS/JS later, this helps serve them if referenced relatively
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Start scheduler in background
    t = threading.Thread(target=scheduler_thread, daemon=True)
    t.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
