# ============================================================
# SUBAGENT — VG: Mo-Assistant Multi-Agent Extension
# ============================================================
# A SubAgent is a disposable mini-agent spawned for one task.
# It runs its own Claude ReAct loop (think → tool → observe →
# repeat) and returns a result when done or when budget is hit.
#
# The main agent (agent.py) can spawn several SubAgents at once
# using run_parallel(), which runs them all in separate threads
# so they work simultaneously instead of one after another.
#
# split_task() asks Claude to break a complex request into
# 2-3 independent subtasks before spawning the sub-agents.
#
# All sub-agents share the same token budget (claude.py's
# tokens_spent counter) — if one overshoots, the others stop.
# ============================================================

import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import claude
from config_loader import API_KEY, settings
from tools import write_file, read_file, run_command, str_replace_file

MAX_STEPS = 8

SUBAGENT_SYSTEM_PROMPT = (
    "You are a focused sub-agent. Your job is to complete one specific task "
    "using the available tools. Work step by step: think, call a tool, observe "
    "the result, then decide what to do next. When the task is fully done, write "
    "a short summary of what you accomplished — no tool call needed at that point. "
    "Never report fake output. Only describe what the tools actually returned. "
    "Never call the same tool with the same arguments twice in a row. "
    "For system queries (disk space, processes, environment info) use run_command "
    "with appropriate shell commands such as 'df -h', 'ps aux', or 'ls'."
)

TOOLS = [
    {
        "name": "write_file",
        "description": "Write content to a file in the shared workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Relative path inside workspace, e.g. project/main.py",
                },
                "content": {
                    "type": "string",
                    "description": "Full file content to write.",
                },
            },
            "required": ["filename", "content"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a file from the shared workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Relative path inside workspace.",
                },
            },
            "required": ["filename"],
        },
    },
    {
        "name": "run_command",
        "description": "Run a safe, non-destructive terminal command.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute.",
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "str_replace_file",
        "description": (
            "Partially edit a file by replacing the first occurrence of old_str "
            "with new_str. Use this instead of write_file when you only need to "
            "change part of a file."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "old_str": {
                    "type": "string",
                    "description": "Exact string to find and replace.",
                },
                "new_str": {
                    "type": "string",
                    "description": "Replacement string.",
                },
            },
            "required": ["filename", "old_str", "new_str"],
        },
    },
]


def _first_input_value(inp: dict) -> str:
    if not inp:
        return ""
    return str(next(iter(inp.values())))[:60]


class SubAgent:
    """
    One disposable agent that handles a single subtask.

    Runs its own Claude loop with tool calls until:
      - Claude signals it is done (end_turn with no tool calls)
      - The shared token budget is exhausted
      - MAX_STEPS iterations are reached

    When task_id and emit_fn are provided (web mode), the agent
    emits structured SSE events for live progress in the browser.
    """

    def __init__(self, task: str, agent_id: int, task_id: str = None, emit_fn=None):
        self.task     = task
        self.agent_id = agent_id
        self.task_id  = task_id
        self.emit_fn  = emit_fn
        self.messages = []

    # ── thread-local setup ───────────────────────────────────

    def _setup_thread(self):
        """Called at the start of run() to wire up events and workspace for this thread."""
        if not self.emit_fn:
            return
        from events import set_emit, set_task_dir
        set_emit(self.emit_fn)
        if self.task_id:
            task_dir = str(Path(__file__).parent / "workspace" / self.task_id)
            import os
            os.makedirs(task_dir, exist_ok=True)
            set_task_dir(task_dir)

    def _emit(self, event_type: str, data: dict):
        try:
            from events import emit_event
            emit_event(event_type, data)
        except ImportError:
            pass

    # ── public entry point ───────────────────────────────────

    def run(self) -> str:
        """Entry point — called directly or by run_parallel() in a thread."""
        self._setup_thread()
        self._emit("agent_start", {"agentId": self.agent_id, "task": self.task})
        print(f"[SUB-{self.agent_id}] Starting: {self.task[:70]}")
        self.messages = [{"role": "user", "content": self.task}]

        for step in range(MAX_STEPS):
            if not claude.check_budget():
                print(f"[SUB-{self.agent_id}] Budget exhausted at step {step}.")
                result = f"[Sub-agent {self.agent_id}] Stopped: token budget exhausted."
                self._emit("agent_done", {"agentId": self.agent_id, "result": result})
                return result

            response_data = self._call_claude()
            if response_data is None:
                result = f"[Sub-agent {self.agent_id}] API error — task incomplete."
                self._emit("agent_done", {"agentId": self.agent_id, "result": result})
                return result

            usage = response_data.get("usage", {})
            claude.update_tokens(
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
            )

            stop_reason    = response_data.get("stop_reason")
            content_blocks = response_data.get("content", [])

            text_parts = []
            tool_calls = []
            for block in content_blocks:
                if block["type"] == "text":
                    text_parts.append(block["text"])
                elif block["type"] == "tool_use":
                    tool_calls.append(block)

            self.messages.append({"role": "assistant", "content": content_blocks})

            if stop_reason == "end_turn" or not tool_calls:
                result = "\n".join(text_parts).strip() or "Task completed."
                print(f"[SUB-{self.agent_id}] Done in {step + 1} step(s): {result[:80]}")
                self._emit("agent_done", {"agentId": self.agent_id, "result": result})
                return result

            tool_results = []
            for tc in tool_calls:
                self._emit("tool_call", {
                    "agentId": self.agent_id,
                    "tool":    tc["name"],
                    "args":    tc["input"],
                })
                output = self._execute_tool(tc["name"], tc["input"])
                print(
                    f"[SUB-{self.agent_id}] {tc['name']}"
                    f"({list(tc['input'].keys())}) → {str(output)[:60]}"
                )
                self._emit("tool_result", {
                    "agentId": self.agent_id,
                    "tool":    tc["name"],
                    "result":  str(output)[:200],
                })
                tool_results.append({
                    "type":        "tool_result",
                    "tool_use_id": tc["id"],
                    "content":     str(output),
                })

            self.messages.append({"role": "user", "content": tool_results})

        result = (
            f"[Sub-agent {self.agent_id}] Reached max steps ({MAX_STEPS}) "
            f"— partial result may be in workspace."
        )
        self._emit("agent_done", {"agentId": self.agent_id, "result": result})
        return result

    # ── private helpers ──────────────────────────────────────

    def _call_claude(self):
        for attempt in range(3):
            try:
                resp = requests.post(
                    url="https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key":          API_KEY,
                        "anthropic-version":  "2023-06-01",
                        "content-type":       "application/json",
                    },
                    json={
                        "model":      settings["model"],
                        "max_tokens": settings["max_tokens"],
                        "system":     SUBAGENT_SYSTEM_PROMPT,
                        "tools":      TOOLS,
                        "messages":   self.messages,
                    },
                    timeout=60,
                )
            except requests.exceptions.RequestException as exc:
                print(f"[SUB-{self.agent_id}] Network error (attempt {attempt + 1}/3): {exc}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                return None

            try:
                data = resp.json()
            except Exception:
                print(f"[SUB-{self.agent_id}] JSON decode error (attempt {attempt + 1}/3)")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                return None
            if "error" in data:
                err_type = data.get("error", {}).get("type", "unknown")
                print(f"[SUB-{self.agent_id}] API error (attempt {attempt + 1}/3): HTTP {resp.status_code} — {err_type}")
                if err_type in ("rate_limit_error", "overloaded_error") and attempt < 2:
                    wait = 5 * (attempt + 1)
                    print(f"[SUB-{self.agent_id}] Retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                return None
            return data
        return None

    def _execute_tool(self, name: str, inp: dict) -> str:
        if name == "write_file":
            return str(write_file(inp["filename"], inp["content"]))
        if name == "read_file":
            return read_file(inp["filename"])
        if name == "run_command":
            return run_command(inp["command"])
        if name == "str_replace_file":
            return str_replace_file(inp["filename"], inp["old_str"], inp["new_str"])
        return f"[ERROR] Unknown tool: {name}"


# ── PUBLIC FUNCTIONS ─────────────────────────────────────────

def run_parallel(subtasks: list, task_id: str = None, emit_fn=None) -> dict:
    """
    Spawn one SubAgent per subtask and run them all concurrently.
    Returns a dict mapping index → result string.
    """
    max_workers = settings.get("max_subagents", 3)
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_idx = {
            pool.submit(SubAgent(task, i + 1, task_id, emit_fn).run): i
            for i, task in enumerate(subtasks)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as exc:
                results[idx] = f"[Sub-agent {idx + 1} crashed: {exc}]"

    return results


def split_task(task_description: str) -> list:
    """
    Ask Claude to break a complex task into 2-3 independent subtasks.
    Falls back to [task_description] if splitting fails.
    """
    try:
        resp = requests.post(
            url="https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":      settings["model"],
                "max_tokens": 200,
                "system": (
                    "You split software development tasks into exactly 2 or 3 independent parts "
                    "that can be built in parallel by separate agents. ALWAYS return 2 or 3 parts, "
                    "never 1. Reply with ONLY a JSON array of strings. "
                    'Example: ["Write the game logic and movement", "Write the rendering and UI", '
                    '"Write the score tracking and file saving"]. Each part must be self-contained.'
                ),
                "messages": [{
                    "role": "user",
                    "content": (
                        f"Split this coding task into 2-3 independent parallel subtasks. "
                        f"Always return at least 2 parts:\n\n{task_description}"
                    ),
                }],
            },
            timeout=30,
        )
        try:
            data = resp.json()
        except Exception:
            return [task_description]
        if "error" in data or "content" not in data:
            return [task_description]

        usage = data.get("usage", {})
        claude.update_tokens(
            usage.get("input_tokens", 0),
            usage.get("output_tokens", 0),
        )

        raw = data["content"][0]["text"].strip()
        if "```" in raw:
            import re as _re
            m = _re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
            if m:
                raw = m.group(1).strip()
        subtasks = json.loads(raw)
        if isinstance(subtasks, list) and all(isinstance(s, str) for s in subtasks):
            return subtasks[:3]

    except Exception as exc:
        print(f"[SPLIT] Task splitting failed ({exc}), treating as single task.")

    return [task_description]
