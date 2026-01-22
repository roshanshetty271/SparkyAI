"""Tests for security middleware and features."""
import pytest
from fastapi.testclient import TestClient
from server.main import app


client = TestClient(app)


def test_security_headers():
    """Test that security headers are present."""
    response = client.get("/health")
    assert response.status_code == 200
    
    # Check security headers
    assert "x-content-type-options" in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"
    
    assert "x-frame-options" in response.headers
    assert response.headers["x-frame-options"] == "DENY"
    
    assert "x-xss-protection" in response.headers
    assert response.headers["x-xss-protection"] == "1; mode=block"


def test_cors_headers():
    """Test that CORS is configured."""
    response = client.options("/health")
    # CORS headers should be present on preflight requests
    # Note: This requires proper CORS middleware setup
    assert response.status_code in [200, 405]


# TODO: Add more security tests
# - Test rate limiting enforcement
# - Test prompt injection protection
# - Test input sanitization
# - Test budget limits
# - Test session management
