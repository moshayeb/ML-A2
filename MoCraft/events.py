import threading

_local = threading.local()


def set_emit(fn):
    """Register an SSE emit function for the current thread."""
    _local.emit = fn


def set_task_dir(path: str):
    """Override the workspace directory for the current thread."""
    _local.task_dir = path


def get_task_dir():
    return getattr(_local, 'task_dir', None)


def emit_event(event_type: str, data: dict):
    fn = getattr(_local, 'emit', None)
    if fn:
        try:
            fn(event_type, data)
        except Exception:
            pass
