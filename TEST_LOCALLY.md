# Test IST Voice Agent Locally

## 1. One-time setup

### Create `.env` with your keys

Edit `.env` in the project root and set:

- **LiveKit** (get from [LiveKit Cloud](https://cloud.livekit.io) → your project → Settings):
  - `LIVEKIT_URL` – e.g. `wss://your-project.livekit.cloud`
  - `LIVEKIT_API_KEY`
  - `LIVEKIT_API_SECRET`
- **Groq** (get from [Groq Console](https://console.groq.com/keys)):
  - `GROQ_API_KEY`

### Install dependencies

From the project root (`taking agent`):

```bash
pip install -r requirements.txt
```

First run may take a few minutes (sentence-transformers + ChromaDB).

---

## 2. Run locally (two terminals)

You need **two** processes: the **agent worker** (connects to LiveKit) and the **web app** (token + UI).

### Terminal 1 – Agent worker

```bash
cd "c:\Users\minal\Desktop\taking agent"
python agent_entrypoint.py dev
```

Leave this running. You should see something like: `connecting to LiveKit...` then `registered worker`.

### Terminal 2 – Web app

```bash
cd "c:\Users\minal\Desktop\taking agent"
set PORT=5000
python -m flask --app app.web run --host 0.0.0.0 --port 5000
```

Or on Windows you can double‑click:

- `run_agent.bat` (first terminal)
- `run_web.bat` (second terminal)

---

## 3. Test in the browser

1. Open **http://localhost:5000**
2. Click **Start Call**
3. Allow microphone when prompted
4. Ask e.g. “What are the BS program fees?” or “When do admissions open?”

The agent should join the room and answer from the IST data in `data/`.

---

## Troubleshooting

| Issue | What to do |
|-------|------------|
| “Could not get token” | Check `.env`: `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `LIVEKIT_URL` |
| Agent never joins / no voice | Worker must be running (`agent_entrypoint.py dev`) and same LiveKit project as in `.env` |
| “RAG prewarm failed” | Ensure `data/` has `.txt`/`.json` files; check console for errors |
| Module not found | Run `pip install -r requirements.txt` from project root |
