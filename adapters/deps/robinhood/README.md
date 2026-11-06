<!-- willow-addon
section: Keeping track
line: Your Robinhood account as dated files: positions, orders, portfolio and watchlists, read through Robinhood's own MCP server and never traded on.
source: new
added: 2026-11-06
needs: mcp (Python SDK); MIT
floor: mcp 2.0.0; the rule names 0.9.1, its first release, but 2.x renamed the client's fields and its tests' stand-in server needs MCPServer, which arrived in 2.0.0
writes: to
network: agent.robinhood.com and Robinhood's sign-in, to read your account; this machine, for the sign-in's return
role: reads
reads: none
-->
# robinhood

A brokerage account forgets. It shows what you hold today, and an order
history that scrolls; what you held in March, and what the portfolio was
worth the week you stopped looking, are gone unless you kept them. This
keeps them: each run reads your Robinhood account through Robinhood's own
MCP server and writes what it said, dated, into a folder the kernel
searches. A day a week, a day a month: the folder becomes your account's
history, in your files.

    pip install -r adapters/deps/robinhood/requirements.txt
    python adapters/deps/robinhood/robinhood.py snapshot --to FOLDER [--quotes VTI,KR]
    python adapters/deps/robinhood/robinhood.py tools

**It never trades, and can't.** Robinhood's server has twelve tools, and
four of them act: two place and cancel orders, two change watchlists. This
add-on can call six, all read: `get_accounts`, `get_portfolio`,
`get_equity_positions`, `get_equity_orders`, `get_watchlists` and, with
`--quotes`, `get_equity_quotes`. There is no argument that names a tool,
so nothing on the command line reaches the others, and a tool on the list
that the server itself marks as changing something is skipped and said so.
willow decides nothing for you; an order is a decision. `tools` shows the
server's list with each marked `reads` or `never`.

**Signing in.** The first call opens Robinhood's own sign-in page in your
browser; you log in there, never here, and Robinhood sends you back to this
machine (127.0.0.1, port 8765 unless `--port` says) with a one-time code.
The token lives in this process and is gone when it ends: nothing about the
sign-in is kept, so each run signs in again. Robinhood's agent access is in
beta and opened from a desktop browser; its own pages say who can use it.

**What it writes,** under `--to`, one folder a day:

    FOLDER/2026-11-06/get_equity_positions.txt     the answer, as the json-paths reader writes it
    FOLDER/2026-11-06/.raw/get_equity_positions.json   the answer as it came (the kernel skips it)
    FOLDER/.robinhood.jsonl                        each write: time, tool, bytes, SHA-256

An account number is written as its last four digits (`****5678`), in both
forms. A tool that needs an account is asked once for each account
`get_accounts` names. A day already written is refused before anything is
asked: one snapshot a day, never overwritten. Point a box at the folder,
and every answer is a passage with its date; a [stack](../../stdlib/stack/)
of [timeline](../../stdlib/timeline/), [first-mention](../../stdlib/first-mention/)
and [readings](../../stdlib/readings/) reads your own history back:
[stack.md](stack.md) is one. Two days whose answer is the same, word for
word, are one passage to the kernel; the log keeps both.

**Its limits:** equities only, as Robinhood's server is at launch; the
answers are Robinhood's words and numbers, as it sent them, not checked,
and its numbers come bare ("1234.56"), so an add-on that looks for sums of
money (amounts) won't see them;
`--url` takes another address (https, or plain http on this machine only,
which its tests use), and nothing else about the server is assumed but the
tool names. Exit codes, the kernel's: 0 something written (or listed); 42
nothing on the list was offered, or the server answered none of it; 2
refused (a bad command line, an address that isn't https, a day already
written, the SDK not installed).
