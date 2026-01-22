"""
Greeter Node
============

First node in the pipeline. Checks if the message is a simple greeting
and prepares state for the intent classifier.
"""

import time
from typing import Dict, Any

from agent_core.state import AgentState, NodeTiming


def greeter_node(state: AgentState) -> Dict[str, Any]:
    """
    Process incoming message and prepare for intent classification.
    
    This node:
    1. Marks itself as active (for visualization)
    2. Does lightweight preprocessing
    3. Passes to intent classifier
    
    Args:
        state: Current agent state
        
    Returns:
        Partial state update with node status
    """
    start_time = int(time.time() * 1000)
    
    # Update node states for visualization
    node_states = state["node_states"].copy()
    node_states["greeter"] = "complete"
    
    end_time = int(time.time() * 1000)
    
    # Record timing
    timing = NodeTiming(
        node="greeter",
        start_ms=start_time,
        end_ms=end_time,
        duration_ms=end_time - start_time,
    )
    
    # Update trace metadata
    trace_metadata = state["trace_metadata"].copy() if state["trace_metadata"] else {}
    existing_timings = trace_metadata.get("node_timings", [])
    trace_metadata["node_timings"] = existing_timings + [timing]
    
    return {
        "current_node": "intent_classifier",
        "node_states": node_states,
        "trace_metadata": trace_metadata,
    }
