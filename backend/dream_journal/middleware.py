"""
Custom middleware for security headers.
"""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware to add security headers including Content Security Policy."""

    def process_response(
        self,
        request: HttpRequest,
        response: HttpResponse,
    ) -> HttpResponse:
        # Only add CSP headers if not in debug mode and not already set
        if not settings.DEBUG and "Content-Security-Policy" not in response:
            # Content Security Policy for XSS protection
            # This is restrictive but secure - adjust as needed for your app
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "object-src 'none'; "
                "base-uri 'self'"
            )
            response["Content-Security-Policy"] = csp_policy

            # Additional security headers
            response["X-Content-Type-Options"] = "nosniff"
            response["X-XSS-Protection"] = "1; mode=block"
            response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
