"""
Agent Utilities
================

Input sanitization, prompt injection detection, rate limiting helpers,
and conversation management utilities.
"""

import re
from typing import Tuple, Optional

# Export token counter and window manager
from agent_core.utils.token_counter import (
    TokenCounter,
    ConversationWindowManager,
    get_token_counter,
    get_window_manager,
    format_conversation_for_llm,
)

# Export circuit breaker
from agent_core.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
    get_openai_breaker,
    get_embedding_breaker,
    reset_all_breakers,
)


# Prompt injection patterns to block
INJECTION_PATTERNS = [
    # Direct instruction override attempts
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)",
    r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)",
    
    # System prompt extraction
    r"(what|show|reveal|tell)\s+(is|me|are)?\s*(your|the)\s+(system\s+)?prompt",
    r"(print|display|output)\s+(your|the)\s+(system\s+)?prompt",
    r"repeat\s+(your|the)\s+(initial|system|original)\s+(instructions?|prompt)",
    
    # Role-play jailbreaks
    r"you\s+are\s+now\s+(DAN|evil|unfiltered|uncensored)",
    r"pretend\s+(you\s+are|to\s+be)\s+(DAN|evil|unfiltered)",
    r"act\s+as\s+(if\s+you\s+are\s+)?(DAN|evil|unfiltered)",
    r"roleplay\s+as\s+(DAN|evil|an?\s+AI\s+without)",
    
    # Instruction injection via formatting
    r"```\s*system",
    r"\[INST\]",
    r"\[\/INST\]",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    
    # Developer mode attempts
    r"(enable|activate|enter)\s+(developer|dev|debug)\s+mode",
    r"sudo\s+mode",
    
    # Override attempts
    r"new\s+(instructions?|rules?):\s*",
    r"updated\s+(instructions?|rules?):\s*",
    r"override\s+(instructions?|rules?|prompt)",
]

# Compiled patterns for efficiency
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def sanitize_input(text: str, max_length: int = 500) -> Tuple[str, Optional[str]]:
    """
    Sanitize user input for security.
    
    Args:
        text: Raw user input
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (sanitized_text, warning_message or None)
    """
    warning = None
    
    # Strip whitespace
    text = text.strip()
    
    # Check length
    if len(text) > max_length:
        text = text[:max_length]
        warning = f"Message truncated to {max_length} characters."
    
    # Check for injection patterns
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            # Don't reveal which pattern matched
            return "", "I can only help with questions about professional background and experience."
    
    # Remove null bytes and other control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text, warning


def is_valid_session_id(session_id: str) -> bool:
    """
    Validate session ID format.
    
    Args:
        session_id: Session identifier to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not session_id:
        return False
    
    # Allow alphanumeric, hyphens, underscores
    # Length between 8 and 64 characters
    if not re.match(r'^[a-zA-Z0-9_-]{8,64}$', session_id):
        return False
    
    return True


def sanitize_session_id(session_id: str) -> str:
    """
    Sanitize and normalize session ID.
    
    Args:
        session_id: Raw session ID
        
    Returns:
        Sanitized session ID
    """
    # Remove invalid characters
    cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', session_id)
    
    # Ensure minimum length
    if len(cleaned) < 8:
        import uuid
        cleaned = str(uuid.uuid4())
    
    # Truncate if too long
    return cleaned[:64]


class RateLimitInfo:
    """Information about rate limit status."""
    
    def __init__(
        self,
        allowed: bool,
        remaining: int,
        reset_seconds: int,
        limit: int,
    ):
        self.allowed = allowed
        self.remaining = remaining
        self.reset_seconds = reset_seconds
        self.limit = limit
    
    def to_headers(self) -> dict:
        """Convert to HTTP headers."""
        return {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(self.reset_seconds),
        }
