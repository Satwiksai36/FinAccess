import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def get_redis_client() -> redis.Redis:
    """
    Initializes an asynchronous connection pool to Redis based on the application config.
    Applies production-grade socket pooling and strict timeout bounds.
    """
    logger.info(f"Connecting to Redis at {settings.REDIS_URL} with TTL {settings.CACHE_TTL}s")
    pool = redis.ConnectionPool.from_url(
        settings.REDIS_URL, 
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=2,
        retry_on_timeout=True,
        max_connections=50
    )
    client = redis.Redis(connection_pool=pool)
    return client
