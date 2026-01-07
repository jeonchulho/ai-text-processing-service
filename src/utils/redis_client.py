"""
Redis client for caching and message queuing.

This module provides a wrapper around Redis for caching translation results,
managing sessions, and implementing message queues using Redis Streams.
"""

import json
from typing import Optional, Any, List
import redis
from redis.exceptions import RedisError
import structlog

from src.core.config import settings
from src.core.exceptions import CacheError

logger = structlog.get_logger(__name__)


class RedisClient:
    """Redis client wrapper with caching and pub/sub functionality."""

    def __init__(self):
        """Initialize Redis client."""
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            self.client.ping()
            logger.info("Redis client initialized successfully")
        except RedisError as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise CacheError(f"Redis connection failed: {e}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except RedisError as e:
            logger.error(f"Redis get error for key {key}: {e}")
            raise CacheError(f"Failed to get from cache: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for key {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default from settings)

        Returns:
            True if successful
        """
        try:
            ttl = ttl or settings.REDIS_CACHE_TTL
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
            return True
        except RedisError as e:
            logger.error(f"Redis set error for key {key}: {e}")
            raise CacheError(f"Failed to set cache: {e}")
        except (TypeError, ValueError) as e:
            logger.error(f"JSON encode error for key {key}: {e}")
            raise CacheError(f"Failed to serialize value: {e}")

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted
        """
        try:
            result = self.client.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            raise CacheError(f"Failed to delete from cache: {e}")

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists
        """
        try:
            return self.client.exists(key) > 0
        except RedisError as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    def get_ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        try:
            return self.client.ttl(key)
        except RedisError as e:
            logger.error(f"Redis TTL error for key {key}: {e}")
            return -2

    def keys_pattern(self, pattern: str) -> List[str]:
        """
        Get keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "translation:*")

        Returns:
            List of matching keys
        """
        try:
            return self.client.keys(pattern)
        except RedisError as e:
            logger.error(f"Redis keys error for pattern {pattern}: {e}")
            return []

    def flush_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "translation:*")

        Returns:
            Number of keys deleted
        """
        try:
            keys = self.keys_pattern(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Redis flush pattern error for {pattern}: {e}")
            return 0

    def publish(self, channel: str, message: Any) -> int:
        """
        Publish message to a channel.

        Args:
            channel: Channel name
            message: Message to publish (will be JSON serialized)

        Returns:
            Number of subscribers that received the message
        """
        try:
            serialized = json.dumps(message)
            return self.client.publish(channel, serialized)
        except RedisError as e:
            logger.error(f"Redis publish error for channel {channel}: {e}")
            raise CacheError(f"Failed to publish message: {e}")

    def subscribe(self, *channels: str):
        """
        Subscribe to channels.

        Args:
            channels: Channel names to subscribe to

        Returns:
            PubSub object
        """
        try:
            pubsub = self.client.pubsub()
            pubsub.subscribe(*channels)
            return pubsub
        except RedisError as e:
            logger.error(f"Redis subscribe error: {e}")
            raise CacheError(f"Failed to subscribe: {e}")

    def health_check(self) -> bool:
        """
        Check if Redis is healthy.

        Returns:
            True if Redis is responsive
        """
        try:
            return self.client.ping()
        except RedisError:
            return False


# Global Redis client instance
redis_client = RedisClient()
