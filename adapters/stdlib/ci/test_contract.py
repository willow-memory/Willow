"""What every add-on promises alike, held for all of them in one place.

The command line: run with nothing, an add-on refuses (exit 2) and says how
to run it, by its own file name. Run right, it works; with one argument more,
against a real box, it refuses the same way, so the refusal is the command
line's and nothing else's.

The readers: each that writes a mirror (`mirror --from FOLDER --to MIRROR`)
keeps the one contract the readers share, whatever it reads. It says
`wrote N files to MIRROR; skipped M`; the same folder gives the same bytes;
originals are never changed; hidden files and folders are never read; a
folder with nothing to read is 42; a mirror inside the folder, or the folder
inside the mirror, or a folder that isn't one, is refused and writes
nothing. `check_reader` is the contract, so a reader in adapters/deps (pdf)
runs it from its own tests, where its install is.

WILLOW_ONLY=NAME narrows both to one add-on: mutants.py runs an add-on's own
tests and its share of these, and nothing else.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
STDLIB = ROOT / "adapters" / "stdlib"
KERNEL = ROOT / "kernel.py"
ONLY = os.environ.get("WILLOW_ONLY", "")
NOW = ["--now", "2026-10-23T00:00:00Z"]


def _docx(text: str) -> bytes:
    from io import BytesIO

    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", f'<w:document xmlns:w="{w}"><w:body><w:p><w:r>'
                   f"<w:t>{text}</w:t></w:r></w:p></w:body></w:document>")  # fmt: skip
    return buf.getvalue()


#: one small readable file per reader, by the name it is written under
READERS: dict[str, tuple[str, dict[str, bytes]]] = {
    "books": ("books.py", {"My Clippings.txt": (
        "Made-Up Harbour (Ada Example)\n- Your Highlight on page 12 | Location 180 | "
        "Added on Sunday, 3 March 2024 10:15:22\n\nThe tide keeps its own calendar.\n"
        "==========\n").encode()}),
    "calendar": ("cal.py", {"home.ics": (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nDTSTART:20261028T140000Z\r\n"
        "SUMMARY:Dentist\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n").encode()}),
    "chats": ("chats.py", {"chat.txt": (
        "[13/12/2024, 08:10:00] Dev Raman: I can do 600 tonight\n"
        "[13/12/2024, 08:11:00] Ada: Done\n").encode()}),
    "mail": ("mail.py", {"roof.eml": (
        "From: Ada Example <ada@example.org>\nDate: Thu, 14 Oct 2026 09:15:00 +0100\n"
        "Subject: Roof estimate\n\nThe estimate is in.\n").encode()}),
    "notes": ("notes.py", {"garden.md": b"Tomatoes want [[sun]].\n"}),
    "office": ("office.py", {"letter.docx": _docx("The roof is fixed.")}),
    "web-pages": ("web_pages.py", {"saved.html": (
        "<!-- saved from url=(0020)https://example.org/ -->\n"
        "<p>The roof is fixed.</p>\n").encode()}),
    "clauses": ("clauses.py", {"terms.html": (
        "<h1>Terms</h1><p>We keep your data. We delete it on request.</p>\n").encode()}),
}  # fmt: skip

#: a command that works, for each add-on a person runs; {box}, {pile} and
#: {tmp} are filled in. The repo's own tools (ci, readme, similar, mutants,
#: github) are tested in their own folders.
COMMANDS: dict[str, tuple[str, list[str]]] = {
    "again": ("again.py", ["--box", "{box}"]),
    "aider": ("aider.py", ["--box", "{box}"]),
    "ci-why": ("ci_why.py", ["--record", "{box}/record.jsonl"]),
    "claude-code": ("hook.py", ["setup", "--box", "{box}"]),
    "codex-cli": ("codex_cli.py", ["--box", "{box}"]),
    "copilot": ("copilot.py", ["--box", "{box}"]),
    "cursor": ("cursor.py", ["--box", "{box}"]),
    "emacs": ("emacs.py", ["--box", "{box}"]),
    "gemini-cli": ("gemini_cli.py", ["--box", "{box}"]),
    "jetbrains": ("jetbrains.py", ["--box", "{box}"]),
    "mcp-lite": ("server.py", ["--box", "{box}"]),
    "opencode": ("opencode.py", ["--box", "{box}"]),
    "shell": ("shell.py", ["script", "bash"]),
    "vim": ("vim.py", ["--box", "{box}"]),
    "vscode": ("vscode.py", ["--box", "{box}"]),
    "live": ("live.py", ["list"]),
    "windsurf": ("windsurf.py", ["--box", "{box}"]),
    "zed": ("zed.py", ["--box", "{box}"]),
    "all": ("all.py", ["--box", "{box}", "tomatoes"]),
    "coming-up": ("coming_up.py", ["--box", "{box}", *NOW]),
    "export": ("export.py", ["--box", "{box}"]),
    "gaps": ("gaps.py", ["--box", "{box}", *NOW]),
    "on-this-day": ("on_this_day.py", ["--box", "{box}", *NOW]),
    "pipe": ("pipe.py", ["--box", "{box}", *NOW]),
    "plain": ("plain.py", ["bite", "--box", "{box}", *NOW, "tomatoes"]),
    "privacy": ("privacy.py", ["bite", "--box", "{box}", *NOW, "tomatoes"]),
    "quote-check": ("quote_check.py", ["--box", "{box}", "Tomatoes want sun"]),
    "misquote": ("misquote.py", ["--box", "{box}", "Tomatoes want rain"]),
    "claim-check": ("claim_check.py", ["--box", "{box}", "tomatoes want sun"]),
    "policy-watch": ("policy_watch.py", ["--url", "http://127.0.0.1:9/terms", "--to", "{tmp}/w"]),
    "readings": ("readings.py", ["bite", "--box", "{box}", *NOW, "tomatoes"]),
    "advisories": ("advisories.py", ["--box", "{box}"]),
    "outdated": ("outdated.py", ["--box", "{box}"]),
    "typosquat": ("typosquat.py", ["--box", "{box}"]),
    "install-scripts": ("install_scripts.py", ["--box", "{box}"]),
    "pins": ("pins.py", ["--box", "{box}"]),
    "scan": ("scan.py", ["index", "--from", "{pile}", "--to", "{tmp}/index"]),
    "slow-tests": ("slow_tests.py", ["--runs", "{pile}"]),
    "snapshot": ("snapshot.py", ["check", "--in", "{pile}"]),
    "wayback": ("wayback.py", ["find", "--url", "https://example.org/", "--to", "{tmp}/w",
                               "--after", "20261016", "--before", "20261001"]),
    "stale": ("stale.py", ["--box", "{box}"]),
    "starter-words": ("starter.py", ["copy", "--to", "{tmp}/words.txt"]),
    "surprise": ("surprise.py", ["--box", "{box}", *NOW]),
    "todo": ("todo.py", ["--box", "{box}"]),
    "contradictions": ("contradictions.py", ["--box", "{box}"]),
    "lending": ("lending.py", ["--box", "{box}"]),
    "timeline": ("timeline.py", ["--box", "{box}", "--to", "{tmp}/timeline.txt", "tomatoes"]),
    "stack": ("stack.py", ["--box", "{box}", "digest"]),
    "browse": ("browse.py", ["launcher", "--box", "{box}"]),
    "digest": ("digest.py", ["--box", "{box}", *NOW]),
    **{f"words-{c}": (f"words_{c}.py", ["bite", "--box", "{box}", *NOW, "tomatoes"])
       for c in ("de", "es", "fr", "it", "nl", "pt")},
    "backup": ("backup.py", ["--box", "{box}", "--to", "{tmp}/backups", *NOW]),
    "history": ("history.py", ["--box", "{box}"]),
    "dice": ("dice.py", ["--box", "{box}", "roll", "2d6", *NOW]),
    "hook-fail-closed": ("hook_fail_closed.py", ["--hook", "true"]),
    "hook-fuzz": ("hook_fuzz.py", ["--hook", "true"]),
    "hook-pin": ("hook_pin.py", ["--box", "{box}", "approve", "{pile}/garden.md", *NOW]),
    "hook-replay": ("hook_replay.py", ["--box", "{box}", "--to", "{tmp}", "run", "--hook", "true", *NOW]),
    "horoscope": ("horoscope.py", ["Ana", "--date", "2026-10-24"]),
    "life": ("life.py", ["--box", "{box}", "play", "--generations", "8", *NOW]),
    "odds": ("odds.py", ["2d6"]),
    "changed": ("changed.py", ["--box", "{box}", *NOW]),
    "diverge": ("diverge.py", ["{pile}", "{pile}"]),
    "secrets-audit": ("secrets_audit.py", ["--box", "{box}"]),
    "risky-code": ("risky_code.py", ["--box", "{box}"]),
    "session-seal": ("session_seal.py", ["--box", "{box}", *NOW]),
    "xref": ("xref.py", ["--box", "{box}"]),
    "test-impact": ("impact.py", ["plan", "README.md"]),
    "print": ("print.py", ["--box", "{box}", "--to", "{tmp}/page.html", *NOW, "tomatoes"]),
    "start": ("start.py", ["--pile", "{pile}", "--to", "{tmp}/willow"]),
    # a list naming no owner/repo builds nothing, before any clone: no network
    "repo-pile": ("repo_pile.py", ["build", "--to", "{tmp}/base", "--repos",
                                   "{pile}/garden.md", "--key", "{tmp}/base.key"]),
    "test-shards": ("shards.py", ["--shards", "2", "--tests", "{pile}/garden.md"]),
    "restack": ("restack.py", ["--onto", "HEAD", "HEAD"]),
    **{name: (script, ["mirror", "--from", "{pile}", "--to", "{tmp}/mirror"])
       for name, (script, _) in READERS.items()},
}  # fmt: skip


def only(names) -> list[str]:
    return [n for n in sorted(names) if not ONLY or n == ONLY]


def run(script: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *argv], stdin=subprocess.DEVNULL,
                          capture_output=True, text=True)  # fmt: skip


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}  # fmt: skip


def test_every_add_on_a_person_runs_is_listed_here():
    """A new add-on with a command line can't slip past these checks."""
    run_by_people = {
        p.parent.name for p in STDLIB.glob("*/*.py")
        if "__main__" in p.read_text(encoding="utf-8") and not p.name.startswith("test_")
    } - {"ci", "readme", "similar", "mutants", "github"}  # fmt: skip
    assert run_by_people == set(COMMANDS)


@pytest.mark.parametrize("name", only(COMMANDS))
def test_a_bad_command_line_is_refused_and_says_how_to_run_it(name, tmp_path):
    script_name, argv = COMMANDS[name]
    script = STDLIB / name / script_name
    got = run(script)
    assert got.returncode == 2 and script_name in got.stderr, got.stderr
    pile = tmp_path / "pile"
    pile.mkdir()
    for rel, data in READERS.get(name, ("", {"garden.md": b"Tomatoes want sun.\n"}))[
        1
    ].items():
        (pile / rel).write_bytes(data)
    box = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile",
                    str(pile), "--key", str(tmp_path / "key"), *NOW], check=True,
                   capture_output=True)  # fmt: skip
    fill = {"box": str(box), "pile": str(pile), "tmp": str(tmp_path)}
    good = [a.format(**fill) for a in argv]
    assert run(script, *good).returncode in (0, 42), "the command that works"
    if name == "starter-words":
        (tmp_path / "words.txt").unlink()
    got = run(script, *good, "--stray", "more")  # two: again takes one more as words
    assert got.returncode == 2 and script_name in got.stderr, (
        got.returncode,
        got.stderr,
    )


def check_reader(script: Path, sample: dict[str, bytes], tmp: Path) -> None:
    """The contract every reader keeps, run on one folder of its own files."""
    folder, mirror = tmp / "folder", tmp / "mirror"
    for rel, data in sample.items():
        for where in (rel, f".hidden/{rel}", f".{Path(rel).name}"):
            p = folder / where
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
    before = snapshot(folder)

    got = run(script, "mirror", "--from", str(folder), "--to", str(mirror))
    assert got.returncode == 0, got.stderr
    line = got.stdout.strip().splitlines()[-1]
    assert re.fullmatch(rf"wrote {len(sample)} files? to .+; skipped 0", line), line
    assert sorted(snapshot(mirror)) == sorted(f"{rel}.txt" for rel in sample)
    again = tmp / "again"
    run(script, "mirror", "--from", str(folder), "--to", str(again))
    assert snapshot(again) == snapshot(mirror), "the same folder, the same bytes"
    assert snapshot(folder) == before, "originals are never changed"

    empty = tmp / "empty"
    empty.mkdir()
    got = run(script, "mirror", "--from", str(empty), "--to", str(tmp / "m2"))
    assert got.returncode == 42 and "wrote 0 files" in got.stdout

    for src, dst in ((folder, folder / "inside"), (folder, tmp)):
        got = run(script, "mirror", "--from", str(src), "--to", str(dst))
        assert got.returncode == 2 and got.stderr.startswith("refused"), got.stderr
    assert snapshot(folder) == before, "a refusal writes nothing"
    got = run(script, "mirror", "--from", str(tmp / "missing"), "--to", str(tmp / "m3"))
    assert got.returncode == 2 and got.stderr.startswith("refused"), got.stderr


@pytest.mark.parametrize("name", only(READERS))
def test_every_reader_keeps_the_readers_contract(name, tmp_path):
    script, sample = READERS[name]
    check_reader(STDLIB / name / script, sample, tmp_path)
