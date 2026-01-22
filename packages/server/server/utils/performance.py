"""
Performance monitoring and profiling utilities.

Provides decorators and utilities for tracking API endpoint performance,
database query times, and identifying bottlenecks.
"""

import time
import logging
import functools
from typing import Callable, Any, Optional
from contextlib import asynccontextmanager
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Monitor and log performance metrics for functions and API endpoints.
    
    Tracks:
    - Execution time
    - Call frequency
    - Slow queries (> threshold)
    - Error rates
    """

    def __init__(self, slow_threshold_ms: float = 1000.0):
        """
        Initialize monitor.
        
        Args:
            slow_threshold_ms: Threshold for logging slow operations (milliseconds)
        """
        self.slow_threshold_ms = slow_threshold_ms
        self.metrics = {}

    def track(
        self,
        name: Optional[str] = None,
        log_args: bool = False,
        log_result: bool = False
    ) -> Callable:
        """
        Decorator to track function performance.
        
        Args:
            name: Custom name for the operation (defaults to function name)
            log_args: Whether to log function arguments
            log_result: Whether to log function result
            
        Returns:
            Decorated function
        """

        def decorator(func: Callable) -> Callable:
            op_name = name or f"{func.__module__}.{func.__name__}"

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                error = None

                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    self._record_metric(op_name, elapsed_ms, error, args, kwargs, log_args)

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                error = None

                try:
                    result = await func(*args, **kwargs)
                    if log_result and result is not None:
                        logger.debug(f"{op_name} result: {result}")
                    return result
                except Exception as e:
                    error = e
                    raise
                finally:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    self._record_metric(op_name, elapsed_ms, error, args, kwargs, log_args)

            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def _record_metric(
        self,
        name: str,
        elapsed_ms: float,
        error: Optional[Exception],
        args: tuple,
        kwargs: dict,
        log_args: bool
    ):
        """Record performance metric."""
        # Update metrics
        if name not in self.metrics:
            self.metrics[name] = {
                "count": 0,
                "total_time_ms": 0,
                "min_time_ms": float("inf"),
                "max_time_ms": 0,
                "errors": 0,
                "slow_calls": 0,
            }

        metric = self.metrics[name]
        metric["count"] += 1
        metric["total_time_ms"] += elapsed_ms
        metric["min_time_ms"] = min(metric["min_time_ms"], elapsed_ms)
        metric["max_time_ms"] = max(metric["max_time_ms"], elapsed_ms)

        if error:
            metric["errors"] += 1

        # Log slow operations
        if elapsed_ms > self.slow_threshold_ms:
            metric["slow_calls"] += 1
            log_msg = f"SLOW: {name} took {elapsed_ms:.2f}ms"
            if log_args:
                log_msg += f" (args={args}, kwargs={kwargs})"
            logger.warning(log_msg)
        else:
            logger.debug(f"{name} completed in {elapsed_ms:.2f}ms")

    def get_stats(self) -> dict:
        """Get performance statistics for all tracked operations."""
        stats = {}
        for name, metric in self.metrics.items():
            count = metric["count"]
            if count > 0:
                avg_time = metric["total_time_ms"] / count
                error_rate = metric["errors"] / count
                slow_rate = metric["slow_calls"] / count

                stats[name] = {
                    "call_count": count,
                    "avg_time_ms": round(avg_time, 2),
                    "min_time_ms": round(metric["min_time_ms"], 2),
                    "max_time_ms": round(metric["max_time_ms"], 2),
                    "total_time_ms": round(metric["total_time_ms"], 2),
                    "error_rate": round(error_rate, 4),
                    "slow_call_rate": round(slow_rate, 4),
                    "errors": metric["errors"],
                    "slow_calls": metric["slow_calls"],
                }

        return stats

    def reset_stats(self):
        """Reset all performance statistics."""
        self.metrics = {}

    def log_stats(self, top_n: int = 10):
        """Log performance statistics for top N slowest operations."""
        stats = self.get_stats()
        if not stats:
            logger.info("No performance metrics available")
            return

        # Sort by average time
        sorted_stats = sorted(
            stats.items(), key=lambda x: x[1]["avg_time_ms"], reverse=True
        )

        logger.info(f"\n{'=' * 80}")
        logger.info(f"Performance Statistics (Top {top_n} Slowest Operations)")
        logger.info(f"{'=' * 80}")

        for i, (name, metric) in enumerate(sorted_stats[:top_n], 1):
            logger.info(f"\n{i}. {name}")
            logger.info(f"   Calls: {metric['call_count']}")
            logger.info(f"   Avg Time: {metric['avg_time_ms']:.2f}ms")
            logger.info(f"   Min/Max: {metric['min_time_ms']:.2f}ms / {metric['max_time_ms']:.2f}ms")
            logger.info(f"   Error Rate: {metric['error_rate'] * 100:.2f}%")
            logger.info(f"   Slow Call Rate: {metric['slow_call_rate'] * 100:.2f}%")

        logger.info(f"{'=' * 80}\n")


# Global performance monitor instance
_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor(slow_threshold_ms: float = 1000.0) -> PerformanceMonitor:
    """Get or create global performance monitor."""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor(slow_threshold_ms)
    return _monitor


@asynccontextmanager
async def measure_time(operation_name: str):
    """
    Context manager to measure execution time.
    
    Usage:
        async with measure_time("database_query"):
            result = await db.query(...)
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.debug(f"{operation_name} took {elapsed_ms:.2f}ms")


def time_it(func: Callable) -> Callable:
    """
    Simple decorator to time function execution.
    
    Usage:
        @time_it
        async def my_function():
            pass
    """

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"{func.__name__} took {elapsed_ms:.2f}ms")

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"{func.__name__} took {elapsed_ms:.2f}ms")

    # Return appropriate wrapper
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class RequestTimer:
    """Track request timing for FastAPI endpoints."""

    def __init__(self):
        """Initialize request timer."""
        self.timings = []

    async def __call__(self, request, call_next):
        """Middleware to time requests."""
        start_time = time.perf_counter()

        response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Add timing header
        response.headers["X-Response-Time"] = f"{elapsed_ms:.2f}ms"

        # Log slow requests
        if elapsed_ms > 1000:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} took {elapsed_ms:.2f}ms"
            )

        # Store timing
        self.timings.append({
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "elapsed_ms": elapsed_ms,
            "status_code": response.status_code,
        })

        # Keep only last 1000 requests
        if len(self.timings) > 1000:
            self.timings = self.timings[-1000:]

        return response

    def get_stats(self):
        """Get request timing statistics."""
        if not self.timings:
            return {}

        times = [t["elapsed_ms"] for t in self.timings]
        return {
            "total_requests": len(times),
            "avg_time_ms": sum(times) / len(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "p50_ms": sorted(times)[len(times) // 2],
            "p95_ms": sorted(times)[int(len(times) * 0.95)],
            "p99_ms": sorted(times)[int(len(times) * 0.99)],
        }


# Import asyncio for coroutine checks
import asyncio
