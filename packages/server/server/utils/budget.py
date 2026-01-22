"""
Budget Tracker
==============

Tracks OpenAI API spend to prevent runaway costs.
Uses Redis for persistent tracking across server restarts.
"""

from datetime import datetime, timezone

from agent_core.config import settings
from server.utils.redis import RedisClient


class BudgetTracker:
    """
    Tracks API spend against daily and monthly budgets.
    
    Uses Redis keys:
    - budget:daily:{date} - Daily spend
    - budget:monthly:{year-month} - Monthly spend
    """

    def __init__(self, redis: RedisClient):
        """
        Initialize budget tracker.
        
        Args:
            redis: Redis client instance
        """
        self.redis = redis
        self.daily_limit = settings.daily_budget_usd
        self.monthly_limit = settings.monthly_budget_usd

    def _daily_key(self) -> str:
        """Get Redis key for today's spend."""
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"budget:daily:{date}"

    def _monthly_key(self) -> str:
        """Get Redis key for this month's spend."""
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        return f"budget:monthly:{month}"

    async def get_daily_spend(self) -> float:
        """
        Get today's total spend.
        
        Returns:
            Total spend in USD
        """
        if not self.redis.enabled:
            return 0.0

        value = await self.redis.get(self._daily_key())
        return float(value) if value else 0.0

    async def get_monthly_spend(self) -> float:
        """
        Get this month's total spend.
        
        Returns:
            Total spend in USD
        """
        if not self.redis.enabled:
            return 0.0

        value = await self.redis.get(self._monthly_key())
        return float(value) if value else 0.0

    async def can_spend(self, amount: float = 0.01) -> bool:
        """
        Check if we can spend the given amount.
        
        Args:
            amount: Amount to spend in USD (default: minimum for one request)
            
        Returns:
            True if within budget, False otherwise
        """
        if not self.redis.enabled:
            # If Redis is not configured, allow (no tracking)
            return True

        daily = await self.get_daily_spend()
        monthly = await self.get_monthly_spend()

        # Check both limits
        if daily + amount > self.daily_limit:
            return False

        if monthly + amount > self.monthly_limit:
            return False

        return True

    async def record_spend(self, amount: float) -> None:
        """
        Record spend for a request.
        
        Args:
            amount: Amount spent in USD
        """
        if not self.redis.enabled or amount <= 0:
            return

        # Increment daily counter
        daily_key = self._daily_key()
        await self.redis.incrbyfloat(daily_key, amount)
        # Set 48-hour expiry on daily key (buffer for timezone edge cases)
        await self.redis.expire(daily_key, 172800)

        # Increment monthly counter
        monthly_key = self._monthly_key()
        await self.redis.incrbyfloat(monthly_key, amount)
        # Set 35-day expiry on monthly key
        await self.redis.expire(monthly_key, 3024000)

    async def get_status(self) -> dict:
        """
        Get current budget status.
        
        Returns:
            Dict with spend and limit info
        """
        daily = await self.get_daily_spend()
        monthly = await self.get_monthly_spend()

        return {
            "daily_spend": round(daily, 4),
            "daily_limit": self.daily_limit,
            "daily_remaining": round(max(0, self.daily_limit - daily), 4),
            "daily_percent_used": round((daily / self.daily_limit) * 100, 1) if self.daily_limit > 0 else 0,
            "monthly_spend": round(monthly, 4),
            "monthly_limit": self.monthly_limit,
            "monthly_remaining": round(max(0, self.monthly_limit - monthly), 4),
            "monthly_percent_used": round((monthly / self.monthly_limit) * 100, 1) if self.monthly_limit > 0 else 0,
        }
