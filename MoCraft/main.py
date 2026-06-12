import sys
import io

try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True
        )
    else:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from agent import handle_task

def print_status():
    import claude
    from config_loader import settings
    budget  = settings["max_tokens_budget"]
    spent   = claude.tokens_spent
    pct     = (spent / budget * 100) if budget else 0
    bar_len = 30
    filled  = int(bar_len * pct / 100)
    bar     = "█" * filled + "░" * (bar_len - filled)
    color   = "WARNING" if pct >= 90 else "NOTICE" if pct >= 75 else "OK"
    print(f"\n[STATUS] Token budget: [{bar}] {pct:.1f}%")
    print(f"[STATUS] Spent: {spent:,} / {budget:,} tokens  ({color})")
    print(f"[STATUS] Model: {settings['model']}")
    print(f"[STATUS] Context window: last {settings['context_messages']} messages\n")

if __name__ == "__main__":
    print("[MOCRAFT] Ready. Commands: type a task, 'status', or 'quit'.")
    while True:
        try:
            task = input("\nTask> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[MOCRAFT] Goodbye.")
            break
        if not task:
            continue
        if task.lower() in ("quit", "exit", "q"):
            print("[MOCRAFT] Goodbye.")
            break
        if task.lower() == "status":
            print_status()
            continue
        handle_task(task)
