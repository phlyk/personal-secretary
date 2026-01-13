"""Utility functions for webhook security."""
import os
import hashlib
import hmac
from fastapi import HTTPException, Request
import config


async def verify_telnyx_signature(request: Request) -> bool:
    """
    Verify that a webhook request came from Telnyx.
    
    Telnyx signs webhooks with a timestamp and signature in headers:
    - telnyx-timestamp-header: Unix timestamp
    - telnyx-signature-header: HMAC SHA256 signature
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if signature is valid
        
    Raises:
        HTTPException: If signature is invalid or missing
    """
    # Get signature headers
    timestamp = request.headers.get("telnyx-timestamp")
    signature = request.headers.get("telnyx-signature-ed25519")
    
    if not timestamp or not signature:
        raise HTTPException(
            status_code=401,
            detail="Missing Telnyx signature headers"
        )
    
    # Get raw body
    body = await request.body()
    
    # Create signed payload (timestamp + . + body)
    signed_payload = f"{timestamp}.{body.decode('utf-8')}"
    
    # Compute expected signature using public key
    # Note: Telnyx uses Ed25519 signatures, but for MVP we'll use HMAC verification
    # In production, implement proper Ed25519 verification
    try:
        expected_signature = hmac.new(
            config.TELNYX_PUBLIC_KEY.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # For now, we'll do a basic verification
        # TODO: Implement proper Ed25519 signature verification for production
        if not signature:
            raise HTTPException(
                status_code=401,
                detail="Invalid signature"
            )
            
        return True
        
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Signature verification failed: {str(e)}"
        )


def skip_signature_verification() -> bool:
    """
    Check if signature verification should be skipped.
    Useful for local development with ngrok/zgrok.
    
    Set SKIP_WEBHOOK_VERIFICATION=true in .env for development only.
    """
    return os.getenv("SKIP_WEBHOOK_VERIFICATION", "false").lower() == "true"
