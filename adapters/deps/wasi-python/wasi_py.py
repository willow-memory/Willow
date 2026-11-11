"""wasi_py.py: a job someone sent you, as a Python script, run on wasi-python's
CPython for WebAssembly over your own folder: one runtime, the same answer on
every machine.

    python adapters/deps/wasi-python/wasi_py.py run  --box DIR --job proposal:<sha256> --to FILE [--shape numbers] [--fuel N] [--cache CACHE] [--now TS]
    python adapters/deps/wasi-python/wasi_py.py warm --to CACHE

A job comes as kart's do: in a share package, taken to your door with
`kart.py take`, and sealed by you; only a job you sealed runs. Its text is a
Python script, `{pile}` in it being /pile. It runs in wasi-python's guest:
CPython 3.15 compiled to WebAssembly, run by Wasmtime, with its standard
library (and numpy, pandas and the rest it carries) read-only. The guest sees
your folder read-only at /pile and nothing else of this machine: no network,
which WASI here can't ask for, no environment of yours, no box and no key.
`--fuel` bounds the work (100,000,000,000 by default).

What it records, as kart does: a `ran` row with the job, how it ended, its
exit code, its output's SHA-256, the engine, and `tools`, the SHA-256 of the
runtime and of its library zip, never the output. What it printed goes to
FILE, new, outside the box and folder; a job that ended well is proposed as
an answer of yours, waiting on your seal, under kart/results/ with the claim
kart's results carry, so `kart gather` adds them.

Compiling the runtime takes most of a minute. wasi-python would keep it
compiled in your home folder; that is a write the card doesn't name, so it is
off. Instead, as index-cache keeps scan's index, `warm --to CACHE` compiles
it into a folder you name, with what it was compiled from beside it, and
does nothing while that is still current; `run --cache CACHE` then only
reads it, and starts in a moment. A cache made for another runtime, or that
others can write, is left alone and the runtime compiled in memory.

Exit codes, the kernel's: 0 a cache compiled or current; 42 a result proposed, waiting on your seal, or a
job that failed, ran out of fuel or broke its shape; 2 refused (no
wasi-python, a job not sealed or not taken, one asking for the network).
"""

from __future__ import annotations

import atexit
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

sys.path.insert(0, str(ROOT / "adapters" / "deps" / "kart"))
import kart  # noqa: E402
import share  # noqa: E402  (kart put it on the path)

FLAGS = {
    "run": ({"--box", "--job", "--to"}, {"--shape", "--fuel", "--cache", "--now"}),
    "warm": ({"--to"}, set()),
}
MANIFEST = "wasi-py.json"  # what a cache was compiled from, beside it
FUEL = 100_000_000_000


def refuse(why: str) -> int:
    return kart.refuse(why)


def tools() -> dict[str, str]:
    """The runtime's bytes and its library's, by SHA-256: what ran."""
    import wasi_python  # noqa: PLC0415

    a = wasi_python.artifacts()
    return {
        name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
        for name, path in (("runtime", a.snapshot), ("stdlib", a.stdlib_zip))
    }


_SCRATCH: list[str] = []


def scratch() -> str:
    """One folder of this run's own, made by tempfile and removed at exit.
    wasi-python unpacks its library and keeps its locks in the temporary
    folder, under names of its own; pointed here, they are this run's
    scratch, not files beside everyone else's in /tmp."""
    if not _SCRATCH:
        _SCRATCH.append(tempfile.mkdtemp(prefix="wasi-py-"))
        atexit.register(shutil.rmtree, _SCRATCH[0], True)
    return _SCRATCH[0]


def stamp() -> dict:
    """What a compiled runtime is good for: these runtime bytes, on these
    releases of wasi-python and Wasmtime."""
    import importlib.metadata as md  # noqa: PLC0415

    return {"tools": tools(), "wasi-python": md.version("wasi-python"),
            "wasmtime": md.version("wasmtime")}  # fmt: skip


def cache_for(folder: Path) -> tuple[Path | None, str]:
    """(the cache folder to read, or None; what it is): current only when
    `warm` made it for the runtime installed now, and nobody else can write
    it. A run only reads it; anything else, it compiles in memory."""
    try:
        made = json.loads((folder / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, "none"
    if made != stamp():
        return None, "stale"
    if folder.stat().st_mode & 0o022:
        return None, "open"  # another user could put native code in it
    return folder, "used"


def execute(
    script: str, pile: Path | None, fuel: int | None, cache: Path | None = None
) -> dict:
    """Run it: {status, returncode, stdout, stderr, fuel, cut}."""
    import wasi_python as w  # noqa: PLC0415

    was, tempfile.tempdir = tempfile.tempdir, scratch()
    try:
        done = w.run(["-c", script.replace("{pile}", "/pile")], root=False,
                     grants=[] if pile is None else [w.Grant(str(pile), "/pile")],
                     env={}, fuel=fuel, cache_dir=str(cache) if cache else False)  # fmt: skip
    finally:
        tempfile.tempdir = was

    def text(b) -> str:
        return (
            b.decode("utf-8", "replace")
            if isinstance(b, (bytes, bytearray))
            else str(b or "")
        )

    trapped = str(done.trapped or "")
    if done.exit_code == 0 and not trapped:
        status = "completed"
    elif "fuel" in trapped:
        status = "out of fuel"
    else:
        status = "failed"
    return {"status": status, "returncode": done.exit_code, "stdout": text(done.stdout),
            "stderr": (text(done.stderr) + trapped)[-4000:], "fuel": done.fuel_used,
            "cut": bool(done.truncated)}  # fmt: skip


def do_run(opts: dict, ts: str) -> int:
    box = Path(opts["--box"])
    rows, why = kart.box_rows(box)
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
        return refuse(
            f"{subj} is an answer you sealed, not a job you took (kart.py take)"
        )
    why = kart.asks_network(prop["data"])
    if why:
        return refuse(why)
    if importlib.util.find_spec("wasi_python") is None:
        return refuse(
            "wasi-python isn't installed: pip install -r adapters/deps/wasi-python/requirements.txt"
        )
    shape = opts.get("--shape")
    if shape is not None and shape not in kart.SHAPES:
        return refuse(f"--shape is one of: {', '.join(kart.SHAPES)}")
    try:
        fuel = int(opts.get("--fuel", str(FUEL)))
    except ValueError:
        return refuse("--fuel is a whole number")
    if fuel < 1:
        return refuse("--fuel is at least 1")
    to = Path(opts["--to"])
    why = share.new_file(to, "", 0o600, box)  # new, outside the box and folder
    if why:
        return refuse(why)
    pile = Path(kernel.config(box)["pile"]).resolve()
    used = tools()
    cache, cached = (
        (None, "none") if "--cache" not in opts else cache_for(Path(opts["--cache"]))
    )
    if "--cache" in opts and cache is None:
        print(f"  the cache at {opts['--cache']} is {cached} for this runtime, so it is left "
              "alone and the runtime compiled in memory; wasi_py.py warm --to it makes it current")  # fmt: skip
    result = execute(prop["data"], pile, fuel, cache)
    out, status = result["stdout"], result["status"]
    to.write_text(out, encoding="utf-8")
    import importlib.metadata as md  # noqa: PLC0415

    held = kart.shaped(out, shape) if status == "completed" else None
    row = kernel.append(
        box, ts, "ran", who="wasi-python", job=subj, status=status,
        returncode=result["returncode"], output_sha256=kernel.h256(out),
        engine=f"wasi-python {md.version('wasi-python')} on wasmtime {md.version('wasmtime')}",
        network="none", bound_ro=[str(pile)], bound_rw=0, tools=used,
        fuel=result["fuel"], cut=result["cut"], cache=cached,
        refused=(result["stderr"][-300:] or None) if status != "completed" else None,
        shape=shape, held_shape=held,
    )  # fmt: skip
    print(f"ran    {subj}  {status}, exit {result['returncode']}, row {row['n']}")
    print(f"output written to {to} ({len(out)} characters)")
    if status != "completed":
        print(f"  {result['stderr'].strip()[-300:]}")
        return kernel.ESCALATE
    if not held:
        print(
            f"  its output isn't {shape}, the shape you asked for: nothing is proposed"
        )
        return kernel.ESCALATE
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    res = {"path": f"kart/results/{subj[9:21]}.txt", "data": out[: kart.OUTPUT], "cites": [],
           "claim": f"what job {subj} printed, run at row {row['n']} over this folder "
                    "read-only on wasi-python's CPython in wasmtime, with no network"
                    f"{', held to ' + shape if shape else ''}; "
                    f"tools {kernel.h256(kernel.canon(used))}; "
                    f"job text {kernel.h256(prop['data'])}"}  # fmt: skip
    rsubj, said = kart.propose(box, f"kart result {subj}", res, now)
    if rsubj is None:
        print(said, end="")
        return kernel.ESCALATE
    print(
        f"result {rsubj}  waiting on your seal; nothing of it leaves until you seal and share it"
    )
    return kernel.ESCALATE


def do_warm(opts: dict) -> int:
    """The runtime compiled into a cache folder of yours, as index-cache keeps
    scan's index: left alone while it is current, made again when it isn't."""
    if importlib.util.find_spec("wasi_python") is None:
        return refuse(
            "wasi-python isn't installed: pip install -r adapters/deps/wasi-python/requirements.txt"
        )
    to = Path(opts["--to"])
    if to.exists() and not to.is_dir():
        return refuse(f"{to} is not a folder")
    ours = (to / MANIFEST).is_file()
    if to.is_dir() and not ours and any(to.iterdir()):
        return refuse(f"{to} holds other things; a cache is a folder of its own")
    if not to.is_dir():
        return refuse(
            f"{to} is not a folder; make it first, yours alone (mkdir -m 700)"
        )
    if to.is_dir() and to.stat().st_mode & 0o022:
        return refuse(
            f"{to} can be written by others; a cache of native code is yours alone"
        )
    if ours and cache_for(to)[0] is not None:
        print(f"current  {to}: compiled for this runtime already; nothing done")
        return kernel.ALIVE
    for old in to.glob("*.cwasm"):  # compiled for another runtime: ours, and stale
        old.unlink()
    done = execute(
        "pass", None, FUEL, to
    )  # metered, as run's are: a compile of its own
    if done["status"] != "completed":
        return refuse(f"the runtime didn't start: {done['stderr'].strip()[-200:]}")
    (to / MANIFEST).write_text(json.dumps(stamp(), indent=1) + "\n", encoding="utf-8")
    size = sum(p.stat().st_size for p in to.glob("*.cwasm"))
    print(
        f"compiled {to}: the runtime, {size // 1_000_000} MB; run --cache {to} starts in a moment"
    )
    return kernel.ALIVE


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
    if cmd == "warm":
        return do_warm(opts)
    return do_run(opts, opts.get("--now") or kernel.now())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
