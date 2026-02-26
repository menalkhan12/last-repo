@echo off
REM Start the Flask web app (run in second terminal)
cd /d "%~dp0"
if not exist .env (
  copy .env.example .env
  echo Created .env from .env.example - please edit .env with your LIVEKIT_* and GROQ_API_KEY
  pause
)
set PORT=5000
echo Starting web app on http://localhost:%PORT% ...
python -m flask --app app.web run --host 0.0.0.0 --port %PORT%
