from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any, Union
from ....schemas.tao_dividends import (
    TaoDividendsResponse,
    NetuidDividendsResponse,
    AllNetuidsResponse
)
from ....services.blockchain_service import BlockchainService
from ....services.sentiment_service import SentimentService
from ....services.redis_service import redis_service

router = APIRouter()
blockchain_service = BlockchainService()
sentiment_service = SentimentService()

@router.get("/", response_model=Union[TaoDividendsResponse, NetuidDividendsResponse, AllNetuidsResponse])
async def get_dividends(
    netuid: Optional[int] = None,
    hotkey: Optional[str] = None,
    trade: bool = False,
):
    """
    Get Tao dividends for a given subnet and hotkey.
    
    Parameters:
    - netuid: Optional subnet ID. If not provided, returns data for all netuids.
    - hotkey: Optional hotkey address. If not provided, returns data for all hotkeys on the specified netuid.
    - trade: If True, triggers sentiment analysis and stake/unstake operations.
    
    Returns:
    - If netuid is None: Returns data for all netuids (AllNetuidsResponse)
    - If hotkey is None: Returns data for all hotkeys in the netuid (NetuidDividendsResponse)
    - If both are provided: Returns data for specific hotkey (TaoDividendsResponse)
    """
    try:
        # Query blockchain for dividends
        result = await blockchain_service.get_tao_dividends(netuid=netuid, hotkey=hotkey)
        
        # Handle error cases
        if "error" in result:
            raise HTTPException(
                status_code=500,
                detail=f"Blockchain service error: {result['error']}"
            )
        
        # Validate required fields
        if not all(key in result for key in ["cached", "timestamp"]):
            missing_fields = [key for key in ["cached", "timestamp"] if key not in result]
            raise HTTPException(
                status_code=500,
                detail=f"Missing required fields in response: {', '.join(missing_fields)}"
            )
        
        # If trade is enabled and netuid is provided, perform sentiment analysis
        if trade and netuid is not None:
            try:
                # Get sentiment analysis for the netuid
                sentiment_result = await sentiment_service.get_twitter_sentiment(f"Bittensor netuid {netuid}")
                
                print(f"sentiment_result: {sentiment_result}")

                if sentiment_result.get("success", False):
                    # Calculate stake amount based on sentiment score
                    sentiment_score = sentiment_result["sentiment_score"]
                    stake_amount = sentiment_service.get_stake_amount(sentiment_score)
                    
                    # Publish stake task to Redis for background processing
                    await redis_service.publish_stake_task(netuid, hotkey, sentiment_score)
                    
                    print(f"\nSentiment Analysis Results:")
                    print(f"Netuid: {netuid}")
                    print(f"Hotkey: {hotkey}")
                    print(f"Sentiment Score: {sentiment_score}")
                    print(f"Stake Amount: {stake_amount} TAO")
                    print(f"Tweet Count: {sentiment_result['tweet_count']}")
                    print(f"Sample Tweets: {sentiment_result['tweets'][:3]}")
                else:
                    print(f"\nSentiment Analysis Failed:")
                    print(f"Error: {sentiment_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"\nError in sentiment analysis: {str(e)}")
        
        # If querying all netuids
        if netuid is None:
            if "all_netuids" not in result:
                raise HTTPException(
                    status_code=500,
                    detail="Missing 'all_netuids' field in response"
                )
            return AllNetuidsResponse(
                all_netuids=result["all_netuids"],
                cached=result["cached"],
                timestamp=result["timestamp"]
            )
        
        # If querying all hotkeys for a netuid
        if hotkey is None:
            if "results" not in result:
                raise HTTPException(
                    status_code=500,
                    detail="Missing 'results' field in response"
                )
            return NetuidDividendsResponse(
                netuid=netuid,
                results=result["results"],
                cached=result["cached"],
                timestamp=result["timestamp"]
            )
        
        # Single hotkey result
        if not all(key in result for key in ["netuid", "hotkey", "dividend"]):
            missing_fields = [key for key in ["netuid", "hotkey", "dividend"] if key not in result]
            raise HTTPException(
                status_code=500,
                detail=f"Missing required fields for hotkey response: {', '.join(missing_fields)}"
            )
            
        return TaoDividendsResponse(
            netuid=result["netuid"],
            hotkey=result["hotkey"],
            dividend=result["dividend"],
            cached=result["cached"],
            timestamp=result["timestamp"],
            stake_tx_triggered=trade  # Set to true if trade is enabled
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        ) 