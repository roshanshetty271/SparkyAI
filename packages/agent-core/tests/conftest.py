"""Pytest configuration and fixtures for agent-core tests."""
from unittest.mock import Mock

import pytest

from agent_core.state import AgentState


@pytest.fixture
def mock_agent_state() -> AgentState:
    """Create a mock AgentState for testing."""
    return {
        "conversation": [],
        "user_query": "test query",
        "current_node": "START",
        "user_intent": None,
        "rag_context": "",
        "retrieved_chunks": [],
        "retrieved_scores": [],
        "retrieval_confidence": 0.0,
        "query_embedding": None,
        "query_projection": None,
        "needs_rag": False,
        "response": "",
        "timestamp": "2026-01-22T00:00:00",
        "session_id": "test-session-123",
        "trace_id": None,
        "node_timings": {},
    }


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    mock = Mock()
    mock.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Test response"))]
    )
    return mock


@pytest.fixture
def mock_embedding_store():
    """Create a mock embedding store."""
    mock = Mock()
    mock.search.return_value = ([], [], 0.0)
    return mock
