# ============================================================
# AGENT -- Part 3: Mo-Assistant
# ============================================================
# The brain of Mo-Assistant. Decides WHEN to respond and
# WHAT to do with each incoming message.
#
# Two core functions:
#   should_respond(message) -> True/False: should we reply?
#   handle_message(message) -> process and reply to one message
#
# The main while loop is in loop.py.
# The console control thread is in console.py.
# Shared runtime state is in state.py.
#
# Files it uses:
#   state.py      -> last_message_time (updated after each reply)
#   claude.py     -> ask_claude(), check_budget()
#   hub.py        -> post_message()
#   history.py    -> save_message()
#   tools.py      -> write_file()
#   templates.py  -> find_template() (zero-token fast replies)
# ============================================================


# --- IMPORTS ------------------------------------------------

import re
import json
import time

import claude
import state
from config_loader import AGENT_NAME
from hub           import post_message
from history       import save_message
from tools         import write_file
from templates     import find_template


# --- SHOULD RESPOND -----------------------------------------
# Decides whether Mo-Assistant should reply to a message.
# NOT every message needs a reply -- if all agents replied to
# everything, the chat would explode with noise.
#
# Rules (in order):
#   1. Never reply to our own messages (infinite loop risk)
#   2. Always reply if mentioned by name
#   3. Reply to broadcasts for all agents
#   4. Reply to humans asking engineering questions
#   5. Stay quiet for everything else

def should_respond(message):
    sender  = message["agent_name"]
    content = message["content"].lower()

    if sender == AGENT_NAME:
        return False
    if AGENT_NAME.lower() in content:
        return True
    if "attention all agents" in content:
        return True
    if "@everyone" in content:
        return True
    if sender.lower().startswith("human"):
        engineering_words = [
            "help", "code", "build", "create", "fix",
            "review", "python", "error", "bug", "write", "function"
        ]
        if any(word in content for word in engineering_words):
            return True
    return False


# --- HANDLE MESSAGE -----------------------------------------
# Processes one message from the hub:
#   1. Save to history (always -- even if we do not reply)
#   2. Check if we should respond
#   3. Check budget
#   4. Check templates (free, instant -- no Claude call)
#   5. Ask Claude (with recent context)
#   6. If Claude returns file JSON -> write it to workspace
#   7. If Claude returns text -> post it to the hub

def handle_message(message):
    sender  = message["agent_name"]
    content = message["content"]

    print(f"[HUB] {sender}: {content[:80]}")
    save_message(message)

    if not should_respond(message):
        print("[QUIET] Not our turn to speak.")
        return

    if not claude.check_budget():
        print("[QUIET] Budget exhausted.")
        return

    # Check templates BEFORE calling Claude.
    # If the message matches a pre-written template, we reply instantly
    # with 0 tokens spent. Only if no template matches do we call Claude.
    template_reply = find_template(content)
    if template_reply:
        print("[TEMPLATE] Using pre-written response -- no tokens spent.")
        post_message(template_reply)
        state.last_message_time = time.time()
        return

    print("[THINKING] Asking Claude for a reply...")
    reply = claude.ask_claude(content, sender)

    # Claude sometimes wraps JSON in markdown code blocks like ```json ... ```
    # We strip those out before parsing -- this was a bug we fixed earlier.
    clean = reply.strip()
    if "```" in clean:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", clean)
        if match:
            clean = match.group(1).strip()

    try:
        parsed = json.loads(clean)
        if parsed.get("type") == "file":
            filename = parsed["filename"]
            code     = parsed["content"]
            write_file(filename, code)
            post_message(
                f"I have written `{filename}` to the workspace:\n\n"
                f"```python\n{code}\n```"
            )
            print(f"[FILE] Created and confirmed: {filename}")
            state.last_message_time = time.time()
            return
    except (json.JSONDecodeError, KeyError):
        pass

    print(f"[REPLY] Sending: {reply[:80]}")
    post_message(reply)
    state.last_message_time = time.time()
