from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any, Union
from ....schemas.tao_dividends import (
    TaoDividendsResponse,
    NetuidDividendsResponse,
    AllNetuidsResponse
)
from ....services.blockchain_service import BlockchainService
from ....services.sentiment_service import SentimentService
from ....tasks.sentiment import analyze_sentiment_and_stake
import logging

router = APIRouter()
blockchain_service = BlockchainService()
sentiment_service = SentimentService()
logger = logging.getLogger(__name__)

@router.get("/", response_model=Union[TaoDividendsResponse, NetuidDividendsResponse, AllNetuidsResponse])
async def get_dividends(
    netuid: Optional[int] = None,
    hotkey: Optional[str] = None,
    trade: bool = False,
    background_tasks: BackgroundTasks = None
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
        
        # If trade is enabled and netuid is provided, trigger Celery task
        if trade and netuid is not None and hotkey is not None:
            try:
                # Trigger Celery task for sentiment analysis and stake operations
                logger.info(f"Triggering sentiment analysis task for netuid={netuid}, hotkey={hotkey}")
                task = analyze_sentiment_and_stake.delay(netuid, hotkey)
                logger.info(f"Sentiment analysis task triggered with ID: {task.id}")
                
                # Add task to background tasks to track its status
                if background_tasks:
                    background_tasks.add_task(
                        track_task_status,
                        task_id=task.id,
                        netuid=netuid,
                        hotkey=hotkey
                    )
            except Exception as e:
                logger.error(f"Error triggering sentiment analysis task: {str(e)}")
                # Don't raise the error, just log it and continue
        
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
        logger.error(f"Internal server error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

async def track_task_status(task_id: str, netuid: int, hotkey: str):
    """Track the status of a Celery task."""
    try:
        task = analyze_sentiment_and_stake.AsyncResult(task_id)
        if task.state == 'FAILURE':
            logger.error(f"Task {task_id} failed: {task.result}")
        elif task.state == 'SUCCESS':
            logger.info(f"Task {task_id} completed successfully: {task.result}")
        else:
            logger.info(f"Task {task_id} is in state: {task.state}")
    except Exception as e:
        logger.error(f"Error tracking task {task_id}: {str(e)}", exc_info=True) 