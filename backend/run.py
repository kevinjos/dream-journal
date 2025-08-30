"""
Gunicorn runner for distroless environments with Cloud Run PORT support.
"""

import os
import sys

from gunicorn.app.wsgiapp import run

if __name__ == "__main__":
    # Cloud Run sets PORT environment variable
    port = os.environ.get("PORT", "8000")

    # If no explicit bind argument provided, add PORT-based binding
    if not any(arg.startswith("--bind") for arg in sys.argv[1:]):
        sys.argv.extend(["--bind", f"0.0.0.0:{port}"])

    sys.exit(run())
