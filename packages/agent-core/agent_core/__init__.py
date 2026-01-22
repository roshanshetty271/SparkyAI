"""
SparkyAI Agent Core
===================

LangGraph-powered conversational agent with RAG capabilities.
"""

from agent_core.graph import create_agent_graph, AgentGraph
from agent_core.state import AgentState
from agent_core.config import settings

__version__ = "1.0.0"
__all__ = ["create_agent_graph", "AgentGraph", "AgentState", "settings"]
