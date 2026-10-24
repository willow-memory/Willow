"""repo_pile.py: public repositories made into a box you can ask. Python 3.9+.

    python adapters/stdlib/repo-pile/repo_pile.py build --to BASE --repos LIST --key FILE
        [--notes FILE ...] [--words FILE] [--source URL] [--no-code-index]
    python adapters/stdlib/repo-pile/repo_pile.py ask --base BASE --questions FILE
        [--rank kernel|bm25] [--words FILE] [--top N] [--todo] [--raw]
    python adapters/stdlib/repo-pile/repo_pile.py bite --base BASE "your question"
    python adapters/stdlib/repo-pile/repo_pile.py quote --base BASE "an exact quote" [--raw]
    python adapters/stdlib/repo-pile/repo_pile.py report --base BASE [--days N]
    python adapters/stdlib/repo-pile/repo_pile.py check --base BASE
    python adapters/stdlib/repo-pile/repo_pile.py backup --base BASE --to FOLDER

LIST is one owner/repo a line; # starts a comment, and a line that isn't
owner/repo is skipped and said. `build` writes only under BASE:

    1. clone     each repo, shallow, from --source (https://github.com) into
                 BASE/repos/owner-repo, by the git program
    2. licence   each repo's own top-level licence files. It is kept only when
                 one of them grants a licence an Apache-2.0 project can use
                 (Apache, MIT, BSD, ISC, zlib, CC0, Unlicense, PSF, CC-BY) and
                 holds no copyleft text. The rest are left out, and why goes
                 in BASE/REJECTED.txt
    3. pile      BASE/pile: each kept repo's docs (READMEs, agent notes,
                 licences, docs/ folders) and each --notes file
    4. secrets   secrets-audit over the pile: where, never the value
    5. box       the kernel's own init: BASE/box, over the pile, with --key
                 (the kernel makes it if it's missing) and --words
    6. changed   changed: one fingerprint row of what the pile holds
    7. index     scan: BASE/index-pile, and BASE/index-code over the whole
                 source unless --no-code-index
    8. verify    the kernel's own verify

After it, each verb is willow's own add-ons over BASE:

    ask      scan over both indexes, a list of questions in seconds;
             --rank bm25 points where to look, --todo adds marked lines
    bite     privacy's bite: one question through the box, on the record
    quote    quote-check: is this exact quote in the pile, and where
    report   digest, again, stale, export --log, history, then verify
    check    xref, todo and secrets-audit over the pile, as counts
    backup   backup: the record zipped and checked into FOLDER

What ask and quote print goes through privacy's scrub unless --raw, since
other people's docs hold their addresses and keys. Approving an answer is
the person's: this never seals, and never reads the key.

Exit codes, the kernel's: 0 something held; 42 nothing to build, or nothing
held a question; 2 refused, or a bad command line.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

SOURCE = "https://github.com"
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
# Licence texts an Apache-2.0 project can use, by a phrase each carries.
KEEP = {
    "Apache-2.0": "apache license",
    "MIT": "permission is hereby granted, free of charge",
    "BSD": "redistribution and use in source and binary forms",
    "ISC": "permission to use, copy, modify, and/or distribute",
    "Zlib": "altered source versions must be plainly marked",
    "CC0": "cc0 1.0 universal",
    "Unlicense": "free and unencumbered software released into the public domain",
    "PSF": "python software foundation license",
    "CC-BY": "creative commons attribution",
}
# Copyleft or source-available texts: a file holding one grants nothing here.
REFUSE = {
    "GPL": "gnu general public license",
    "LGPL": "gnu lesser general public license",
    "AGPL": "gnu affero general public license",
    "MPL": "mozilla public license",
    "SSPL": "server side public license",
    "BUSL": "business source license",
    "CC-BY-SA": "sharealike",
    "CC-BY-NC": "noncommercial",
}
# a licence file by its name: LICENSE, COPYING.md, LICENSE-MIT, apache-2.0.LICENSE
LICENCE_FILE = re.compile(
    r"(?:^|[.\-_])(?:licen[cs]e|copying|unlicense)(?:[.\-_]|$)", re.I
)
DOCS = (".md", ".txt", ".rst")
SKIP = {"node_modules", "vendor", "third_party", "target", "tests", "test",
        "fixtures", "testdata"}  # fmt: skip
TAKES = {
    "build": {"--to", "--repos", "--key", "--notes", "--words", "--source"},
    "ask": {"--base", "--questions", "--rank", "--words", "--top"},
    "bite": {"--base"},
    "quote": {"--base"},
    "report": {"--base", "--days"},
    "check": {"--base"},
    "backup": {"--base", "--to"},
}
NEEDS = {
    "build": {"--to", "--repos", "--key"},
    "ask": {"--base", "--questions"},
    "backup": {"--base", "--to"},
}
FLAGS = {"build": {"--no-code-index"}, "ask": {"--todo", "--raw"}, "quote": {"--raw"}}
WORDS = {"bite": 1, "quote": 1}  # verbs that take one more argument, the words


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def say(step: str, msg: str) -> None:
    print(f"[{step}] {msg}", flush=True)


def addon(name: str) -> Path:
    return STDLIB / name / f"{name.replace('-', '_')}.py"


def run(argv: list, text_in: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([str(a) for a in argv], input=text_in, capture_output=True,
                          text=True)  # fmt: skip


def py(script: Path, *argv) -> subprocess.CompletedProcess:
    return run([sys.executable, script, *argv])


def first(r: subprocess.CompletedProcess, last: bool = False) -> str:
    lines = (r.stdout.strip() or r.stderr.strip()).splitlines() or ["(nothing said)"]
    return lines[-1] if last else lines[0]


def licences(repo: Path) -> tuple[list[str], list[str]]:
    """The licences a repo's own top-level licence files grant alone, and the
    copyleft ones they carry. A file holding both grants nothing here."""
    grant, copyleft = set(), set()
    for f in sorted(repo.iterdir()):
        if not f.is_file() or not LICENCE_FILE.search(f.name):
            continue
        text = " ".join(f.read_text(encoding="utf-8", errors="replace").lower().split())
        bad = {k for k, p in REFUSE.items() if p in text}
        copyleft |= bad
        if not bad:
            grant |= {k for k, p in KEEP.items() if p in text}
    return sorted(grant), sorted(copyleft)


def wanted(listing: Path) -> list[str]:
    """owner/repo names from the list, in its order, once each."""
    names = []
    lines = listing.read_text(encoding="utf-8", errors="replace").splitlines()
    for n, line in enumerate(lines, 1):
        name = line.split("#")[0].strip()
        if not name:
            continue
        if not REPO.fullmatch(name):
            say("list", f"line {n} skipped: not owner/repo")
        elif name not in names:
            names.append(name)
    return names


def clone_and_gate(base: Path, names: list[str], source: str) -> list[Path]:
    """Steps 1 and 2: the clones kept, by name. A clone already there is
    gated again, never fetched again."""
    repos, staging, kept, out = base / "repos", base / "staging", [], []
    repos.mkdir(exist_ok=True)
    for name in names:
        dest = repos / name.replace("/", "-")
        if not dest.exists():
            shutil.rmtree(staging, ignore_errors=True)
            r = run(["git", "clone", "-q", "--depth", "1", f"{source}/{name}", staging])
            if r.returncode:
                out.append(f"{name}\tnot cloned: {first(r, last=True)}")
                say("clone", f"{name}: not cloned")
                continue
            staging.rename(dest)
        grant, copyleft = licences(dest)
        if grant:  # a permissive grant of its own, so a dual licence passes
            kept.append(dest)
            say("licence", f"{name}: kept ({', '.join(grant)})")
        else:
            why = (
                f"copyleft: {', '.join(copyleft)}"
                if copyleft
                else "no licence it can read"
            )
            out.append(f"{name}\t{why}")
            shutil.rmtree(dest)
            say("licence", f"{name}: left out ({why})")
    (base / "REJECTED.txt").write_text("".join(f"{r}\n" for r in out), encoding="utf-8")
    return kept


def build_pile(base: Path, kept: list[Path], notes: list[Path]) -> Path:
    """Step 3: rebuilt whole each run, so it holds exactly what is kept now."""
    pile = base / "pile"
    shutil.rmtree(pile, ignore_errors=True)
    (pile / "repos").mkdir(parents=True)
    n = 0
    for repo in kept:
        for root, dirs, files in os.walk(repo):
            dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP)
            rel = Path(root).relative_to(repo.parent)
            if len(rel.parts) > 3 and "docs" not in rel.parts:
                continue
            for f in sorted(files):
                src = Path(root) / f
                doc = f.lower().endswith(DOCS) or bool(LICENCE_FILE.search(f))
                if doc and src.stat().st_size <= kernel.MAX_FILE:
                    (pile / "repos" / rel).mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, pile / "repos" / rel / f)
                    n += 1
    for note in notes:
        shutil.copyfile(note, pile / note.name)
    say("pile", f"{n} docs from {len(kept)} repos, and {len(notes)} notes")
    return pile


def build(o: dict) -> int:
    base, listing = Path(o["--to"]).resolve(), Path(o["--repos"])
    notes = [Path(n) for n in o.get("--notes", [])]
    if not listing.is_file() or any(not n.is_file() for n in notes):
        print("refused: the repo list and each note must be a file", file=sys.stderr)
        return kernel.REFUSED
    if not base.parent.is_dir():
        print(f"refused: {base.parent} is not a folder; make it first", file=sys.stderr)
        return kernel.REFUSED
    names = wanted(listing)
    if not names and not notes:
        say("list", "nothing to build: no owner/repo in the list, and no notes")
        return kernel.ESCALATE
    if names and shutil.which("git") is None:
        print("refused: cloning needs the git program; install git", file=sys.stderr)
        return kernel.REFUSED
    base.mkdir(exist_ok=True)
    kept = clone_and_gate(base, names, o.get("--source", SOURCE).rstrip("/"))
    if not kept and not notes:
        say("pile", "nothing to build: no repo was kept")
        return kernel.ESCALATE
    pile = build_pile(base, kept, notes)
    r = py(addon("secrets-audit"), "--from", pile)
    for line in r.stdout.strip().splitlines():
        if line.strip():
            say("secrets", line.strip())
    box = base / "box"
    if not (box / "kernel.json").exists():
        init = ["init", "--box", box, "--pile", pile, "--key", o["--key"]]
        r = py(STDLIB.parents[1] / "kernel.py", *init, *words_for(o))
        say("box", first(r))
        if r.returncode:
            return r.returncode
    else:
        say("box", "already made; its words list was set then")
    say("changed", first(py(addon("changed"), "--box", box)))
    indexes = [("index-pile", pile)]
    if "--no-code-index" not in o:
        indexes.append(("index-code", base / "repos"))
    for name, src in indexes:
        shutil.rmtree(base / name, ignore_errors=True)
        r = py(addon("scan"), "index", "--from", src, "--to", base / name)
        say("index", f"{name}: {first(r).split(' to ')[0]}")
    r = py(STDLIB.parents[1] / "kernel.py", "verify", "--box", box)
    say("verify", first(r))
    return r.returncode


def words_for(o: dict) -> list[str]:
    return ["--words", o["--words"]] if o.get("--words") else []


def scrubbed(r: subprocess.CompletedProcess, raw: bool) -> int:
    """r's output, through privacy's scrub unless raw; then r's exit code."""
    out = r.stdout
    if out and not raw:
        s = run([sys.executable, addon("privacy"), "scrub"], text_in=out)
        out = s.stdout
        if json.loads(s.stderr or "{}").get("withheld"):  # say only what it hid
            print(s.stderr.strip(), file=sys.stderr)
    sys.stdout.write(out)
    sys.stderr.write(r.stderr)
    return r.returncode


def ask(o: dict, base: Path) -> int:
    """Questions to both indexes through scan. The box's words list is used
    unless --words names another; BM25 takes none."""
    argv = [
        "scan",
        "--questions",
        o["--questions"],
        "--rank",
        o.get("--rank", "kernel"),
    ]
    for name in ("index-pile", "index-code"):
        if (base / name / "index.json").exists():
            argv += ["--index", base / name]
    cfg = json.loads((base / "box" / "kernel.json").read_text(encoding="utf-8"))
    words = o.get("--words") or cfg.get("words")
    if words and o.get("--rank", "kernel") == "kernel":
        argv += ["--words", words]
    argv += ["--top", o["--top"]] if "--top" in o else []
    argv += ["--todo"] if "--todo" in o else []
    return scrubbed(py(addon("scan"), *argv), "--raw" in o)


def report(o: dict, base: Path) -> int:
    """What the box needs from its person, read only, then verify."""
    box, days = base / "box", o.get("--days", "7")
    steps = [
        ("digest", addon("digest"), ["--box", box, "--days", days]),
        ("asked again", addon("again"), ["--box", box]),
        ("stale", addon("stale"), ["--box", box]),
        ("questions by day", addon("export"), ["--box", box, "--log"]),
        ("history", addon("history"), ["--box", box, "--days", days]),
        ("verify", STDLIB.parents[1] / "kernel.py", ["verify", "--box", box]),
    ]
    code = kernel.ALIVE
    for title, script, argv in steps:
        r = py(script, *argv)
        print(f"## {title}\n\n{(r.stdout or r.stderr).strip()}\n")
        code = kernel.REFUSED if r.returncode == kernel.REFUSED else code
    return code


def check(base: Path) -> int:
    """The pile's health as counts: references that don't hold (xref), lines
    marked to do (todo), secrets in plain text (secrets-audit)."""
    box = base / "box"
    say("xref", first(py(addon("xref"), "--box", box), last=True))
    todo = py(addon("todo"), "--box", box)  # 42: nothing marked, said in a line
    marked = 0 if todo.returncode == kernel.ESCALATE else len(todo.stdout.splitlines())
    say("todo", f"{marked} lines marked to do")
    secrets = py(addon("secrets-audit"), "--box", box)
    say(
        "secrets", first(secrets, last=True) if secrets.stdout.strip() else "none found"
    )
    say("each", "the add-on itself, with --box, lists every place by file and line")
    return kernel.ALIVE


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in TAKES:
        return usage()
    verb, o, words, it = argv[0], {}, [], iter(argv[1:])
    for a in it:
        if a in FLAGS.get(verb, ()):
            o[a] = True
        elif a in TAKES[verb] and (a == "--notes" or a not in o):
            v = next(it, "")
            if not v:
                return usage()
            if a == "--notes":
                o.setdefault(a, []).append(v)
            else:
                o[a] = v
        elif a.startswith("--"):
            return usage()
        else:
            words.append(a)
    need = NEEDS.get(verb, {"--base"})
    if not need <= o.keys() or len(words) != WORDS.get(verb, 0):
        return usage()
    if o.get("--rank", "kernel") not in ("kernel", "bm25"):
        return usage()
    if verb == "build":
        return build(o)
    base = Path(o["--base"]).resolve()
    if not (base / "box" / "kernel.json").exists():
        print(f"refused: {base} holds no box; build it first", file=sys.stderr)
        return kernel.REFUSED
    if verb == "ask":
        return ask(o, base)
    if verb == "bite":
        r = py(addon("privacy"), "bite", "--box", base / "box", words[0])
        sys.stdout.write(r.stdout)
        sys.stderr.write(r.stderr)
        return r.returncode
    if verb == "quote":
        r = py(addon("quote-check"), "--box", base / "box", words[0])
        return scrubbed(r, "--raw" in o)
    if verb == "report":
        return report(o, base)
    if verb == "check":
        return check(base)
    r = py(addon("backup"), "--box", base / "box", "--to", o["--to"])
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
