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
        
        return response
