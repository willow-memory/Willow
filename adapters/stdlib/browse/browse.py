"""browse.py: your folder in your web browser, on this machine only. Python 3.9+.

    python adapters/stdlib/browse/browse.py --box DIR [--stack FILE] [--run FOLDER]
        [--index INDEX] [--beside INDEX ...] [--home FOLDER] [--boxes FILE] [--say MODEL] [--port N] [--lang de|es|fr|pt] [--no-open]
    python adapters/stdlib/browse/browse.py launcher --box DIR

A page to ask your folder questions, read the passages that answer them
(each with its file and line), see the suggestions waiting for you, and
approve one with a click. The front page is the digest add-on's: what's
waiting, what went stale, what's coming up. Nothing to install and no
commands to type once it's open. Stop it with Ctrl-C.

With --stack FILE (a stack file, as the stack add-on runs), a third page
shows what the stack's steps found: each step whose card says it prints a
report is run and drawn as a card, its one line, then its rows, where and
what. One way of drawing serves every report add-on, since they all print
the one shape. Steps that print something else are named and left to stack.

With --run FOLDER (a run the stack add-on kept with its --to), a page shows
that run and runs nothing: each step in the order it ran, whether it has
ended and how, a report step's report drawn from the data the run kept, any
other step's words. While the run is still going the page looks again every
few seconds, with no script: a step's lines appear as it prints them.

Every page is three panels: on the left the project and its sections (and
the run's steps); in the middle the section that is open; on the right,
when you click a file and line, the passage that is there. With --index
INDEX (scan's index, kept current by index-cache) a question is answered
from the index, the kernel's own answer without reading every file again,
and the page says which of your question's words no passage there holds.
With --beside INDEX, once for each, other piles' indexes are asked too
(the fair-merge add-on): what each holds is shown under your folder's
answer, apart from it, with the words each one lacks.
With --home FOLDER, the folder your projects are under, the left panel
lists them (the projects add-on) and a click opens another.
With --boxes FILE, a list of boxes kept somewhere else on this machine
(the boxes-here add-on's), the left panel lists those too, each with how
many suggestions wait on it, and a click opens one where it is. "Find
boxes in a folder" looks through a folder you name for boxes already
there, and the ones you tick are kept on the list. The list is written by
boxes-here, not by this page.

The middle is a stream: each question is added under the last, your line
plain and what the page says back marked as code's, one line made from
what the boxes under it hold. No model is asked. A question asked before
says when it was first asked. The stream is kept only while the page runs.

With --say MODEL (an Ollama tag on this machine, as the say add-on asks
it), a model also says each answer in a sentence of its own, under code's
line and marked with the model's name. The say-check add-on holds that
sentence to what code said: one that adds a word or a number is struck,
shown struck through with what failed, and code's line stands.

Asking is the kernel's own `bite`, and approving is its own `seal`, so
both are on the record exactly as if typed. With --run, a question is also
sent to the steps whose job it is (the look add-on): "who still owes me
money" shows what the run's debts and invoices steps found, above your
files' own passages. A question that finds nothing is given the why-not
add-on's reasons. With --lang, a question goes
through that language's words add-on first (words-de, for instance).

Who can reach it. It listens on 127.0.0.1, never on the network. Each
start makes a new secret: the link it prints (and opens) hands it to your
browser as a cookie no other site can send, and every request needs it,
and every form also carries it. A request naming another host is refused,
so a web page can't reach it by renaming itself as this machine (DNS
rebinding), and no page may frame it, so a button can't be laid over
another site's. It sends one script, its own file (page.js), and allows
no other: none from elsewhere, none written into a page. Anything already
running as you could
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
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

HERE = Path(__file__).resolve()
STDLIB = HERE.parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

LANGS = ("de", "es", "fr", "pt")
#: the page's one script, a file beside this one, sent as it is
SCRIPT = HERE.parent / "page.js"
COOKIE = "willow"
#: one script, the page's own file and never one written into a page; no
#: outside anything, never framed, forms and fetches only back here
CSP = ("default-src 'none'; style-src 'unsafe-inline'; script-src 'self'; connect-src 'self'; form-action 'self'; "
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


def report_of(folder: str, module: str, *argv: str) -> tuple[int, dict | None]:
    """A report add-on asked in this process: (its exit code, its report),
    the report None when the add-on isn't here or printed something else."""
    mod = sibling(folder, module)
    if mod is None:
        return 0, None
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = mod.main([*argv, "--json"])
    try:
        doc = json.loads(out.getvalue())
        [(r["where"], r["what"]) for g in doc["groups"] for r in g["rows"]]
        doc["addon"], doc["state"], doc["said"]
    except (ValueError, KeyError, TypeError):
        return code, None
    return code, doc


def indexed(box: Path, text: str, at: Path) -> dict | None:
    """The kernel's bite, answered from scan's index at `at` instead of a
    fresh read of the whole folder: the same row on the record and the same
    passages, since scan only narrows which ones the kernel's own `rank`
    looks at. None, and the kernel reads the folder as before, when scan or
    index-cache isn't here, the index isn't current for the box's folder by
    index-cache's manifest, or the box's words list can't be read (the
    kernel's bite then says why)."""
    cache, scan = sibling("index-cache", "index_cache"), sibling("scan", "scan")
    if cache is None or scan is None:
        return None
    cfg = kernel.config(box)
    alias, listed = {}, {}
    if "words" in cfg:  # asked with their words, as the kernel's bite asks
        alias, sha, why = kernel.read_words(Path(cfg["words"]), box)
        if why is not None:
            return None
        listed = {"words_sha256": sha}
    old = cache.cached(at)
    if old is None or old != cache.manifest(Path(cfg["pile"])):
        return None
    rows, breaks = kernel.read(box / "record.jsonl")
    k = kernel.bite_key(text)
    if breaks or k is None:
        return None  # the kernel's bite says why
    ts = kernel.now()
    for subj, row in kernel.sealed(box, rows).items():  # a sealed answer first
        prop, asked, why = kernel.standing(box, rows, subj, row)
        if why is None and asked == k:
            kernel.append(box, ts, "bite", bite_key=k, answered_by=subj, served=[])
            return {"state": "sealed", "answer": prop["data"], "by": subj}
    served = scan.Index(at).rank(text, alias, None)
    refs = [{"id": c["id"], "where": f"{c['path']}:{c['line']}",
             "echo": kernel.echo(text, c["text"])} for c in served]  # fmt: skip
    kernel.append(box, ts, "bite", bite_key=k, served=refs, **listed)
    return {"state": "populated" if refs else "empty", "bite_key": k,
            "served": [{**r, "text": c["text"]} for r, c in zip(refs, served)]}  # fmt: skip


def lacking(box: Path, text: str, at: Path) -> list[str]:
    """The question's words no passage of the index at `at` holds, each held
    as the kernel holds a word, with the box's words list; none when
    fair-merge or scan isn't here, or the index or the list can't be read."""
    fair = sibling("fair-merge", "fair_merge")
    if fair is None or sibling("scan", "scan") is None:
        return []
    cfg, alias = kernel.config(box), {}
    try:
        if "words" in cfg:
            alias, _, why = kernel.read_words(Path(cfg["words"]), box)
            if why is not None:
                return []
        return fair.from_index(at, text, alias or {})[1]
    except (OSError, ValueError):
        return []


def short(text: str, most: int = 200) -> str:
    """A text on one line, cut at a word when it runs long."""
    flat = " ".join(str(text).split())
    return flat if len(flat) <= most else flat[:most].rsplit(" ", 1)[0] + "…"


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
.shell { display: grid; grid-template-columns: 14rem minmax(0, 1fr); min-height: 100vh; }
.shell.open { grid-template-columns: 14rem minmax(0, 1fr) minmax(18rem, 34%); }
nav, aside { background: var(--side); position: sticky; top: 0; align-self: start;
       height: 100vh; overflow: auto; }
nav { border-right: 1px solid var(--line); padding: 14px 10px; }
nav a { display: block; padding: 5px 8px; border-radius: 4px; color: var(--fg);
       font-weight: 600; text-decoration: none; overflow-wrap: anywhere; }
nav a.on { background: var(--accl); }
nav a.sub { font-weight: 400; font-size: 14px; padding: 2px 8px 2px 20px; }
nav .proj { font: 600 11px/1.3 var(--mono); text-transform: uppercase; letter-spacing: .09em;
       color: var(--muted); margin: 0 8px 10px; overflow-wrap: anywhere; }
aside { display: none; border-left: 1px solid var(--line); padding: 16px 14px; }
.shell.open aside { display: block; }
aside .close { float: right; font-size: 14px; }
main { margin: 0 auto; width: 100%; max-width: 46rem; padding: 24px 16px 64px; }
.where a { color: inherit; text-decoration: none; }
.where a:hover { text-decoration: underline; }
.ln { font: 13px/1.5 var(--mono); white-space: pre-wrap; overflow-wrap: anywhere; }
.ln.at { background: var(--accl); }
.turn { margin: 14px 0; } .turn > summary { color: var(--fg); list-style: none; }
.turn > summary::-webkit-details-marker { display: none; }
.you { display: block; font-weight: 600; }
.stamp { font: 12px/1.4 var(--mono); color: var(--muted); font-weight: 400; margin-right: 6px; }
.say { display: block; border-left: 3px solid var(--accent); padding: 2px 0 2px 10px;
       margin: 4px 0 0; }
.by { font: 600 11px/1.3 var(--mono); text-transform: uppercase; letter-spacing: .09em;
      color: var(--muted); margin-right: 6px; }
.more > summary { color: var(--accent); }
.say.struck s { color: var(--muted); }
.say .why { display: block; font: 12px/1.5 var(--mono); color: var(--muted); }
form.switch { margin: 0; } .prow { display: flex; align-items: center; } .prow form:first-child { flex: 1; }
.prow button.tiny { border: 0; background: none; color: var(--muted); cursor: pointer; padding: 0 .5em; }
nav a.over { outline: 2px dashed var(--accent); } nav button.link { display: block; width: 100%; text-align: left;
      background: none; color: var(--fg); font-weight: 400; padding: 5px 8px; }
nav button.link:hover { background: var(--accl); }
@media (max-width: 820px) {
  .shell, .shell.open { grid-template-columns: 1fr; }
  nav, aside { position: static; height: auto; border: 0; border-bottom: 1px solid var(--line); } }
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
.pill.wait { background: var(--accl); color: var(--fg); }
.group { font-weight: 600; margin: 10px 0 2px; }
.row { display: grid; grid-template-columns: minmax(7rem, 38%) 1fr; gap: 10px;
       padding: 3px 0; border-top: 1px solid var(--line); }
.row .text { margin: 0; white-space: normal; }
"""


#: each section's page, by the title it is shown under
SECTIONS = {"Your folder": "/", "Ask": "/", "Waiting for you": "/waiting",
            "What your stack found": "/steps", "The run": "/run"}  # fmt: skip
#: the left panel of a page that has no box to speak of (a refusal)
BARE = '<a href="/">Ask</a><a href="/waiting">Waiting for you</a>'


def page(
    title: str, body: str, side: str = BARE, head: str = "", detail: str = ""
) -> str:
    """One page, three panels: `side` is the left one, where you are and
    what there is to open; the middle is the section that is open; `detail`
    is the right one, about one thing picked in the middle, and is out of
    sight while it is empty. `head` is for the head (the run's page asks to
    be looked at again). The one script, the page's own, fills the right
    panel without leaving the page; with no script every link still goes."""
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width, initial-scale=1">'
        f"{head}<title>{esc(title)} · willow</title><style>{STYLE}</style>"
        '<script src="/page.js" defer></script></head><body>'
        f"<div class='shell{' open' if detail else ''}'><nav>{side}</nav>"
        f"<main><h1>{esc(title)}</h1>{body}</main>"
        f"<aside id=detail>{detail}</aside></div></body></html>"
    )


#: a place: a file, then a line in it (the last thing said, after any date)
_PLACE = re.compile(r"\S.*:\d+")


def where_html(where: object) -> str:
    """A place as words, or as a link to what is there when it reads as a
    file and a line: the right panel shows it, or its own page with no script."""
    w = str(where)
    if not _PLACE.fullmatch(w):
        return esc(w)
    return f'<a data-place href="/place?at={quote(w, safe="")}">{esc(w)}</a>'


#: a report's state, the kernel's word, as a person says it
STATES = {
    "populated": "found",
    "empty": "nothing found",
    "unreachable": "couldn't look",
}
SHOWN = 8  # rows a card shows before the rest fold away


def rows_html(pairs: list[tuple[object, dict]]) -> str:
    """(group, row) pairs as rows under their group's name, each row where
    then what, a group's name said once above its first row."""
    out, last = [], object()
    for group, row in pairs:
        if group != last and group is not None:
            out.append(f"<p class=group>{esc(group)}</p>")
        last = group
        out.append(
            f"<div class=row><span class=where>{where_html(row['where'])}</span>"
            f"<p class=text>{esc(row['what'])}</p></div>"
        )
    return "".join(out)


def report_card(doc: dict, code: int = 0, shown: int = SHOWN, pills: str = "") -> str:
    """One report, any add-on's, as a card: whose it is and its state, the one
    thing it said, then its rows, the first few in sight and the rest folded.
    The shape is the report contract's (ci/README.md): `addon`, `state`,
    `said`, and `groups` of `rows`, each a `where` and a `what`. A report
    that found things and exited 42 waits on the person, and says so.
    `pills` is more to say beside its state, already HTML."""
    pairs = [(g["name"], r) for g in doc["groups"] for r in g["rows"]]
    state = STATES.get(doc["state"], str(doc["state"]))
    waits = code == kernel.ESCALATE and doc["state"] == "populated"
    head = (
        f"<p class=kick>{esc(doc['addon'])} <span class=pill>{esc(state)}</span>"
        + (" <span class='pill wait'>waits on you</span>" if waits else "")
        + f"{pills}</p><h2>{esc(doc['said'])}</h2>"
    )
    rest = ""
    if len(pairs) > shown:
        rest = (
            f"<details><summary>All {len(pairs)} rows</summary>"
            f"{rows_html(pairs[shown:])}</details>"
        )
    return f"<div class=card>{head}{rows_html(pairs[:shown])}{rest}</div>"


#: small talk, answered by code with one of its own few words: nothing is
#: asked of your folder, and nothing goes on the record
SMALL = {"hi": "Hello.", "hello": "Hello.", "morning": "Morning.",
         "good morning": "Morning.", "thanks": "Anytime.", "thank you": "Anytime.",
         "ok": "Got it.", "okay": "Got it."}  # fmt: skip
#: how many turns of a sitting the stream keeps for a box
KEPT = 50


def turn_html(at: str, you: str, say: str, again: str, boxes, opened: bool, model: str = "") -> str:  # fmt: skip
    """One turn of the stream. Your line is plain, as you typed it. What
    the page says back is marked as code's: its one line, then the boxes
    the line rests on, the first in sight and the rest behind "more?". A
    question asked before says when it was first asked. `boxes` is a list
    of boxes, or one already put together; a turn with no line of yours is
    the page's own opening."""
    boxes = [boxes] if isinstance(boxes, str) else list(boxes)
    yours = f"<span class=you><span class=stamp>{esc(at)}</span>{esc(you)}</span>" if you else ""  # fmt: skip
    noted = ""
    if again:
        noted = f" <span class=stamp>asked before: first on {esc(again[:10])} at {esc(again[11:16])}</span>"  # fmt: skip
    said = f"<span class=say><span class=by>willow · code</span>{esc(say)}{noted}</span>" if say else ""  # fmt: skip
    said += model  # a model's sentence about the same boxes, already HTML
    body = boxes[0] if boxes else ""
    if len(boxes) > 1:
        body += f"<details class=more><summary>more?</summary>{''.join(boxes[1:])}</details>"  # fmt: skip
    return (
        f"<details class=turn name=turn{' open' * opened}>"
        f"<summary>{yours}{said}</summary>{body}</details>"
    )


def model_html(got: dict) -> str:
    """A model's sentence about a turn's boxes, as the say add-on gave it:
    marked with the model's name, never as code's. One that held to the
    boxes stands, its tags taken out for reading. One that failed a check
    is struck through, with what failed, and code's line above it stands.
    A model that couldn't be asked is said in a word."""
    by = f"<span class=by>willow · {esc(got.get('model', 'a model'))}</span>"
    if got["state"] != "populated":
        return f"<span class='say struck'>{by}<span class=why>not asked: {esc(got['why'])}</span></span>"  # fmt: skip
    plain = " ".join(re.sub(r"\s*\[\w+\]", "", got["sentence"]).split())
    if got["stands"]:
        n = len(got["checks"])
        return f"<span class=say>{by}{esc(plain)}<span class=why>held to the boxes by {n} checks</span></span>"  # fmt: skip
    failed = "; ".join(f"{c}: {w.removeprefix('failed: ')}" for c, ok, w in got["checks"] if ok is False)  # fmt: skip
    return (
        f"<span class='say struck'>{by}<s>{esc(plain)}</s>"
        f"<span class=why>struck, so code's line stands. {esc(failed)}</span></span>"
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
    return (f'<div class=card><div class=where>{where_html(where)}{note}</div>'
            f'<p class=text>{esc(text)}</p></div>')  # fmt: skip


def box_name(box: Path) -> str:
    """What a box is called: its folder's name, or the folder it is in when
    it is itself named box."""
    return box.parent.name if box.name == "box" and box.parent.name else box.name


class Willow:
    """The pages for one box, with this start's secret."""

    def __init__(
        self,
        box: Path,
        lang: str | None = None,
        token: str | None = None,
        stack: Path | None = None,
        run: Path | None = None,
        index: Path | None = None,
        home: Path | None = None,
        say: str | None = None,
        beside: list[Path] | None = None,
        boxes: Path | None = None,
    ):
        self.kept = boxes  # the list of boxes kept elsewhere, boxes-here's
        self.beside = list(beside or [])  # other piles' indexes, asked too
        self.joined: dict[str, list[Path]] = {}  # projects put beside this one
        self.say_model = say  # the model that says a turn's boxes, if any
        self.sayer = None  # prompt -> words, in place of the model: for tests
        self.said_turns = 0
        self.under = home  # the folder its sibling projects are under
        self.sittings: dict[Path, list[dict]] = {}
        self.box = box
        self.stack = stack
        self.run = run
        self.index = index
        self.token = token or secrets.token_urlsafe(32)
        self.words = sibling(f"words-{lang}", f"words_{lang}") if lang else None
        if lang and self.words is None:
            raise ValueError(f"the words-{lang} add-on isn't here")

    @property
    def turns(self) -> list[dict]:
        """This sitting's turns for the box that is open: kept while the
        page runs, and nowhere else."""
        return self.sittings.setdefault(self.box.resolve(), [])

    def projects(self) -> list[dict]:
        """The projects under --home, as the projects add-on finds them:
        each folder that holds a record, with its runs, newest first."""
        pr, st = sibling("projects", "projects"), sibling("stack", "stack")
        if self.under is None or pr is None or st is None:
            return []
        try:
            return pr.find(self.under, st)
        except OSError:
            return []

    def switch(self, name: str) -> bool:
        """Open another project: its box, and its newest run. Only a project
        the projects add-on finds under --home can be opened."""
        for p in self.projects():
            if p["name"] == name:
                self.box = p["boxes"][0]
                self.run = p["runs"][0]["folder"] if p["runs"] else None
                self.stack = self.index = None
                self.beside, self.joined = [], {}
                return True
        return False

    def elsewhere(self) -> list[dict]:
        """The boxes on the --boxes list, as the boxes-here add-on keeps it:
        where each is, what it is called, how many suggestions wait on it,
        and anything else there is to say (it is gone, its chain is
        broken). Empty with no list, or one that can't be read."""
        bh, pr = sibling("boxes-here", "boxes_here"), sibling("projects", "projects")
        if self.kept is None or bh is None or pr is None:
            return []
        doc, _ = bh.kept(self.kept)
        out = []
        for b in doc or []:
            at = Path(b["box"])
            row = {"box": at, "name": box_name(at), "waiting": 0, "said": ""}
            if not bh.is_box(at):
                row["said"] = "gone"
            else:
                said, row["waiting"], broken = bh.waits(at, pr)
                row["said"] = said if broken else ""
            out.append(row)
        return out

    def switch_box(self, at: str) -> bool:
        """Open a box kept elsewhere. Only one on the --boxes list, and
        still there, can be opened."""
        for b in self.elsewhere():
            if str(b["box"]) == at and b["said"] != "gone":
                self.box, self.run = b["box"], None
                self.stack = self.index = None
                self.beside, self.joined = [], {}
                return True
        return False

    def find_boxes(self, folder: str) -> str:
        """The page of the boxes already in a folder, each to tick and
        keep, by the boxes-here add-on; with no folder, the form alone."""
        bh, pr = sibling("boxes-here", "boxes_here"), sibling("projects", "projects")
        token = f'<input type=hidden name=token value="{esc(self.token)}">'
        form = (
            '<form class=find method=post action="/find">' + token
            + '<label>A folder on this machine <input name=folder size=40 '
            f'value="{esc(folder)}"></label> <button>Look</button></form>'
        )  # fmt: skip
        head = (
            "<p>A box that is already there is opened, never made again. Only "
            "whether a box is there, and its record's rows, are looked at. "
            "Nothing is copied or moved.</p>"
        )
        if self.kept is None or bh is None or pr is None:
            return self.page(
                "Boxes elsewhere",
                "<p class=muted>This page was started without a list to keep "
                "them on (--boxes FILE), or the boxes-here add-on isn't here.</p>",
                here="/find",
            )
        if not folder.strip():
            return self.page("Boxes elsewhere", head + form, here="/find")
        at = Path(folder.strip()).expanduser()
        if not at.is_dir():
            body = f"<p>{esc(str(at))} isn't a folder on this machine.</p>"
            return self.page("Boxes elsewhere", head + form + body, here="/find")
        at = at.resolve()
        found, skipped = bh.find(at)
        have = {str(b["box"]) for b in self.elsewhere()}
        body = [head, form]
        if found:
            body.append(f'<form method=post action="/keep">{token}<h2>Already in {esc(str(at))}</h2>')  # fmt: skip
            for b in found:
                said, _, _ = bh.waits(b, pr)
                tick = (
                    "<span class=pill>kept</span>"
                    if str(b) in have
                    else f'<input type=checkbox name=box value="{esc(str(b))}">'
                )
                body.append(
                    f"<p><label>{tick} <b>{esc(box_name(b))}</b> "
                    f"<span class=muted>{esc(str(b))}</span><br>{esc(said)}</label></p>"
                )
            body.append(
                "<p><button>Keep the ticked ones at hand</button></p></form>"
            )  # fmt: skip
        else:
            body.append(
                f"<p>No box is in {esc(str(at))} or {bh.DEEP} folders under it. "
                "To start one there, with the kernel: <code>python kernel.py init "
                "--box FOLDER/box --pile FOLDER</code>.</p>"
            )
        if skipped:
            body.append("<h2>Not looked in</h2>")
            body += [
                f"<p><span class=muted>{esc(str(d))}</span>: {esc(why)}</p>"
                for d, why in skipped
            ]
        return self.page("Boxes elsewhere", "".join(body), here="/find")

    def keep(self, boxes: list[str], drop: bool = False) -> str | None:
        """Keep boxes on the --boxes list, or drop them from it, by the
        boxes-here add-on, in a process of its own: the list is its file to
        write, not this page's. It says why not, or None when it is done."""
        script = STDLIB / "boxes-here" / "boxes_here.py"
        if self.kept is None or not script.is_file():
            return "This page was started without a list to keep boxes on."
        if not boxes:
            return "No box was ticked."
        got = subprocess.run(
            [sys.executable, str(script), "drop" if drop else "keep",
             "--to", str(self.kept), *boxes],
            capture_output=True, text=True, timeout=60,
        )  # fmt: skip
        return None if got.returncode == 0 else got.stderr.strip() or "It wasn't kept."

    def name(self) -> str:
        """What this project is called: its folder's name."""
        return box_name(self.box.resolve())

    def pile(self) -> Path:
        return Path(kernel.config(self.box)["pile"])

    def cited(self, ids: set[str]) -> dict[str, dict]:
        """The passages of the open box's pile with these ids, read a folder
        at a time by the pieces add-on, so a big pile is never all held at
        once; the kernel's whole read when pieces isn't here."""
        if not ids:
            return {}
        pc = sibling("pieces", "pieces")
        found = {}
        for c in pc.passages(self.pile()) if pc else kernel.chunks(self.pile()):
            if c["id"] in ids:
                found[c["id"]] = c
                if len(found) == len(ids):
                    break
        return found

    def of_file(self, path: str) -> list[dict]:
        """One file's passages, and only that file read (pieces), or the
        kernel's whole read when pieces isn't here."""
        pc = sibling("pieces", "pieces")
        return pc.of_file(self.pile(), path) if pc else kernel.chunks(self.pile())

    def owed(self) -> tuple[list[str], list[str]]:
        """(the suggestions waiting for a yes or a no, the record's breaks)."""
        rows, breaks = kernel.read(self.box / "record.jsonl")
        if breaks:
            return [], breaks
        done = {**kernel.sealed(self.box, rows), **kernel.declined(self.box, rows)}
        return [r["subject"] for r in rows if r["kind"] == "proposal"
                and r.get("verdict") == "pass" and r["subject"] not in done], []  # fmt: skip

    def put_beside(self, name: str, off: bool = False) -> str | None:
        """Put another project under --home beside the one that is open, so
        its piles are asked too, or (off) take it away again. Nothing is
        copied and nothing is written: it lasts while the page runs. It says
        why not, or None when it is done. A project is asked by its indexes
        (scan's), never by reading its whole folder."""
        if off:
            self.joined.pop(name, None)
            return None
        for p in self.projects():
            if p["name"] != name:
                continue
            if p["boxes"][0].resolve() == self.box.resolve():
                return "That project is the one that's open."
            d = p["boxes"][0].parent
            found = sorted(
                q.parent
                for depth in ("*", "*/*", "*/*/*")
                for q in d.glob(f"{depth}/index.json")
                if (q.parent / "chunks.jsonl").is_file()
            )
            if not found:
                return (f"{name} has no index yet, and a project is only asked beside "
                        "another by its index. Make one of its folder with the "
                        "index-cache add-on, then drop it here again.")  # fmt: skip
            self.joined[name] = found
            return None
        return "There's no project by that name."

    def side(self, here: str) -> str:
        """The left panel: the project, then each section there is to open,
        the one that is open marked; under the run, its steps."""

        def link(href: str, text: str, more: str = "", sub: bool = False) -> str:
            cls = " ".join(c for c in ("on" * (href == here), "sub" * sub) if c)
            cls = f" class='{cls}'" if cls else ""
            return f'<a href="{href}"{cls}>{esc(text)}{more}</a>'

        n = len(self.owed()[0])
        out = [f"<p class=proj>{esc(self.name())}</p>", link("/", "Ask")]
        out.append(link("/waiting", "Waiting for you",
                        f" <span class='pill wait'>{n}</span>" if n else ""))  # fmt: skip
        if self.stack:
            out.append(link("/steps", "What your stack found"))
        if self.run:
            out.append(link("/run", "The run"))
            st = sibling("stack", "stack")
            logs = sorted(self.run.glob("0*-stack.txt"))
            if st is not None and logs:
                steps, _ = run_steps(
                    logs[0].read_text(encoding="utf-8", errors="replace"), st
                )
                for s in steps:
                    mark = ""
                    if not s["ended"]:
                        mark = " <span class='pill wait'>running</span>"
                    elif s["flagged"]:
                        mark = " <span class='pill wait'>flagged</span>"
                    out.append(link(f"/run#s{s['n']}", f"{s['n']} {s['name']}", mark, True))  # fmt: skip
        found = self.projects()
        if len(found) > 1 or any(
            p["boxes"][0].resolve() != self.box.resolve() for p in found
        ):
            out.append("<p class=proj>Projects</p>")
            for p in found:
                if p["boxes"][0].resolve() == self.box.resolve():
                    out.append(f"<a class=on data-drop>{esc(p['name'])}</a>")
                    continue
                name, on = esc(p["name"]), p["name"] in self.joined
                hidden = (f'<input type=hidden name=token value="{esc(self.token)}">'
                          f'<input type=hidden name=project value="{name}">')  # fmt: skip
                # dragged onto the open project it is asked beside it; the
                # small button does the same with scripts off
                out.append(
                    f'<div class=prow draggable=true data-project="{name}">'
                    f'<form class=switch method=post action="/switch">{hidden}'
                    f"<button class=link>{name}"
                    + (" <span class=pill>beside</span>" if on else "")
                    + "</button></form>"
                    f'<form class=switch method=post action="/beside" data-beside="{name}">{hidden}'
                    + ("<input type=hidden name=off value=1>" if on else "")
                    + f'<button class=tiny title="{"Stop asking it" if on else "Ask it"} beside '
                    f'{esc(self.name())}">{"×" if on else "+"}</button></form></div>'
                )
        if self.kept is not None:
            out.append("<p class=proj>Elsewhere</p>")
            for b in self.elsewhere():
                at = esc(str(b["box"]))
                hidden = (f'<input type=hidden name=token value="{esc(self.token)}">'
                          f'<input type=hidden name=box value="{at}">')  # fmt: skip
                marks = (
                    (f" <span class='pill wait'>{b['waiting']}</span>" if b["waiting"] else "")
                    + (f" <span class='pill wait'>{esc(b['said'].split(':')[0])}</span>" if b["said"] else "")
                )  # fmt: skip
                if b["box"].resolve() == self.box.resolve():
                    out.append(f'<a class=on title="{at}">{esc(b["name"])}{marks}</a>')
                    continue
                out.append(
                    "<div class=prow>"
                    f'<form class=switch method=post action="/switch">{hidden}'
                    f'<button class=link title="{at}">{esc(b["name"])}{marks}</button></form>'
                    f'<form class=switch method=post action="/keep">{hidden}'
                    "<input type=hidden name=off value=1>"
                    '<button class=tiny title="Take it off this list; the box stays '
                    'where it is">×</button></form></div>'
                )
            out.append(link("/find", "Find boxes in a folder"))
        return "".join(out)

    def page(self, title: str, body: str, head: str = "", here: str = "") -> str:
        """A page of this box's. The section that is open is `here`, or the
        one its title is the name of."""
        return page(title, body, self.side(here or SECTIONS.get(title, "")), head)

    def place(self, at: str) -> tuple[str, str]:
        """(What a place is called, what is there): the passage of your
        folder that holds that line, or the lines around it in a file the
        run kept. Only a file the kernel reads into your folder's passages,
        or one of the run's own kept files, is ever opened."""
        at = (at.split() or [""])[-1]
        path, _, line = at.rpartition(":")
        if not path or not line.isdigit():
            return "Not a place", "<p class=muted>That isn't a file and a line.</p>"
        n = int(line)
        if self.run is not None and re.fullmatch(r"\d+-[\w-]+\.txt", path):
            try:
                lines = (self.run / path).read_text(encoding="utf-8", errors="replace").splitlines()  # fmt: skip
            except OSError:
                lines = []
            if 1 <= n <= len(lines):
                near = "".join(
                    f"<div class='ln{' at' if i == n else ''}'>{esc(lines[i - 1]) or '&nbsp;'}</div>"
                    for i in range(max(1, n - 4), min(len(lines), n + 4) + 1)
                )
                return at, f"<p class=kick>What the run kept</p><div class=card>{near}</div>"  # fmt: skip
        best = None
        for c in self.of_file(path):
            if c["path"] == path and c["line"] <= n:
                if best is None or c["line"] > best["line"]:
                    best = c
        if best is None:
            return at, ("<p class=muted>Nothing is at that place in your folder now. "
                        "The file may have changed since this was found.</p>")  # fmt: skip
        return at, (
            "<p class=kick>In your folder</p><div class=card>"
            f"<div class=where>{esc(best['path'])}:{best['line']}</div>"
            f"<p class=text>{esc(best['text'])}</p></div>"
        )

    def detail(self, at: str) -> str:
        """The right panel for a place: what it is called, a way to shut it,
        what is there."""
        title, body = self.place(at)
        return (
            f'<a class=close data-close href="/">Close</a><h2>{esc(title)}</h2>{body}'
        )

    def ran(self) -> str:
        """The run kept in the folder named with --run: read, never run."""
        title = "The run"
        st = sibling("stack", "stack")
        if self.run is None or st is None:
            why = (
                "No run was named when this was started."
                if st
                else "The stack add-on isn't here."
            )
            return self.page(title, f"<p class=muted>{why}</p>")
        logs = sorted(self.run.glob("0*-stack.txt"))
        if not logs:
            return self.page(title, f"<p>{esc(self.run)} holds no run: the stack add-on's <code>--to</code> makes one.</p>")  # fmt: skip
        steps, done = run_steps(
            logs[0].read_text(encoding="utf-8", errors="replace"), st
        )
        if done:
            body = [f"<p><strong>Finished.</strong> {esc(done)}.</p>"]
            head = ""
        else:
            body = [f"<p><strong>Still running.</strong> This page looks again every {AGAIN} seconds.</p>"]  # fmt: skip
            head = f'<meta http-equiv="refresh" content="{AGAIN}">'
        for step in steps:
            name = f"{step['n']}-{step['name']}"
            pills = ""
            if not step["ended"]:
                pills = " <span class='pill wait'>running</span>"
            else:
                pills += " <span class=pill>kept from before</span>" * step["kept"]
                pills += " <span class='pill wait'>flagged</span>" * step["flagged"]
            try:
                doc = json.loads((self.run / "reports" / f"{name}.json").read_text(encoding="utf-8"))  # fmt: skip
                card = report_card(doc, step["code"], pills=f" <span class=pill>step {esc(step['n'])}</span>{pills}")  # fmt: skip
                body.append(f'<div id="s{esc(step["n"])}">{card}</div>')
                continue
            except (OSError, ValueError, KeyError, TypeError):
                pass  # no report kept, or the step hasn't ended: its words
            try:
                text = (self.run / f"{name}.txt").read_text(
                    encoding="utf-8", errors="replace"
                )
            except OSError:
                text = ""
            code = (
                f" <span class=pill>exit {step['code']}</span>" if step["ended"] else ""
            )
            head_html = f"<p class=kick>{esc(step['name'])} <span class=pill>step {esc(step['n'])}</span>{code}{pills}</p>"  # fmt: skip
            body.append(
                f'<div id="s{esc(step["n"])}">{words_card(head_html, text)}</div>'
            )
        if not steps:
            body.append("<p class=muted>No step has started yet.</p>")
        return self.page(title, "".join(body), head, here="/run")

    def steps(self) -> str:
        """What the stack's report steps found, each drawn as a card, in the
        stack file's order under its pools' headings. Run when asked for."""
        title = "What your stack found"
        st = sibling("stack", "stack")
        if self.stack is None or st is None:
            why = (
                "No stack was named when this was started."
                if st
                else "The stack add-on isn't here."
            )
            return self.page(title, f"<p class=muted>{why}</p>")
        try:
            pools, err = st.parse_stack(self.stack.read_text(encoding="utf-8"))
        except OSError:
            pools, err = [], f"can't read the stack {self.stack}"
        if err:
            return self.page(title, f"<p>Couldn't read your stack: {esc(err)}</p>")
        body, left = [], []
        for heading, steps in pools:
            cards = []
            for name, args in steps:
                script = st.resolve(name)
                if script is None:
                    cards.append(f"<div class=card><p class=kick>{esc(name)}</p><p class=muted>The {esc(name)} add-on isn't here.</p></div>")  # fmt: skip
                elif not st.prints_a_report(script):
                    left.append(name)
                else:
                    code, out = st.run_step(script, [*args, "--json"], str(self.box))
                    doc, text = st.as_report(code, out)
                    try:
                        cards.append(report_card(doc, code))
                    except (KeyError, TypeError):  # no report came: what it said
                        cards.append(f"<div class=card><p class=kick>{esc(name)} <span class=pill>exit {code}</span></p><p class=text>{esc(text)}</p></div>")  # fmt: skip
            if cards:
                body.append(f"<h2>{esc(heading)}</h2>" + "".join(cards))
        if left:
            names = ", ".join(dict.fromkeys(left))
            body.append(f"<p class=muted>Not drawn here, since they print something other than a report: {esc(names)}. The stack add-on runs those.</p>")  # fmt: skip
        return self.page(title, "".join(body) or "<p class=muted>Your stack has no step that prints a report.</p>", here="/steps")  # fmt: skip

    def opening(self) -> tuple[str, str]:
        """(Code's one line, the boxes under it) for the top of the stream:
        what waits, what is coming up, what went stale, by the digest add-on."""
        dg = sibling("digest", "digest")
        if dg is None:
            return "", "<p class=muted>The digest add-on isn't here, so there's no summary.</p>"  # fmt: skip
        doc = dg.digest(self.box, date.today())
        if "refused" in doc:
            return "", f"<p>Your record doesn't check out: {esc(doc['refused'])}</p>"
        n, c, s = (len(doc[k]["items"]) for k in ("waiting", "coming", "stale"))
        say = [f"{n} suggestion{'s wait' if n != 1 else ' waits'} for you" if n
               else "Nothing is waiting for you"]  # fmt: skip
        if c:
            say.append(f"{c} coming up in the next two weeks")
        if s:
            say.append(f"{s} approved answer{'s' * (s != 1)} went stale")
        return "; ".join(say) + ".", self.summary(doc)

    def home(self) -> str:
        return self.stream()

    def stream(self) -> str:
        """The middle panel's own section: one column, in the order things
        were said. A line of yours is plain. Everything this page says is
        marked as code's, with the boxes it rests on under it; the newest is
        open and the rest are folded to their one line."""
        turns = self.turns
        say, boxes = self.opening()
        # the one that is open is the newest with boxes under it: small talk
        # doesn't fold the answer you were reading
        shown = next((t for t in reversed(turns) if t["boxes"]), None)
        out = [turn_html("", "", say, "", boxes, shown is None)]
        out += [
            turn_html(
                t["at"],
                t["you"],
                t["say"],
                t["again"],
                t["boxes"],
                t is shown,
                self.voiced(t),
            )  # fmt: skip
            for t in turns
        ]
        title = "Ask" if turns else "Your folder"
        return self.page(title, "".join(out) + ask_form(self.token), here="/")

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

    def from_run(self, question: str) -> tuple[str, bool, str]:
        """(What the kept run already holds for a question, as the look add-on
        finds it: the lines of the steps whose job its kind is; whether a
        step answered; look's one line, to say.) The kernel's own answer is
        the page's, below, so look's note that it left the ask is dropped; a
        step it couldn't answer from is still said."""
        if self.run is None:
            return "", False, ""
        _, doc = report_of("look", "look", question, "--run", str(self.run))
        if doc is None:
            return "", False, ""
        groups = []
        for g in doc["groups"]:
            rows = [
                r
                for r in g["rows"]
                if not (g["name"] == "left" and r["where"] == "ask")
            ]
            if rows:
                groups.append({**g, "rows": rows})
        if not groups:
            return "", False, ""
        left = any(g["name"] == "left" for g in groups)
        doc = {**doc, "state": "populated", "groups": groups}
        card = report_card(doc, kernel.ESCALATE if left else kernel.ALIVE)
        answered = any(g["name"] != "left" for g in groups)
        # look's line without the question said back, or the cue that sent it
        line = re.sub(r' \(by "[^"]*"\)', "", doc["said"].rpartition('": ')[2])
        return "<h2>What your stack already found</h2>" + card, answered, line

    def voiced(self, turn: dict) -> str:
        """Where a model's sentence about a turn goes: the sentence, once it
        has been asked for; before that, an empty place the page's script
        fills by asking. With no script it stays empty, and code's line is
        the whole reply. Nothing, when no model was named or the turn has
        no boxes to say."""
        if "model" in turn:
            return model_html(turn["model"])
        if self.say_model is None or not turn.get("facts"):
            return ""
        return f'<span data-say="/say?turn={turn["id"]}"></span>'

    def say(self, turn_id: str) -> str:
        """A model's sentence about one turn's boxes, asked once and kept
        with the turn: the say add-on asks a model on this machine and holds
        the sentence to the boxes. The boxes are what code's own line was
        made from, so the model is given nothing code didn't say."""
        turn = next((t for t in self.turns if str(t.get("id")) == turn_id), None)
        if turn is None or self.say_model is None or not turn.get("facts"):
            return ""
        if "model" not in turn:
            boxes = [{"id": f"b{n}", "text": f} for n, f in enumerate(turn["facts"], 1)]
            try:
                mod = sibling("say", "say")
                got = (
                    mod.said(boxes, turn["you"], None, self.sayer, self.say_model)
                    if mod is not None
                    else {"state": "unreachable", "why": "the say add-on isn't here"}
                )
            except Exception as e:  # noqa: BLE001 - a voice that fails never takes the page with it
                got = {"state": "unreachable", "why": f"the say add-on couldn't: {type(e).__name__}"}  # fmt: skip
            turn["model"] = {"model": self.say_model, **got}
        return model_html(turn["model"])

    def other_piles(self, asked: str) -> tuple[str, str]:
        """(What the piles beside your folder hold for a question, as one box;
        the line to say.) Each pile is ranked on its own and they take turns
        (the fair-merge add-on); nothing of it goes on your record, and none
        of it is your folder's answer. ("", "") with no pile beside, or
        when fair-merge isn't here."""
        fair = sibling("fair-merge", "fair_merge")
        if fair is None or sibling("scan", "scan") is None:
            return "", ""
        piles = [(i.name, i) for i in self.beside]
        piles += [(f"{n}: {i.name}", i) for n, found in self.joined.items() for i in found]  # fmt: skip
        if not piles:
            return "", ""
        try:
            got = fair.across(
                [i for _, i in piles], asked, {}, names=[n for n, _ in piles]
            )
        except (OSError, ValueError) as e:
            return f"<h2>Other piles</h2><p class=muted>Couldn't look: {esc(e)}</p>", ""
        cards = "".join(
            f"<div class=card><div class=where>{esc(s['where'])} "
            f"<span class=muted>(in {esc(', '.join(s['in']))})</span></div>"
            f"<p class=text>{esc(s['text'])}</p></div>"
            for s in got["served"]
        )
        rows = []
        for q in got["piles"]:
            said = ["found nothing"] if not q["found"] else (
                [f"{q['more']} more, not shown"] if q["more"] else [])  # fmt: skip
            if q["lacks"]:
                said.append("no passage holds: " + ", ".join(q["lacks"]))
            if said:
                rows.append(
                    f"<p class=muted>{esc(q['name'])}: {esc('; '.join(said))}</p>"
                )
        n, of = sum(bool(q["found"]) for q in got["piles"]), len(got["piles"])
        line = (f"{n} of {of} other pile{'s' * (of != 1)} hold{'s' * (n == 1)} something for it"
                if n else f"none of the {of} other pile{'s' * (of != 1)} holds it")  # fmt: skip
        return f"<h2>Other piles, not your folder</h2>{cards}{''.join(rows)}", line

    def ask(self, question: str) -> str:
        """Your line, then code's answer under it, added to the stream."""
        turns = self.turns
        turns.append(self.answer(question.strip()))
        del turns[:-KEPT]
        return self.stream()

    def answer(self, question: str) -> dict:
        """One turn: when, your words as you typed them, code's one line,
        when the same words were first asked (if they were), and the boxes
        the line rests on. No model is asked; the line is made here, from
        what the boxes hold."""
        self.said_turns += 1
        turn = {"at": datetime.now().strftime("%H:%M"), "you": question, "say": "",
                "again": "", "boxes": [], "facts": [], "id": self.said_turns}  # fmt: skip
        small = SMALL.get(" ".join(question.lower().split()).strip(" .!?"))
        if small:  # small talk: code's own word, nothing asked, nothing on the record
            return {**turn, "say": small}
        asked = question
        if self.words is not None:
            asked = " ".join(self.words.kept(question))
        if not kernel.words(asked):
            return {**turn, "say": "Every word there is a common one. Name the thing you mean."}  # fmt: skip
        key = kernel.bite_key(asked)
        before = [r["ts"] for r in kernel.read(self.box / "record.jsonl")[0]
                  if r["kind"] == "bite" and r.get("bite_key") == key]  # fmt: skip
        turn["again"] = before[0] if before else ""
        doc = indexed(self.box, asked, self.index) if self.index else None
        if doc is None:  # no index, or not current: the kernel reads the folder
            code, said, err = call("bite", "--box", str(self.box), asked)
            if code == kernel.REFUSED:
                return {**turn, "again": "", "say": f"Couldn't ask: {err.strip() or said.strip()}"}  # fmt: skip
            doc = json.loads(said)
        found, answered, line = self.from_run(question)
        line = line[:1].upper() + line[1:] + "." if line else ""
        boxes, facts = turn["boxes"], turn["facts"]
        turn = self.answered(turn, doc, asked, found, answered, line)
        if doc["state"] == "populated" and self.index:
            lacks = lacking(self.box, asked, self.index)
            if lacks:  # shown on half the words: say which the folder holds nowhere
                gone = ", ".join(lacks)
                turn["say"] += f" No passage in your folder holds: {gone}."
                boxes.append(f"<p class=muted>No passage in your folder holds: {esc(gone)}.</p>")  # fmt: skip
                facts.append(f"no passage in your folder holds: {gone}")
        other, said = self.other_piles(asked)
        if other:
            boxes.append(other)
        if said:
            turn["say"] += f" Beside it, {said}."
            facts.append(f"beside your folder, {said}")
        return turn

    def answered(self, turn: dict, doc: dict, asked: str, found, answered, line: str) -> dict:  # fmt: skip
        """A turn with your folder's own answer in it: what the run held,
        then the kernel's answer, sealed, served or nothing."""
        boxes, facts = turn["boxes"], turn["facts"]
        if found:
            boxes.append(found)
            facts.append(line)
        if doc["state"] == "sealed":
            boxes.insert(0, "<h2>You approved this answer</h2><div class=card>"
                         f"{rich(doc['answer'])}<p class=where>{esc(doc['by'])}</p></div>")  # fmt: skip
            turn["say"] = "You approved an answer for this."
            facts.insert(0, "you approved an answer for this: " + short(doc["answer"]))
        elif doc["state"] == "populated":
            served = [
                passage(s["where"], s["text"], "only asks your question back" if s["echo"] else "")
                for s in doc["served"]
            ]  # fmt: skip
            served[0] = "<h2>Your files say</h2>" + served[0]
            boxes += served
            n = sum(not s["echo"] for s in doc["served"])
            first = next(s["where"] for s in doc["served"] if not s["echo"])
            text = next(s["text"] for s in doc["served"] if not s["echo"])
            facts.append(f"your files hold {n} passage{'s' * (n != 1)} for it; "
                         f"the first is at {first}: {short(text)}")  # fmt: skip
            turn["say"] = (
                f"{line} Your files hold {n} passage{'s' * (n != 1)} for it too."
                if answered
                else f"Your files hold {n} passage{'s' * (n != 1)} for that; the first is at {first}."
            )
        else:
            # a question a step answered is no miss: it is a sum over many
            # lines, which no one passage says
            head = ("<h2>No one passage in your folder says that</h2>" if answered
                    else "<h2>Nothing in your folder holds that</h2>")  # fmt: skip
            echoes = "".join(passage(s["where"], s["text"], "only asks your question back")
                             for s in doc["served"])  # fmt: skip
            tips = "".join(
                "<p class=muted>" + " · ".join(esc(h[k]) for k in ("why", "where", "next") if h.get(k)) + "</p>"
                for h in doc.get("look", [])
            )  # fmt: skip
            boxes.append(head + echoes + tips)
            # why it found nothing, in the why-not add-on's words, if it's here
            code, why = report_of("why-not", "why_not", "--box", str(self.box), asked)
            if why is not None and why["groups"]:
                card = report_card(why, code)
                boxes.append(
                    f"<details><summary>Why no passage holds it</summary>{card}</details>"
                    if answered
                    else card
                )
            turn["say"] = (f"{line} No one passage in your folder says it." if answered
                           else "Nothing in your folder holds that.")  # fmt: skip
            facts.append("no one passage in your folder says it" if answered
                         else "nothing in your folder holds that")  # fmt: skip
        return turn

    def waiting(self) -> str:
        subjects, breaks = self.owed()
        if breaks:
            return self.page(
                "Waiting for you",
                f"<p>Your record doesn't check out: {esc('; '.join(breaks))}</p>",
            )
        if not subjects:
            return self.page(
                "Waiting for you",
                "<p class=muted>Nothing is waiting for your approval.</p>",
            )
        props = {
            subj: json.loads((self.box / "proposals" / f"{subj[9:]}.json").read_text())
            for subj in subjects
        }
        pile = self.cited({c for prop in props.values() for c in prop["cites"]})
        n = len(subjects)
        body = [
            f"<p><strong>{n} waiting.</strong> Each was suggested by something you let "
            "ask your folder. Approving one makes it the answer to its question from "
            "now on.</p>"
        ]
        for subj in subjects:
            prop = props[subj]
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
        return self.page("Waiting for you", "".join(body), here="/waiting")

    def approve(self, subject: str) -> str:
        code, said, err = call("seal", "--box", str(self.box), subject)
        if code != kernel.ALIVE:
            return self.page(
                "Not approved", f"<p>{esc(err.strip() or said.strip())}</p>"
            )
        return self.page("Approved", "<p>It's on your record, signed with your key, and it "
                    "answers its question from now on.</p>"
                    '<p><a href="/waiting">Back to what\'s waiting</a></p>')  # fmt: skip


AGAIN = 3  # seconds between looks at a run that is still going


def run_steps(log: str, st) -> tuple[list[dict], str | None]:
    """A run's log as (its steps in order, the line that ended it or None).
    Each step: its number as written, its name, whether it has ended, and
    then its exit code, whether it was flagged, and whether it was kept from
    an earlier go. The lines are the stack add-on's, read by its own
    patterns, so the two can't come to disagree about what a line says."""
    steps: dict[str, dict] = {}
    done = None
    for line in log.splitlines():
        if m := st.STARTED.fullmatch(line):
            steps[m.group(1)] = {"n": m.group(1), "name": m.group(2), "ended": False}
            done = None
        elif m := st.ENDED.fullmatch(line):
            step = steps.get(m.group(1))
            if step and step["name"] == m.group(2):
                said = [x for x in m.group(5).split(", ") if x]
                step.update(ended=True, code=int(m.group(3)), flagged="flagged" in said, kept=False)  # fmt: skip
        elif line.endswith(": kept from before"):
            n = line.split(" ", 1)[0]
            if n in steps and steps[n]["ended"]:
                steps[n]["kept"] = True
        elif line.startswith("done: "):
            done = line[6:]
        elif line.startswith("resumed: "):
            done = None
    return [steps[n] for n in sorted(steps)], done


def words_card(head: str, text: str, shown: int = SHOWN) -> str:
    """A step that printed words, not a report: its first lines in sight and
    the rest folded, as written."""
    lines = text.splitlines()
    rest = ""
    if len(lines) > shown:
        rest = (
            f"<details><summary>All {len(lines)} lines</summary>"
            f"<pre>{esc(chr(10).join(lines[shown:]))}</pre></details>"
        )
    first = f"<pre>{esc(chr(10).join(lines[:shown]))}</pre>" if lines else "<p class=muted>It printed nothing.</p>"  # fmt: skip
    return f"<div class=card>{head}{first}{rest}</div>"


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
        if url.path == "/steps":
            return self.send(200, self.willow.steps())
        if url.path == "/run":
            return self.send(200, self.willow.ran())
        if url.path == "/find":
            return self.send(200, self.willow.find_boxes(""))
        if url.path == "/page.js":
            return self.send(200, SCRIPT.read_text(encoding="utf-8"),
                             {"Content-Type": "text/javascript; charset=utf-8"})  # fmt: skip
        if url.path == "/say":
            return self.send(200, self.willow.say(parse_qs(url.query).get("turn", [""])[0]))  # fmt: skip
        if url.path == "/place":
            asked = parse_qs(url.query)
            at = asked.get("at", [""])[0]
            if asked.get("part"):  # the right panel alone, for the page's script
                return self.send(200, self.willow.detail(at))
            title, body = self.willow.place(at)
            return self.send(200, self.willow.page(title, body))
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
        if url.path == "/find":
            return self.send(200, self.willow.find_boxes(form.get("folder", [""])[0]))
        if url.path == "/keep":
            why = self.willow.keep(form.get("box", []), "off" in form)
            if why is not None:
                return self.send(409, self.willow.page("Not kept", f"<p>{esc(why)}</p>"))  # fmt: skip
            return self.send(303, "", {"Location": "/"})
        if url.path == "/switch" and "box" in form:
            if not self.willow.switch_box(form["box"][0]):
                return self.send(404, self.willow.page("Not here", "<p>There's no box kept by that place.</p>"))  # fmt: skip
            return self.send(303, "", {"Location": "/"})
        if url.path == "/switch":
            if not self.willow.switch(form.get("project", [""])[0]):
                return self.send(404, self.willow.page("Not here", "<p>There's no project by that name.</p>"))  # fmt: skip
            return self.send(303, "", {"Location": "/"})
        if url.path == "/beside":
            why = self.willow.put_beside(form.get("project", [""])[0], "off" in form)
            if why is not None:
                return self.send(
                    409, self.willow.page("Not beside", f"<p>{esc(why)}</p>")
                )
            return self.send(303, "", {"Location": "/"})
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
    opts, flags, rest, beside, it = {}, set(), [], [], iter(argv)
    for a in it:
        if a in (
            "--box",
            "--port",
            "--lang",
            "--stack",
            "--run",
            "--index",
            "--home",
            "--say",
            "--boxes",
        ):
            opts[a] = next(it, "")
        elif a == "--beside":
            beside.append(next(it, ""))
        elif a == "--no-open":
            flags.add(a)
        else:
            rest.append(a)
    port = opts.get("--port", "0")
    if (not opts.get("--box") or rest or not port.isdigit() or int(port) > 65535
            or opts.get("--lang", "de") not in LANGS
            or ("--stack" in opts and not opts["--stack"])
            or ("--run" in opts and not opts["--run"])
            or ("--index" in opts and not opts["--index"])
            or ("--home" in opts and not opts["--home"])
            or ("--say" in opts and not opts["--say"])
            or ("--boxes" in opts and not opts["--boxes"])
            or "" in beside):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    try:
        stack = Path(opts["--stack"]) if "--stack" in opts else None
        if stack is not None and not stack.is_file():
            print(f"refused: can't read the stack {stack}", file=sys.stderr)
            return kernel.REFUSED
        run = Path(opts["--run"]) if "--run" in opts else None
        if run is not None and not run.is_dir():
            print(f"refused: {run} isn't a folder that's there", file=sys.stderr)
            return kernel.REFUSED
        index = Path(opts["--index"]) if "--index" in opts else None
        if index is not None and not index.is_dir():
            print(f"refused: {index} isn't an index that's there (scan's index, kept by index-cache)", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
        for i in beside:
            if not (Path(i) / "index.json").is_file():
                print(f"refused: {i} isn't an index (scan makes one)", file=sys.stderr)
                return kernel.REFUSED
        home = Path(opts["--home"]) if "--home" in opts else None
        if home is not None and not home.is_dir():
            print(f"refused: {home} isn't a folder that's there", file=sys.stderr)
            return kernel.REFUSED
        kept = Path(opts["--boxes"]).expanduser() if "--boxes" in opts else None
        if kept is not None and not kept.parent.is_dir():
            print(f"refused: {kept.parent} isn't a folder that's there", file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
        willow = Willow(box, opts.get("--lang"), stack=stack, run=run, index=index, home=home, say=opts.get("--say"),
                        beside=[Path(i) for i in beside], boxes=kept)  # fmt: skip
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
