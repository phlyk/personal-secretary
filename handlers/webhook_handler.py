"""Webhook handler for processing Telnyx events."""
import json
from datetime import datetime
from pathlib import Path
from fastapi import BackgroundTasks
from handlers import call_handler
from services import telnyx_service, openai_service
from schemas import CallProcessingResult
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
    event_type = event_data.get("data", {}).get("event_type")
    
    if not event_type:
        print("[Webhook] Received event with no event_type")
        return "unknown"
    
    print(f"[Webhook] Received event: {event_type}")
    
    # Extract the actual event data
    event = event_data.get("data", {})
    
    # Route to appropriate handler
    if event_type == "call.initiated":
        call_handler.handle_call_initiated(event)
        
    elif event_type == "call.answered":
        call_handler.handle_call_answered(event)
        
    elif event_type == "call.speak.ended":
        call_handler.handle_speak_ended(event)
        
    elif event_type == "call.playback.ended":
        call_handler.handle_playback_ended(event)
        
    elif event_type == "call.recording.saved":
        # Get recording info
        recording_info = call_handler.handle_recording_saved(event)
        
        # Process recording in background
        background_tasks.add_task(
            process_recording,
            recording_info
        )
        print("[Webhook] Recording processing queued in background")
        
    elif event_type == "call.hangup":
        call_handler.handle_call_hangup(event)
        
    else:
        print(f"[Webhook] Unhandled event type: {event_type}")
    
    return event_type


def process_recording(recording_info: dict) -> None:
    """
    Background task to download recording, transcribe, and extract info.
    
    Args:
        recording_info: Dictionary with recording details
    """
    try:
        print(f"\n{'='*60}")
        print(f"🎙️  PROCESSING RECORDING")
        print(f"{'='*60}\n")
        
        # Download recording
        print("[Processing] Downloading recording...")
        audio_file = telnyx_service.download_recording(
            recording_info["recording_url"],
            recording_info["call_control_id"]
        )
        
        # Transcribe audio
        print("[Processing] Transcribing audio...")
        transcription = openai_service.transcribe_audio(audio_file)
        print(f"\n📝 TRANSCRIPTION:\n{transcription}\n")
        
        # Extract structured information
        print("[Processing] Extracting call information...")
        call_info = openai_service.extract_call_info(
            transcription,
            recording_info["from_number"]
        )
        
        # Create result
        result = CallProcessingResult(
            call_control_id=recording_info["call_control_id"],
            recording_id=recording_info["recording_id"],
            transcription=transcription,
            extracted_info=call_info,
            timestamp=datetime.now().isoformat()
        )
        
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
        
    except Exception as e:
        print(f"\n❌ ERROR PROCESSING RECORDING: {e}\n")
        import traceback
        traceback.print_exc()


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
