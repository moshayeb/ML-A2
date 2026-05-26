# ============================================================
# TOOLS — Part 3: Mo-Assistant
# ============================================================
# This file contains all the tools Mo-Assistant can use.
# Each tool is a function that does one specific job.
#
# Available tools:
#   run_command(command)           → runs a terminal command safely
#   write_file(filename, content)  → writes a file to workspace
#   read_file(filename)            → reads a file from workspace
# ============================================================


# ─── IMPORTS ────────────────────────────────────────────────

import subprocess
import os
from safety import is_safe_command


# ─── CONFIGURATION ──────────────────────────────────────────
# WORKSPACE : the folder where all code files are saved.
#             The agent can only read and write inside here —
#             never anywhere else on your computer.
# MAX_OUTPUT: limits how much text a tool can return.
#             Protects the token budget — a command that prints
#             thousands of lines would waste all your tokens.

WORKSPACE  = "workspace"
MAX_OUTPUT = 500

# Create the workspace folder if it doesn't exist yet.
# exist_ok=True means: don't crash if the folder is already there.
os.makedirs(WORKSPACE, exist_ok=True)


# ─── TOOL 1: RUN COMMAND ────────────────────────────────────
# Runs a terminal command on your computer.
# Always checks safety first — dangerous commands are blocked
# before they can do any harm.

def run_command(command):
    """
    Run a terminal command safely.
    Checks safety first — blocks dangerous commands.
    Limits output to 500 characters to protect token budget.
    """
    if not is_safe_command(command):
        return f"[BLOCKED] Command not allowed: {command}"

    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    output = result.stdout + result.stderr

    if len(output) > MAX_OUTPUT:
        output = output[:MAX_OUTPUT] + "\n[Output truncated at 500 characters]"

    return output


# ─── TOOL 2: WRITE FILE ─────────────────────────────────────
# Saves a code file into the workspace folder.
# This is what makes Mo-Assistant a real software collaborator —
# it can create actual files, not just chat about code.
# Safety check prevents writing outside the workspace folder.

def write_file(filename, content):
    """
    Write a code file to the workspace folder.
    Only allows writing inside the workspace — not anywhere on disk.
    """
    # Safety: block path tricks like ../../secret.txt that could
    # escape the workspace and write to sensitive parts of the disk.
    if "/" in filename or "\\" in filename or ".." in filename:
        return f"[BLOCKED] Invalid filename: {filename}"

    filepath = os.path.join(WORKSPACE, filename)

    with open(filepath, "w") as f:
        f.write(content)

    print(f"[FILE] Created: {filepath}")
    return filepath


# ─── TOOL 3: READ FILE ──────────────────────────────────────
# Reads a code file from the workspace folder.
# Useful when the agent needs to review or build on existing code.
# Output is limited to 500 characters to protect the token budget.

def read_file(filename):
    """
    Read a file from the workspace folder.
    Returns the content as a string.
    Limits output to 500 characters to protect token budget.
    """
    # Same safety check as write_file — no path tricks allowed.
    if "/" in filename or "\\" in filename or ".." in filename:
        return f"[BLOCKED] Invalid filename: {filename}"

    filepath = os.path.join(WORKSPACE, filename)

    try:
        with open(filepath, "r") as f:
            content = f.read()

        if len(content) > MAX_OUTPUT:
            content = content[:MAX_OUTPUT] + "\n[Content truncated at 500 characters]"

        return content

    except FileNotFoundError:
        return f"[ERROR] File not found: {filename}"
