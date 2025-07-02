"""
Redis configuration and utilities for Document Server
"""

import os
import redis
from flask import current_app
import json
from typing import Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis connection manager and utility class"""
    
    def __init__(self, app=None):
        self.redis_client = None
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a key-value pair in Redis"""
        if not self.is_connected():
            return False
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            self.redis_client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from Redis"""
        if not self.is_connected():
            return default
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return default
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except:
                return value
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """Delete a key from Redis"""
        if not self.is_connected():
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis"""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key"""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis expire error: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get time to live for a key"""
        if not self.is_connected():
            return -1
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error: {e}")
            return -1
    
    def flush_all(self) -> bool:
        """Clear all keys from Redis (use with caution)"""
        if not self.is_connected():
            return False
        
        try:
            self.redis_client.flushall()
            return True
        except Exception as e:
            logger.error(f"Redis flush error: {e}")
            return False

# Global Redis manager instance
redis_manager = RedisManager()

def init_redis(app):
    """Initialize Redis for the Flask app"""
    redis_manager.init_app(app)
    return redis_manager

def get_redis() -> RedisManager:
    """Get the Redis manager instance"""
    return redis_manager 