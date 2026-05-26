# ============================================================
# HUB — Part 3: Mo-Assistant
# ============================================================
# This file handles all communication with the group chat hub.
# The hub is a shared server where all students' agents meet
# and exchange messages to collaborate on software projects.
#
# Think of it like a Slack channel — agents post messages,
# read what others posted, and decide whether to reply.
#
# Two main functions:
#   post_message(content)     → send a message to the hub
#   get_messages(since)       → fetch new messages from the hub
#
# TEST_MODE:
#   When True  → uses FAKE_MESSAGES (safe, no real hub connection)
#   When False → connects to the real class hub
# ============================================================


# ─── IMPORTS ────────────────────────────────────────────────

import requests
from config_loader import HUB, PWD, AGENT_NAME, TEST_MODE


# ─── FAKE MESSAGES (TEST MODE) ──────────────────────────────
# These are fake messages used when TEST_MODE = True.
# They let you test the agent safely without touching the hub.
#
# Edit these to simulate different scenarios:
#   - A human asking an engineering question
#   - Another agent mentioning Mo-Assistant by name
#   - A broadcast for all agents
#   - A bot message that should be ignored
#
# The 'seq' number must be unique and increasing.
# get_messages(since=N) returns only messages with seq > N.

FAKE_MESSAGES = [
    {
        "seq": 1,
        "agent_name": "human:Teacher",
        "content": "Can anyone write a Python function that reverses a string?"
    },
    {
        "seq": 2,
        "agent_name": "Hassan-Agent",
        "content": "I can help with that!"
    },
    {
        "seq": 3,
        "agent_name": "human:Teacher",
        "content": "Mo-Assistant, can you review that code?"
    },
    {
        "seq": 4,
        "agent_name": "amr-quizmaster",
        "content": "Quiz time! What is 2+2?"  # should be ignored
    },
    {
        "seq": 5,
        "agent_name": "human:Teacher",
        "content": "Mo-Assistant, write a Python function that sorts a list"
    },
]


# ─── POST MESSAGE ───────────────────────────────────────────
# Sends a message from Mo-Assistant to the group chat hub.
# In TEST_MODE, prints to the screen instead of sending.

def post_message(content):
    """
    Post a message to the group chat hub.
    In TEST_MODE, prints locally instead of sending to the real hub.
    """
    if TEST_MODE:
        print(f"[TEST] Would send to hub: {content}")
        return {}

    response = requests.post(
        f"{HUB}/api/message",
        json={
            "agent_name": AGENT_NAME,
            "content":    content,
            "password":   PWD
        }
    )
    return response.json()


# ─── GET MESSAGES ───────────────────────────────────────────
# Fetches new messages from the hub.
# 'since' is the sequence number of the last message we saw.
# Only messages with a higher seq number are returned —
# this prevents re-reading messages we already processed.
#
# Each message has:
#   seq        : unique number, increases with every new message
#   agent_name : who sent it (e.g. "human:Teacher", "Hassan-Agent")
#   content    : the message text

def get_messages(since=0):
    """
    Fetch all new messages from the hub since a given seq number.
    In TEST_MODE, returns FAKE_MESSAGES filtered by seq.
    """
    if TEST_MODE:
        return [m for m in FAKE_MESSAGES if m["seq"] > since]

    response = requests.get(
        f"{HUB}/api/messages",
        params={"since": since, "password": PWD}
    )
    return response.json()["messages"]
