<!-- willow-addon
section: Finding things
line: Keeps your folder's search ready in one background process on this machine, so a hook's lookup answers in milliseconds instead of seconds.
source: bot
added: 2026-10-28
writes: to
network: none
tags: no-install, offline, writes-output, search, pile
-->
# pile-serve

A cold lookup reads the folder (or opens the store), counts it, and only then
answers; the counting is most of the time. `pile-serve` does it once and
keeps it, in one process that answers on a Unix socket.

    python adapters/stdlib/pile-serve/pile_serve.py serve --from FOLDER --to SOCKET
        [--store STORE] [--for SECONDS]
    python adapters/stdlib/pile-serve/pile_serve.py ask --at SOCKET
        [--rank kernel|pile-rank|rungs] [--top N] QUESTION...
    python adapters/stdlib/pile-serve/pile_serve.py stop --at SOCKET

`ask` answers as the rank it names: `kernel` (the kernel's own rank, the
default: a passage only when it holds half the question's words),
[pile-rank](../pile-rank/) (where to look), or [pile-rungs](../pile-rungs/)'
climb. On Hollis's folder (`demo/hollis`, 2,112 passages) a question takes
about 17 ms on the socket and 0.09 s for `ask` with Python's own start-up,
against 0.35 s for pile-rank cold.

## Never older than the folder

Before each answer it looks at the folder's files' sizes and modification
times. When one changed, was added or went, it reads the passages again,
from a [pile-store](../pile-store/) store while that still matches (its
SHA-256 check), else from the folder, and the answer's `reads` goes up by
one. An edit inside the file system's timestamp resolution that keeps a
file's size could be missed until the next one.

## Speaking to it

A request is one JSON line and so is its answer, so any program on this
machine can ask, a hook in any language included:

    {"question": "bass strings", "rank": "pile-rank", "top": 3}
    {"stop": true}

A bad request is answered `{"refused": "why"}` and the server goes on. One
connection is answered at a time; a client that says nothing for ten seconds
is let go.

## It ends

`stop`, SIGTERM and Ctrl-C each end it, and it removes its socket on the way
out. `--for SECONDS` also ends it after that long with no question, so a
server a hook started never lingers.

## What it reads and writes

The idea said it writes nothing, but binding a Unix socket makes a file, so
its card says `writes: to`: the socket, at `--to`, mode 600 so only you can
ask, and removed when it stops. It refuses a `--to` that is a file and not a
socket, and one where a server already answers; a socket a dead server left
is replaced. It writes no box and no store, reads no key, and reaches no
network: a Unix socket is this machine. Systems without Unix sockets are
refused.

Exit codes, the kernel's: `serve` and `stop` `0` when done; `ask` `0`
something was served, `42` nothing was; `2` refused (a bad command line, a
`--from` that is not a folder, a socket path over 100 bytes, or nothing
serving at `--at`).
