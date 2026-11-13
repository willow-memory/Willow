"""The run memory's reader: what a step reads, said to WILLOW_READ_LOG, one
line an event, and then the add-on guard, as it would have run.

The trace puts this folder first on PYTHONPATH for a step it may remember,
so Python loads this sitecustomize, not the guard's; this one loads the
guard's by its path, so the guard holds the step exactly as before. A child
Python the step starts gets both too (PYTHONPATH is passed on).

Each line is JSON: {"e": event, "p": path}, the path made absolute. The
events: open (a file opened to read), list (a folder listed: os.listdir,
os.scandir), sqlite (a database connected to), and run (a program started
that isn't this Python, whose reads can't be seen, so the step can't be
remembered). Nothing is said when WILLOW_READ_LOG is unset.
"""

import importlib.util
import json
import os
import sys

LOG = os.environ.get("WILLOW_READ_LOG", "")
ROOT = os.path.abspath(__file__)
for _ in range(5):  # memo, trace, pools, demo: the repository is five up
    ROOT = os.path.dirname(ROOT)
GUARD = os.path.join(ROOT, "adapters", "stdlib", "ci", "guard", "sitecustomize.py")
WRITE = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
_out = None
_busy = False


def _say(event: str, path) -> None:
    global _busy
    if _busy:
        return
    _busy = True
    try:
        if isinstance(path, int):
            return
        if isinstance(path, bytes):
            path = os.fsdecode(path)
        path = os.fspath(path) if event == "run" else os.path.abspath(os.fspath(path))
        if _out is None:
            return
        _out.write(json.dumps({"e": event, "p": path}) + "\n")
        _out.flush()
    except (OSError, TypeError, ValueError):
        pass
    finally:
        _busy = False


def _hook(event: str, args: tuple) -> None:
    if _busy:
        return
    if event == "open":
        path, mode, flags = args
        if path is None:
            return
        writes = (
            any(c in mode for c in "wax+")
            if isinstance(mode, str)
            else bool((flags or 0) & WRITE)
        )
        if not writes:
            _say("open", path)
    elif event in ("os.listdir", "os.scandir"):
        _say("list", args[0] if args and args[0] is not None else ".")
    elif event == "sqlite3.connect":
        _say("sqlite", args[0] if args else "")
    elif event == "subprocess.Popen":
        exe = args[0]
        if os.path.realpath(str(exe)) != os.path.realpath(sys.executable):
            _say("run", str(exe))
    elif event == "os.system":
        _say("run", "os.system")


if LOG:
    # opened now, before any add-on's code runs, so the guard never sees it
    # as the add-on's write; after this only write() is called, which no
    # audit event names
    _out = open(LOG, "a", encoding="utf-8")  # noqa: SIM115
    sys.addaudithook(_hook)
if os.path.isfile(GUARD):
    _spec = importlib.util.spec_from_file_location("willow_guard_sitecustomize", GUARD)
    _guard = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_guard)
