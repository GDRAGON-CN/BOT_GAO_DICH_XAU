"""Security and authentication functions."""
import hmac
from typing import Optional
from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_webhook_token(
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    payload_secret: Optional[str] = None
) -> bool:
    expected_secret = settings.WEBHOOK_SECRET
    if not expected_secret:
        return True
        
    candidate = x_webhook_secret or payload_secret
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook secret header or payload field."
        )
        
    if not hmac.compare_digest(candidate, expected_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret."
        )
    return True

def verify_dashboard_api_key(api_key: Optional[str] = Security(api_key_header)) -> bool:
    expected_key = settings.DASHBOARD_API_KEY
    if not expected_key:
        return True
        
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header."
        )
        
    if not hmac.compare_digest(api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key."
        )
    return True
