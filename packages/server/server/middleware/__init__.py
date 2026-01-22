"""
Security Headers Middleware
===========================

Adds security headers to all responses.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: Prevents MIME-type sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Enables browser XSS filtering
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Restricts browser features
    - Content-Security-Policy: Prevents XSS and data injection attacks
    - Strict-Transport-Security: Enforces HTTPS (production only)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response."""
        response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS filter (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser features
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # Content Security Policy - prevents XSS and injection attacks
        # This is a production-ready CSP that allows frontend to load necessary resources
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "  # Only load from same origin by default
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://d3js.org; "  # Allow scripts from self and D3.js CDN
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "  # Allow styles from self and Google Fonts
            "font-src 'self' https://fonts.gstatic.com; "  # Allow fonts from Google Fonts
            "img-src 'self' data: https:; "  # Allow images from self, data URIs, and HTTPS
            "connect-src 'self' https://api.openai.com https://cloud.langfuse.com wss:; "  # Allow API calls to OpenAI, Langfuse, and WebSocket
            "frame-ancestors 'none'; "  # Prevent embedding in iframes
            "base-uri 'self'; "  # Restrict base tag to same origin
            "form-action 'self'; "  # Only allow form submissions to same origin
            "upgrade-insecure-requests; "  # Upgrade HTTP to HTTPS automatically
        )

        # Strict Transport Security (HSTS) - enforce HTTPS
        # Note: Only add in production with HTTPS enabled
        # Uncomment when deploying with HTTPS:
        # response.headers["Strict-Transport-Security"] = (
        #     "max-age=31536000; includeSubDomains; preload"
        # )

        return response
