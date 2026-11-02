r"""bookmarks.py: browser bookmarks and history as dated passages. Python 3.9+.

    python adapters/stdlib/bookmarks/bookmarks.py mirror --from FOLDER --to MIRROR

Walks FOLDER (hidden folders and files skipped) and reads each file that is,
by what it holds rather than its name, one of:

- the bookmark HTML export every browser writes (`<!DOCTYPE
  NETSCAPE-Bookmark-file-1>`), with its folders, tags and `<DD>` descriptions;
- a Firefox bookmarks backup, `.json` or the compressed `.jsonlz4`;
- the `Bookmarks` file of Chrome, Chromium, Edge or Brave;
- a copy of Firefox's `places.sqlite` (its bookmarks and history) or of
  Chrome's `History`, opened read-only so nothing is written beside it.

Any other file is left alone and not counted. Each bookmark is one passage, in
the browser's own order: the day it was added, its title, its address, its
folder, its tags and its description:

    2024-03-02  Tomato growing guide
    example.org/tomatoes
    in Garden / Seeds
    #garden, #veg
    Staking and pruning, step by step.

and each page in a history is one passage, oldest last visit first: its last
visit, title, address, how many visits, and the days it was visited (the
newest twenty, or fewer if a long address would cut the passage in two; the
older days counted after a +):

    2024-03-05 15:02  Tomato blight: what to do
    example.org/blight
    ×3  2024-03-01, 2024-03-05

No word is added that would stand on every passage, since a question pairing
that word with a topic the folder lacks would then be answered: no labels, no
`https://` or `www.` before an address, no browser's root folder (the menu,
the toolbar, other bookmarks), and nothing in place of a missing date or title.
Times are UTC, read as each format stores them: the HTML export in Unix
seconds, Firefox in microseconds since 1970, Chrome in microseconds since 1601.

Each file is written to MIRROR at the same relative path with `.txt` added; a
mirror bigger than the kernel reads from one file (`kernel.MAX_FILE`) is cut
between passages into `NAME.txt`, `NAME.part2.txt` and on. FOLDER is only read.
A file that is one of these but cannot be read, or holds no bookmark or page,
is skipped and counted.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import json
import os
import sqlite3
import struct
import sys
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: bookmarks.py mirror --from FOLDER --to MIRROR"
HEAD = 8192  # bytes looked at to tell what a file is
DAYS = 20  # visit days listed for one page; older ones are counted
UNIX = datetime(1970, 1, 1, tzinfo=timezone.utc)
WINDOWS = datetime(1601, 1, 1, tzinfo=timezone.utc)  # Chrome's epoch
ERRORS = (OSError, UnicodeDecodeError, ValueError, IndexError, sqlite3.Error)

#: a browser's own root folders: they hold every bookmark, so their names are
#: not written (a word on every passage answers questions the folder can't)
ROOTS = ("menu________", "toolbar_____", "unfiled_____", "mobile______", "root________")
#: the attributes the HTML export marks the toolbar and other bookmarks with
ROOT_MARKS = ("personal_toolbar_folder", "unfiled_bookmarks_folder")


# ── times ───────────────────────────────────────────────────────────────────
def moment(value: object, epoch: datetime, per_second: int) -> datetime | None:
    """`value` units of 1/`per_second` second after `epoch`; None for zero,
    nothing, or a time no calendar holds."""
    try:
        n = int(value)  # Chrome writes its times as strings of digits
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return None
    try:
        return epoch + timedelta(microseconds=n * (1_000_000 // per_second))
    except OverflowError:
        return None


def day(t: datetime | None) -> str:
    return t.strftime("%Y-%m-%d") if t else ""


def address(url: object) -> str:
    """A URL without the `https://` and `www.` that nearly every one has."""
    u = one_line(url)
    if u.startswith("https://"):
        u = u[len("https://") :]
        u = u[len("www.") :] if u.startswith("www.") else u
    return u


def one_line(value: object) -> str:
    return " ".join(value.split()) if isinstance(value, str) else ""


# ── a bookmark, a page ──────────────────────────────────────────────────────
def bookmark(
    when: datetime | None, title: str, url: str, folder: list, tags: list, about: str
) -> str:
    head = "  ".join(x for x in (day(when), one_line(title)) if x)
    lines = [head] if head else []
    lines.append(address(url))
    path = " / ".join(f for f in folder if f)
    if path:
        lines.append(f"in {path}")  # "in" is a word the kernel never counts
    tags = [one_line(t) for t in tags if one_line(t)]
    if tags:
        lines.append(", ".join("#" + t for t in tags))
    if one_line(about):
        lines.append(one_line(about))
    return "\n".join(lines)


def page(title: str, url: str, visits: list, count: int, last: datetime | None) -> str:
    """One page of a history: its visits' times, or, when the browser kept
    none, its own count and last visit."""
    if visits:
        visits = sorted(visits)
        count, last = len(visits), visits[-1]
    days = sorted({day(t) for t in visits})
    when = last.strftime("%Y-%m-%d %H:%M") if last else ""
    head = "  ".join(x for x in (when, one_line(title)) if x)
    lines = ([head] if head else []) + [address(url)]
    said = f"×{count}"
    shown = days[-DAYS:]
    while shown:  # as many of the newest as keep the page one passage for the kernel
        more = len(days) - len(shown)
        said = f"×{count}  " + ", ".join(shown) + (f" +{more}" if more else "")
        if len("\n".join(lines + [said])) <= kernel.MAX_CHUNK or len(shown) == 1:
            break
        shown = shown[1:]
    return "\n".join(lines + [said])


# ── the HTML export ─────────────────────────────────────────────────────────
class Netscape(HTMLParser):
    """The bookmark HTML export: folders are <H3> then a <DL>, bookmarks are
    <A HREF ADD_DATE TAGS>, and a <DD> after one is its description."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.path: list[str] = []
        self.heading = ""  # an <H3>'s text, for the <DL> that follows
        self.root = False  # the heading is the export's own: <H1>, the toolbar
        self.text: list[str] | None = None  # text being gathered
        self.into = ""  # what that text is: h, a or dd
        self.mark: dict | None = None  # the bookmark a <DD> would describe

    def done(self) -> None:
        if self.mark is not None:
            m = self.mark
            self.out.append(bookmark(m["when"], m["title"], m["url"], m["folder"], m["tags"], m["about"]))  # fmt: skip
        self.mark = None

    def close_text(self) -> str:
        text, self.text, self.into = " ".join(self.text or []), None, ""
        return one_line(text)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if self.into == "dd" and tag in ("dt", "dl", "hr", "h3", "a"):
            self.mark["about"] = self.close_text()
        if tag in ("dt", "dl", "h1", "h3", "hr"):
            self.done()
        if tag in ("h1", "h3"):
            self.text, self.into = [], "h"
            self.root = tag == "h1" or any(k in ROOT_MARKS for k, _ in attrs)
        elif tag == "dl":
            self.path.append(self.heading)
            self.heading = ""
        elif tag == "a":
            a = dict(attrs)
            if a.get("href") and not a["href"].startswith("place:"):
                self.done()
                self.mark = {
                    "when": moment(a.get("add_date"), UNIX, 1),
                    "url": a["href"],
                    "folder": list(self.path),
                    "tags": (a.get("tags") or "").split(","),
                    "about": "",
                }
                self.text, self.into = [], "a"
        elif tag == "dd" and self.mark is not None:
            self.text, self.into = [], "dd"

    def handle_endtag(self, tag: str) -> None:
        if tag in ("h1", "h3") and self.into == "h":
            text = self.close_text()
            self.heading = "" if self.root else text
        elif tag == "a" and self.into == "a":
            self.mark["title"] = self.close_text()
        elif tag == "dl":
            if self.into == "dd":
                self.mark["about"] = self.close_text()
            self.done()
            if self.path:
                self.path.pop()

    def handle_data(self, data: str) -> None:
        if self.text is not None:
            self.text.append(data)


def netscape(text: str) -> list[str]:
    p = Netscape()
    p.feed(text)
    p.close()
    if p.into == "dd":
        p.mark["about"] = p.close_text()
    p.done()
    return p.out


# ── Firefox's backup and Chrome's Bookmarks ─────────────────────────────────
def firefox_json(node: dict, folder: list, out: list) -> None:
    kind = node.get("type")
    if kind == "text/x-moz-place-container":
        if node.get("root") == "tagsFolder":
            return  # each bookmark carries its own tags
        name = "" if node.get("root") else one_line(node.get("title"))
        for child in node.get("children") or []:
            if isinstance(child, dict):
                firefox_json(child, folder + [name], out)
    elif kind == "text/x-moz-place" and isinstance(node.get("uri"), str):
        if node["uri"].startswith("place:"):
            return
        about = next((a.get("value") for a in node.get("annos") or []
                      if isinstance(a, dict) and a.get("name") == "bookmarkProperties/description"), "")  # fmt: skip
        tags = node.get("tags") if isinstance(node.get("tags"), str) else ""
        when = moment(node.get("dateAdded"), UNIX, 1_000_000)
        out.append(bookmark(when, node.get("title"), node["uri"], folder, tags.split(","), about))  # fmt: skip


def chrome_json(node: dict, folder: list, out: list) -> None:
    if node.get("type") == "url" and isinstance(node.get("url"), str):
        when = moment(node.get("date_added"), WINDOWS, 1_000_000)
        out.append(bookmark(when, node.get("name"), node["url"], folder, [], ""))
    elif node.get("type") == "folder":
        for child in node.get("children") or []:
            if isinstance(child, dict):
                chrome_json(child, folder + [one_line(node.get("name"))], out)


def from_json(data: bytes) -> list[str] | None:
    """A Firefox backup's or Chrome's bookmarks; None if the JSON is neither."""
    doc = json.loads(data.decode("utf-8-sig"))
    if not isinstance(doc, dict):
        return None
    out: list[str] = []
    roots = doc.get("roots")
    if isinstance(roots, dict) and {"bookmark_bar", "other"} <= set(roots):
        for key in sorted(roots, key=lambda k: (k != "bookmark_bar", k != "other", k)):
            root = roots[key] if isinstance(roots[key], dict) else {}
            for child in root.get("children") or []:
                if isinstance(child, dict):
                    chrome_json(child, [], out)
        return out
    if doc.get("type") == "text/x-moz-place-container":
        firefox_json(doc, [], out)
        return out
    return None


def lz4_block(src: bytes, size: int) -> bytes:
    """An LZ4 block decompressed (the format Firefox's .jsonlz4 holds)."""
    out = bytearray()
    i = 0
    while i < len(src):
        token = src[i]
        i += 1
        run = token >> 4
        if run == 15:
            while True:
                i += 1
                run += src[i - 1]
                if src[i - 1] != 255:
                    break
        out += src[i : i + run]
        i += run
        if i >= len(src):
            break
        back = src[i] | src[i + 1] << 8
        i += 2
        if not 0 < back <= len(out):
            raise ValueError("an LZ4 match before the start")
        length = token & 15
        if length == 15:
            while True:
                i += 1
                length += src[i - 1]
                if src[i - 1] != 255:
                    break
        length += 4
        start = len(out) - back
        for k in range(length):  # a match may overlap what it writes
            out.append(out[start + k])
    if len(out) != size:
        raise ValueError("an LZ4 block of the wrong size")
    return bytes(out)


def mozlz4(data: bytes) -> bytes:
    (size,) = struct.unpack("<I", data[8:12])
    return lz4_block(data[12:], size)


# ── the history databases ───────────────────────────────────────────────────
def columns(con: sqlite3.Connection, table: str) -> set:
    return {r[1] for r in con.execute(f"PRAGMA table_info({table})")}


def firefox_places(con: sqlite3.Connection) -> list[str]:
    out: list[str] = []
    about = "description" in columns(con, "moz_places")
    places = {
        r[0]: r[1:]
        for r in con.execute(
            "SELECT id, url, title, visit_count, last_visit_date, hidden"
            + (", description" if about else ", NULL")
            + " FROM moz_places"
        )
    }
    if "moz_bookmarks" in tables(con):
        rows = con.execute(
            "SELECT b.id, b.type, b.fk, b.parent, b.title, b.dateAdded, b.guid "
            "FROM moz_bookmarks b ORDER BY b.parent, b.position, b.id"
        ).fetchall()
        kids: dict = {}
        for r in rows:
            kids.setdefault(r[3], []).append(r)
        tags: dict = {}
        for tag_folder in [r for r in rows if r[6] == "tags________"]:
            for t in kids.get(tag_folder[0], []):
                for b in kids.get(t[0], []):
                    tags.setdefault(b[2], []).append(one_line(t[4]))

        def walk(parent: int, folder: list) -> None:
            for bid, kind, fk, _, title, added, guid in kids.get(parent, []):
                if guid == "tags________":
                    continue
                if kind == 2:
                    walk(bid, folder + ["" if guid in ROOTS else one_line(title)])
                elif kind == 1 and fk in places:
                    url = places[fk][0] or ""
                    if url.startswith("place:"):
                        continue
                    when = moment(added, UNIX, 1_000_000)
                    out.append(bookmark(when, title or places[fk][1], url, folder,
                                        sorted(set(tags.get(fk, []))), places[fk][5] or ""))  # fmt: skip

        for r in rows:
            if r[6] == "root________":
                walk(r[0], [])
    visits: dict = {}
    for place, when, kind in con.execute(
        "SELECT place_id, visit_date, visit_type FROM moz_historyvisits ORDER BY id"
    ):
        t = moment(when, UNIX, 1_000_000)
        kept = visits.setdefault(place, [])  # a page with visits kept: none are guessed
        if t and kind not in (4, 8):  # embedded and framed pages: not visits you made
            kept.append(t)
    pages = []
    for pid, (url, title, count, last, hidden, _) in places.items():
        if hidden or not url or url.startswith("place:"):
            continue
        last_t = moment(last, UNIX, 1_000_000)
        if visits.get(pid) or (pid not in visits and count and last_t):
            pages.append((title, url, visits.get(pid, []), count or 0, last_t))
    return out + history(pages)


def chrome_history(con: sqlite3.Connection) -> list[str]:
    visits: dict = {}
    for url_id, when, transition in con.execute(
        "SELECT url, visit_time, transition FROM visits ORDER BY id"
    ):
        t = moment(when, WINDOWS, 1_000_000)
        kept = visits.setdefault(url_id, [])
        if t and (transition or 0) & 0xFF not in (3, 4):  # a page's frames
            kept.append(t)
    hidden = "hidden" in columns(con, "urls")
    pages = []
    for uid, url, title, count, last, hid in con.execute(
        "SELECT id, url, title, visit_count, last_visit_time, "
        + ("hidden" if hidden else "0")
        + " FROM urls ORDER BY id"
    ):
        last_t = moment(last, WINDOWS, 1_000_000)
        if (
            url
            and not hid
            and (visits.get(uid) or (uid not in visits and count and last_t))
        ):
            pages.append((title, url, visits.get(uid, []), count or 0, last_t))
    return history(pages)


def history(pages: list) -> list[str]:
    """Each page as a passage, oldest last visit first."""

    def last(p: tuple) -> tuple:
        when = max(p[2]) if p[2] else p[4]
        return (when or UNIX, p[1], one_line(p[0]))

    return [page(*p) for p in sorted(pages, key=last)]


def tables(con: sqlite3.Connection) -> set:
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}  # fmt: skip


def from_sqlite(path: Path) -> list[str] | None:
    """A copy of places.sqlite or History, opened read-only and immutable so no
    journal is written beside it; None if it is neither."""
    uri = f"file:{quote(path.resolve().as_posix())}?mode=ro&immutable=1"
    con = sqlite3.connect(uri, uri=True)
    try:
        have = tables(con)
        if {"moz_places", "moz_historyvisits"} <= have:
            return firefox_places(con)
        if {"urls", "visits"} <= have:
            return chrome_history(con)
        return None
    finally:
        con.close()


# ── one file ────────────────────────────────────────────────────────────────
def kind(head: bytes) -> str:
    """What a file is, from its first bytes: '' when it is none of these."""
    if head.startswith(b"SQLite format 3\0"):
        return "sqlite"
    if head.startswith(b"mozLz40\0"):
        return "mozlz4"
    start = head.lstrip(b"\xef\xbb\xbf \t\r\n")  # a file that only names one is not one
    if start[:35].lower() == b"<!doctype netscape-bookmark-file-1>":
        return "html"
    if start.startswith(b"{") and (b'"text/x-moz-place' in head or b'"roots"' in head):
        return "json"
    return ""


def convert(path: Path, what: str) -> str | None:
    """The mirror text of a file of kind `what`; None if it holds nothing, or
    is not a browser's after all."""
    if what == "sqlite":
        found = from_sqlite(path)
    elif what == "html":
        found = netscape(path.read_bytes().decode("utf-8-sig"))
    elif what == "mozlz4":
        found = from_json(mozlz4(path.read_bytes()))
    else:
        found = from_json(path.read_bytes())
    if found is None:
        return None
    return "\n\n".join(found) + "\n" if found else ""


def parts(text: str, limit: int = kernel.MAX_FILE) -> list[str]:
    """`text` cut between passages into pieces of at most `limit` bytes."""
    out: list[str] = []
    piece = ""
    for para in text.split("\n\n"):
        para = para.strip("\n") + "\n"
        if len(para.encode("utf-8")) > limit:
            para = para.encode("utf-8")[: limit - 1].decode("utf-8", "ignore") + "\n"
        if piece and len((piece + "\n" + para).encode("utf-8")) > limit:
            out.append(piece)
            piece = ""
        piece = piece + "\n" + para if piece else para
    if piece:
        out.append(piece)
    return out


def _part_name(name: str, n: int) -> str:
    return f"{name}.txt" if n == 1 else f"{name}.part{n}.txt"


def _sources(folder: Path) -> list[Path]:
    """Every file under `folder`, sorted by relative path. Hidden folders and
    files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            with path.open("rb") as f:
                what = kind(f.read(HEAD))
            if not what:
                continue
            text = convert(path, what)
            if text is None:
                continue  # an SQLite file or JSON that is not a browser's
            if not text:
                skipped += 1
                continue
            folder = dst.joinpath(rel.parent)
            folder.mkdir(parents=True, exist_ok=True)
            pieces = parts(text)
            for n, piece in enumerate(pieces, 1):
                (folder / _part_name(rel.name, n)).write_bytes(piece.encode("utf-8"))
            n = len(pieces) + 1
            while (folder / _part_name(rel.name, n)).is_file():
                (folder / _part_name(rel.name, n)).unlink()
                n += 1
        except ERRORS:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src = Path(opts["--from"]).resolve()
    dst = Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
