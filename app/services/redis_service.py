from typing import Optional, Any, Dict
import json
from datetime import datetime, timedelta
import redis.asyncio as redis
from ..core.config import get_settings

settings = get_settings()

class RedisService:
    def __init__(self):
        """Initialize Redis connection."""
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.cache_ttl = settings.CACHE_TTL

    async def get_cached_dividends(self, netuid: int, hotkey: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached dividends data for a netuid and optional hotkey.
        
        Args:
            netuid: The subnet ID
            hotkey: Optional hotkey to get specific dividend data
            
        Returns:
            Cached data if exists, None otherwise
        """
        cache_key = f"dividends:netuid:{netuid}"
        if hotkey:
            cache_key += f":hotkey:{hotkey}"
            
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None

    async def cache_dividends(self, netuid: int, data: Dict[str, Any], hotkey: Optional[str] = None):
        """
        Cache dividends data for a netuid and optional hotkey.
        
        Args:
            netuid: The subnet ID
            data: The data to cache
            hotkey: Optional hotkey to cache specific dividend data
        """
        cache_key = f"dividends:netuid:{netuid}"
        if hotkey:
            cache_key += f":hotkey:{hotkey}"
            
        await self.redis.setex(
            cache_key,
            self.cache_ttl,
            json.dumps(data)
        )

    async def publish_stake_task(self, netuid: int, hotkey: str, sentiment_score: float):
        """
        Publish a stake task to Redis for background processing.
        
        This method is used to trigger stake/unstake operations based on sentiment analysis.
        It publishes a message to the 'stake_tasks' channel in Redis, which can be consumed
        by Celery workers or other background processes.
        
        The task includes:
        - netuid: The subnet ID to stake/unstake on
        - hotkey: The hotkey to stake/unstake for
        - sentiment_score: A value between -100 and +100 indicating sentiment
        - timestamp: When the task was created
        
        Args:
            netuid: The subnet ID
            hotkey: The hotkey to stake/unstake for
            sentiment_score: The sentiment score (-100 to +100)
        """
        task_data = {
            "netuid": netuid,
            "hotkey": hotkey,
            "sentiment_score": sentiment_score,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.redis.publish(
            "stake_tasks",
            json.dumps(task_data)
        )

# Create a global instance
redis_service = RedisService() 