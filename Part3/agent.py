# ============================================================
# MO-ASSISTANT — Part 3: Multi-Agent Collaboration
# ============================================================
# This agent connects to a shared group chat hub where all
# students' agents communicate and collaborate on software.
# Run it with: python agent.py
# ============================================================


# ─── SECTION 1: IMPORTS ─────────────────────────────────────
# These are Python libraries (tools) we borrow before starting.

import requests  # sends messages over the internet (to Claude and the hub)
import threading  # lets two things run at the same time (agent + console control)
import time  # lets us pause and track time (rate limiting)
import os  # reads environment variables like your API key
import json  # converts between Python objects and JSON text
import datetime  # used to add a timestamp when we save messages to history
from dotenv import load_dotenv  # reads your .env file so the API key stays secret


# ─── SECTION 2: CONFIGURATION ───────────────────────────────
# Settings are loaded from two places:
#   .env        → secret things (API key) — never share this file
#   config.json → non-secret settings (model, budget, hub URL, system prompt)
#
# This is the same pattern as Part 2. The benefit: you can change
# any setting in config.json without touching the Python code.

load_dotenv()  # reads the .env file into memory
API_KEY = os.getenv("ANTHROPIC_API_KEY")  # your secret key, never hardcoded
PWD = "th25-agents-vg"  # hub password (shared with the whole class)

# Load all other settings from config.json
with open("config.json", "r") as f:
    config = json.load(f)

HUB = config["hub"]  # the shared class hub URL
AGENT_NAME = config["agent_name"]  # your agent's unique name in the group chat
TEST_MODE = config["test_mode"]  # True = local test, False = connect to real hub

# These two variables track token spending and are updated as the agent runs.
# They are NOT in config.json because they change at runtime, not at startup.
tokens_spent = 0
last_message_time = 0

# This flag controls the main loop.
# When it becomes False (via console "stop" command), the agent shuts down.
agent_running = True

# Create the logs/ folder if it doesn't exist yet.
# exist_ok=True means: don't crash if the folder is already there.
os.makedirs("logs", exist_ok=True)


# ─── SECTION 3: CHAT HISTORY ────────────────────────────────
# New in Part 3! In Part 2, we saved the conversation between
# the user and the agent. In Part 3, we save the entire group
# chat so the agent can look back at what was discussed.
#
# TWO separate things:
#   DISK  → we save ALL messages forever (logs/chat_history.json)
#   CLAUDE → we only send the last N messages as context (saves tokens)
#
# Why not send everything to Claude?
# Each API call costs tokens for everything you send.
# Sending 500 old messages every time = 12,500 tokens per reply.
# Your entire budget would be gone in one message.
# Sending only the last 15 messages = ~375 tokens. Much smarter.

HISTORY_FILE = os.path.join("logs", "chat_history.json")


def save_message(message):
    """
    Save one hub message to the history file on disk.
    We save EVERY message we receive, even ones we don't reply to.
    This gives us a complete record of the group chat.
    """
    # Add a timestamp so we know exactly when we received the message
    record = dict(message)  # make a copy so we don't modify the original
    record["received_at"] = datetime.datetime.now().isoformat()

    # Load the existing history, add the new message, save back
    history = load_all_history()
    history.append(record)

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def load_all_history():
    """
    Load the full chat history from disk.
    Returns an empty list if the file doesn't exist yet
    (which is normal on first run).
    """
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def get_recent_context():
    """
    Return the last N messages from history as a formatted string.
    N comes from config.json ("context_messages").

    This is the 'memory' we give Claude before asking it to reply.
    Without this, Claude would reply without knowing what was discussed.

    Example output:
        human:Teacher: Can anyone write a sort function?
        Hassan-Agent: I can help!
        human:Teacher: Mo-Assistant, can you review that?
    """
    n = config["context_messages"]  # how many messages to include (e.g. 15)
    history = load_all_history()
    recent = history[-n:]  # take only the last N from the full list

    if not recent:
        return "No previous messages in this session."

    # Format each message as "sender: content" on its own line
    lines = [f"{m['agent_name']}: {m['content']}" for m in recent]
    return "\n".join(lines)


# ─── SECTION 4: CLAUDE API FUNCTION ─────────────────────────
# This is how your agent "thinks". It sends the recent chat
# context + the new message to Claude and gets a reply back.
# It also tracks token usage so we stay within budget.


def ask_claude(current_message, sender):
    """
    Send a message to Claude with recent chat history as context.

    current_message : the new message we need to reply to
    sender          : who sent that message (e.g. "human:Teacher")

    We include the last N chat messages so Claude understands
    the conversation before replying — just like a human would
    read back through the chat before writing an answer.
    """
    context = get_recent_context()

    # Build the message we send to Claude.
    # We combine the recent context + the new message into one prompt.
    messages = [
        {
            "role": "user",
            "content": (
                f"Here is the recent group chat history:\n\n"
                f"{context}\n\n"
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
            "model": config["model"],  # from config.json
            "max_tokens": config["max_tokens"],  # from config.json
            "system": config["system_prompt"],
            "messages": messages,
        },
    )
    data = response.json()

    # Track how many tokens this call used
    update_tokens(data["usage"]["input_tokens"], data["usage"]["output_tokens"])

    return data["content"][0]["text"]


def check_budget():
    """Returns True if we still have token budget left, False if we're out."""
    budget = config["max_tokens_budget"]
    if tokens_spent >= budget:
        print(f"[BUDGET] Token budget reached! Spent: {tokens_spent}/{budget}")
        return False
    return True


def update_tokens(input_tokens, output_tokens):
    """Adds the tokens used by one Claude call to the running total."""
    global tokens_spent
    tokens_spent += input_tokens + output_tokens
    print(f"[TOKENS] Spent so far: {tokens_spent}/{config['max_tokens_budget']}")


# ─── SECTION 5: HUB COMMUNICATION ───────────────────────────
# These two functions are how your agent talks to the group chat.
# The hub is like a message board — agents post messages and
# read what others have posted.


def post_message(content):
    """
    Post a message from Mo-Assistant to the group chat hub.
    In TEST_MODE, just prints to the screen instead of sending.
    This lets you test the agent safely without touching the class hub.
    """
    if TEST_MODE:
        print(f"[TEST] Would send to hub: {content}")
        return {}
    response = requests.post(
        f"{HUB}/api/message",
        json={"agent_name": AGENT_NAME, "content": content, "password": PWD},
    )
    return response.json()


# These are fake messages used in TEST_MODE.
# Edit them to simulate different scenarios before going live.
# Good test cases to include:
#   - A human asking an engineering question
#   - Another agent mentioning Mo-Assistant by name
#   - A bot message that should be ignored
#   - A broadcast (@everyone / attention all agents)
FAKE_MESSAGES = [
    {
        "seq": 1,
        "agent_name": "human:Teacher",
        "content": "Can anyone write a Python function that reverses a string?",
    },
    {"seq": 2, "agent_name": "Hassan-Agent", "content": "I can help with that!"},
    {
        "seq": 3,
        "agent_name": "human:Teacher",
        "content": "Mo-Assistant, can you review that code?",
    },
    {
        "seq": 4,
        "agent_name": "amr-quizmaster",
        "content": "Quiz time! What is 2+2?",
    },  # should be ignored
]


def get_messages(since=0):
    """
    Fetch all new messages from the hub since a given sequence number.
    'since=0' means fetch everything from the beginning.
    Each message has: seq, agent_name, content

    In TEST_MODE, returns FAKE_MESSAGES instead of calling the real hub.
    The filter [m for m in ... if m["seq"] > since] makes sure we only
    return messages we haven't seen yet.
    """
    if TEST_MODE:
        return [m for m in FAKE_MESSAGES if m["seq"] > since]
    response = requests.get(
        f"{HUB}/api/messages", params={"since": since, "password": PWD}
    )
    return response.json()["messages"]


# ─── SECTION 5b: WORKSPACE ──────────────────────────────────
# The workspace folder is where the agent saves code files.
# When another agent or human asks Mo-Assistant to write code,
# it creates a real .py file here instead of just chatting.

WORKSPACE = "workspace"


def write_file(filename, content):
    """
    Write a code file to the workspace folder.
    filename : the name of the file, e.g. "sort.py"
    content  : the code to write inside the file
    Returns the full path so we can confirm it was created.
    """
    filepath = os.path.join(WORKSPACE, filename)
    with open(filepath, "w") as f:
        f.write(content)
    print(f"[FILE] Created: {filepath}")
    return filepath


# ─── SECTION 6: MESSAGE HANDLER ─────────────────────────────
# This is the brain that decides WHEN to respond and WHAT to say.
# Not every message needs a reply — if all agents replied to
# everything, the chat would explode with hundreds of messages.


def should_respond(message):
    """
    Decide whether Mo-Assistant should reply to this message.
    Returns True (respond) or False (stay quiet).

    The logic: only speak when it's genuinely useful.
    Smart filtering prevents message storms — if every agent
    replied to every message, the chat would become unusable.
    """
    sender = message["agent_name"]
    content = message["content"].lower()

    # Never respond to our own messages — would cause an infinite loop
    if sender == AGENT_NAME:
        return False

    # Always respond if someone mentions us directly by name
    if AGENT_NAME.lower() in content:
        return True

    # Respond to broadcasts meant for all agents
    if "attention all agents" in content:
        return True
    if "@everyone" in content:
        return True

    # Respond to humans posting engineering questions.
    # Humans post as "human" or "human:Name" — we use startswith
    # so both formats are caught (fixes a bug from the notebook version).
    if sender.lower().startswith("human"):
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
        if any(word in content for word in engineering_words):
            return True

    # Stay quiet for everything else
    return False


def handle_message(message):
    """
    Process one message from the hub:
    1. Save it to history (always — even if we don't reply)
    2. Check if we should respond
    3. Check if we have budget left
    4. Ask Claude (with recent context) what to reply
    5. Post the reply to the hub
    """
    global last_message_time

    sender = message["agent_name"]
    content = message["content"]

    print(f"[HUB] {sender}: {content[:80]}")  # show first 80 chars

    # Save every message to disk — even ones we won't reply to.
    # This builds a complete record of the group chat.
    save_message(message)

    if not should_respond(message):
        print("[QUIET] Not our turn to speak.")
        return

    if not check_budget():
        print("[QUIET] Budget exhausted.")
        return

    print("[THINKING] Asking Claude for a reply...")
    reply = ask_claude(content, sender)

    # Check if Claude wants to write a file.
    # If the reply is JSON with "type": "file", we create the file
    # in the workspace folder and post a confirmation to the chat.
    # If it's normal text, we just post it as a message.
    try:
        parsed = json.loads(reply)
        if parsed.get("type") == "file":
            filename = parsed["filename"]
            code = parsed["content"]
            write_file(filename, code)
            post_message(
                f"I've written `{filename}` to the workspace:\n\n```python\n{code}\n```"
            )
            print(f"[FILE] Sent file confirmation to hub.")
            last_message_time = time.time()
            return
    except (json.JSONDecodeError, KeyError):
        pass  # not a file response — treat as normal text reply

    print(f"[REPLY] Sending: {reply[:80]}")
    post_message(reply)
    last_message_time = time.time()


# ─── SECTION 7: CONSOLE CONTROL ─────────────────────────────
# This runs in a separate thread so you can type commands
# while the agent is running — without stopping it.
#
# A "thread" is like a second worker running at the same time.
# Worker 1 (main loop): polls the hub every 5 seconds
# Worker 2 (this):      waits for you to type a command
#
# Available commands:
#   budget <number>  — change the max token budget
#   rate <seconds>   — change the rate limit between messages
#   status           — show current token usage and settings
#   history          — show how many messages are saved to disk
#   stop             — shut down the agent gracefully


def console_control():
    """Runs in background. Lets you control the agent while it runs."""
    global agent_running
    rate = config["rate_limit_seconds"]

    print(
        "[CONSOLE] Control active. Commands: budget <n>, rate <n>, status, history, stop"
    )

    while agent_running:
        try:
            cmd = input("Control> ").strip().lower()

            if cmd.startswith("budget "):
                # Update the budget inside config so check_budget() sees the new value
                config["max_tokens_budget"] = int(cmd.split()[1])
                print(
                    f"[CONSOLE] Budget updated to {config['max_tokens_budget']} tokens"
                )

            elif cmd.startswith("rate "):
                config["rate_limit_seconds"] = int(cmd.split()[1])
                print(
                    f"[CONSOLE] Rate limit updated to {config['rate_limit_seconds']} seconds"
                )

            elif cmd == "status":
                print(
                    f"[CONSOLE] Tokens spent : {tokens_spent}/{config['max_tokens_budget']}"
                )
                print(
                    f"[CONSOLE] Rate limit   : {config['rate_limit_seconds']}s between messages"
                )
                print(
                    f"[CONSOLE] Context size : last {config['context_messages']} messages sent to Claude"
                )
                print(f"[CONSOLE] Test mode    : {TEST_MODE}")

            elif cmd == "history":
                # Show how many messages are saved in the history file
                all_msgs = load_all_history()
                print(f"[CONSOLE] {len(all_msgs)} messages saved in {HISTORY_FILE}")

            elif cmd == "stop":
                print("[CONSOLE] Stopping agent...")
                agent_running = False
                break

            else:
                print(
                    "[CONSOLE] Unknown command. Try: budget <n>, rate <n>, status, history, stop"
                )

        except Exception as e:
            print(f"[CONSOLE] Error: {e}")


# ─── SECTION 8: MAIN LOOP ────────────────────────────────────
# This is the heart of the agent. It runs forever until stopped.
#
# Every 5 seconds it:
# 1. Fetches new messages from the hub (or fake messages in TEST_MODE)
# 2. For each new message:
#    - Updates last_seq so we never re-read old messages
#    - Saves the message to history
#    - Checks the rate limit
#    - Decides whether to reply
#    - If yes: asks Claude (with context) and posts the reply
# 3. Waits 5 seconds and repeats
#
# The console_control thread runs at the same time so you can
# type commands without interrupting the polling loop.

if __name__ == "__main__":
    # Start the console control in a background thread.
    # daemon=True means it stops automatically when the main program stops,
    # so you don't have to manually kill it.
    control_thread = threading.Thread(target=console_control, daemon=True)
    control_thread.start()

    print(f"[START] {AGENT_NAME} is starting up...")
    print(f"[START] Test mode: {TEST_MODE}")
    print(f"[START] History will be saved to: {HISTORY_FILE}")
    post_message(f"{AGENT_NAME} is online and ready to collaborate!")

    last_seq = 0  # tracks the last message we've seen so we don't re-read old ones

    while agent_running:
        try:
            # Fetch only messages newer than last_seq
            new_messages = get_messages(since=last_seq)

            for message in new_messages:
                # Always update our position — even if we skip replying.
                # This was a bug in the notebook: skipped messages were lost forever.
                last_seq = message["seq"]

                # Check rate limit BEFORE deciding to reply.
                # We still save the message to history (done inside handle_message),
                # but we skip sending a reply if too soon.
                current_time = time.time()
                if current_time - last_message_time < config["rate_limit_seconds"]:
                    sender = message["agent_name"]
                    print(
                        f"[RATE] Rate limit active — read message from {sender} but not replying yet."
                    )
                    save_message(message)  # still save it even if rate limited
                    continue

                handle_message(message)

            time.sleep(5)  # wait 5 seconds before checking for new messages again

        except KeyboardInterrupt:
            # User pressed Ctrl+C in the terminal
            print(f"\n[STOP] {AGENT_NAME} shutting down...")
            post_message(f"{AGENT_NAME} is going offline. Goodbye!")
            agent_running = False
            break

        except Exception as e:
            # Something went wrong (hub might be down, network error, etc.)
            # We wait 10 seconds and try again — no crash.
            print(f"[ERROR] {e}")
            print("[ERROR] Waiting 10 seconds before retrying...")
            time.sleep(10)

    print("[STOP] Agent stopped.")
