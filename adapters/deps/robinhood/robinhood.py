"""robinhood.py: your Robinhood account as dated files, read through
Robinhood's own MCP server and never traded on. Python 3.10+.

    python adapters/deps/robinhood/robinhood.py snapshot --to FOLDER [--quotes SYM,SYM]
        [--url URL] [--port N] [--now ISO]
    python adapters/deps/robinhood/robinhood.py tools [--url URL] [--port N]

`snapshot` signs in through Robinhood's own page (it opens in your browser;
you log in there, never here), asks the server's read tools for your
accounts, portfolio, positions, order history and watchlists, and with
--quotes the quotes for those symbols, and writes each answer under
FOLDER/<date>/ as text the kernel searches (TOOL.txt, the json-paths
reader's form) with the answer as it came beside it (.raw/TOOL.json, which
the kernel skips). Each write is a line in FOLDER/.robinhood.jsonl: the
time, the tool, its bytes and SHA-256. A day already written is refused,
never overwritten: one snapshot a day, kept.

It can call six tools and no others: get_accounts, get_portfolio,
get_equity_positions, get_equity_orders, get_watchlists and
get_equity_quotes. The server has tools that place and cancel orders and
change watchlists; there is no argument that names a tool, so none of them
can be reached from here, and a tool on the list that the server marks as
changing anything is skipped and said so. willow decides nothing for you,
and an order is a decision.

An account number is written as its last four digits only. Nothing about
the sign-in is kept: the token lives in this process and is gone when it
ends, so each run signs in again. --url is Robinhood's address unless you
say; anything but https is refused except on this machine (for tests).

`tools` lists what the server offers and which of it this add-on would
call. Exit codes, the kernel's: 0 something written (or listed); 42 nothing
the server offers was on the list, or it answered nothing; 2 refused.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parents[1] / "stdlib" / "json-paths"))
import json_paths  # noqa: E402
import kernel  # noqa: E402

URL = "https://agent.robinhood.com/mcp/trading"
PORT = 8765  # where the sign-in returns, on this machine only
LOG = ".robinhood.jsonl"
INSTALL = "pip install -r adapters/deps/robinhood/requirements.txt"
#: The only tools this add-on can call, in the order it calls them.
READ = (
    "get_accounts",
    "get_portfolio",
    "get_equity_positions",
    "get_equity_orders",
    "get_watchlists",
    "get_equity_quotes",
)
ACCOUNT_KEY = re.compile(r"account.?(number|num|no)$|^acct", re.I)
USAGE = (
    "usage: robinhood.py snapshot --to FOLDER [--quotes SYM,SYM] [--url URL] [--port N] [--now ISO]\n"
    "       robinhood.py tools [--url URL] [--port N]\n"
    "  your Robinhood account as dated files, read only"
)


def allowed_url(url: str) -> bool:
    """https anywhere; plain http only on this machine, where tests run."""
    p = urllib.parse.urlsplit(url)
    local = (p.hostname or "") in ("127.0.0.1", "localhost", "::1")
    return p.scheme == "https" or (p.scheme == "http" and local)


def changes_things(tool) -> bool:
    """True when the server says a tool on the list isn't read-only."""
    a = getattr(tool, "annotations", None)
    if a is None:
        return False
    return a.read_only_hint is False or bool(a.destructive_hint)


def mask(node: object) -> object:
    """Every account number as its last four digits, wherever it sits."""
    if isinstance(node, dict):
        return {
            k: (
                last_four(v)
                if ACCOUNT_KEY.search(str(k)) and isinstance(v, (str, int))
                else mask(v)
            )
            for k, v in node.items()
        }
    if isinstance(node, list):
        return [mask(v) for v in node]
    return node


def last_four(v: object) -> str:
    s = str(v)
    return "****" + s[-4:] if len(s) > 4 else "****"


def answer(result) -> object | None:
    """A tool's answer as data: its structured content, else its text, read
    as JSON when it is JSON. None for an error or nothing."""
    if result.is_error:
        return None
    if result.structured_content is not None:
        return result.structured_content
    texts = [c.text for c in result.content if getattr(c, "type", "") == "text"]
    if not texts:
        return None
    text = "\n".join(texts)
    try:
        return json.loads(text)
    except ValueError:
        return text


def required(tool) -> list[str]:
    schema = tool.input_schema or {}
    return list(schema.get("required") or [])


def accounts_of(found: object) -> dict[str, list]:
    """Each account-ish key in get_accounts' answer, with every value it holds,
    so a tool that needs an account can be asked once for each."""
    keys: dict[str, list] = {}

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if re.search(r"account", str(k), re.I) and isinstance(v, (str, int)):
                    keys.setdefault(str(k), []).append(v)
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(found)
    return keys


def calls(tool, accounts: dict[str, list], quotes: list[str]) -> list[dict] | str:
    """The argument sets to ask a tool with, or why it can't be asked."""
    need = required(tool)
    if not need:
        return (
            [{"symbols": quotes}]
            if tool.name == "get_equity_quotes" and quotes
            else [{}]
        )
    if tool.name == "get_equity_quotes":
        if not quotes:
            return "no --quotes given"
        key = next((k for k in need if re.search(r"symbol", k, re.I)), None)
        return [{key: quotes}] if key and len(need) == 1 else f"needs {', '.join(need)}"
    if len(need) == 1 and need[0] in accounts:
        return [{need[0]: v} for v in dict.fromkeys(accounts[need[0]])]
    return f"needs {', '.join(need)}"


def return_server(port: int):
    """A one-shot server on this machine for the sign-in's return: (thread, box)."""
    got: dict = {}

    class Back(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"Signed in. You can close this tab; willow has what it needs."
            )

        def log_message(self, *a):  # quiet
            pass

    httpd = HTTPServer(("127.0.0.1", port), Back)
    thread = threading.Thread(target=httpd.handle_request, daemon=True)
    return httpd, thread, got


def provider(url: str, port: int):
    """Robinhood's OAuth, kept in memory only."""
    import anyio
    from mcp.client.auth import OAuthClientProvider, TokenStorage
    from mcp.shared.auth import AuthorizationCodeResult, OAuthClientMetadata

    class Memory(TokenStorage):
        def __init__(self):
            self.tokens = self.client = None

        async def get_tokens(self):
            return self.tokens

        async def set_tokens(self, tokens):
            self.tokens = tokens

        async def get_client_info(self):
            return self.client

        async def set_client_info(self, info):
            self.client = info

    redirect = f"http://127.0.0.1:{port}/callback"

    async def go(auth_url: str) -> None:
        print(f"Sign in to Robinhood in your browser:\n  {auth_url}", file=sys.stderr)
        webbrowser.open(auth_url)

    async def back() -> AuthorizationCodeResult:
        httpd, thread, got = return_server(port)
        thread.start()
        await anyio.to_thread.run_sync(thread.join)
        httpd.server_close()
        return AuthorizationCodeResult(code=got.get("code", ""), state=got.get("state"))

    meta = OAuthClientMetadata(
        client_name="willow (read-only)",
        redirect_uris=[redirect],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        token_endpoint_auth_method="none",
    )
    return OAuthClientProvider(url, meta, Memory(), go, back)


async def session_run(url: str, port: int, work):
    from mcp import ClientSession
    from mcp.client.streamable_http import (
        create_mcp_http_client,
        streamable_http_client,
    )

    async with create_mcp_http_client(auth=provider(url, port)) as http:
        async with streamable_http_client(url, http_client=http) as (read, write):
            async with ClientSession(read, write) as s:
                await s.initialize()
                return await work(s)


def on_list(tools) -> tuple[list, list[str]]:
    """The listed tools this add-on would call, in READ's order, and why any
    of READ is left out."""
    by = {t.name: t for t in tools}
    use, why = [], []
    for name in READ:
        t = by.get(name)
        if t is None:
            why.append(f"{name}: not offered by this server")
        elif changes_things(t):
            why.append(f"{name}: skipped, the server marks it as changing something")
        else:
            use.append(t)
    return use, why


async def take(s, quotes: list[str]) -> tuple[dict[str, list], list[str]]:
    """Each allowed tool's answers, and what was skipped and why."""
    listed = (await s.list_tools()).tools
    use, why = on_list(listed)
    got: dict[str, list] = {}
    accounts: dict[str, list] = {}
    for t in use:
        plan = calls(t, accounts, quotes)
        if isinstance(plan, str):
            why.append(f"{t.name}: {plan}")
            continue
        for args in plan:
            if t.name not in READ:  # never reached: READ is the only list
                raise RuntimeError(t.name)
            found = answer(await s.call_tool(t.name, args))
            if found is not None:
                got.setdefault(t.name, []).append(found)
        if t.name == "get_accounts" and t.name in got:
            accounts = accounts_of(got[t.name])
    return got, why


def write(to: Path, day: str, now: str, got: dict[str, list]) -> list[str]:
    folder, raw = to / day, to / day / ".raw"
    raw.mkdir(parents=True)
    done = []
    with open(to / LOG, "a", encoding="utf-8", newline="\n") as log:
        for name, answers in got.items():
            data = mask(answers[0] if len(answers) == 1 else answers)
            body = (
                json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
            ).encode()
            (raw / f"{name}.json").write_bytes(body)
            text = json_paths.convert(body, f"{name}.json") or body.decode()
            (folder / f"{name}.txt").write_text(text, encoding="utf-8", newline="\n")
            log.write(json.dumps({"at": now, "tool": name, "file": f"{day}/{name}.txt",
                                  "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()},
                                 sort_keys=True) + "\n")  # fmt: skip
            done.append(f"{day}/{name}.txt")
    return done


def args(argv: list[str]) -> dict[str, str] | None:
    it, out = iter(argv[1:]), {"cmd": argv[0] if argv else ""}
    for a in it:
        if a not in ("--to", "--quotes", "--url", "--port", "--now"):
            return None
        out[a] = next(it, "")
    if out["cmd"] not in ("snapshot", "tools") or (out["cmd"] == "snapshot") != (
        "--to" in out
    ):
        return None
    if not out.get("--port", "1").isdigit():
        return None
    return out


def main(argv: list[str]) -> int:
    o = args(argv)
    if o is None:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    url, port = o.get("--url", URL), int(o.get("--port", PORT))
    if not allowed_url(url):
        print(
            f"refused: {url} is not https (plain http only on this machine)",
            file=sys.stderr,
        )
        return kernel.REFUSED
    now = o.get("--now") or dt.datetime.now(dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", now):
        print("refused: --now is YYYY-MM-DDTHH:MM:SSZ", file=sys.stderr)
        return kernel.REFUSED
    if o["cmd"] == "snapshot":
        to, day = Path(o["--to"]), now[:10]
        if (to / day).exists():
            print(
                f"refused: {to / day} is already written; one snapshot a day",
                file=sys.stderr,
            )
            return kernel.REFUSED
    try:
        import anyio
    except ImportError:
        print(f"refused: robinhood needs the mcp SDK: {INSTALL}", file=sys.stderr)
        return kernel.REFUSED
    quotes = [q.strip().upper() for q in o.get("--quotes", "").split(",") if q.strip()]

    if o["cmd"] == "tools":

        async def work(s):
            return (await s.list_tools()).tools

        listed = anyio.run(session_run, url, port, work)
        use, _ = on_list(listed)
        for t in listed:
            mark = "reads" if t in use else "never"
            print(f"  {mark}  {t.name}")
        return kernel.ALIVE if use else kernel.ESCALATE

    got, why = anyio.run(session_run, url, port, lambda s: take(s, quotes))
    for w in why:
        print(f"  {w}")
    if not got:
        print("Nothing to write: the server answered none of the read tools.")
        return kernel.ESCALATE
    for f in write(to, day, now, got):
        print(f"wrote {to / f}")
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
