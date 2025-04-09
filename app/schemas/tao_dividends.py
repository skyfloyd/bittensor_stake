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
    timestamp: str
    stake_tx_triggered: bool

class NetuidDividendsResponse(BaseModel):
    netuid: int
    results: List[Dict[str, Any]]
    cached: bool
    timestamp: str

class AllNetuidsResponse(BaseModel):
    all_netuids: Dict[int, Dict[str, Any]]
    cached: bool
    timestamp: str 