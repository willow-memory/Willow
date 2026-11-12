"""strangers_notebooks.py: the door met by two signers nobody enrolled, one of them a liar, as Kaggle notebooks.

    python demo/shared-runs/door/strangers/strangers_notebooks.py make --user NAME --to DIR
        [--plan PLAN --starts STARTS]

DIR gets a folder for each notebook, in the order they are pushed:

    round-1-machine-K          the first round, each place signing as itself
    round-2-machine-K-before   the second round, by a taker the ring knows,
                               given its own place's first round
    check                      every kept state and every halt of the five
                               first rounds stepped again, by a checker
                               the ring knows
    round-2-machine-K-after    for the two places nobody enrolled: the second
                               round again, given the check as well

Two places sign their first round with identities the ring does not
hold: place 1, which is honest, and place 3, which changes one kept
state and writes one halt that is no halt, and seals that with its own
key (lie.py). The takers, the checker and places 0, 2 and 4 are in the
ring.

So before the check, the takers of places 1 and 3 should hold what they
are given and step from nothing; after it, place 1 should be taken on
the checker's word and place 3 still held; and no job anywhere should
come to a wrong byte.

Every identity is made here, for this run and no other, and is nobody's
key. NAME is the Kaggle account; it goes only into DIR, which is refused
if it is inside this repository.

Exit codes, the kernel's: 0 made; 2 refused.
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
STRANGER, LIAR = 1, 3
CARRIED = {
    "sweep.py": STUDY,
    "runner.py": STUDY,
    "machine.py": DOOR,
    "ed25519.py": SHARE,
    "lie.py": HERE,
}

SCRIPT = '''"""One machine's part of a shared run with a door on it. Made by
demo/shared-runs/door/strangers/strangers_notebooks.py in the willow repository; it decides nothing."""

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
    if code == 0 and ROLE.get("lies"):
        told = subprocess.run([sys.executable, str(scratch / "lie.py"), "--run", str(out),
                               "--plan", str(scratch / "plan.json"), "--starts", str(scratch / "starts.json"),
                               "--machine", str(ROLE["machine"]), "--id", str(scratch / "id"),
                               "--to", str(working / (ROLE["name"] + ".lied.json"))], env=env)
        if told.returncode != 0:
            sys.exit(f"{ROLE['name']}: the lie was not told")
    if code not in ROLE["ends"]:
        sys.exit(f"{ROLE['name']}: ended {code}, and {ROLE['ends']} was looked for")
    print(ROLE["name"], "ended", code, (out / "machine.json").read_text().strip())
    for line in (out / "log.jsonl").read_text().splitlines():
        row = json.loads(line)
        print({k: v for k, v in row.items() if k not in ("prev", "hash")})


main()
'''


def roles(plan: dict) -> list[dict]:
    """Each notebook, in the order it is pushed: what it runs, whose
    identity it signs with, what it is given, and how it may end."""
    out: list[dict] = []
    places = range(plan["machines"])
    for k in places:
        out.append({"name": f"round-1-machine-{k}", "mode": "shared", "machine": k, "round": 1,
                    "needs": [], "memory": [], "ends": [0], "signs": f"place {k}", "lies": k == LIAR})  # fmt: skip
    for k in places:
        own = [f"round-1-machine-{k}"]
        out.append({"name": f"round-2-machine-{k}-before", "mode": "shared", "machine": k, "round": 2,
                    "needs": own, "memory": own, "ends": [42] if k in (STRANGER, LIAR) else [0],
                    "signs": f"taker {k}"})  # fmt: skip
    firsts = [f"round-1-machine-{k}" for k in places]
    out.append({"name": "check", "mode": "check", "needs": firsts, "memory": firsts, "ends": [0],
                "signs": "checker"})  # fmt: skip
    for k in (STRANGER, LIAR):
        given = [f"round-1-machine-{k}", "check"]
        out.append({"name": f"round-2-machine-{k}-after", "mode": "shared", "machine": k, "round": 2,
                    "needs": given, "memory": given, "ends": [0] if k == STRANGER else [42],
                    "signs": f"taker {k}"})  # fmt: skip
    return out


def slug(name: str) -> str:
    return f"shared-runs-strangers-{name}"


def signers(plan: dict) -> list[str]:
    places = range(plan["machines"])
    return [*(f"place {k}" for k in places), *(f"taker {k}" for k in places), "checker"]


def enrolled(name: str) -> bool:
    return name not in (f"place {STRANGER}", f"place {LIAR}")


def script(role: dict, files: dict[str, str], ring: dict[str, str], seed: str) -> str:
    sha = {n: hashlib.sha256(t.encode("utf-8")).hexdigest() for n, t in files.items()}
    project = json.loads(files["plan.json"]).get("project") or {}
    told = {k: v for k, v in role.items() if k != "signs"}
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


def make(plan_path: Path, starts_path: Path, user: str, to: Path) -> list[str]:
    plan = sweep.load(plan_path)
    files = {"plan.json": plan_path.read_text(encoding="utf-8"),
             "starts.json": starts_path.read_text(encoding="utf-8")}  # fmt: skip
    files.update({n: (d / n).read_text(encoding="utf-8") for n, d in CARRIED.items()})
    if set(json.loads(files["starts.json"])) != {
        t["name"] for t in plan["trajectories"]
    }:
        raise ValueError("the starts are not this plan's")
    seeds = {name: secrets.token_bytes(32).hex() for name in signers(plan)}
    ring = {
        ed25519.public(bytes.fromhex(s)).hex(): n
        for n, s in seeds.items()
        if enrolled(n)
    }
    made = []
    to.mkdir(parents=True)
    for role in roles(plan):
        folder = to / role["name"]
        folder.mkdir()
        (folder / "run.py").write_text(script(role, files, ring, seeds[role["signs"]]), encoding="utf-8")  # fmt: skip
        (folder / "kernel-metadata.json").write_text(json.dumps(metadata(role, user), indent=1) + "\n")  # fmt: skip
        made.append(role["name"])
    (to / "ring.json").write_text(json.dumps(ring, indent=1) + "\n")
    strangers = {
        ed25519.public(bytes.fromhex(s)).hex(): n
        for n, s in seeds.items()
        if not enrolled(n)
    }
    (to / "strangers.json").write_text(json.dumps(strangers, indent=1) + "\n")
    (to / "order.txt").write_text("\n".join(made) + "\n")
    return made


def main(argv: list[str]) -> int:
    opts: dict = {}
    it = iter(argv[1:])
    for a in it:
        if a in ("--user", "--to", "--plan", "--starts") and a[2:] not in opts:
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
        if to.is_relative_to(HERE.parents[3]):
            raise ValueError("DIR is inside the repository; an account's name and a run's keys are not kept here")  # fmt: skip
        if to.exists():
            raise ValueError(f"{to} is already there")
        made = make(Path(opts.get("plan") or STUDY / "plan.json"),
                    Path(opts.get("starts") or STUDY / "starts.json"), opts["user"], to)  # fmt: skip
    except (OSError, ValueError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return REFUSED
    print(f"made {len(made)} notebooks under {to}, to push in the order of order.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
