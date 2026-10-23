"""The guard: every add-on held to its card's promises while its tests run.

Python loads `sitecustomize` at start-up from any folder on PYTHONPATH, so
with this folder there, every process an add-on's tests start, the tests
themselves and each script they run, carries one audit hook. It does
nothing unless WILLOW_GUARD_LOG names a file; `ci.py` sets both.

The hook sees each file opened for writing, made, removed or renamed, each
open of the key file, and each network connection or name lookup. It finds
whose code asked by walking the call stack to the first frame in the repo:

    an add-on's own code     judged against that add-on's card
    the kernel, called by    judged as that add-on writing through the
      an add-on's code       kernel
    a test, or anything      not judged: a test may build a folder or
      else in the repo         break a record on purpose

and an add-on is held to its card's header:

    network: none            no connection and no name lookup at all
    network: loopback        only this machine: localhost, 127.0.0.1, ::1
    network: (anything else) what it reaches and why; not narrowed further
    writes: nothing          writes no file, but in a scratch folder it
                             made itself with tempfile
    writes: record           may write the record, only through the kernel
    writes: to               writes only under the path given to --to
    writes: README.md        writes that one file of the repo; a pattern,
                             such as adapters/*/*/README.md, matches one
                             path segment per segment
                             (several, comma-separated)

and to the rules no card can loosen: it never changes an original (the
folder given to --from, or the pile of the box given to --box), never
writes a box but through the kernel, and never reads the key itself. No
add-on widens its own reach (CONSTITUTION.md, CONST-0-3 and CONST-III).

A breach raises PermissionError, so the add-on stops there, and is also
written to WILLOW_GUARD_LOG, so a breach the add-on catches and swallows is
still on the log. CI fails a run whose log isn't empty.

It sees what the tests run. A path an add-on's tests never take is a path
the guard never checks; that is the tests' coverage, and their job.
"""

from __future__ import annotations

import fnmatch
import json
import os
import sys
import threading

LOG = os.environ.get("WILLOW_GUARD_LOG", "")
ROOT = os.path.realpath(
    os.environ.get("WILLOW_GUARD_ROOT")
    or os.path.join(os.path.dirname(os.path.abspath(__file__)), *[os.pardir] * 4)
)
HERE = os.path.realpath(__file__)
KERNEL = os.path.join(ROOT, "kernel.py")
TEMPFILE = os.path.realpath(__import__("tempfile").__file__)
ADAPTERS = os.path.join(ROOT, "adapters")
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
WRITES = {"os.remove", "os.rename", "os.rmdir", "os.mkdir", "shutil.rmtree",
          "os.truncate", "os.chmod", "os.symlink", "os.link"}  # fmt: skip
NETWORK = {"socket.connect", "socket.sendto", "socket.getaddrinfo"}
LOOPBACK = {"localhost", "127.0.0.1", "::1"}

_busy = threading.local()
_kind: dict[str, tuple] = {}
_cards: dict[str, dict] = {}
_scratch: list[str] = []  # folders and files this process made with tempfile


def under(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def repo_file(rel: str, pattern: str) -> bool:
    """A path of the repo against a `writes` file or pattern, segment by
    segment: `*` never crosses a /."""
    got, want = rel.split(os.sep), pattern.split("/")
    return len(got) == len(want) and all(
        fnmatch.fnmatchcase(g, w) for g, w in zip(got, want)
    )


def real(path, dir_fd=None) -> str | None:
    """The full path an event names. `dir_fd`: a name relative to an open
    folder, as shutil.rmtree removes a tree; found through /proc where there
    is one, and not judged where there isn't."""
    if isinstance(path, int) or path is None:
        return None
    try:
        path = os.fsdecode(os.fspath(path))
    except TypeError:
        return None
    if isinstance(dir_fd, int) and not os.path.isabs(path):
        try:
            path = os.path.join(os.readlink(f"/proc/self/fd/{dir_fd}"), path)
        except OSError:
            return None
    return os.path.realpath(path)


def classify(filename: str) -> tuple:
    """("addon", name) | ("kernel",) | ("test",) | ("repo",) | ("outside",)"""
    got = _kind.get(filename)
    if got is None:
        path = os.path.realpath(filename)
        base = os.path.basename(path)
        if path == TEMPFILE:
            got = ("test",)  # tempfile's own probing for a writable folder
        elif path == HERE or not under(path, ROOT):
            got = ("outside",)
        elif path == KERNEL:
            got = ("kernel",)
        elif base.startswith("test_") or base == "conftest.py":
            got = ("test",)
        else:
            parts = os.path.relpath(path, ADAPTERS).split(os.sep)
            if len(parts) >= 3 and parts[0] in ("stdlib", "deps"):
                got = ("addon", f"{parts[0]}/{parts[1]}")
            else:
                got = ("repo",)
        _kind[filename] = got
    return got


def actor() -> tuple[str | None, bool]:
    """(the add-on whose code asked, or None; whether through the kernel)."""
    via_kernel = False
    try:
        frame = sys._getframe(2)
    except ValueError:  # at start-up the stack can be shallower than that
        return None, False
    while frame is not None:
        got = classify(frame.f_code.co_filename)
        if got[0] == "addon":
            return got[1], via_kernel
        if got[0] == "kernel":
            via_kernel = True
        elif got[0] in ("test", "repo"):
            return None, via_kernel
        frame = frame.f_back
    return None, via_kernel


def card(addon: str) -> dict:
    """The header fields of an add-on's card, read once."""
    if addon not in _cards:
        fields = {}
        try:
            with open(
                os.path.join(ADAPTERS, addon, "README.md"), encoding="utf-8"
            ) as f:
                head = f.read().split("-->")[0]
        except OSError:
            head = ""
        for line in head.splitlines()[1:]:
            key, sep, value = line.partition(":")
            if sep:
                fields[key.strip()] = value.strip()
        _cards[addon] = fields
    return _cards[addon]


def argv(flag: str) -> str | None:
    args = sys.argv
    for i, a in enumerate(args[:-1]):
        if a == flag:
            return os.path.realpath(args[i + 1])
    return None


def box_of(path: str) -> str | None:
    """The box a path is in: the nearest folder above it with kernel.json."""
    d = path if os.path.isdir(path) else os.path.dirname(path)
    while True:
        if os.path.isfile(os.path.join(d, "kernel.json")):
            return d
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up


def box_fields(box: str | None) -> dict:
    if not box:
        return {}
    try:
        with open(os.path.join(box, "kernel.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def originals() -> list[str]:
    out = [p for p in (argv("--from"),) if p]
    pile = box_fields(argv("--box")).get("pile")
    if pile:
        out.append(os.path.realpath(pile))
    return out


def breach(addon: str, what: str) -> None:
    line = f"{addon}: {what}"
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    finally:
        raise PermissionError(f"willow guard: {line}")


def judge_write(addon: str, via_kernel: bool, path: str) -> None:
    writes = {w.strip() for w in card(addon).get("writes", "").split(",") if w.strip()}
    for root in originals():
        if under(path, root):
            breach(addon, f"changed an original, {path}")
    box = box_of(path)
    if box or os.path.basename(path) == "kernel.json":
        if not via_kernel:
            breach(addon, f"wrote the box itself, not through the kernel: {path}")
        if "record" not in writes:
            breach(addon, f"wrote the record; its card says writes: {', '.join(sorted(writes)) or 'nothing'}")  # fmt: skip
        return
    if via_kernel:
        return
    to = argv("--to")
    if to and under(path, to):
        if "to" in writes:
            return
        breach(addon, f"wrote {path} under --to; its card says writes: {', '.join(sorted(writes)) or 'nothing'}")  # fmt: skip
    if under(path, ROOT) and any(
        repo_file(os.path.relpath(path, ROOT), w) for w in writes
    ):
        return
    if any(under(path, s) for s in _scratch):
        return  # its own scratch, made with tempfile
    breach(addon, f"wrote {path}; its card says writes: {', '.join(sorted(writes)) or 'nothing'}")  # fmt: skip


def judge_read(addon: str, via_kernel: bool, path: str) -> None:
    if via_kernel:
        return
    key = box_fields(argv("--box") or box_of(path)).get("key")
    if key and os.path.realpath(key) == path:
        breach(addon, f"read the key itself: {path}")


def hook(event: str, args: tuple) -> None:
    if getattr(_busy, "on", False):
        return
    if event in ("tempfile.mkdtemp", "tempfile.mkstemp"):
        _scratch.append(os.path.realpath(args[0]))
        return
    if event != "open" and event not in WRITES and event not in NETWORK:
        return
    _busy.on = True
    try:
        addon, via_kernel = actor()
        if addon is None:
            return
        if event in NETWORK:
            if event != "socket.getaddrinfo":
                sock = args[0]
                if getattr(sock, "family", None) == getattr(os, "AF_UNIX", object()):
                    return
            network = card(addon).get("network", "none")
            if network == "none":
                breach(addon, f"went online ({event}); its card says network: none")
            if network == "loopback":
                host = args[0] if event == "socket.getaddrinfo" else args[1]
                host = host[0] if isinstance(host, tuple) else host
                if isinstance(host, bytes):
                    host = host.decode("ascii", "replace")
                if host not in LOOPBACK:
                    breach(addon, f"reached {host!r} ({event}); its card says network: loopback")  # fmt: skip
            return
        if event == "open":
            path, mode, flags = args
            is_write = (
                any(c in mode for c in "wax+") if isinstance(mode, str)
                else bool((flags or 0) & WRITE_FLAGS)
            )  # fmt: skip
            path = real(path)
            if path is None:
                return
            (judge_write if is_write else judge_read)(addon, via_kernel, path)
            return
        if event == "os.rename":  # (src, dst, src_dir_fd, dst_dir_fd)
            paths = [real(args[0], args[2]), real(args[1], args[3])]
        elif event in ("os.link", "os.symlink"):
            paths = [real(args[0]), real(args[1])]
        elif event in ("os.remove", "os.rmdir"):  # (path, dir_fd)
            paths = [real(args[0], args[1])]
        elif event == "os.mkdir":  # (path, mode, dir_fd)
            paths = [real(args[0], args[2])]
        else:
            paths = [real(args[0])]
        for path in paths:
            if path is not None:
                judge_write(addon, via_kernel, path)
    finally:
        _busy.on = False


if LOG:
    sys.addaudithook(hook)
