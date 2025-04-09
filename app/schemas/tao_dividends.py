from pydantic import BaseModel

class TaoDividendsResponse(BaseModel):
    netuid: int
    hotkey: str
    dividend: int
    cached: bool
    stake_tx_triggered: bool 