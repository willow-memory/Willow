"""hook_feedback.py: your corrections to an assistant (no, wrong, I said)
caught by a words list (corrections.txt) at each prompt and handed in through propose, for
you to keep or drop. Python 3.9+.

    python adapters/stdlib/hook-feedback/hook_feedback.py run --box DIR [--now TS]
    python adapters/stdlib/hook-feedback/hook_feedback.py check --box DIR

`run` is a UserPromptSubmit hook. It reads the JSON Claude Code, Gemini CLI
and Cursor send on standard input. When the prompt matches a fixed
correction pattern (`no`, `wrong`, or `I said` as a word), it bites that
text and proposes it under `feedback/<hash>.md` with an empty cite list, so
you can seal or decline it. Other prompts, and events that aren't
UserPromptSubmit, are left alone. It prints nothing on stdout (a prompt
hook that adds context would change the turn); the proposal waits on the
record.

`check` lists each waiting `hook-feedback` proposal still on the box (not
yet sealed or declined); exit 42 when any wait, 0 when none.

It never reads the key. Exit codes: 0 allowed (or `check` none waiting);
42 `check` found waiting feedback; 2 refused.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

KIND = "hook-feedback"
GIVE = {"UserPromptSubmit", "user_prompt_submit"}
#: the base words list: what marks a prompt as a correction (+ at its start,
#: ~ anywhere) and what never does (- at its start, read first)
WORDS = Path(__file__).resolve().parent / "corrections.txt"


def read_words(path: Path) -> dict[str, list[str]] | None:
    """A words list as {"+": [...], "~": [...], "-": [...]}, each phrase in
    small letters; None when a line isn't one of the three."""
    out: dict[str, list[str]] = {"+": [], "~": [], "-": []}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        mark, _, phrase = line.partition(" ")
        phrase = plain(phrase)
        if mark not in out or not phrase:
            return None
        out[mark].append(phrase)
    return out


def plain(text: str) -> str:
    """Small letters, one space between words, straight apostrophes."""
    return " ".join(text.replace("\u2019", "'").lower().split())


def quiet(fn, *args) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*args)
    return code, out.getvalue()


def prompt_of(call: dict) -> str | None:
    for f in ("prompt", "user_prompt", "text"):
        v = call.get(f)
        if isinstance(v, str) and v.strip():
            return v
    return None


def event_of(call: dict) -> str:
    e = call.get("hook_event_name") or call.get("hookEventName") or ""
    return e if isinstance(e, str) else ""


def ends(text: str, at: int) -> bool:
    """Whether a phrase ending at `at` ends at a word's end."""
    return at >= len(text) or not text[at].isalnum()


def is_correction(text: str, words: dict[str, list[str]] | None = None) -> bool:
    """Whether the prompt is a correction by the words list: never when it
    starts with a - phrase; when it starts with a + phrase, or holds a ~
    phrase as words of their own."""
    words = words or read_words(WORDS) or {}
    said = plain(text)
    if any(said.startswith(p) and ends(said, len(p)) for p in words.get("-", [])):
        return False
    if any(said.startswith(p) and ends(said, len(p)) for p in words.get("+", [])):
        return True
    for p in words.get("~", []):
        at = said.find(p)
        while at >= 0:
            if (at == 0 or not said[at - 1].isalnum()) and ends(said, at + len(p)):
                return True
            at = said.find(p, at + 1)
    return False


def waiting(box: Path, rows: list[dict]) -> list[dict]:
    """hook-feedback proposal rows still waiting (not sealed, not declined)."""
    sealed = set(kernel.sealed(box, rows)) | set(kernel.declined(box, rows))
    out = []
    for r in rows:
        if r["kind"] != KIND:
            continue
        subj = r.get("subject")
        if isinstance(subj, str) and subj not in sealed:
            out.append(r)
    return out


def hand_in(box: Path, text: str, ts: str) -> tuple[int, str]:
    """Bite and propose the correction; (exit, stderr reason)."""
    code, said = quiet(kernel.bite, box, text, ts)
    if code == kernel.REFUSED:
        return 2, f"refused: the kernel wouldn't take the bite: {said.strip()}"
    digest = kernel.h256(text)[:12]
    prop = {
        "path": f"feedback/{digest}.md",
        "data": text,
        "cites": [],
        "claim": "correction caught by hook-feedback",
    }
    code, said = quiet(kernel.propose, box, [json.dumps(prop)], ts)
    if code != kernel.ESCALATE or "pass" not in said:
        return 2, f"refused: the kernel's door: {said.strip()}"
    subj = kernel.subject_of(prop)
    kernel.append(box, ts, KIND, who="hook-feedback", subject=subj, path=prop["path"])
    return 0, ""


def judge(raw: str, box: Path, ts: str, words: dict | None = None) -> tuple[int, str]:
    try:
        call = json.loads(raw)
    except ValueError:
        call = None
    if not isinstance(call, dict):
        return (
            2,
            "refused: the hook was sent something it can't read, so it can't say it is safe.",
        )
    if event_of(call) not in GIVE:
        return 0, ""
    text = prompt_of(call)
    if text is None or not is_correction(text, words):
        return 0, ""
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return 2, "refused: the record doesn't verify: " + "; ".join(breaks)
    return hand_in(box, text, ts)


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--now", "--words"):
            opts[a] = next(it, "")
        elif a.startswith("--"):
            args = []
            break
        else:
            args.append(a)
    verb = args[0] if args else ""
    if (
        verb not in ("run", "check", "match")
        or len(args) != 1
        or (verb != "match" and not opts.get("--box"))
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    words = None
    if opts.get("--words") is not None:
        try:
            words = read_words(Path(opts["--words"]))
        except (OSError, UnicodeDecodeError):
            words = None
        if words is None:
            print(f"refused: {opts['--words']} isn't a words list (+, ~ or - and a phrase, a line)",
                  file=sys.stderr)  # fmt: skip
            return kernel.REFUSED
    if verb == "match":  # only whether it is one: nothing proposed, nothing written
        try:
            call = json.loads(sys.stdin.read())
        except ValueError:
            call = None
        if not isinstance(call, dict):
            print("refused: the hook was sent something it can't read", file=sys.stderr)
            return kernel.REFUSED
        text = prompt_of(call) if event_of(call) in GIVE else None
        return kernel.ESCALATE if text and is_correction(text, words) else kernel.ALIVE
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    if verb == "run":
        code, why = judge(
            sys.stdin.read(), box, opts.get("--now") or kernel.now(), words
        )
        if why:
            print(why, file=sys.stderr)
        return code
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    found = waiting(box, rows)
    if not found:
        print("no feedback waiting")
        return kernel.ALIVE
    for r in found:
        print(f"waiting  {r['subject']}  {r.get('path', '')}  (row {r['n']})")
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
