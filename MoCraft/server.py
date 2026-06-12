import sys
import io
import os
import json
import time
import threading
import queue
from pathlib import Path

try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True
        )
except Exception:
    pass

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

BASE_DIR  = Path(__file__).parent
WORKSPACE = BASE_DIR / "workspace"
WORKSPACE.mkdir(exist_ok=True)

app = FastAPI(title="MoCraft API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Per-task event queues (thread-safe): task_id → Queue
_queues: dict[str, queue.Queue] = {}


@app.post("/task")
async def submit_task(request: Request):
    body = await request.json()
    description = (body.get("description") or "").strip()
    if not description:
        return JSONResponse({"error": "No description provided."}, status_code=400)

    task_id = str(int(time.time() * 1000))
    q: queue.Queue = queue.Queue()
    _queues[task_id] = q

    def emit_fn(event_type: str, data: dict):
        q.put({"type": event_type, "data": data})

    def run():
        try:
            from agent import handle_task_web
            handle_task_web(description, task_id, emit_fn)
        except Exception as exc:
            q.put({"type": "error", "data": {"message": str(exc)}})
        finally:
            q.put(None)  # sentinel: tells the SSE stream to close

    threading.Thread(target=run, daemon=True).start()
    return JSONResponse({"taskId": task_id})


@app.get("/task/{task_id}/stream")
async def stream_task(task_id: str):
    q = _queues.get(task_id)
    if not q:
        return JSONResponse(
            {"error": "Task not found or already completed."},
            status_code=404,
        )

    async def generator():
        import asyncio
        loop = asyncio.get_running_loop()
        while True:
            try:
                event = await loop.run_in_executor(None, lambda: q.get(timeout=90))
            except queue.Empty:
                yield "event: ping\ndata: {}\n\n"
                continue
            if event is None:
                _queues.pop(task_id, None)
                break
            yield (
                f"event: {event['type']}\n"
                f"data: {json.dumps(event['data'], ensure_ascii=False)}\n\n"
            )

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "Connection":       "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/workspace")
def list_workspace(task: str = None):
    if task and (".." in task or task.startswith("/") or task.startswith("\\")):
        return []
    root = WORKSPACE / task if task else WORKSPACE

    def walk(d, base=""):
        out = []
        try:
            for entry in os.scandir(str(d)):
                rel = f"{base}/{entry.name}" if base else entry.name
                if entry.is_dir():
                    out.extend(walk(entry.path, rel))
                else:
                    out.append(rel)
        except OSError:
            pass
        return out

    return walk(root)


@app.get("/status")
def get_status():
    import claude
    from config_loader import settings
    budget = settings["max_tokens_budget"]
    spent  = claude.tokens_spent
    pct    = (spent / budget * 100) if budget else 0
    level  = "WARNING" if pct >= 90 else "NOTICE" if pct >= 75 else "OK"
    return {
        "spent":   spent,
        "budget":  budget,
        "percent": round(pct, 1),
        "level":   level,
    }


app.mount("/files", StaticFiles(directory=str(WORKSPACE)), name="files")


if __name__ == "__main__":
    print(f"[MOCRAFT] API server  → http://localhost:8000")
    print(f"[MOCRAFT] Workspace   → {WORKSPACE}")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
