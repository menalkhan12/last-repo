@echo off
REM Start the LiveKit agent worker (run in first terminal)
cd /d "%~dp0"
if not exist .env (
  copy .env.example .env
  echo Created .env from .env.example - please edit .env with your LIVEKIT_* and GROQ_API_KEY
  pause
)
echo Starting IST agent worker...
python agent_entrypoint.py dev
