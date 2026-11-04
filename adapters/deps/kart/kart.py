"""kart.py: a job someone sent you, run over your own folder in Kartikeya's sandbox.

    python adapters/deps/kart/kart.py policy --box DIR
    python adapters/deps/kart/kart.py take   --box DIR --package FILE --words "your words" [--now TS]
    python adapters/deps/kart/kart.py run    --box DIR --job proposal:<sha256> --to FILE [--shape numbers] [--timeout SECONDS] [--now TS]
    python adapters/deps/kart/kart.py gather --box DIR --package FILE[,...] --words "your words" [--now TS]

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

`--shape numbers` is yours to set when you run a job: its output must be
whole numbers, one a line, at most 100, or nothing is proposed and the
`ran` row says the shape didn't hold. Only aggregates leave; no word of your
folder can. `gather` takes the results others sent you back, each a package
that held and that your record received, of numbers, all naming the same
job text by its SHA-256 and each from its own chain, adds them line by
line, and proposes the totals as your answer, waiting on your seal.

Exit codes, the kernel's: 0 the policy printed; 42 a job taken, a result or
a total proposed, waiting on your seal, or a job that failed or broke its
shape; 2 refused (no
bubblewrap or Kartikeya, a bubblewrap that can't make a sandbox here, a job
not sealed, one asking for the network).
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shlex
import shutil
import subprocess
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
    "run": ({"--box", "--job", "--to"}, {"--timeout", "--now", "--shape"}),
    "gather": ({"--box", "--package", "--words"}, {"--now"}),
}
SHAPES = ("numbers",)  # what --shape may hold a job's output to
MOST = 100  # lines a numbers-shaped output may have


def shaped(out: str, shape: str | None) -> bool:
    """Whether the output keeps the shape the person asked for: `numbers` is
    whole numbers, one a line, nothing else, so no word of the folder leaves."""
    if shape is None:
        return True
    lines = out.strip().splitlines()
    return 0 < len(lines) <= MOST and all(_whole(x.strip()) for x in lines)


def _whole(s: str) -> bool:
    return s.lstrip("-").isdigit() and len(s) <= 18


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


#: an empty sandbox: the namespaces and the fresh /proc every job's needs
PROBE = ["bwrap", "--unshare-all", "--die-with-parent", "--ro-bind", "/", "/",
         "--proc", "/proc", "--dev", "/dev", "true"]  # fmt: skip


def missing() -> str | None:
    """Why a job can't run here, or None: Kartikeya and bubblewrap, named, and
    a bubblewrap that can't make a sandbox on this machine, in its own words."""
    if importlib.util.find_spec("kartikeya") is None:
        return "Kartikeya isn't installed: pip install -r adapters/deps/kart/requirements.txt"
    if shutil.which("bwrap") is None:
        return "bubblewrap isn't installed: the bwrap program (apt install bubblewrap)"
    try:
        got = subprocess.run(PROBE, capture_output=True, text=True, timeout=30,
                             stdin=subprocess.DEVNULL)  # fmt: skip
    except (OSError, subprocess.TimeoutExpired) as e:
        got = subprocess.CompletedProcess(PROBE, 1, "", str(e))
    if got.returncode != 0:
        said = (got.stderr.strip().splitlines() or ["no reason given"])[0][:300]
        return (f"bubblewrap can't make a sandbox on this machine ({said}); "
                "nothing ran. a container's or AppArmor's rules may forbid it")  # fmt: skip
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
    shape = opts.get("--shape")
    if shape is not None and shape not in SHAPES:
        return refuse(f"--shape is one of: {', '.join(SHAPES)}")
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
        shape=shape, held_shape=shaped(out, shape) if status == "completed" else None,
    )  # fmt: skip
    print(f"ran    {subj}  {status}, exit {result.get('returncode')}, row {row['n']}")
    print(f"output written to {to} ({len(out)} characters)")
    if status != "completed":
        print(
            f"  {str(result.get('error') or result.get('stderr') or '').strip()[:300]}"
        )
        return kernel.ESCALATE
    if not shaped(out, shape):
        print(
            f"  its output isn't {shape}, the shape you asked for: nothing is proposed"
        )
        return kernel.ESCALATE
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    res = {"path": f"kart/results/{subj[9:21]}.txt", "data": out[:OUTPUT], "cites": [],
           "claim": f"what job {subj} printed, run at row {row['n']} over this folder "
                    f"read-only, with no network{', held to ' + shape if shape else ''}; "
                    f"job text {kernel.h256(prop['data'])}"}  # fmt: skip
    rsubj, said = propose(box, f"kart result {subj}", res, now)
    if rsubj is None:
        print(said, end="")
        return kernel.ESCALATE
    print(
        f"result {rsubj}  waiting on your seal; nothing of it leaves until you seal and share it"
    )
    return kernel.ESCALATE


# ── gather: everyone's numbers, added up ────────────────────────────────────
def result_of(rows: list[dict], path: Path) -> tuple[dict | None, str | None]:
    """(what one package says, why not): a kart result that holds, that your
    record says you received, of numbers, naming the job text it ran."""
    pkg, why = share.read_package(path)
    if why:
        return None, why
    if share.problems(pkg):
        return None, f"{path} doesn't hold (share.py check says why)"
    pid = share.package_id(pkg)
    got = share.mine(rows, "received", pid)
    if got is None or got.get("verdict") != "good":
        return None, f"{pid} is not a package your record says you received and it held"
    core = share.layers(pkg)[-1]
    ans = core["answers"]
    if len(ans) != 1 or not str(ans[0]["path"]).startswith("kart/results/"):
        return None, f"{path} isn't one kart result"
    job = ans[0]["claim"].rpartition("job text ")[2]
    if not share.is_hex(job, 64):
        return None, f"{path} doesn't name the job it ran"
    if not shaped(ans[0]["data"], "numbers"):
        return None, f"{path} isn't numbers"
    lines = [int(x) for x in ans[0]["data"].strip().splitlines()]
    return {"package": pid, "from": core["from"], "chain": core["chain"]["start"],
            "job": job, "numbers": lines}, None  # fmt: skip


def do_gather(opts: dict) -> int:
    box = Path(opts["--box"])
    rows, why = box_rows(box)
    if why:
        return refuse(why)
    got = []
    for path in opts["--package"].split(","):
        r, why = result_of(rows, Path(path))
        if why:
            return refuse(why)
        got.append(r)
    if len({r["job"] for r in got}) != 1:
        return refuse("these results ran different jobs")
    if len({len(r["numbers"]) for r in got}) != 1:
        return refuse("these results don't have the same number of lines")
    if len({r["chain"] for r in got}) != len(got):
        return refuse("two results come from one chain; each is counted once")
    total = [sum(col) for col in zip(*(r["numbers"] for r in got))]
    for r in got:
        print(
            f"  {share.short(r['from'])}  {' '.join(map(str, r['numbers']))}  {r['package']}"
        )
    print(f"  total          {' '.join(map(str, total))}  from {len(got)} folders")
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    prop = {"path": f"kart/gathered/{got[0]['job'][:12]}.txt",
            "data": "\n".join(map(str, total)) + "\n", "cites": [],
            "claim": f"the sum of {len(got)} results of job text {got[0]['job']}, from "
                     + ", ".join(r["package"] for r in got)}  # fmt: skip
    subj, said = propose(box, opts["--words"], prop, now)
    if subj is None:
        print(said, end="")
        return refuse("the kernel didn't take the total as a proposal")
    print(f"total  {subj}  waiting on your seal")
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
    if cmd == "gather":
        return do_gather(opts)
    return do_run(opts, opts.get("--now") or kernel.now())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
