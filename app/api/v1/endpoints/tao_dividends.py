from fastapi import APIRouter, HTTPException
from typing import Optional
from ....schemas.tao_dividends import TaoDividendsResponse
from ....services.blockchain import BlockchainService

router = APIRouter()
blockchain_service = BlockchainService()

@router.get("/", response_model=TaoDividendsResponse)
async def get_dividends(
    netuid: Optional[int] = None,
    hotkey: Optional[str] = None,
    trade: bool = False,
):
    """
    Get Tao dividends for a given subnet and hotkey.
    If netuid is not provided, returns data for all netuids.
    If hotkey is not provided, returns data for all hotkeys on the specified netuid.
    If trade is True, triggers sentiment analysis and stake/unstake operations.
    """
    try:
        # Query blockchain for dividends
        result = await blockchain_service.get_tao_dividends(netuid=netuid, hotkey=hotkey)
        
        # Handle error cases
        if "error" in result:
            raise HTTPException(
                status_code=500,
                detail=result["error"]
            )
        
        # If querying all netuids
        if netuid is None:
            return TaoDividendsResponse(
                netuid=0,
                hotkey="",
                dividend=0,
                cached=False,
                stake_tx_triggered=False,
                all_netuids_data=result
            )
        
        # If querying all hotkeys for a netuid
        if hotkey is None and "results" in result:
            return TaoDividendsResponse(
                netuid=netuid,
                hotkey="",
                dividend=0,
                cached=False,
                stake_tx_triggered=False,
                all_hotkeys_data=result["results"]
            )
        
        # Single hotkey result
        return TaoDividendsResponse(
            netuid=result["netuid"],
            hotkey=result["hotkey"],
            dividend=result["dividend"],
            cached=False,
            stake_tx_triggered=False
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 