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

import subprocess
import os
from safety import is_safe_command

WORKSPACE = "workspace"
MAX_OUTPUT = 500

# Make sure workspace folder exists
os.makedirs(WORKSPACE, exist_ok=True)


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


def write_file(filename, content):
    """
    Write a code file to the workspace folder.
    Only allows writing inside the workspace — not anywhere on disk.
    """
    # Safety: only allow simple filenames, no path tricks like ../../secret.txt
    if "/" in filename or "\\" in filename or ".." in filename:
        return f"[BLOCKED] Invalid filename: {filename}"

    filepath = os.path.join(WORKSPACE, filename)

    with open(filepath, "w") as f:
        f.write(content)

    print(f"[FILE] Created: {filepath}")
    return filepath


def read_file(filename):
    """
    Read a file from the workspace folder.
    Returns the content as a string.
    Limits output to 500 characters to protect token budget.
    """
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
