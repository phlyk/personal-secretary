"""Configuration management for the application."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent

# Telnyx Configuration
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY")
CONNECTION_ID = os.getenv("CONNECTION_ID")

# SMS Configuration
SMS_FROM_NUMBER = os.getenv("SMS_FROM_NUMBER")  # Number to send SMS from
SMS_TO_NUMBER = os.getenv("SMS_TO_NUMBER")      # Plumber's number to receive notifications

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Server Configuration
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "5000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")  # DEBUG, INFO, WARNING, ERROR

# Greeting Configuration
GREETING_AUDIO_URL = os.getenv("GREETING_AUDIO_URL", "")

# Recordings directory
RECORDINGS_DIR = BASE_DIR / "recordings"
RECORDINGS_DIR.mkdir(exist_ok=True)

# Output file
OUTPUT_FILE = BASE_DIR / "output.txt"

# Validation
def validate_config():
    """Validate that all required environment variables are set."""
    required_vars = {
        "TELNYX_API_KEY": TELNYX_API_KEY,
        "TELNYX_PUBLIC_KEY": TELNYX_PUBLIC_KEY,
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "CONNECTION_ID": CONNECTION_ID,
    }
    
    missing = [var for var, value in required_vars.items() if not value]
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Please check your .env file."
        )
