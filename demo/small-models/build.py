"""build.py: one box holding every run of the small-models night, and the session.

    python demo/small-models/build.py --to DIR [--session FILE] [--now TS]

The pile, under DIR/pile, is made by willow's own add-ons:

    session/   the Claude Code session that ran it all, if --session is given:
               transcript-redact takes out keys, home paths and emails, then
               agent-transcript writes its spoken turns, numbered. It must be
               the session SESSION.json names, held to its SHA-256.
    runs/      each result in runs/ here and in demo/ofrenda/results, flattened
               to one "where: what" line per value, so every reply, served
               passage, kept line and struck point is a passage the kernel reads.
    ofrenda/   demo/ofrenda's README and screenshots' text, as they are.
    code/      the experiments' scripts, so "how was the hold rule written"
               finds the line that wrote it.

Then `kernel.py init` makes DIR/box over the pile, with a key of its own at
DIR/box.key. Ask it with plain:

    python adapters/stdlib/plain/plain.py bite --box DIR/box "which model told the secret"

Nothing here goes online, and nothing is written outside DIR.

Exit codes, the kernel's: 0 built; 2 refused (DIR exists, or the session
isn't the one SESSION.json names).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SESSION = json.loads((HERE / "SESSION.json").read_text(encoding="utf-8"))
NOW = "2026-11-01T01:00:00Z"
USAGE = "usage: build.py --to DIR [--session FILE] [--now TS]"


def flatten(value: object, where: str = "") -> list[str]:
    """One `where: what` line per value; a long string keeps its lines, so a
    reply stays readable and each paragraph of it is its own passage."""
    if isinstance(value, dict):
        return [
            ln
            for k, v in value.items()
            for ln in flatten(v, f"{where}.{k}" if where else str(k))
        ]
    if isinstance(value, list):
        return [ln for i, v in enumerate(value) for ln in flatten(v, f"{where}[{i}]")]
    text = (
        json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    )
    return [f"{where}: {text}", ""] if "\n" in text else [f"{where}: {text}"]


def runs(pile: Path) -> int:
    out = pile / "runs"
    out.mkdir(parents=True)
    n = 0
    for src in [
        *sorted((HERE / "runs").glob("*.json")),
        *sorted((ROOT / "demo/ofrenda/results").glob("*.json")),
    ]:
        doc = json.loads(src.read_text(encoding="utf-8"))
        lines = [f"run: {src.relative_to(ROOT).as_posix()}", ""]
        lines += flatten(doc)
        (out / f"{src.parent.parent.name}-{src.stem}.txt").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        n += 1
    return n


def session(pile: Path, path: Path, tmp: Path) -> str:
    """The session's first SESSION["bytes"] bytes, held to their SHA-256: a
    session file only grows, so a later copy of the same session still holds
    the frozen part, and only that part is read."""
    raw = path.read_bytes()[: SESSION["bytes"]]
    if hashlib.sha256(raw).hexdigest() != SESSION["sha256"]:
        raise ValueError("not the session SESSION.json names, or cut short")
    frozen = tmp / "frozen.jsonl"
    frozen.write_bytes(raw)
    clean = tmp / "session"
    clean.mkdir()
    redacted = clean / f"{SESSION['id']}.jsonl"
    said = subprocess.run(
        [
            sys.executable,
            str(ROOT / "adapters/stdlib/transcript-redact/transcript_redact.py"),
            "--from",
            str(frozen),
            "--to",
            str(redacted),
        ],
        capture_output=True,
        text=True,
    )
    if said.returncode != 0:
        raise ValueError(f"transcript-redact: {said.stderr.strip()}")
    got = subprocess.run(
        [
            sys.executable,
            str(ROOT / "adapters/stdlib/agent-transcript/agent_transcript.py"),
            "mirror",
            "--from",
            str(clean),
            "--to",
            str(pile / "session"),
        ],
        capture_output=True,
        text=True,
    )
    if got.returncode != 0:
        raise ValueError(f"agent-transcript: {got.stdout.strip()} {got.stderr.strip()}")
    return said.stdout.strip().splitlines()[-1]


def build(to: Path, session_file: Path | None, now: str) -> int:
    pile = to / "pile"
    pile.mkdir(parents=True)
    n = runs(pile)
    print(f"runs: {n} result files flattened")
    (pile / "ofrenda").mkdir()
    shutil.copy(ROOT / "demo/ofrenda/README.md", pile / "ofrenda/README.md")
    for p in sorted((ROOT / "demo/ofrenda/screenshots").glob("*.txt")):
        shutil.copy(p, pile / "ofrenda" / p.name)
    (pile / "code").mkdir()
    for p in [*sorted((HERE / "experiments").glob("*.py")), HERE / "build.py"]:
        if not p.name.startswith("test_"):
            shutil.copy(p, pile / "code" / f"{p.name}.txt")
    if session_file is not None:
        with tempfile.TemporaryDirectory() as tmp:
            print(f"session: {session(pile, session_file, Path(tmp))}")
    got = subprocess.run(
        [
            sys.executable,
            str(ROOT / "kernel.py"),
            "init",
            "--box",
            str(to / "box"),
            "--pile",
            str(pile),
            "--key",
            str(to / "box.key"),
            "--now",
            now,
        ],
        capture_output=True,
        text=True,
    )
    print(got.stdout.strip() or got.stderr.strip())
    return got.returncode


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    if (
        len(argv) % 2
        or not opts.get("--to")
        or set(opts) - {"--to", "--session", "--now"}
    ):
        print(USAGE, file=sys.stderr)
        return 2
    to = Path(opts["--to"])
    if to.exists():
        print(f"refused: {to} exists", file=sys.stderr)
        return 2
    try:
        return build(
            to,
            Path(opts["--session"]) if opts.get("--session") else None,
            opts.get("--now") or NOW,
        )
    except ValueError as e:
        shutil.rmtree(to, ignore_errors=True)
        print(f"refused: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
