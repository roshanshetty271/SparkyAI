"""
Security middleware module.
Re-exports SecurityHeadersMiddleware from package init.
"""

from server.middleware import SecurityHeadersMiddleware

__all__ = ["SecurityHeadersMiddleware"]
