"""Pydantic schemas for structured data extraction."""
from typing import List, Optional
from pydantic import BaseModel, Field


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
