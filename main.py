"""
Personal Secretary - AI Phone Assistant MVP
Main FastAPI application for handling Telnyx webhooks
"""
from typing import Dict
from pathlib import Path
from datetime import datetime
import json
import logging
import structlog
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import config
from handlers import webhook_handler
from services import openai_service, sms_service
from schemas import AudioProcessingResponse
from utils import security
from webhook_models import TelnyxWebhookRequest


# Configure structlog for better logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(colors=True)
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False
)

logger = structlog.get_logger()


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
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle incoming Telnyx webhook events.
    
    This endpoint receives call events from Telnyx and processes them accordingly.
    For call.recording.saved events, processing happens in the background.
    
    Note: Using raw Request instead of Pydantic model to handle validation errors
    and log the actual payload when validation fails.
    """
    # Get raw body first for logging
    raw_body = await request.body()
    
    try:
        # Parse JSON
        event_data = json.loads(raw_body)
        
        # Extract from data wrapper for logging
        data = event_data.get("data", {})
        payload = data.get("payload", {})
        
        logger.info(
            "webhook_received",
            event_type=data.get("event_type", "unknown"),
            payload_keys=list(event_data.keys()),
            call_control_id=payload.get("call_control_id", "N/A"),
            from_number=payload.get("from", "N/A")
        )
        
        # Log full payload at debug level
        if config.LOG_LEVEL == "DEBUG":
            logger.debug(
                "webhook_full_payload",
                payload=event_data
            )
        
        # Validate with Pydantic
        try:
            webhook = TelnyxWebhookRequest(**event_data)
            validated_data = webhook.model_dump(by_alias=True)
        except Exception as validation_error:
            logger.error(
                "webhook_validation_failed",
                error=str(validation_error),
                error_type=type(validation_error).__name__,
                raw_payload=event_data,
                payload_structure={
                    "top_level_keys": list(event_data.keys()),
                    "event_type": event_data.get("event_type"),
                    "has_payload": "payload" in event_data,
                    "payload_keys": list(event_data.get("payload", {}).keys()) if "payload" in event_data else []
                }
            )
            # Use event_data even if validation fails
            validated_data = event_data
        
        # Verify webhook signature (skip if configured for development)
        if not security.skip_signature_verification():
            try:
                await security.verify_telnyx_signature(request)
            except HTTPException:
                logger.warning("webhook_signature_verification_failed")
        
        # Process webhook
        event_type = await webhook_handler.process_telnyx_webhook(
            validated_data,
            background_tasks
        )
        
        logger.info(
            "webhook_processed",
            event_type=event_type,
            status="accepted"
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "event_type": event_type,
                "message": "Webhook received and processing"
            }
        )
        
    except json.JSONDecodeError as e:
        logger.error(
            "webhook_invalid_json",
            error=str(e),
            raw_body=raw_body.decode('utf-8', errors='replace')[:1000]
        )
        return JSONResponse(
            status_code=202,
            content={
                "status": "error",
                "message": "Invalid JSON"
            }
        )
        
    except Exception as e:
        logger.error(
            "webhook_processing_error",
            error=str(e),
            error_type=type(e).__name__,
            traceback=True
        )
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


@app.post("/test/process-audio", response_model=AudioProcessingResponse)
async def test_process_audio(
    audio_file: UploadFile = File(..., description="Audio file to process (MP3, WAV, etc.)")
):
    """
    Test endpoint for audio processing pipeline.
    
    Upload an audio file to test the transcription and extraction pipeline
    without going through Telnyx. Useful for testing and development.
    
    This endpoint:
    1. Accepts an audio file upload
    2. Transcribes it using OpenAI Whisper
    3. Extracts structured information using GPT-4o-mini
    4. Returns the results
    
    Args:
        audio_file: Audio file to process (supports MP3, WAV, M4A, etc.)
    
    Returns:
        AudioProcessingResponse with transcription and extracted info
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/test/process-audio" \\
          -F "audio_file=@recording.mp3"
        ```
    """
    temp_file_path = None
    
    try:
        print(f"\n{'='*60}")
        print("🎤 TEST AUDIO PROCESSING")
        print(f"{'='*60}\n")
        print(f"[Test] Received file: {audio_file.filename}")
        print(f"[Test] Content type: {audio_file.content_type}")
        
        # Save uploaded file temporarily
        temp_dir = config.RECORDINGS_DIR / "test"
        temp_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(audio_file.filename).suffix or ".mp3"
        temp_filename = f"test_{timestamp}{file_extension}"
        temp_file_path = temp_dir / temp_filename
        
        # Write uploaded file
        print(f"[Test] Saving to: {temp_file_path}")
        with open(temp_file_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
        
        print(f"[Test] File saved: {len(content)} bytes")
        
        # Transcribe audio
        print("[Test] Starting transcription...")
        transcription = openai_service.transcribe_audio(temp_file_path)
        print(f"[Test] Transcription complete: {len(transcription)} characters")
        print(f"\n📝 TRANSCRIPTION:\n{transcription}\n")
        
        # Extract structured information
        print("[Test] Extracting structured information...")
        call_info = openai_service.extract_call_info(transcription, "test-caller")
        print("[Test] Extraction complete")
        
        # Print results
        print(f"\n{'='*60}")
        print("✅ PROCESSING COMPLETE")
        print(f"{'='*60}")
        print("\n📊 EXTRACTED INFORMATION:")
        print(f"   Caller: {call_info.caller}")
        print(f"   Intent: {call_info.intent}")
        print(f"   Job Type: {call_info.job_type or 'Not specified'}")
        print(f"   Urgency: {call_info.urgency}")
        print(f"   Summary: {call_info.summary or 'N/A'}")
        if call_info.missing_fields:
            print(f"   Missing Info: {', '.join(call_info.missing_fields)}")
        print(f"\n{'='*60}\n")
        
        # Return response
        return AudioProcessingResponse(
            status="success",
            transcription=transcription,
            extracted_info=call_info,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"\n❌ ERROR PROCESSING AUDIO: {e}\n")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio: {str(e)}"
        )
        
    finally:
        # Note: keeping test files for debugging
        # Could add cleanup here if needed
        pass


@app.post("/sms/send")
async def send_sms_notification(
    to: str = None,
    message: str = None
):
    """
    Send an SMS message via Telnyx.
    
    Test endpoint for manually sending SMS messages.
    If no parameters provided, sends a test message to the configured SMS_TO_NUMBER.
    
    Args:
        to: Recipient phone number (E.164 format). Defaults to SMS_TO_NUMBER from config.
        message: Message text to send. Defaults to a test message.
    
    Returns:
        Status of SMS sending
    
    Example:
        ```bash
        # Send test message to configured number
        curl -X POST "http://localhost:8000/sms/send"
        
        # Send custom message
        curl -X POST "http://localhost:8000/sms/send?to=%2B15551234567&message=Hello"
        ```
    """
    try:
        # Use configured values if not provided
        recipient = to or config.SMS_TO_NUMBER
        text = message or "🧪 Test message from Personal Secretary"
        
        if not recipient:
            raise HTTPException(
                status_code=400,
                detail="No recipient specified and SMS_TO_NUMBER not configured in .env"
            )
        
        if not config.SMS_FROM_NUMBER:
            raise HTTPException(
                status_code=400,
                detail="SMS_FROM_NUMBER not configured in .env"
            )
        
        logger.info(
            "sending_sms",
            to=recipient,
            from_number=config.SMS_FROM_NUMBER,
            message_length=len(text)
        )
        
        response = sms_service.send_sms(
            to=recipient,
            message=text,
            from_number=config.SMS_FROM_NUMBER
        )
        
        return {
            "status": "sent",
            "to": recipient,
            "from": config.SMS_FROM_NUMBER,
            "message": text,
            "message_id": response.data.id if hasattr(response, 'data') and hasattr(response.data, 'id') else None
        }
        
    except Exception as e:
        logger.error("sms_send_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send SMS: {str(e)}"
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
    print("🚀 Starting Personal Secretary API")
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
