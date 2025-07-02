"""
Caching utilities for Document Server
"""

import functools
import hashlib
import json
from typing import Any, Optional, Callable
from flask import request, current_app
from ..redis_config import get_redis
import logging

logger = logging.getLogger(__name__)

def cache_key_generator(*args, **kwargs) -> str:
    """Generate a cache key from function arguments and request data"""
    # Include function name and arguments
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    
    # Include user ID if available
    try:
        from flask_login import current_user
        if current_user.is_authenticated:
            key_parts.append(f"user:{current_user.id}")
    except:
        pass
    
    # Include request path for route-specific caching
    try:
        key_parts.append(f"path:{request.path}")
    except:
        pass
    
    # Create hash of the key parts
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def cache(expire: int = 300, key_prefix: str = "cache"):
    """
    Cache decorator for Flask routes
    
    Args:
        expire: Cache expiration time in seconds (default: 5 minutes)
        key_prefix: Prefix for cache keys
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            redis_manager = get_redis()
            
            # Skip caching if Redis is not available
            if not redis_manager.is_connected():
                return func(*args, **kwargs)
            
            # Generate cache key
            cache_key = f"{key_prefix}:{cache_key_generator(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = redis_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            # Cache the result
            try:
                redis_manager.set(cache_key, result, expire=expire)
                logger.debug(f"Cached result for key: {cache_key} (expires in {expire}s)")
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")
            
            return result
        
        return wrapper
    return decorator

def invalidate_cache(pattern: str = None):
    """
    Decorator to invalidate cache after function execution
    
    Args:
        pattern: Cache key pattern to invalidate (e.g., "cache:user:*")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            redis_manager = get_redis()
            if redis_manager.is_connected() and pattern:
                try:
                    # Find and delete keys matching pattern
                    keys = redis_manager.redis_client.keys(pattern)
                    if keys:
                        redis_manager.redis_client.delete(*keys)
                        logger.debug(f"Invalidated {len(keys)} cache keys matching pattern: {pattern}")
                except Exception as e:
                    logger.warning(f"Failed to invalidate cache: {e}")
            
            return result
        
        return wrapper
    return decorator

class CacheManager:
    """Utility class for cache operations"""
    
    @staticmethod
    def set_user_cache(user_id: int, key: str, value: Any, expire: int = 300) -> bool:
        """Set cache for a specific user"""
        redis_manager = get_redis()
        if not redis_manager.is_connected():
            return False
        
        cache_key = f"user:{user_id}:{key}"
        return redis_manager.set(cache_key, value, expire=expire)
    
    @staticmethod
    def get_user_cache(user_id: int, key: str, default: Any = None) -> Any:
        """Get cache for a specific user"""
        redis_manager = get_redis()
        if not redis_manager.is_connected():
            return default
        
        cache_key = f"user:{user_id}:{key}"
        return redis_manager.get(cache_key, default)
    
    @staticmethod
    def delete_user_cache(user_id: int, key: str = None) -> bool:
        """Delete cache for a specific user"""
        redis_manager = get_redis()
        if not redis_manager.is_connected():
            return False
        
        if key:
            cache_key = f"user:{user_id}:{key}"
            return redis_manager.delete(cache_key)
        else:
            # Delete all cache for user
            pattern = f"user:{user_id}:*"
            try:
                keys = redis_manager.redis_client.keys(pattern)
                if keys:
                    redis_manager.redis_client.delete(*keys)
                    return True
                return False
            except Exception as e:
                logger.error(f"Failed to delete user cache: {e}")
                return False
    
    @staticmethod
    def set_file_cache(file_id: int, key: str, value: Any, expire: int = 300) -> bool:
        """Set cache for a specific file"""
        redis_manager = get_redis()
        if not redis_manager.is_connected():
            return False
        
        cache_key = f"file:{file_id}:{key}"
        return redis_manager.set(cache_key, value, expire=expire)
    
    @staticmethod
    def get_file_cache(file_id: int, key: str, default: Any = None) -> Any:
        """Get cache for a specific file"""
        redis_manager = get_redis()
        if not redis_manager.is_connected():
            return default
        
        cache_key = f"file:{file_id}:{key}"
        return redis_manager.get(cache_key, default)
    
    @staticmethod
    def delete_file_cache(file_id: int, key: str = None) -> bool:
        """Delete cache for a specific file"""
        redis_manager = get_redis()
        if not redis_manager.is_connected():
            return False
        
        if key:
            cache_key = f"file:{file_id}:{key}"
            return redis_manager.delete(cache_key)
        else:
            # Delete all cache for file
            pattern = f"file:{file_id}:*"
            try:
                keys = redis_manager.redis_client.keys(pattern)
                if keys:
                    redis_manager.redis_client.delete(*keys)
                    return True
                return False
            except Exception as e:
                logger.error(f"Failed to delete file cache: {e}")
                return False 