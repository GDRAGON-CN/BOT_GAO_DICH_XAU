from fastapi import APIRouter, Depends, Query
from app.core.security import verify_dashboard_api_key
from app.schemas.control import StateCommandResponseDTO, StateResponseDTO
from app.trading.state_manager import state_manager

router = APIRouter(prefix="/control", tags=["Bot Control"])

@router.get("/status", response_model=StateResponseDTO)
async def get_status():
    return StateResponseDTO(
        current_state=state_manager.current_state,
        is_running=state_manager.is_running,
        is_paused=state_manager.is_paused,
        is_emergency_stopped=state_manager.is_emergency_stopped,
        emergency_reason=state_manager.emergency_reason
    )

@router.post("/resume", response_model=StateCommandResponseDTO, dependencies=[Depends(verify_dashboard_api_key)])
async def resume(operator: str = Query("OPERATOR")):
    prev = state_manager.current_state
    new = state_manager.resume_trading(operator=operator)
    return StateCommandResponseDTO(status="ok", previous_state=prev, new_state=new, operator=operator)

@router.post("/pause", response_model=StateCommandResponseDTO, dependencies=[Depends(verify_dashboard_api_key)])
async def pause(reason: str = Query("Manual pause"), operator: str = Query("OPERATOR")):
    prev = state_manager.current_state
    new = state_manager.pause_trading(reason=reason, operator=operator)
    return StateCommandResponseDTO(status="ok", previous_state=prev, new_state=new, operator=operator)

@router.post("/emergency-stop", response_model=StateCommandResponseDTO, dependencies=[Depends(verify_dashboard_api_key)])
async def emergency_stop(reason: str = Query("Operator Emergency Stop"), operator: str = Query("OPERATOR")):
    prev = state_manager.current_state
    new = state_manager.trigger_emergency_stop(reason=reason, operator=operator)
    return StateCommandResponseDTO(status="ok", previous_state=prev, new_state=new, operator=operator)
