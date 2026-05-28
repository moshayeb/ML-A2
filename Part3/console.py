# ============================================================
# CONSOLE -- Part 3: Mo-Assistant
# ============================================================
# Background control thread. Runs alongside the main loop so
# you can type commands in the terminal while the agent runs.
#
# Started by loop.py as a daemon thread -- it shuts down
# automatically when the main program exits.
#
# Commands:
#   budget <n>   -> change the maximum token budget
#   rate <n>     -> change seconds between replies
#   status       -> show token usage and current settings
#   history      -> show how many messages are saved to disk
#   stop         -> shut down the agent gracefully
# ============================================================


# --- IMPORTS ------------------------------------------------

import claude
import state
from config_loader import settings
from history       import load_all_history, HISTORY_FILE


# --- CONSOLE CONTROL ----------------------------------------

def console_control():
    print("[CONSOLE] Control active. Commands: budget <n>, rate <n>, status, history, stop/quit/q")

    while state.agent_running:
        try:
            cmd = input("Control> ").strip().lower()

            if cmd.startswith("budget "):
                settings["max_tokens_budget"] = int(cmd.split()[1])
                print(f"[CONSOLE] Budget updated to {settings['max_tokens_budget']} tokens")

            elif cmd.startswith("rate "):
                settings["rate_limit_seconds"] = int(cmd.split()[1])
                print(f"[CONSOLE] Rate limit updated to {settings['rate_limit_seconds']} seconds")

            elif cmd == "status":
                print(f"[CONSOLE] Tokens spent : {claude.tokens_spent}/{settings['max_tokens_budget']}")
                print(f"[CONSOLE] Rate limit   : {settings['rate_limit_seconds']}s between replies")
                print(f"[CONSOLE] Context size : last {settings['context_messages']} messages sent to Claude")

            elif cmd == "history":
                all_msgs = load_all_history()
                print(f"[CONSOLE] {len(all_msgs)} messages saved in {HISTORY_FILE}")

            elif cmd in ("stop", "quit", "exit", "q"):
                print("[CONSOLE] Stopping agent...")
                state.agent_running = False
                break

            else:
                print("[CONSOLE] Unknown command. Try: budget <n>, rate <n>, status, history, stop/quit/q")

        except Exception as e:
            print(f"[CONSOLE] Error: {e}")
