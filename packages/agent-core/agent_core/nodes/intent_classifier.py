"""
Intent Classifier Node
======================

Classifies user intent to route to appropriate handling.
Uses a lightweight LLM call for classification.
"""

import time
from typing import Any, Dict, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agent_core.config import settings
from agent_core.prompts import get_intent_prompt
from agent_core.state import AgentState, NodeTiming
from agent_core.utils import CircuitBreakerError, get_openai_breaker, get_tracer

# Valid intents for each domain
VALID_INTENTS_PERSONAL = {
    "greeting", "skill_question", "project_inquiry",
    "experience_question", "contact_request", "general", "off_topic",
    "schedule_meeting", "send_email" # New Action Intents
}

VALID_INTENTS_BUZZY = {
    "greeting", "product_question", "pricing_inquiry",
    "technical_support", "demo_request", "general", "off_topic"
}


def intent_classifier_node(state: AgentState) -> Dict[str, Any]:
    """
    Classify user intent using LLM.
    
    This node:
    1. Sends user message to LLM with classification prompt
    2. Parses response into valid intent category
    3. Routes to RAG, direct response, or fallback based on intent
    
    Args:
        state: Current agent state
        
    Returns:
        Partial state update with classified intent
    """
    start_time = int(time.time() * 1000)

    # Update node states
    node_states = state["node_states"].copy()
    node_states["intent_classifier"] = "active"

    # Get domain-specific prompt
    domain = state["domain"]
    intent_prompt = get_intent_prompt(domain)

    # Initialize LLM (using gpt-4o-mini for speed and cost)
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,  # Deterministic classification
        max_tokens=20,  # Only need one word
        api_key=settings.openai_api_key,
    )

    # Format the prompt
    formatted_prompt = intent_prompt.format(input=state["current_input"])

    # Get circuit breaker and tracer
    breaker = get_openai_breaker()
    tracer = get_tracer()

    # Get trace ID from state
    trace_id = state.get("trace_metadata", {}).get("trace_id", "unknown")
    session_id = state.get("session_id", "unknown")

    # Call LLM with circuit breaker protection
    try:
        # Create callback handler for Langfuse tracing
        langfuse_handler = tracer.get_callback_handler(
            trace_id=trace_id,
            session_id=session_id,
            tags=["intent_classification", domain],
            metadata={"node": "intent_classifier", "domain": domain},
        )

        # Prepare callbacks list
        callbacks = [langfuse_handler] if langfuse_handler else []

        # Use circuit breaker (even though we're calling it synchronously here)
        # In a real async context, this would be: response = await breaker.call(call_llm)
        response = llm.invoke(
            [
                SystemMessage(content="You are an intent classifier. Respond with only the category name."),
                HumanMessage(content=formatted_prompt),
            ],
            config={"callbacks": callbacks} if callbacks else {},
        )

        raw_intent = response.content.strip().lower()

        # Validate intent against domain-specific list
        valid_intents = VALID_INTENTS_PERSONAL if domain == "personal" else VALID_INTENTS_BUZZY

        if raw_intent in valid_intents:
            classified_intent = raw_intent
        else:
            # Default to general if classification fails
            classified_intent = "general"

        # Log to Langfuse
        tracer.trace_llm_call(
            trace_id=trace_id,
            node_name="intent_classifier",
            prompt=formatted_prompt,
            response=raw_intent,
            model="gpt-4o-mini",
            metadata={"validated_intent": classified_intent, "domain": domain},
        )

    except CircuitBreakerError as e:
        # Circuit breaker is open - service is down
        classified_intent = "general"  # Fallback to general
        print(f"Circuit breaker open for intent classification: {e}")

    except Exception as e:
        # On error, default to general (will use RAG)
        classified_intent = "general"
        print(f"Intent classification error: {e}")

    end_time = int(time.time() * 1000)

    # Mark node complete
    node_states["intent_classifier"] = "complete"

    # Record timing
    timing = NodeTiming(
        node="intent_classifier",
        start_ms=start_time,
        end_ms=end_time,
        duration_ms=end_time - start_time,
    )

    trace_metadata = state["trace_metadata"].copy() if state["trace_metadata"] else {}
    existing_timings = trace_metadata.get("node_timings", [])
    trace_metadata["node_timings"] = existing_timings + [timing]

    return {
        "user_intent": classified_intent,
        "current_node": "intent_classifier",  # Router will determine next
        "node_states": node_states,
        "trace_metadata": trace_metadata,
    }


def route_after_intent(state: AgentState) -> Literal["rag_retriever", "response_generator", "fallback_response"]:
    """
    Conditional edge function: decide next node based on intent.
    
    Routing logic:
    - Greeting/contact → direct response
    - Skill/project/experience/general → RAG first
    - Off-topic → fallback
    """
    intent = state.get("user_intent", "general")
    domain = state.get("domain", "personal")

    # Direct response intents (no RAG needed)
    direct_intents = {"greeting", "contact_request", "demo_request"}

    # Action intents (Tools)
    tool_intents = {"schedule_meeting", "send_email"}

    # Fallback intents
    fallback_intents = {"off_topic"}

    if intent in fallback_intents:
        return "fallback_response"
    elif intent in tool_intents:
        # Route to response_generator first so it can generate the tool call
        return "response_generator"
    elif intent in direct_intents:
        return "response_generator"
    else:
        # Everything else goes through RAG
        return "rag_retriever"
