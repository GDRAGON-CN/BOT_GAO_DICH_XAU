from typing import Optional
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
from app.core.constants import RiskAction, RiskEventType

class RiskValidationResultDTO(BaseModel):
    is_valid: bool
    calculated_lots: float = 0.0
    reason: Optional[str] = None
    rule_name: Optional[str] = None
    action_taken: Optional[RiskAction] = None

class RiskEventDTO(BaseModel):
    id: Optional[int] = None
    event_type: RiskEventType
    rule_name: str
    threshold_value: str
    actual_value: str
    system_action_taken: RiskAction
