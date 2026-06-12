# ============================================================
# CLAUDE — Part 3: Mo-Assistant
# ============================================================
# This file handles all communication with the Claude AI API.
# It is the "thinking" part of Mo-Assistant.
#
# Responsibilities:
#   - Send messages to Claude and get replies
#   - Track how many tokens have been spent
#   - Enforce the token budget (stop spending when limit is reached)
#
# TOKEN TRACKING:
# Every API call to Claude costs tokens — one token ≈ one word.
# We track spending here so the agent never goes over budget.
# The budget can be changed live via the console_control command.
# ============================================================


# ─── IMPORTS ────────────────────────────────────────────────

import time
import threading
import requests
from config_loader import API_KEY, AGENT_NAME, settings
from history import get_recent_context


# ─── TOKEN STATE ────────────────────────────────────────────
# tokens_spent tracks how much has been used since the agent started.
# It is a module-level variable — any file that does
# 'import claude' can read it with 'claude.tokens_spent'.
# It is updated every time ask_claude() is called.
# _token_lock guards the counter against concurrent sub-agent updates.

tokens_spent = 0
_token_lock  = threading.Lock()


# ─── ASK CLAUDE ─────────────────────────────────────────────
# This is the core function. It sends a message to Claude
# along with the recent chat history as context, and returns
# Claude's reply as a plain string.
#
# WHY WE INCLUDE CONTEXT:
# Without context, Claude replies without knowing what was
# discussed before. With context, it reads the last N messages
# first — just like a human would scroll up before replying.


def ask_claude(current_message, sender, template_context=None):
    """
    Send a message to Claude with recent chat history as context.

    current_message  : the new message we need to reply to
    sender           : who sent it (e.g. "human:Teacher")
    template_context : optional reference material from templates.py

    Returns Claude's reply as a string.
    """
    context = get_recent_context()

    # If a template matched, inject it as reference material so Claude
    # can use it to write a natural, context-aware answer.
    reference = ""
    if template_context:
        reference = f"\nRelevant reference material (use this to inform your reply):\n{template_context}\n"

    # We combine recent chat history + the new message into one prompt.
    messages = [
        {
            "role": "user",
            "content": (
                f"Here is the recent group chat history:\n\n"
                f"{context}\n"
                f"{reference}\n"
                f"The latest message is from {sender}:\n"
                f'"{current_message}"\n\n'
                f"Reply as {AGENT_NAME}. Be specific and helpful."
            ),
        }
    ]

    # Retry up to 3 times for transient errors (rate limits, overloaded)
    for attempt in range(3):
        try:
            response = requests.post(
                url="https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings["model"],
                    "max_tokens": settings["max_tokens"],
                    "system": settings["system_prompt"],
                    "messages": messages,
                },
                timeout=60,
            )
        except requests.exceptions.RequestException as exc:
            print(f"[CLAUDE] Network error (attempt {attempt + 1}/3): {exc}")
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return "I encountered a network error and could not complete the request."

        data = response.json()

        # Retry on rate limit or overloaded — wait, then try again
        if "error" in data:
            err_type = data.get("error", {}).get("type", "unknown")
            print(f"[CLAUDE] API error (attempt {attempt + 1}/3): HTTP {response.status_code} — {err_type}")
            if err_type in ("rate_limit_error", "overloaded_error") and attempt < 2:
                wait = 5 * (attempt + 1)   # 5s, 10s
                print(f"[CLAUDE] Retrying in {wait}s...")
                time.sleep(wait)
                continue
            return "I encountered an API error and could not complete the request. Please try again."

        if "content" not in data:
            print(f"[CLAUDE] Unexpected response (attempt {attempt + 1}/3): {data}")
            return "I encountered an API error and could not complete the request. Please try again."

        # Success — count tokens and return reply
        update_tokens(data["usage"]["input_tokens"], data["usage"]["output_tokens"])
        return data["content"][0]["text"]

    return "I encountered an API error and could not complete the request. Please try again."


# ─── BUDGET CHECK ───────────────────────────────────────────
# Called before every Claude API call.
# Returns True if we still have budget left, False if not.
# Reads max_tokens_budget from settings — which is the shared
# dict from config_loader, so console changes take effect instantly.


def check_budget():
    """Return True if token budget has not been reached."""
    budget = settings["max_tokens_budget"]
    if tokens_spent >= budget:
        print(f"[BUDGET] Token budget reached! Spent: {tokens_spent}/{budget}")
        return False
    return True


# ─── UPDATE TOKEN COUNT ─────────────────────────────────────
# Called automatically after every ask_claude() call.
# Adds input + output tokens to the running total.


def update_tokens(input_tokens, output_tokens):
    """Add tokens used by one Claude call to the running total."""
    global tokens_spent
    budget = settings["max_tokens_budget"]
    with _token_lock:
        tokens_spent += input_tokens + output_tokens
        pct = (tokens_spent / budget) * 100
    print(f"[TOKENS] Spent so far: {tokens_spent}/{budget} ({pct:.1f}%)")
    if pct >= 90:
        print(f"[BUDGET] WARNING: Token budget is {pct:.1f}% used ({tokens_spent}/{budget}). Approaching limit!")
    elif pct >= 75:
        print(f"[BUDGET] NOTICE: Token budget is {pct:.1f}% used ({tokens_spent}/{budget}).")
