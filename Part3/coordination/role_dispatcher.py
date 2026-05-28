# ============================================================
# ROLE DISPATCHER -- Part 3: Mo-Assistant / coordination
# ============================================================
# Scans recent chat history to find which agents are online,
# assigns roles to each one, and posts the assignments to the hub.
#
# Role priority order:
#   1. planner     -> breaks down the task
#   2. implementer -> writes the code
#   3. reviewer    -> checks the result
#
# Mo-Assistant takes its chosen role first.
# Remaining roles go to other online agents in order.
# Any role with no agent assigned goes back to Mo-Assistant.
# ============================================================

from config_loader        import AGENT_NAME
from hub                  import post_message
from history              import load_all_history
from coordination.collaboration_roles import describe_role


# How many recent messages to scan when looking for active agents.
RECENT_SCAN_LIMIT = 50

# The three core task roles in priority order.
TASK_ROLES = ["planner", "implementer", "reviewer"]


# --- GET ACTIVE AGENTS --------------------------------------
# Scans the last N messages in history and returns a list of
# agent names who have spoken recently (excluding humans and
# Mo-Assistant itself).

def get_active_agents() -> list:
    """Return a list of other agent names seen in recent history."""
    history = load_all_history()
    recent  = history[-RECENT_SCAN_LIMIT:]

    seen = {}
    for msg in recent:
        name = msg.get("agent_name", "")
        if name == AGENT_NAME:
            continue
        if "human" in name.lower():
            continue
        seen[name] = True

    return list(seen.keys())


# --- BUILD DISPATCH MESSAGE ---------------------------------
# Formats the role assignment as a readable hub message.

def build_dispatch_message(agent_roles: dict) -> str:
    """
    Build a hub message announcing role assignments.

    agent_roles : {agent_name: [role1, role2, ...]}
    """
    lines = ["**Task received. Here are the role assignments:**\n"]

    for agent, roles in agent_roles.items():
        role_str  = " + ".join(roles)
        first_role = roles[0]
        desc      = describe_role(first_role)
        tag       = " *(you)*" if agent == AGENT_NAME else ""
        lines.append(f"- **{agent}**{tag} → {role_str} — {desc}")

    lines.append(
        f"\nI will start as **{agent_roles[AGENT_NAME][0]}**. "
        f"Let's coordinate before anyone starts building."
    )

    return "\n".join(lines)


# --- DISPATCH ROLES -----------------------------------------
# Main entry point. Assigns roles to all online agents and
# posts the result to the hub.

def dispatch_roles(my_role: str) -> dict:
    """
    Assign roles to Mo-Assistant and all other online agents.
    Posts the assignments to the hub.

    my_role : the role Mo-Assistant has already chosen

    Returns the assignments dict {agent_name: [roles]}
    """
    active_agents = get_active_agents()

    # Roles left to assign after Mo-Assistant takes its own.
    remaining = [r for r in TASK_ROLES if r != my_role]

    # Build assignments dict -- Mo-Assistant goes first.
    assignments: dict = {AGENT_NAME: [my_role]}

    for i, agent in enumerate(active_agents):
        if i < len(remaining):
            assignments[agent] = [remaining[i]]

    # Any role still uncovered goes back to Mo-Assistant.
    assigned_roles = {r for roles in assignments.values() for r in roles}
    for role in TASK_ROLES:
        if role not in assigned_roles:
            assignments[AGENT_NAME].append(role)

    # Post the dispatch message to the hub.
    post_message(build_dispatch_message(assignments))

    return assignments
