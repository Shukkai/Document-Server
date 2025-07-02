"""
Redis-related routes for Document Server
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ..redis_config import get_redis
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('redis', __name__, url_prefix='/redis')

@bp.route('/health', methods=['GET'])
def redis_health():
    """Check Redis connection health"""
    redis_manager = get_redis()
    
    if redis_manager.is_connected():
        try:
            # Test basic operations
            test_key = "health_check"
            redis_manager.set(test_key, "ok", expire=10)
            value = redis_manager.get(test_key)
            redis_manager.delete(test_key)
            
            return jsonify({
                "status": "healthy",
                "connected": True,
                "test_passed": value == "ok"
            })
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return jsonify({
                "status": "unhealthy",
                "connected": True,
                "error": str(e)
            }), 500
    else:
        return jsonify({
            "status": "unhealthy",
            "connected": False,
            "error": "Redis not connected"
        }), 503

@bp.route('/cache/stats', methods=['GET'])
@login_required
def cache_stats():
    """Get cache statistics (admin only)"""
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403
    
    redis_manager = get_redis()
    
    if not redis_manager.is_connected():
        return jsonify({"error": "Redis not connected"}), 503
    
    try:
        # Get basic Redis info
        info = redis_manager.redis_client.info()
        
        return jsonify({
            "connected": True,
            "used_memory_human": info.get('used_memory_human'),
            "connected_clients": info.get('connected_clients'),
            "total_commands_processed": info.get('total_commands_processed'),
            "keyspace_hits": info.get('keyspace_hits'),
            "keyspace_misses": info.get('keyspace_misses'),
            "uptime_in_seconds": info.get('uptime_in_seconds')
        })
    except Exception as e:
        logger.error(f"Failed to get Redis stats: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/cache/clear', methods=['POST'])
@login_required
def clear_cache():
    """Clear all cache (admin only)"""
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403
    
    redis_manager = get_redis()
    
    if not redis_manager.is_connected():
        return jsonify({"error": "Redis not connected"}), 503
    
    try:
        success = redis_manager.flush_all()
        if success:
            return jsonify({"message": "Cache cleared successfully"})
        else:
            return jsonify({"error": "Failed to clear cache"}), 500
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/cache/key/<key>', methods=['GET'])
@login_required
def get_cache_key(key):
    """Get a specific cache key (admin only)"""
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403
    
    redis_manager = get_redis()
    
    if not redis_manager.is_connected():
        return jsonify({"error": "Redis not connected"}), 503
    
    try:
        value = redis_manager.get(key)
        ttl = redis_manager.ttl(key)
        
        return jsonify({
            "key": key,
            "value": value,
            "ttl": ttl,
            "exists": value is not None
        })
    except Exception as e:
        logger.error(f"Failed to get cache key {key}: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/cache/key/<key>', methods=['DELETE'])
@login_required
def delete_cache_key(key):
    """Delete a specific cache key (admin only)"""
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403
    
    redis_manager = get_redis()
    
    if not redis_manager.is_connected():
        return jsonify({"error": "Redis not connected"}), 503
    
    try:
        success = redis_manager.delete(key)
        return jsonify({
            "key": key,
            "deleted": success
        })
    except Exception as e:
        logger.error(f"Failed to delete cache key {key}: {e}")
        return jsonify({"error": str(e)}), 500 