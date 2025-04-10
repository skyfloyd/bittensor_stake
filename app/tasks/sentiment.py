from typing import Dict, Any
from asgiref.sync import async_to_sync
from ..services.sentiment_service import SentimentService
from ..services.stake_service import StakeService
from ..services.mongodb_service import mongodb_service
from ..core.celery_app import celery
import logging

# Initialize services
sentiment_service = SentimentService()
stake_service = StakeService()

# Configure logging
logger = logging.getLogger(__name__)

@celery.task(
    name='analyze_sentiment_and_stake',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def analyze_sentiment_and_stake(self, netuid: int, hotkey: str) -> Dict[str, Any]:
    """
    Celery task to analyze sentiment and handle stake operations.
    
    Args:
        netuid: The subnet ID
        hotkey: The hotkey address
        
    Returns:
        Dict containing task results
    """
    logger.info(f"Starting sentiment analysis task for netuid={netuid}, hotkey={hotkey}")
    
    try:
        # Get sentiment analysis for the netuid using async_to_sync
        logger.info("Getting Twitter sentiment...")
        sentiment_result = async_to_sync(sentiment_service.get_twitter_sentiment)(f"Bittensor netuid {netuid}")
        
        logger.info(f"Sentiment result: {sentiment_result}")

        if sentiment_result.get("success", False):
            # Calculate stake amount based on sentiment score
            sentiment_score = sentiment_result["sentiment_score"]
            stake_amount = async_to_sync(sentiment_service.get_stake_amount)(sentiment_score)

            logger.info(f"Calculated stake amount: {stake_amount} sentiment_score: {sentiment_score}")
            
            # Execute stake operation based on sentiment
            logger.info("Executing stake operation...")
            # stake_result = async_to_sync(stake_service.execute_stake_operation)(
            #     netuid=netuid,
            #     hotkey=hotkey,
            #     sentiment_score=sentiment_score,
            #     stake_amount=stake_amount
            # )

            # Determine stake operation based on sentiment score
            if sentiment_score > 0:
                stake_operation = "add_stake"
            elif sentiment_score < 0:
                stake_operation = "remove_stake"
            else:
                stake_operation = "none"

            result = {
                "success": True,
                "netuid": netuid,
                "hotkey": hotkey,
                "sentiment_score": sentiment_score,
                "stake_amount": stake_amount,
                "stake_operation": stake_operation,
                # "stake_result": stake_result,
                "tweet_count": sentiment_result["tweet_count"],
                "sample_tweets": sentiment_result["tweets"][:3]
            }
        else:
            logger.error(f"Sentiment analysis failed: {sentiment_result.get('error', 'Unknown error')}")

            result = {
                "success": False,
                "netuid": netuid,
                "hotkey": hotkey,
                "error": sentiment_result.get("error", "Unknown error")
            }
            
        # Store the result in MongoDB
        logger.info("Storing result in MongoDB...")
        async_to_sync(mongodb_service.create_stake_document)(result)
            
        logger.info(f"Task completed with result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Task failed with error: {str(e)}", exc_info=True)
        # Create error result
        error_result = {
            "success": False,
            "netuid": netuid,
            "hotkey": hotkey,
            "error": str(e)
        }
        # Store error in MongoDB
        async_to_sync(mongodb_service.create_stake_document)(error_result)
        # Retry the task if it fails
        self.retry(exc=e)
        return error_result
