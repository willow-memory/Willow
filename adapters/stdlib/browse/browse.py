"""browse.py: your folder in your web browser, on this machine only. Python 3.9+.

    python adapters/stdlib/browse/browse.py --box DIR [--port N] [--lang de|es|fr|pt] [--no-open]
    python adapters/stdlib/browse/browse.py launcher --box DIR

A page to ask your folder questions, read the passages that answer them
(each with its file and line), see the suggestions waiting for you, and
approve one with a click. The front page is the digest add-on's: what's
waiting, what went stale, what's coming up. Nothing to install and no
commands to type once it's open. Stop it with Ctrl-C.

Asking is the kernel's own `bite`, and approving is its own `seal`, so
both are on the record exactly as if typed. With --lang, a question goes
through that language's words add-on first (words-de, for instance).

Who can reach it. It listens on 127.0.0.1, never on the network. Each
start makes a new secret: the link it prints (and opens) hands it to your
browser as a cookie no other site can send, and every request needs it,
and every form also carries it. A request naming another host is refused,
so a web page can't reach it by renaming itself as this machine (DNS
rebinding), and no page may frame it, so a button can't be laid over
another site's. It sends no scripts. Anything already running as you could
run `kernel.py seal` itself, so the page gives nothing on this machine more
reach than it had; what it keeps out is every website.

`launcher` prints a file to double-click instead of typing the command,
for macOS, Windows and Linux, and where to save it. It writes nothing.

Exit codes, the kernel's: 0 stopped cleanly, or the launcher printed; 2 a
bad command line, a box that isn't one, or a port that can't be had.
"""

from __future__ import annotations

import contextlib
import hmac
import html
import io
import json
import re
import secrets
import shlex
import socketserver
import subprocess
import sys
import types
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve()
STDLIB = HERE.parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

LANGS = ("de", "es", "fr", "pt")
COOKIE = "willow"
#: no scripts, no outside anything, never framed, forms only back here
CSP = ("default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; "
       "frame-ancestors 'none'; base-uri 'none'")  # fmt: skip
MAX_FORM = 64 * 1024


def sibling(folder: str, module: str):
    """Another add-on's module from its source, or None when it was deleted."""
    path = STDLIB / folder / f"{module}.py"
    if not path.is_file():
        return None
    mod = types.ModuleType(f"browse_{module}")
    mod.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


def call(*argv: str) -> tuple[int, str, str]:
    """A kernel verb, in this process: (exit code, what it printed, its errors)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = kernel.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


# ── the pages ────────────────────────────────────────────────────────────────
#: the canvas's own colours, type and corners (ui/page.html), so the two pages
#: read as one; a card here is laid out as a person reads it: what kind of
#: thing it is, the thing in a sentence, why, then what it stands on, folded
STYLE = """
:root { color-scheme: light dark; --bg: #eceee7; --side: #e2e5dc; --card: #f8f9f5;
        --fg: #23251f; --muted: #5f6458; --line: #cdd1c4; --accent: #45652a;
        --onacc: #f6f8f0; --accl: #dde7cc; --tag: #e2e5db;
        --mono: ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, monospace; }
@media (prefers-color-scheme: dark) {
  :root { --bg: #141712; --side: #181c16; --card: #1d221a; --fg: #e2e5da;
          --muted: #a0a795; --line: #353c2f; --accent: #a6c56f; --onacc: #16200d;
          --accl: #2a3620; --tag: #272d23; } }
* { box-sizing: border-box; }
body { margin: 0; font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
       color: var(--fg); background: var(--bg); }
nav { background: var(--side); border-bottom: 1px solid var(--line); padding: 10px 16px; }
nav a { margin-right: 16px; color: var(--fg); font-weight: 600; text-decoration: none; }
main { margin: 0 auto; max-width: 46rem; padding: 24px 16px 64px; }
h1 { font-size: 27px; line-height: 1.15; letter-spacing: -.02em; margin: 0 0 8px; }
h2 { font-size: 16px; font-weight: 650; margin: 28px 0 6px; }
a { color: var(--accent); }
form.ask { display: flex; gap: 8px; flex-wrap: wrap; margin: 16px 0; }
input[type=text] { flex: 1 1 16rem; font: inherit; padding: 8px 10px;
       border: 1px solid var(--line); border-radius: 4px; background: var(--card); color: inherit; }
button { font: inherit; font-weight: 600; padding: 7px 14px; border: 0; border-radius: 4px;
         background: var(--accent); color: var(--onacc); cursor: pointer; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 4px;
        padding: 12px 14px; margin: 10px 0; }
.card h2 { font-size: 18px; margin: 2px 0 6px; overflow-wrap: anywhere; }
.card p, .card ul { margin: 6px 0; } .card ul { padding-left: 1.2rem; }
.kick { font: 600 11px/1.3 var(--mono); text-transform: uppercase; letter-spacing: .09em;
        color: var(--muted); margin: 0 0 4px; }
.pill { display: inline-block; font: 12px/1.6 var(--mono); text-transform: none;
        letter-spacing: 0; padding: 0 7px; border-radius: 9px;
        background: var(--tag); color: var(--muted); margin-right: 4px; overflow-wrap: anywhere; }
.where { color: var(--muted); font: 13px/1.4 var(--mono); overflow-wrap: anywhere; }
.text { white-space: pre-wrap; overflow-wrap: anywhere; margin: 4px 0 0; }
.said { overflow-wrap: anywhere; }
details { margin: 8px 0; } summary { cursor: pointer; color: var(--muted); }
pre { white-space: pre-wrap; overflow-wrap: anywhere; font: 12px/1.5 var(--mono);
      background: var(--bg); border: 1px solid var(--line); border-radius: 4px; padding: 8px 10px; }
.muted { color: var(--muted); }
"""


def page(title: str, body: str) -> str:
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width, initial-scale=1">'
        f"<title>{esc(title)} · willow</title><style>{STYLE}</style></head><body>"
        '<nav><a href="/">Home</a><a href="/waiting">Waiting for you</a></nav>'
        f"<main><h1>{esc(title)}</h1>{body}</main></body></html>"
    )


def ask_form(token: str, value: str = "") -> str:
    return (
        '<form class=ask method=post action="/ask">'
        f'<input type=hidden name=token value="{esc(token)}">'
        f'<input type=text name=q value="{esc(value)}" aria-label="Your question" '
        'placeholder="Ask your folder, in your own words" autofocus required>'
        "<button>Ask</button></form>"
    )


_BOLD = re.compile(r"\*\*(.+?)\*\*")
_STEP = re.compile(r"^- \S+ -- ", re.M)


def rich(text: str) -> str:
    """Text a suggestion gave, as a person reads it: `# ` lines as headings,
    `- ` lines as a list, `**bold**` as bold, and every character escaped
    first, so nothing a suggestion says is ever markup of its own."""
    out: list[str] = []
    items: list[str] = []
    para: list[str] = []

    def close() -> None:
        if items:
            out.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
            items.clear()
        if para:
            out.append("<p class=said>" + " ".join(para) + "</p>")
            para.clear()

    for raw in text.splitlines():
        line = _BOLD.sub(r"<strong>\1</strong>", esc(raw.strip()))
        if line.startswith("- "):
            if para:
                close()
            items.append(line[2:])
        elif line.startswith("#"):
            close()
            out.append(f"<p class=said><strong>{line.lstrip('#').strip()}</strong></p>")
        elif not line:
            close()
        else:
            if items:
                close()
            para.append(line)
    close()
    return "".join(out)


def listed(names: list) -> str:
    """Names as a person lists them: a, b or c."""
    names = [str(n) for n in names]
    if len(names) < 2:
        return "".join(names)
    return ", ".join(names[:-1]) + " or " + names[-1]


def reading(prop: dict) -> tuple[str, str, str, str]:
    """A suggestion as (what kind of thing, its headline, its body, why), each
    already HTML. Told by the shape of what it holds, never by who made it: a
    choice is a JSON object saying which was chosen for a word and over what;
    a stack is a file of `- NAME -- ARGS` steps under a heading; anything else
    is an answer in words."""
    data = prop["data"]
    try:
        doc = json.loads(data)
    except ValueError:
        doc = None
    if (
        isinstance(doc, dict)
        and isinstance(doc.get("chose"), str)
        and isinstance(doc.get("word"), str)
        and isinstance(doc.get("over"), list)
    ):
        body = ""
        if doc["over"]:
            body += f"<p>Not {esc(listed(doc['over']))}.</p>"
        card = doc.get("card")
        if isinstance(card, dict) and isinstance(card.get("line"), str):
            body += f"<p class=muted>{esc(doc['chose'])}: {esc(card['line'])}</p>"
        why = (
            doc["why"]
            if isinstance(doc.get("why"), str) and doc["why"]
            else prop["claim"]
        )
        head = f"For \u201c{esc(doc['word'])}\u201d, use {esc(doc['chose'])}"
        return "choice", head, body, esc(why)
    if data.lstrip().startswith("# ") and _STEP.search(data):
        first, _, rest = data.lstrip().partition("\n")
        steps = "\n".join(ln for ln in rest.splitlines() if not ln.startswith("#"))
        return "stack", esc(first[2:].strip()), rich(steps), esc(prop["claim"])
    return "answer", "", rich(data), esc(prop["claim"])


def passage(where: str, text: str, note: str = "") -> str:
    note = f" <span class=muted>({esc(note)})</span>" if note else ""
    return (f'<div class=card><div class=where>{esc(where)}{note}</div>'
            f'<p class=text>{esc(text)}</p></div>')  # fmt: skip


class Willow:
    """The pages for one box, with this start's secret."""

    def __init__(self, box: Path, lang: str | None = None, token: str | None = None):
        self.box = box
        self.token = token or secrets.token_urlsafe(32)
        self.words = sibling(f"words-{lang}", f"words_{lang}") if lang else None
        if lang and self.words is None:
            raise ValueError(f"the words-{lang} add-on isn't here")

    def home(self) -> str:
        dg = sibling("digest", "digest")
        if dg is None:
            summary = "<p class=muted>The digest add-on isn't here, so there's no summary.</p>"
        else:
            doc = dg.digest(self.box, date.today())
            summary = (
                self.summary(doc)
                if "refused" not in doc
                else (f"<p>Your record doesn't check out: {esc(doc['refused'])}</p>")
            )
        return page("Your folder", ask_form(self.token) + summary)

    def summary(self, doc: dict) -> str:
        out = []
        n = len(doc["waiting"]["items"])
        out.append("<h2>Waiting for you</h2>")
        out.append(f'<p><a href="/waiting">{n} suggestion{"s" if n != 1 else ""} '
                   "waiting for your approval</a></p>" if n else
                   "<p class=muted>Nothing is waiting for your approval.</p>")  # fmt: skip
        out.append("<h2>Coming up</h2>")
        c = doc["coming"]
        if c["state"] == "unreachable":
            out.append(f"<p class=muted>Couldn't look: {esc(c['why'])}</p>")
        elif not c["items"]:
            out.append("<p class=muted>Nothing dated in the next two weeks.</p>")
        out += [passage(f"{i['date']} · {i['where']}", i["line"]) for i in c["items"]]
        s = doc["stale"]
        if s["state"] == "unreachable":
            out.append(
                f"<h2>Gone stale</h2><p class=muted>Couldn't look: {esc(s['why'])}</p>"
            )
        elif s["items"]:
            out.append(
                "<h2>Gone stale</h2><p>These approved answers' sources changed or went:</p>"
            )
            out += [
                passage(", ".join(g["was"] for g in e["gone"]), e["data"])
                for e in s["items"]
            ]
        return "".join(out)

    def ask(self, question: str) -> str:
        question = question.strip()
        asked = question
        if self.words is not None:
            asked = " ".join(self.words.kept(question))
        if not kernel.words(asked):
            return page("Ask", ask_form(self.token, question) +
                        "<p>Every word there is a common one. Name the thing you mean.</p>")  # fmt: skip
        code, said, err = call("bite", "--box", str(self.box), asked)
        body = ask_form(self.token, question)
        if code == kernel.REFUSED:
            return page(
                "Ask", body + f"<p>Couldn't ask: {esc(err.strip() or said.strip())}</p>"
            )
        doc = json.loads(said)
        if doc["state"] == "sealed":
            body += (
                "<h2>You approved this answer</h2><div class=card>"
                f"{rich(doc['answer'])}<p class=where>{esc(doc['by'])}</p></div>"
            )
        elif doc["state"] == "populated":
            body += "<h2>Your files say</h2>" + "".join(
                passage(
                    s["where"],
                    s["text"],
                    "only asks your question back" if s["echo"] else "",
                )
                for s in doc["served"]
            )
        else:
            body += "<h2>Nothing in your folder holds that</h2>"
            body += "".join(passage(s["where"], s["text"], "only asks your question back")
                            for s in doc["served"])  # fmt: skip
            for h in doc.get("look", []):
                tips = " · ".join(
                    esc(h[k]) for k in ("why", "where", "next") if h.get(k)
                )
                body += f"<p class=muted>{tips}</p>"
        return page("Ask", body)

    def waiting(self) -> str:
        rows, breaks = kernel.read(self.box / "record.jsonl")
        if breaks:
            return page(
                "Waiting for you",
                f"<p>Your record doesn't check out: {esc('; '.join(breaks))}</p>",
            )
        done = {**kernel.sealed(self.box, rows), **kernel.declined(self.box, rows)}
        subjects = [r["subject"] for r in rows if r["kind"] == "proposal"
                    and r.get("verdict") == "pass" and r["subject"] not in done]  # fmt: skip
        if not subjects:
            return page(
                "Waiting for you",
                "<p class=muted>Nothing is waiting for your approval.</p>",
            )
        pile = {
            c["id"]: c for c in kernel.chunks(Path(kernel.config(self.box)["pile"]))
        }
        n = len(subjects)
        body = [
            f"<p><strong>{n} waiting.</strong> Each was suggested by something you let "
            "ask your folder. Approving one makes it the answer to its question from "
            "now on.</p>"
        ]
        for subj in subjects:
            prop = json.loads((self.box / "proposals" / f"{subj[9:]}.json").read_text())
            cites = "".join(
                passage(f"{pile[c]['path']}:{pile[c]['line']}", pile[c]["text"])
                if c in pile
                else passage(c[:12], "This passage is no longer in your folder.")
                for c in prop["cites"]
            )
            kind, head, said, why = reading(prop)
            n = len(prop["cites"])
            stands = (
                f"<details><summary>It cites {n} passage{'s' if n != 1 else ''} "
                f"of your folder</summary>{cites}</details>"
                if n
                else "<p class=muted>It cites nothing from your folder.</p>"
            )
            exact = (
                "<details><summary>Exactly what you'd be approving</summary>"
                f"<pre>{esc(prop['data'])}</pre>"
                f"<p class=where>{esc(subj)}</p></details>"
            )
            body.append(
                f"<div class=card><p class=kick>A suggested {kind}"
                f" <span class=pill>{esc(prop['path'])}</span></p>"
                + (f"<h2>{head}</h2>" if head else "")
                + said
                + f"<p class=muted>Why: {why}</p>{stands}{exact}"
                '<form method=post action="/approve">'
                f'<input type=hidden name=token value="{esc(self.token)}">'
                f'<input type=hidden name=subject value="{esc(subj)}">'
                f"<button>Approve this {kind}</button></form></div>"
            )
        return page("Waiting for you", "".join(body))

    def approve(self, subject: str) -> str:
        code, said, err = call("seal", "--box", str(self.box), subject)
        if code != kernel.ALIVE:
            return page("Not approved", f"<p>{esc(err.strip() or said.strip())}</p>")
        return page("Approved", "<p>It's on your record, signed with your key, and it "
                    "answers its question from now on.</p>"
                    '<p><a href="/waiting">Back to what\'s waiting</a></p>')  # fmt: skip


# ── the server ───────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    willow: Willow
    hosts: frozenset

    def log_message(self, *args) -> None:  # the questions stay off the terminal
        pass

    def send(self, status: int, body: str = "", headers: dict | None = None) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        for k, v in {"Content-Type": "text/html; charset=utf-8",
                     "Content-Length": str(len(data)),
                     "Content-Security-Policy": CSP, "X-Frame-Options": "DENY",
                     "X-Content-Type-Options": "nosniff", "Referrer-Policy": "same-origin",
                     "Cache-Control": "no-store", **(headers or {})}.items():  # fmt: skip
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def refuse(self, why: str) -> None:
        self.send(403, page("Not allowed", f"<p>{esc(why)}</p><p>Open willow from the link "
                            "browse.py printed when it started.</p>"))  # fmt: skip

    def cookie(self) -> str:
        for part in self.headers.get("Cookie", "").split(";"):
            name, _, value = part.strip().partition("=")
            if name == COOKIE:
                return value
        return ""

    def allowed(self) -> bool:
        """This machine's name in Host, and this start's secret in the cookie."""
        if self.headers.get("Host", "") not in self.hosts:
            self.refuse("This page only answers to this machine's own address.")
            return False
        if not hmac.compare_digest(self.cookie(), self.willow.token):
            self.refuse("This browser hasn't been given this start's link.")
            return False
        return True

    def do_GET(self) -> None:  # noqa: N802 — http.server's name
        url = urlsplit(self.path)
        if url.path == "/start":
            if self.headers.get("Host", "") not in self.hosts:
                return self.refuse(
                    "This page only answers to this machine's own address."
                )
            given = parse_qs(url.query).get("key", [""])[0]
            if not hmac.compare_digest(given, self.willow.token):
                return self.refuse("That link is from another start, or was cut short.")
            return self.send(
                303,
                "",
                {
                    "Location": "/",
                    "Set-Cookie": f"{COOKIE}={self.willow.token}; HttpOnly; SameSite=Strict; Path=/",
                },
            )
        if not self.allowed():
            return None
        if url.path == "/":
            return self.send(200, self.willow.home())
        if url.path == "/waiting":
            return self.send(200, self.willow.waiting())
        return self.send(
            404, page("Not here", "<p>There's no page at that address.</p>")
        )

    def do_POST(self) -> None:  # noqa: N802
        if not self.allowed():
            return None
        origin = self.headers.get("Origin")
        if origin is not None and urlsplit(origin).netloc not in self.hosts:
            return self.refuse("A form from another site can't ask or approve here.")
        size = int(self.headers.get("Content-Length") or 0)
        if size > MAX_FORM:
            return self.send(413, page("Too long", "<p>That form was too long.</p>"))
        form = parse_qs(self.rfile.read(size).decode("utf-8", "replace"))
        if not hmac.compare_digest(form.get("token", [""])[0], self.willow.token):
            return self.refuse("That form wasn't made by this page.")
        url = urlsplit(self.path)
        if url.path == "/ask":
            return self.send(200, self.willow.ask(form.get("q", [""])[0]))
        if url.path == "/approve":
            return self.send(200, self.willow.approve(form.get("subject", [""])[0]))
        return self.send(
            404, page("Not here", "<p>There's no page at that address.</p>")
        )


class Server(HTTPServer):
    def server_bind(self) -> None:
        # HTTPServer's own looks this machine's name up; nothing here needs it
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


def serve(willow: Willow, port: int = 0) -> Server:
    """A server for `willow` on 127.0.0.1, bound but not yet serving."""
    server = Server(("127.0.0.1", port), Handler)
    bound = server.server_address[1]
    handler = type(
        "BoundHandler",
        (Handler,),
        {
            "willow": willow,
            "hosts": frozenset({f"127.0.0.1:{bound}", f"localhost:{bound}"}),
        },
    )
    server.RequestHandlerClass = handler
    return server


# ── the launcher ─────────────────────────────────────────────────────────────
def launchers(box: Path, py: str) -> list[tuple[str, str, str]]:
    """(system, file name and where, its text) for each system."""
    argv = [py, str(HERE), "--box", str(box.resolve())]
    return [
        (
            "macOS",
            "willow.command, on your Desktop; then in Terminal once: "
            "chmod +x ~/Desktop/willow.command",
            f"#!/bin/sh\nexec {shlex.join(argv)}\n",
        ),
        (
            "Windows",
            "willow.bat, on your Desktop",
            f"@echo off\r\n{subprocess.list2cmdline(argv)}\r\n",
        ),
        (
            "Linux",
            "willow.desktop, in ~/.local/share/applications",
            "[Desktop Entry]\nType=Application\nName=willow\nTerminal=true\n"
            f"Exec={subprocess.list2cmdline(argv)}\n",
        ),
    ]


def launcher(box: Path) -> str:
    out = []
    for system, where, text in launchers(box, sys.executable or "python3"):
        out.append(f"{system}: save as {where}\n\n{text}")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if argv[:1] == ["launcher"]:
        if len(argv) != 3 or argv[1] != "--box":
            print(__doc__.split("\n\n")[1], file=sys.stderr)
            return kernel.REFUSED
        box = Path(argv[2])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        print(launcher(box), end="")
        return kernel.ALIVE
    opts, flags, rest, it = {}, set(), [], iter(argv)
    for a in it:
        if a in ("--box", "--port", "--lang"):
            opts[a] = next(it, "")
        elif a == "--no-open":
            flags.add(a)
        else:
            rest.append(a)
    port = opts.get("--port", "0")
    if (not opts.get("--box") or rest or not port.isdigit() or int(port) > 65535
            or opts.get("--lang", "de") not in LANGS):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    try:
        willow = Willow(box, opts.get("--lang"))
        server = serve(willow, int(port))
    except (OSError, ValueError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    link = f"http://127.0.0.1:{server.server_address[1]}/start?key={willow.token}"
    print(
        f"willow is open on this machine only:\n\n    {link}\n\nCtrl-C stops it.",
        flush=True,
    )
    if "--no-open" not in flags:
        webbrowser.open(link)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
