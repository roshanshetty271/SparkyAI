"""
Redis Client (Upstash)
======================

Async Redis client using Upstash's REST API.
Free tier: 10,000 commands/day.
"""

from typing import Optional, Any

from agent_core.config import settings


class RedisClient:
    """
    Async Redis client for Upstash.
    
    Uses Upstash's REST API which is perfect for serverless
    and doesn't require persistent connections.
    """

    def __init__(self, url: str, token: str):
        """
        Initialize Redis client.
        
        Args:
            url: Upstash Redis REST URL
            token: Upstash Redis REST token
        """
        self.url = url.rstrip("/")
        self.token = token
        self._enabled = bool(url and token)

    @property
    def enabled(self) -> bool:
        """Check if Redis is configured."""
        return self._enabled

    async def _request(self, *args) -> Any:
        """
        Make a request to Upstash REST API.
        
        Args:
            *args: Redis command arguments
            
        Returns:
            Command result
        """
        if not self._enabled:
            return None

        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                json=list(args),
            )

            if response.status_code != 200:
                return None

            data = response.json()
            return data.get("result")

    async def ping(self) -> bool:
        """
        Ping Redis to check connectivity.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            result = await self._request("PING")
            return result == "PONG"
        except Exception:
            return False

    async def get(self, key: str) -> Optional[str]:
        """
        Get a value from Redis.
        
        Args:
            key: Redis key
            
        Returns:
            Value if exists, None otherwise
        """
        return await self._request("GET", key)

    async def set(
        self, 
        key: str, 
        value: str, 
        ex: Optional[int] = None,
    ) -> bool:
        """
        Set a value in Redis.
        
        Args:
            key: Redis key
            value: Value to set
            ex: Optional expiration in seconds
            
        Returns:
            True if successful
        """
        if ex:
            result = await self._request("SET", key, value, "EX", str(ex))
        else:
            result = await self._request("SET", key, value)
        return result == "OK"

    async def incr(self, key: str) -> Optional[int]:
        """
        Increment a counter.
        
        Args:
            key: Redis key
            
        Returns:
            New value after increment
        """
        result = await self._request("INCR", key)
        return int(result) if result is not None else None

    async def incrbyfloat(self, key: str, amount: float) -> Optional[float]:
        """
        Increment a float counter.
        
        Args:
            key: Redis key
            amount: Amount to increment by
            
        Returns:
            New value after increment
        """
        result = await self._request("INCRBYFLOAT", key, str(amount))
        return float(result) if result is not None else None

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration on a key.
        
        Args:
            key: Redis key
            seconds: Expiration time in seconds
            
        Returns:
            True if successful
        """
        result = await self._request("EXPIRE", key, str(seconds))
        return result == 1

    async def ttl(self, key: str) -> Optional[int]:
        """
        Get time-to-live for a key.
        
        Args:
            key: Redis key
            
        Returns:
            TTL in seconds, -2 if key doesn't exist, -1 if no expiry
        """
        result = await self._request("TTL", key)
        return int(result) if result is not None else None

    async def delete(self, key: str) -> bool:
        """
        Delete a key.
        
        Args:
            key: Redis key
            
        Returns:
            True if key was deleted
        """
        result = await self._request("DEL", key)
        return result == 1

    async def hset(self, key: str, field: str, value: str) -> bool:
        """
        Set a hash field.
        
        Args:
            key: Redis key
            field: Hash field
            value: Value to set
            
        Returns:
            True if field was added (not updated)
        """
        result = await self._request("HSET", key, field, value)
        return result is not None

    async def hget(self, key: str, field: str) -> Optional[str]:
        """
        Get a hash field.
        
        Args:
            key: Redis key
            field: Hash field
            
        Returns:
            Field value if exists
        """
        return await self._request("HGET", key, field)

    async def hgetall(self, key: str) -> Optional[dict]:
        """
        Get all fields in a hash.
        
        Args:
            key: Redis key
            
        Returns:
            Dict of field -> value
        """
        result = await self._request("HGETALL", key)
        if result and isinstance(result, list):
            # Convert flat list to dict
            return dict(zip(result[::2], result[1::2]))
        return None


# Singleton instance
_redis_client: Optional[RedisClient] = None


def get_redis() -> Optional[RedisClient]:
    """
    Get the Redis client instance.
    
    Returns:
        RedisClient if configured, None otherwise
    """
    global _redis_client

    if _redis_client is None:
        if settings.redis_enabled:
            _redis_client = RedisClient(
                url=settings.upstash_redis_rest_url,
                token=settings.upstash_redis_rest_token,
            )
        else:
            return None

    return _redis_client
