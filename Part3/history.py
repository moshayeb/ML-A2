# ============================================================
# HISTORY — Part 3: Mo-Assistant
# ============================================================
# This file manages the chat memory of Mo-Assistant.
#
# TWO separate things happen here:
#   DISK   → every message is saved to logs/chat_history.json forever
#   CLAUDE → only the last N messages are sent to Claude as context
#
# WHY NOT SEND EVERYTHING TO CLAUDE?
# Every API call costs tokens for everything you send.
# Sending 500 old messages every time = ~12,500 tokens per reply.
# Your entire budget would be gone in one message.
# Sending only the last 15 messages = ~375 tokens. Much smarter.
#
# Think of it like this: you record a whole meeting, but when
# you ask a colleague a question, you only remind them of the
# last few things said — not read the whole transcript.
# ============================================================


# ─── IMPORTS ────────────────────────────────────────────────

import os
import json
import datetime
from config_loader import settings  # shared settings dictionary


# ─── CONFIGURATION ──────────────────────────────────────────
# HISTORY_FILE : where all messages are saved on disk.
# logs/ folder is created automatically if it doesn't exist.

HISTORY_FILE = os.path.join("logs", "chat_history.json")
SEQ_FILE     = os.path.join("logs", "last_seq.json")
os.makedirs("logs", exist_ok=True)  # create logs/ if not there yet


# ─── LAST SEQ PERSISTENCE ───────────────────────────────────
# Saves and loads the last hub message sequence number so the
# agent never re-processes old messages after a restart.

def save_last_seq(seq: int):
    """Write the last seen seq number to disk."""
    with open(SEQ_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_seq": seq}, f)

def load_last_seq() -> int:
    """Read the last seen seq number from disk. Returns 0 if not found."""
    try:
        with open(SEQ_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("last_seq", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


# ─── SAVE MESSAGE ───────────────────────────────────────────
# Saves one hub message to the history file on disk.
# We save EVERY message we receive — even ones we don't reply to.
# This gives us a complete record of the entire group chat.

def save_message(message):
    """
    Append one message to the history file.
    Adds a 'received_at' timestamp so we know when we saw it.
    """
    record = dict(message)  # copy so we don't modify the original
    record["received_at"] = datetime.datetime.now().isoformat()

    history = load_all_history()
    history.append(record)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# ─── LOAD ALL HISTORY ───────────────────────────────────────
# Loads the full chat history from disk.
# Returns an empty list if the file doesn't exist yet —
# which is normal on the very first run.

def load_all_history():
    """Read the entire saved chat history from disk."""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# ─── GET RECENT CONTEXT ─────────────────────────────────────
# Returns the last N messages as a formatted string to send
# to Claude. This is the "memory" we give Claude so it
# understands what was discussed before it replies.
#
# N comes from settings["context_messages"] in config.json.
# You can change that number without touching this code.
#
# Example output:
#   human:Teacher: Can anyone write a sort function?
#   Hassan-Agent: I can help!
#   human:Teacher: Mo-Assistant, can you review that?

def get_recent_context():
    """
    Return the last N messages as a formatted string for Claude.
    N is defined by 'context_messages' in config.json.
    """
    n       = settings["context_messages"]
    history = load_all_history()
    recent  = history[-n:]  # take only the last N messages

    if not recent:
        return "No previous messages in this session."

    lines = [f"{m['agent_name']}: {m['content']}" for m in recent]
    return "\n".join(lines)
