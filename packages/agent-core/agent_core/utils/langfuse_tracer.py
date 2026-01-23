"""Langfuse tracing utilities for SparkyAI agent.

This module provides decorators and context managers for comprehensive
observability of the agent workflow using Langfuse.
"""

import time
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Dict, Optional, ParamSpec, TypeVar

from langfuse import Langfuse
try:
    from langfuse.langchain import CallbackHandler
except ImportError:
    CallbackHandler = None

from agent_core.config import settings

# Type variables for generic decorators
P = ParamSpec('P')
T = TypeVar('T')


class LangfuseTracer:
    """Centralized Langfuse tracing for the SparkyAI agent."""

    def __init__(self):
        """Initialize Langfuse client if configured."""
        self._client: Optional[Langfuse] = None
        self._enabled = settings.langfuse_enabled

        if self._enabled:
            try:
                self._client = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
                print(f"✅ Langfuse tracing enabled (host: {settings.langfuse_host})")
            except Exception as e:
                print(f"⚠️ Failed to initialize Langfuse: {e}")
                self._enabled = False
                self._client = None
        else:
            print("ℹ️ Langfuse tracing disabled (no API keys configured)")

    @property
    def enabled(self) -> bool:
        """Check if Langfuse is enabled and configured."""
        return self._enabled and self._client is not None

    @property
    def client(self) -> Optional[Langfuse]:
        """Get the Langfuse client instance."""
        return self._client

    def get_callback_handler(
        self,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[CallbackHandler]:
        """
        Create a LangChain callback handler for Langfuse.
        
        Use this with LangChain LLM calls to automatically trace them.
        
        Args:
            trace_id: Unique trace identifier
            session_id: Session identifier
            user_id: User identifier
            tags: Tags for categorization
            metadata: Additional metadata
            
        Returns:
            CallbackHandler instance if Langfuse is enabled, else None
        """
        if not self.enabled:
            return None

        try:
            return CallbackHandler(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
                trace_id=trace_id,
                session_id=session_id,
                user_id=user_id,
                tags=tags or [],
                metadata=metadata or {},
            )
        except Exception as e:
            print(f"⚠️ Failed to create Langfuse callback handler: {e}")
            return None

    @contextmanager
    def trace_node(
        self,
        node_name: str,
        trace_id: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Context manager for tracing a graph node execution.
        
        Usage:
            with tracer.trace_node("intent_classifier", trace_id, session_id):
                # Node execution code
                result = classify_intent(input)
        
        Args:
            node_name: Name of the node being executed
            trace_id: Trace identifier
            session_id: Session identifier
            metadata: Additional metadata to log
        """
        if not self.enabled:
            yield None
            return

        start_time = time.time()
        span = None

        try:
            # Create a span for this node
            span = self._client.span(
                name=node_name,
                trace_id=trace_id,
                metadata={
                    "node": node_name,
                    "session_id": session_id,
                    **(metadata or {}),
                },
            )
            yield span
        except Exception as e:
            if span:
                span.update(
                    level="ERROR",
                    status_message=str(e),
                )
            raise
        finally:
            if span:
                end_time = time.time()
                span.update(
                    end_time=end_time,
                    metadata={
                        "duration_ms": int((end_time - start_time) * 1000),
                        **(metadata or {}),
                    },
                )

    @asynccontextmanager
    async def trace_node_async(
        self,
        node_name: str,
        trace_id: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Async context manager for tracing a graph node execution.
        
        Usage:
            async with tracer.trace_node_async("response_generator", trace_id, session_id):
                # Async node execution
                result = await generate_response(input)
        
        Args:
            node_name: Name of the node being executed
            trace_id: Trace identifier
            session_id: Session identifier
            metadata: Additional metadata to log
        """
        if not self.enabled:
            yield None
            return

        start_time = time.time()
        span = None

        try:
            # Create a span for this node
            span = self._client.span(
                name=node_name,
                trace_id=trace_id,
                metadata={
                    "node": node_name,
                    "session_id": session_id,
                    **(metadata or {}),
                },
            )
            yield span
        except Exception as e:
            if span:
                span.update(
                    level="ERROR",
                    status_message=str(e),
                )
            raise
        finally:
            if span:
                end_time = time.time()
                span.update(
                    end_time=end_time,
                    metadata={
                        "duration_ms": int((end_time - start_time) * 1000),
                        **(metadata or {}),
                    },
                )

    def trace_rag_retrieval(
        self,
        trace_id: str,
        query: str,
        results: list,
        scores: list[float],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log a RAG retrieval operation to Langfuse.
        
        Args:
            trace_id: Trace identifier
            query: The search query
            results: Retrieved documents/chunks
            scores: Similarity scores
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        try:
            self._client.span(
                name="rag_retrieval",
                trace_id=trace_id,
                input={"query": query},
                output={
                    "results_count": len(results),
                    "top_score": max(scores) if scores else 0,
                    "avg_score": sum(scores) / len(scores) if scores else 0,
                },
                metadata={
                    "results": [
                        {"content": r[:100], "score": s}
                        for r, s in zip(results[:5], scores[:5])  # First 5 results
                    ],
                    **(metadata or {}),
                },
            )
        except Exception as e:
            print(f"⚠️ Failed to log RAG retrieval to Langfuse: {e}")

    def trace_llm_call(
        self,
        trace_id: str,
        node_name: str,
        prompt: str,
        response: str,
        model: str,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log an LLM call to Langfuse.
        
        Args:
            trace_id: Trace identifier
            node_name: Node making the LLM call
            prompt: Input prompt
            response: LLM response
            model: Model used
            tokens_used: Total tokens used
            cost_usd: Estimated cost
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        try:
            self._client.generation(
                name=f"{node_name}_llm",
                trace_id=trace_id,
                input=prompt,
                output=response,
                model=model,
                usage={
                    "total_tokens": tokens_used,
                } if tokens_used else None,
                metadata={
                    "node": node_name,
                    "cost_usd": cost_usd,
                    **(metadata or {}),
                },
            )
        except Exception as e:
            print(f"⚠️ Failed to log LLM call to Langfuse: {e}")

    def create_trace(
        self,
        trace_id: str,
        session_id: str,
        user_input: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Create a new trace in Langfuse.
        
        Args:
            trace_id: Unique trace identifier
            session_id: Session identifier
            user_input: User's input message
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        try:
            self._client.trace(
                id=trace_id,
                session_id=session_id,
                input=user_input,
                metadata=metadata or {},
            )
        except Exception as e:
            print(f"⚠️ Failed to create Langfuse trace: {e}")

    def update_trace(
        self,
        trace_id: str,
        output: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
    ):
        """
        Update an existing trace with output and metadata.
        
        Args:
            trace_id: Trace identifier
            output: Final output
            metadata: Additional metadata
            tags: Tags for categorization
        """
        if not self.enabled:
            return

        try:
            trace = self._client.trace(id=trace_id)
            update_data = {}

            if output is not None:
                update_data["output"] = output
            if metadata is not None:
                update_data["metadata"] = metadata
            if tags is not None:
                update_data["tags"] = tags

            if update_data:
                trace.update(**update_data)
        except Exception as e:
            print(f"⚠️ Failed to update Langfuse trace: {e}")

    def flush(self):
        """Flush all pending traces to Langfuse."""
        if self.enabled and self._client:
            try:
                self._client.flush()
            except Exception as e:
                print(f"⚠️ Failed to flush Langfuse traces: {e}")


# Global tracer instance
_tracer: Optional[LangfuseTracer] = None


def get_tracer() -> LangfuseTracer:
    """Get the global Langfuse tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = LangfuseTracer()
    return _tracer


def reset_tracer():
    """Reset the global tracer (useful for testing)."""
    global _tracer
    _tracer = None
