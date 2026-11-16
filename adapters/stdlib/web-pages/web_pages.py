"""web_pages.py: saved web pages as their readable text, with the address
they came from.

    python adapters/stdlib/web-pages/web_pages.py mirror --from FOLDER --to MIRROR [--body-only]

The kernel reads a web page as the words it shows, but a page saved from a
browser is one long line of markup, and a .mhtml file is a whole message of
parts. This writes, for each .html, .htm, .mhtml or .mht under FOLDER,
`MIRROR/<same relative path>.txt`: a first line saying where the page came
from, then the page's blocks (paragraphs, headings, list items), one
paragraph each, so an answer lands on the paragraph that says it.

    address: https://example.org/terms

The address is the first of: the `saved from url=` note a browser writes in
an .html it saves (not `about:internet`, Internet Explorer's zone marker);
an .mhtml's `Snapshot-Content-Location` or its page's `Content-Location`;
the page's canonical link; its `og:url`. A page that
says none of them gets `address: not in the file`, never a guess.

With `--body-only` a page's menus are left out: any nav, footer or aside
element, and any element whose role says navigation, contentinfo or
complementary, with everything inside it. Without it nothing is left out, so
the same folder gives the same bytes as before. A header is kept (an
article's title is often in one), and so is an element that never closes:
what the rule cannot cut cleanly stays in.

A page is read as UTF-8, or as the charset its own `<meta charset>` names
in its first 4,096 bytes; an .mhtml's page in the charset its part names,
else the same way. The contract every reader shares: hidden
files and folders are skipped; nothing is written inside FOLDER; the same
folder gives the same bytes; a file it can't read is skipped and counted.
Exit codes: 0 wrote at least one file, 42 nothing to read, 2 refused.
"""

from __future__ import annotations

import codecs
import email
import email.policy
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1] / "clauses"))
import clauses  # noqa: E402
import kernel  # noqa: E402

READS = (".html", ".htm", ".mhtml", ".mht")
SAVED = re.compile(r"<!--\s*saved from url=\(\d+\)(\S+?)\s*-->", re.I)
CHARSET = re.compile(rb"<meta[^>]+charset=[\"']?([A-Za-z0-9_\-]+)", re.I)
CANONICAL = (
    re.compile(r"<link[^>]+rel=[\"']?canonical[\"']?[^>]*href=[\"']([^\"']+)", re.I),
    re.compile(r"<link[^>]+href=[\"']([^\"']+)[\"'][^>]*rel=[\"']?canonical", re.I),
    re.compile(r"<meta[^>]+property=[\"']og:url[\"'][^>]*content=[\"']([^\"']+)", re.I),
    re.compile(r"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]*property=[\"']og:url", re.I),
)


CHROME = ("nav", "footer", "aside")
CHROME_ROLES = ("navigation", "contentinfo", "complementary")


class Chrome(HTMLParser):
    """The spans of a page that are its menus: an element that is a nav, a
    footer or an aside, or says its role is navigation, contentinfo or
    complementary, from its start tag to its own end tag (an element of the
    same name inside it is counted, so the span ends with the right one).
    An element that never closes is not a span: its words are kept."""

    def __init__(self, page: str):
        super().__init__(convert_charrefs=False)
        self.page = page
        self.starts = [0] + [i + 1 for i, c in enumerate(page) if c == "\n"]
        self.spans: list[tuple[int, int]] = []
        self.open: list | None = None  # [tag, depth, start] of the span being read

    def _here(self) -> int:
        line, col = self.getpos()
        return self.starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if self.open:
            if tag == self.open[0]:
                self.open[1] += 1
            return
        roles = (dict(attrs).get("role") or "").lower().split()
        if tag in CHROME or any(r in CHROME_ROLES for r in roles):
            self.open = [tag, 1, self._here()]

    def handle_endtag(self, tag):
        if not self.open or tag != self.open[0]:
            return
        self.open[1] -= 1
        if self.open[1] == 0:
            at = self.page.find(">", self._here())
            if at >= 0:
                self.spans.append((self.open[2], at + 1))
            self.open = None


def without_chrome(page: str) -> str:
    """The page with its menus cut out, a line break where each was."""
    p = Chrome(page)
    p.feed(page)
    p.close()
    out, at = [], 0
    for a, b in p.spans:
        out += [page[at:a], "\n"]
        at = b
    return "".join(out) + page[at:]


def decode(raw: bytes) -> str | None:
    """A saved page's text: UTF-8, or the charset its own meta tag names."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    m = CHARSET.search(raw[:4096])
    if not m:
        return None
    try:
        return raw.decode(codecs.lookup(m.group(1).decode("ascii")).name)
    except (LookupError, UnicodeDecodeError):
        return None


def mhtml(raw: bytes) -> tuple[str, str] | None:
    """An .mhtml's page and the address it says, or None. The page is read
    in the charset its part names, else as a saved .html is: Chrome names
    none on the part, only in the page's own meta tag."""
    msg = email.message_from_bytes(raw, policy=email.policy.default)
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            body = part.get_payload(decode=True) or b""
            named = part.get_content_charset()
            if named:
                try:
                    page = body.decode(codecs.lookup(named).name)
                except (LookupError, UnicodeDecodeError):
                    return None
            elif (page := decode(body)) is None:
                return None
            where = (
                msg.get("Snapshot-Content-Location")
                or part.get("Content-Location")
                or ""
            )
            return page, str(where).strip()
    return None


def address(page: str, said: str = "") -> str:
    """Where the page came from, by the first thing that says so. A
    saved-from note of `about:internet` is Internet Explorer's zone marker
    (the Mark of the Web), not an address, so it says nothing here."""
    m = SAVED.search(page[:4096])
    if m and not m.group(1).lower().startswith("about:"):
        return m.group(1)
    if said:
        return said
    for pat in CANONICAL:
        if m := pat.search(page):
            return m.group(1)
    return ""


def as_text(page: str, said: str = "", body_only: bool = False) -> str:
    where = address(page, said) or "not in the file"
    shown = without_chrome(page) if body_only else page
    blocks = [b for _, b in clauses.blocks_of_html(shown)]
    return (
        "".join(s + "\n\n" for s in [f"address: {where}", *blocks]).rstrip("\n") + "\n"
    )


def mirror(src: Path, dst: Path, body_only: bool = False) -> int:
    src, dst = src.resolve(), dst.resolve()
    if not src.is_dir():
        print(f"refused: {src} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    if clauses.inside(dst, src) or clauses.inside(src, dst):
        print("refused: the mirror and the folder can't be inside each other",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    wrote = skipped = 0
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if not p.is_file() or p.suffix.lower() not in READS:
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        raw = p.read_bytes()
        if p.suffix.lower() in (".mhtml", ".mht"):
            got = mhtml(raw)
        else:
            page = decode(raw)
            got = (page, "") if page is not None else None
        if got is None:
            skipped += 1
            continue
        out = dst / (str(rel) + ".txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(as_text(*got, body_only=body_only))
        wrote += 1
    print(f"wrote {wrote} files to {dst}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


def main(argv: list[str]) -> int:
    body_only = argv[5:] == ["--body-only"]
    if (
        len(argv) in (5, 6)
        and (len(argv) == 5 or body_only)
        and argv[0] == "mirror"
        and argv[1] == "--from"
        and argv[3] == "--to"
    ):
        return mirror(Path(argv[2]), Path(argv[4]), body_only)
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
