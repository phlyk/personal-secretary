### Beginning:

- No Cloud, using ngrok/ zgrok to expose [localhost](http://localhost)
- Need webhooks to handle `call.recording.saved` most of all
- Need to fetch the saved call (and its potential transcription) and then download it, and send it to OpenAI Whisper `client.audio.transcriptions.create(`via the SDK
- Then the transcribed message will be passed to GPT-5-mini LLM via `client.responses.parse`  method with a structured output schema (validated via Pydantic)
    - Fields for now will be: 
    {
    "tenant_id": "...",
    "caller": "...",
    "intent": "...",
    "job_type": "...",
    "urgency": "...",
    "missing_fields": [...]
    }
- No storage to start, just output the result to stdout or some file

The telnyx flow specifics:

The flow:

1. Answer the call using the Answer command
2. Play your greeting using the [Play Audio URL](https://developers.telnyx.com/api-reference/call-commands/play-audio-url) command
3. Record the caller's message using the [Recording Start](https://developers.telnyx.com/api-reference/call-commands/recording-start) command with `play_beep: true`

### Later

- Need to add appropriate persistance for
    - The output of pipeline
    - The audio files
- Hardcoded multi-tenancy
- Need to protect webhooks against spam (because webhooks are unauthenticated right?)

### Very later

- Need to add infra (AWS Free Tier)
- Add a UI to view the messages, sort, filter, and replay