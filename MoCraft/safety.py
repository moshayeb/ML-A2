# ============================================================
# SAFETY CHECKER
# Blocks dangerous commands before they run on your computer.
# Called before every bash command the agent wants to execute.
# ============================================================

# Commands that are too dangerous to allow
BLOCKED_COMMANDS = [
    "rm",
    "del",
    "format",
    "shutdown",
    "rmdir",
    "rd",
    "erase",
    "deltree",
    "cipher",
    "curl",
    "wget",
    "powershell -enc",
    ":(){:|:&};:",  # fork bomb
]

# Only block true code-injection patterns — pipes and chaining are needed for real bash work
BLOCKED_PATTERNS = [
    "$(",   # command substitution
    "`",    # backtick substitution
    ">/dev/sd",   # block writing to raw devices
    ">/etc/",     # block overwriting system files
]


def is_safe_command(command):
    """
    Returns True if the command is safe to run.
    Returns False if it should be blocked.
    """
    import os as _os
    command_lower = command.lower().strip()
    # Extract the bare executable name so /bin/rm, ./rm, etc. are caught too
    first_token = command_lower.split()[0] if command_lower.split() else ""
    base_cmd = _os.path.basename(first_token)

    # Check for blocked commands
    for blocked in BLOCKED_COMMANDS:
        if command_lower.startswith(blocked) or base_cmd == blocked:
            print(f"[SAFETY] Blocked dangerous command: {blocked}")
            return False

    # Check for dangerous patterns
    for pattern in BLOCKED_PATTERNS:
        if pattern in command:
            print(f"[SAFETY] Blocked dangerous pattern: {pattern}")
            return False

    return True
