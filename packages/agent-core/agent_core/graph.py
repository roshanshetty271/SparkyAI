"""
LangGraph Agent Graph
=====================

Defines the complete agent workflow as a StateGraph.
This is the main entry point for the agent.
"""

from typing import Any, AsyncIterator, Dict, Literal, Optional

from langgraph.graph import END, StateGraph

from agent_core.config import settings
from agent_core.nodes import (
    fallback_response_node,
    greeter_node,
    intent_classifier_node,
    rag_retriever_node,
    response_generator_node,
)
from agent_core.nodes.intent_classifier import route_after_intent
from agent_core.nodes.rag_retriever import route_after_rag
from agent_core.nodes.response_generator import response_generator_streaming
from agent_core.state import AgentState, create_initial_state, get_node_graph_data
from agent_core.utils import get_tracer


def create_agent_graph() -> StateGraph:
    """
    Create the LangGraph StateGraph for the agent.
    
    Graph structure:
        START → greeter → intent_classifier
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
              rag_retriever  response   fallback
                    │       generator
                    ▼          │          │
              ┌─────┴─────┐    │          │
              ▼           ▼    │          │
           response   fallback │          │
           generator     │     │          │
              │          │     │          │
              └──────────┴─────┴──────────┘
                               │
                              END
    
    Returns:
        Compiled StateGraph ready for invocation
    """

    # Create the graph with our state schema
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("greeter", greeter_node)
    graph.add_node("intent_classifier", intent_classifier_node)
    graph.add_node("rag_retriever", rag_retriever_node)
    graph.add_node("response_generator", response_generator_node)
    graph.add_node("fallback_response", fallback_response_node)

    # Set entry point
    graph.set_entry_point("greeter")

    # Add edges
    # Greeter always goes to intent classifier
    graph.add_edge("greeter", "intent_classifier")

    # Intent classifier routes conditionally
    graph.add_conditional_edges(
        "intent_classifier",
        route_after_intent,
        {
            "rag_retriever": "rag_retriever",
            "response_generator": "response_generator",
            "fallback_response": "fallback_response",
        }
    )

    # RAG retriever routes based on confidence
    graph.add_conditional_edges(
        "rag_retriever",
        route_after_rag,
        {
            "response_generator": "response_generator",
            "fallback_response": "fallback_response",
        }
    )

    # Terminal nodes go to END
    graph.add_edge("response_generator", END)
    graph.add_edge("fallback_response", END)

    return graph.compile()


class AgentGraph:
    """
    High-level wrapper for the agent graph with streaming support.
    
    Usage:
        agent = AgentGraph()
        
        # Non-streaming
        result = agent.invoke("Tell me about your React experience", session_id="abc123")
        
        # Streaming
        async for event in agent.stream("Tell me about your projects", session_id="abc123"):
            print(event)
    """

    def __init__(self, domain: Literal["personal", "buzzy"] = "personal"):
        """
        Initialize the agent graph.
        
        Args:
            domain: Which persona to use ("personal" for SparkyAI, "buzzy" for EasyBee)
        """
        self.domain = domain
        self._graph = create_agent_graph()
        self._sessions: Dict[str, AgentState] = {}

    def get_session_state(self, session_id: str) -> Optional[AgentState]:
        """Get the current state for a session."""
        return self._sessions.get(session_id)

    def clear_session(self, session_id: str) -> None:
        """Clear a session's state."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def invoke(
        self,
        user_input: str,
        session_id: str,
    ) -> AgentState:
        """
        Process a user message synchronously.
        
        Args:
            user_input: The user's message
            session_id: Session identifier
            
        Returns:
            Final agent state with response
        """
        # Get existing session or create new
        existing_state = self._sessions.get(session_id)

        # Create initial state for this invocation
        state = create_initial_state(
            user_input=user_input,
            session_id=session_id,
            domain=self.domain,
            existing_messages=existing_state["messages"] if existing_state else None,
            conversation_summary=existing_state.get("conversation_summary") if existing_state else None,
        )

        # Create Langfuse trace
        tracer = get_tracer()
        trace_id = state.get("trace_metadata", {}).get("trace_id", "unknown")
        if tracer.enabled:
            tracer.create_trace(
                trace_id=trace_id,
                session_id=session_id,
                user_input=user_input,
                metadata={"domain": self.domain},
            )

        # Run the graph
        result = self._graph.invoke(state)

        # Update Langfuse trace with output
        if tracer.enabled:
            tracer.update_trace(
                trace_id=trace_id,
                output=result.get("response", ""),
                metadata={
                    "domain": self.domain,
                    "intent": result.get("user_intent"),
                    "retrieval_confidence": result.get("retrieval_confidence"),
                    "total_tokens": result.get("trace_metadata", {}).get("total_tokens"),
                    "cost_usd": result.get("trace_metadata", {}).get("estimated_cost_usd"),
                },
                tags=[self.domain, result.get("user_intent", "unknown")],
            )
            tracer.flush()

        # Update session
        self._sessions[session_id] = result

        return result

    async def stream(
        self,
        user_input: str,
        session_id: str,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process a user message with streaming.
        
        Yields events for each state change and token.
        
        Args:
            user_input: The user's message
            session_id: Session identifier
            
        Yields:
            State change events and streaming tokens
        """
        # Get existing session
        existing_state = self._sessions.get(session_id)

        # Create initial state
        state = create_initial_state(
            user_input=user_input,
            session_id=session_id,
            domain=self.domain,
            existing_messages=existing_state["messages"] if existing_state else None,
            conversation_summary=existing_state.get("conversation_summary") if existing_state else None,
        )

        # Create Langfuse trace
        tracer = get_tracer()
        trace_id = state["trace_metadata"]["trace_id"]
        if tracer.enabled:
            tracer.create_trace(
                trace_id=trace_id,
                session_id=session_id,
                user_input=user_input,
                metadata={"domain": self.domain},
            )

        # Emit initial state
        yield {
            "event": "start",
            "payload": {
                "trace_id": trace_id,
                "session_id": session_id,
                "node_states": state["node_states"],
            }
        }

        # Run greeter
        greeter_update = greeter_node(state)
        state = {**state, **greeter_update}
        yield {
            "event": "node_complete",
            "payload": {
                "node": "greeter",
                "node_states": state["node_states"],
            }
        }

        # Run intent classifier
        yield {
            "event": "node_enter",
            "payload": {"node": "intent_classifier"}
        }

        intent_update = intent_classifier_node(state)
        state = {**state, **intent_update}

        yield {
            "event": "node_complete",
            "payload": {
                "node": "intent_classifier",
                "intent": state["user_intent"],
                "node_states": state["node_states"],
            }
        }

        # Route based on intent
        next_node = route_after_intent(state)

        if next_node == "rag_retriever":
            # Run RAG
            yield {
                "event": "node_enter",
                "payload": {"node": "rag_retriever"}
            }

            rag_update = rag_retriever_node(state)
            state = {**state, **rag_update}

            yield {
                "event": "rag_results",
                "payload": {
                    "node": "rag_retriever",
                    "confidence": state["retrieval_confidence"],
                    "chunk_ids": state["retrieved_chunk_ids"],
                    "scores": state["retrieval_scores"],
                    "query_projection": state["query_projection"],
                    "node_states": state["node_states"],
                }
            }

            # Route after RAG
            next_node = route_after_rag(state)

        # Generate response (streaming)
        if next_node == "response_generator":
            yield {
                "event": "node_enter",
                "payload": {"node": "response_generator"}
            }

            async for update in response_generator_streaming(state):
                state = {**state, **update}

                if "streaming_tokens" in update and update["streaming_tokens"]:
                    # Emit token event
                    yield {
                        "event": "token",
                        "payload": {
                            "token": update["streaming_tokens"][-1],
                            "full_response": state.get("response", ""),
                        }
                    }

                if update.get("response_complete"):
                    yield {
                        "event": "node_complete",
                        "payload": {
                            "node": "response_generator",
                            "node_states": state["node_states"],
                        }
                    }

        elif next_node == "fallback_response":
            yield {
                "event": "node_enter",
                "payload": {"node": "fallback_response"}
            }

            fallback_update = fallback_response_node(state)
            state = {**state, **fallback_update}

            yield {
                "event": "node_complete",
                "payload": {
                    "node": "fallback_response",
                    "node_states": state["node_states"],
                }
            }

            # Emit response as tokens for consistency
            yield {
                "event": "token",
                "payload": {
                    "token": state["response"],
                    "full_response": state["response"],
                }
            }

        # Update session
        self._sessions[session_id] = state

        # Update Langfuse trace with output
        if tracer.enabled:
            tracer.update_trace(
                trace_id=trace_id,
                output=state.get("response", ""),
                metadata={
                    "domain": self.domain,
                    "intent": state.get("user_intent"),
                    "retrieval_confidence": state.get("retrieval_confidence"),
                    "total_tokens": state.get("trace_metadata", {}).get("total_tokens"),
                    "cost_usd": state.get("trace_metadata", {}).get("estimated_cost_usd"),
                },
                tags=[self.domain, state.get("user_intent", "unknown")],
            )
            tracer.flush()

        # Emit completion
        yield {
            "event": "complete",
            "payload": {
                "trace_id": state["trace_metadata"]["trace_id"],
                "response": state["response"],
                "node_states": state["node_states"],
                "timings": state["trace_metadata"]["node_timings"],
                "total_tokens": state["trace_metadata"]["total_tokens"],
                "estimated_cost_usd": state["trace_metadata"]["estimated_cost_usd"],
            }
        }

    @staticmethod
    def get_graph_structure() -> Dict[str, Any]:
        """
        Get the static graph structure for D3.js visualization.
        
        Returns:
            Dict with nodes and edges for rendering
        """
        return get_node_graph_data()


# Convenience function for creating an agent
def create_agent(domain: Literal["personal", "buzzy"] = None) -> AgentGraph:
    """
    Create an agent instance.
    
    Args:
        domain: Persona to use. Defaults to settings.agent_config
        
    Returns:
        Configured AgentGraph instance
    """
    if domain is None:
        domain = settings.agent_config
    return AgentGraph(domain=domain)
