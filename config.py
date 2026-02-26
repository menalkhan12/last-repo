"""IST AI Voice Agent - Configuration from environment."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")
LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "logs")
CHROMA_PERSIST_DIR = BASE_DIR / os.getenv("CHROMA_PERSIST_DIR", "chroma_db")

# Ensure dirs exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

# LiveKit
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Server
PORT = int(os.getenv("PORT", "5000"))
HOST = os.getenv("HOST", "0.0.0.0")

# RAG
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 8
FALLBACK_QUERY = "General IST Admission Overview"

# Session
MAX_HISTORY_TURNS = 12

# Escalation
ESCALATION_MESSAGE = (
    "I will forward your specific query to the IST Admissions Office. "
    "Could you please provide your phone number so we can call you back with an official answer?"
)
LEAD_LOG_PATH = LOG_DIR / "lead_logs.txt"
SESSION_RECORDS_DIR = LOG_DIR  # session records as .json

# Pakistani phone regex: 03xx-xxxxxxx or 03xxxxxxxxx or +92 3xx xxxxxxx
PHONE_REGEX = r"(\+92\s?)?(0?3[0-4][0-9][\s\-]?\d{7})"
