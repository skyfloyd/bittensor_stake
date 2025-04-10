from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any
from datetime import datetime
from ..core.config import get_settings

# Get settings
settings = get_settings()

class MongoDBService:
    def __init__(self):
        self.mongodb_url = settings.MONGODB_URL
        self.db_name = settings.MONGODB_DB_NAME
        self.client = AsyncIOMotorClient(self.mongodb_url)
        self.db = self.client[self.db_name]
        self.stake_collection = self.db["stake"]

    async def create_stake_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new document in the stake collection.
        
        Args:
            data: Dictionary containing stake operation data
            
        Returns:
            Dict containing the created document
        """
        document = {
            "netuid": data["netuid"],
            "hotkey": data["hotkey"],
            "sentiment_score": data["sentiment_score"],
            "stake_amount": data["stake_amount"],
            "operation": data["stake_operation"],
            "created_at": datetime.utcnow(),
            "success": data["success"],
            "tweet_count": data.get("tweet_count", 0),
            "sample_tweets": data.get("sample_tweets", [])
        }
        
        result = await self.stake_collection.insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document

# Create a singleton instance
mongodb_service = MongoDBService() 