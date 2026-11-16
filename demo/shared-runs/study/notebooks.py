"""notebooks.py: the study's Kaggle notebooks, made from the frozen files:
one script a machine run, each whole in itself.

    python demo/shared-runs/study/notebooks.py make --user NAME --to DIR
        [--plan PLAN --starts STARTS]

DIR gets a folder for each machine run of the plan: the baseline twice,
each round's machines, and the check. In each is one script and the small
file Kaggle's command line reads to push it: private, CPU only, internet
on. A later round's file names the earlier rounds' notebooks as its
inputs, and the check's names every round's; so one notebook's output is
the next one's input, and nothing is carried by hand.

A script carries the plan, the starts, sweep.py and runner.py inside
itself, each held to its SHA-256 when it is unpacked, so nothing else is
uploaded. When it runs it fetches the project at the plan's commit,
installs the plan's NumPy beside the machine's own if that is another,
and calls runner.py for its part. It decides nothing: what to run is the
plan's, and what is kept is runner.py's.

NAME is the Kaggle account the notebooks are pushed from. It goes only
into the files under DIR, which is refused if it is inside this
repository: an account's name is not the repository's to keep.

It reads the frozen files and writes DIR. Exit codes, the kernel's: 0
made; 2 refused (a bad command line, a plan that isn't one, a DIR inside
the repository or already there).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sweep  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
REFUSED = 2
CARRIED = ("sweep.py", "runner.py")

SCRIPT = '''"""One machine's part of the shared-runs study. Made by notebooks.py from the
frozen files; it decides nothing. See demo/shared-runs in the willow repository."""

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
FILES = __FILES__


def main():
    inputs = Path(os.environ.get("SHARED_RUNS_INPUT", "/kaggle/input"))
    working = Path(os.environ.get("SHARED_RUNS_WORKING", "/kaggle/working"))
    scratch = Path(tempfile.mkdtemp())
    study = scratch / "study"
    study.mkdir()
    for name, text in FILES.items():
        data = text.encode("utf-8")
        if hashlib.sha256(data).hexdigest() != SHA256[name]:
            sys.exit(f"{name} is not the file that was frozen")
        (study / name).write_bytes(data)

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

    kept = sorted({p.parent for p in inputs.rglob("memory.jsonl")
                   if p.parent.name.startswith("round-")})
    earlier = [p for p in kept if int(p.name.split("-")[1]) < ROLE.get("round", 10**9)]
    missing = sorted(set(ROLE["needs"]) - {p.name for p in earlier})
    if missing:
        sys.exit(f"an earlier round's output is not among the inputs: {missing}")
    out = working / ROLE["name"]
    for mode in ROLE["modes"]:
        cmd = [sys.executable, str(study / "runner.py"), mode,
               "--plan", str(study / "plan.json"), "--starts", str(study / "starts.json"),
               "--to", str(out), *stepper]
        if mode == "shared":
            cmd += ["--machine", str(ROLE["machine"]), "--round", str(ROLE["round"])]
        if mode in ("shared", "check"):
            for folder in earlier:
                cmd += ["--memory", str(folder)]
        if subprocess.run(cmd, env=env).returncode != 0:
            sys.exit(f"{ROLE['name']}: {mode} did not end clean")
    acts = [json.loads(line) for line in (out / "acts.jsonl").read_text().splitlines()]
    print(ROLE["name"], (out / "machine.json").read_text().strip())
    print(len(acts), "acts,", sum(a.get("stepped", 0) for a in acts), "steps stepped")


main()
'''


def roles(plan: dict) -> list[dict]:
    """Each machine run of the plan: its name, what it runs, and the earlier
    runs whose output it must be given."""
    out = [{"name": f"baseline-{b}", "modes": ["alone", "native"], "needs": []} for b in (1, 2)]  # fmt: skip
    before: list[str] = []
    for r in range(1, plan["rounds"] + 1):
        names = [f"round-{r}-machine-{k}" for k in range(plan["machines"])]
        for k, name in enumerate(names):
            out.append({"name": name, "modes": ["shared"], "machine": k, "round": r,
                        "needs": list(before)})  # fmt: skip
        before += names
    out.append({"name": "check", "modes": ["check", "native"], "needs": list(before)})
    return out


def slug(name: str) -> str:
    return f"shared-runs-{name}"


def script(role: dict, plan_text: str, starts_text: str) -> str:
    files = {"plan.json": plan_text, "starts.json": starts_text}
    files.update({name: (HERE / name).read_text(encoding="utf-8") for name in CARRIED})
    sha = {n: hashlib.sha256(t.encode("utf-8")).hexdigest() for n, t in files.items()}
    project = json.loads(plan_text).get("project") or {}
    out = SCRIPT
    for mark, value in (("__ROLE__", role), ("__PROJECT__", project),
                        ("__SHA256__", sha), ("__FILES__", files)):  # fmt: skip
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
    plan_text = plan_path.read_text(encoding="utf-8")
    starts_text = starts_path.read_text(encoding="utf-8")
    if set(json.loads(starts_text)) != {t["name"] for t in plan["trajectories"]}:
        raise ValueError("the starts are not this plan's")
    made = []
    for role in roles(plan):
        folder = to / role["name"]
        folder.mkdir(parents=True)
        (folder / "run.py").write_text(script(role, plan_text, starts_text), encoding="utf-8")  # fmt: skip
        (folder / "kernel-metadata.json").write_text(json.dumps(metadata(role, user), indent=1) + "\n")  # fmt: skip
        made.append(role["name"])
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
        if to.is_relative_to(HERE.parents[2]):
            raise ValueError("DIR is inside the repository; an account's name is not kept here")  # fmt: skip
        if to.exists():
            raise ValueError(f"{to} is already there")
        made = make(Path(opts.get("plan") or HERE / "plan.json"),
                    Path(opts.get("starts") or HERE / "starts.json"), opts["user"], to)  # fmt: skip
    except (OSError, ValueError) as why:
        print(f"refused: {why}", file=sys.stderr)
        return REFUSED
    print(f"made {len(made)} notebooks under {to}: {', '.join(made)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
