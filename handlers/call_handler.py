"""Call control handler for managing call flow."""
from services import telnyx_service
import config


def handle_call_initiated(event_data: dict) -> None:
    """
    Handle call.initiated event - answer the call.
    
    Args:
        event_data: Event payload from Telnyx webhook
    """
    call_control_id = event_data["payload"]["call_control_id"]
    from_number = event_data["payload"].get("from", "unknown")
    
    print(f"\n{'='*60}")
    print(f"📞 INCOMING CALL from {from_number}")
    print(f"{'='*60}\n")
    
    # Answer the call
    telnyx_service.answer_call(call_control_id)


def handle_call_answered(event_data: dict) -> None:
    """
    Handle call.answered event - play greeting and start recording.
    
    Args:
        event_data: Event payload from Telnyx webhook
    """
    call_control_id = event_data["payload"]["call_control_id"]
    
    print(f"[Call Handler] Call answered: {call_control_id}")
    
    # Play greeting (use TTS or audio URL)
    if config.GREETING_AUDIO_URL:
        telnyx_service.play_audio_url(call_control_id, config.GREETING_AUDIO_URL)
    else:
        # Use text-to-speech for greeting
        greeting_text = (
            "Hello! You've reached your friendly neighborhood plumber. "
            "Unfortunately, I'm with another customer right now. "
            "Please leave your name, number, and details about what you need, "
            "and I'll get back to you as soon as possible. "
            "If this is an emergency, please mention that. "
            "Thanks, and speak after the beep!"
        )
        telnyx_service.speak_text(call_control_id, greeting_text, voice="male")


def handle_speak_ended(event_data: dict) -> None:
    """
    Handle call.speak.ended event - start recording after greeting.
    
    Args:
        event_data: Event payload from Telnyx webhook
    """
    call_control_id = event_data["payload"]["call_control_id"]
    
    print(f"[Call Handler] Greeting completed: {call_control_id}")
    
    # Start recording with beep
    telnyx_service.start_recording(call_control_id, play_beep=True)


def handle_playback_ended(event_data: dict) -> None:
    """
    Handle call.playback.ended event - start recording after audio greeting.
    
    Args:
        event_data: Event payload from Telnyx webhook
    """
    call_control_id = event_data["payload"]["call_control_id"]
    
    print(f"[Call Handler] Audio playback completed: {call_control_id}")
    
    # Start recording with beep
    telnyx_service.start_recording(call_control_id, play_beep=True)


def handle_recording_saved(event_data: dict) -> dict:
    """
    Handle call.recording.saved event - extract recording info for processing.
    
    Args:
        event_data: Event payload from Telnyx webhook
        
    Returns:
        Dictionary with recording information for background processing
    """
    payload = event_data["payload"]
    
    recording_url = payload["recording_urls"]["mp3"]
    call_control_id = payload["call_control_id"]
    recording_id = payload.get("recording_id", "unknown")
    
    print(f"[Call Handler] Recording saved: {recording_id}")
    print(f"[Call Handler] Recording URL: {recording_url}")
    
    # Get caller phone number from payload (fix: was getting from wrong location)
    from_number = payload.get("from", "unknown")
    
    return {
        "recording_url": recording_url,
        "call_control_id": call_control_id,
        "recording_id": recording_id,
        "from_number": from_number
    }


def handle_call_hangup(event_data: dict) -> None:
    """
    Handle call.hangup event - log call completion.
    
    Args:
        event_data: Event payload from Telnyx webhook
    """
    call_control_id = event_data["payload"]["call_control_id"]
    
    print(f"\n[Call Handler] Call ended: {call_control_id}")
    print(f"{'='*60}\n")
