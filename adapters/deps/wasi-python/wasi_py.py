"""wasi_py.py: a job someone sent you, as a Python script, run on wasi-python's
CPython for WebAssembly over your own folder: one runtime, the same answer on
every machine.

    python adapters/deps/wasi-python/wasi_py.py run --box DIR --job proposal:<sha256> --to FILE [--shape numbers] [--fuel N] [--now TS]

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

wasi-python keeps a cache of the compiled runtime in your home folder; this
turns it off, since it is a write the card doesn't name, so each run compiles
the runtime first (most of a minute).

Exit codes, the kernel's: 42 a result proposed, waiting on your seal, or a
job that failed, ran out of fuel or broke its shape; 2 refused (no
wasi-python, a job not sealed or not taken, one asking for the network).
"""

from __future__ import annotations

import atexit
import hashlib
import importlib.util
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

NEED = {"--box", "--job", "--to"}
MAY = {"--shape", "--fuel", "--now"}
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


def execute(script: str, pile: Path, fuel: int) -> dict:
    """Run it: {status, returncode, stdout, stderr, fuel, cut}."""
    import wasi_python as w  # noqa: PLC0415

    was, tempfile.tempdir = tempfile.tempdir, scratch()
    try:
        done = w.run(["-c", script.replace("{pile}", "/pile")], root=False,
                     grants=[w.Grant(str(pile), "/pile")], env={}, fuel=fuel,
                     cache_dir=False)  # fmt: skip
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
    result = execute(prop["data"], pile, fuel)
    out, status = result["stdout"], result["status"]
    to.write_text(out, encoding="utf-8")
    import importlib.metadata as md  # noqa: PLC0415

    held = kart.shaped(out, shape) if status == "completed" else None
    row = kernel.append(
        box, ts, "ran", who="wasi-python", job=subj, status=status,
        returncode=result["returncode"], output_sha256=kernel.h256(out),
        engine=f"wasi-python {md.version('wasi-python')} on wasmtime {md.version('wasmtime')}",
        network="none", bound_ro=[str(pile)], bound_rw=0, tools=used,
        fuel=result["fuel"], cut=result["cut"],
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


def main(argv: list[str]) -> int:
    cmd, rest = (argv[0], argv[1:]) if argv else ("", [])
    opts: dict[str, str] = {}
    ok = cmd == "run" and len(rest) % 2 == 0
    for flag, value in zip(rest[::2], rest[1::2]):
        ok = ok and flag in NEED | MAY and flag not in opts
        opts[flag] = value
    if not ok or not NEED <= opts.keys():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    return do_run(opts, opts.get("--now") or kernel.now())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
