# Mo-Assistant — Part 3: Multi-Agent Collaboration

A Python-based AI agent that joins a shared group chat hub, collaborates with other agents, answers software engineering questions, and writes real code files to a local workspace.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your API key
echo ANTHROPIC_API_KEY=your-key-here > .env

# 3. Run the agent
python main.py
```

---

## Project Structure

```
Part3/
├── main.py           Entry point — run this to start the agent
├── loop.py           Main while loop — polls the hub every 5 seconds
├── console.py        Background control thread — type commands while running
├── state.py          Shared runtime state (agent_running, last_message_time)
├── agent.py          Brain — decides when and how to respond
├── claude.py         Claude API communication and token tracking
├── hub.py            Group chat hub — send and receive messages
├── history.py        Chat memory — saves all messages, sends last N to Claude
├── tools.py          Workspace tools — write files, run safe commands
├── safety.py         Command safety checker — blocks dangerous operations
├── templates.py      Pre-written responses for common questions (saves tokens)
├── config_loader.py  Loads .env and config.json once; all modules import from here
├── config.json       Settings (model, budget, rate limit, agent name, hub URL)
├── .env              API key — never committed to git
├── logs/
│   └── chat_history.json   All messages saved to disk
└── workspace/        Files written by the agent go here
```

---

## How It Works

### 1. Startup
`main.py` calls `run()` in `loop.py`. The agent posts an online message to the hub and starts polling every 5 seconds.

### 2. Receiving Messages
`loop.py` fetches new messages from the hub using a `since` counter so it never re-reads old messages. Each message is passed to `handle_message()` in `agent.py`.

### 3. Deciding Whether to Respond
`should_respond()` in `agent.py` applies these rules in order:
1. Never reply to our own messages (prevents infinite loops)
2. Always reply if mentioned by name (`Mo-Assistant`)
3. Reply to broadcasts (`attention all agents`, `@everyone`)
4. Reply to humans asking engineering questions
5. Stay quiet for everything else

### 4. Templates First (Zero Tokens)
Before calling Claude, `handle_message()` checks if the message matches a pre-written template in `templates.py`. If it matches, the agent replies instantly — no API call, no token cost.

**Template categories:**
- Identity & status
- Hello world
- String operations (reverse, count, case)
- List operations (sort, remove duplicates, flatten)
- Dictionary operations
- File reading and writing
- Error handling (try/except)
- Functions and classes (OOP)
- Loops and comprehensions
- API requests
- Algorithms (fibonacci, factorial, binary search, sorting)

### 5. Asking Claude
If no template matches, the agent calls `ask_claude()` in `claude.py`. This sends:
- The last N messages as context (so Claude remembers what was discussed)
- The new message
- A system prompt defining Mo-Assistant's role and safety rules

### 6. Writing Files
If Claude responds with a JSON object like:
```json
{"type": "file", "filename": "sort.py", "content": "def sort_list(lst):\n    return sorted(lst)"}
```
The agent writes the file to the `workspace/` folder and posts a confirmation to the hub.

### 7. Rate Limiting
The agent enforces a minimum gap between replies (`rate_limit_seconds` in config). During a rate-limited period, messages are still saved to history but not replied to.

### 8. Console Control
A background thread lets you type commands while the agent runs:

| Command | Effect |
|---|---|
| `budget <n>` | Change the token budget |
| `rate <n>` | Change seconds between replies |
| `status` | Show token usage and current settings |
| `history` | Show how many messages are saved |
| `stop` | Shut down the agent gracefully |

---

## Configuration (`config.json`)

| Key | Default | Description |
|---|---|---|
| `model` | `claude-haiku-4-5-20251001` | Claude model to use |
| `max_tokens` | `500` | Max length of each Claude reply |
| `max_tokens_budget` | `10000` | Total token budget for the session |
| `rate_limit_seconds` | `5` | Minimum seconds between replies |
| `context_messages` | `15` | How many recent messages to send to Claude |
| `test_mode` | `false` | If `true`, uses fake messages and never touches the hub |
| `agent_name` | `Mo-Assistant` | The agent's name in the group chat |
| `hub` | `https://...` | URL of the shared class hub |

### Test Mode
Set `"test_mode": true` in `config.json` to run the agent safely without connecting to the real hub. It uses the fake messages defined in `hub.py` instead.

---

## Security

- **API key** is stored in `.env` and never hardcoded
- **Command execution** is filtered by `safety.py` — dangerous commands like `rm`, `del`, `shutdown`, pipes, and redirects are blocked
- **File writing** blocks path traversal — filenames with `/`, `\`, or `..` are rejected
- **System prompt** instructs Claude never to reveal credentials, file paths, or private configuration

---

## Module Dependency Map

```
main.py
  └── loop.py
        ├── state.py          (shared flags)
        ├── config_loader.py  (settings, agent name)
        ├── hub.py            (get_messages, post_message)
        ├── history.py        (save_message)
        ├── agent.py
        │     ├── state.py
        │     ├── claude.py   (ask_claude, check_budget)
        │     ├── hub.py      (post_message)
        │     ├── history.py  (save_message)
        │     ├── tools.py    (write_file)
        │     └── templates.py (find_template)
        └── console.py
              ├── state.py
              ├── claude.py   (tokens_spent)
              ├── config_loader.py
              └── history.py
```

---

## Dependencies

```
requests       HTTP calls to the Claude API and the hub
python-dotenv  Load API key from .env file
```

Install with:
```bash
pip install -r requirements.txt
```
