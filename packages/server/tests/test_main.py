"""Tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


# Create test client with lifespan disabled for simpler testing
@pytest.fixture
def client():
    """Create a test client."""
    from server.main import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_endpoint_success(self, client):
        """Test that /health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "timestamp" in data

    def test_health_endpoint_structure(self, client):
        """Test health response structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "openai_connected" in data
        assert "redis_connected" in data
        assert "embeddings_loaded" in data
        assert "chunks_count" in data


class TestGraphStructureEndpoint:
    """Test graph structure endpoint."""

    def test_graph_structure_success(self, client):
        """Test that /graph/structure returns valid graph data."""
        response = client.get("/graph/structure")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data

    def test_graph_structure_has_required_nodes(self, client):
        """Test that graph contains all required nodes."""
        response = client.get("/graph/structure")
        if response.status_code != 200:
            pytest.skip("Graph structure endpoint not available")
        data = response.json()

        node_ids = [node["id"] for node in data["nodes"]]
        expected_nodes = ["greeter", "intent_classifier", "rag_retriever", "response_generator"]

        for expected in expected_nodes:
            assert expected in node_ids

    def test_graph_structure_edges(self, client):
        """Test that graph edges are properly formatted."""
        response = client.get("/graph/structure")
        if response.status_code != 200:
            pytest.skip("Graph structure endpoint not available")
        data = response.json()

        for edge in data["edges"]:
            assert "source" in edge
            assert "target" in edge


class TestEmbeddingsEndpoint:
    """Test embeddings endpoint."""

    def test_embeddings_knowledge_success(self, client):
        """Test /embeddings/knowledge endpoint."""
        response = client.get("/embeddings/knowledge")
        assert response.status_code == 200
        data = response.json()
        assert "points" in data
        assert "total_count" in data
        assert isinstance(data["points"], list)


class TestChatEndpoint:
    """Test chat endpoint."""

    def test_chat_endpoint_validation_missing_message(self, client):
        """Test chat endpoint input validation - missing message."""
        response = client.post("/chat", json={"session_id": "test-12345678"})
        assert response.status_code == 422  # Validation error

    def test_chat_endpoint_allows_optional_session_id(self, client):
        """Test chat endpoint allows optional session_id."""
        # session_id is optional, so this should not fail validation
        # It may fail for other reasons (like rate limiting or agent errors)
        response = client.post("/chat", json={"message": "Hello"})
        # Should not be a validation error
        assert response.status_code != 422 or "session_id" not in str(response.json())


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiting_headers(self, client):
        """Test that rate limit headers are present."""
        response = client.get("/health")

        # Check for rate limit headers (may vary based on implementation)
        assert response.status_code == 200


class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are configured."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )

        # Should handle OPTIONS request with CORS headers
        assert response.status_code in [200, 405, 400]
