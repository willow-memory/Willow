"""print.py: an answer as a page to print and take with you. Python 3.9+.

    python adapters/stdlib/print/print.py --box DIR --to FILE.html [--large] [--now TS] "your question"

Asks the kernel (its own `bite`, so the question is on the record as if
typed) and writes one page: the question, the day, and the answer. That's
your approved answer if you approved one, or else the passages from your
files, each with its file and line, so whoever reads it can see where it
came from. Open it in a browser and print it, or save it as a PDF.

--large sets it in large, high-contrast type, for reading on a screen or
on paper without glasses: the large-print idea, built as a switch here.

The page carries no script and loads nothing from anywhere. It says, at the
foot, the record's row and fingerprint for the question, so the answer can
be checked against the record later. It never overwrites a file.

Exit codes, the kernel's bite's: 0 your files hold it (the page says so);
42 they don't (the page says that, and where it looked); 2 refused.
"""

from __future__ import annotations

import contextlib
import html
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

STYLE = """
body { font: 12pt/1.5 Georgia, 'Times New Roman', serif; color: #111; background: #fff;
       max-width: 42rem; margin: 2rem auto; padding: 0 1rem; }
h1 { font-size: 1.5em; margin: 0 0 .2em; } .day { color: #444; margin: 0 0 1.5em; }
.passage { border-left: 3px solid #999; padding: .2em 0 .2em .8em; margin: 1em 0;
           page-break-inside: avoid; }
.where { font: .85em ui-monospace, monospace; color: #333; }
.text { white-space: pre-wrap; margin: .2em 0 0; }
footer { margin-top: 2.5em; border-top: 1px solid #ccc; padding-top: .5em;
         font-size: .8em; color: #444; overflow-wrap: anywhere; }
@page { margin: 2cm; }
"""
LARGE = """
body { font: 24pt/1.45 Verdana, Arial, sans-serif; color: #000; background: #fff;
       max-width: 40rem; }
.where { font-size: .8em; color: #000; } .day, footer { color: #000; }
.passage { border-left: 6px solid #000; }
"""


def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def page(question: str, doc: dict, row: dict, large: bool) -> str:
    style = STYLE + (LARGE if large else "")
    body = [f"<h1>{esc(question)}</h1><p class=day>Asked {esc(row['ts'][:10])}</p>"]
    if doc["state"] == "sealed":
        body.append("<h2>Your approved answer</h2>"
                    f'<div class=passage><p class=text>{esc(doc["answer"])}</p></div>')  # fmt: skip
    elif doc["state"] == "populated":
        body.append("<h2>What your files say</h2>")
        for s in doc["served"]:
            if not s["echo"]:
                body.append(f'<div class=passage><div class=where>{esc(s["where"])}</div>'
                            f'<p class=text>{esc(s["text"])}</p></div>')  # fmt: skip
    else:
        body.append("<h2>Nothing in your folder holds this</h2>")
        for h in doc.get("look", []):
            tips = " · ".join(esc(h[k]) for k in ("why", "where", "next") if h.get(k))
            body.append(f"<p>{tips}</p>")
    body.append(f"<footer>From your own files, by willow. On your record as row "
                f"{row['n']}, fingerprint {esc(row['hash'][:16])}.</footer>")  # fmt: skip
    return ("<!doctype html><html lang=en><head><meta charset=utf-8>"
            "<meta http-equiv=Content-Security-Policy content=\"default-src 'none'; style-src 'unsafe-inline'\">"
            f"<title>{esc(question)}</title><style>{style}</style></head>"
            f"<body>{''.join(body)}</body></html>\n")  # fmt: skip


def main(argv: list[str]) -> int:
    opts, words, large, it = {}, [], False, iter(argv)
    for a in it:
        if a in ("--box", "--to", "--now"):
            opts[a] = next(it, "")
        elif a == "--large":
            large = True
        else:
            words.append(a)
    if (not opts.get("--box") or not opts.get("--to") or len(words) != 1
            or words[0].startswith("--")):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    box, to = Path(opts["--box"]), Path(opts["--to"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    if to.exists():
        print(f"refused: {to} is already there; it isn't overwritten", file=sys.stderr)
        return kernel.REFUSED
    if not to.parent.is_dir():
        print(
            f"refused: {to.parent} isn't a folder; it isn't made for you",
            file=sys.stderr,
        )
        return kernel.REFUSED
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = kernel.main(["bite", "--box", str(box), *now, words[0]])
    if code == kernel.REFUSED:
        print(err.getvalue() or out.getvalue(), end="", file=sys.stderr)
        return code
    rows, _ = kernel.read(box / "record.jsonl")
    to.write_text(
        page(words[0], json.loads(out.getvalue()), rows[-1], large), encoding="utf-8"
    )
    print(f"written: {to}  (open it in a browser and print it)")
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
