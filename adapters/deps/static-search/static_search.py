"""static_search.py: your approved answers as a static site with its own search.

    python adapters/deps/static-search/static_search.py --box DIR --to SITE

Needs Pagefind (MIT), its Python package and its program both pinned in
requirements.txt beside this file:

    pip install -r adapters/deps/static-search/requirements.txt

Each approved answer becomes a page of SITE, `answers/N.html`: the answer,
the reason its suggestion gave, the passages it cited and where they were,
and when you approved it. Only approvals that prove under your key are
written (the kernel's `sealed` and `standing`), as the export add-on does;
a forged one never is. Then Pagefind indexes them, into `SITE/pagefind/`,
and `SITE/index.html` is a search box over them and a list of them all.

No server of its own and nothing online: the pages load only their own
files. A browser won't run Pagefind's search from a file:// address, so
serve the folder as it is from any static host, or on this machine:

    python -m http.server --directory SITE --bind 127.0.0.1

SITE is made, and must not be there yet; its parent must. The same answers
give the same bytes, from the same Pagefind. It writes only under SITE.
Without Pagefind it refuses and names the install; it never skips quietly.
Exit codes, the kernel's: 0 written; 42 no approved answer to write (or one
left out, its proposal file changed); 2 refused.
"""

from __future__ import annotations

import html
import importlib.util
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

INSTALL = "pip install -r adapters/deps/static-search/requirements.txt"
STYLE = """body{font:16px/1.5 system-ui,sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem;color:#1d1d1f;background:#fff}
@media (prefers-color-scheme:dark){body{color:#e8e8ea;background:#16161a}a{color:#9ec5ff}}
h1{font-size:1.4rem}.meta{color:#6b6b73;font-size:.9rem}li{margin:.4rem 0}blockquote{margin:0;white-space:pre-wrap}"""


def approved(box: Path, rows: list[dict]) -> tuple[list[dict], int]:
    """(the approved answers, oldest first; how many approvals were left
    out, their proposal file no longer the bytes the key signed)."""
    places = {}
    for r in rows:
        for s in r.get("served", []):
            places.setdefault(s["id"], s["where"])
    out, left = [], 0
    for subj, row in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, _, why = kernel.standing(box, rows, subj, row)
        if why is not None:
            left += 1
            continue
        out.append({
            "approved": row["ts"],
            "answer": str(prop["data"]),
            "reason": str(prop.get("claim", "")),
            "cites": [places.get(c, c[:12]) for c in prop.get("cites", [])],
        })  # fmt: skip
    return out, left


def page(title: str, body: str, home: str) -> str:
    return (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{html.escape(title)}</title>\n<style>{STYLE}</style>\n{home}</head>\n"
            f"<body>\n{body}\n</body>\n</html>\n")  # fmt: skip


def title_of(a: dict) -> str:
    first = a["answer"].strip().splitlines()[0] if a["answer"].strip() else "An answer"
    return first if len(first) <= 70 else first[:67].rstrip() + "..."


def answer_page(a: dict) -> str:
    cites = "".join(f"<li><code>{html.escape(c)}</code></li>" for c in a["cites"])
    body = (f'<p><a href="../index.html">All answers</a></p>\n<main data-pagefind-body>\n'
            f"<h1>{html.escape(title_of(a))}</h1>\n"
            f"<blockquote>{html.escape(a['answer'])}</blockquote>\n"
            f"<p><strong>Why:</strong> {html.escape(a['reason'])}</p>\n"
            f"<p><strong>From:</strong></p>\n<ul>{cites}</ul>\n"
            f'<p class="meta" data-pagefind-meta="approved">Approved {html.escape(a["approved"][:10])}</p>\n'
            f"</main>")  # fmt: skip
    return page(title_of(a), body, "")


def index_page(answers: list[dict]) -> str:
    items = "".join(
        f'<li><a href="answers/{n}.html">{html.escape(title_of(a))}</a> '
        f'<span class="meta">{html.escape(a["approved"][:10])}</span></li>\n'
        for n, a in enumerate(answers, 1)
    )
    head = ('<link href="pagefind/pagefind-ui.css" rel="stylesheet">\n'
            '<script src="pagefind/pagefind-ui.js"></script>\n')  # fmt: skip
    body = ("<h1>Approved answers</h1>\n<div id=\"search\"></div>\n"
            "<script>window.addEventListener('DOMContentLoaded',()=>"
            "{new PagefindUI({element:'#search',showImages:false})})</script>\n"
            f"<h2>All {len(answers)}</h2>\n<ul>\n{items}</ul>")  # fmt: skip
    return page("Approved answers", body, head)


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    it = iter(argv)
    bad = False
    for a in it:
        if a in ("--box", "--to"):
            opts[a] = next(it, "")
        else:
            bad = True
    if bad or not opts.get("--box") or not opts.get("--to"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if importlib.util.find_spec("pagefind") is None:
        print(f"refused: static-search needs Pagefind: {INSTALL}", file=sys.stderr)
        return kernel.REFUSED
    box, site = Path(opts["--box"]), Path(opts["--to"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    if site.exists() or not site.parent.is_dir():
        print(
            f"refused: {site} must not be there yet, and its folder must",
            file=sys.stderr,
        )
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print("refused:", *breaks, sep="\n  ", file=sys.stderr)
        return kernel.REFUSED
    answers, left = approved(box, rows)
    if left:
        print(f"left out {left} approval{'s' * (left != 1)}: its proposal file "
              "is not the bytes your key signed", file=sys.stderr)  # fmt: skip
    if not answers:
        print("No approved answer to write.")
        return kernel.ESCALATE
    (site / "answers").mkdir(parents=True)
    for n, a in enumerate(answers, 1):
        (site / "answers" / f"{n}.html").write_text(answer_page(a), encoding="utf-8")
    (site / "index.html").write_text(index_page(answers), encoding="utf-8")
    got = subprocess.run([sys.executable, "-m", "pagefind", "--site", str(site)],
                         capture_output=True, text=True)  # fmt: skip
    if got.returncode != 0 or not (site / "pagefind" / "pagefind-ui.js").is_file():
        said = (got.stderr or got.stdout).strip().splitlines()[-1:] or ["no index made"]
        print(f"refused: Pagefind failed: {said[0][:200]}", file=sys.stderr)
        return kernel.REFUSED
    print(f"wrote {len(answers)} answers to {site}, searchable")
    print(f"open: python -m http.server --directory {site} --bind 127.0.0.1")
    return kernel.ESCALATE if left else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
