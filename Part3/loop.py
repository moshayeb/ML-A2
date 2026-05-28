# ============================================================
# LOOP -- Part 3: Mo-Assistant
# ============================================================
# The main run loop. Called by main.py to start the agent.
# Polls the hub every 5 seconds for new messages and hands
# each one off to handle_message() in agent.py.
#
# This file also starts the console control thread (console.py)
# so you can type commands while the loop is running.
#
# Files it uses:
#   state.py    -> shared flags (agent_running, last_message_time)
#   agent.py    -> handle_message() (process one message)
#   console.py  -> console_control() (background command thread)
#   hub.py      -> post_message(), get_messages()
#   history.py  -> save_message() (rate-limited saves)
# ============================================================


# --- IMPORTS ------------------------------------------------

import time
import threading

import state
from config_loader import AGENT_NAME, TEST_MODE, settings
from hub           import post_message, get_messages
from history       import save_message, HISTORY_FILE, save_last_seq, load_last_seq
from agent         import handle_message
from console       import console_control


# --- RUN ----------------------------------------------------
# The main loop. Called by main.py to start the agent.

def run():
    control_thread = threading.Thread(target=console_control, daemon=True)
    control_thread.start()

    state.last_seq = load_last_seq()  # resume from where we left off

    # Check if the hub was reset since we last ran.
    # If our saved seq is higher than the hub's highest message,
    # the teacher restarted the hub and we need to start from 0.
    try:
        hub_messages = get_messages(since=0)
        if hub_messages:
            hub_max = max(m["seq"] for m in hub_messages)
            if state.last_seq > hub_max:
                print(f"[START] Hub was reset (our seq {state.last_seq} > hub max {hub_max}). Starting fresh.")
                state.last_seq = 0
                if not TEST_MODE:
                    save_last_seq(0)
    except Exception:
        pass

    print(f"[START] {AGENT_NAME} is starting up...")
    print(f"[START] Resuming from message seq: {state.last_seq}")
    print(f"[START] History will be saved to: {HISTORY_FILE}")
    post_message(f"{AGENT_NAME} is online and ready to collaborate!")

    while state.agent_running:
        try:
            new_messages = get_messages(since=state.last_seq)

            for message in new_messages:
                state.last_seq = message["seq"]
                if not TEST_MODE:
                    save_last_seq(state.last_seq)

                current_time = time.time()
                if current_time - state.last_message_time < settings["rate_limit_seconds"]:
                    sender = message["agent_name"]
                    print(f"[RATE] Rate limit active -- saving but not replying to {sender}.")
                    save_message(message)
                    continue

                handle_message(message)

            time.sleep(5)

        except KeyboardInterrupt:
            print(f"\n[STOP] {AGENT_NAME} shutting down...")
            post_message(f"{AGENT_NAME} is going offline. Goodbye!")
            state.agent_running = False
            break

        except Exception as e:
            print(f"[ERROR] {e}")
            print("[ERROR] Waiting 10 seconds before retrying...")
            time.sleep(10)

    print("[STOP] Agent stopped.")
