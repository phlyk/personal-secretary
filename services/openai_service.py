"""OpenAI service for transcription and structured extraction."""
from pathlib import Path
from openai import OpenAI
from schemas import CallInfo
import config


# Initialize OpenAI client
client = OpenAI(api_key=config.OPENAI_API_KEY)


def transcribe_audio(audio_file_path: Path) -> str:
    """
    Transcribe audio file using OpenAI Whisper.
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Transcribed text
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en",
                prompt="This is a voicemail message from a customer calling a plumber. They may discuss plumbing issues, repairs, emergencies, or appointment requests."
            )
        
        transcription = transcript.text
        print(f"[OpenAI] Transcribed audio: {len(transcription)} characters")
        return transcription
        
    except Exception as e:
        print(f"[OpenAI] Error transcribing audio: {e}")
        raise


def extract_call_info(transcription: str, phone_number: str = "unknown") -> CallInfo:
    """
    Extract structured information from transcription using GPT-4o-mini.
    
    Args:
        transcription: Transcribed text from the call
        phone_number: Caller's phone number (from Telnyx)
        
    Returns:
        CallInfo object with extracted data
    """
    try:
        # Create system prompt for extraction
        system_prompt = """You are an AI assistant helping a busy plumber manage incoming calls.
Extract key information from voicemail transcriptions in a structured format.

Focus on:
- Caller's name (if mentioned, otherwise use phone number)
- What they want (intent)
- Type of plumbing work
- How urgent it is
- What information is missing that would help the plumber

Be concise and practical. The plumber needs to quickly understand what the caller wants."""

        user_prompt = f"""Transcription of voicemail:
"{transcription}"

Caller's phone number: {phone_number}

Extract the key information from this voicemail."""

        # Use structured output with Pydantic model
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=CallInfo,
        )
        
        # Extract parsed response
        call_info = completion.choices[0].message.parsed
        
        # Set tenant_id for MVP
        call_info.tenant_id = "plumber-solo"
        
        # Use phone number as caller if no name extracted
        if not call_info.caller or call_info.caller == "unknown":
            call_info.caller = phone_number
        
        print(f"[OpenAI] Extracted call info: {call_info.intent} - {call_info.urgency}")
        return call_info
        
    except Exception as e:
        print(f"[OpenAI] Error extracting call info: {e}")
        raise
