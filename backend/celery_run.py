"""
Celery runner for distroless environments.
Ensures celery can be found and executed properly in the virtual environment.
Starts a health server for Cloud Run probes when running worker.
"""

import os
import sys

# Add virtual environment to Python path
sys.path.insert(0, "/home/venv/lib/python3.11/site-packages")

try:
    # Try importing celery to verify it's available
    from celery import Celery
    from celery.__main__ import main

    if __name__ == "__main__":
        # Check if this is a worker command that needs health server
        if "worker" in sys.argv:
            # Create Celery app for health checks
            app = Celery("dream_journal")
            app.config_from_object("celery_config")

            # Start health server on port 8080 (Cloud Run default)
            from health_server import start_health_server

            start_health_server(app, port=int(os.getenv("PORT", "8080")))
            print("Health server started for Celery worker", file=sys.stderr)

        # Remove the script name from argv so celery gets clean arguments
        sys.argv = ["celery"] + sys.argv[1:]
        sys.exit(main())

except ImportError as e:
    print(f"Error: Could not import celery: {e}", file=sys.stderr)
    print("Check that celery is installed in the virtual environment", file=sys.stderr)
    sys.exit(1)
