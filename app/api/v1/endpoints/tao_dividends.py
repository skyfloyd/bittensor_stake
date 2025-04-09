from fastapi import APIRouter
from typing import Optional
from ....schemas.tao_dividends import TaoDividendsResponse

router = APIRouter()

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
    return TaoDividendsResponse(
        netuid=netuid or 0,
        hotkey=hotkey or "",
        dividend=0,
        cached=False,
        stake_tx_triggered=False
    ) 