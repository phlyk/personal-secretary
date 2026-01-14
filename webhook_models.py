"""Pydantic models for Telnyx webhook payloads."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TelnyxWebhookMeta(BaseModel):
    """Metadata about the webhook request."""
    attempt: Optional[int] = None
    delivered_to: Optional[str] = None


class TelnyxEventPayload(BaseModel):
    """Base payload structure for Telnyx events."""
    call_control_id: Optional[str] = None
    call_leg_id: Optional[str] = None
    call_session_id: Optional[str] = None
    client_state: Optional[str] = None
    connection_id: Optional[str] = None
    from_: Optional[str] = Field(None, alias="from")
    to: Optional[str] = None
    direction: Optional[str] = None
    state: Optional[str] = None
    
    # Recording-specific fields
    recording_id: Optional[str] = None
    recording_urls: Optional[Dict[str, str]] = None
    
    # Additional fields that may appear in various events
    answer_state: Optional[str] = None
    sip_notify_response: Optional[int] = None
    
    class Config:
        populate_by_name = True


class TelnyxEventData(BaseModel):
    """The data wrapper for Telnyx events."""
    event_type: str
    id: str
    occurred_at: str
    payload: TelnyxEventPayload
    record_type: str = "event"


class TelnyxWebhookRequest(BaseModel):
    """Complete Telnyx webhook request structure."""
    data: TelnyxEventData
    meta: Optional[TelnyxWebhookMeta] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "event_type": "call.initiated",
                    "id": "e5e5e5e5-e5e5-e5e5-e5e5-e5e5e5e5e5e5",
                    "occurred_at": "2026-01-14T12:00:00.000Z",
                    "payload": {
                        "call_control_id": "v3:abc123...",
                        "call_leg_id": "leg_abc123",
                        "call_session_id": "session_abc123",
                        "connection_id": "1234567890",
                        "from": "+15551234567",
                        "to": "+15557654321",
                        "direction": "incoming",
                        "state": "parked"
                    },
                    "record_type": "event"
                },
                "meta": {
                    "attempt": 1,
                    "delivered_to": "https://your-webhook-url.com/webhooks/telnyx"
                }
            }
        }
