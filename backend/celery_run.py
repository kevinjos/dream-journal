"""
Celery runner for distroless environments.
Ensures celery can be found and executed properly in the virtual environment.
"""

import sys

# Add virtual environment to Python path
sys.path.insert(0, "/home/venv/lib/python3.11/site-packages")

try:
    # Try importing celery to verify it's available
    from celery.__main__ import main

    if __name__ == "__main__":
        # Remove the script name from argv so celery gets clean arguments
        sys.argv = ["celery"] + sys.argv[1:]
        sys.exit(main())

except ImportError as e:
    print(f"Error: Could not import celery: {e}", file=sys.stderr)
    print("Check that celery is installed in the virtual environment", file=sys.stderr)
    sys.exit(1)
