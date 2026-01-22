"""Tests for LangGraph agent flow."""
import pytest
from agent_core.graph import AgentGraph
from agent_core.state import AgentState


@pytest.mark.asyncio
async def test_graph_initialization():
    """Test that AgentGraph initializes correctly."""
    graph = AgentGraph()
    assert graph is not None
    assert graph.graph is not None


@pytest.mark.asyncio
async def test_greeting_flow():
    """Test that greeting node works correctly."""
    graph = AgentGraph()
    initial_state: AgentState = {
        "conversation": [],
        "user_query": "",
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
        "timestamp": "",
        "session_id": "test-session",
        "trace_id": None,
        "node_timings": {},
    }
    
    # This test requires mocking or a full setup
    # For now, just verify the graph structure
    assert "greeter" in [node for node in graph.graph.nodes]


# TODO: Add more comprehensive tests
# - Test intent classification
# - Test RAG retrieval
# - Test response generation
# - Test fallback handling
# - Test error scenarios
