"""Telnyx API service for call control and recording management."""
from telnyx import Telnyx
import requests
from pathlib import Path
from typing import Optional
import config


# Initialize Telnyx client
client = Telnyx(api_key=config.TELNYX_API_KEY)


def answer_call(call_control_id: str) -> dict:
    """
    Answer an incoming call.
    
    Args:
        call_control_id: Unique identifier for the call
        
    Returns:
        Response from Telnyx API
    """
    try:
        result = client.calls.actions.answer(call_control_id=call_control_id)
        print(f"[Telnyx] Answered call: {call_control_id}")
        return result
    except Exception as e:
        print(f"[Telnyx] Error answering call: {e}")
        raise


def play_audio_url(call_control_id: str, audio_url: str) -> dict:
    """
    Play an audio file to the caller.
    
    Args:
        call_control_id: Unique identifier for the call
        audio_url: URL of the audio file to play
        
    Returns:
        Response from Telnyx API
    """
    try:
        result = client.calls.actions.start_playback(
            call_control_id=call_control_id,
            audio_url=audio_url
        )
        print(f"[Telnyx] Playing audio for call: {call_control_id}")
        return result
    except Exception as e:
        print(f"[Telnyx] Error playing audio: {e}")
        raise


def speak_text(call_control_id: str, text: str, voice: str = "male") -> dict:
    """
    Speak text to the caller using text-to-speech.
    Uses Telnyx TTS with simple voice specification.
    
    Args:
        call_control_id: Unique identifier for the call
        text: Text to speak
        voice: Voice to use (male/female)
        
    Returns:
        Response from Telnyx API
    """
    try:
        # Use client.calls.actions.speak() for TTS
        result = client.calls.actions.speak(
            call_control_id=call_control_id,
            payload=text,
            voice=voice,
            language="en-US"
        )
        print(f"[Telnyx] Speaking text for call: {call_control_id}")
        return result
    except Exception as e:
        print(f"[Telnyx] Error speaking text: {e}")
        raise


def start_recording(call_control_id: str, play_beep: bool = True) -> dict:
    """
    Start recording the call.
    
    Args:
        call_control_id: Unique identifier for the call
        play_beep: Whether to play a beep before recording
        
    Returns:
        Response from Telnyx API
    """
    try:
        result = client.calls.actions.start_recording(
            call_control_id=call_control_id,
            format="mp3",
            channels="single",
            play_beep=play_beep
        )
        print(f"[Telnyx] Started recording for call: {call_control_id}")
        return result
    except Exception as e:
        print(f"[Telnyx] Error starting recording: {e}")
        raise


def download_recording(recording_url: str, call_control_id: str) -> Path:
    """
    Download a call recording from Telnyx.
    
    Args:
        recording_url: URL of the recording
        call_control_id: Unique identifier for the call
        
    Returns:
        Path to the downloaded file
    """
    try:
        # Make authenticated request to download recording
        headers = {
            "Authorization": f"Bearer {config.TELNYX_API_KEY}"
        }
        
        response = requests.get(recording_url, headers=headers, stream=True)
        response.raise_for_status()
        
        # Save to recordings directory
        filename = f"{call_control_id}_{Path(recording_url).stem}.mp3"
        filepath = config.RECORDINGS_DIR / filename
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"[Telnyx] Downloaded recording: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"[Telnyx] Error downloading recording: {e}")
        raise


def hangup_call(call_control_id: str) -> dict:
    """
    Hang up a call.
    
    Args:
        call_control_id: Unique identifier for the call
        
    Returns:
        Response from Telnyx API
    """
    try:
        result = client.calls.actions.hangup(
            call_control_id=call_control_id
        )
        print(f"[Telnyx] Hung up call: {call_control_id}")
        return result
    except Exception as e:
        print(f"[Telnyx] Error hanging up call: {e}")
        raise
