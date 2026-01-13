## Plan: Telnyx + OpenAI Phone Assistant MVP

Build a webhook-based phone system for a solo plumber to capture caller messages, transcribe them, and extract structured data (caller info, urgency, job type) using Telnyx for call handling and OpenAI for transcription + parsing. Python-based, local development with ngrok, no cloud infrastructure initially.

### Steps

1. **Set up FastAPI webhook server** with endpoint at `/webhooks/telnyx` and implement Telnyx signature verification in `utils/security.py` to prevent webhook spam. Return 202 Accepted immediately after webhook validation

2. **Implement call control flow** in `handlers/call_handler.py` to handle `call.initiated` (answer), `call.answered` (play greeting), and trigger recording start with beep

3. **Handle recording webhook** in `handlers/webhook_handler.py` to process `call.recording.saved` events. Use FastAPI's `BackgroundTasks` to asynchronously download audio via `services/telnyx_service.py` and save to local `recordings/` folder while returning 202 Accepted immediately

4. **Transcribe and parse** in `services/openai_service.py` (executed as background task) using Whisper API for transcription, then send to GPT-4o-mini with Pydantic schema defined in `schemas.py` for structured output extraction. Write results to stdout and append to `output.txt` file

5. **Configure environment** in `.env` with `TELNYX_API_KEY`, `TELNYX_PUBLIC_KEY` (for webhook verification), `OPENAI_API_KEY`, `CONNECTION_ID` (from Telnyx Voice Application), and `WEBHOOK_PORT`

6. **Test end-to-end** by running zgrok (`zgrok http 5000`), configuring Telnyx Voice Application with zgrok HTTPS URL, assigning phone number, and making test calls to validate the full pipeline

### Further Considerations

1. **Telnyx setup needed**: Create Voice API Application in Telnyx Mission Control, purchase/assign a phone number, obtain Connection ID and Public Key for webhook verification. Which greeting message should the system play?

2. **Async processing**: Using FastAPI's `BackgroundTasks` to handle recording download, transcription, and parsing asynchronously. Webhook endpoint returns 202 Accepted immediately (well within Telnyx's 10-second timeout)

3. **Output format**: Structured JSON printed to stdout and appended to `output.txt` file for MVP. Each call's result saved as formatted JSON with timestamp
