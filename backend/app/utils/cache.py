"""
cache.py - Redis cache utility for CodeMentor AI

Provides simple get/set/delete operations with TTL (time-to-live).
All values are stored as JSON strings in Redis.

Redis Key Patterns:
    repo:status:{repo_id}     -> ingestion status (TTL: 5 min)
    repo:files:{repo_id}      -> file list cache (TTL: 30 min)
    chat:{repo_id}:{hash}     -> chat answer cache (TTL: 10 min)
"""

import json
from typing import Any, Optional

import redis

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RedisCache:
    """
    Simple Redis cache wrapper.

    Handles connection, serialization (JSON), and TTL-based expiration.
    If Redis is unavailable, operations fail gracefully (log warning, return None).
    """

    def __init__(self):
        """Connect to Redis using the URL from environment variables."""
        try:
            self.client = redis.from_url(
                settings.redis_url,
                decode_responses=True,  # Return strings, not bytes
                socket_connect_timeout=5,  # Don't hang if Redis is down
            )
            # Test the connection
            self.client.ping()
            self.is_connected = True
            logger.info("Redis cache connected successfully")
        except redis.ConnectionError:
            self.client = None
            self.is_connected = False
            logger.warning("Redis not available - cache disabled. App will still work.")

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """
        Store a value in Redis with expiration.

        Args:
            key: The cache key (e.g., "repo:status:my-repo")
            value: Any JSON-serializable Python object
            ttl_seconds: Time-to-live in seconds (default 5 minutes)

        Returns:
            True if stored successfully, False otherwise
        """
        if not self.is_connected:
            return False

        try:
            json_value = json.dumps(value)
            self.client.setex(key, ttl_seconds, json_value)
            logger.info(f"Cache SET: {key} (TTL: {ttl_seconds}s)")
            return True
        except (redis.RedisError, json.JSONEncodeError) as error:
            logger.warning(f"Cache SET failed for {key}: {error}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from Redis.

        Args:
            key: The cache key to look up

        Returns:
            The cached Python object, or None if not found / expired / error
        """
        if not self.is_connected:
            return None

        try:
            json_value = self.client.get(key)
            if json_value is None:
                logger.info(f"Cache MISS: {key}")
                return None

            logger.info(f"Cache HIT: {key}")
            return json.loads(json_value)
        except (redis.RedisError, json.JSONDecodeError) as error:
            logger.warning(f"Cache GET failed for {key}: {error}")
            return None

    def delete(self, key: str) -> bool:
        """
        Remove a key from Redis.

        Args:
            key: The cache key to delete

        Returns:
            True if deleted, False otherwise
        """
        if not self.is_connected:
            return False

        try:
            self.client.delete(key)
            logger.info(f"Cache DELETE: {key}")
            return True
        except redis.RedisError as error:
            logger.warning(f"Cache DELETE failed for {key}: {error}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        Useful for clearing all cache for a specific repo.

        Args:
            pattern: Redis key pattern (e.g., "repo:*:my-repo")

        Returns:
            Number of keys deleted
        """
        if not self.is_connected:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                count = self.client.delete(*keys)
                logger.info(f"Cache DELETE PATTERN: {pattern} ({count} keys)")
                return count
            return 0
        except redis.RedisError as error:
            logger.warning(f"Cache DELETE PATTERN failed for {pattern}: {error}")
            return 0


# Single cache instance used across the app
cache = RedisCache()
