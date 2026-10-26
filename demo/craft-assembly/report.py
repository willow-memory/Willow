"""report.py: the study's full report, written from its committed files alone.

    python demo/craft-assembly/report.py write    REPORT.md, then results/checks.md
    python demo/craft-assembly/report.py check    exit 1 if either would change

REPORT.md is made from the files this folder holds: sources.json,
composite.json, FROZEN.json, the three runs' results, the record they were
judged on (results/record.jsonl), README.md and BACKGROUND.md, and two
entries of the repo's CHANGELOG.md. Every number in it is counted from those
files here; none is typed. The prose between the numbers is this file's, and
every passage it quotes is quoted whole, under the name of the file it is in.

results/checks.md is what willow's own tools say of the report and the
study: the kernel reads the record's chain; `xref` checks every reference
in the folder; `claim-check` looks for each counted claim in the README,
which was written by hand, so the two are held to each other. It reads no
key and seals nothing: sealing is the person's.

The same files give the same bytes, every run.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

RUNS = (1, 2, 3)
RULES = ("rebuilt", "same-store", "same-composite", "builds", "tests")
INPUTS = ("sources.json", "composite.json", "FROZEN.json", "README.md",
          "BACKGROUND.md", "results/run-1.json", "results/run-2.json",
          "results/run-3.json", "results/record.jsonl", "report.py")  # fmt: skip
REPORT, CHECKS = HERE / "REPORT.md", HERE / "results" / "checks.md"


def load(name: str):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def n(x: int) -> str:
    return f"{x:,}"


def mb(x: int) -> str:
    return f"{x / 1e6:,.0f} MB"


def section(text: str, heading: str, down: int = 1) -> str:
    """The section of `text` under `heading`, to the next heading of its
    level or above, its own headings moved `down` levels."""
    lines, out, level = text.splitlines(), [], None
    for line in lines:
        m = re.match(r"(#+) ", line)
        if level is None:
            if line == heading:
                level = len(m.group(1))
            continue
        if m and len(m.group(1)) <= level:
            break
        out.append("#" * down + line if m else line)
    if level is None:
        raise SystemExit(f"refused: no heading {heading!r}")
    return "\n".join(out).strip()


def entry(changelog: str, starts: str) -> str:
    """The whole CHANGELOG entry that opens with `starts`."""
    lines = changelog.splitlines()
    i = next(i for i, ln in enumerate(lines) if ln.startswith(starts))
    out = [lines[i]]
    for ln in lines[i + 1 :]:
        if not ln.startswith("  "):
            break
        out.append(ln)
    return "\n".join(out)


def record() -> tuple[list[dict], list[str]]:
    return kernel.read(HERE / "results" / "record.jsonl")


def freeze_of(row: dict, frozen: dict) -> int:
    """Which freeze a verdict row was judged by: the one whose files hash as
    the row's tools did (the last freeze's are FROZEN.json's own files)."""
    tools = {Path(p).name: h for p, h in row["tools"].items()}
    for f in frozen["freezes"]:
        files = f.get("files", frozen["files"])
        if all(tools.get(k) == v for k, v in files.items()):
            return f["freeze"]
    return 0


def counts(res: dict) -> dict:
    """What a run's results say, counted."""
    base, comp = res["baseline"], res["composite"]
    held_in = res.get("composite_members")

    def held(a, p):
        return p in held_in.get(a, ()) if held_in else p in comp.get(a, {})

    out = {}
    for f in ("builds", "tests"):
        want = sorted((a, p) for a, ps in base.items() for p, o in ps.items()
                      if o[f] and held(a, p))  # fmt: skip
        out[f] = (
            len(want),
            [w for w in want if not comp.get(w[0], {}).get(w[1], {}).get(f)],
        )
    same = sorted((a, p) for a, ps in comp.items() for p, o in ps.items()
                  if base.get(a, {}).get(p) != o)  # fmt: skip
    g = res["glue"]
    lib = g.get("git") or g.get("library") or {}
    return {
        "sources": len(res["rebuilt"]),
        "rebuilt": sum(res["rebuilt"].values()),
        "pieces": res["pieces"],
        "baseline": sum(len(v) for v in base.values()),
        "composite": sum(len(v) for v in comp.values()),
        "differ": same,
        "members": g["members"],
        "git": len(lib),
        "left_out": g["left_out"],
        "pinned": g.get("pinned") or [],
        "not_pinned": g.get("not_pinned") or [],
        "dropped": g["profiles_dropped"],
        "lock": res["lockfile_made"],
        "left_out_held": res.get("left_out_held"),
        **{f: out[f] for f in ("builds", "tests")},
    }


def runs() -> dict[int, dict]:
    rows, _ = record()
    frozen = load("FROZEN.json")
    out = {}
    for r in RUNS:
        name = f"results/run-{r}.json"
        res, h = load(name), sha(HERE / name)
        mine = [row for row in rows if row.get("results_sha256") == h]
        out[r] = {"file": name, "sha": h, "res": res, "c": counts(res), "rows": mine,
                  "verdicts": {row["gate"].split(":", 1)[1]: row["state"] for row in mine},
                  "freeze": freeze_of(mine[0], frozen) if mine else 0,
                  "ts": mine[0]["ts"] if mine else None}  # fmt: skip
    return out


def table(head: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    return "\n".join(out + ["| " + " | ".join(r) + " |" for r in rows])


def link(text: str, path: str) -> str:
    """A markdown link, built here so the template itself holds none."""
    return "[" + text + "]" + "(" + path + ")"


def names(pairs) -> str:
    return ", ".join(f"`{a}/{p}`" for a, p in pairs) or "none"


def render() -> str:
    readme = (HERE / "README.md").read_text(encoding="utf-8")
    background = (HERE / "BACKGROUND.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    src, recipe, frozen = (
        load("sources.json"),
        load("composite.json"),
        load("FROZEN.json"),
    )
    rows, breaks = record()
    R = runs()
    last = R[RUNS[-1]]
    c3 = last["c"]
    held_all = all(v == "satisfied" for v in last["verdicts"].values())
    pins = src["sources"]
    apps = recipe["apps"]
    libs = sorted(k for k in pins if k.startswith("craft-libs@"))
    out: list[str] = []
    w = out.append

    w("# Craft assembly: the full report\n")
    w(
        "Written by [report.py](report.py) from this folder's own files, the "
        "same bytes every run. Every number below is counted from them by it; "
        "none was typed. What [willow](../../README.md)'s own tools say of it "
        "is in [results/checks.md](results/checks.md).\n"
    )
    w("## In short\n")
    w(
        f"No model anywhere: {n(c3['sources'])} repositories, the AI-built Craft apps "
        f"and what they are built from, taken apart into {n(c3['pieces']['pieces'])} "
        f"pieces by SHA-256 ({n(c3['pieces']['files'])} files, "
        f"{mb(c3['pieces']['piece_bytes'])}; {n(c3['pieces']['shared_pieces'])} pieces in "
        f"two or more sources), and {n(c3['rebuilt'])} of {n(c3['sources'])} rebuilt from "
        f"those pieces alone to their exact git trees. Then {len(apps)} of the apps "
        f"({', '.join(apps)}), with {n(c3['git'])} crates they take by git, all "
        f"from the same pieces, assembled by written rules into one Cargo workspace "
        f"of {n(c3['members'])} packages: in run {RUNS[-1]}, {n(c3['builds'][0] - len(c3['builds'][1]))} "
        f"of the {n(c3['builds'][0])} packages that build in their own app build in it, and "
        f"{n(c3['tests'][0] - len(c3['tests'][1]))} of the {n(c3['tests'][0])} whose tests pass "
        f"in their own app pass them in it. "
        + ("Every pass rule held. " if held_all else "Not every pass rule held. ")
        + f"It took {len(frozen['freezes'])} freezes, each made before its run, and "
        f"{sum(1 for r in R.values() if any(v != 'satisfied' for v in r['verdicts'].values()))} "
        "runs that failed, kept beside the one that held.\n"
    )
    w(table(["Run", "Freeze", "When (UTC)", *RULES],
            [[str(r), str(x["freeze"]), x["ts"] or "-",
              *[("**failing**" if x["verdicts"].get(k) == "failing" else x["verdicts"].get(k, "-")) for k in RULES]]
             for r, x in R.items()]) + "\n")  # fmt: skip

    w("## 1. Why: AI rebuilding large programs\n")
    w(
        "Quoted whole from [BACKGROUND.md](BACKGROUND.md), written before the "
        "study; its facts are from search summaries, as it says, and nothing "
        "here checks them.\n"
    )
    w(section(background, background.splitlines()[0], down=1) + "\n")

    w("## 2. Before the study\n")
    w(
        "The research's repositories, Apache-compatible licences only, were made "
        "into a kernel box and asked questions; the script that did it became "
        "the `repo-pile` add-on, and running it found two things `privacy` "
        "missed. Quoted whole from [CHANGELOG.md](../../CHANGELOG.md):\n"
    )
    for starts in ("- `repo-pile`:", "- `privacy` also withholds a national phone"):
        w("> " + entry(changelog, starts).replace("\n", "\n> ") + "\n")

    w("## 3. The study's claim, and how it could be wrong\n")
    w("Quoted whole from [README.md](README.md), written before the runs.\n")
    w(section(readme, "## The claim", down=1) + "\n")
    w(section(readme, "## How it could be wrong, and what answers it", down=1) + "\n")

    w("## 4. The sources\n")
    w(
        f"{n(len(pins))} sources, pinned {src['pinned']} by address, commit and git "
        f"tree in [sources.json](sources.json), never their text: "
        f"{n(sum(1 for k in pins if '@' not in k))} apps, {n(len(libs))} commits of "
        f"their shared `craft-libs`, and {n(sum(1 for k in pins if '@' in k) - len(libs))} "
        f"repositories the apps take crates from by git. The composite's apps are "
        f"marked.\n"
    )
    w(table(["Source", "Commit", "Address"],
            [[f"**{k}**" if k in apps else k, p["commit"][:10], p["url"]]
             for k, p in pins.items()]) + "\n")  # fmt: skip

    w("## 5. The freezes\n")
    w(
        "Each freeze is the SHA-256 of the study's tools, held in "
        "[FROZEN.json](FROZEN.json) and by a test, committed before its run. A "
        "run's freeze below is found by hashing: the freeze whose files hash as "
        "the tools on that run's verdict rows did.\n"
    )
    w(table(["Freeze", "Commit", "Why", "Run judged by it"],
            [[str(f["freeze"]), f.get("commit", "not in FROZEN.json"), f["why"],
              ", ".join(str(r) for r, x in R.items() if x["freeze"] == f["freeze"]) or "-"]
             for f in frozen["freezes"]]) + "\n")  # fmt: skip
    w("What was seen before each, quoted whole from [README.md](README.md):\n")
    for h in ("## What was seen before freeze 1", "## Freeze 2, and what was seen before it",
              "## Freeze 3, and what was seen before it"):  # fmt: skip
        w("#" + h + "\n")
        w(section(readme, h, down=1) + "\n")

    w("## 6. The runs, counted\n")
    w(table(["", *(f"Run {r}" for r in R)], [
        ["sources rebuilt to their trees", *(f"{n(x['c']['rebuilt'])} of {n(x['c']['sources'])}" for x in R.values())],
        ["files taken apart", *(n(x["c"]["pieces"]["files"]) for x in R.values())],
        ["pieces in the store", *(n(x["c"]["pieces"]["pieces"]) for x in R.values())],
        ["pieces in two or more sources", *(n(x["c"]["pieces"]["shared_pieces"]) for x in R.values())],
        ["composite members", *(n(x["c"]["members"]) for x in R.values())],
        ["crates from outside the apps", *(n(x["c"]["git"]) for x in R.values())],
        ["left out by the rules", *(n(len(x["c"]["left_out"])) for x in R.values())],
        ["a lockfile resolved", *("yes" if x["c"]["lock"] else "**no**" for x in R.values())],
        ["crates moved to the apps' versions", *(n(len(x["c"]["pinned"])) for x in R.values())],
        ["moves Cargo refused", *(n(len(x["c"]["not_pinned"])) for x in R.values())],
        ["packages tried alone", *(n(x["c"]["baseline"]) for x in R.values())],
        ["packages tried in the composite", *(n(x["c"]["composite"]) for x in R.values())],
        ["build alone, and in the composite", *(f"{n(x['c']['builds'][0] - len(x['c']['builds'][1]))} of {n(x['c']['builds'][0])}" for x in R.values())],
        ["pass alone, and in the composite", *(f"{n(x['c']['tests'][0] - len(x['c']['tests'][1]))} of {n(x['c']['tests'][0])}" for x in R.values())],
        ["results SHA-256", *(f"`{x['sha'][:16]}…`" for x in R.values())],
    ]) + "\n")  # fmt: skip
    for r, x in R.items():
        c = x["c"]
        lost = {f: names(c[f][1]) if len(c[f][1]) < 10 else f"all {n(len(c[f][1]))}"
                for f in ("builds", "tests")}  # fmt: skip
        w(f"**Run {r}.** Lost builds: {lost['builds']}. Lost tests: {lost['tests']}. "
          + "Outcomes in the composite that differ from the app alone: "
          + (f"{n(len(c['differ']))}." if c["differ"] else "none."
             ) + "\n")  # fmt: skip

    w(f"## 7. Run {RUNS[-1]}, the composite\n")
    per = []
    for app in apps:
        b, k = (
            last["res"]["baseline"].get(app, {}),
            last["res"]["composite"].get(app, {}),
        )
        held = last["res"]["composite_members"].get(app, [])
        per.append([app, n(len(held)),
                    n(sum(1 for p in held if b.get(p, {}).get("builds"))), n(sum(1 for p in held if k.get(p, {}).get("builds"))),
                    n(sum(1 for p in held if b.get(p, {}).get("tests"))), n(sum(1 for p in held if k.get(p, {}).get("tests")))])  # fmt: skip
    w(
        table(
            [
                "App",
                "Members",
                "Build alone",
                "Build in it",
                "Pass alone",
                "Pass in it",
            ],
            per,
        )
        + "\n"
    )
    w(
        "**Crates from outside the apps**, each from the store, with the apps that use it:\n"
    )
    git = last["res"]["glue"]["git"]
    w(table(["Crate", "From", "Used by"],
            [[f"`{k}`", v["source"], ", ".join(v["used_by"]) or "other crates here, by path"]
             for k, v in sorted(git.items())]) + "\n")  # fmt: skip
    w("**Left out by the rules**, and whether it built in its own app:\n")
    loh = set(c3["left_out_held"] or [])
    w(table(["Member", "Why", "Built alone"],
            [[f"`{x['member']}`", x["why"],
              "yes" if f"{x['member'].split('/')[0]}/{Path(x['member']).name}" in loh else "no"]
             for x in c3["left_out"]]) + "\n")  # fmt: skip
    w(
        f"**Rule 7 moved {n(len(c3['pinned']))} crates** to the version the apps "
        f"locked: " + ", ".join(f"`{p}`" for p in c3["pinned"]) + ".\n"
    )
    w(
        f"**Cargo refused {n(len(c3['not_pinned']))} moves**, each a crate another "
        f"needed newer: " + ", ".join(f"`{p}`" for p in c3["not_pinned"]) + ".\n"
    )
    w(
        "**Profile settings dropped** (rule 4), since the apps set them "
        "differently: " + ", ".join(f"`{p}`" for p in c3["dropped"]) + ".\n"
    )

    w("## 8. What each run found, in the words written after it\n")
    w(
        "Quoted whole from [README.md](README.md), which was written by hand "
        "after each run; [results/checks.md](results/checks.md) holds it to "
        "the counts above.\n"
    )
    for h in ("### Run 3, 2026-10-25: every rule held",
              "### Run 2, 2026-10-25: four rules held; two packages lost their tests",
              "### Run 1, 2026-10-25: taking apart held; assembling failed"):  # fmt: skip
        w(h + "\n")
        w(section(readme, h, down=1) + "\n")

    w("## 9. The record\n")
    seals = [r for r in rows if r["kind"] == "seal"]
    w(
        "The verdicts are rows on a kernel record kept outside the repo; "
        "[results/record.jsonl](results/record.jsonl) is a copy of it, without "
        "its key. Read by the kernel's own `read`: "
        + (
            "the chain holds"
            if not breaks
            else "**the chain breaks**: " + "; ".join(breaks)
        )
        + f", {n(len(rows))} rows, {n(len(seals))} of them seals. Each run's rows "
        f"name the SHA-256 of its results, and each results file above hashes to it.\n"
    )
    w(table(["Row", "When (UTC)", "Gate", "State", "Results"],
            [[str(r["n"]), r["ts"], r.get("gate", r["kind"]), r.get("state", "-"),
              next((x["file"] for x in R.values() if x["sha"] == r.get("results_sha256")), "-")]
             for r in rows]) + "\n")  # fmt: skip
    w(
        "No row is sealed. Sealing is the person's, with their key, and nothing "
        "in this study, this report or its checks reads the key.\n"
    )

    w("## 10. How this report was made\n")
    w(table(["Input", "SHA-256"],
            [[link(p, p), f"`{sha(HERE / p)[:16]}…`"] for p in INPUTS if p != "report.py"]
            + [["[CHANGELOG.md](../../CHANGELOG.md), two entries", "-"]]) + "\n")  # fmt: skip
    w(
        "    python demo/craft-assembly/report.py write    # this file, then results/checks.md\n"
        "    python demo/craft-assembly/report.py check    # exit 1 if either would change\n"
    )
    w(
        "Of willow's add-ons: the kernel's `read` checks the record; `xref` "
        "checks every reference in this folder, this file's included; "
        "`claim-check` looks for each counted claim in the hand-written README. "
        "`serve` (pull request 43) was left out: it hands a model "
        "only a scope the person has sealed, with ids drawn at random each "
        "run, so it can't be part of a file made the same every time; once "
        "this report is sealed as a scope, it is the way to serve it.\n"
    )
    return "\n".join(out).rstrip() + "\n"


def claims() -> list[str]:
    """Short claims, counted from the results, for claim-check to look for
    in the README."""
    R = runs()
    out = []
    for r, x in R.items():
        c = x["c"]
        b, t = (c[f][0] - len(c[f][1]) for f in ("builds", "tests"))
        out += [f"all {c['sources']} sources rebuilt from the store",
                f"{c['builds'][0]} packages build in their own app; none builds in the composite" if not b
                else f"{b} of the {c['builds'][0]} packages build" if c["builds"][1]
                else f"all {b} packages build in it",
                f"{c['tests'][0]} pass their tests in their own app; none in the composite" if not t
                else f"{t} of the {c['tests'][0]} pass their tests" if c["tests"][1]
                else f"all {t} pass their tests in it"]  # fmt: skip
    c = R[RUNS[-1]]["c"]
    out += [f"{c['pieces']['pieces']:,} pieces", f"{c['pieces']['files']:,} files",
            f"{c['pieces']['shared_pieces']:,} of them in two or more sources",
            f"{c['members']} packages", f"{c['git']} crates", f"moved {len(c['pinned'])} crates",
            f"refused {len(c['not_pinned'])} moves"]  # fmt: skip
    return list(dict.fromkeys(out))


def quiet(argv: list[str]) -> str:
    got = subprocess.run(
        [sys.executable, *argv], cwd=ROOT, capture_output=True, text=True
    )
    return (got.stdout + got.stderr).strip()


def render_checks() -> str:
    rows, breaks = record()
    R = runs()
    out = ["# What willow's tools say of the report\n",
           "Written by [report.py](../report.py) `write`, after "
           "[REPORT.md](../REPORT.md), the same bytes every run.\n"]  # fmt: skip
    w = out.append
    w("## The record, read by the kernel\n")
    w(
        f"`kernel.read` on {link('record.jsonl', 'record.jsonl')}: "
        + ("the chain holds" if not breaks else "the chain breaks")
        + f", {len(rows)} rows.\n"
    )
    for r, x in R.items():
        w(f"- run {r}: {link(Path(x['file']).name, Path(x['file']).name)} hashes to `{x['sha'][:16]}…`, "
          f"named by {len(x['rows'])} rows ({', '.join(str(row['n']) for row in x['rows'])})")  # fmt: skip
    w("")
    w("## Every reference in the folder, by xref\n")
    w("    python adapters/stdlib/xref/xref.py --from demo/craft-assembly\n")
    w(
        "    "
        + quiet(
            ["adapters/stdlib/xref/xref.py", "--from", "demo/craft-assembly"]
        ).replace("\n", "\n    ")
        + "\n"
    )
    w("## The counts, looked for in the README by claim-check\n")
    w(
        "Each claim below is counted from the results by report.py, and looked "
        "for in [README.md](../README.md) alone, a box made of it in a scratch "
        "folder. `all parts` means a passage of the README holds every word of "
        "it; anything else is said as claim-check said it.\n"
    )
    with tempfile.TemporaryDirectory() as t:
        pile = Path(t) / "pile"
        pile.mkdir()
        (pile / "README.md").write_bytes((HERE / "README.md").read_bytes())
        with contextlib.redirect_stdout(io.StringIO()):
            kernel.init(Path(t) / "box", pile, Path(t) / "key", R[RUNS[-1]]["ts"])
        rows_ = []
        for claim in claims():
            got = quiet(["adapters/stdlib/claim-check/claim_check.py", "--box",
                         str(Path(t) / "box"), claim, "--top", "1"]).splitlines()  # fmt: skip
            first = got[0] if got else "nothing"
            parts = re.split(r"\s{2,}", first.strip())
            rows_.append([claim, parts[0], parts[1] if len(parts) > 1 else "-"])
    w(table(["Claim", "claim-check", "Where"], rows_) + "\n")
    held = sum(1 for r in rows_ if r[1] == "all parts")
    w(f"{held} of {len(rows_)} found whole.\n")
    return "\n".join(out).rstrip() + "\n"


def main(argv: list[str]) -> int:
    if argv not in (["write"], ["check"]):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    report = render()
    if argv == ["write"]:
        REPORT.write_text(report, encoding="utf-8")
        for _ in range(3):  # xref reads checks.md too: write till it holds still
            checks = render_checks()
            if CHECKS.exists() and CHECKS.read_text(encoding="utf-8") == checks:
                break
            CHECKS.write_text(checks, encoding="utf-8")
        print(f"wrote {REPORT.relative_to(ROOT)} and {CHECKS.relative_to(ROOT)}")
        return 0
    stale = [p.name for p, want in ((REPORT, report), (CHECKS, render_checks()))
             if not p.exists() or p.read_text(encoding="utf-8") != want]  # fmt: skip
    for s in stale:
        print(f"{s} would change: run report.py write")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
