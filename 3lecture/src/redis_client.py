import redis
from config import settings

# Create Redis client
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

# Test connection
def test_redis_connection():
    try:
        redis_client.ping()
        return True
    except redis.ConnectionError:
        return False

# Redis utility functions
async def set_value(key: str, value: str, expire: int = None):
    """Set a value in Redis with optional expiration"""
    if expire:
        redis_client.setex(key, expire, value)
    else:
        redis_client.set(key, value)

async def get_value(key: str):
    """Get a value from Redis"""
    return redis_client.get(key)

async def delete_key(key: str):
    """Delete a key from Redis"""
    return redis_client.delete(key)

async def exists(key: str):
    """Check if a key exists in Redis"""
    return redis_client.exists(key) 