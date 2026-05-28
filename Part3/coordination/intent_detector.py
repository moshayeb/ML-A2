# ============================================================
# INTENT DETECTOR -- Part 3: Mo-Assistant / coordination
# ============================================================
# Reads a message and figures out what the sender wants.
# Returns a single intent string used by collaboration_roles.py
# to decide what role Mo-Assistant should take.
#
# Intents:
#   execute_task  -> build / write / create something
#   delegate_task -> assign work to other agents
#   review        -> review or give feedback on code
#   test          -> test or verify something
#   plan          -> design or plan an approach
#   question      -> asking for information
#   unknown       -> fallback when nothing matches
# ============================================================


def detect_intent(content: str) -> str:
    """
    Detect what the sender wants based on message keywords.

    content : the raw message text

    Returns one of: execute_task, delegate_task, review,
                    test, plan, question, unknown
    """
    lower = content.lower()

    # Delegation -- asking someone else to take ownership
    delegation_words = [
        "assign", "delegate", "who can", "who should",
        "take care of", "handle this", "you do it"
    ]
    if any(w in lower for w in delegation_words):
        return "delegate_task"

    # Build / execute -- asking for code to be written
    execute_words = [
        "build", "create", "write", "make", "implement",
        "develop", "code", "generate", "produce"
    ]
    if any(w in lower for w in execute_words):
        return "execute_task"

    # Review -- asking for feedback on existing code
    review_words = [
        "review", "check", "look at", "granska", "feedback",
        "improve", "what do you think", "evaluate", "assess"
    ]
    if any(w in lower for w in review_words):
        return "review"

    # Test -- asking for verification
    test_words = ["test", "verify", "validate", "testa", "run it", "does it work"]
    if any(w in lower for w in test_words):
        return "test"

    # Plan -- asking for structure or approach
    plan_words = [
        "plan", "design", "architect", "structure",
        "how should", "approach", "outline", "breakdown"
    ]
    if any(w in lower for w in plan_words):
        return "plan"

    # Question -- ends with ? or starts with a question word
    question_words = ["what", "how", "why", "when", "where", "which", "who", "can you", "could you"]
    if "?" in content or any(lower.startswith(w) for w in question_words):
        return "question"

    return "unknown"
