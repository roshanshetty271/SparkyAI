"""Tests for circuit breaker pattern."""
import asyncio

import pytest

from agent_core.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitState,
    get_openai_breaker,
    reset_all_breakers,
)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def setup_method(self):
        """Reset breakers before each test."""
        reset_all_breakers()

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test circuit breaker initialization."""
        breaker = CircuitBreaker("test")
        assert breaker.name == "test"
        assert breaker.stats.state == CircuitState.CLOSED
        assert breaker.stats.failure_count == 0

    @pytest.mark.asyncio
    async def test_successful_call(self):
        """Test successful function call through breaker."""
        breaker = CircuitBreaker("test")

        async def success_func():
            return "success"

        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.stats.state == CircuitState.CLOSED
        assert breaker.stats.total_successes == 1

    @pytest.mark.asyncio
    async def test_failed_call(self):
        """Test failed function call through breaker."""
        breaker = CircuitBreaker(
            "test",
            config=CircuitBreakerConfig(failure_threshold=3),
        )

        async def failing_func():
            raise ValueError("Test error")

        # First failure
        with pytest.raises(ValueError):
            await breaker.call(failing_func)

        assert breaker.stats.state == CircuitState.CLOSED
        assert breaker.stats.failure_count == 1

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold(self):
        """Test that circuit opens after failure threshold."""
        breaker = CircuitBreaker(
            "test",
            config=CircuitBreakerConfig(failure_threshold=3),
        )

        async def failing_func():
            raise ValueError("Test error")

        # Trigger failures up to threshold
        for i in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        # Circuit should now be open
        assert breaker.stats.state == CircuitState.OPEN

        # Next call should immediately fail with CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await breaker.call(failing_func)

    @pytest.mark.asyncio
    async def test_circuit_half_open_after_timeout(self):
        """Test that circuit transitions to half-open after timeout."""
        breaker = CircuitBreaker(
            "test",
            config=CircuitBreakerConfig(
                failure_threshold=2,
                recovery_timeout=0.1,  # Short timeout for testing
            ),
        )

        async def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.stats.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Next call should attempt recovery (half-open)
        async def success_func():
            return "success"

        result = await breaker.call(success_func)
        assert result == "success"
        # After one success in half-open, still need more
        assert breaker.stats.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_circuit_closes_after_success_threshold(self):
        """Test that circuit closes after enough successes in half-open."""
        breaker = CircuitBreaker(
            "test",
            config=CircuitBreakerConfig(
                failure_threshold=2,
                recovery_timeout=0.1,
                success_threshold=2,
            ),
        )

        async def failing_func():
            raise ValueError("Test error")

        async def success_func():
            return "success"

        # Open the circuit
        for i in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        # Wait for recovery
        await asyncio.sleep(0.15)

        # Succeed enough times to close circuit
        for i in range(2):
            await breaker.call(success_func)

        assert breaker.stats.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_decorator_usage(self):
        """Test using breaker as a decorator."""
        breaker = CircuitBreaker("test")

        @breaker.protect
        async def decorated_func(x):
            return x * 2

        result = await decorated_func(5)
        assert result == 10
        assert breaker.stats.total_successes == 1

    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        """Test that statistics are tracked correctly."""
        breaker = CircuitBreaker("test")

        async def success_func():
            return "success"

        async def failing_func():
            raise ValueError("Error")

        # Run some operations
        await breaker.call(success_func)
        await breaker.call(success_func)

        try:
            await breaker.call(failing_func)
        except ValueError:
            pass

        stats = breaker.get_stats()
        assert stats.total_calls == 3
        assert stats.total_successes == 2
        assert stats.total_failures == 1

    @pytest.mark.asyncio
    async def test_reset(self):
        """Test manual circuit breaker reset."""
        breaker = CircuitBreaker(
            "test",
            config=CircuitBreakerConfig(failure_threshold=1),
        )

        async def failing_func():
            raise ValueError("Error")

        # Open the circuit
        with pytest.raises(ValueError):
            await breaker.call(failing_func)

        assert breaker.stats.state == CircuitState.OPEN

        # Reset
        breaker.reset()

        assert breaker.stats.state == CircuitState.CLOSED
        assert breaker.stats.failure_count == 0
        assert breaker.stats.total_calls == 0


class TestGlobalBreakers:
    """Test global circuit breaker instances."""

    def setup_method(self):
        """Reset breakers before each test."""
        reset_all_breakers()

    def test_get_openai_breaker(self):
        """Test getting OpenAI circuit breaker."""
        breaker1 = get_openai_breaker()
        breaker2 = get_openai_breaker()

        # Should return same instance
        assert breaker1 is breaker2
        assert breaker1.name == "openai"

    def test_reset_all_breakers(self):
        """Test resetting all global breakers."""
        breaker = get_openai_breaker()
        breaker.stats.failure_count = 5

        reset_all_breakers()

        assert breaker.stats.failure_count == 0


@pytest.mark.asyncio
async def test_circuit_breaker_with_timeout():
    """Test circuit breaker behavior with recovery timeout."""
    breaker = CircuitBreaker(
        "timeout_test",
        config=CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.2,
        ),
    )

    async def failing_func():
        raise RuntimeError("Failure")

    # Open circuit
    with pytest.raises(RuntimeError):
        await breaker.call(failing_func)

    assert breaker.stats.state == CircuitState.OPEN

    # Should still be open before timeout
    with pytest.raises(CircuitBreakerError):
        await breaker.call(failing_func)

    # Wait for timeout
    await asyncio.sleep(0.25)

    # Should transition to half-open on next call
    with pytest.raises(RuntimeError):
        await breaker.call(failing_func)

    # Should be open again after failure in half-open
    assert breaker.stats.state == CircuitState.OPEN
