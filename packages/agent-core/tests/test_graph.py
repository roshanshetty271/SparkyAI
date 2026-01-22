"""Tests for LangGraph agent flow."""
from unittest.mock import Mock, patch

import pytest

from agent_core.graph import AgentGraph
from agent_core.nodes.fallback import fallback_response_node
from agent_core.nodes.intent_classifier import intent_classifier_node, route_after_intent


class TestAgentGraph:
    """Test Agent Graph functionality."""

    def test_graph_initialization(self):
        """Test that AgentGraph initializes correctly."""
        graph = AgentGraph()
        assert graph is not None
        assert graph._graph is not None

    def test_graph_has_all_nodes(self):
        """Test that graph contains all required nodes."""
        graph = AgentGraph()
        node_names = [node for node in graph._graph.nodes]

        expected_nodes = [
            "greeter",
            "intent_classifier",
            "rag_retriever",
            "response_generator",
            "fallback_response",
        ]

        for expected in expected_nodes:
            assert expected in node_names, f"Missing node: {expected}"


class TestIntentClassifier:
    """Test intent classification node."""

    def test_route_after_intent_greeting(self):
        """Test routing for greeting intent."""
        state = {
            "user_intent": "greeting",
            "domain": "personal",
        }
        result = route_after_intent(state)
        assert result == "response_generator"

    def test_route_after_intent_off_topic(self):
        """Test routing for off-topic intent."""
        state = {
            "user_intent": "off_topic",
            "domain": "personal",
        }
        result = route_after_intent(state)
        assert result == "fallback_response"

    def test_route_after_intent_general(self):
        """Test routing for general intent."""
        state = {
            "user_intent": "general",
            "domain": "personal",
        }
        result = route_after_intent(state)
        assert result == "rag_retriever"

    def test_route_after_intent_skill_question(self):
        """Test routing for skill question."""
        state = {
            "user_intent": "skill_question",
            "domain": "personal",
        }
        result = route_after_intent(state)
        assert result == "rag_retriever"


class TestFallbackNode:
    """Test fallback response node."""

    def test_fallback_node_basic(self):
        """Test basic fallback response."""
        state = {
            "current_input": "Tell me about aliens",
            "domain": "personal",
            "node_states": {},
            "trace_metadata": {},
        }

        result = fallback_response_node(state)

        assert "response" in result
        assert len(result["response"]) > 0
        assert result["response_complete"] is True
        assert result["node_states"]["fallback_response"] == "complete"


class TestConversationMemory:
    """Test conversation memory integration."""

    def test_conversation_state_structure(self):
        """Test that conversation state has correct structure."""
        from agent_core.utils.token_counter import Message

        message: Message = {
            "role": "human",
            "content": "Hello",
        }

        assert message["role"] in ["human", "ai", "system"]
        assert isinstance(message["content"], str)


# Integration tests requiring API keys
@pytest.mark.skip(reason="Requires OpenAI API key")
class TestAgentIntegration:
    """Integration tests for full agent flow."""

    @pytest.mark.asyncio
    async def test_full_greeting_flow(self):
        """Test complete greeting flow through agent."""
        graph = AgentGraph()

        # TODO: Implement full integration test
        # This would require:
        # 1. Valid OpenAI API key
        # 2. Embeddings loaded
        # 3. Full state initialization
        pass

    @pytest.mark.asyncio
    async def test_full_rag_flow(self):
        """Test complete RAG flow through agent."""
        # TODO: Implement RAG integration test
        pass


# Mock-based tests
class TestAgentWithMocks:
    """Test agent behavior with mocked dependencies."""

    @patch('agent_core.nodes.intent_classifier.ChatOpenAI')
    def test_intent_classification_with_mock(self, mock_llm):
        """Test intent classification with mocked LLM."""
        # Setup mock
        mock_response = Mock()
        mock_response.content = "greeting"
        mock_llm.return_value.invoke.return_value = mock_response

        state = {
            "current_input": "Hi there!",
            "domain": "personal",
            "node_states": {},
            "trace_metadata": {},
        }

        result = intent_classifier_node(state)

        assert result["user_intent"] == "greeting"
        assert result["node_states"]["intent_classifier"] == "complete"
