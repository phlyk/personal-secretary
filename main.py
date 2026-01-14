"""
Personal Secretary - AI Phone Assistant MVP
Main FastAPI application for handling Telnyx webhooks
"""
from typing import Dict
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import config
from handlers import webhook_handler
from utils import security
from webhook_models import TelnyxWebhookRequest


# Validate configuration on startup
try:
    config.validate_config()
    print("✅ Configuration validated successfully")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    print("Please set up your .env file with required variables")
    exit(1)

# Create FastAPI app
app = FastAPI(
    title="Personal Secretary",
    description="AI-powered phone assistant for busy professionals",
    version="0.1.0"
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Personal Secretary API",
        "version": "0.1.0"
    }


@app.post("/webhooks/telnyx", response_model=Dict)
async def telnyx_webhook(
    webhook: TelnyxWebhookRequest,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle incoming Telnyx webhook events.
    
    This endpoint receives call events from Telnyx and processes them accordingly.
    For call.recording.saved events, processing happens in the background.
    
    Args:
        webhook: The Telnyx webhook payload (auto-validated by Pydantic)
        request: The raw FastAPI request (for signature verification)
        background_tasks: FastAPI background tasks manager
    
    Returns:
        202 Accepted for successful webhook processing
    
    Example webhook payload:
        ```json
        {
          "data": {
            "event_type": "call.initiated",
            "id": "...",
            "occurred_at": "2026-01-14T12:00:00.000Z",
            "payload": {
              "call_control_id": "v3:...",
              "from": "+15551234567",
              "to": "+15557654321"
            },
            "record_type": "event"
          }
        }
        ```
    """
    # Verify webhook signature (skip if configured for development)
    if not security.skip_signature_verification():
        try:
            await security.verify_telnyx_signature(request)
        except HTTPException:
            # Allow processing even if signature verification fails for MVP
            # TODO: Enforce strict verification in production
            print("⚠️  Webhook signature verification failed (continuing anyway for MVP)")
    
    # Convert Pydantic model to dict for processing
    event_data = webhook.model_dump(by_alias=True)
    
    # Process webhook
    try:
        event_type = await webhook_handler.process_telnyx_webhook(
            event_data,
            background_tasks
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "event_type": event_type,
                "message": "Webhook received and processing"
            }
        )
        
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        import traceback
        traceback.print_exc()
        
        # Still return 202 to prevent Telnyx retries
        return JSONResponse(
            status_code=202,
            content={
                "status": "error",
                "message": str(e)
            }
        )


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "config": {
            "telnyx_configured": bool(config.TELNYX_API_KEY),
            "openai_configured": bool(config.OPENAI_API_KEY),
            "recordings_dir": str(config.RECORDINGS_DIR),
            "output_file": str(config.OUTPUT_FILE)
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    print(f"\n{'='*60}")
    print(f"🚀 Starting Personal Secretary API")
    print(f"{'='*60}\n")
    print(f"Server: http://localhost:{config.WEBHOOK_PORT}")
    print(f"Webhooks: http://localhost:{config.WEBHOOK_PORT}/webhooks/telnyx")
    print(f"Health: http://localhost:{config.WEBHOOK_PORT}/health")
    print(f"\n{'='*60}\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.WEBHOOK_PORT,
        reload=True,
        log_level="info"
    )
