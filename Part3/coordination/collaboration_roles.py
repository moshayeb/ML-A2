# ============================================================
# COLLABORATION ROLES -- Part 3: Mo-Assistant / coordination
# ============================================================
# Picks the best temporary role for Mo-Assistant to take in
# the current conversation, based on intent and context.
#
# Original design by Elias (classmate) -- adapted for Mo-Assistant.
#
# This is NOT a fixed identity. It is a context-aware decision
# about how Mo-Assistant can be most useful RIGHT NOW.
#
# Roles:
#   planner      -> define scope, break down the work
#   implementer  -> write the code for a clear assigned task
#   reviewer     -> review code or plans for correctness
#   tester       -> suggest or run verification steps
#   coordinator  -> help team agree on task ownership
#   clarifier    -> ask focused questions when goal is unclear
#   observer     -> stay quiet, nothing useful to add
# ============================================================

from typing import Literal


# Strict type for all valid roles.
HubCollaborationRole = Literal[
    "planner",
    "implementer",
    "reviewer",
    "tester",
    "coordinator",
    "clarifier",
    "observer",
]


def choose_collaboration_role(
    content: str,
    intent: str,
    is_group_context: bool = False,
) -> HubCollaborationRole:
    """
    Choose a temporary collaboration role for this message.

    content          : the raw message text
    intent           : output from detect_intent()
    is_group_context : True if other agents are online

    Returns a HubCollaborationRole string.
    """
    normalized = content.lower()

    # In group context, coordinate first to avoid duplicate work.
    if is_group_context:
        if intent in ("execute_task", "delegate_task"):
            return "coordinator"
        if "test" in normalized or "verify" in normalized:
            return "tester"
        if "review" in normalized or "granska" in normalized:
            return "reviewer"
        if "unclear" in normalized or "?" in normalized:
            return "clarifier"
        return "planner"

    # One-on-one: can take on direct implementation.
    if intent == "execute_task":
        return "implementer"
    if intent == "delegate_task":
        return "coordinator"
    if intent == "review":
        return "reviewer"
    if intent == "test":
        return "tester"
    if intent == "plan":
        return "planner"
    if intent == "question":
        return "clarifier"

    return "observer"


def describe_role(role: HubCollaborationRole) -> str:
    """
    Return a short human-readable description of a role.
    Used when Mo-Assistant announces its role or dispatches others.
    """
    descriptions = {
        "planner":     "define scope, break down the work, and identify the next step",
        "implementer": "write the code for one clear assigned task",
        "reviewer":    "review code or plans for correctness and improvements",
        "tester":      "suggest or run safe verification steps and report results",
        "coordinator": "reduce duplicate work by helping the team agree on ownership",
        "clarifier":   "ask focused questions when the goal or scope is unclear",
        "observer":    "stay quiet unless a clear useful contribution is possible",
    }
    return descriptions[role]
