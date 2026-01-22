"""Tests for token counting and conversation memory management."""
import pytest
from agent_core.utils.token_counter import (
    TokenCounter,
    ConversationWindowManager,
    format_conversation_for_llm,
)


class TestTokenCounter:
    """Test token counting functionality."""
    
    def test_count_tokens_basic(self):
        """Test basic token counting."""
        counter = TokenCounter()
        text = "Hello, how are you?"
        tokens = counter.count_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_count_tokens_empty(self):
        """Test counting tokens in empty string."""
        counter = TokenCounter()
        tokens = counter.count_tokens("")
        assert tokens == 0
    
    def test_count_message_tokens(self):
        """Test counting tokens in a message dict."""
        counter = TokenCounter()
        message = {"role": "user", "content": "Hello, world!"}
        tokens = counter.count_message_tokens(message)
        # Should include overhead (3) + role tokens + content tokens
        assert tokens > 3
    
    def test_count_messages_tokens(self):
        """Test counting tokens in multiple messages."""
        counter = TokenCounter()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        tokens = counter.count_messages_tokens(messages)
        assert tokens > 0
    
    def test_count_conversation_tokens(self):
        """Test counting tokens in conversation format."""
        counter = TokenCounter()
        conversation = [
            {"role": "human", "content": "What is your name?"},
            {"role": "ai", "content": "I'm an AI assistant."},
        ]
        tokens = counter.count_conversation_tokens(conversation)
        assert tokens > 0


class TestConversationWindowManager:
    """Test conversation window management."""
    
    def test_initialization(self):
        """Test manager initialization."""
        manager = ConversationWindowManager(max_tokens=1000)
        assert manager.max_tokens == 1000
        assert manager.min_messages_to_keep == 4
    
    def test_no_truncation_needed(self):
        """Test that short conversations are not truncated."""
        manager = ConversationWindowManager(max_tokens=100000)
        conversation = [
            {"role": "human", "content": "Hi"},
            {"role": "ai", "content": "Hello"},
        ]
        result = manager.truncate_conversation(conversation)
        assert len(result) == len(conversation)
    
    def test_truncation_with_small_limit(self):
        """Test that long conversations are truncated."""
        manager = ConversationWindowManager(
            max_tokens=100,  # Very small limit
            min_messages_to_keep=2,
        )
        conversation = [
            {"role": "human", "content": "Message 1"},
            {"role": "ai", "content": "Response 1"},
            {"role": "human", "content": "Message 2"},
            {"role": "ai", "content": "Response 2"},
            {"role": "human", "content": "Message 3"},
            {"role": "ai", "content": "Response 3"},
        ]
        result = manager.truncate_conversation(conversation)
        # Should keep at least min_messages_to_keep
        assert len(result) >= manager.min_messages_to_keep
        # Should have removed some messages
        assert len(result) <= len(conversation)
    
    def test_min_messages_preserved(self):
        """Test that minimum messages are always kept."""
        manager = ConversationWindowManager(
            max_tokens=10,  # Impossibly small
            min_messages_to_keep=3,
        )
        conversation = [
            {"role": "human", "content": "1"},
            {"role": "ai", "content": "2"},
            {"role": "human", "content": "3"},
            {"role": "ai", "content": "4"},
        ]
        result = manager.truncate_conversation(conversation)
        # Should keep at least min_messages
        assert len(result) >= min(manager.min_messages_to_keep, len(conversation))
    
    def test_should_summarize_false_for_short(self):
        """Test that short conversations don't need summarization."""
        manager = ConversationWindowManager(max_tokens=100000)
        conversation = [
            {"role": "human", "content": "Hi"},
            {"role": "ai", "content": "Hello"},
        ]
        assert manager.should_summarize(conversation) is False
    
    def test_should_summarize_true_for_long(self):
        """Test that long conversations need summarization."""
        manager = ConversationWindowManager(max_tokens=100)
        # Create a long conversation
        conversation = [
            {"role": "human", "content": "Message " * 50},
            {"role": "ai", "content": "Response " * 50},
        ] * 10  # 20 messages total
        assert manager.should_summarize(conversation, threshold=0.1) is True


class TestFormatConversationForLLM:
    """Test conversation formatting utilities."""
    
    def test_format_with_system_prompt(self):
        """Test formatting with system prompt."""
        conversation = [
            {"role": "human", "content": "Hello"},
            {"role": "ai", "content": "Hi there"},
        ]
        result = format_conversation_for_llm(
            conversation,
            system_prompt="You are helpful.",
        )
        assert len(result) == 3  # system + 2 messages
        assert result[0]["role"] == "system"
        assert "helpful" in result[0]["content"].lower()
    
    def test_format_with_rag_context(self):
        """Test formatting with RAG context."""
        conversation = [
            {"role": "human", "content": "Hello"},
        ]
        result = format_conversation_for_llm(
            conversation,
            system_prompt="You are helpful.",
            rag_context="User is a software engineer.",
        )
        assert "software engineer" in result[0]["content"].lower()
    
    def test_format_without_system_prompt(self):
        """Test formatting without system prompt."""
        conversation = [
            {"role": "human", "content": "Hello"},
            {"role": "ai", "content": "Hi"},
        ]
        result = format_conversation_for_llm(conversation)
        assert len(result) == 2
        assert result[0]["role"] == "human"


# Integration tests would require OpenAI API key
@pytest.mark.skip(reason="Requires OpenAI API key")
class TestConversationSummarization:
    """Test conversation summarization (requires API)."""
    
    @pytest.mark.asyncio
    async def test_summarize_conversation(self):
        """Test conversation summarization."""
        import os
        manager = ConversationWindowManager()
        conversation = [
            {"role": "human", "content": "What is Python?"},
            {"role": "ai", "content": "Python is a programming language."},
            {"role": "human", "content": "What is it used for?"},
            {"role": "ai", "content": "It's used for web development, data science, and more."},
            {"role": "human", "content": "Is it easy to learn?"},
            {"role": "ai", "content": "Yes, it's known for being beginner-friendly."},
        ]
        
        api_key = os.getenv("OPENAI_API_KEY", "test-key")
        result = await manager.summarize_conversation(
            conversation,
            api_key,
            keep_recent_messages=2,
        )
        
        # Should have summary + recent messages
        assert len(result) < len(conversation)
        # First message should be summary
        assert result[0]["role"] == "system"
        assert "summary" in result[0]["content"].lower()
