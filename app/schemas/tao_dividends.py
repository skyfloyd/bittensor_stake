from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class HotkeyDividend(BaseModel):
    hotkey: str
    dividend: float
    timestamp: str

class TaoDividendsResponse(BaseModel):
    netuid: int
    hotkey: str
    dividend: float
    cached: bool
    stake_tx_triggered: bool
    all_netuids_data: Optional[Dict[str, Any]] = None
    all_hotkeys_data: Optional[List[HotkeyDividend]] = None 