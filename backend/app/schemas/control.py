from typing import Optional
from pydantic import BaseModel
from app.core.constants import BotState

class StateResponseDTO(BaseModel):
    current_state: BotState
    is_running: bool
    is_paused: bool
    is_emergency_stopped: bool
    emergency_reason: Optional[str] = None

class StateCommandResponseDTO(BaseModel):
    status: str
    previous_state: BotState
    new_state: BotState
    operator: str
