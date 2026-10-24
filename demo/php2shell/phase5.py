"""phase5.py: robustness. Rewording, settings, and leakage.

    python demo/php2shell/phase5.py --data DIR --ix DIR --box DIR --out FILE

--data and --ix as in phase2.py. Frozen, with the reworded questions and the
advisory words list, before it ran (FROZEN.json). All three checks ask the
PHP2Shell pairs: the vulnerable release `--changed-from` the fixed one,
scored by rule 2 (score2.py) on the old side, in a core file (score.py).

reword: the author's eight questions rephrased five ways each by a blind
agent (questions/reword.txt). A variant is stable when it hits the same
fix its original hits. Reported: the originals' hit rate, the variants', and
how often a hit survives each kind of rewording.

settings: the author's eight, ranked by the kernel, top 1, 3 and 10, and
with the advisory words list (questions/advisory-words.txt, acronyms the
advisories expand) against without it.

leakage: a hit asking the old code holds a line the fix removed, so it can
never be in a comment the fix added; this confirms it, and counts, on the
fixed side, how many hits rest only on a line the fix added that is a C
comment. The headline results ask the old side, so leakage cannot inflate
them.

A fourth check, php.net's release tarball against the git tree, is not run:
php.net is unreachable from here (the proxy returns 403). It is described so
it can be run where php.net is reachable.

Exit 0; reword and leakage are reported, settings too, and the one pass rule
is that rewording keeps most hits (the variants' hit rate is at least 70% of
the originals', pooled). 42 if it does not, 2 for a bad command line.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "scan"))
sys.path.insert(0, str(HERE))
import kernel  # noqa: E402
import scan  # noqa: E402
import score  # noqa: E402
import score2  # noqa: E402

NOW = "2026-10-24T00:00:00Z"
TOP = 3


def q(name: str):
    return scan.questions((HERE / "questions" / name).read_text(encoding="utf-8"))


def changed_core(diff: str) -> dict:
    """Rule 2's changed lines, kept to the PHP2Shell core files."""
    full = score2.changed(diff)
    core = {f: full["old"][f] for f in full["old"] if f in score.CORE}
    return {"old": core, "files": set(full["files"]) & score.CORE}


def hit(served: list[dict], fix: dict) -> bool:
    for c in served:
        if {x.strip() for x in c["text"].splitlines()} & fix["old"].get(
            c["path"], set()
        ):
            return True
    return False


def added_lines(diff: str) -> dict:
    """Per file, every line the fix added (a + line, stripped)."""
    out, new = {}, None
    for ln in diff.splitlines():
        if ln.startswith("+++ "):
            new = ln[6:] if ln.startswith("+++ b/") else None
        elif ln.startswith("+") and new and len(ln[1:].strip()) >= 8:
            out.setdefault(new, set()).add(ln[1:].strip())
    return out


def run(data: Path, ix: Path) -> dict:
    fixes = {b: changed_core((data / "fixes" / f"{b}.diff").read_text(encoding="utf-8"))
             for b in score.PINS["fixes"]}  # fmt: skip
    author, variants = q("author.txt"), q("reword.txt")
    words = kernel.parse_words((HERE / "questions" / "advisory-words.txt").read_text())[
        0
    ]
    reword = {
        "orig": {"hit": 0, "of": 0},
        "variant": {"hit": 0, "of": 0},
        "by_kind": {},
    }
    settings = {"plain": {}, "words": {}}
    leak = {"old_side_hits": 0, "old_side_touching_added_line": 0}
    for branch, fx in score.PINS["fixes"].items():
        vuln, fixed = fx["vulnerable"], fx["fixed"]
        before = {c["id"] for c in scan.passages(ix / fixed)}
        old = scan.Index(ix / vuln)
        fix = fixes[branch]
        orig_hit = {}
        for n, text in author:
            h = hit(old.rank(text, {}, TOP, before), fix)
            orig_hit[n] = h
            reword["orig"]["hit"] += h
            reword["orig"]["of"] += 1
        for n, text in variants:
            base = n.split("-")[0]
            kind = n.split("-")[1]
            h = hit(old.rank(text, {}, TOP, before), fix)
            reword["variant"]["hit"] += h
            reword["variant"]["of"] += 1
            bk = reword["by_kind"].setdefault(
                kind, {"hit": 0, "of": 0, "kept": 0, "could": 0}
            )
            bk["hit"] += h
            bk["of"] += 1
            if orig_hit.get(base):
                bk["could"] += 1
                bk["kept"] += h
        for k in (1, 3, 10):
            settings["plain"].setdefault(k, 0)
            settings["words"].setdefault(k, 0)
            for n, text in author:
                settings["plain"][k] += hit(old.rank(text, {}, k, before), fix)
                settings["words"][k] += hit(old.rank(text, words, k, before), fix)
        # leakage: an old-side hit holds a line the fix REMOVED, so it can
        # never hold a line the fix ADDED (a new comment included). Count the
        # served passages that hold any added line, which should be none.
        added = added_lines((data / "fixes" / f"{branch}.diff").read_text())
        for _, text in author:
            for c in old.rank(text, {}, TOP, before):
                lines = {x.strip() for x in c["text"].splitlines()}
                if lines & fix["old"].get(c["path"], set()):
                    leak["old_side_hits"] += 1
                if lines & added.get(c["path"], set()):
                    leak["old_side_touching_added_line"] += 1
        old = None
    return {"reword": reword, "settings": settings, "leakage": leak,
            "tarball": "not run: php.net unreachable from here (proxy 403)"}  # fmt: skip


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    need = {"--data", "--ix", "--box", "--out"}
    if len(argv) != 2 * len(need) or set(opts) != need:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    box, out = Path(opts["--box"]), Path(opts["--out"])
    if not (box / "record.jsonl").exists():
        with contextlib.redirect_stdout(io.StringIO()):
            if (
                kernel.init(box, HERE, box.parent / (box.name + ".key"), NOW)
                != kernel.ALIVE
            ):
                print(f"refused: couldn't start a record at {box}", file=sys.stderr)
                return 2
    result = run(Path(opts["--data"]), Path(opts["--ix"]))
    out.write_text(json.dumps(result, indent=1) + "\n")
    r = result["reword"]
    kept = (
        r["variant"]["hit"] / r["variant"]["of"]
        >= 0.7 * r["orig"]["hit"] / r["orig"]["of"]
    )
    tools = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in (
        "kernel.py", "adapters/stdlib/scan/scan.py", "demo/php2shell/phase5.py")}  # fmt: skip
    kernel.append(box, NOW, "verdict", who="php2shell", gate="phase5:rewording-keeps-hits",
                  state="satisfied" if kept else "failing",
                  answers_sha256=hashlib.sha256(out.read_bytes()).hexdigest(), tools=tools)  # fmt: skip
    print(json.dumps(result, indent=1))
    return 0 if kept else 42


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
