"""LLM layer: Groq (Llama-3-70b), strict system prompt, escalation, refusal interception."""
import re
from typing import List, Optional, Tuple

from groq import Groq

from config import (
    ESCALATION_MESSAGE,
    GROQ_API_KEY,
    MAX_HISTORY_TURNS,
)
from app.rag import get_rag


SYSTEM_PROMPT = """You are the official voice assistant for the Institute of Space Technology (IST) Admissions. You answer only from the provided OFFICIAL CONTEXT below. You are speaking in a live phone call.

RULES (strict):
1. NO HALLUCINATIONS: Use ONLY the provided context. If the answer is not in the context and it is not a simple yes/no, respond with exactly: [ESCALATE]
2. NO ECHOING: Never repeat the user's question (e.g. "You asked about fees..."). Start directly with the answer.
3. CONFIDENCE: Do not apologize or say "I think" or "I'm not sure." If the user says "You're wrong," politely restate the facts from the official IST context.
4. CONCISENESS: Keep responses to 1–2 sentences. Maximum 4 sentences only for complex fee structures.
5. If you cannot answer from context, output exactly [ESCALATE] and nothing else.

OFFICIAL CONTEXT:
{context}
"""

# Strings that indicate LLM refusal or error; replace with escalation
REFUSAL_PATTERNS = [
    r"i('m| am) (sorry|unable|not able)",
    r"i (cannot|can't) (help|answer|assist)",
    r"as an (ai|language model)",
    r"i (don't|do not) have (access|information)",
    r"technical (issue|difficulty|problem)",
    r"error|something went wrong",
    r"apologize|apologies",
]


def _refusal_or_error(text: str) -> bool:
    if not text or len(text.strip()) < 10:
        return True
    lower = text.strip().lower()
    for pat in REFUSAL_PATTERNS:
        if re.search(pat, lower):
            return True
    if "[ESCALATE]" in text:
        return True
    return False


def _format_messages(history: List[Tuple[str, str]], query: str, context: str) -> list:
    system = SYSTEM_PROMPT.format(context="\n\n---\n\n".join(context) if isinstance(context, list) else context)
    messages = [{"role": "system", "content": system}]
    for user, assistant in history[-MAX_HISTORY_TURNS:]:
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": assistant})
    messages.append({"role": "user", "content": query})
    return messages


def get_response(
    query: str,
    history: Optional[List[Tuple[str, str]]] = None,
    session_id: Optional[str] = None,
) -> Tuple[str, bool]:
    """
    Get LLM response with RAG context. Returns (reply_text, should_escalate).
    If should_escalate is True, caller should say ESCALATION_MESSAGE and optionally ask for phone.
    """
    history = history or []
    rag = get_rag()
    chunks = rag.search(query, top_k=8)
    context = "\n\n".join(chunks) if chunks else "No specific context available. For any query you cannot answer from this, output [ESCALATE]."

    client = Groq(api_key=GROQ_API_KEY)
    messages = _format_messages(history, query, context)

    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=150,
            temperature=0.3,
        )
        text = (resp.choices[0].message.content or "").strip()
    except Exception:
        return ESCALATION_MESSAGE, True

    if "[ESCALATE]" in text or not text:
        return ESCALATION_MESSAGE, True
    if _refusal_or_error(text):
        return ESCALATION_MESSAGE, True
    return text, False


def get_escalation_message() -> str:
    return ESCALATION_MESSAGE
