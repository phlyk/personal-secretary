"""Telnyx SMS service for sending notifications."""
from telnyx import Telnyx
import config
from services import translation_service


# Initialize Telnyx client
client = Telnyx(api_key=config.TELNYX_API_KEY)


def send_sms(to: str, message: str, from_number: str = None) -> dict:
    """
    Send an SMS message via Telnyx.
    
    Args:
        to: Recipient phone number in E.164 format
        message: Message text to send
        from_number: Sender phone number (defaults to config.SMS_FROM_NUMBER)
        
    Returns:
        Response from Telnyx API
    """
    if from_number is None:
        from_number = config.SMS_FROM_NUMBER
    
    try:
        response = client.messages.send(
            from_=from_number,
            to=to,
            text=message,
            type="SMS"
        )
        
        print(f"[SMS] Message sent to {to}")
        print(f"[SMS] Message ID: {response.data.id if hasattr(response, 'data') else 'N/A'}")
        
        return response
        
    except Exception as e:
        print(f"[SMS] Error sending message: {e}")
        raise


def format_call_summary_sms(call_info: dict, transcription: str, caller_phone: str) -> str:
    """
    Format call information into an SMS message with French labels.
    
    Args:
        call_info: Extracted call information (CallInfo object dict)
        transcription: Full transcription text
        caller_phone: Caller's phone number
        
    Returns:
        Formatted SMS message text in French
    """
    # Get French labels
    labels = translation_service.get_french_labels()
    
    urgency_emoji = {
        "emergency": "🚨",
        "urgent": "⚠️",
        "normal": "📝",
        "flexible": "📅"
    }
    
    urgency_value = call_info.get("urgency", "normal").lower()
    emoji = urgency_emoji.get(urgency_value, "📞")
    
    # Build SMS message with French labels, English values
    message_parts = [
        f"{emoji} {labels['new_voicemail']}",
        f"",
        f"{labels['from']}: {call_info.get('caller', 'Unknown')} ({caller_phone})",
        f"{labels['urgency']}: {call_info.get('urgency', 'N/A').upper()}",
        f"",
        f"{labels['intent']}: {call_info.get('intent', 'N/A')}",
    ]
    
    if call_info.get("job_type"):
        message_parts.append(f"{labels['job_type']}: {call_info['job_type']}")
    
    if call_info.get("summary"):
        message_parts.append(f"")
        message_parts.append(f"{labels['summary']}: {call_info['summary']}")
    
    if call_info.get("missing_fields"):
        message_parts.append(f"")
        message_parts.append(f"{labels['missing_fields']}: {', '.join(call_info['missing_fields'])}")
    
    # Add truncated transcription if space allows
    message_text = "\n".join(message_parts)
    
    # SMS has 160 chars for single message, 1600 for concatenated
    # Keep it under 500 chars for reliability
    if len(message_text) < 400:
        message_parts.append(f"")
        message_parts.append(f"---")
        # Add truncated transcription
        max_transcript_len = 450 - len(message_text)
        if len(transcription) > max_transcript_len:
            message_parts.append(transcription[:max_transcript_len] + "...")
        else:
            message_parts.append(transcription)
    
    return "\n".join(message_parts)
