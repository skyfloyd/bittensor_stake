from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any, Union
from ....schemas.tao_dividends import (
    TaoDividendsResponse,
    NetuidDividendsResponse,
    AllNetuidsResponse
)
from ....services.blockchain_service import BlockchainService

router = APIRouter()
blockchain_service = BlockchainService()

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
    - trade: If True, triggers sentiment analysis and stake/unstake operations (not implemented yet).
    
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
            stake_tx_triggered=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        ) 