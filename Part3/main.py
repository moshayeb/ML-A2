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

from loop import run

if __name__ == "__main__":
    run()
