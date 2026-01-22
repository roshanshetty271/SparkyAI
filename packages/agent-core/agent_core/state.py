"""
Agent State Schema for LangGraph.
Defines the complete state that flows through the agent graph.
"""

from typing import Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import BaseMessage


class QueryProjection(TypedDict):
    """2D projection of query embedding for visualization."""
    x: float
    y: float


class RetrievedChunk(TypedDict):
    """A single retrieved chunk from RAG."""
    id: str
    content: str
    source: str
    similarity: float
    metadata: Dict[str, Any]


class NodeTiming(TypedDict):
    """Timing information for a single node."""
    node: str
    start_ms: int
    end_ms: int
    duration_ms: int


class TraceMetadata(TypedDict):
    """Metadata for the current trace."""
    trace_id: str
    session_id: str
    started_at: str
    node_timings: List[NodeTiming]
    total_tokens: int
    estimated_cost_usd: float


class AgentState(TypedDict):
    """
    Complete state schema for the SparkyAI agent.
    
    This state flows through every node in the LangGraph and tracks:
    - Conversation history (with sliding window)
    - Current processing state (for visualization)
    - RAG retrieval results
    - Response generation
    - Observability metadata
    """

    # ============================================
    # Conversation State
    # ============================================

    # Full message history (sliding window, max 20 recent + summary of older)
    messages: List[BaseMessage]

    # Summary of older messages (when history exceeds max)
    conversation_summary: Optional[str]

    # The current user input being processed
    current_input: str

    # ============================================
    # Processing State (for visualization)
    # ============================================

    # Which node is currently executing
    current_node: str

    # Status of each node: pending | active | complete | error
    node_states: Dict[str, Literal["pending", "active", "complete", "error"]]

    # Classified user intent
    user_intent: Optional[Literal[
        "greeting",
        "skill_question",
        "project_inquiry",
        "experience_question",
        "contact_request",
        "general",
        "off_topic"
    ]]

    # ============================================
    # RAG State
    # ============================================

    # Retrieved chunks with metadata
    retrieved_chunks: List[RetrievedChunk]

    # Formatted context string for the LLM
    retrieved_context: Optional[str]

    # Highest similarity score from retrieval
    retrieval_confidence: float

    # All similarity scores (for embedding explorer visualization)
    retrieval_scores: List[float]

    # IDs of retrieved chunks (for embedding explorer)
    retrieved_chunk_ids: List[str]

    # 2D projection of query for embedding explorer
    query_projection: Optional[QueryProjection]

    # ============================================
    # Response State
    # ============================================

    # Final response text
    response: Optional[str]

    # Streaming tokens as they're generated
    streaming_tokens: List[str]

    # Whether response is complete
    response_complete: bool

    # ============================================
    # Metadata & Observability
    # ============================================

    # Trace metadata for Langfuse
    trace_metadata: Optional[TraceMetadata]

    # Error information if something failed
    error: Optional[str]

    # Domain config (personal vs buzzy)
    domain: Literal["personal", "buzzy"]


def create_initial_state(
    user_input: str,
    session_id: str,
    domain: Literal["personal", "buzzy"] = "personal",
    existing_messages: Optional[List[BaseMessage]] = None,
    conversation_summary: Optional[str] = None,
) -> AgentState:
    """
    Create a fresh agent state for a new user message.
    
    Args:
        user_input: The user's message
        session_id: Session identifier for tracking
        domain: Which persona to use
        existing_messages: Previous messages in this conversation
        conversation_summary: Summary of older messages if any
    
    Returns:
        Initialized AgentState ready for processing
    """
    import uuid
    from datetime import datetime, timezone

    return AgentState(
        # Conversation
        messages=existing_messages or [],
        conversation_summary=conversation_summary,
        current_input=user_input,

        # Processing
        current_node="start",
        node_states={
            "greeter": "pending",
            "intent_classifier": "pending",
            "rag_retriever": "pending",
            "response_generator": "pending",
            "fallback_response": "pending",
        },
        user_intent=None,

        # RAG
        retrieved_chunks=[],
        retrieved_context=None,
        retrieval_confidence=0.0,
        retrieval_scores=[],
        retrieved_chunk_ids=[],
        query_projection=None,

        # Response
        response=None,
        streaming_tokens=[],
        response_complete=False,

        # Metadata
        trace_metadata=TraceMetadata(
            trace_id=str(uuid.uuid4()),
            session_id=session_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            node_timings=[],
            total_tokens=0,
            estimated_cost_usd=0.0,
        ),
        error=None,
        domain=domain,
    )


def get_node_graph_data() -> Dict[str, Any]:
    """
    Return the static graph structure for D3.js visualization.
    This defines the nodes and edges of the agent graph.
    """
    return {
        "nodes": [
            {"id": "greeter", "label": "Greeter", "description": "Initial greeting check"},
            {"id": "intent_classifier", "label": "Intent", "description": "Classify user intent"},
            {"id": "rag_retriever", "label": "RAG", "description": "Retrieve relevant context"},
            {"id": "response_generator", "label": "Response", "description": "Generate answer"},
            {"id": "fallback_response", "label": "Fallback", "description": "Handle unknown queries"},
        ],
        "edges": [
            {"source": "greeter", "target": "intent_classifier"},
            {"source": "intent_classifier", "target": "rag_retriever", "label": "needs_context"},
            {"source": "intent_classifier", "target": "response_generator", "label": "direct"},
            {"source": "rag_retriever", "target": "response_generator", "label": "confident"},
            {"source": "rag_retriever", "target": "fallback_response", "label": "low_confidence"},
            {"source": "response_generator", "target": "end"},
            {"source": "fallback_response", "target": "end"},
        ],
    }
