# ============================================================
# MAIN -- Part 3: Mo-Assistant
# ============================================================
# Entry point. Run the agent with: python main.py
#
# WHY A SEPARATE FILE?
# main.py has one job: start the agent.
# loop.py has one job: contain the main while loop.
# Keeping them separate means you can import from loop.py or
# agent.py in other scripts without accidentally starting
# the agent.
#
# This is standard Python project structure.
# ============================================================

import sys
import io

# Force UTF-8 output on Windows (cmd, PowerShell, Git Bash/mintty).
# Without this, Claude replies with emoji or checkmarks crash with charmap.
try:
    if hasattr(sys.stdout, 'buffer'):
        # Standard case — works on cmd, PowerShell, most terminals
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True
        )
    else:
        # Git Bash / mintty — no .buffer, use reconfigure instead
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from loop import run

if __name__ == "__main__":
    run()
