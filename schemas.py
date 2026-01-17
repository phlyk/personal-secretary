"""Pydantic schemas for structured data extraction."""
from typing import List, Optional
from pydantic import BaseModel, Field


class AudioProcessingResponse(BaseModel):
    """Response from audio processing endpoint."""
    status: str = Field(..., description="Processing status")
    transcription: str = Field(..., description="Transcribed text from audio")
    extracted_info: 'CallInfo' = Field(..., description="Structured information extracted from transcription")
    timestamp: str = Field(..., description="ISO timestamp of processing")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "transcription": "Hi, this is John. I have a leaking pipe in my kitchen...",
                "extracted_info": {
                    "tenant_id": "plumber-solo",
                    "caller": "John",
                    "intent": "Request plumbing repair",
                    "job_type": "leak repair",
                    "urgency": "high",
                    "missing_fields": ["address"],
                    "summary": "Leaking pipe in kitchen, needs urgent repair"
                },
                "timestamp": "2026-01-17T12:34:56.789012"
            }
        }


class CallInfo(BaseModel):
    """Structured information extracted from caller's message."""
    
    tenant_id: str = Field(
        description="Identifier for the business/tenant (default: 'plumber-solo' for MVP)"
    )
    caller: str = Field(
        description="Name or phone number of the caller"
    )
    intent: str = Field(
        description="What the caller wants (e.g., 'book appointment', 'get quote', 'emergency repair', 'general inquiry')"
    )
    job_type: Optional[str] = Field(
        default=None,
        description="Type of plumbing work needed (e.g., 'leak repair', 'installation', 'drain cleaning', 'emergency')"
    )
    urgency: str = Field(
        description="How urgent the request is: 'emergency', 'urgent', 'normal', 'flexible'"
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="List of important information that the caller didn't provide (e.g., 'address', 'callback number', 'preferred time')"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Brief summary of the caller's message"
    )


class CallProcessingResult(BaseModel):
    """Complete result of processing a call recording."""
    
    call_control_id: str
    recording_id: str
    transcription: str
    extracted_info: CallInfo
    timestamp: str
