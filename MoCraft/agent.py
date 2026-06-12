import claude
from config_loader import AGENT_NAME, settings
from history import save_message, compact_if_needed
from subagent import SubAgent, run_parallel, split_task


_PARALLEL_KEYWORDS = [
    "use sub-agents", "use subagents", "spawn sub-agents",
    "in parallel", "simultaneously", "at the same time",
    "parallel agents",
]
_CODE_VERBS = ["write", "create", "build", "make", "implement", "add"]


def is_complex_task(content: str) -> bool:
    lower = content.lower()
    if any(kw in lower for kw in _PARALLEL_KEYWORDS):
        return True
    if len(content) < 80:
        return False
    has_code_verb = any(v in lower for v in _CODE_VERBS)
    many_ands     = lower.count(" and ") >= 2
    and_and_comma = lower.count(" and ") >= 1 and lower.count(",") >= 1
    return has_code_verb and (many_ands or and_and_comma)


def handle_task(content: str):
    save_message({"role": "user", "content": content})
    compact_if_needed()

    if not claude.check_budget():
        print("[QUIET] Token budget exhausted.")
        return

    # ── COMPLEX TASK → parallel sub-agents ──────────────────
    if is_complex_task(content):
        print("[MULTI-AGENT] Complex task — splitting into parallel subtasks...")
        subtasks = split_task(content)

        if len(subtasks) > 1:
            labels = " | ".join(f"#{i+1}: {t[:40]}" for i, t in enumerate(subtasks))
            print(f"[MULTI-AGENT] Spawning {len(subtasks)} sub-agents:\n  {labels}")
            results = run_parallel(subtasks)

            combined = "\n\n".join(
                f"Sub-agent {i+1} result:\n{r}" for i, r in sorted(results.items())
            )
            synthesis_prompt = (
                f"The original task was: '{content}'\n\n"
                f"Results from {len(subtasks)} parallel sub-agents:\n\n{combined}\n\n"
                f"Write a brief combined summary of what was accomplished."
            )
            reply = claude.ask_claude(synthesis_prompt, "SYSTEM")
            print(f"\n[RESULT]\n{reply}")
            save_message({"role": "assistant", "content": reply})
            return

    # ── SINGLE TASK → ReAct loop via SubAgent ────────────────
    # SubAgent uses the Anthropic tool-use API with a full think→tool→observe
    # loop, so it can call write_file, read_file, run_command, str_replace_file
    # and naturally decides when to call another tool vs yield back a final answer.
    print("[THINKING] Running single-agent ReAct loop...")
    result = SubAgent(content, 1).run()
    print(f"\n[RESULT]\n{result}")
    save_message({"role": "assistant", "content": result})


def handle_task_web(content: str, task_id: str, emit_fn):
    """
    Web API version of handle_task.
    Runs the same multi-agent logic but emits structured SSE events
    via emit_fn(event_type, data) instead of printing to stdout.
    """
    from events import set_emit
    set_emit(emit_fn)  # allows history.py to emit compact events on this thread

    save_message({"role": "user", "content": content})
    compact_if_needed()

    if not claude.check_budget():
        emit_fn("error", {"message": "Token budget exhausted."})
        return

    if is_complex_task(content):
        subtasks = split_task(content)
        if len(subtasks) > 1:
            emit_fn("subtasks", {"subtasks": subtasks})

            labels = " | ".join(f"#{i+1}: {t[:40]}" for i, t in enumerate(subtasks))
            print(f"[MULTI-AGENT] Spawning {len(subtasks)} sub-agents:\n  {labels}")

            results = run_parallel(subtasks, task_id=task_id, emit_fn=emit_fn)

            combined = "\n\n".join(
                f"Sub-agent {i+1} result:\n{r}" for i, r in sorted(results.items())
            )
            summary = claude.ask_claude(
                f"Task: '{content}'\n\nResults from {len(subtasks)} parallel agents:\n\n"
                f"{combined}\n\nWrite 2 sentences summarising what was built.",
                "SYSTEM",
            )
            emit_fn("complete", {"summary": summary})
            return

    # Single sub-agent
    emit_fn("subtasks", {"subtasks": [content]})
    print("[THINKING] Running single-agent ReAct loop (web)...")
    result = SubAgent(content, 1, task_id=task_id, emit_fn=emit_fn).run()
    emit_fn("complete", {"summary": result})
