# MoCraft Web

A browser-based frontend for MoCraft — type a coding task, watch parallel AI
sub-agents build it live, then preview or download the generated files.

---

## What it does

- Splits your task into 2-3 independent subtasks using Claude
- Spawns one sub-agent per subtask — they run in parallel
- Streams live progress (agent status, tool calls, files written) via SSE
- Shows a live preview for HTML/JS apps inside the page
- Shows run instructions for Python apps
- Live token budget bar in the header (turns orange at 75%, red at 90%)
- Context compaction notifications in the activity log

All agent logic runs in **MoCraft's Python backend** (`server.py`). This
Node.js server only serves the HTML frontend and proxies API requests.

---

## How to run

Requires two terminals.

**Terminal 1 — MoCraft Python API:**
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

Open **http://localhost:3000** in your browser.

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `3000` | Port for this Node.js server |
| `MOCRAFT_HOST` | `localhost` | Host where MoCraft Python API runs |
| `MOCRAFT_PORT` | `8000` | Port where MoCraft Python API runs |

Copy `.env.example` to `.env` to override defaults.

---

## Project structure

```
mocraft-web/
├── server.js        Express server — static files + proxy to Python
├── public/
│   └── index.html   Single-page UI (vanilla JS, no framework)
├── .env.example     Environment variable template
└── package.json     Dependencies: express, dotenv
```

---

## API endpoints (proxied to MoCraft Python)

| Method | Path | Description |
|---|---|---|
| `POST` | `/task` | Submit a task, returns `{ taskId }` |
| `GET` | `/task/:id/stream` | SSE stream of live agent events |
| `GET` | `/status` | Current token budget status |
| `GET` | `/workspace?task=id` | List files generated for a task |
| `GET` | `/files/*` | Serve generated files statically |