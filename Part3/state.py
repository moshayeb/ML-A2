# ============================================================
# STATE -- Part 3: Mo-Assistant
# ============================================================
# Shared runtime variables that multiple modules read and write.
#
# WHY A SEPARATE FILE?
# agent.py, console.py, and loop.py all need to read and update
# these two variables. Putting them here avoids circular imports
# and makes shared mutable state explicit and easy to find.
#
# HOW TO USE:
#   import state
#   state.agent_running = False     <- update
#   if state.agent_running: ...     <- read
#
# DO NOT use 'from state import agent_running' in any file that
# writes to these variables -- that copies the value and your
# update will NOT be visible to the other modules.
# ============================================================

agent_running     = True   # set to False to stop the main loop
last_message_time = 0      # unix timestamp of the last reply we sent
last_seq          = 0      # seq number of the last hub message we processed
replied_seqs      = set()  # seq numbers we have already replied to -- never reply twice
paused            = False  # True when a human issues a broadcast pause; cleared on resume
