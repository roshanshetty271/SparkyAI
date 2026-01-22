"""Tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from server.main import app


client = TestClient(app)


def test_health_endpoint():
    """Test that /health endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_graph_structure_endpoint():
    """Test that /graph/structure returns valid graph data."""
    response = client.get("/graph/structure")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0


# TODO: Add more endpoint tests
# - Test /chat endpoint with mock AgentGraph
# - Test /embeddings/knowledge endpoint
# - Test WebSocket connection
# - Test rate limiting
# - Test budget protection
# - Test error handling
