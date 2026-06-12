# MoCraft — AI Coding Agent

A multi-agent AI system built by Mo Alshayeb. Type a coding task and MoCraft
automatically splits it into parallel subtasks, spawns one sub-agent per task,
runs a full ReAct loop (think → write file → run it → fix errors → repeat),
and returns working code.

---

## How to Run

### Option A — Terminal (CLI)

```bash
cd MoCraft
pip install -r requirements.txt
cp .env.example .env        # then add your ANTHROPIC_API_KEY to .env
python main.py
```

Commands while running:

| Input | Effect |
|-------|--------|
| Any text | Send a task to the agent |
| `status` | Show live token budget bar |
| `quit` | Exit |

---

### Option B — Web UI

Requires two terminals.

**Terminal 1 — Python API server:**
```bash
cd MoCraft
pip install -r requirements.txt
python server.py
# → http://localhost:8000
```

**Terminal 2 — Web frontend:**
```bash
cd mocraft-web
npm install
node server.js
# → http://localhost:3000
```

Open **http://localhost:3000** in your browser. Type a task, watch sub-agents
build it live, then download or preview the generated files.

---

### Option C — Docker

```bash
cd MoCraft
cp .env.example .env    # add your key
docker-compose up --build
```

---

## VG Features

### 1. Parallel Sub-Agents
When a task is complex, the main agent:
1. Detects complexity (`is_complex_task()` in `agent.py`)
2. Calls `split_task()` to break it into 2–3 independent subtasks using Claude
3. Spawns one `SubAgent` per subtask via `ThreadPoolExecutor` — they run simultaneously
4. Synthesises all results into one final reply

### 2. ReAct Loop (Reason + Act)
Each sub-agent runs its own Claude tool-use loop:
- **Think** — Claude decides what to do next
- **Call tool** — write_file, run_command, read_file, or str_replace_file
- **Observe** — feed the tool result back to Claude
- **Repeat** — until Claude signals it is done (`end_turn`, no tool calls)

### 3. Token Budget — Monitoring + Hard Cap
- Every API call (main agent and all sub-agents) is counted with a thread-safe lock
- **75%** of budget → `NOTICE` printed
- **90%** of budget → `WARNING` printed
- **100%** → `check_budget()` returns `False` — agent stops completely (hard cap)
- Type `status` at any time to see the live progress bar

### 4. Context Compaction
When the chat history exceeds `compaction_threshold` (default: 50 messages),
`compact_if_needed()` in `history.py` automatically:
- Summarises the oldest half of the history with one Claude call
- Replaces those messages with a single summary entry
- Keeps the most recent half intact

### 5. Safety — Harmful Command Blocking
`safety.py` blocks commands before they reach `subprocess`:
- Destructive commands: `rm`, `del`, `format`, `shutdown`, `rmdir`, `rd`
- Dangerous shell patterns: `&&`, `||`, `;`, `|`, `>`, `>>`, `<`, `$(`, backtick

### 6. Bash Execution
`run_command()` runs real shell commands via `subprocess`, filtered by the
safety checker. Output is capped at 500 characters to protect the token budget.
In web mode, commands run inside the per-task workspace directory.

### 7. Partial File Editing
`str_replace_file()` replaces the first occurrence of a string in a file.
Sub-agents use this to make targeted fixes without rewriting the whole file.

### 8. Web Dashboard
`mocraft-web/` is a Node.js frontend that connects to MoCraft's Python API:
- Live agent status cards (running / done)
- Real-time tool call and file logs
- File browser with syntax-highlighted previews
- Live iframe preview for HTML/JS apps
- Download button for all generated files

---

## Project Structure

```
MoCraft/
├── main.py            CLI entry point — task input, status command
├── server.py          HTTP API server (FastAPI + SSE) for the web UI
├── agent.py           Task routing — single agent or parallel sub-agents
├── subagent.py        SubAgent class + run_parallel() + split_task()
├── claude.py          Claude API wrapper + thread-safe token budget
├── history.py         Chat history persistence + context compaction
├── tools.py           write_file, read_file, run_command, str_replace_file
├── safety.py          Command safety filter
├── events.py          Thread-local SSE event system (web mode)
├── config_loader.py   Loads .env + config.json
├── config.json        Model, budget, thresholds
├── .env               Your API key — git-ignored
├── .env.example       Template — copy to .env and fill in key
├── Dockerfile         Builds the CLI agent as a container
├── docker-compose.yml Single-service compose (agent only)
└── requirements.txt   Python dependencies

mocraft-web/
├── server.js          Express server — serves HTML, proxies API to Python
├── public/
│   └── index.html     Single-page web UI
└── package.json       Node dependencies (express, dotenv)
```

---

## Configuration (`config.json`)

| Key | Default | Description |
|-----|---------|-------------|
| `model` | `claude-haiku-4-5-20251001` | Claude model for all calls |
| `max_tokens` | `2000` | Max tokens per API reply |
| `max_tokens_budget` | `100000` | Hard token cap for the session |
| `context_messages` | `15` | Recent messages sent to Claude as context |
| `max_subagents` | `3` | Max parallel sub-agents |
| `compaction_threshold` | `50` | History length before compaction triggers |

---

## Secrets & Security

- API key lives in `.env` only — never hardcoded, never committed to git
- `.gitignore` blocks `.env`, `logs/`, `workspace/`, and `node_modules/`
- `.env.example` shows required variables with placeholder values
- Docker passes the key at runtime via `env_file` — never baked into the image
- Workspace file operations block `..` path traversal attacks
