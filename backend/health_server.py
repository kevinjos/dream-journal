"""
Lightweight HTTP health server for Celery workers in Cloud Run.
Provides a /health endpoint that uses celery inspect ping to check worker status.
"""

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from celery import Celery

logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for health checks."""

    celery_app: Celery  # Class variable set by factory

    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path == "/health":
            self._handle_health_check()
        else:
            self._send_not_found()

    def _handle_health_check(self) -> None:
        """Check Celery worker health using inspect ping."""
        try:
            # Use celery inspect to ping workers
            # Note: timeout is set on the inspect object, not the ping method
            inspect = self.celery_app.control.inspect(timeout=5.0)
            pong = inspect.ping()

            if pong:
                # Worker responded to ping
                self._send_json_response(200, {"status": "healthy", "worker": pong})
            else:
                # No workers responded
                self._send_json_response(
                    503, {"status": "unhealthy", "error": "worker not responding"}
                )

        except Exception as exc:
            logger.error(f"Health check failed: {exc}")
            self._send_json_response(503, {"status": "unhealthy", "error": str(exc)})

    def _send_json_response(self, status_code: int, data: dict[str, Any]) -> None:
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_not_found(self) -> None:
        """Send 404 response."""
        self.send_response(404)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Not Found")

    def log_message(self, format: str, *args: object) -> None:
        """Override to use Python logging instead of stderr."""
        logger.info(f"Health server: {format % args}")


def start_health_server(celery_app: Celery, port: int = 8080) -> None:
    """Start the health server in a background daemon thread."""

    # Set the celery app on the handler class
    HealthHandler.celery_app = celery_app

    def run_server() -> None:
        try:
            server = HTTPServer(("0.0.0.0", port), HealthHandler)
            logger.info(f"Health server started on port {port}")
            server.serve_forever()
        except Exception as exc:
            logger.error(f"Health server failed: {exc}")

    # Start server in daemon thread - will live as long as Celery worker runs
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    logger.info("Health server thread started")
