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

import requests
from config_loader import API_KEY, AGENT_NAME, settings
from history import get_recent_context


# ─── TOKEN STATE ────────────────────────────────────────────
# tokens_spent tracks how much has been used since the agent started.
# It is a module-level variable — any file that does
# 'import claude' can read it with 'claude.tokens_spent'.
# It is updated every time ask_claude() is called.

tokens_spent = 0


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

    response = requests.post(
        url="https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": settings["model"],  # e.g. claude-haiku-4-5
            "max_tokens": settings["max_tokens"],  # max length of reply
            "system": settings["system_prompt"],
            "messages": messages,
        },
    )
    data = response.json()

    if "error" in data or "content" not in data:
        print(f"[CLAUDE] API error response: {data}")
        return "I encountered an API error and could not complete the request. Please try again."

    # Count and record how many tokens this call used
    update_tokens(data["usage"]["input_tokens"], data["usage"]["output_tokens"])

    return data["content"][0]["text"]


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
    tokens_spent += input_tokens + output_tokens
    pct = (tokens_spent / budget) * 100
    print(f"[TOKENS] Spent so far: {tokens_spent}/{budget} ({pct:.1f}%)")
    if pct >= 90:
        print(f"[BUDGET] WARNING: Token budget is {pct:.1f}% used ({tokens_spent}/{budget}). Approaching limit!")
    elif pct >= 70:
        print(f"[BUDGET] NOTICE: Token budget is {pct:.1f}% used ({tokens_spent}/{budget}).")
