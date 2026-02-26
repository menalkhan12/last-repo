#!/bin/bash
# Start both Flask web app AND LiveKit agent worker together on Render

echo "Starting IST Voice Agent..."

# Start the LiveKit agent worker in the background
python agent_entrypoint.py start &
AGENT_PID=$!
echo "Agent worker started (PID: $AGENT_PID)"

# Start the Flask web app (foreground - this is what Render monitors)
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120