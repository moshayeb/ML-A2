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

# Force UTF-8 output — works on Windows cmd, PowerShell, and Git Bash.
# reconfigure() alone fails in Git Bash, so we replace the stream entirely.
try:
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True
    )
except AttributeError:
    pass  # IDLE or other environments where buffer is unavailable

from loop import run

if __name__ == "__main__":
    run()
