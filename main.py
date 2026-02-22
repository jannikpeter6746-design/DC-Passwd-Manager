"""
Entry point: starts the Flask dashboard and the Discord bot concurrently.

Usage:
    python main.py

Environment:
    Copy .env.example to .env and fill in the required values.
"""

import os
import threading
from dotenv import load_dotenv

load_dotenv()

from dashboard import create_app
from bot import bot

# ---------------------------------------------------------------------------
# Initialise the database through the Flask app context
# ---------------------------------------------------------------------------

flask_app = create_app()

# ---------------------------------------------------------------------------
# Run Flask in a background thread
# ---------------------------------------------------------------------------


def run_dashboard():
    port = int(os.environ.get("DASHBOARD_PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)


dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
dashboard_thread.start()
print(f"Dashboard running on port {os.environ.get('DASHBOARD_PORT', 5000)}")

# ---------------------------------------------------------------------------
# Start the Discord bot (blocks the main thread)
# ---------------------------------------------------------------------------

token = os.environ.get("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN is not set. Copy .env.example to .env and fill in the values.")

bot.run(token)
