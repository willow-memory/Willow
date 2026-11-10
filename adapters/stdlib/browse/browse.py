"""browse.py: your folder in your web browser, on this machine only. Python 3.9+.

    python adapters/stdlib/browse/browse.py --box DIR [--stack FILE] [--run FOLDER]
        [--port N] [--lang de|es|fr|pt] [--no-open]
    python adapters/stdlib/browse/browse.py projects [--home DIR] [--port N] [--no-open]
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

`projects` is the front door when you keep several: every folder under DIR
(~/willow-stacks unless you say) that holds a box is a project, shown with
what waits in each box, its stack files and its runs. Opening one gives the
same pages as above for that box, with links to switch between its stacks
and between its runs.

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
.switch { margin: 0 0 12px; }
.pill.wait { background: var(--accl); color: var(--fg); }
.group { font-weight: 600; margin: 10px 0 2px; }
.row { display: grid; grid-template-columns: minmax(7rem, 38%) 1fr; gap: 10px;
       padding: 3px 0; border-top: 1px solid var(--line); }
.row .text { margin: 0; white-space: normal; }
"""


def page(title: str, body: str, more: str = "", head: str = "") -> str:
    """One page. `more` is links for the bar after the two every page has;
    `head` is for the head (the run's page asks to be looked at again)."""
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width, initial-scale=1">'
        f"{head}<title>{esc(title)} · willow</title><style>{STYLE}</style></head><body>"
        f'<nav><a href="/">Home</a><a href="/waiting">Waiting for you</a>{more}</nav>'
        f"<main><h1>{esc(title)}</h1>{body}</main></body></html>"
    )


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
            f"<div class=row><span class=where>{esc(row['where'])}</span>"
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

    def __init__(
        self,
        box: Path,
        lang: str | None = None,
        token: str | None = None,
        stack: Path | None = None,
        run: Path | None = None,
        base: str = "",
        stacks: list[Path] | None = None,
        runs: list[Path] | None = None,
    ):
        self.box = box
        #: every stack file and run this box's pages may show; the first is
        #: shown unless another is asked for by name, never by path
        self.stacks = stacks if stacks is not None else ([stack] if stack else [])
        self.runs = runs if runs is not None else ([run] if run else [])
        self.stack = self.stacks[0] if self.stacks else None
        self.run = self.runs[0] if self.runs else None
        self.base = base  # "/p/NAME" when one of several projects, else ""
        self.token = token or secrets.token_urlsafe(32)
        self.words = sibling(f"words-{lang}", f"words_{lang}") if lang else None
        if lang and self.words is None:
            raise ValueError(f"the words-{lang} add-on isn't here")

    def page(self, title: str, body: str, head: str = "") -> str:
        more = '<a href="/steps">What your stack found</a>' if self.stack else ""
        more += '<a href="/run">The run</a>' if self.run else ""
        html = page(title, body, more, head)
        if self.base:  # one of several: its links are its own, and a way back
            html = html.replace('href="/', f'href="{self.base}/')
            html = html.replace('action="/', f'action="{self.base}/')
            html = html.replace("<nav>", '<nav><a href="/">Projects</a>', 1)
        return html

    def switch(self, what: str, choices: list[Path], chosen: Path) -> str:
        """Links to the other stacks (or runs) of this project, the one in
        view named plainly; nothing when there is only the one."""
        if len(choices) < 2:
            return ""
        links = [
            f"<strong>{esc(c.name)}</strong>" if c == chosen
            else f'<a href="/{what}?pick={esc(c.name)}">{esc(c.name)}</a>'
            for c in choices
        ]  # fmt: skip
        return f"<p class=switch>{' · '.join(links)}</p>"

    @staticmethod
    def picked(choices: list[Path], name: str) -> Path | None:
        """The choice of that name, or the first; a name is never a path."""
        return next(
            (c for c in choices if c.name == name), choices[0] if choices else None
        )

    def ran(self, pick: str = "") -> str:
        """The run kept in the folder named with --run: read, never run."""
        title = "The run"
        st = sibling("stack", "stack")
        run = self.picked(self.runs, pick)
        if run is None or st is None:
            why = (
                "No run was named when this was started."
                if st
                else "The stack add-on isn't here."
            )
            return self.page(title, f"<p class=muted>{why}</p>")
        logs = sorted(run.glob("0*-stack.txt"))
        if not logs:
            return self.page(title, f"<p>{esc(run)} holds no run: the stack add-on's <code>--to</code> makes one.</p>")  # fmt: skip
        steps, done = run_steps(
            logs[0].read_text(encoding="utf-8", errors="replace"), st
        )
        if done:
            body = [self.switch("run", self.runs, run), f"<p><strong>Finished.</strong> {esc(done)}.</p>"]  # fmt: skip
            head = ""
        else:
            body = [self.switch("run", self.runs, run), f"<p><strong>Still running.</strong> This page looks again every {AGAIN} seconds.</p>"]  # fmt: skip
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
                doc = json.loads((run / "reports" / f"{name}.json").read_text(encoding="utf-8"))  # fmt: skip
                body.append(report_card(doc, step["code"], pills=f" <span class=pill>step {esc(step['n'])}</span>{pills}"))  # fmt: skip
                continue
            except (OSError, ValueError, KeyError, TypeError):
                pass  # no report kept, or the step hasn't ended: its words
            try:
                text = (run / f"{name}.txt").read_text(
                    encoding="utf-8", errors="replace"
                )
            except OSError:
                text = ""
            code = (
                f" <span class=pill>exit {step['code']}</span>" if step["ended"] else ""
            )
            head_html = f"<p class=kick>{esc(step['name'])} <span class=pill>step {esc(step['n'])}</span>{code}{pills}</p>"  # fmt: skip
            body.append(words_card(head_html, text))
        if not steps:
            body.append("<p class=muted>No step has started yet.</p>")
        return self.page(title, "".join(body), head)

    def steps(self, pick: str = "") -> str:
        """What the stack's report steps found, each drawn as a card, in the
        stack file's order under its pools' headings. Run when asked for."""
        title = "What your stack found"
        st = sibling("stack", "stack")
        stack = self.picked(self.stacks, pick)
        if stack is None or st is None:
            why = (
                "No stack was named when this was started."
                if st
                else "The stack add-on isn't here."
            )
            return self.page(title, f"<p class=muted>{why}</p>")
        try:
            pools, err = st.parse_stack(stack.read_text(encoding="utf-8"))
        except OSError:
            pools, err = [], f"can't read the stack {stack}"
        if err:
            return self.page(title, f"<p>Couldn't read your stack: {esc(err)}</p>")
        body, left = [self.switch("steps", self.stacks, stack)], []
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
        if not any(body[1:]):
            body.append(
                "<p class=muted>Your stack has no step that prints a report.</p>"
            )
        return self.page(title, "".join(body))

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
        return self.page("Your folder", ask_form(self.token) + summary)

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
            return self.page("Ask", ask_form(self.token, question) +
                        "<p>Every word there is a common one. Name the thing you mean.</p>")  # fmt: skip
        code, said, err = call("bite", "--box", str(self.box), asked)
        body = ask_form(self.token, question)
        if code == kernel.REFUSED:
            return self.page(
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
        return self.page("Ask", body)

    def waiting(self) -> str:
        rows, breaks = kernel.read(self.box / "record.jsonl")
        if breaks:
            return self.page(
                "Waiting for you",
                f"<p>Your record doesn't check out: {esc('; '.join(breaks))}</p>",
            )
        done = {**kernel.sealed(self.box, rows), **kernel.declined(self.box, rows)}
        subjects = [r["subject"] for r in rows if r["kind"] == "proposal"
                    and r.get("verdict") == "pass" and r["subject"] not in done]  # fmt: skip
        if not subjects:
            return self.page(
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
        return self.page("Waiting for you", "".join(body))

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


def tally(box: Path) -> dict:
    """A box in four counts, or why it can't be counted: questions asked,
    answers approved, suggestions waiting, rows on the record."""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return {"broken": "; ".join(breaks)}
    done = {**kernel.sealed(box, rows), **kernel.declined(box, rows)}
    waiting = sum(1 for r in rows if r["kind"] == "proposal"
                  and r.get("verdict") == "pass" and r["subject"] not in done)  # fmt: skip
    return {
        "asked": sum(1 for r in rows if r["kind"] == "bite"),
        "approved": len(kernel.sealed(box, rows)),
        "waiting": waiting,
        "rows": len(rows),
    }


def find_projects(home: Path) -> list[dict]:
    """Each folder under `home` that holds a box: its boxes, the stack files
    beside them, and its runs (here, or one folder down), newest first.
    A project is found by what it holds, never by a name it was given."""
    st = sibling("stack", "stack")
    out = []
    for d in sorted(
        p for p in home.iterdir() if p.is_dir() and not p.name.startswith(".")
    ):
        boxes = sorted(b for b in d.iterdir() if (b / "kernel.json").is_file())
        if not boxes:
            continue
        stacks = []
        for f in sorted(d.glob("*.md")) if st else []:
            try:
                if not st.parse_stack(f.read_text(encoding="utf-8"))[1]:
                    stacks.append(f)
            except (OSError, ValueError):
                pass
        # a run is a folder with a stack's log in it: here, or one folder down
        # (runs/, mine/, whatever the person called it), never inside a box
        places = [d, *(c for c in d.iterdir() if c.is_dir() and c not in boxes)]
        runs = [
            r
            for place in places
            for r in sorted(place.iterdir())
            if r.is_dir() and r not in boxes and any(r.glob("0*-stack.txt"))
        ]
        runs.sort(key=lambda r: (-r.stat().st_mtime, r.name))
        out.append(
            {
                "name": d.name,
                "folder": d,
                "boxes": boxes,
                "stacks": stacks,
                "runs": runs,
            }
        )
    return out


class Projects:
    """The front door: every project under one folder, and the pages of each."""

    def __init__(self, home: Path, token: str | None = None):
        self.home = home
        self.token = token or secrets.token_urlsafe(32)

    def key(self, project: dict, box: Path) -> str:
        return f"{project['name']}~{box.name}"

    def willow(self, key: str) -> Willow | None:
        """The pages for one box of one project, by its key; None if no
        project found now has that key (a key is looked up, never joined
        to a path)."""
        for pr in find_projects(self.home):
            for box in pr["boxes"]:
                if self.key(pr, box) == key:
                    return Willow(box, None, self.token, base=f"/p/{key}",
                                  stacks=pr["stacks"], runs=pr["runs"])  # fmt: skip
        return None

    def front(self) -> str:
        found = find_projects(self.home)
        body = []
        for pr in found:
            boxes = []
            for box in pr["boxes"]:
                t = tally(box)
                if "broken" in t:
                    said = f"<span class='pill wait'>its record doesn't check out</span> {esc(t['broken'])}"
                else:
                    said = (
                        (
                            f"<span class='pill wait'>{t['waiting']} waiting on you</span> "
                            if t["waiting"]
                            else ""
                        )
                        + f"<span class=pill>{t['approved']} approved</span> "
                        f"<span class=pill>{t['asked']} asked</span>"
                    )
                boxes.append(
                    f'<div class=row><a href="/p/{esc(self.key(pr, box))}/">{esc(box.name)}</a>'
                    f"<p class=text>{said}</p></div>"
                )
            n, m = len(pr["stacks"]), len(pr["runs"])
            stacks = ", ".join(esc(f.name) for f in pr["stacks"]) or "none yet"
            latest = f", the latest {esc(pr['runs'][0].name)}" if m else ""
            body.append(
                f"<div class=card><p class=kick>project</p><h2>{esc(pr['name'])}</h2>"
                + "".join(boxes)
                + f"<p class=muted>{n} stack{'s' * (n != 1)}: {stacks}. {m} run{'s' * (m != 1)} kept{latest}.</p></div>"
            )
        if not found:
            body.append(
                f"<p class=muted>No folder under {esc(self.home)} holds a box yet.</p>"
            )
        examples = sorted(p.stem for p in (STDLIB / "stack" / "examples").glob("*.md"))
        body.append(
            "<h2>Start a new one</h2><p>A new project is put together on the canvas, "
            "willow's page for choosing folders and what to do with them. This page "
            "can't open it for you yet; from a terminal, in willow's folder:</p>"
            f"<pre>python ui/canvas.py --to {esc(self.home)}/NAME</pre>"
            + (
                f"<p class=muted>It can start from an example: {esc(', '.join(examples))}.</p>"
                if examples
                else ""
            )
        )
        html = page("Your projects", "".join(body))
        return html.replace('<a href="/">Home</a><a href="/waiting">Waiting for you</a>', '<a href="/">Projects</a>', 1)  # fmt: skip


# ── the server ───────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    willow: Willow | None  # the one box's pages, or None when there are projects
    projects: "Projects | None" = None
    token: str
    hosts: frozenset

    def site(self, path: str) -> tuple[Willow | None, str]:
        """(whose pages, the path within them) for an address: the one box's,
        or under /p/KEY/ the project's of that key."""
        if self.projects is None:
            return self.willow, path
        if path.startswith("/p/"):
            key, _, rest = path[3:].partition("/")
            return self.projects.willow(key), "/" + rest
        return None, path

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
        if not hmac.compare_digest(self.cookie(), self.token):
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
            if not hmac.compare_digest(given, self.token):
                return self.refuse("That link is from another start, or was cut short.")
            return self.send(
                303,
                "",
                {
                    "Location": "/",
                    "Set-Cookie": f"{COOKIE}={self.token}; HttpOnly; SameSite=Strict; Path=/",
                },
            )
        if not self.allowed():
            return None
        if self.projects is not None and url.path == "/":
            return self.send(200, self.projects.front())
        willow, path = self.site(url.path)
        pick = parse_qs(url.query).get("pick", [""])[0]
        if willow is not None and path == "/":
            return self.send(200, willow.home())
        if willow is not None and path == "/waiting":
            return self.send(200, willow.waiting())
        if willow is not None and path == "/steps":
            return self.send(200, willow.steps(pick))
        if willow is not None and path == "/run":
            return self.send(200, willow.ran(pick))
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
        if not hmac.compare_digest(form.get("token", [""])[0], self.token):
            return self.refuse("That form wasn't made by this page.")
        willow, path = self.site(urlsplit(self.path).path)
        if willow is not None and path == "/ask":
            return self.send(200, willow.ask(form.get("q", [""])[0]))
        if willow is not None and path == "/approve":
            return self.send(200, willow.approve(form.get("subject", [""])[0]))
        return self.send(
            404, page("Not here", "<p>There's no page at that address.</p>")
        )


class Server(HTTPServer):
    def server_bind(self) -> None:
        # HTTPServer's own looks this machine's name up; nothing here needs it
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


def serve(willow: "Willow | Projects", port: int = 0) -> Server:
    """A server for `willow` on 127.0.0.1, bound but not yet serving."""
    server = Server(("127.0.0.1", port), Handler)
    bound = server.server_address[1]
    handler = type(
        "BoundHandler",
        (Handler,),
        {
            "willow": willow if isinstance(willow, Willow) else None,
            "projects": willow if isinstance(willow, Projects) else None,
            "token": willow.token,
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


def main_projects(argv: list[str]) -> int:
    opts, flags, rest, it = {}, set(), [], iter(argv)
    for a in it:
        if a in ("--home", "--port"):
            opts[a] = next(it, "")
        elif a == "--no-open":
            flags.add(a)
        else:
            rest.append(a)
    port = opts.get("--port", "0")
    if rest or not port.isdigit() or int(port) > 65535 or ("--home" in opts and not opts["--home"]):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    home = Path(opts["--home"]) if "--home" in opts else Path.home() / "willow-stacks"
    if not home.is_dir():
        print(f"refused: {home} isn't a folder that's there", file=sys.stderr)
        return kernel.REFUSED
    try:
        site = Projects(home)
        server = serve(site, int(port))
    except OSError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    link = f"http://127.0.0.1:{server.server_address[1]}/start?key={site.token}"
    print(f"willow is open on this machine only:\n\n    {link}\n\nCtrl-C stops it.", flush=True)  # fmt: skip
    if "--no-open" not in flags:
        webbrowser.open(link)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return kernel.ALIVE


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
    if argv[:1] == ["projects"]:
        return main_projects(argv[1:])
    opts, flags, rest, it = {}, set(), [], iter(argv)
    for a in it:
        if a in ("--box", "--port", "--lang", "--stack", "--run"):
            opts[a] = next(it, "")
        elif a == "--no-open":
            flags.add(a)
        else:
            rest.append(a)
    port = opts.get("--port", "0")
    if (not opts.get("--box") or rest or not port.isdigit() or int(port) > 65535
            or opts.get("--lang", "de") not in LANGS
            or ("--stack" in opts and not opts["--stack"])
            or ("--run" in opts and not opts["--run"])):  # fmt: skip
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
        willow = Willow(box, opts.get("--lang"), stack=stack, run=run)
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
