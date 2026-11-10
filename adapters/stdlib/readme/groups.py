"""groups.py: every add-on's place, the one grouping the UI and the lists share. Python 3.9+.

The part an add-on plays in a stack is its role (its card says it, or
`guess_role` works it out from what the card does say), and some roles have
a second level, a group: readers by what their files come from, the ways in
by where you'd be, and suggesting split in two. ui/canvas.py's page and its
`pieces`, ADDONS.md (readme.py) and FILES.md (files.py) all read them from
here, so each shows an add-on in the same place; test_groups.py fails a
built add-on that lands nowhere, or in two places.

Nothing to run: it is read by the others. It reads no file and writes none.
"""

from __future__ import annotations

import re

# ── roles: the part a piece plays in a stack ───────────────────────────────
#: what a piece does in your stack, in the order the page lists them. A card
#: says what it's about (its section); until it says its role too, `role`
#: guesses it from what the card does say, and says which fact it went by.
ROLES = (
    ("reads", "What it reads"),
    ("words", "What words it knows"),
    ("page", "What runs on your page"),
    ("suggests", "What suggests answers"),
    ("ways", "Where you ask from"),
    ("guards", "What guards it"),
    ("makes", "What it makes for elsewhere"),
    ("tools", "Tools you run yourself"),
    ("repo", "Works on willow itself"),
)
#: the ways in, by where you'd be. The editor and assistant ones are filed
#: under Assistants on their cards; as a role, they're ways in like the rest.
WAYS = (
    ("In your terminal", ("shell", "pipe", "plain", "start", "tui", "warm")),
    ("In your editor", ("vscode", "vim", "emacs", "jetbrains", "zed", "cursor",
                        "windsurf", "copilot", "obsidian")),
    ("With an AI assistant", ("claude-code", "codex-cli", "gemini-cli", "opencode",
                              "aider", "mcp", "mcp-lite", "hosts")),
    ("In your browser or on your desktop", ("browse", "launcher", "desktop",
                                            "static-search", "datasette", "kiosk")),
    ("From your phone, by voice or by email", ("telegram-bot", "email-ask",
                                               "home-assistant", "dictate", "wake-gate", "speak",
                                               "qr")),
    ("Several add-ons at once", ("stack", "stack-share", "across")),
)  # fmt: skip
WAY = {n: (i, h) for i, (h, ns) in enumerate(WAYS) for n in ns}
#: the readers, by what the files come from: the second level under `reads`,
#: as the ways in are by where you'd be. A built reader must be in one
#: (test_groups.py); an idea not yet placed goes under OTHER_READERS.
READERS = (
    ("Documents and office files", ("pdf", "ocr", "office", "sheets", "rtf", "text",
                                    "markdown", "asciidoc", "rst", "latex", "equations",
                                    "notation", "clauses", "books", "screenplay",
                                    "man-pages", "mediawiki", "bibtex", "ris", "zotero")),
    ("Mail and chat", ("mail", "apple-mail", "chats", "texts", "discord", "irc", "matrix",
                       "slack", "mastodon", "meta-archive", "x-archive", "reddit", "linkedin")),
    ("Notes, journals and saved pages", ("notes", "org", "day-one", "evernote", "google-keep",
                                         "joplin", "jrnl", "notion", "trello", "readwise",
                                         "karakeep", "pocket", "wallabag", "bookmarks",
                                         "web-pages", "webarchive", "warc", "snapshot",
                                         "shortcuts", "opml")),
    ("Exports from apps and services", ("bank", "robinhood", "orders", "goodreads",
                                        "letterboxd", "listening", "health", "strava",
                                        "location-history", "places", "home-sensors",
                                        "calendar", "family-tree", "pgn", "takeout",
                                        "almanac", "almanac-keep", "oakenscroll")),
    ("Code and data", ("code-comments", "codebase-memory", "dotfiles", "git-history",
                       "gh-json", "jira", "lockfiles", "manifests", "sarif", "sbom",
                       "ci-logs", "logs", "shell-history", "agent-transcript",
                       "corpus-lens", "csv-rows", "json-paths", "jupyter", "parallel",
                       "star-system")),
    ("Media", ("photos", "subtitles", "musicxml", "chordpro")),
)  # fmt: skip
READER = {n: (i, h) for i, (h, ns) in enumerate(READERS) for n in ns}
OTHER_READERS = "Other readers"
SUGGESTS = re.compile(
    r"^suggestions? (from|through)\b|\bsuggests?\b|held until you seal"
    r"|waiting for its own seal|handed in through propose|waiting for suggestions",
    re.I,
)
MODELISH = re.compile(r"\bmodels?\b|\bweights\b|assistant.s suggestions", re.I)


def role(p: dict) -> dict:
    """The role a piece plays, why that one, and the heading it goes under
    inside it (readers by what their files come from, ways in by where you'd
    be, and the two kinds of suggesting).
    A card says its role; `guess_role` is for a willow from before they did."""
    n, line = p["name"], p.get("line", "")
    said = p.get("role", "")
    key, why = (
        (
            said,
            "its card says so"
            if p.get("state") == "built"
            else "its entry on the list says so",
        )  # fmt: skip
        if said in dict(ROLES)
        else guess_role(p)
    )
    group, at = "", 0
    if key == "ways":
        at, group = WAY.get(n, (len(WAYS), "Other ways in"))
    elif key == "reads":
        at, group = READER.get(n, (len(READERS), OTHER_READERS))
    elif key == "suggests":
        at, group = (0, "Models that suggest answers") if SUGGESTS.search(line) else (1, "Checking a model before you trust it")  # fmt: skip
    return {"role": key, "role_why": why, "group": group, "group_at": at}


def guess_role(p: dict) -> tuple[str, str]:
    """A role from what a card without one does say, and which fact it went by."""
    n, line = p["name"], p.get("line", "")
    writes = [w.strip() for w in p.get("writes", "").split(",")]
    if p.get("runs_in") == "repo":
        return "repo", "its card says it runs in willow's own repository"
    if p.get("section") == "Reading more kinds of files":
        return "reads", "its card is filed under reading more kinds of files"
    if n in WAY:
        return "ways", "it's an editor, an assistant or a terminal you ask from"
    if n.startswith("hook") or "hook" in p.get("tags", []):
        return "guards", "it's a hook"
    if SUGGESTS.search(line):
        return "suggests", "its card says it suggests answers, or holds what it makes until you seal it"  # fmt: skip
    if p.get("section") == "Assistants" and MODELISH.search(f"{line} {n}"):
        return "suggests", "its card is about checking a model that suggests answers"
    if p.get("page"):
        return "page", "it runs with nothing but your record, so it can be a step on your page"  # fmt: skip
    if p.get("section") == "Your own words":
        return "words", "its card is filed under your own words"
    if p.get("section") == "Ways to use it" and "to" not in writes:
        return "ways", "its card is filed under ways to use it"
    if "to" in writes:
        return "makes", "its card says it writes where you point it"
    if p.get("state") == "idea":
        return "tools", "it's still an idea, so there's no way yet to tell how it runs"
    return (
        "tools",
        "it needs words or options of its own to run, so you run it yourself",
    )
