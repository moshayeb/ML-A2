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
from config_loader import AGENT_NAME, settings
from hub import post_message, get_messages
from history import save_message
from tools import write_file
from templates import find_template
from coordination import coordinate


# --- SHOULD RESPOND -----------------------------------------
# Decides whether Mo-Assistant should reply to a message.
# NOT every message needs a reply -- if all agents replied to
# everything, the chat would explode with noise.
#
# Rules (in order):
#   1. Never reply to our own messages (infinite loop risk)
#   2. If another agent mentions us, only reply if they share real
#      content (code, a question) -- ignore short acknowledgements
#      like "I'll draft X" or "Sure!"
#   3. Always reply to broadcasts for all agents
#   4. Reply to humans asking engineering questions
#   5. Stay quiet for everything else


def should_respond(message):
    sender = message["agent_name"]
    content = message["content"]
    lower = content.lower()

    if sender == AGENT_NAME:
        return False

    # If the message starts with another agent's name and Mo is not mentioned,
    # it is addressed to someone else -- stay quiet.
    mo_names = ["mo-assistant", "mo assistant", "mo-assist", "@mo"]
    mo_mentioned = (
        any(name in lower for name in mo_names)
        or "mo" in lower.split()   # "mo" as a standalone word
    )
    words = lower.split()
    if words:
        first_word = words[0].rstrip(",.!?:")
        if (first_word != "mo-assistant"
                and not mo_mentioned
                and len(words) > 1
                and words[1] in ("can", "could", "please", "will", "would", "are", "do")):
            print(f"[QUIET] Message addressed to '{first_word}', not us.")
            return False

    if AGENT_NAME.lower() in lower:
        # If the sender is another agent (not a human), only reply when
        # they share actual content -- code block, a question, or a long
        # message. Short acknowledgements like "I'll draft X" are noise.
        if "human" not in sender.lower():
            has_code = "```" in content
            has_question = "?" in content
            is_long = len(content) > 150
            if not (has_code or has_question or is_long):
                print(f"[QUIET] Ignoring short acknowledgement from {sender}.")
                return False
        return True

    if "attention all agents" in lower:
        return True
    if "@everyone" in lower:
        return True
    # If an agent posts a code block, only respond if Mo-Assistant was
    # recently asked to review -- not just because code exists in the chat.
    if "human" not in sender.lower() and "```" in content:
        from history import load_all_history

        recent = load_all_history()[-10:]
        review_requested = any(
            AGENT_NAME.lower() in m.get("content", "").lower()
            and any(
                w in m.get("content", "").lower()
                for w in ["review", "check", "granska"]
            )
            for m in recent
        )
        return review_requested
    if "human" in sender.lower():
        engineering_words = [
            "help",
            "code",
            "build",
            "create",
            "fix",
            "review",
            "python",
            "error",
            "bug",
            "write",
            "function",
        ]
        if any(word in lower for word in engineering_words):
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
    sender = message["agent_name"]
    content = message["content"]

    seq = message.get("seq")

    print(f"[HUB] {sender}: {content[:80]}")
    save_message(message)

    if seq in state.replied_seqs:
        print(f"[SKIP] Already replied to seq {seq} -- skipping.")
        return

    if not should_respond(message):
        print("[QUIET] Not our turn to speak.")
        return

    if not claude.check_budget():
        print("[QUIET] Budget exhausted.")
        return

    # Wait before responding -- gives other agents time to claim the task first.
    # After waiting, fetch any new messages so Claude has the latest context.
    delay = settings.get("response_delay_seconds", 3)
    print(f"[WAIT] Pausing {delay}s before responding...")
    time.sleep(delay)

    fresh = get_messages(since=state.last_seq)
    for m in fresh:
        save_message(m)
        state.last_seq = m["seq"]
        print(f"[REFRESH] Picked up message from {m['agent_name']} during wait")

    if not claude.check_budget():
        print("[QUIET] Budget exhausted.")
        return

    # Check templates BEFORE calling Claude -- but only for human messages.
    # When an agent posts code, we should review it, not fire a template.
    # A template firing on agent code causes repeated identical replies.
    if "human" in sender.lower():
        template_reply = find_template(content)
        if template_reply:
            print("[TEMPLATE] Using pre-written response -- no tokens spent.")
            post_message(template_reply)
            state.replied_seqs.add(seq)
            state.last_message_time = time.time()
            return

    # Only coordinate roles when explicitly asked.
    # Keywords that trigger dispatch: "dispatch", "assign roles", "coordinate", etc.
    dispatch_triggers = [
        "dispatch",
        "assign roles",
        "assign tasks",
        "coordinate",
        "who does what",
        "who should do",
    ]
    if any(kw in content.lower() for kw in dispatch_triggers):
        role = coordinate(content, sender)
        print(f"[COORD] Role assigned: {role}")
        state.last_message_time = time.time()
        return

    # Fetch any messages that arrived while we were deciding whether to respond.
    # This ensures Claude sees code or context posted by other agents in the
    # gap between our last poll and now -- fixes the "missed code review" bug.
    fresh = get_messages(since=state.last_seq)
    for m in fresh:
        save_message(m)
        state.last_seq = m["seq"]
        print(f"[REFRESH] Picked up late message from {m['agent_name']}")

    # Detect if this is real work (writing or reviewing code).
    # Only claim and announce done for actual tasks -- not for questions or chat.
    lower = content.lower()
    is_write_task = any(
        w in lower for w in ["write", "create", "build", "make", "implement"]
    ) and any(w in lower for w in ["code", "function", "program", "script", "file"])
    is_review_task = (
        any(w in lower for w in ["review", "check", "granska"]) or "```" in content
    )
    is_real_task = is_write_task or is_review_task

    task_summary = content[:60] + "..." if len(content) > 60 else content

    if is_real_task:
        post_message(f"Taking on: {task_summary}")

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
            code = parsed["content"]
            write_file(filename, code)
            post_message(
                f"I have written `{filename}` to the workspace:\n\n"
                f"```python\n{code}\n```"
            )
            post_message(f"Done: {task_summary}")
            print(f"[FILE] Created and confirmed: {filename}")
            state.replied_seqs.add(seq)
            state.last_message_time = time.time()
            return
    except (json.JSONDecodeError, KeyError):
        pass

    # Scan for JSON embedded in plain text -- Claude sometimes wraps the JSON
    # in a sentence like "Here is the file: {...}" instead of returning pure JSON.
    if not clean.strip().startswith("{"):
        decoder = json.JSONDecoder()
        for i, char in enumerate(clean):
            if char == "{":
                try:
                    parsed, _ = decoder.raw_decode(clean, i)
                    if isinstance(parsed, dict) and parsed.get("type") == "file":
                        filename = parsed["filename"]
                        code = parsed["content"]
                        write_file(filename, code)
                        post_message(
                            f"I have written `{filename}` to the workspace:\n\n"
                            f"```python\n{code}\n```"
                        )
                        if is_real_task:
                            post_message(f"Done: {task_summary}")
                        print(f"[FILE] Created and confirmed: {filename}")
                        state.replied_seqs.add(seq)
                        state.last_message_time = time.time()
                        return
                except json.JSONDecodeError:
                    continue

    print(f"[REPLY] Sending: {reply[:80]}")
    post_message(reply)
    if is_real_task and "```" in reply:
        post_message(f"Done: {task_summary}")
    state.replied_seqs.add(seq)
    state.last_message_time = time.time()
