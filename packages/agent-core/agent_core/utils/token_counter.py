"""Token counting utilities for conversation management.

This module provides utilities to count tokens in messages and manage
conversation history to stay within model context limits.
"""
import tiktoken
from typing import List, Dict, Any, Optional, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class Message(TypedDict):
    """Message format for conversation history."""
    role: str
    content: str


class TokenCounter:
    """Handles token counting for OpenAI models."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize token counter with specific model encoding.
        
        Args:
            model: OpenAI model name (default: gpt-4o-mini)
        """
        self.model = model
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding (used by GPT-4 and GPT-3.5-turbo)
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string.
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))
    
    def count_message_tokens(self, message: Dict[str, str]) -> int:
        """Count tokens in a message dict (role + content).
        
        Args:
            message: Message dict with 'role' and 'content' keys
            
        Returns:
            Number of tokens (includes overhead for message formatting)
        """
        # OpenAI API adds overhead for each message:
        # - 3 tokens per message (for formatting)
        # - 1 token per name (if present)
        tokens = 3  # Base overhead
        tokens += self.count_tokens(message.get("role", ""))
        tokens += self.count_tokens(message.get("content", ""))
        if "name" in message:
            tokens += 1
        return tokens
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count total tokens in a list of messages.
        
        Args:
            messages: List of message dicts
            
        Returns:
            Total number of tokens
        """
        total = sum(self.count_message_tokens(msg) for msg in messages)
        total += 3  # Every reply is primed with <|start|>assistant<|message|>
        return total
    
    def count_conversation_tokens(self, conversation: List[Message]) -> int:
        """Count tokens in AgentState conversation format.
        
        Args:
            conversation: List of Message dicts from AgentState
            
        Returns:
            Total number of tokens
        """
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation
        ]
        return self.count_messages_tokens(messages)


class ConversationWindowManager:
    """Manages conversation history to stay within token limits."""
    
    def __init__(
        self,
        max_tokens: int = 100000,  # GPT-4o-mini supports 128K, leave buffer
        model: str = "gpt-4o-mini",
        min_messages_to_keep: int = 4,  # Always keep at least 2 exchanges
    ):
        """Initialize conversation window manager.
        
        Args:
            max_tokens: Maximum tokens to allow in conversation history
            model: OpenAI model name
            min_messages_to_keep: Minimum number of messages to always keep
        """
        self.max_tokens = max_tokens
        self.min_messages_to_keep = min_messages_to_keep
        self.token_counter = TokenCounter(model=model)
    
    def truncate_conversation(
        self,
        conversation: List[Message],
        system_prompt_tokens: int = 0,
        rag_context_tokens: int = 0,
    ) -> List[Message]:
        """Truncate conversation to fit within token limits.
        
        Uses a sliding window approach: keeps most recent messages and removes
        oldest ones first, but always keeps the minimum number of messages.
        
        Args:
            conversation: Full conversation history
            system_prompt_tokens: Tokens used by system prompt
            rag_context_tokens: Tokens used by RAG context
            
        Returns:
            Truncated conversation that fits within limits
        """
        if len(conversation) <= self.min_messages_to_keep:
            return conversation
        
        # Calculate available tokens for conversation history
        available_tokens = (
            self.max_tokens - system_prompt_tokens - rag_context_tokens
        )
        
        # Calculate current conversation tokens
        current_tokens = self.token_counter.count_conversation_tokens(conversation)
        
        if current_tokens <= available_tokens:
            return conversation  # No truncation needed
        
        # Start from the end and work backwards
        truncated = list(conversation)
        
        while len(truncated) > self.min_messages_to_keep:
            # Remove oldest message (after any system messages)
            # Keep first message if it's a system message
            if truncated[0].get("role") == "system":
                truncated.pop(1)  # Remove second message
            else:
                truncated.pop(0)  # Remove first message
            
            current_tokens = self.token_counter.count_conversation_tokens(truncated)
            
            if current_tokens <= available_tokens:
                break
        
        return truncated
    
    def should_summarize(
        self,
        conversation: List[Message],
        threshold: float = 0.8,
    ) -> bool:
        """Determine if conversation should be summarized.
        
        Args:
            conversation: Current conversation history
            threshold: Token usage threshold (0.0-1.0) to trigger summarization
            
        Returns:
            True if conversation should be summarized
        """
        current_tokens = self.token_counter.count_conversation_tokens(conversation)
        usage_ratio = current_tokens / self.max_tokens
        return usage_ratio >= threshold and len(conversation) > 10
    
    async def summarize_conversation(
        self,
        conversation: List[Message],
        openai_api_key: str,
        keep_recent_messages: int = 4,
    ) -> List[Message]:
        """Summarize old conversation history to save tokens.
        
        This keeps the most recent N messages intact and summarizes the older
        messages into a single system message.
        
        Args:
            conversation: Full conversation history
            openai_api_key: OpenAI API key for summarization
            keep_recent_messages: Number of recent messages to keep unsummarized
            
        Returns:
            Conversation with older messages summarized
        """
        if len(conversation) <= keep_recent_messages:
            return conversation
        
        # Split into old (to summarize) and recent (to keep)
        messages_to_summarize = conversation[:-keep_recent_messages]
        recent_messages = conversation[-keep_recent_messages:]
        
        if not messages_to_summarize:
            return conversation
        
        # Format conversation for summarization
        conversation_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in messages_to_summarize
        ])
        
        # Use LLM to create summary
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=200,
            api_key=openai_api_key,
        )
        
        try:
            response = await llm.ainvoke([
                SystemMessage(content="""Summarize this conversation history concisely.
Focus on key topics discussed and important information exchanged.
Keep it under 150 words."""),
                HumanMessage(content=f"Conversation to summarize:\n\n{conversation_text}"),
            ])
            
            summary = response.content
            
            # Create summary message
            summary_message: Message = {
                "role": "system",
                "content": f"[Previous conversation summary: {summary}]",
            }
            
            # Return summary + recent messages
            return [summary_message] + recent_messages
            
        except Exception as e:
            # If summarization fails, just truncate
            print(f"Summarization failed: {e}, falling back to truncation")
            return self.truncate_conversation(conversation)
    
    def summarize_conversation_sync(
        self,
        conversation: List[Message],
        openai_api_key: str,
        keep_recent_messages: int = 4,
    ) -> List[Message]:
        """Synchronous version of summarize_conversation.
        
        Args:
            conversation: Full conversation history
            openai_api_key: OpenAI API key for summarization
            keep_recent_messages: Number of recent messages to keep unsummarized
            
        Returns:
            Conversation with older messages summarized
        """
        if len(conversation) <= keep_recent_messages:
            return conversation
        
        # Split into old and recent
        messages_to_summarize = conversation[:-keep_recent_messages]
        recent_messages = conversation[-keep_recent_messages:]
        
        if not messages_to_summarize:
            return conversation
        
        # Format conversation
        conversation_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in messages_to_summarize
        ])
        
        # Use LLM to create summary
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=200,
            api_key=openai_api_key,
        )
        
        try:
            response = llm.invoke([
                SystemMessage(content="""Summarize this conversation history concisely.
Focus on key topics discussed and important information exchanged.
Keep it under 150 words."""),
                HumanMessage(content=f"Conversation to summarize:\n\n{conversation_text}"),
            ])
            
            summary = response.content
            
            # Create summary message
            summary_message: Message = {
                "role": "system",
                "content": f"[Previous conversation summary: {summary}]",
            }
            
            # Return summary + recent messages
            return [summary_message] + recent_messages
            
        except Exception as e:
            # If summarization fails, just truncate
            print(f"Summarization failed: {e}, falling back to truncation")
            return self.truncate_conversation(conversation)


def format_conversation_for_llm(
    conversation: List[Message],
    system_prompt: Optional[str] = None,
    rag_context: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Format conversation history for LLM API call.
    
    Args:
        conversation: Conversation history from AgentState
        system_prompt: Optional system prompt to prepend
        rag_context: Optional RAG context to include
        
    Returns:
        Formatted messages for OpenAI API
    """
    messages = []
    
    # Add system prompt if provided
    if system_prompt:
        content = system_prompt
        if rag_context:
            content += f"\n\nRelevant Context:\n{rag_context}"
        messages.append({"role": "system", "content": content})
    
    # Add conversation history
    for msg in conversation:
        messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })
    
    return messages


# Singleton instance for convenience
_default_counter = None
_default_manager = None


def get_token_counter(model: str = "gpt-4o-mini") -> TokenCounter:
    """Get or create default TokenCounter instance.
    
    Args:
        model: OpenAI model name
        
    Returns:
        TokenCounter instance
    """
    global _default_counter
    if _default_counter is None:
        _default_counter = TokenCounter(model=model)
    return _default_counter


def get_window_manager(
    max_tokens: int = 100000,
    model: str = "gpt-4o-mini",
) -> ConversationWindowManager:
    """Get or create default ConversationWindowManager instance.
    
    Args:
        max_tokens: Maximum tokens to allow
        model: OpenAI model name
        
    Returns:
        ConversationWindowManager instance
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = ConversationWindowManager(
            max_tokens=max_tokens,
            model=model,
        )
    return _default_manager
