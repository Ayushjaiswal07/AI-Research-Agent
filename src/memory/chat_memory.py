"""
Chat Memory Manager
Persists conversation summaries to data/chat_history.json.
Each entry:
  {
    "id":        "uuid4",
    "timestamp": "2026-06-13T14:32:00",
    "topic":     "what is RAG?",
    "summary":   "The assistant explained RAG as ..."
  }
"""

import json
import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

HISTORY_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "chat_history.json")
)

MAX_CONTEXT_TURNS = 6  # how many recent turns to inject into each prompt


def _ensure_file():
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def load_history() -> List[Dict[str, Any]]:
    _ensure_file()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not read chat history: {e}")
        return []


def append_turn(topic: str, summary: str) -> Dict[str, Any]:
    """Append one Q&A turn and return the new entry."""
    _ensure_file()
    history = load_history()

    entry = {
        "id":        str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "topic":     topic,
        "summary":   summary[:600].strip(),
    }

    history.append(entry)

    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error(f"Could not write chat history: {e}")

    return entry


def get_recent_context(n: int = MAX_CONTEXT_TURNS) -> str:
    """Return last n turns as a formatted string to inject into the LLM prompt."""
    history = load_history()
    if not history:
        return ""

    recent = history[-n:]
    lines  = ["--- CONVERSATION HISTORY (most recent turns) ---"]
    for turn in recent:
        lines.append(f"[{turn.get('timestamp', '')}]")
        lines.append(f"  User:      {turn.get('topic', '')}")
        lines.append(f"  Assistant: {turn.get('summary', '')}")
        lines.append("")
    lines.append("--- END OF HISTORY ---")
    return "\n".join(lines)


def clear_history():
    _ensure_file()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
