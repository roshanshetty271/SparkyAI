"""
SparkyAI Agent Core
===================

LangGraph-powered conversational agent with RAG capabilities.
"""

from agent_core.config import settings
from agent_core.graph import AgentGraph, create_agent_graph
from agent_core.state import AgentState

__version__ = "1.0.0"
__all__ = ["create_agent_graph", "AgentGraph", "AgentState", "settings"]
