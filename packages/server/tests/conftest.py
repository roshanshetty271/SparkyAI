"""Pytest configuration and fixtures for server tests."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
from server.main import app


@pytest.fixture
def client():
    """Create a test client for FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = "OK"
    mock.incrbyfloat.return_value = 1.0
    return mock


@pytest.fixture
def mock_agent_graph():
    """Create a mock AgentGraph."""
    mock = AsyncMock()
    mock.run.return_value = {
        "response": "Test response",
        "session_id": "test-session",
    }
    return mock


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket."""
    mock = AsyncMock()
    mock.accept = AsyncMock()
    mock.send_json = AsyncMock()
    mock.receive_json = AsyncMock()
    return mock
