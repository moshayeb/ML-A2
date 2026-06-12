import os
import json
import threading
import datetime
from config_loader import settings

_history_lock = threading.Lock()

HISTORY_FILE = os.path.join("logs", "chat_history.json")
os.makedirs("logs", exist_ok=True)


def save_message(message: dict):
    record = dict(message)
    record["received_at"] = datetime.datetime.now().isoformat()
    with _history_lock:
        history = load_all_history()
        history.append(record)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)


def load_all_history() -> list:
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def get_recent_context() -> str:
    n = settings["context_messages"]
    history = load_all_history()
    recent = history[-n:]
    if not recent:
        return "No previous messages in this session."
    lines = [
        f"{m.get('role', m.get('agent_name', 'unknown'))}: {m.get('content', '')}"
        for m in recent
    ]
    return "\n".join(lines)


def compact_if_needed():
    threshold = settings.get("compaction_threshold", 4)
    history = load_all_history()
    if len(history) <= threshold:
        return

    half = len(history) // 2
    to_summarise = history[:half]
    to_keep = history[half:]

    text = "\n".join(
        f"{m.get('role', m.get('agent_name', 'unknown'))}: {m.get('content', '')}"
        for m in to_summarise
    )
    summary = _summarise_with_claude(text, len(to_summarise))
    if summary is None:
        return

    summary_entry = {
        "role": "system",
        "content": f"[Compacted summary of {len(to_summarise)} earlier messages]: {summary}",
        "received_at": datetime.datetime.now().isoformat(),
    }
    new_history = [summary_entry] + to_keep
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(new_history, f, indent=2, ensure_ascii=False)
    print(
        f"[COMPACT] Condensed {len(to_summarise)} messages → 1 summary. History: {len(new_history)} entries."
    )
    try:
        from events import emit_event

        emit_event(
            "compact",
            {
                "condensed": len(to_summarise),
                "remaining": len(new_history),
            },
        )
    except ImportError:
        pass


def _summarise_with_claude(text: str, msg_count: int):
    try:
        import requests as _requests
        from config_loader import API_KEY

        resp = _requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.get("model", "claude-haiku-4-5-20251001"),
                "max_tokens": 300,
                "system": (
                    "Summarise the following conversation history in 3-4 sentences. "
                    "Focus on decisions made, tasks completed, and files written. Be concise."
                ),
                "messages": [{"role": "user", "content": text}],
            },
            timeout=30,
        )
        data = resp.json()
        if "content" not in data:
            return None
        import claude as _claude

        usage = data.get("usage", {})
        _claude.update_tokens(
            usage.get("input_tokens", 0), usage.get("output_tokens", 0)
        )
        return data["content"][0]["text"]
    except Exception as exc:
        print(f"[COMPACT] Summarisation failed: {exc}")
        return None
