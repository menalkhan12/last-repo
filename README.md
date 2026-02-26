# IST AI Voice Agent

Production-ready voice AI calling agent for **Institute of Space Technology (IST)** admissions. Built with LiveKit (WebRTC), Flask, Groq (LLM + STT), Edge-TTS, and hybrid RAG (ChromaDB + BM25).

## Features

- **Real-time voice**: LiveKit for low-latency WebRTC, VAD-based barge-in (interrupt agent while speaking).
- **RAG-grounded answers**: Hybrid search (vector + keyword) over IST admission data; fallback to "General IST Admission Overview".
- **Strict behavior**: No hallucinations, no echoing, concise 1–2 sentence answers, escalation when out of scope.
- **Lead capture**: Escalation message + Pakistani phone extraction; logs to `logs/lead_logs.txt` (thread-safe).
- **Session**: 10–12 turns of history for follow-ups (e.g. "What about hostels for that program?").

## Tech stack

| Component | Choice |
|----------|--------|
| Real-time | LiveKit (WebRTC, VAD, barge-in) |
| Backend | Flask + Gunicorn (Render) |
| LLM | Groq (Llama-3.3-70b-versatile) |
| STT | Groq Whisper (whisper-large-v3) |
| TTS | Edge-TTS (en-US-AriaNeural) |
| RAG | ChromaDB (vector) + RankBM25 (keyword), top 8 chunks |
| Storage | Local `.txt` lead logs, `.json` session records (MVP) |

## Setup

### 1. Clone and install

```bash
cd "taking agent"
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 2. Environment

Copy `.env.example` to `.env` and set:

- **LiveKit**: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` (from [LiveKit Cloud](https://cloud.livekit.io)).
- **Groq**: `GROQ_API_KEY` (from [Groq Console](https://console.groq.com)).

### 3. Data

Put IST admission content in the `data/` folder (`.txt` and/or `.json`). The app loads all files from `data/` and builds the RAG index on first use.

### 4. Run locally

**Terminal 1 – agent worker (connects to LiveKit):**

```bash
python agent_entrypoint.py dev
```

**Terminal 2 – Flask web + token + static:**

```bash
set PORT=5000
python -m flask --app app.web run --host 0.0.0.0 --port 5000
# or: gunicorn --bind 0.0.0.0:5000 app.web:app
```

Open `http://localhost:5000`, click **Start Call**, allow microphone. The agent joins the room and answers from the IST knowledge base.

## Deployment (Render)

1. Connect the repo to Render; use `render.yaml` for two services:
   - **Web**: Flask app, `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 app.web:app`, health check `/health`.
   - **Worker**: LiveKit agent, `python agent_entrypoint.py dev` (or `start` per LiveKit docs).

2. In Render dashboard, set env vars for both services:
   - `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `GROQ_API_KEY`.
   - Optional: `DATA_DIR`, `LOG_DIR`, `CHROMA_PERSIST_DIR`, `PORT`.

3. **Port**: The web service must bind to `0.0.0.0:$PORT` (handled by the start command above).

4. **Persistence**: Render disks are ephemeral. Lead logs and session files are for MVP/session tracking; for production, use external logging or a database.

## API

- `GET /health` – Health check (returns `{"status": "ok"}`).
- `POST /token` – Issue LiveKit token. Body (optional): `room_name`, `participant_identity`, `participant_name`. Returns `server_url`, `participant_token`, `room_name`.

## Project layout

```
├── app/
│   ├── data_loader.py   # Load /data (txt, json) and chunk
│   ├── rag.py           # ChromaDB + BM25, hybrid search, fallback
│   ├── llm.py           # Groq + system prompt, escalation, refusal handling
│   ├── llm_rag.py       # LiveKit LLM wrapper (RAG + Groq)
│   ├── lead_capture.py   # Phone regex, thread-safe lead log
│   ├── tts_edge.py      # Edge-TTS LiveKit plugin
│   └── web.py           # Flask: /health, /token, static
├── agent_entrypoint.py  # LiveKit worker: STT/LLM/TTS/VAD, barge-in
├── config.py            # Env and paths
├── data/                # IST admission content (txt/json)
├── logs/                # lead_logs.txt, session records
├── static/
│   └── index.html       # IST theme, Start Call, status, post-call summary
├── requirements.txt
├── render.yaml
└── README.md
```

## Escalation and lead log

When the query is outside the knowledge base, the agent says:

> "I will forward your specific query to the IST Admissions Office. Could you please provide your phone number so we can call you back with an official answer?"

If the user replies with a Pakistani phone (e.g. `03xx-xxxxxxx`), it is extracted and appended to `logs/lead_logs.txt` in the format:

`timestamp | phone | query | session_id`

File writes use a `threading.Lock()` for concurrency safety.

## License

Use according to your organization’s policy.
