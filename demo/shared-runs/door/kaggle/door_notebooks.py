"""door_notebooks.py: the door's machine as Kaggle notebooks, for a plan: cut and carried on, sealed, each given only its own place's earlier work.

    python demo/shared-runs/door/kaggle/door_notebooks.py make --user NAME --to DIR
        [--plan PLAN --starts STARTS] [--cut SECONDS]

DIR gets a folder for each notebook, in the order they are pushed:

    round-1-machine-K-a   the first round, stopped by a budget of SECONDS (10)
    round-1-machine-K     the same round, carried on from what `-a` left
    round-R-machine-K     a later round, given its own place's earlier rounds
    check                 every kept state of every round stepped again

A machine's part is cut on purpose: a notebook's output is all or nothing,
so a long part must be several short ones, and this is the first time
one is carried from a notebook to the next. If the part comes back on
another kind of processor, machine.py refuses to go on in that folder;
the notebook then starts the part over, and says so in `restarted.json`.

Each place has an identity made here, for this run and no other, and
the check has one; every notebook carries the ring of their public
halves. A place's secret half is in that place's notebooks only, which
are private, and in DIR. They are not anyone's key: nothing they sign
is an approval.

A script carries the plan, the starts, sweep.py, runner.py, machine.py
and the share add-on's ed25519.py inside itself, each held to its
SHA-256 when it is unpacked. NAME is the Kaggle account; it goes only
into DIR, which is refused if it is inside this repository.

It reads the files it carries and writes DIR. Exit codes, the kernel's:
0 made; 2 refused (a bad command line, a plan that isn't one, a DIR
inside the repository or already there).
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOOR, STUDY = HERE.parent, HERE.parents[1] / "study"
SHARE = HERE.parents[3] / "adapters" / "stdlib" / "share"
for place in (STUDY, SHARE):
    sys.path.insert(0, str(place))
import ed25519  # noqa: E402
import sweep  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
REFUSED = 2
CARRIED = {
    "sweep.py": STUDY,
    "runner.py": STUDY,
    "machine.py": DOOR,
    "ed25519.py": SHARE,
}

SCRIPT = '''"""One machine's part of a shared run with a door on it. Made by
demo/shared-runs/door/kaggle/door_notebooks.py in the willow repository; it decides nothing."""

import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROLE = __ROLE__
PROJECT = __PROJECT__
SHA256 = __SHA256__
RING = __RING__
SEED = __SEED__
FILES = __FILES__


def main():
    inputs = Path(os.environ.get("SHARED_RUNS_INPUT", "/kaggle/input"))
    working = Path(os.environ.get("SHARED_RUNS_WORKING", "/kaggle/working"))
    scratch = Path(tempfile.mkdtemp())
    for name, text in FILES.items():
        data = text.encode("utf-8")
        if hashlib.sha256(data).hexdigest() != SHA256[name]:
            sys.exit(f"{name} is not the file that was frozen")
        (scratch / name).write_bytes(data)
    (scratch / "ring.json").write_text(json.dumps(RING))
    (scratch / "id").write_text("ed25519 " + SEED + "\\n")

    env = dict(os.environ)
    stepper = os.environ.get("SHARED_RUNS_STEPPER", "").split()
    if not stepper:
        repo = os.environ.get("SHARED_RUNS_REPO")
        if not repo:
            address = f"{PROJECT['address']}/archive/{PROJECT['commit']}.zip"
            with urllib.request.urlopen(address, timeout=120) as got:
                zipfile.ZipFile(io.BytesIO(got.read())).extractall(scratch / "project")
            repo = str(next((scratch / "project").iterdir()))
        stepper = ["--repo", repo]
        want = PROJECT.get("numpy")
        import numpy

        if want and numpy.__version__ != want:
            beside = scratch / "numpy"
            subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--target",
                            str(beside), f"numpy=={want}"], check=True)
            env["PYTHONPATH"] = str(beside) + os.pathsep + env.get("PYTHONPATH", "")

    found = {p.parent.name: p.parent for p in inputs.rglob("run.json")}
    missing = sorted(set(ROLE["needs"]) - set(found))
    if missing:
        sys.exit(f"an earlier notebook's output is not among the inputs: {missing}")
    out = working / ROLE["name"]
    base = [sys.executable, str(scratch / "machine.py"), ROLE["mode"],
            "--plan", str(scratch / "plan.json"), "--starts", str(scratch / "starts.json"),
            "--to", str(out), "--id", str(scratch / "id"), "--ring", str(scratch / "ring.json"),
            *stepper]
    if ROLE["mode"] == "shared":
        base += ["--machine", str(ROLE["machine"]), "--round", str(ROLE["round"])]
    for name in ROLE["memory"]:
        base += ["--memory", str(found[name])]
    more = []
    if ROLE.get("budget") is not None:
        more += ["--budget", str(ROLE["budget"])]
    if ROLE.get("from"):
        more += ["--from", str(found[ROLE["from"]])]
    code = subprocess.run(base + more, env=env).returncode
    if code == 2 and ROLE.get("from"):
        # refused to go on from what the notebook before left: said, and begun over
        why = [json.loads(x) for x in (out / "log.jsonl").read_text().splitlines()][-1]
        for old in out.iterdir():
            old.unlink()
        code = subprocess.run(base, env=env).returncode
        (out / "restarted.json").write_text(json.dumps({"refused": why.get("why")}) + "\\n")
    if code not in ROLE["ends"]:
        sys.exit(f"{ROLE['name']}: ended {code}, and {ROLE['ends']} was looked for")
    print(ROLE["name"], "ended", code, (out / "machine.json").read_text().strip())
    for line in (out / "log.jsonl").read_text().splitlines():
        row = json.loads(line)
        print({k: v for k, v in row.items() if k not in ("prev", "hash")})


main()
'''


def roles(plan: dict, cut: int) -> list[dict]:
    """Each notebook of the plan, in the order it is pushed: its name, what
    it runs, the earlier notebooks whose output it is given, and how it
    may end."""
    out: list[dict] = []
    places = range(plan["machines"])
    for k in places:
        out.append({"name": f"round-1-machine-{k}-a", "mode": "shared", "machine": k, "round": 1,
                    "needs": [], "memory": [], "budget": cut, "ends": [0, 42], "place": k})  # fmt: skip
    for k in places:
        first = f"round-1-machine-{k}-a"
        out.append({"name": f"round-1-machine-{k}", "mode": "shared", "machine": k, "round": 1,
                    "needs": [first], "memory": [], "from": first, "ends": [0], "place": k})  # fmt: skip
    for r in range(2, plan["rounds"] + 1):
        for k in places:
            before = [f"round-{q}-machine-{k}" for q in range(1, r)]
            out.append({"name": f"round-{r}-machine-{k}", "mode": "shared", "machine": k, "round": r,
                        "needs": before, "memory": before, "ends": [0], "place": k})  # fmt: skip
    every = [
        f"round-{r}-machine-{k}" for r in range(1, plan["rounds"] + 1) for k in places
    ]
    out.append({"name": "check", "mode": "check", "needs": every, "memory": every, "ends": [0],
                "place": "check"})  # fmt: skip
    return out


def slug(name: str) -> str:
    return f"shared-runs-door-{name}"


def carried(plan_text: str, starts_text: str) -> dict[str, str]:
    files = {"plan.json": plan_text, "starts.json": starts_text}
    files.update({n: (d / n).read_text(encoding="utf-8") for n, d in CARRIED.items()})
    return files


def script(role: dict, files: dict[str, str], ring: dict[str, str], seed: str) -> str:
    sha = {n: hashlib.sha256(t.encode("utf-8")).hexdigest() for n, t in files.items()}
    project = json.loads(files["plan.json"]).get("project") or {}
    told = {k: v for k, v in role.items() if k != "place"}
    out = SCRIPT
    for mark, value in (("__ROLE__", told), ("__PROJECT__", project), ("__SHA256__", sha),
                        ("__RING__", ring), ("__SEED__", seed), ("__FILES__", files)):  # fmt: skip
        assert out.count(mark) == 1
        out = out.replace(mark, repr(value))
    return out


def metadata(role: dict, user: str) -> dict:
    """What Kaggle's command line reads to push one notebook."""
    return {
        "id": f"{user}/{slug(role['name'])}",
        "title": slug(role["name"]),
        "code_file": "run.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": False,
        "enable_internet": True,
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [f"{user}/{slug(n)}" for n in role["needs"]],
    }


def make(plan_path: Path, starts_path: Path, user: str, to: Path, cut: int = 10,
         seeds: dict | None = None) -> list[str]:  # fmt: skip
    plan = sweep.load(plan_path)
    files = carried(
        plan_path.read_text(encoding="utf-8"), starts_path.read_text(encoding="utf-8")
    )
    if set(json.loads(files["starts.json"])) != {
        t["name"] for t in plan["trajectories"]
    }:
        raise ValueError("the starts are not this plan's")
    places = [*range(plan["machines"]), "check"]
    seeds = seeds or {p: secrets.token_bytes(32).hex() for p in places}
    ring = {ed25519.public(bytes.fromhex(seeds[p])).hex(): f"place {p}" for p in places}
    made = []
    to.mkdir(parents=True)
    for role in roles(plan, cut):
        folder = to / role["name"]
        folder.mkdir()
        (folder / "run.py").write_text(script(role, files, ring, seeds[role["place"]]), encoding="utf-8")  # fmt: skip
        (folder / "kernel-metadata.json").write_text(json.dumps(metadata(role, user), indent=1) + "\n")  # fmt: skip
        made.append(role["name"])
    (to / "ring.json").write_text(json.dumps(ring, indent=1) + "\n")
    (to / "order.txt").write_text("\n".join(made) + "\n")
    return made


def main(argv: list[str]) -> int:
    opts: dict = {}
    it = iter(argv[1:])
    for a in it:
        if a in ("--user", "--to", "--plan", "--starts", "--cut") and a[2:] not in opts:
            opts[a[2:]] = next(it, "")
        else:
            opts = {}
            break
    if argv[:1] != ["make"] or not opts.get("user") or not opts.get("to"):
        print(USAGE, file=sys.stderr)
        return REFUSED
    to = Path(opts["to"]).resolve()
    try:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", opts["user"]):
            raise ValueError("NAME is not a Kaggle account's name")
        if not opts.get("cut", "10").isdigit():
            raise ValueError("SECONDS must be a whole number")
        if to.is_relative_to(HERE.parents[3]):
            raise ValueError("DIR is inside the repository; an account's name and a run's keys are not kept here")  # fmt: skip
        if to.exists():
            raise ValueError(f"{to} is already there")
        made = make(Path(opts.get("plan") or STUDY / "plan.json"),
                    Path(opts.get("starts") or STUDY / "starts.json"), opts["user"], to,
                    int(opts.get("cut", "10")))  # fmt: skip
    except (OSError, ValueError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return REFUSED
    print(f"made {len(made)} notebooks under {to}, to push in the order of order.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
