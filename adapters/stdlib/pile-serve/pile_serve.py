"""pile_serve.py: the store held open by one process on this machine, over a
Unix socket, so a hook's lookup takes milliseconds instead of a cold start.
Python 3.9+, where the system has Unix sockets.

    python adapters/stdlib/pile-serve/pile_serve.py serve --from FOLDER --to SOCKET
        [--store STORE] [--for SECONDS]
    python adapters/stdlib/pile-serve/pile_serve.py ask --at SOCKET
        [--rank kernel|pile-rank|rungs] [--top N] QUESTION...
    python adapters/stdlib/pile-serve/pile_serve.py stop --at SOCKET

A cold lookup reads the folder (or opens the store), counts it, then answers;
the counting is most of the time. `serve` does that once and keeps it: the
passages, their dates, and pile-rank's counts, held in one process that
answers on a Unix socket only this user can open (mode 600).

Before each answer it looks at the folder's files' sizes and times; when one
changed, was added or went, it reads the passages again (from the store
while it matches, else the folder) and says so. So an answer is never older
than the folder it was asked of, except within a file system's timestamp
resolution.

`ask` sends one question and prints the answer, as the rank asked for
prints it: `kernel` (the kernel's own rank, which serves a passage only when
it holds half the question's words; the default), `pile-rank` (where to
look), or `rungs` (pile-rungs' climb). `stop` asks the server to stop, as
SIGTERM or Ctrl-C does; it removes its socket on the way out. With `--for`,
it also stops by itself once that many seconds pass with no question, so a
server a hook started never lingers.

A request is one JSON line, `{"question": ..., "rank": ..., "top": ...}` or
`{"stop": true}`, and the answer one JSON line; any program on this machine
may speak it. Only one connection is answered at a time.

`serve` writes only its socket, at `--to`, and removes it when it stops. It
refuses a `--to` that is there and is not a socket, and one where a server
already answers; a socket left by a server that died is replaced. It writes
no box, reads no key, and reaches no network: a Unix socket is this machine.
Exit codes, the kernel's: `serve` and `stop` 0 when done; `ask` 0 something
was served, 42 nothing was; 2 refused (a bad command line, a `--from` that
is not a folder, a SOCKET path too long, or nothing serving at `--at`).
"""

from __future__ import annotations

import json
import os
import signal
import socket
import stat
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "pile-rank"))
sys.path.insert(0, str(HERE.parent / "pile-rungs"))
import kernel  # noqa: E402
import pile_rank  # noqa: E402
import pile_rungs  # noqa: E402

RANKS = ("kernel", "pile-rank", "rungs")
LONGEST = 100  # bytes in a socket's path: macOS allows 104, Linux 108
WAIT = 10.0  # seconds a connection may take to send its line
BIG = 1 << 16  # bytes in a request, at most


def looks(folder: Path) -> tuple:
    """The folder's files by path, size and modification time: cheap to take,
    and different whenever a file is edited, added or removed."""
    out = []
    for p in sorted(folder.rglob("*")):
        rel = p.relative_to(folder)
        if any(part.startswith(".") for part in rel.parts):
            continue
        try:
            s = p.stat()
        except OSError:
            continue
        if stat.S_ISREG(s.st_mode):
            out.append((str(rel), s.st_size, s.st_mtime_ns))
    return tuple(out)


class Held:
    """The folder's passages and their counts, read again when it changes."""

    def __init__(self, folder: Path, store: Path | None):
        self.folder, self.store = folder, store
        self.seen: tuple | None = None
        self.reads = 0

    def fresh(self) -> None:
        now = looks(self.folder)
        if now == self.seen:
            return
        self.pile, self.where = pile_rank.passages(self.folder, self.store)
        self.dated = (
            (lambda p: [c["date"] for c in p]) if self.where == "store" else None
        )
        self.ranker = pile_rank.Ranker(self.pile)
        self.seen, self.reads = now, self.reads + 1

    def answer(self, question: str, rank: str, top: int) -> dict:
        self.fresh()
        base = {"question": question, "read_from": self.where, "reads": self.reads}
        if rank == "rungs":
            got, rungs, served = pile_rungs.climb(
                self.pile, question, top, self.dated, self.ranker
            )
            base.update(rung=got, rungs=rungs)
        elif rank == "pile-rank":
            served = self.ranker.rank(question, top)
        else:
            cs = kernel.rank(self.pile, question, top=top, dated=self.dated)
            served = [(c, None, []) for c in cs]
        rows = []
        for r, (c, s, ph) in enumerate(served, 1):
            row = {"rank": r, "where": f"{c['path']}:{c['line']}", "id": c["id"]}
            if s is not None:
                row["score"] = round(s, 4)
            rows.append({**row, "phrases": ph, "text": c["text"]})
        state = "populated" if rows else "empty"
        return {**base, "state": state, "ranked_by": rank, "served": rows}


def request(line: bytes) -> tuple[dict | None, str | None]:
    """A request read, or why it can't be."""
    try:
        req = json.loads(line)
    except ValueError:
        return None, "a request is one JSON line"
    if not isinstance(req, dict):
        return None, "a request is a JSON object"
    if req.get("stop") is True:
        return req, None
    q, rank, top = req.get("question"), req.get("rank", "kernel"), req.get("top", 5)
    if not isinstance(q, str) or not q.strip():
        return None, "a question is text"
    if rank not in RANKS:
        return None, f"a rank is one of {', '.join(RANKS)}"
    if isinstance(top, bool) or not isinstance(top, int) or top < 1:
        return None, "top is a whole number, 1 or more"
    return {"question": q, "rank": rank, "top": top}, None


def read_line(conn: socket.socket) -> bytes:
    buf = b""
    while b"\n" not in buf and len(buf) < BIG:
        got = conn.recv(4096)
        if not got:
            break
        buf += got
    return buf.split(b"\n", 1)[0]


def answers(at: str) -> bool:
    """Whether a server answers at `at` now."""
    s = socket.socket(socket.AF_UNIX)
    s.settimeout(2)
    try:
        s.connect(at)
        return True
    except OSError:
        return False
    finally:
        s.close()


def stopped(*_) -> None:
    raise KeyboardInterrupt  # SIGTERM stops it as Ctrl-C does: socket removed


def serve(folder: Path, at: str, store: Path | None, idle: float | None) -> int:
    held = Held(folder, store)
    held.fresh()  # counted before the socket opens: the first ask is warm too
    old = os.umask(0o177)  # the socket is this user's alone
    server = socket.socket(socket.AF_UNIX)
    try:
        server.bind(at)
    except OSError as e:  # another server took the address first
        print(f"refused: {at} could not be served: {e.strerror}", file=sys.stderr)
        server.close()
        return kernel.REFUSED
    finally:
        os.umask(old)
    server.listen()
    signal.signal(signal.SIGTERM, stopped)
    server.settimeout(idle)  # None: until stopped
    print(f"serving {len(held.pile)} passages of {folder} at {at}", flush=True)
    try:
        while True:
            try:
                conn, _ = server.accept()
            except (socket.timeout, BlockingIOError):
                break  # idle for --for seconds
            with conn:
                conn.settimeout(WAIT)
                try:
                    req, why = request(read_line(conn))
                    if req is not None and req.get("stop"):
                        conn.sendall(b'{"stopped": true}\n')
                        break
                    out = {"refused": why} if why else held.answer(**req)
                    conn.sendall(json.dumps(out, ensure_ascii=False).encode() + b"\n")
                except OSError:
                    continue  # a client gone or too slow: the next one is served
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        Path(at).unlink(missing_ok=True)
    print("stopped", flush=True)
    return kernel.ALIVE


def send(at: str, req: dict) -> dict | None:
    s = socket.socket(socket.AF_UNIX)
    s.settimeout(60)
    try:
        s.connect(at)
        s.sendall(json.dumps(req).encode() + b"\n")
        got = b""
        while not got.endswith(b"\n"):
            part = s.recv(1 << 16)
            if not part:
                break
            got += part
        return json.loads(got)
    except (OSError, ValueError):
        return None
    finally:
        s.close()


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("serve", "ask", "stop"):
        return usage()
    verb, opts, words = argv[0], {}, []
    it = iter(argv[1:])
    for a in it:
        if a in ("--from", "--to", "--store", "--for", "--at", "--rank", "--top"):
            opts[a] = next(it, "")
        elif a.startswith("--"):
            return usage()
        else:
            words.append(a)
    allowed = {
        "serve": {"--from", "--to", "--store", "--for"},
        "ask": {"--at", "--rank", "--top"},
        "stop": {"--at"},
    }[verb]
    need = {"serve": ("--from", "--to"), "ask": ("--at",), "stop": ("--at",)}[verb]
    if set(opts) - allowed or any(not opts.get(k) for k in need):
        return usage()
    if any(not v for v in opts.values()) or (words and verb != "ask"):
        return usage()
    if not hasattr(socket, "AF_UNIX"):
        print("refused: this system has no Unix sockets", file=sys.stderr)
        return kernel.REFUSED
    at = opts.get("--to") or opts["--at"]
    if len(os.fsencode(at)) > LONGEST:
        print(f"refused: a socket's path is at most {LONGEST} bytes; use a "
              "shorter one", file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    if verb == "serve":
        folder = Path(opts["--from"])
        if not folder.is_dir():
            print(f"refused: {opts['--from']} is not a folder", file=sys.stderr)
            return kernel.REFUSED
        if os.path.lexists(at):
            if not stat.S_ISSOCK(os.lstat(at).st_mode):
                print(f"refused: {at} is there and is not a socket; it is left "
                      "as it is", file=sys.stderr)  # fmt: skip
                return kernel.REFUSED
            if answers(at):
                print(f"refused: a server already answers at {at}", file=sys.stderr)
                return kernel.REFUSED
            os.remove(at)  # left by a server that died
        store = Path(opts["--store"]) if "--store" in opts else None
        try:
            idle = float(opts["--for"]) if "--for" in opts else None
        except ValueError:
            return usage()
        if idle is not None and not 0 <= idle < 1e9:
            return usage()
        return serve(folder.resolve(), at, store, idle)
    if verb == "stop":
        got = send(at, {"stop": True})
        if got is None:
            print(f"refused: nothing serves at {at}", file=sys.stderr)
            return kernel.REFUSED
        print("stopped")
        return kernel.ALIVE
    question = " ".join(words)
    try:
        top = int(opts.get("--top", "5"))
    except ValueError:
        return usage()
    rank = opts.get("--rank", "kernel")
    if not question.strip() or rank not in RANKS or top < 1:
        return usage()
    got = send(at, {"question": question, "rank": rank, "top": top})
    if got is None:
        print(f"refused: nothing serves at {at}", file=sys.stderr)
        return kernel.REFUSED
    if "refused" in got:
        print(f"refused: {got['refused']}", file=sys.stderr)
        return kernel.REFUSED
    print(json.dumps(got, ensure_ascii=False))
    return kernel.ALIVE if got["served"] else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
