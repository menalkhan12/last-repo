"""Lead capture: Pakistani phone regex, thread-safe log append."""
import re
from datetime import datetime
from threading import Lock
from typing import Optional

from config import LEAD_LOG_PATH, PHONE_REGEX


_lead_log_lock = Lock()


def extract_pakistani_phone(text: str) -> Optional[str]:
    """Extract first Pakistani phone number (03xx-xxxxxxx style). Normalize to digits only for storage."""
    if not text:
        return None
    m = re.search(PHONE_REGEX, text.replace("-", " ").strip())
    if not m:
        return None
    num = re.sub(r"\D", "", m.group(0))
    if num.startswith("92"):
        num = "0" + num[2:]
    if len(num) >= 10 and num.startswith("03"):
        return num
    return None


def log_lead(phone: str, query: str, session_id: str) -> None:
    """Append one lead line to logs/lead_logs.txt with thread-safe write."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{timestamp} | {phone} | {query} | {session_id}\n"
    with _lead_log_lock:
        with open(LEAD_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
