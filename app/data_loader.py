"""Load and chunk all IST admission data from /data (PDFs and text)."""
import json
import re
from pathlib import Path
from typing import List, Tuple

from config import DATA_DIR


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


def _read_json_file(path: Path) -> List[str]:
    """Extract text-like content from JSON for RAG (flatten to paragraphs)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        texts = []
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str) and len(v) > 50:
                    texts.append(v)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, str) and len(item) > 50:
                            texts.append(item)
                        elif isinstance(item, dict):
                            for v2 in item.values():
                                if isinstance(v2, str) and len(v2) > 50:
                                    texts.append(v2)
        return texts
    except Exception:
        return []


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks (by characters)."""
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        # Prefer sentence boundary
        if end < len(text):
            last_period = chunk.rfind(".")
            if last_period > chunk_size // 2:
                end = start + last_period + 1
                chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end - overlap
    return [c for c in chunks if c]


def load_documents() -> List[Tuple[str, str]]:
    """
    Load all documents from DATA_DIR. Returns list of (text_chunk, source_id).
    source_id is filename or 'filename|section' for traceability.
    """
    documents: List[Tuple[str, str]] = []
    data_path = Path(DATA_DIR)
    if not data_path.exists():
        return documents

    for path in sorted(data_path.iterdir()):
        if path.suffix.lower() == ".txt":
            raw = _read_text_file(path)
            if not raw:
                continue
            # Split by double newlines or long blocks for better chunks
            blocks = re.split(r"\n\s*\n", raw)
            for block in blocks:
                block = block.strip()
                if len(block) < 30:
                    continue
                for chunk in chunk_text(block, chunk_size=600, overlap=100):
                    if len(chunk) >= 50:
                        documents.append((chunk, path.name))
        elif path.suffix.lower() == ".json":
            for i, text in enumerate(_read_json_file(path)):
                for chunk in chunk_text(text, chunk_size=600, overlap=100):
                    if len(chunk) >= 50:
                        documents.append((chunk, f"{path.name}|{i}"))

    return documents
