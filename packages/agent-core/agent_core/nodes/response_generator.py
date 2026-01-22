"""
Response Generator Node
=======================

Generates the final response using LLM with context from RAG.
Supports streaming for real-time token delivery.
"""

import time
from typing import Any, AsyncIterator, Callable, Dict, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agent_core.config import settings
from agent_core.prompts import (
    get_greeting_prompt,
    get_response_prompt,
    get_system_prompt,
)
from agent_core.state import AgentState, NodeTiming
from agent_core.utils import (
    CircuitBreakerError,
    get_openai_breaker,
    get_token_counter,
    get_tracer,
    get_window_manager,
)


def response_generator_node(state: AgentState) -> Dict[str, Any]:
    """
    Generate response using LLM (non-streaming version).
    
    For streaming, use response_generator_streaming instead.
    
    Args:
        state: Current agent state
        
    Returns:
        Partial state update with generated response
    """
    start_time = int(time.time() * 1000)

    # Update node states
    node_states = state["node_states"].copy()
    node_states["response_generator"] = "active"

    domain = state["domain"]
    intent = state.get("user_intent", "general")

    # Initialize LLM
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.7,
        max_tokens=500,
        api_key=settings.openai_api_key,
    )

    # Get token counter and window manager
    token_counter = get_token_counter(model=settings.openai_model)
    window_manager = get_window_manager(
        max_tokens=settings.max_conversation_tokens,
        model=settings.openai_model,
    )

    # Build messages
    system_prompt = get_system_prompt(domain)
    messages = [SystemMessage(content=system_prompt)]

    # Calculate tokens for system prompt and context
    system_tokens = token_counter.count_tokens(system_prompt)
    context_text = state.get("retrieved_context") or ""
    context_tokens = token_counter.count_tokens(context_text) if context_text else 0

    # Truncate conversation history if needed
    history = state.get("messages", [])
    if history:
        # Convert LangChain messages to Message dicts for token counting
        history_dicts = [
            {"role": msg.type, "content": msg.content}
            for msg in history
        ]
        truncated_history = window_manager.truncate_conversation(
            history_dicts,
            system_prompt_tokens=system_tokens,
            rag_context_tokens=context_tokens,
        )
        # Convert back to LangChain messages
        for msg_dict in truncated_history:
            if msg_dict["role"] == "human":
                messages.append(HumanMessage(content=msg_dict["content"]))
            elif msg_dict["role"] == "ai":
                messages.append(AIMessage(content=msg_dict["content"]))
    else:
        messages.extend(history)

    # Build the user prompt based on intent
    if intent == "greeting":
        prompt = get_greeting_prompt(domain).format(input=state["current_input"])
    else:
        context = state.get("retrieved_context") or "No specific context available."
        prompt = get_response_prompt(domain).format(
            context=context,
            input=state["current_input"],
        )

    messages.append(HumanMessage(content=prompt))

    # Generate response with circuit breaker protection
    breaker = get_openai_breaker()
    tracer = get_tracer()
    trace_id = state.get("trace_metadata", {}).get("trace_id", "unknown")
    session_id = state.get("session_id", "unknown")

    try:
        # Create callback handler for Langfuse tracing
        langfuse_handler = tracer.get_callback_handler(
            trace_id=trace_id,
            session_id=session_id,
            tags=["response_generation", domain, intent],
            metadata={"node": "response_generator", "domain": domain, "intent": intent},
        )

        # Prepare callbacks list
        callbacks = [langfuse_handler] if langfuse_handler else []

        response = llm.invoke(
            messages,
            config={"callbacks": callbacks} if callbacks else {},
        )
        response_text = response.content

        # Count actual tokens used
        input_tokens = token_counter.count_messages_tokens([
            {"role": "system", "content": system_prompt},
            *[{"role": msg.type, "content": msg.content} for msg in messages[1:]],
            {"role": "user", "content": prompt},
        ])
        output_tokens = token_counter.count_tokens(response_text)
        total_tokens = input_tokens + output_tokens

    except CircuitBreakerError:
        response_text = (
            "I apologize, but I'm temporarily unable to process your request. "
            "Our AI service is experiencing high load. Please try again in a moment."
        )
        total_tokens = 0

    except Exception:
        response_text = (
            "I apologize, but I'm having trouble generating a response right now. "
            "Please try again in a moment."
        )
        total_tokens = 0

    end_time = int(time.time() * 1000)

    # Mark node complete
    node_states["response_generator"] = "complete"

    # Record timing
    timing = NodeTiming(
        node="response_generator",
        start_ms=start_time,
        end_ms=end_time,
        duration_ms=end_time - start_time,
    )

    trace_metadata = state["trace_metadata"].copy() if state["trace_metadata"] else {}
    existing_timings = trace_metadata.get("node_timings", [])
    trace_metadata["node_timings"] = existing_timings + [timing]
    trace_metadata["total_tokens"] = trace_metadata.get("total_tokens", 0) + total_tokens

    # Estimate cost (GPT-4o-mini pricing: ~$0.15/1M input, $0.60/1M output)
    estimated_cost = (total_tokens / 1_000_000) * 0.40  # Rough average
    trace_metadata["estimated_cost_usd"] = trace_metadata.get("estimated_cost_usd", 0) + estimated_cost

    # Add AI message to history
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


async def response_generator_streaming(
    state: AgentState,
    on_token: Optional[Callable[[str], None]] = None,
) -> AsyncIterator[Dict[str, Any]]:
    """
    Generate response with streaming support.
    
    Yields partial state updates as tokens are generated.
    
    Args:
        state: Current agent state
        on_token: Optional callback for each token
        
    Yields:
        Partial state updates with streaming tokens
    """
    start_time = int(time.time() * 1000)

    # Update node states
    node_states = state["node_states"].copy()
    node_states["response_generator"] = "active"

    yield {
        "current_node": "response_generator",
        "node_states": node_states,
    }

    domain = state["domain"]
    intent = state.get("user_intent", "general")

    # Get token counter and window manager
    token_counter = get_token_counter(model=settings.openai_model)
    window_manager = get_window_manager(
        max_tokens=settings.max_conversation_tokens,
        model=settings.openai_model,
    )

    # Initialize streaming LLM
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.7,
        max_tokens=500,
        api_key=settings.openai_api_key,
        streaming=True,
    )

    # Build messages
    system_prompt = get_system_prompt(domain)
    messages = [SystemMessage(content=system_prompt)]

    # Calculate tokens for system prompt and context
    system_tokens = token_counter.count_tokens(system_prompt)
    context_text = state.get("retrieved_context") or ""
    context_tokens = token_counter.count_tokens(context_text) if context_text else 0

    # Truncate conversation history if needed
    history = state.get("messages", [])
    if history:
        # Convert LangChain messages to Message dicts for token counting
        history_dicts = [
            {"role": msg.type, "content": msg.content}
            for msg in history
        ]
        truncated_history = window_manager.truncate_conversation(
            history_dicts,
            system_prompt_tokens=system_tokens,
            rag_context_tokens=context_tokens,
        )
        # Convert back to LangChain messages
        for msg_dict in truncated_history:
            if msg_dict["role"] == "human":
                messages.append(HumanMessage(content=msg_dict["content"]))
            elif msg_dict["role"] == "ai":
                messages.append(AIMessage(content=msg_dict["content"]))
    else:
        messages.extend(history)

    # Build the user prompt
    if intent == "greeting":
        prompt = get_greeting_prompt(domain).format(input=state["current_input"])
    else:
        context = state.get("retrieved_context") or "No specific context available."
        prompt = get_response_prompt(domain).format(
            context=context,
            input=state["current_input"],
        )

    messages.append(HumanMessage(content=prompt))

    # Stream response with circuit breaker protection
    full_response = ""
    streaming_tokens = []
    breaker = get_openai_breaker()
    tracer = get_tracer()
    trace_id = state.get("trace_metadata", {}).get("trace_id", "unknown")
    session_id = state.get("session_id", "unknown")

    # Count input tokens accurately
    input_tokens = token_counter.count_messages_tokens([
        {"role": "system", "content": system_prompt},
        *[{"role": msg.type, "content": msg.content} for msg in messages[1:]],
        {"role": "user", "content": prompt},
    ])

    try:
        # Create callback handler for Langfuse tracing
        langfuse_handler = tracer.get_callback_handler(
            trace_id=trace_id,
            session_id=session_id,
            tags=["response_generation", "streaming", domain, intent],
            metadata={"node": "response_generator", "domain": domain, "intent": intent, "streaming": True},
        )

        # Prepare callbacks list
        callbacks = [langfuse_handler] if langfuse_handler else []

        # Wrap streaming in circuit breaker
        async def stream_with_protection():
            async for chunk in llm.astream(
                messages,
                config={"callbacks": callbacks} if callbacks else {},
            ):
                if chunk.content:
                    yield chunk

        async for chunk in stream_with_protection():
            if chunk.content:
                token = chunk.content
                full_response += token
                streaming_tokens.append(token)

                if on_token:
                    on_token(token)

                yield {
                    "streaming_tokens": streaming_tokens.copy(),
                    "response": full_response,
                }

    except CircuitBreakerError:
        full_response = (
            "I apologize, but I'm temporarily unable to process your request. "
            "Our AI service is experiencing high load. Please try again in a moment."
        )
        yield {
            "response": full_response,
            "error": "circuit_breaker_open",
        }

    except Exception as e:
        full_response = (
            "I apologize, but I'm having trouble generating a response. "
            "Please try again."
        )
        yield {
            "response": full_response,
            "error": str(e),
        }

    # Count output tokens accurately
    output_tokens = token_counter.count_tokens(full_response)
    total_tokens = input_tokens + output_tokens

    end_time = int(time.time() * 1000)

    # Mark complete
    node_states["response_generator"] = "complete"

    # Record timing
    timing = NodeTiming(
        node="response_generator",
        start_ms=start_time,
        end_ms=end_time,
        duration_ms=end_time - start_time,
    )

    trace_metadata = state["trace_metadata"].copy() if state["trace_metadata"] else {}
    existing_timings = trace_metadata.get("node_timings", [])
    trace_metadata["node_timings"] = existing_timings + [timing]
    trace_metadata["total_tokens"] = trace_metadata.get("total_tokens", 0) + total_tokens

    # Estimate cost
    estimated_cost = (total_tokens / 1_000_000) * 0.40
    trace_metadata["estimated_cost_usd"] = trace_metadata.get("estimated_cost_usd", 0) + estimated_cost

    # Add to message history
    new_messages = list(state.get("messages", []))
    new_messages.append(HumanMessage(content=state["current_input"]))
    new_messages.append(AIMessage(content=full_response))

    yield {
        "response": full_response,
        "response_complete": True,
        "messages": new_messages,
        "current_node": "end",
        "node_states": node_states,
        "trace_metadata": trace_metadata,
    }
