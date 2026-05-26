# ============================================================
# CONFIG LOADER — Part 3: Mo-Assistant
# ============================================================
# This file loads ALL settings exactly once when the program starts.
# Every other file imports from here instead of loading config.json
# themselves.
#
# WHY THIS MATTERS:
# If each file loaded config.json separately, they would each get
# their own copy of the settings. When you type "rate 10" in the
# console to change the rate limit, only one copy would change —
# all the others would still have the old value.
#
# By loading once here and sharing the same 'settings' dictionary,
# ALL files see the same object. A change in one place is instantly
# visible everywhere. This is the standard Python way to share
# configuration across multiple files.
# ============================================================


# ─── IMPORTS ────────────────────────────────────────────────

import os
import json
from dotenv import load_dotenv  # reads the .env file


# ─── LOAD SECRETS FROM .ENV ─────────────────────────────────
# The .env file holds your API key — a secret that should never
# be hardcoded in Python files or shared with anyone.
# load_dotenv() reads it and makes it available via os.getenv().

load_dotenv()
API_KEY = os.getenv("ANTHROPIC_API_KEY")  # your Anthropic secret key
PWD     = "th25-agents-vg"               # hub password (shared with the class)


# ─── LOAD SETTINGS FROM CONFIG.JSON ─────────────────────────
# All non-secret settings live in config.json.
# 'settings' is a dictionary — a mutable object.
# Because it is mutable, all files that import it share
# the exact same object in memory. Changes made in one
# file (like the console_control updating rate_limit_seconds)
# are immediately visible in all other files.

with open("config.json", "r") as f:
    settings = json.load(f)

# Shortcuts for the most commonly used settings.
# These are read once at startup and do not change at runtime.
HUB        = settings["hub"]         # the class hub URL
AGENT_NAME = settings["agent_name"]  # your unique name in the group chat
TEST_MODE  = settings["test_mode"]   # True = safe local test, False = live hub
