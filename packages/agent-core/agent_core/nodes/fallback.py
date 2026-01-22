"""
Fallback Response Node
======================

Handles queries where:
- RAG retrieval confidence is too low
- User intent is off-topic
- Something went wrong in the pipeline
"""

import time
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from agent_core.state import AgentState, NodeTiming
from agent_core.config import settings
from agent_core.prompts import get_fallback_prompt, get_system_prompt


# Pre-defined fallback responses for common scenarios
FALLBACK_RESPONSES = {
    "personal": {
        "off_topic": """I appreciate your question, but I'm specifically designed to help you learn about Roshan Shetty's professional background. 

I can help you with:
• His technical skills (React, D3.js, FastAPI, LangGraph)
• Work experience at Aosenuma AI and Capgemini
• Projects he's built
• Education at Northeastern University
• How to get in touch with him

What would you like to know?""",
        
        "low_confidence": """I don't have specific information about that in my knowledge base, but I'd be happy to help you with:

• Roshan's technical expertise and skills
• His professional experience
• Projects and portfolio work
• His educational background

Or feel free to reach out to Roshan directly at his email for more specific questions!""",
        
        "error": """I apologize, but I'm having a bit of trouble right now. Please try again in a moment, or reach out to Roshan directly if you need immediate assistance.""",
    },
    
    "buzzy": {
        "off_topic": """I'm Buzzy, EasyBee AI's assistant! I'm here to help with storage and organization questions.

I can help you with:
• How EasyBee's AI-powered storage works
• Product features and capabilities
• Getting started with a demo
• Pricing and plans

What would you like to know about EasyBee?""",
        
        "low_confidence": """I don't have specific details about that, but I'd be happy to help with:

• EasyBee's AI organization features
• How semantic search works
• Product demos and trials
• Connecting you with our team

What can I help you with?""",
        
        "error": """I apologize, but I'm having trouble processing that right now. Please try again, or I can connect you with the EasyBee team for assistance.""",
    },
}


def fallback_response_node(state: AgentState) -> Dict[str, Any]:
    """
    Generate a fallback response when normal processing fails.
    
    This node handles:
    - Off-topic queries (polite redirect)
    - Low RAG confidence (suggest alternatives)
    - Errors (graceful degradation)
    
    Args:
        state: Current agent state
        
    Returns:
        Partial state update with fallback response
    """
    start_time = int(time.time() * 1000)
    
    # Update node states
    node_states = state["node_states"].copy()
    node_states["fallback_response"] = "active"
    
    domain = state["domain"]
    intent = state.get("user_intent", "general")
    retrieval_confidence = state.get("retrieval_confidence", 0.0)
    error = state.get("error")
    
    # Determine fallback type
    if error:
        fallback_type = "error"
    elif intent == "off_topic":
        fallback_type = "off_topic"
    elif retrieval_confidence < settings.rag_similarity_threshold:
        fallback_type = "low_confidence"
    else:
        fallback_type = "low_confidence"
    
    # Try to generate a contextual fallback using LLM
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=200,
            api_key=settings.openai_api_key,
        )
        
        fallback_prompt = get_fallback_prompt(domain).format(
            input=state["current_input"]
        )
        
        response = llm.invoke([
            SystemMessage(content=get_system_prompt(domain)),
            HumanMessage(content=fallback_prompt),
        ])
        
        response_text = response.content
        
    except Exception:
        # Use pre-defined fallback if LLM fails
        response_text = FALLBACK_RESPONSES.get(domain, {}).get(
            fallback_type, 
            FALLBACK_RESPONSES["personal"]["error"]
        )
    
    end_time = int(time.time() * 1000)
    
    # Mark node complete
    node_states["fallback_response"] = "complete"
    
    # Record timing
    timing = NodeTiming(
        node="fallback_response",
        start_ms=start_time,
        end_ms=end_time,
        duration_ms=end_time - start_time,
    )
    
    trace_metadata = state["trace_metadata"].copy() if state["trace_metadata"] else {}
    existing_timings = trace_metadata.get("node_timings", [])
    trace_metadata["node_timings"] = existing_timings + [timing]
    
    # Add to message history
    new_messages = list(state.get("messages", []))
    new_messages.append(HumanMessage(content=state["current_input"]))
    new_messages.append(AIMessage(content=response_text))
    
    return {
        "response": response_text,
        "response_complete": True,
        "messages": new_messages,
        "current_node": "end",
        "node_states": node_states,
        "trace_metadata": trace_metadata,
    }
