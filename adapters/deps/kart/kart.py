"""kart.py: a job someone sent you, run over your own folder in Kartikeya's sandbox.

    python adapters/deps/kart/kart.py policy --box DIR [--project DIR] [--hide PATH[,...]] [--hold PATH[,...]]
    python adapters/deps/kart/kart.py take   --box DIR --package FILE --words "your words" [--now TS]
    python adapters/deps/kart/kart.py write  --box DIR --file JOB --words "your words" [--now TS]
    python adapters/deps/kart/kart.py try    --box DIR --file JOB --to FILE [--timeout SECONDS] [--now TS]
    python adapters/deps/kart/kart.py queue  --box DIR --file JOB --db QUEUE
    python adapters/deps/kart/kart.py work   --box DIR --db QUEUE [--timeout SECONDS] [--now TS]
    python adapters/deps/kart/kart.py status --box DIR --db QUEUE --id ID [--to FILE]
    python adapters/deps/kart/kart.py run    --box DIR --job proposal:<sha256> --to FILE [--shape numbers] [--timeout SECONDS] [--now TS]
    python adapters/deps/kart/kart.py gather --box DIR --package FILE[,...] --words "your words" [--now TS]
    python adapters/deps/kart/kart.py shell  --box DIR --project DIR --command TEXT [--cwd DIR] [--hide PATH[,...]] [--hold PATH[,...]] [--timeout SECONDS]

A job is a shell task, as Kartikeya runs them, that came to you in a share
package, or that you wrote yourself. It never runs because it arrived, or
because it was written. `take` puts a received job at the kernel's door as
a proposal of yours, under your own words, citing nothing, and `write` does
the same for a job in a file of your own; only you seal it, through the
kernel. `run` runs a job you sealed, and nothing else.

`try` runs a job in a file of your own with no seal, in the same sandbox,
and proposes nothing: what it printed is in FILE on your machine, the run
is on your record, and nothing of it is an answer of yours or can be
shared. A job that is to go anywhere is written, sealed and run.

`queue` puts a job of your own in a queue file (Kartikeya's, SQLite) to be
run later; `work` runs everything queued, one at a time, as `try` runs one,
and stops when the queue is empty: nothing is left running. `status` says
where a queued job stands and, with --to, writes what it printed to FILE.
The queue file holds what jobs printed, so it is kept outside the box and
your folder, on your machine.

It runs in Kartikeya's bubblewrap sandbox under a policy of willow's, not
Kartikeya's default: your folder read-only, one scratch folder of its own,
the system's /usr read-only, private /tmp, no network, and no environment
variable of yours: its PATH is the system's and its locale C. The box and
the key are never in it. `{pile}` and `{scratch}` in the job are its two
folders, as they are mounted. A job that
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

`shell` is the other way round: not a job over your folder, but one command
of a session working in a project of yours, run in the sandbox in place of
your own shell. The project is writable, since the work is there. Your home
and the system's /usr and /etc are read-only, /tmp is private, there is no
network, and the environment is PATH, LANG and HOME. The box and its key
are never in it, nor anything you name with --hide: home is mounted around
them, piece by piece, so they are not there to be read by any path a command
builds. A project that holds one of them, or lies inside one, is refused.
What you name with --hold is read-only wherever it is, in the project too:
the code that judges a session's commands, say. It
takes no seal and proposes nothing, and nothing of it is on your record:
it is a shell, and what it changed is in the project for you to read. What
the command printed comes back as one line of JSON (`returncode`, `stdout`,
`stderr`, `status`, and `how` when it never ran or was ended), on standard
output.

Exit codes, the kernel's: 0 the policy printed, or a job tried or a command
run that ended well; 42 a job taken, a result or
a total proposed, waiting on your seal, or a job or a command that failed, or
a job that broke its
shape; 2 refused (no
bubblewrap or Kartikeya, a bubblewrap that can't make a sandbox here, a job
not sealed, one asking for the network, a job file that can't be read as
text, is empty or too long, or is inside the box; a project that isn't a
folder, that holds your home, or that holds or lies inside what is hidden).
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
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
    "policy": ({"--box"}, {"--project", "--hide", "--hold"}),
    "shell": (
        {"--box", "--project", "--command"},
        {"--cwd", "--hide", "--hold", "--timeout"},
    ),
    "take": ({"--box", "--package", "--words"}, {"--now"}),
    "write": ({"--box", "--file", "--words"}, {"--now"}),
    "try": ({"--box", "--file", "--to"}, {"--timeout", "--now"}),
    "queue": ({"--box", "--file", "--db"}, set()),
    "work": ({"--box", "--db"}, {"--timeout", "--now"}),
    "status": ({"--box", "--db", "--id"}, {"--to"}),
    "run": ({"--box", "--job", "--to"}, {"--timeout", "--now", "--shape"}),
    "gather": ({"--box", "--package", "--words"}, {"--now"}),
}
SHAPES = ("numbers",)  # what --shape may hold a job's output to
MOST = 100  # lines a numbers-shaped output may have
JOB = 20_000  # characters of a job you wrote: what a person reads before sealing


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


#: what a job's programs are found on, and its locale: the system's, never yours,
#: so one job reads the same on everyone's machine but for the tools themselves
PATH = "/usr/bin:/bin"
LOCALE = "C"
#: settings of Kartikeya's and a fleet's that a person's environment may hold,
#: never handed on to a run; but the resource group, which is theirs to set up
SETTINGS = ("KART_", "WILLOW_")
KEPT = ("KART_CGROUP_PARENT",)


def tools(job: str) -> dict[str, str]:
    """{program: SHA-256 of its file} for bash and each word of the job that is
    a program on PATH under /usr, the only system folder a job sees. The same
    job over two machines answers alike only if these are alike."""
    words = {"bash"} | set(re.findall(r"(?<![\w./{-])[A-Za-z][\w.+-]*", job))
    found = {}
    for w in sorted(words):
        at = shutil.which(w, path=PATH)
        real = Path(at).resolve() if at else None
        if real and real.is_relative_to("/usr"):
            found[w] = hashlib.sha256(real.read_bytes()).hexdigest()
    return found


def missing() -> str | None:
    """Why a job can't run here, or None: Kartikeya and bubblewrap, named, a
    resource group you named that isn't there, and a bubblewrap that can't
    make a sandbox on this machine, in its own words."""
    if importlib.util.find_spec("kartikeya") is None:
        return "Kartikeya isn't installed: pip install -r adapters/deps/kart/requirements.txt"
    if shutil.which("bwrap") is None:
        return "bubblewrap isn't installed: the bwrap program (apt install bubblewrap)"
    why = group_not_ready()
    if why:
        return why
    try:
        # an empty pipe for its input, not the null device: opening that is a
        # write by the guard's rule, and this add-on writes record and to only
        got = subprocess.run(PROBE, capture_output=True, text=True, timeout=30,
                             input="")  # fmt: skip
    except (OSError, subprocess.TimeoutExpired) as e:
        got = subprocess.CompletedProcess(PROBE, 1, "", str(e))
    if got.returncode != 0:
        said = (got.stderr.strip().splitlines() or ["no reason given"])[0][:300]
        return (f"bubblewrap can't make a sandbox on this machine ({said}); "
                "nothing ran. a container's or AppArmor's rules may forbid it")  # fmt: skip
    return None


def why_failed(result: dict) -> str | None:
    """How a run failed, as the record keeps it: Kartikeya's name for it
    ("exited 3", "timeout", "cgroup_setup_failed", its scan's label) and
    never what follows the colon, which is the last thing the job printed:
    a line of the person's files, if that is what it was reading."""
    said = str(result.get("error") or "").strip()
    return said.split(":", 1)[0].strip()[:80] or None


def group_not_ready() -> str | None:
    """Why a resource group that is set up for Kartikeya can't be used, or
    None. Kartikeya's own check: a group counts as set up when
    KART_CGROUP_PARENT names one, or its kart.slice unit is installed, and
    it then refuses to run a task without it. A reload of systemd undoes
    what `kartikeya setup-cgroup` wrote into the group; that is put back
    here when it can be. A group that can't be readied is refused by name
    before anything runs or is recorded. A Kartikeya from before it had a
    resource group to check has none to ready: it runs a task under its
    per-process limits, as it always did."""
    try:
        from kartikeya import cgroup_setup  # noqa: PLC0415
    except ImportError:
        return None

    try:
        st = cgroup_setup.cgroup_status()
    except Exception as e:  # noqa: BLE001  its check is its own; never run blind
        return f"Kartikeya couldn't say whether its resource group is ready ({e}); nothing ran"
    if st.get("ready"):
        return None
    unit = st.get("slice_unit_path")
    named = st.get("env_parent") or st.get("systemd_parent")
    if not named and not (unit and Path(unit).exists()):
        return None  # none set up: Kartikeya runs under per-process limits
    # the one thing a reload of systemd undoes is the group handing its
    # memory and process limits down to the groups under it. Where the group
    # is there and can, that is put back, as `kartikeya setup-cgroup` wrote
    # it: no unit is written and nothing is reloaded.
    why = ""
    if named and cgroup_setup.controllers_available(named) \
            and not cgroup_setup.subtree_control_enabled(named):  # fmt: skip
        why = cgroup_setup.enable_subtree_control(named) or ""
        if not why:
            try:
                if cgroup_setup.cgroup_status().get("ready"):
                    print(
                        f"restored the resource group's limits ({named}), lost to a reload"
                    )
                    return None
            except Exception as e:  # noqa: BLE001
                why = str(e)
    return (f"a resource group is set up for Kartikeya but isn't ready ({named or unit})"
            f"{', and its limits could not be put back (' + why + ')' if why else ''}; "
            "nothing ran. run: kartikeya setup-cgroup (a restart of the slice or "
            "the machine undoes it); or, to run under per-process limits, unset "
            "KART_CGROUP_PARENT and remove the kart.slice unit")  # fmt: skip


def do_policy(opts: dict) -> int:
    box = Path(opts["--box"])
    _, why = box_rows(box)
    if why:
        return refuse(why)
    if opts.keys() & {"--project", "--hide", "--hold"}:
        if "--project" not in opts:
            return refuse(
                "--hide and --hold go with --project: it is the shell's policy"
            )
        project, hidden, held, why = shell_place(box, opts)
        if why:
            return refuse(why)
        run = Path("<the command, made new for each run>")
        print(json.dumps(shell_policy(project, Path.home().resolve(), hidden, held, run), indent=1))  # fmt: skip
        return kernel.ALIVE
    pile = kernel.folder(kernel.config(box)).resolve()
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


def own_job(src: Path, box: Path) -> tuple[str, str | None]:
    """(a job in a file of the person's, why not): text, not in the box, not
    empty, not too long to read, and asking for no network."""
    if src.resolve().is_relative_to(box.resolve()):
        return "", f"{src} is inside the box; a job is a file of your own"
    try:
        job = src.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "", f"{src} can't be read as text"
    if not job.strip():
        return "", f"{src} is empty; there is no job in it"
    if len(job) > JOB:
        return "", (f"{src} is {len(job)} characters; a job is at most {JOB}, "
                    "what a person reads before sealing")  # fmt: skip
    return job, asks_network(job)


# ── try: a job of your own, run with no seal and proposing nothing ──────────
def do_try(opts: dict, ts: str) -> int:
    """A job in a file of yours, run in the sandbox as a sealed one is. No
    seal, since nothing leaves by running it: its output is in FILE, the run
    is on the record by the job text's hash, and nothing is proposed."""
    box = Path(opts["--box"])
    _, why = box_rows(box)
    if why:
        return refuse(why)
    job, why = own_job(Path(opts["--file"]), box)
    why = why or missing()
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
    pile = kernel.folder(kernel.config(box)).resolve()
    used = tools(job)
    status, result = sandboxed(job, pile, timeout)
    out = str(result.get("stdout") or "")
    to.write_text(out, encoding="utf-8")
    manifest = result.get("sandbox_manifest") or {}
    row = kernel.append(
        box, ts, "ran", who="kart", job=f"text:{kernel.h256(job)}", sealed=False,
        status=status, returncode=result.get("returncode"),
        output_sha256=kernel.h256(out), engine=manifest.get("engine"),
        network=manifest.get("network_mode"), bound_ro=manifest.get("bound_ro"),
        bound_rw=len(manifest.get("bound_rw") or []),
        refused=why_failed(result) if status != "completed" else None,
        tools=used, locale=LOCALE,
    )  # fmt: skip
    print(
        f"tried  text:{kernel.h256(job)}  {status}, exit {result.get('returncode')}, row {row['n']}"
    )
    print(f"output written to {to} ({len(out)} characters); nothing is proposed")
    if status != "completed":
        print(
            f"  {str(result.get('error') or result.get('stderr') or '').strip()[:300]}"
        )
        return kernel.ESCALATE
    return kernel.ALIVE


# ── queue, work, status: jobs of your own, run later ────────────────────────
LATER = 1800  # seconds a queued job may run: Kartikeya's batch lane's


def queue_at(db: Path, box: Path, must_exist: bool):
    """(Kartikeya's SQLite queue at db, why not). The file holds what jobs
    printed, so it is never in the box or the folder it reads."""
    if importlib.util.find_spec("kartikeya") is None:
        return (
            None,
            "Kartikeya isn't installed: pip install -r adapters/deps/kart/requirements.txt",
        )
    pile = kernel.folder(kernel.config(box)).resolve()
    for name, root in (("the box", box.resolve()), ("your folder", pile)):
        if db.resolve().is_relative_to(root):
            return None, f"{db} is inside {name}; a queue holds what jobs printed"
    if must_exist and not db.is_file():
        return None, f"{db} isn't a queue: nothing was queued there"
    if not db.parent.is_dir():
        return None, f"{db.parent} isn't a folder; this never makes one"
    from kartikeya import SqliteTaskQueue  # noqa: PLC0415

    try:
        return SqliteTaskQueue(db), None
    except Exception as e:  # noqa: BLE001  a file that isn't a queue
        return None, f"{db} can't be opened as a queue ({e})"


def do_queue(opts: dict) -> int:
    """A job in a file of yours, queued to run later. Held to what every job
    is before it is queued; queueing runs nothing."""
    box = Path(opts["--box"])
    _, why = box_rows(box)
    if why:
        return refuse(why)
    job, why = own_job(Path(opts["--file"]), box)
    if why:
        return refuse(why)
    queue, why = queue_at(Path(opts["--db"]), box, must_exist=False)
    if why:
        return refuse(why)
    tid = f"{kernel.h256(job)[:12]}-{os.urandom(4).hex()}"
    queue.submit(tid, job, submitted_by="kart queue")
    print(f"queued  {tid}  it runs when you run: kart.py work")
    return kernel.ALIVE


def do_work(opts: dict, ts: str) -> int:
    """Run everything queued, one at a time, each as `try` runs one, and stop
    when the queue is empty. A job a worker died holding is failed first, so
    it is never run twice or left looking as if it runs."""
    box = Path(opts["--box"])
    _, why = box_rows(box)
    if why:
        return refuse(why)
    queue, why = queue_at(Path(opts["--db"]), box, must_exist=True)
    why = why or missing()
    if why:
        return refuse(why)
    try:
        timeout = int(opts.get("--timeout", str(LATER)))
    except ValueError:
        return refuse("--timeout is whole seconds")
    pile = kernel.folder(kernel.config(box)).resolve()
    # an old Kartikeya's queue has no stale jobs to take back
    for tid in getattr(queue, "reap_stale", list)():
        print(f"gave up  {tid}  a worker stopped while it ran; it is not run again")
    done = 0
    while True:
        rows = queue.claim_pending("kart", 1)
        if not rows:
            break
        row = rows[0]
        why = asks_network(row.task)  # held again here: the queue is a file
        if why:
            queue.mark_done(row.task_id, status="failed",
                            result=json.dumps({"stdout": "", "how": "asks for the network"}))  # fmt: skip
            print(f"refused  {row.task_id}  {why}")
            continue
        used = tools(row.task)
        status, result = sandboxed(row.task, pile, timeout)
        out = str(result.get("stdout") or "")
        manifest = result.get("sandbox_manifest") or {}
        rec = kernel.append(
            box, opts.get("--now") or kernel.now(), "ran", who="kart",
            job=f"text:{kernel.h256(row.task)}", sealed=False, queued=row.task_id,
            status=status, returncode=result.get("returncode"),
            output_sha256=kernel.h256(out), engine=manifest.get("engine"),
            network=manifest.get("network_mode"), bound_ro=manifest.get("bound_ro"),
            bound_rw=len(manifest.get("bound_rw") or []),
            refused=why_failed(result) if status != "completed" else None,
            tools=used, locale=LOCALE,
        )  # fmt: skip
        queue.mark_done(
            row.task_id, status="completed" if status == "completed" else "failed",
            result=json.dumps({"stdout": out, "returncode": result.get("returncode"),
                               "how": why_failed(result) if status != "completed" else None,
                               "row": rec["n"]}),
        )  # fmt: skip
        done += 1
        print(
            f"ran    {row.task_id}  {status}, exit {result.get('returncode')}, row {rec['n']}"
        )
    print(f"worked {done} queued job{'' if done == 1 else 's'}; the queue is empty")
    return kernel.ALIVE


def do_status(opts: dict) -> int:
    """Where one queued job stands, as one line of JSON; with --to, what it
    printed, written to FILE once it has ended."""
    box = Path(opts["--box"])
    _, why = box_rows(box)
    if why:
        return refuse(why)
    queue, why = queue_at(Path(opts["--db"]), box, must_exist=True)
    if why:
        return refuse(why)
    got = queue.get(opts["--id"])
    if got is None:
        return refuse(f"{opts['--id']} isn't a job in this queue")
    try:
        res = json.loads(got.get("result") or "{}")
    except ValueError:
        res = {}
    ended = got["status"] in ("completed", "failed")
    out = str(res.get("stdout") or "")
    if "--to" in opts:
        if not ended:
            return refuse(
                f"{opts['--id']} hasn't ended ({got['status']}); nothing to write yet"
            )
        why = share.new_file(Path(opts["--to"]), "", 0o600, box)
        if why:
            return refuse(why)
        Path(opts["--to"]).write_text(out, encoding="utf-8")
    print(json.dumps({"id": opts["--id"], "status": got["status"],
                      "returncode": res.get("returncode"), "how": res.get("how"),
                      "characters": len(out) if ended else None}, sort_keys=True))  # fmt: skip
    return kernel.ALIVE


# ── write: a job of your own, at your door ──────────────────────────────────
def do_write(opts: dict) -> int:
    """A job in a file of yours, put at the kernel's door as `take` puts a
    received one: it ran nowhere and runs nowhere until you seal it."""
    box = Path(opts["--box"])
    _, why = box_rows(box)
    if why:
        return refuse(why)
    src = Path(opts["--file"])
    job, why = own_job(src, box)
    if why:
        return refuse(why)
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    prop = {"path": f"kart/jobs/{src.name}", "data": job, "cites": [],
            "claim": f"a job you wrote yourself, text {kernel.h256(job)}; it runs only once sealed"}  # fmt: skip
    subj, said = propose(box, opts["--words"], prop, now)
    if subj is None:
        print(said, end="")
        return refuse("the kernel didn't take the job as a proposal")
    print(f"written  {subj}  waiting on your seal; then: kart.py run --job {subj}")
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
    pile = kernel.folder(kernel.config(box)).resolve()
    used = tools(prop["data"])
    status, result = sandboxed(prop["data"], pile, timeout)
    out = str(result.get("stdout") or "")
    to.write_text(out, encoding="utf-8")
    manifest = result.get("sandbox_manifest") or {}
    row = kernel.append(
        box, ts, "ran", who="kart", job=subj, status=status,
        returncode=result.get("returncode"), output_sha256=kernel.h256(out),
        engine=manifest.get("engine"), network=manifest.get("network_mode"),
        bound_ro=manifest.get("bound_ro"), bound_rw=len(manifest.get("bound_rw") or []),
        refused=why_failed(result) if status != "completed" else None,
        shape=shape, held_shape=shaped(out, shape) if status == "completed" else None,
        tools=used, locale=LOCALE,
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
                    f"tools {kernel.h256(kernel.canon(used))}; "
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
    said = re.search(r"; tools ([0-9a-f]{64}); job text ", ans[0]["claim"])
    return {"package": pid, "from": core["from"], "chain": core["chain"]["start"],
            "job": job, "numbers": lines, "tools": said and said[1]}, None  # fmt: skip


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
    sets = {r["tools"] for r in got}
    alike = len(sets) == 1 and None not in sets
    if not alike:
        print(f"  ran on {len(sets)} different sets of tools{' (or tools not said)' if None in sets else ''}: "
              "the same job can count differently on each; read them before you seal")  # fmt: skip
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    prop = {"path": f"kart/gathered/{got[0]['job'][:12]}.txt",
            "data": "\n".join(map(str, total)) + "\n", "cites": [],
            "claim": f"the sum of {len(got)} results of job text {got[0]['job']}, "
                     + ("on the same tools" if alike else f"on {len(sets)} sets of tools")
                     + ", from " + ", ".join(r["package"] for r in got)}  # fmt: skip
    subj, said = propose(box, opts["--words"], prop, now)
    if subj is None:
        print(said, end="")
        return refuse("the kernel didn't take the total as a proposal")
    print(f"total  {subj}  waiting on your seal")
    return kernel.ESCALATE


# ── shell: a session's own command, in the sandbox ──────────────────────────
#: the system a command sees, read-only, beside your home
SYSTEM = ("/usr", "/etc")


def around(root: Path, hidden: list[Path]) -> list[Path]:
    """What of root to mount so that nothing hidden is in the sandbox: root
    whole when it holds nothing hidden, nothing when it is hidden, and else
    the folders and files in it, each the same way. A link in a folder taken
    apart is left out: Kartikeya mounts what a link points at, which could be
    what is hidden."""
    if root in hidden:
        return []
    if not any(h.is_relative_to(root) for h in hidden):
        return [root]
    try:
        inside = sorted(root.iterdir())
    except OSError:
        return []
    found: list[Path] = []
    for p in inside:
        if not p.is_symlink() and (p.is_dir() or p.is_file()):
            found += around(p, hidden)
    return found


def shell_policy(
    project: Path, home: Path, hidden: list[Path], held: list[Path], run: Path
) -> dict:
    """The mount policy for a session's shell: the project writable; home,
    the system, what is held and the command's own file read-only; nothing
    hidden; and nothing of the person's environment. What is held is mounted
    after the project that holds it, so it is read-only there too."""
    return {
        "version": 1,
        "description": "willow kart shell: the project writable, home and the system "
                       "read-only, the box and what is hidden never mounted",
        "env_prefixes": [], "db_env_prefixes": [], "credential_env_prefixes": [],
        "env_deny": [],
        "bind_read_only": [*SYSTEM, *map(str, around(home, hidden)),
                           *map(str, held), str(run)],
        "bind_read_write": [str(project)],
        "bind_try": [], "bind_try_read_only": ["/lib32", "/opt"],
        "worktree_scan_roots": [],
    }  # fmt: skip


def shell_place(
    box: Path, opts: dict
) -> tuple[Path, list[Path], list[Path], str | None]:
    """(the project, what is never mounted, what is held read-only, why not).
    Hidden are the box, its key and each path of --hide. The project is a
    folder that neither holds your home or anything hidden, nor lies inside
    what is hidden or held. What is held is there to hold, and not hidden."""
    project = Path(opts["--project"]).resolve()
    hidden = [box.resolve(), Path(kernel.config(box)["key"]).resolve()]
    hidden += [Path(x).resolve() for x in opts.get("--hide", "").split(",") if x]
    held = [Path(x).resolve() for x in opts.get("--hold", "").split(",") if x]
    held = [
        k for k in held if k.exists() and not any(k.is_relative_to(h) for h in hidden)
    ]
    if not project.is_dir():
        return project, hidden, held, f"{project} isn't a folder"
    if Path.home().resolve().is_relative_to(project):
        return project, hidden, held, (f"{project} holds your home; a project is a "
                                       "folder in it")  # fmt: skip
    for h in hidden:
        if h.is_relative_to(project) or project.is_relative_to(h):
            return project, hidden, held, (f"{h} is never mounted, and the project holds it or "
                                     "lies inside it; nothing ran")  # fmt: skip
        if any(h.is_relative_to(s) or Path(s).is_relative_to(h) for s in SYSTEM):
            return project, hidden, held, f"{h} is the system's; it can't be hidden"
    for k in held:
        if project.is_relative_to(k):
            return project, hidden, held, (f"{k} is held read-only, and the project is it or "
                                           "lies inside it; nothing could be written")  # fmt: skip
    return project, hidden, held, None


def do_shell(opts: dict) -> int:
    """One command of a session, run in the sandbox in the project. No seal,
    no proposal, no row: what it printed goes back as one line of JSON."""
    box = Path(opts["--box"])
    _, why = box_rows(box)
    if why:
        return refuse(why)
    project, hidden, held, why = shell_place(box, opts)
    if why:
        return refuse(why)
    cwd = Path(opts.get("--cwd", project)).resolve()
    if not cwd.is_dir() or not cwd.is_relative_to(project):
        return refuse(f"{cwd} isn't a folder in the project")
    command = opts["--command"]
    if not command.strip():
        return refuse("there is no command")
    why = asks_network(command) or missing()
    if why:
        return refuse(why)
    try:
        timeout = int(opts.get("--timeout", "120"))
    except ValueError:
        return refuse("--timeout is whole seconds")
    status, result = shelled(command, project, cwd, hidden, held, timeout)
    said = {"returncode": result.get("returncode"), "status": status,
            "stdout": str(result.get("stdout") or ""),
            "stderr": str(result.get("stderr") or "")}  # fmt: skip
    if result.get("returncode") is None:  # it never ran, or was ended
        said["how"] = why_failed(result)
    print(json.dumps(said, sort_keys=True))
    return kernel.ALIVE if status == "completed" else kernel.ESCALATE


def shelled(
    command: str,
    project: Path,
    cwd: Path,
    hidden: list[Path],
    held: list[Path],
    timeout: int,
) -> tuple[str, dict]:
    """The command through Kartikeya under the shell's policy. It is handed
    over as a file of its own, read-only in the sandbox: Kartikeya reads a
    task's text for fenced blocks and network lines, and a command's text is
    not a task's. Its scan reads the command first, as it reads a job."""
    try:
        from kartikeya.task_scan import check_kart_task  # noqa: PLC0415
    except ImportError:  # a Kartikeya from before it scanned
        check_kart_task = None
    blocked = check_kart_task(command) if check_kart_task else None
    if blocked:
        return "failed", blocked
    home = Path.home().resolve()
    with tempfile.TemporaryDirectory() as tmp:
        run, fleet = Path(tmp) / "run", Path(tmp) / "home"
        run.mkdir()
        fleet.mkdir()
        (run / "command.sh").write_text(command, encoding="utf-8")
        conf = Path(tmp) / "policy.json"
        conf.write_text(json.dumps(shell_policy(project, home, hidden, held, run)),
                        encoding="utf-8")  # fmt: skip
        task = (f"cd {shlex.quote(str(cwd))} && exec env -i PATH={PATH} LANG={LOCALE} "
                f"HOME={shlex.quote(str(home))} bash {shlex.quote(str(run / 'command.sh'))}")  # fmt: skip
        return kartikeya_runs(task, conf, fleet, timeout)


def sandboxed(job: str, pile: Path, timeout: int) -> tuple[str, dict]:
    """The job through Kartikeya, under willow's policy, with its home,
    logs and scratch in a folder made for this run and removed after."""
    with tempfile.TemporaryDirectory() as tmp:
        scratch, home = Path(tmp) / "scratch", Path(tmp) / "home"
        scratch.mkdir()
        home.mkdir()
        conf = Path(tmp) / "policy.json"
        conf.write_text(json.dumps(policy(pile, scratch)), encoding="utf-8")
        task = job.replace("{pile}", shlex.quote(str(pile)))
        task = task.replace("{scratch}", shlex.quote(str(scratch)))
        # Kartikeya gives a task variables of its own: where it is installed,
        # the Python it runs on, a fleet's sender name. Those are the person's.
        # The job starts again with an empty environment and these three.
        task = (f"cd {shlex.quote(str(home))} && exec env -i PATH={PATH} LANG={LOCALE} "
                f"HOME={shlex.quote(str(home))} bash -c {shlex.quote(task)}")  # fmt: skip
        return kartikeya_runs(task, conf, home, timeout)


def kartikeya_runs(task: str, conf: Path, home: Path, timeout: int) -> tuple[str, dict]:
    """One task through Kartikeya under the policy in conf, its own home and
    logs in `home`, and none of the person's settings in its environment."""
    from kartikeya.execute import run_shell_task  # noqa: PLC0415

    # bwrap itself is looked up on PATH too: its folder goes last, where
    # the job can't see it (only /usr is mounted)
    bwrap = os.path.dirname(shutil.which("bwrap") or "/usr/bin/bwrap")
    path = PATH if bwrap in PATH.split(":") else f"{PATH}:{bwrap}"
    swap = {"KART_SANDBOX_CONFIG": str(conf), "WILLOW_HOME": str(home),
            "HOME": str(home), "PATH": path, "LANG": LOCALE}  # fmt: skip
    # Kartikeya reads its own settings from the environment, and a
    # person's may carry a fleet's: WILLOW_ROOT puts that fleet's venv on
    # the job's PATH. It sees what is set here and none of theirs.
    theirs = [k for k in os.environ if k.startswith(SETTINGS) and k not in KEPT]
    keep = {k: os.environ.get(k) for k in [*swap, *theirs]}
    for k in theirs:
        del os.environ[k]
    os.environ.update(swap)
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
    if cmd == "write":
        return do_write(opts)
    if cmd == "try":
        return do_try(opts, opts.get("--now") or kernel.now())
    if cmd == "queue":
        return do_queue(opts)
    if cmd == "work":
        return do_work(opts, opts.get("--now") or kernel.now())
    if cmd == "status":
        return do_status(opts)
    if cmd == "gather":
        return do_gather(opts)
    if cmd == "shell":
        return do_shell(opts)
    return do_run(opts, opts.get("--now") or kernel.now())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
