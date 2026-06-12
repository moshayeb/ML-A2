import subprocess
import os
from safety import is_safe_command


WORKSPACE  = "workspace"
MAX_OUTPUT = 500

os.makedirs(WORKSPACE, exist_ok=True)


def _get_workspace():
    """Return the active workspace directory for the current thread."""
    try:
        from events import get_task_dir
        td = get_task_dir()
        if td:
            os.makedirs(td, exist_ok=True)
            return td
    except ImportError:
        pass
    return WORKSPACE


def run_command(command):
    """
    Run a terminal command safely.
    In web mode, runs from the per-task workspace directory.
    """
    if not is_safe_command(command):
        return f"[BLOCKED] Command not allowed: {command}"

    try:
        from events import get_task_dir
        cwd = get_task_dir() or None
    except ImportError:
        cwd = None

    result = subprocess.run(
        command, shell=True, capture_output=True, text=True,
        encoding="utf-8", errors="replace", cwd=cwd
    )
    output = result.stdout + result.stderr
    if len(output) > MAX_OUTPUT:
        output = output[:MAX_OUTPUT] + "\n[Output truncated at 500 characters]"
    return output


def write_file(filename, content):
    """
    Write a code file to the workspace.
    Emits a file_written event when running in web mode.
    """
    if ".." in filename or "\\" in filename:
        return f"[BLOCKED] Invalid filename: {filename}"

    parts = filename.replace("\\", "/").split("/")
    if len(parts) > 3:
        return f"[BLOCKED] Maximum two subfolder levels allowed: {filename}"

    workspace = _get_workspace()
    filepath  = os.path.join(workspace, *parts)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    try:
        from events import emit_event
        emit_event("file_written", {"filename": filename, "content": content})
    except ImportError:
        pass

    print(f"[FILE] Created: {filepath}")
    return filepath


def read_file(filename):
    """Read a file from the workspace."""
    if ".." in filename:
        return f"[BLOCKED] Invalid filename: {filename}"

    parts = filename.replace("\\", "/").split("/")
    if len(parts) > 3:
        return f"[BLOCKED] Maximum two subfolder levels allowed: {filename}"

    filepath = os.path.join(_get_workspace(), *parts)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > MAX_OUTPUT:
            content = content[:MAX_OUTPUT] + "\n[Content truncated at 500 characters]"
        return content
    except FileNotFoundError:
        return f"[ERROR] File not found: {filename}"


def str_replace_file(filename, old_str, new_str):
    """Replace the first occurrence of old_str with new_str in a workspace file."""
    if ".." in filename:
        return f"[BLOCKED] Invalid filename: {filename}"

    parts = filename.replace("\\", "/").split("/")
    if len(parts) > 3:
        return f"[BLOCKED] Maximum two subfolder levels allowed: {filename}"

    filepath = os.path.join(_get_workspace(), *parts)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return f"[ERROR] File not found: {filename}"

    if old_str not in content:
        return f"[ERROR] String not found in {filename}: '{old_str[:40]}'"

    new_content = content.replace(old_str, new_str, 1)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[FILE] Edited: {filepath}")
    return f"Replaced in {filename}"
