"""outside.py: the same method on cpython's CVE fixes, the outside control.

    outside.py resolve --repos DIR --draft FILE --advisories FILE --out FILE
    outside.py fetch   --to DIR --repos DIR [--unit CPn]
    outside.py check   --to DIR [--unit CPn]
    outside.py index   --to DIR --ix DIR --unit CPn [--side old|new]
    outside.py ask     --to DIR --ix DIR --unit CPn --mode found|before --out FILE
                       [--part I/N]
    outside.py judge   --mode found|before --to DIR --answers FILE --box DIR --out FILE

Phase 6 asks the frozen method of a program whose advisories and fixes are
public, so the fleet's result has an outside yardstick (php2shell's phase 3 did
the same). Nothing in the rule changes: trees.py writes and checks the trees,
ask.py asks them, score.py's hit rule (by position) scores them, and run.py's
rank statistic, line-level gate and null gate judge them, for the same two
writers. This file only names the seven units and hands them to those scripts.

`resolve` (the only command that reads the advisories) makes cpython_sources.json
from the desk's draft of the pins, the cpython repository under --repos, and the
advisory rows (--advisories, kept outside the branch): for each unit the CVE id,
the OSV address and fetch time, the SHA-256 of the advisory's summary and of its
details, the fix and vulnerable commits and trees, the diff's SHA-256 and the
unit's weight. It checks the draft against git: the fix commit names its CVE id
in its message (or OSV lists it as the fix), its first parent is the vulnerable side, both tree hashes
match, and its diff changes at least one file the hit rule counts. The
advisory text is never written. cpython_sources.json is the pins file of this
phase; a unit's gap is its own id (CP1 ... CP7).

`fetch` and `check` are trees.py's, for these units (--repos holds a folder
`cpython`). `index` builds one tree's index afresh and says how long it took
and how many passages it holds. `ask` asks one unit in one mode (a task of its
own; `found` indexes both sides, `before` one) the blind writers' questions,
questions/cpython/{local,claude}/CPn.txt and the null set questions/null/null.txt,
each file held to the hash FROZEN.json holds or refused. `--part I/N` asks the
I-th of N contiguous parts of that list, for a unit too slow for one task: the
parts' answers are joined and judged as one. `judge` scores the
joined answers of the units of one mode with run.py, strong and weaker apart,
the weights being the sources file's.

Exit codes, the kernel's: 0 done; 42 something is missing, or a rule fails;
2 refused or a bad command line.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trees  # noqa: E402

ask = trees.sibling("ask")
flag = trees.sibling("flag")
score = trees.sibling("score")
run = trees.sibling("run")
HERE = trees.HERE
SOURCES = HERE / "cpython_sources.json"
QDIR = HERE / "questions"
FROZEN = HERE / "FROZEN.json"
REPO = "cpython"
UNITS = tuple(f"CP{n}" for n in range(1, 8))
WEAKER = ("CP5", "CP6")  # the advisory is libexpat's, not cpython's own code
WEIGHTS = ("strong", "weaker")
OSV = "https://api.osv.dev/v1/vulns/"
KEYS = {"gap", "repo", "cve", "osv_address", "fetched_at", "osv_modified",
        "summary_sha256", "details_sha256", "weight", "why_weaker", "vulnerable",
        "fixed", "files_scored", "diff_files", "counted_files",
        "diff_sha256"}  # fmt: skip
HEX40, HEX64 = re.compile(r"[0-9a-f]{40}"), re.compile(r"[0-9a-f]{64}")


def check_sources(doc: dict) -> None:
    """The sources file is whole: seven units, five strong and CP5 and CP6
    weaker, every field there, and nothing else (so no text can be in it)."""
    if set(doc) != {"about", "repo", "units"} or doc["repo"] != REPO:
        raise ValueError("cpython_sources.json: wrong top-level fields")
    units = doc["units"]
    if tuple(units) != UNITS:
        raise ValueError(f"cpython_sources.json: units are not {', '.join(UNITS)}")
    for name, u in units.items():
        weaker = u.get("weight") == "weaker"
        if set(u) != KEYS - (set() if weaker else {"why_weaker"}):
            raise ValueError(f"{name}: wrong fields {sorted(set(u) ^ KEYS)}")
        ok = (u["gap"] == name and u["repo"] == REPO
              and re.fullmatch(r"CVE-\d{4}-\d{4,}", u["cve"])
              and u["osv_address"] == OSV + u["cve"]
              and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\dZ", u["fetched_at"])
              and isinstance(u["osv_modified"], str)
              and HEX64.fullmatch(u["details_sha256"])
              and (u["summary_sha256"] is None or HEX64.fullmatch(u["summary_sha256"]))
              and u["weight"] in WEIGHTS and (weaker == (name in WEAKER))
              and u["files_scored"] is None
              and isinstance(u["diff_files"], list) and u["diff_files"]
              and isinstance(u["counted_files"], int) and u["counted_files"] >= 1
              and HEX64.fullmatch(u["diff_sha256"]))  # fmt: skip
        for side in ("vulnerable", "fixed"):
            s = u["vulnerable" if side == "vulnerable" else "fixed"]
            ok = (
                ok
                and set(s) == {"commit", "tree"}
                and all(HEX40.fullmatch(s[k]) for k in s)
            )
        if weaker:
            ok = ok and isinstance(u["why_weaker"], str) and u["why_weaker"]
        if not ok:
            raise ValueError(f"{name}: a field is not what the sources file holds")


def load_sources(path: Path = SOURCES) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    check_sources(doc)
    return doc["units"]


def git(repo: Path, *argv: str) -> str:
    return trees.phase3.git(*argv, cwd=repo).decode()


def advisory_hashes(row: dict) -> tuple:
    """(SHA-256 of the summary or None, SHA-256 of the details): of the stored
    text, as UTF-8."""
    summary = row.get("summary")
    return (hashlib.sha256(summary.encode()).hexdigest() if summary else None,
            hashlib.sha256(row["details"].encode()).hexdigest())  # fmt: skip


def resolve_unit(repo: Path, d: dict, row: dict) -> dict:
    """One unit of the draft, held to git and to its advisory row."""
    cve, name = d["cve"], d["id"]
    fixed = git(
        repo, "rev-parse", "--verify", "--quiet", d["fix"] + "^{commit}"
    ).strip()
    if row["id"] != cve or row["address"] != OSV + cve:
        raise ValueError(f"{name}: the advisory row is not {cve}'s")
    # the fix is tied to its CVE by its own message or by OSV's fix reference
    named = row.get("osv_fix_commits_main") or []
    by_osv = any(fixed.startswith(c) for c in named)
    if named and not by_osv:
        raise ValueError(f"{name}: OSV names {named}, not {fixed[:12]}")
    if not by_osv and cve not in git(repo, "log", "-1", "--format=%B", fixed):
        raise ValueError(f"{name}: neither {fixed[:12]}'s message nor OSV names {cve}")
    parents = git(repo, "rev-list", "--parents", "-n", "1", fixed).split()[1:]
    if not parents:
        raise ValueError(f"{name}: {fixed[:12]} has no parent")
    vulnerable = parents[0]  # the first parent: the side before the fix
    if not vulnerable.startswith(d["vulnerable"]):
        raise ValueError(f"{name}: the first parent is {vulnerable[:12]}, "
                         f"the draft says {d['vulnerable']}")  # fmt: skip
    sides = {}
    for key, commit, want in (("vulnerable", vulnerable, d["tree_old"]),
                              ("fixed", fixed, d["tree_new"])):  # fmt: skip
        tree = git(repo, "rev-parse", commit + "^{tree}").strip()
        if not tree.startswith(want):
            raise ValueError(
                f"{name}: the {key} tree is {tree[:12]}, the draft says {want}"
            )
        sides[key] = {"commit": commit, "tree": tree}
    names = git(
        repo, "diff", "--no-renames", "--name-only", vulnerable, fixed
    ).splitlines()
    counted = [n for n in names if score.counts(n)]
    if not counted:  # score.py counts no file of this fix: nothing could hit
        raise ValueError(f"{name}: the fix changes no file the hit rule counts")
    diff = trees.phase3.git(*trees.DIFF, vulnerable, fixed, cwd=repo)
    if not diff:
        raise ValueError(f"{name}: an empty diff")
    summary, details = advisory_hashes(row)
    if row.get("details_sha256") not in (None, details):
        raise ValueError(f"{name}: the row's details hash is not its details'")
    unit = {"gap": name, "repo": REPO, "cve": cve, "osv_address": row["address"],
            "fetched_at": row["fetched_at"], "osv_modified": row["osv_modified"],
            "summary_sha256": summary, "details_sha256": details,
            "weight": d["weight"], **sides, "files_scored": None,
            "diff_files": names, "counted_files": len(counted), "diff_sha256": hashlib.sha256(diff).hexdigest()}  # fmt: skip
    if d["weight"] == "weaker":
        unit["why_weaker"] = d["why_weaker"]
    return unit


def resolve(repos: Path, draft: dict, rows: list) -> dict:
    by_cve = {r["id"]: r for r in rows}
    units = {}
    for d in draft["units"]:
        if d["cve"] not in by_cve:
            raise ValueError(f"{d['id']}: no advisory row for {d['cve']}")
        units[d["id"]] = resolve_unit(repos / REPO, d, by_cve[d["cve"]])
    doc = {"about": "cpython_sources.json: phase 6's pins. For each outside unit, the CVE, "
           "the OSV address and fetch time, the SHA-256 of the advisory's summary and "
           "details (the text itself is kept outside this branch), the fix and "
           "vulnerable commits and trees, the diff's SHA-256 and the unit's weight. "
           "Made by outside.py resolve.", "repo": REPO, "units": units}  # fmt: skip
    check_sources(doc)
    return doc


def frozen_files(path: Path = FROZEN) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))["files"]


def unit_questions(qdir: Path, unit: str, mode: str, frozen: dict | None) -> list:
    """[(name, question, writer)] for a unit: the local and claude writers'
    questions/cpython/{writer}/CPn.txt, and the shared null set in `before`
    only. With `frozen`, every file read must be the one it holds."""
    files = [qdir / "cpython" / w / f"{unit}.txt" for w in flag.WRITERS]
    if mode == "before":
        files.append(qdir / "null" / "null.txt")
    if frozen is not None:
        for f in files:
            rel = f.relative_to(qdir).as_posix()
            if (
                frozen.get("questions/" + rel)
                != hashlib.sha256(f.read_bytes()).hexdigest()
            ):
                raise ValueError(f"questions/{rel} is not the file FROZEN.json holds")
    qs = flag.questions(qdir / "cpython", unit, nulls=False)
    for w in flag.WRITERS:
        if not any(x[2] == w for x in qs):
            raise ValueError(f"{unit} has no question from the {w} writer")
    if mode == "before":
        qs += [(f"null {n}", q, "null")
               for n, q in enumerate(flag.read(qdir / "null" / "null.txt"), 1)]  # fmt: skip
    return qs


def part_of(qs: list, part: str) -> list:
    """Part I of N ("2/3") of a question list, in order and cut where the list
    is, so a unit too slow for one task can be asked in several and the answers
    joined: every question is asked exactly once, under its own name. An index
    is built afresh for each part, as ask.py always does."""
    m = re.fullmatch(r"(\d+)/(\d+)", part)
    if not m or not 1 <= int(m[1]) <= int(m[2]):
        raise ValueError(f"{part!r} is not a part like 2/3")
    i, n = int(m[1]), int(m[2])
    return qs[len(qs) * (i - 1) // n : len(qs) * i // n]


def ask_unit(to: Path, ix: Path, unit: str, mode: str, units: dict, qs: list) -> list:
    return ask.ask(to, ix, unit, units[unit], qs, mode)


def index_one(to: Path, ix: Path, unit: str, side: str, pin: dict) -> dict:
    """One pinned tree indexed afresh: how long, and how many passages."""
    tree = pin["vulnerable" if side == "old" else "fixed"]["tree"]
    t0 = time.monotonic()
    at = ask.fresh_index(ix, tree, to / "trees" / unit / side, tree)
    seconds = round(time.monotonic() - t0, 1)
    return {"unit": unit, "side": side, "tree": tree, "seconds": seconds,
            "passages": len(ask.scan.passages(at)),
            "index_sha256": ask.index_hash(at)}  # fmt: skip


@contextlib.contextmanager
def cpython_groups(units: dict):
    """run.py takes a gap's group from gaps.json's source_kind. Here a unit's
    group is its weight in the sources file: strong is a written-before-the-fix
    source, weaker is not."""
    was = trees.load_gaps
    trees.load_gaps = lambda *_: {
        n: {"source_kind": "gap_record" if u["weight"] == "strong" else "commit_message"}
        for n, u in units.items()
    }  # fmt: skip
    try:
        yield
    finally:
        trees.load_gaps = was


def judge(mode: str, to: Path, answers: Path, box: Path, out: Path, units: dict) -> int:
    with cpython_groups(units):
        return run.main([mode, "--to", str(to), "--answers", str(answers),
                         "--box", str(box), "--out", str(out)])  # fmt: skip


TABLE = {
    "resolve": ({"--repos", "--draft", "--advisories", "--out"}, set()),
    "fetch": ({"--to", "--repos"}, {"--unit"}),
    "check": ({"--to"}, {"--unit"}),
    "index": ({"--to", "--ix", "--unit"}, {"--side"}),
    "ask": ({"--to", "--ix", "--unit", "--mode", "--out"}, {"--part"}),
    "judge": ({"--mode", "--to", "--answers", "--box", "--out"}, set()),
}


def main(argv: list[str]) -> int:
    cmd, opts = (argv[0] if argv else ""), dict(zip(argv[1::2], argv[2::2]))
    if (
        cmd not in TABLE
        or len(argv) != 1 + 2 * len(opts)
        or not (TABLE[cmd][0] <= set(opts) <= TABLE[cmd][0] | TABLE[cmd][1])
    ):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    try:
        if cmd == "resolve":
            rows = [json.loads(x) for x in
                    Path(opts["--advisories"]).read_text(encoding="utf-8").splitlines()
                    if x.strip()]  # fmt: skip
            draft = json.loads(Path(opts["--draft"]).read_text(encoding="utf-8"))
            doc = resolve(Path(opts["--repos"]), draft, rows)
            Path(opts["--out"]).write_text(
                json.dumps(doc, indent=1) + "\n", encoding="utf-8"
            )
            for name, u in doc["units"].items():
                print(f"{name:4} {u['cve']:16} {u['weight']:7} "
                      f"{u['vulnerable']['commit'][:12]} -> {u['fixed']['commit'][:12]}")  # fmt: skip
            return 0
        units = load_sources()
        if "--unit" in opts:
            if opts["--unit"] not in units:
                raise ValueError(f"no unit {opts['--unit']}")
            only = {opts["--unit"]: units[opts["--unit"]]}
        else:
            only = units
        to = Path(opts["--to"]) if "--to" in opts else None
        if cmd == "fetch":
            to.mkdir(parents=True, exist_ok=True)
            for name, pin in only.items():
                trees.fetch_unit(to, Path(opts["--repos"]), name, pin)
            return trees.check(to, only)
        if cmd == "check":
            return trees.check(to, only)
        if cmd == "index":
            side = opts.get("--side", "old")
            if side not in ("old", "new") or "--unit" not in opts:
                raise ValueError("a side of old or new, and a unit")
            unit = opts["--unit"]
            print(
                json.dumps(index_one(to, Path(opts["--ix"]), unit, side, units[unit]))
            )
            return 0
        if cmd == "ask":
            unit, mode = opts["--unit"], opts["--mode"]
            if unit not in units or mode not in ask.TOP:
                raise ValueError(
                    "a unit of cpython_sources.json, a mode of found or before"
                )
            qs = part_of(unit_questions(QDIR, unit, mode, frozen_files()),
                         opts.get("--part", "1/1"))  # fmt: skip
            rows = ask_unit(to, Path(opts["--ix"]), unit, mode, units, qs)
            with open(opts["--out"], "w", encoding="utf-8", newline="\n") as f:
                for r in rows:
                    f.write(json.dumps(r, sort_keys=True) + "\n")
            return 0
        return judge(opts["--mode"], to, Path(opts["--answers"]), Path(opts["--box"]),
                     Path(opts["--out"]), units)  # fmt: skip
    except (
        OSError,
        ValueError,
        KeyError,
        trees.phase3.subprocess.CalledProcessError,
    ) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
