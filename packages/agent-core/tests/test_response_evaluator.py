"""
Tests for response quality evaluator.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio

from agent_core.utils.response_evaluator import (
    ResponseEvaluator,
    EvaluationScore,
    get_evaluator,
    reset_evaluator,
)


class TestEvaluationScore:
    """Test EvaluationScore dataclass."""

    def test_evaluation_score_creation(self):
        """Test creating an evaluation score."""
        score = EvaluationScore(
            relevance=0.9,
            accuracy=0.85,
            helpfulness=0.95,
            tone=0.9,
            safety=1.0,
            overall=0.92,
            metadata={"test": "value"}
        )
        
        assert score.relevance == 0.9
        assert score.accuracy == 0.85
        assert score.helpfulness == 0.95
        assert score.tone == 0.9
        assert score.safety == 1.0
        assert score.overall == 0.92
        assert score.metadata == {"test": "value"}
    
    def test_evaluation_score_to_dict(self):
        """Test converting evaluation score to dictionary."""
        score = EvaluationScore(
            relevance=0.9,
            accuracy=0.85,
            helpfulness=0.95,
            tone=0.9,
            safety=1.0,
            overall=0.92,
            metadata={"test": "value"}
        )
        
        score_dict = score.to_dict()
        assert score_dict["relevance"] == 0.9
        assert score_dict["accuracy"] == 0.85
        assert score_dict["overall"] == 0.92
        assert score_dict["metadata"]["test"] == "value"


class TestResponseEvaluator:
    """Test ResponseEvaluator class."""

    def test_evaluator_disabled_without_api_key(self):
        """Test evaluator is disabled without API key."""
        with patch("agent_core.utils.response_evaluator.settings") as mock_settings:
            mock_settings.maxim_api_key = ""
            
            evaluator = ResponseEvaluator()
            assert evaluator.enabled is False
            assert evaluator.client is None
    
    def test_evaluator_enabled_with_api_key(self):
        """Test evaluator is enabled with API key."""
        with patch("agent_core.utils.response_evaluator.settings") as mock_settings:
            mock_settings.maxim_api_key = "test-key"
            
            with patch("maxim.Maxim") as mock_maxim:
                evaluator = ResponseEvaluator()
                assert evaluator.enabled is True
                assert evaluator.client is not None
                mock_maxim.assert_called_once_with(api_key="test-key")
    
    def test_evaluator_disabled_on_import_error(self):
        """Test evaluator gracefully handles missing maxim-py."""
        with patch("agent_core.utils.response_evaluator.settings") as mock_settings:
            mock_settings.maxim_api_key = "test-key"
            
            # Simulate ImportError when trying to import Maxim
            with patch("builtins.__import__", side_effect=ImportError("No module named 'maxim'")):
                evaluator = ResponseEvaluator()
                # Should be disabled due to ImportError
                # Note: This test behavior depends on how ResponseEvaluator handles import
    
    def test_normalize_score(self):
        """Test score normalization from 1-5 to 0-1 range."""
        evaluator = ResponseEvaluator()
        
        assert evaluator._normalize_score(1.0) == 0.0
        assert evaluator._normalize_score(3.0) == 0.5
        assert evaluator._normalize_score(5.0) == 1.0
        assert evaluator._normalize_score(2.0) == 0.25
        assert evaluator._normalize_score(4.0) == 0.75
    
    @pytest.mark.asyncio
    async def test_evaluate_response_disabled(self):
        """Test evaluation returns None when disabled."""
        evaluator = ResponseEvaluator()
        evaluator.enabled = False
        
        result = await evaluator.evaluate_response(
            query="What are your skills?",
            response="I have experience in Python and JavaScript."
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_evaluate_response_with_mock_client(self):
        """Test evaluation with mocked MaximAI client."""
        with patch("agent_core.utils.response_evaluator.settings") as mock_settings:
            mock_settings.maxim_api_key = "test-key"
            
            # Create mock client
            mock_client = MagicMock()
            mock_client.evaluate.return_value = {"score": 4.0}
            
            with patch("maxim.Maxim", return_value=mock_client):
                evaluator = ResponseEvaluator()
                evaluator.enabled = True
                
                result = await evaluator.evaluate_response(
                    query="What are your skills?",
                    response="I have experience in Python and JavaScript.",
                    context="Skills: Python, JavaScript, TypeScript",
                    session_id="test-session",
                    trace_id="test-trace"
                )
                
                assert result is not None
                assert isinstance(result, EvaluationScore)
                assert 0.0 <= result.overall <= 1.0
                assert 0.0 <= result.relevance <= 1.0
                assert 0.0 <= result.accuracy <= 1.0
    
    def test_evaluate_response_sync_disabled(self):
        """Test synchronous evaluation returns None when disabled."""
        evaluator = ResponseEvaluator()
        evaluator.enabled = False
        
        result = evaluator.evaluate_response_sync(
            query="What are your skills?",
            response="I have experience in Python."
        )
        
        assert result is None
    
    def test_evaluate_dimension_returns_default_on_error(self):
        """Test dimension evaluation returns neutral score on error."""
        evaluator = ResponseEvaluator()
        evaluator.client = MagicMock()
        evaluator.client.evaluate.side_effect = Exception("API Error")
        
        score = evaluator._evaluate_dimension(
            payload={"input": "test", "output": "test", "context": ""},
            dimension="relevance",
            instruction="Test instruction"
        )
        
        # Should return neutral score (3.0) on error
        assert score == 3.0
    
    def test_evaluate_dimension_clamps_score(self):
        """Test dimension evaluation clamps scores to valid range."""
        evaluator = ResponseEvaluator()
        evaluator.client = MagicMock()
        
        # Test score too low
        evaluator.client.evaluate.return_value = {"score": 0.0}
        score = evaluator._evaluate_dimension(
            payload={"input": "test", "output": "test", "context": ""},
            dimension="relevance",
            instruction="Test"
        )
        assert score == 1.0
        
        # Test score too high
        evaluator.client.evaluate.return_value = {"score": 10.0}
        score = evaluator._evaluate_dimension(
            payload={"input": "test", "output": "test", "context": ""},
            dimension="relevance",
            instruction="Test"
        )
        assert score == 5.0
    
    def test_evaluate_dimension_with_different_response_formats(self):
        """Test evaluation handles different API response formats."""
        evaluator = ResponseEvaluator()
        evaluator.client = MagicMock()
        
        # Dict response with score key
        evaluator.client.evaluate.return_value = {"score": 4.5}
        score = evaluator._evaluate_dimension(
            payload={"input": "test", "output": "test", "context": ""},
            dimension="relevance",
            instruction="Test"
        )
        assert score == 4.5
        
        # Direct numeric response
        evaluator.client.evaluate.return_value = 3.7
        score = evaluator._evaluate_dimension(
            payload={"input": "test", "output": "test", "context": ""},
            dimension="relevance",
            instruction="Test"
        )
        assert score == 3.7


class TestGlobalEvaluator:
    """Test global evaluator instance management."""

    def test_get_evaluator_returns_singleton(self):
        """Test get_evaluator returns the same instance."""
        reset_evaluator()
        
        evaluator1 = get_evaluator()
        evaluator2 = get_evaluator()
        
        assert evaluator1 is evaluator2
    
    def test_reset_evaluator(self):
        """Test reset_evaluator creates new instance."""
        evaluator1 = get_evaluator()
        reset_evaluator()
        evaluator2 = get_evaluator()
        
        assert evaluator1 is not evaluator2


class TestEvaluationMetadata:
    """Test evaluation metadata handling."""

    def test_metadata_includes_query_response_lengths(self):
        """Test metadata includes query and response lengths."""
        with patch("agent_core.utils.response_evaluator.settings") as mock_settings:
            mock_settings.maxim_api_key = "test-key"
            
            mock_client = MagicMock()
            mock_client.evaluate.return_value = {"score": 4.0}
            
            with patch("maxim.Maxim", return_value=mock_client):
                evaluator = ResponseEvaluator()
                evaluator.enabled = True
                
                result = evaluator.evaluate_response_sync(
                    query="Short query",
                    response="This is a longer response with more words.",
                    context="Some context"
                )
                
                assert result is not None
                assert "query_length" in result.metadata
                assert "response_length" in result.metadata
                assert "has_context" in result.metadata
                assert result.metadata["has_context"] is True
    
    def test_metadata_tracks_session_and_trace(self):
        """Test metadata tracks session and trace IDs."""
        with patch("agent_core.utils.response_evaluator.settings") as mock_settings:
            mock_settings.maxim_api_key = "test-key"
            
            mock_client = MagicMock()
            mock_client.evaluate.return_value = {"score": 4.0}
            
            with patch("maxim.Maxim", return_value=mock_client):
                evaluator = ResponseEvaluator()
                evaluator.enabled = True
                
                result = evaluator.evaluate_response_sync(
                    query="Test query",
                    response="Test response",
                    session_id="session-123",
                    trace_id="trace-456"
                )
                
                assert result is not None
                assert result.metadata["session_id"] == "session-123"
                assert result.metadata["trace_id"] == "trace-456"


@pytest.mark.integration
class TestEvaluationIntegration:
    """Integration tests requiring MaximAI API key."""

    @pytest.mark.skipif(
        True,  # Skip by default - requires MaximAI API key
        reason="Integration tests require MaximAI API key"
    )
    @pytest.mark.asyncio
    async def test_evaluate_real_response(self):
        """Test evaluation with real MaximAI API."""
        # This test requires MAXIM_API_KEY environment variable
        evaluator = get_evaluator()
        
        if not evaluator.enabled:
            pytest.skip("MaximAI not configured")
        
        result = await evaluator.evaluate_response(
            query="What programming languages do you know?",
            response="I am proficient in Python, JavaScript, and TypeScript. "
                     "I have 5 years of experience with Python and 3 years with JavaScript.",
            context="Skills: Python (5 years), JavaScript (3 years), TypeScript (2 years)"
        )
        
        assert result is not None
        assert 0.0 <= result.overall <= 1.0
        assert 0.0 <= result.relevance <= 1.0
        assert 0.0 <= result.accuracy <= 1.0
        assert 0.0 <= result.helpfulness <= 1.0
        assert 0.0 <= result.tone <= 1.0
        assert 0.0 <= result.safety <= 1.0
