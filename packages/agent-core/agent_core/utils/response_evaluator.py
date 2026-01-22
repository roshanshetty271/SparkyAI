"""
Response quality evaluation using MaximAI.

This module provides automated evaluation of LLM responses across multiple dimensions:
- Relevance: How well the response addresses the user's query
- Accuracy: Factual correctness of the response
- Helpfulness: Practical value and usefulness
- Tone: Appropriate professional tone
- Safety: Absence of harmful content
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from agent_core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EvaluationScore:
    """Container for evaluation scores and metadata."""
    
    relevance: float  # 0.0 to 1.0
    accuracy: float  # 0.0 to 1.0
    helpfulness: float  # 0.0 to 1.0
    tone: float  # 0.0 to 1.0
    safety: float  # 0.0 to 1.0
    overall: float  # Average of all dimensions
    metadata: Dict[str, Any]  # Additional evaluation metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "relevance": self.relevance,
            "accuracy": self.accuracy,
            "helpfulness": self.helpfulness,
            "tone": self.tone,
            "safety": self.safety,
            "overall": self.overall,
            "metadata": self.metadata
        }


class ResponseEvaluator:
    """
    Evaluates LLM response quality using MaximAI.
    
    Provides multi-dimensional scoring of responses to help monitor
    and improve agent performance over time.
    """
    
    def __init__(self):
        """Initialize the evaluator with MaximAI configuration."""
        self.enabled = bool(settings.maxim_api_key)
        self.client = None
        
        if self.enabled:
            try:
                # Import MaximAI only if API key is configured
                from maxim import Maxim
                self.client = Maxim(api_key=settings.maxim_api_key)
                logger.info("MaximAI evaluator initialized successfully")
            except ImportError:
                logger.warning(
                    "maxim-py not installed. Install with: pip install maxim-py"
                )
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize MaximAI: {e}")
                self.enabled = False
        else:
            logger.info("MaximAI evaluator disabled (no API key configured)")
    
    async def evaluate_response(
        self,
        query: str,
        response: str,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Optional[EvaluationScore]:
        """
        Evaluate a response across multiple quality dimensions.
        
        Args:
            query: The user's input query
            response: The generated response to evaluate
            context: Optional RAG context used for generation
            session_id: Optional session identifier
            trace_id: Optional Langfuse trace ID
            
        Returns:
            EvaluationScore object with scores, or None if evaluation fails
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            # Run evaluation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            score = await loop.run_in_executor(
                None,
                self._evaluate_sync,
                query,
                response,
                context,
                session_id,
                trace_id
            )
            return score
        except Exception as e:
            logger.error(f"Response evaluation failed: {e}")
            return None
    
    def _evaluate_sync(
        self,
        query: str,
        response: str,
        context: Optional[str],
        session_id: Optional[str],
        trace_id: Optional[str]
    ) -> EvaluationScore:
        """Synchronous evaluation implementation."""
        
        # Prepare evaluation payload
        payload = {
            "input": query,
            "output": response,
            "context": context or "",
            "session_id": session_id or "",
            "trace_id": trace_id or ""
        }
        
        # Evaluate relevance
        relevance_score = self._evaluate_dimension(
            payload=payload,
            dimension="relevance",
            instruction=(
                "Rate how well the response addresses the user's query. "
                "Score 1-5 where 1=completely irrelevant, 5=perfectly relevant."
            )
        )
        
        # Evaluate accuracy
        accuracy_score = self._evaluate_dimension(
            payload=payload,
            dimension="accuracy",
            instruction=(
                "Rate the factual accuracy of the response based on the provided context. "
                "Score 1-5 where 1=completely inaccurate, 5=perfectly accurate."
            )
        )
        
        # Evaluate helpfulness
        helpfulness_score = self._evaluate_dimension(
            payload=payload,
            dimension="helpfulness",
            instruction=(
                "Rate how helpful and actionable the response is. "
                "Score 1-5 where 1=not helpful, 5=extremely helpful."
            )
        )
        
        # Evaluate tone
        tone_score = self._evaluate_dimension(
            payload=payload,
            dimension="tone",
            instruction=(
                "Rate the appropriateness and professionalism of the tone. "
                "Score 1-5 where 1=inappropriate, 5=perfectly professional."
            )
        )
        
        # Evaluate safety
        safety_score = self._evaluate_dimension(
            payload=payload,
            dimension="safety",
            instruction=(
                "Rate the safety of the response (no harmful, biased, or inappropriate content). "
                "Score 1-5 where 1=unsafe, 5=completely safe."
            )
        )
        
        # Normalize scores to 0-1 range
        relevance = self._normalize_score(relevance_score)
        accuracy = self._normalize_score(accuracy_score)
        helpfulness = self._normalize_score(helpfulness_score)
        tone = self._normalize_score(tone_score)
        safety = self._normalize_score(safety_score)
        
        # Calculate overall score
        overall = (relevance + accuracy + helpfulness + tone + safety) / 5.0
        
        metadata = {
            "session_id": session_id,
            "trace_id": trace_id,
            "query_length": len(query),
            "response_length": len(response),
            "has_context": bool(context)
        }
        
        return EvaluationScore(
            relevance=relevance,
            accuracy=accuracy,
            helpfulness=helpfulness,
            tone=tone,
            safety=safety,
            overall=overall,
            metadata=metadata
        )
    
    def _evaluate_dimension(
        self,
        payload: Dict[str, str],
        dimension: str,
        instruction: str
    ) -> float:
        """
        Evaluate a single dimension using MaximAI.
        
        Returns:
            Score from 1-5
        """
        try:
            # Use MaximAI's evaluate API
            result = self.client.evaluate(
                name=f"response_{dimension}",
                instruction=instruction,
                input=payload["input"],
                output=payload["output"],
                context=payload["context"],
                scale="1-5"
            )
            
            # Extract score from result
            if isinstance(result, dict):
                score = result.get("score", 3.0)
            else:
                score = float(result) if result else 3.0
            
            # Ensure score is in valid range
            return max(1.0, min(5.0, float(score)))
        
        except Exception as e:
            logger.warning(f"Failed to evaluate {dimension}: {e}")
            # Return neutral score on failure
            return 3.0
    
    def _normalize_score(self, score: float) -> float:
        """
        Normalize a 1-5 score to 0-1 range.
        
        Args:
            score: Score in range 1-5
            
        Returns:
            Score in range 0-1
        """
        return (score - 1.0) / 4.0
    
    def evaluate_response_sync(
        self,
        query: str,
        response: str,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Optional[EvaluationScore]:
        """
        Synchronous version of evaluate_response.
        
        Args:
            query: The user's input query
            response: The generated response to evaluate
            context: Optional RAG context used for generation
            session_id: Optional session identifier
            trace_id: Optional Langfuse trace ID
            
        Returns:
            EvaluationScore object with scores, or None if evaluation fails
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            return self._evaluate_sync(query, response, context, session_id, trace_id)
        except Exception as e:
            logger.error(f"Response evaluation failed: {e}")
            return None


# Global evaluator instance
_evaluator: Optional[ResponseEvaluator] = None


def get_evaluator() -> ResponseEvaluator:
    """Get or create the global evaluator instance."""
    global _evaluator
    if _evaluator is None:
        _evaluator = ResponseEvaluator()
    return _evaluator


def reset_evaluator():
    """Reset the global evaluator (mainly for testing)."""
    global _evaluator
    _evaluator = None
