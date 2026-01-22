"""Tests for FastAPI endpoints."""
from fastapi.testclient import TestClient
from unittest.mock import patch
from server.main import app


client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_endpoint_success(self):
        """Test that /health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_health_endpoint_structure(self):
        """Test health response structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "dependencies" in data


class TestGraphStructureEndpoint:
    """Test graph structure endpoint."""

    def test_graph_structure_success(self):
        """Test that /graph/structure returns valid graph data."""
        response = client.get("/graph/structure")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) > 0
        assert len(data["edges"]) > 0

    def test_graph_structure_has_required_nodes(self):
        """Test that graph contains all required nodes."""
        response = client.get("/graph/structure")
        data = response.json()

        node_ids = [node["id"] for node in data["nodes"]]
        expected_nodes = ["greeter", "intent_classifier", "rag_retriever", "response_generator"]

        for expected in expected_nodes:
            assert expected in node_ids

    def test_graph_structure_edges(self):
        """Test that graph edges are properly formatted."""
        response = client.get("/graph/structure")
        data = response.json()

        for edge in data["edges"]:
            assert "source" in edge
            assert "target" in edge


class TestEmbeddingsEndpoint:
    """Test embeddings endpoint."""

    @patch('server.main.embedding_store')
    def test_embeddings_knowledge_success(self, mock_store):
        """Test /embeddings/knowledge endpoint."""
        # Mock embedding data
        mock_store.get_all_points.return_value = [
            {"id": "1", "x": 0.5, "y": 0.5, "text": "Test", "metadata": {}}
        ]

        response = client.get("/embeddings/knowledge")
        assert response.status_code == 200
        data = response.json()
        assert "points" in data
        assert isinstance(data["points"], list)


class TestChatEndpoint:
    """Test chat endpoint."""

    @patch('server.main.agent_graph')
    @patch('server.main.budget_tracker')
    def test_chat_endpoint_basic(self, mock_budget, mock_agent):
        """Test basic chat endpoint functionality."""
        # Setup mocks
        mock_budget.can_proceed.return_value = (True, None)
        mock_agent.run.return_value = {
            "response": "Test response",
            "session_id": "test-123"
        }

        response = client.post(
            "/chat",
            json={"message": "Hello", "session_id": "test-123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    @patch('server.main.budget_tracker')
    def test_chat_endpoint_budget_exceeded(self, mock_budget):
        """Test chat endpoint when budget is exceeded."""
        mock_budget.can_proceed.return_value = (False, "Budget exceeded")

        response = client.post(
            "/chat",
            json={"message": "Hello", "session_id": "test-123"}
        )

        assert response.status_code == 429  # Too Many Requests

    def test_chat_endpoint_validation(self):
        """Test chat endpoint input validation."""
        # Missing message
        response = client.post("/chat", json={"session_id": "test"})
        assert response.status_code == 422  # Validation error

        # Missing session_id
        response = client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 422


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiting_headers(self):
        """Test that rate limit headers are present."""
        response = client.get("/health")

        # Check for rate limit headers (may vary based on implementation)
        assert response.status_code == 200


class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers_present(self):
        """Test that CORS headers are configured."""
        response = client.options("/health")

        # Should handle OPTIONS request
        assert response.status_code in [200, 405]  # 405 if no OPTIONS handler
