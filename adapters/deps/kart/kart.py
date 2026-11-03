"""kart.py: a job someone sent you, run over your own folder in Kartikeya's sandbox.

    python adapters/deps/kart/kart.py policy --box DIR
    python adapters/deps/kart/kart.py take   --box DIR --package FILE --words "your words" [--now TS]
    python adapters/deps/kart/kart.py run    --box DIR --job proposal:<sha256> --to FILE [--timeout SECONDS] [--now TS]

A job is a shell task, as Kartikeya runs them, that came to you in a share
package. It never runs because it arrived. `take` puts it at the kernel's
door as a proposal of yours, under your own words, citing nothing; only you
seal it, through the kernel. `run` runs a job you sealed, and nothing else.

It runs in Kartikeya's bubblewrap sandbox under a policy of willow's, not
Kartikeya's default: your folder read-only, one scratch folder of its own,
the system's /usr read-only, private /tmp, no network, and no environment
variable of yours. The box and the key are never in it. `{pile}` and
`{scratch}` in the job are its two folders, as they are mounted. A job that
asks for the network (`# allow_net`, `# allow_db`, `# allow_localhost`) is
refused before anything runs, and Kartikeya's own scan refuses commands it
reads as harmful before any sandbox is built. `policy` prints the policy.

What the job printed is written to FILE, and on your record as a `ran` row:
the job, how it ended, its output's SHA-256 and what the sandbox bound,
never the output. A job that ended well is proposed as an answer of yours,
citing nothing and waiting on your seal: what it found came from your
files, so nothing of it goes anywhere but by your seal and share.

Exit codes, the kernel's: 0 the policy printed; 42 a job taken or a result
proposed, waiting on your seal, or a job that failed; 2 refused (no
bubblewrap or Kartikeya, a job not sealed, one asking for the network).
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shlex
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "share"))
import share  # noqa: E402

#: Kartikeya's directives that open the network or the database: refused here
NETWORK = ("# allow_net", "# allow_db", "# allow_localhost")
OUTPUT = 20_000  # characters of a job's output proposed as an answer
FLAGS = {
    "policy": ({"--box"}, set()),
    "take": ({"--box", "--package", "--words"}, {"--now"}),
    "run": ({"--box", "--job", "--to"}, {"--timeout", "--now"}),
}


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def box_rows(box: Path) -> tuple[list[dict], str | None]:
    if not (box / "kernel.json").exists():
        return [], "not a kernel box; init first"
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return [], f"the record doesn't verify ({breaks[0]}); a person looks first"
    return rows, None


def kernel_says(argv: list[str]) -> tuple[int, str]:
    got = io.StringIO()
    with contextlib.redirect_stdout(got):
        code = kernel.main(argv)
    return code, got.getvalue()


def propose(
    box: Path, words: str, prop: dict, now: list[str]
) -> tuple[str | None, str]:
    """(the subject, what the kernel said): an empty bite under the words,
    then the proposal, at the kernel's door like any other."""
    code, out = kernel_says(["bite", "--box", str(box), *now, words])
    if code == kernel.REFUSED:
        return None, out
    with tempfile.TemporaryDirectory() as tmp:
        sug = Path(tmp) / "suggestion.jsonl"
        sug.write_text(json.dumps(prop) + "\n", encoding="utf-8")
        _, out = kernel_says(["propose", "--box", str(box), *now, "--file", str(sug)])
    return (out.split()[1] if out.startswith("pass") else None), out


# ── the policy ──────────────────────────────────────────────────────────────
def policy(pile: Path, scratch: Path) -> dict:
    """Willow's mount policy for Kartikeya: what a job may see, and nothing
    of the person's environment."""
    return {
        "version": 1,
        "description": "willow kart: the folder read-only, one scratch folder, nothing else",
        "env_prefixes": [], "db_env_prefixes": [], "credential_env_prefixes": [],
        "env_deny": [],
        "bind_read_only": ["/usr", str(pile)],
        "bind_read_write": [str(scratch)],
        "bind_try": [], "bind_try_read_only": ["/lib32", "/etc/alternatives"],
        "worktree_scan_roots": [],
    }  # fmt: skip


def missing() -> str | None:
    """Why a job can't run here, or None: Kartikeya and bubblewrap, named."""
    if importlib.util.find_spec("kartikeya") is None:
        return "Kartikeya isn't installed: pip install -r adapters/deps/kart/requirements.txt"
    if shutil.which("bwrap") is None:
        return "bubblewrap isn't installed: the bwrap program (apt install bubblewrap)"
    return None


def do_policy(opts: dict) -> int:
    box = Path(opts["--box"])
    _, why = box_rows(box)
    if why:
        return refuse(why)
    pile = Path(kernel.config(box)["pile"]).resolve()
    print(json.dumps(policy(pile, Path("<scratch, made new for each run>")), indent=1))
    return kernel.ALIVE


# ── take: a received job, at your door ──────────────────────────────────────
def do_take(opts: dict) -> int:
    box = Path(opts["--box"])
    rows, why = box_rows(box)
    if why:
        return refuse(why)
    pkg, why = share.read_package(Path(opts["--package"]))
    if why:
        return refuse(why)
    if share.problems(pkg):
        return refuse("the package doesn't hold (share.py check says why)")
    pid = share.package_id(pkg)
    got = share.mine(rows, "received", pid)
    if got is None or got.get("verdict") != "good":
        return refuse(
            f"{pid} is not a package your record says you received and it held"
        )
    core = share.layers(pkg)[-1]
    if len(core["answers"]) != 1:
        return refuse("a job package holds one job")
    job = core["answers"][0]["data"]
    why = asks_network(job)
    if why:
        return refuse(why)
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    name = Path(core["answers"][0]["path"]).name or "job.sh"
    prop = {"path": f"kart/jobs/{name}", "data": job, "cites": [],
            "claim": f"a job from {share.short(core['from'])}, taken from {pid}; it runs only once sealed"}  # fmt: skip
    subj, said = propose(box, opts["--words"], prop, now)
    if subj is None:
        print(said, end="")
        return refuse("the kernel didn't take the job as a proposal")
    print(f"taken  {subj}  waiting on your seal; then: kart.py run --job {subj}")
    return kernel.ESCALATE


def asks_network(job: str) -> str | None:
    for line in job.splitlines():
        if line.strip().lower().startswith(NETWORK):
            return f"the job asks for the network ({line.strip()}); a kart job never has it"
    return None


# ── run: a sealed job, in the sandbox ───────────────────────────────────────
def do_run(opts: dict, ts: str) -> int:
    box = Path(opts["--box"])
    rows, why = box_rows(box)
    if why:
        return refuse(why)
    subj = opts["--job"]
    seal = kernel.sealed(box, rows).get(subj)
    if seal is None:
        return refuse(f"{subj} is not a job you sealed in this box")
    prop, _, why = kernel.standing(box, rows, subj, seal)
    if why:
        return refuse(f"its proposal file {why}")
    if not str(prop["path"]).startswith("kart/jobs/"):
        return refuse(f"{subj} is an answer you sealed, not a job you took")
    why = asks_network(prop["data"]) or missing()
    if why:
        return refuse(why)
    try:
        timeout = int(opts.get("--timeout", "120"))
    except ValueError:
        return refuse("--timeout is whole seconds")
    to = Path(opts["--to"])
    why = share.new_file(to, "", 0o600, box)  # new, outside the box and folder
    if why:
        return refuse(why)
    pile = Path(kernel.config(box)["pile"]).resolve()
    status, result = sandboxed(prop["data"], pile, timeout)
    out = str(result.get("stdout") or "")
    to.write_text(out, encoding="utf-8")
    manifest = result.get("sandbox_manifest") or {}
    row = kernel.append(
        box, ts, "ran", who="kart", job=subj, status=status,
        returncode=result.get("returncode"), output_sha256=kernel.h256(out),
        engine=manifest.get("engine"), network=manifest.get("network_mode"),
        bound_ro=manifest.get("bound_ro"), bound_rw=len(manifest.get("bound_rw") or []),
        refused=(result.get("error") or None) if status != "completed" else None,
    )  # fmt: skip
    print(f"ran    {subj}  {status}, exit {result.get('returncode')}, row {row['n']}")
    print(f"output written to {to} ({len(out)} characters)")
    if status != "completed":
        print(
            f"  {str(result.get('error') or result.get('stderr') or '').strip()[:300]}"
        )
        return kernel.ESCALATE
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    res = {"path": f"kart/results/{subj[9:21]}.txt", "data": out[:OUTPUT], "cites": [],
           "claim": f"what job {subj} printed, run at row {row['n']} over this folder "
                    "read-only, with no network"}  # fmt: skip
    rsubj, said = propose(box, f"kart result {subj}", res, now)
    if rsubj is None:
        print(said, end="")
        return kernel.ESCALATE
    print(
        f"result {rsubj}  waiting on your seal; nothing of it leaves until you seal and share it"
    )
    return kernel.ESCALATE


def sandboxed(job: str, pile: Path, timeout: int) -> tuple[str, dict]:
    """The job through Kartikeya, under willow's policy, with its home,
    logs and scratch in a folder made for this run and removed after."""
    from kartikeya.execute import run_shell_task  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmp:
        scratch, home = Path(tmp) / "scratch", Path(tmp) / "home"
        scratch.mkdir()
        home.mkdir()
        conf = Path(tmp) / "policy.json"
        conf.write_text(json.dumps(policy(pile, scratch)), encoding="utf-8")
        task = job.replace("{pile}", shlex.quote(str(pile)))
        task = task.replace("{scratch}", shlex.quote(str(scratch)))
        keep = {
            k: os.environ.get(k) for k in ("KART_SANDBOX_CONFIG", "WILLOW_HOME", "HOME")
        }
        os.environ.update(
            KART_SANDBOX_CONFIG=str(conf), WILLOW_HOME=str(home), HOME=str(home)
        )
        try:
            return run_shell_task(task, timeout=timeout)
        finally:
            for k, v in keep.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


def main(argv: list[str]) -> int:
    cmd, rest = (argv[0], argv[1:]) if argv else ("", [])
    need, may = FLAGS.get(cmd, (None, set()))
    opts: dict[str, str] = {}
    ok = need is not None and len(rest) % 2 == 0
    for flag, value in zip(rest[::2], rest[1::2]):
        ok = ok and flag in need | may and flag not in opts
        opts[flag] = value
    if not ok or not need <= opts.keys():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if cmd == "policy":
        return do_policy(opts)
    if cmd == "take":
        return do_take(opts)
    return do_run(opts, opts.get("--now") or kernel.now())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
