# Personal Secretary - AI Phone Assistant MVP

An AI-powered phone assistant system that handles incoming calls, records voicemails, transcribes them using OpenAI Whisper, and extracts structured information for busy professionals (initially built for a solo plumber).

## Features

- 📞 **Automated Call Handling**: Answers calls, plays greeting, and records voicemails
- 🎙️ **Voice Transcription**: Uses OpenAI Whisper for accurate transcription
- 🤖 **AI-Powered Extraction**: Extracts structured data (caller, intent, urgency, job type)
- ⚡ **Async Processing**: FastAPI BackgroundTasks for efficient webhook handling
- 🔒 **Webhook Security**: Telnyx signature verification
- 📊 **Simple Output**: Results saved to stdout and output.txt file

## Tech Stack

- **FastAPI** - Modern async web framework
- **Telnyx** - Voice API for call handling
- **OpenAI** - Whisper (transcription) + GPT-4o-mini (extraction)
- **Pydantic** - Data validation and structured outputs
- **zgrok** - Local tunnel for webhook testing

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `TELNYX_API_KEY` - Your Telnyx API key
- `TELNYX_PUBLIC_KEY` - For webhook signature verification
- `CONNECTION_ID` - Telnyx Voice Application Connection ID
- `OPENAI_API_KEY` - Your OpenAI API key

### 3. Telnyx Setup

1. Create a Voice API Application in Telnyx Mission Control
2. Purchase/assign a phone number
3. Set webhook URL to your zgrok HTTPS URL + `/webhooks/telnyx`
4. Get Connection ID and Public Key from the application

### 4. Run the Server

```bash
python main.py
```

Server runs on `http://localhost:5000`

### 5. Expose with zgrok

In another terminal:

```bash
zgrok http 5000
```

Use the HTTPS URL in your Telnyx Voice Application webhook settings.

## How It Works

1. **Call Initiated** → System answers the call
2. **Greeting** → Plays greeting (TTS or audio URL)
3. **Recording** → Starts recording after beep
4. **Processing** (Background):
   - Downloads recording from Telnyx
   - Transcribes with Whisper
   - Extracts structured info with GPT-4o-mini
   - Saves to stdout + `output.txt`

## Project Structure

```
personal-secretary/
├── main.py                      # FastAPI application entry point
├── config.py                    # Configuration management
├── schemas.py                   # Pydantic models
├── handlers/
│   ├── call_handler.py          # Call control logic
│   └── webhook_handler.py       # Webhook processing + background tasks
├── services/
│   ├── telnyx_service.py        # Telnyx API interactions
│   └── openai_service.py        # Whisper & GPT integration
└── utils/
    └── security.py              # Webhook verification
```

## Development

For local development, you can skip webhook verification:

```bash
# In .env
SKIP_WEBHOOK_VERIFICATION=true
```

## Output Format

Results are saved to `output.txt` with this structure:

```json
{
  "call_control_id": "...",
  "recording_id": "...",
  "transcription": "Full transcription text...",
  "extracted_info": {
    "tenant_id": "plumber-solo",
    "caller": "John Smith / +1234567890",
    "intent": "emergency repair",
    "job_type": "leak repair",
    "urgency": "emergency",
    "missing_fields": ["address"],
    "summary": "Caller has burst pipe emergency..."
  },
  "timestamp": "2026-01-08T10:30:00"
}
```

## Next Steps
### Ultra MVP 
- [ ] Handle more edge cases (pauses)
- [ ] Handle French language (duh)
    - [x] Transcription
    - [ ] Structured data prompt
- [ ] Accents and poor quality recordings
- [ ] Second transcription for redundancy
- [ ] Ensure final JSON payload is delicious (does it have the person's number)
- [ ] Look into final translation
- [ ] Tidy up
- [ ] Some documentation for non-technical users
    - [ ] With next steps on where we could go from here

### Beyond
- [ ] Add database persistence
- [ ] Build web UI for viewing messages
- [ ] Implement multi-tenancy
- [ ] Deploy to AWS Free Tier
