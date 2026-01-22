"""Circuit Breaker pattern for OpenAI API calls.

Implements a circuit breaker to prevent cascading failures when the OpenAI API
is down or experiencing issues. The circuit breaker has three states:
- CLOSED: Normal operation, requests go through
- OPEN: Too many failures, requests are rejected immediately
- HALF_OPEN: Testing if service has recovered

Based on the "Release It!" pattern by Michael Nygard.
"""

import time
import asyncio
from enum import Enum
from typing import Optional, Callable, TypeVar, Any, Awaitable
from dataclasses import dataclass, field
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Too many failures, blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    
    # Number of failures before opening circuit
    failure_threshold: int = 5
    
    # Time in seconds before attempting recovery
    recovery_timeout: float = 60.0
    
    # Number of successful calls needed to close from half-open
    success_threshold: int = 2
    
    # Time window for counting failures (seconds)
    failure_window: float = 120.0
    
    # Exceptions that should trigger the circuit breaker
    monitored_exceptions: tuple = (Exception,)


@dataclass
class CircuitBreakerStats:
    """Statistics for monitoring circuit breaker behavior."""
    
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0
    
    def to_dict(self) -> dict:
        """Convert stats to dictionary."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
        }


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker for protecting against cascading failures.
    
    Usage:
        breaker = CircuitBreaker(name="openai")
        
        @breaker.protect
        async def call_openai():
            return await openai_client.chat.completions.create(...)
        
        result = await call_openai()
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        """Initialize circuit breaker.
        
        Args:
            name: Identifier for this circuit breaker
            config: Configuration options
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit."""
        if self.stats.state != CircuitState.OPEN:
            return False
        
        if self.stats.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.stats.last_failure_time
        return time_since_failure >= self.config.recovery_timeout
    
    def _is_failure_window_expired(self) -> bool:
        """Check if the failure counting window has expired."""
        if self.stats.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.stats.last_failure_time
        return time_since_failure >= self.config.failure_window
    
    async def _record_success(self):
        """Record a successful call."""
        async with self._lock:
            self.stats.total_calls += 1
            self.stats.total_successes += 1
            
            if self.stats.state == CircuitState.HALF_OPEN:
                self.stats.success_count += 1
                logger.info(
                    f"Circuit breaker '{self.name}': Success in HALF_OPEN "
                    f"({self.stats.success_count}/{self.config.success_threshold})"
                )
                
                if self.stats.success_count >= self.config.success_threshold:
                    self._close_circuit()
            
            elif self.stats.state == CircuitState.CLOSED:
                # Reset failure count if we're in a new window
                if self._is_failure_window_expired():
                    self.stats.failure_count = 0
    
    async def _record_failure(self, exception: Exception):
        """Record a failed call."""
        async with self._lock:
            self.stats.total_calls += 1
            self.stats.total_failures += 1
            self.stats.last_failure_time = time.time()
            
            if self.stats.state == CircuitState.HALF_OPEN:
                # Any failure in half-open immediately opens circuit
                logger.warning(
                    f"Circuit breaker '{self.name}': Failure in HALF_OPEN, "
                    f"reopening circuit"
                )
                self._open_circuit()
            
            elif self.stats.state == CircuitState.CLOSED:
                self.stats.failure_count += 1
                logger.warning(
                    f"Circuit breaker '{self.name}': Failure "
                    f"({self.stats.failure_count}/{self.config.failure_threshold})"
                )
                
                if self.stats.failure_count >= self.config.failure_threshold:
                    self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit (block all requests)."""
        self.stats.state = CircuitState.OPEN
        self.stats.last_state_change = time.time()
        self.stats.success_count = 0
        logger.error(
            f"Circuit breaker '{self.name}': OPENED "
            f"(failures: {self.stats.failure_count})"
        )
    
    def _close_circuit(self):
        """Close the circuit (allow all requests)."""
        self.stats.state = CircuitState.CLOSED
        self.stats.last_state_change = time.time()
        self.stats.failure_count = 0
        self.stats.success_count = 0
        logger.info(f"Circuit breaker '{self.name}': CLOSED")
    
    def _half_open_circuit(self):
        """Half-open the circuit (allow test requests)."""
        self.stats.state = CircuitState.HALF_OPEN
        self.stats.last_state_change = time.time()
        self.stats.success_count = 0
        logger.info(f"Circuit breaker '{self.name}': HALF_OPEN (testing recovery)")
    
    async def call(
        self,
        func: Callable[..., Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        """Execute a function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from func
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception from func
        """
        # Check if we should attempt reset
        if self._should_attempt_reset():
            async with self._lock:
                if self.stats.state == CircuitState.OPEN:
                    self._half_open_circuit()
        
        # Block if circuit is open
        if self.stats.state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service unavailable. Try again in "
                f"{self.config.recovery_timeout}s."
            )
        
        # Attempt the call
        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
        
        except self.config.monitored_exceptions as e:
            await self._record_failure(e)
            raise
    
    def protect(self, func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        """Decorator to protect an async function with circuit breaker.
        
        Usage:
            @breaker.protect
            async def my_function():
                ...
        """
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await self.call(func, *args, **kwargs)
        
        return wrapper
    
    def get_stats(self) -> CircuitBreakerStats:
        """Get current statistics."""
        return self.stats
    
    def reset(self):
        """Manually reset the circuit breaker."""
        self.stats = CircuitBreakerStats()
        logger.info(f"Circuit breaker '{self.name}': Manually reset")


# Global circuit breakers for different services
_openai_breaker: Optional[CircuitBreaker] = None
_embedding_breaker: Optional[CircuitBreaker] = None


def get_openai_breaker() -> CircuitBreaker:
    """Get or create OpenAI circuit breaker."""
    global _openai_breaker
    if _openai_breaker is None:
        _openai_breaker = CircuitBreaker(
            name="openai",
            config=CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60.0,
                success_threshold=2,
                failure_window=120.0,
            ),
        )
    return _openai_breaker


def get_embedding_breaker() -> CircuitBreaker:
    """Get or create embedding circuit breaker."""
    global _embedding_breaker
    if _embedding_breaker is None:
        _embedding_breaker = CircuitBreaker(
            name="openai_embeddings",
            config=CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30.0,
                success_threshold=2,
                failure_window=60.0,
            ),
        )
    return _embedding_breaker


def reset_all_breakers():
    """Reset all global circuit breakers."""
    global _openai_breaker, _embedding_breaker
    if _openai_breaker:
        _openai_breaker.reset()
    if _embedding_breaker:
        _embedding_breaker.reset()
