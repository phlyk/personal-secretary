"""Webhook handler for processing Telnyx events."""
import json
import time
from datetime import datetime
from pathlib import Path
from fastapi import BackgroundTasks
from handlers import call_handler
from services import telnyx_service, openai_service
from schemas import CallProcessingResult
from utils.call_logger import get_or_create_logger, cleanup_logger
import config


async def process_telnyx_webhook(event_data: dict, background_tasks: BackgroundTasks) -> str:
    """
    Process incoming Telnyx webhook events.
    
    Args:
        event_data: The webhook event data from Telnyx
        background_tasks: FastAPI BackgroundTasks for async processing
        
    Returns:
        Event type that was processed
    """
    # Extract from data wrapper (Telnyx sends: {"data": {"event_type": ..., "payload": ...}, "meta": ...})
    data = event_data.get("data", {})
    event_type = data.get("event_type")
    
    if not event_type:
        print("[Webhook] Received event with no event_type")
        return "unknown"
    
    print(f"[Webhook] Received event: {event_type}")
    
    # Extract payload (event_type and payload are inside data wrapper)
    payload = data.get("payload", {})
    call_control_id = payload.get("call_control_id")
    from_number = payload.get("from", "unknown")
    
    # Initialize logger for this call (singleton pattern)
    if call_control_id:
        call_logger = get_or_create_logger(call_control_id, from_number)
        
        # Log full webhook payload at debug level
        if config.LOG_LEVEL == "DEBUG":
            call_logger.debug(f"Webhook Event: {event_type}")
            call_logger.debug(f"Full Payload: {json.dumps(event_data, indent=2)}")
    
    # Route to appropriate handler (pass the data object, not the full event_data)
    if event_type == "call.initiated":
        call_handler.handle_call_initiated(data)
    elif event_type == "call.answered":
        call_handler.handle_call_answered(data)
        
    elif event_type == "call.speak.ended":
        call_handler.handle_speak_ended(data)
        
    elif event_type == "call.playback.ended":
        call_handler.handle_playback_ended(data)
        
    elif event_type == "call.recording.saved":
        # Get recording info
        recording_info = call_handler.handle_recording_saved(data)
        
        # Process recording in background
        background_tasks.add_task(
            process_recording,
            recording_info
        )
        print("[Webhook] Recording processing queued in background")
        
    elif event_type == "call.hangup":
        call_handler.handle_call_hangup(data)
        # Don't cleanup logger yet - wait for recording.saved to complete
        
    else:
        print(f"[Webhook] Unhandled event type: {event_type}")
    
    return event_type


def process_recording(recording_info: dict) -> None:
    """
    Background task to download recording, transcribe, and extract info.
    Includes retry logic and per-call logging.
    
    Args:
        recording_info: Dictionary with recording details
    """
    # Get existing logger for this call
    call_control_id = recording_info["call_control_id"]
    from_number = recording_info["from_number"]
    call_logger = get_or_create_logger(call_control_id, from_number)
    
    max_retries = 3
    retry_delay = 2  # seconds
    
    try:
        print(f"\n{'='*60}")
        print(f"🎙️  PROCESSING RECORDING")
        print(f"{'='*60}\n")
        
        call_logger.info("Starting recording processing")
        call_logger.info(f"Recording ID: {recording_info['recording_id']}")
        call_logger.info(f"From: {recording_info['from_number']}")
        
        # Download recording with retries
        audio_file = None
        for attempt in range(1, max_retries + 1):
            try:
                call_logger.info(f"Downloading recording (attempt {attempt}/{max_retries})...")
                print(f"[Processing] Downloading recording (attempt {attempt}/{max_retries})...")
                
                audio_file = telnyx_service.download_recording(
                    recording_info["recording_url"],
                    recording_info["call_control_id"]
                )
                call_logger.success(f"Recording downloaded: {audio_file.name}")
                break
                
            except Exception as e:
                call_logger.error(f"Download attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    call_logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise
        
        # Transcribe audio with retries
        transcription = None
        for attempt in range(1, max_retries + 1):
            try:
                call_logger.info(f"Transcribing audio (attempt {attempt}/{max_retries})...")
                print(f"[Processing] Transcribing audio (attempt {attempt}/{max_retries})...")
                
                transcription = openai_service.transcribe_audio(audio_file)
                call_logger.success(f"Transcription complete: {len(transcription)} characters")
                call_logger.info(f"Transcription: {transcription}")
                print(f"\n📝 TRANSCRIPTION:\n{transcription}\n")
                break
                
            except Exception as e:
                call_logger.error(f"Transcription attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    call_logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise
        
        # Extract structured information with retries
        call_info = None
        for attempt in range(1, max_retries + 1):
            try:
                call_logger.info(f"Extracting call information (attempt {attempt}/{max_retries})...")
                print(f"[Processing] Extracting call information (attempt {attempt}/{max_retries})...")
                
                call_info = openai_service.extract_call_info(
                    transcription,
                    recording_info["from_number"]
                )
                call_logger.success("Information extraction complete")
                break
                
            except Exception as e:
                call_logger.error(f"Extraction attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    call_logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise
        
        # Create result
        result = CallProcessingResult(
            call_control_id=recording_info["call_control_id"],
            recording_id=recording_info["recording_id"],
            transcription=transcription,
            extracted_info=call_info,
            timestamp=datetime.now().isoformat()
        )
        
        # Log extracted information
        call_logger.info("Extracted Information:")
        call_logger.info(f"  Caller: {call_info.caller}")
        call_logger.info(f"  Intent: {call_info.intent}")
        call_logger.info(f"  Job Type: {call_info.job_type or 'Not specified'}")
        call_logger.info(f"  Urgency: {call_info.urgency}")
        call_logger.info(f"  Summary: {call_info.summary or 'N/A'}")
        if call_info.missing_fields:
            call_logger.info(f"  Missing Info: {', '.join(call_info.missing_fields)}")
        
        # Print to stdout
        print(f"\n{'='*60}")
        print(f"✅ CALL PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"\n📊 EXTRACTED INFORMATION:")
        print(f"   Caller: {call_info.caller}")
        print(f"   Intent: {call_info.intent}")
        print(f"   Job Type: {call_info.job_type or 'Not specified'}")
        print(f"   Urgency: {call_info.urgency}")
        print(f"   Summary: {call_info.summary or 'N/A'}")
        if call_info.missing_fields:
            print(f"   Missing Info: {', '.join(call_info.missing_fields)}")
        print(f"\n{'='*60}\n")
        
        # Write to output file
        write_result_to_file(result)
        call_logger.success(f"Result written to {config.OUTPUT_FILE}")
        # Cleanup logger after recording processing completes
        cleanup_logger(call_control_id)
        
    except Exception as e:
        error_msg = f"Error processing recording: {e}"
        
        call_logger.error(error_msg)
        print(f"\n❌ ERROR PROCESSING RECORDING: {e}\n")
        import traceback
        traceback.print_exc()
        call_logger.error(traceback.format_exc())
        # Cleanup logger even on error
        cleanup_logger(call_control_id)


def write_result_to_file(result: CallProcessingResult) -> None:
    """
    Write processing result to output file.
    
    Args:
        result: The processing result to write
    """
    try:
        # Format as pretty JSON
        result_json = result.model_dump_json(indent=2)
        
        # Append to output file with separator
        with open(config.OUTPUT_FILE, "a") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Timestamp: {result.timestamp}\n")
            f.write(f"{'='*80}\n")
            f.write(result_json)
            f.write("\n\n")
        
        print(f"[Output] Result written to {config.OUTPUT_FILE}")
        
    except Exception as e:
        print(f"[Output] Error writing to file: {e}")
