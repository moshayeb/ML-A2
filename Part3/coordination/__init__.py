# ============================================================
# COORDINATION PACKAGE -- Part 3: Mo-Assistant
# ============================================================
# Exposes a single coordinate() function that runs the full
# role selection and dispatch flow in one call.
#
# Usage in agent.py:
#   from coordination import coordinate
#   coordinate(content, sender)
#
# Internal flow:
#   1. intent_detector   -> what does this message want?
#   2. collaboration_roles -> what role should Mo-Assistant take?
#   3. role_dispatcher   -> assign roles and post to hub
# ============================================================

from coordination.intent_detector      import detect_intent
from coordination.collaboration_roles  import choose_collaboration_role
from coordination.role_dispatcher      import dispatch_roles, get_active_agents


def coordinate(content: str, sender: str) -> str:
    """
    Run the full coordination flow for an incoming task message.

    content : the message text
    sender  : who sent it

    Returns the role Mo-Assistant took, or 'observer' if no action.
    """
    active_agents  = get_active_agents()
    is_group       = len(active_agents) > 0

    intent = detect_intent(content)
    role   = choose_collaboration_role(content, intent, is_group)

    # Observer means nothing useful to contribute -- skip dispatch.
    if role == "observer":
        return "observer"

    # Only dispatch roles for task-level work, not for questions or chat.
    if intent in ("execute_task", "delegate_task", "plan"):
        dispatch_roles(role)

    return role
