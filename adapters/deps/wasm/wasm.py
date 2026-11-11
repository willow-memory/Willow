"""wasm.py: a job someone sent you, as WebAssembly, run by Wasmtime over your
own folder: the same bytes, so the same answer, on every machine.

    python adapters/deps/wasm/wasm.py run --box DIR --job proposal:<sha256> --to FILE [--runtime FILE] [--shape numbers] [--fuel N] [--now TS]

A job comes as kart's do: in a share package, taken to your door with
`kart.py take`, and sealed by you; only a job you sealed runs. kart runs a
shell job on your machine's own grep and sort, which can count differently
from someone else's. A wasm job carries its program: its text is a
WebAssembly module (`(module ...` text, or `wasm:` and its bytes in base64),
or, with `--runtime FILE`, a script for an interpreter compiled to
WebAssembly that you keep (CPython's WASI build, say): FILE runs with the
script as its one argument. Either way what ran is bytes with a SHA-256,
and two machines that ran the same bytes ran the same job.

What it sees, in Wasmtime's WASI: your folder read-only at /pile (`{pile}`
in a script is /pile), the script read-only at /job with `--runtime`, and
nothing else. No network, which WASI here has no way to ask for; no
environment variable; no clock but the one WASI gives. `--fuel` bounds the
work it may do (10,000,000,000 by default); one that runs out is stopped.

What it records, as kart does: a `ran` row with the job, how it ended, its
exit code, its output's SHA-256, the engine, and `tools`, the module's (or
the runtime's) SHA-256, never the output. What it printed goes to FILE,
new, outside the box and folder; a job that ended well is proposed as an
answer of yours, waiting on your seal, under kart/results/ with the same
claim kart's give, so `kart gather` adds them.

Exit codes, the kernel's: 42 a result proposed, waiting on your seal, or a
job that failed, ran out of fuel or broke its shape; 2 refused (no
Wasmtime, a job not sealed or not a module, a runtime that isn't one).
"""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import os
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
MAY = {"--runtime", "--shape", "--fuel", "--now"}
FUEL = 10_000_000_000
OUTPUT = 1_000_000  # characters of output kept; more is cut and said


def refuse(why: str) -> int:
    return kart.refuse(why)


def module_bytes(job: str) -> tuple[bytes | None, str | None]:
    """The job's module as bytes: WebAssembly text compiled, or base64."""
    import wasmtime  # noqa: PLC0415

    text = job.strip()
    if text.startswith("wasm:"):
        try:
            return base64.b64decode(text[5:], validate=True), None
        except ValueError:
            return None, "the job's wasm: isn't base64"
    if text.startswith("(module"):
        try:
            return wasmtime.wat2wasm(text), None
        except Exception as e:  # noqa: BLE001  Wasmtime's own words
            return (
                None,
                f"the job's module doesn't compile: {str(e).splitlines()[0][:200]}",
            )
    return (
        None,
        "the job isn't a module ((module ... or wasm:); with --runtime it's a script",
    )


def execute(module: bytes, pile: Path, script: str | None, fuel: int) -> dict:
    """Run it. {status, returncode, stdout, stderr, fuel}; never raises on
    what the job does."""
    import wasmtime as w  # noqa: PLC0415

    cfg = w.Config()
    cfg.consume_fuel = True
    engine = w.Engine(cfg)
    out, err = bytearray(), bytearray()
    with tempfile.TemporaryDirectory() as tmp:
        wasi = w.WasiConfig()
        wasi.preopen_dir(str(pile), "/pile", False)
        wasi.argv = ["job"]
        if script is not None:
            job = Path(tmp) / "job"
            job.mkdir()
            (job / "job").write_text(
                script.replace("{pile}", "/pile"), encoding="utf-8"
            )
            wasi.preopen_dir(str(job), "/job", False)
            wasi.argv = ["runtime", "/job/job"]
        wasi.stdout_custom = lambda b: out.extend(b[: max(0, OUTPUT + 1 - len(out))])
        wasi.stderr_custom = lambda b: err.extend(b[: max(0, 4000 - len(err))])
        store = w.Store(engine)
        store.set_wasi(wasi)
        store.set_fuel(fuel)
        linker = w.Linker(engine)
        linker.define_wasi()
        status, code = "completed", 0
        try:
            inst = linker.instantiate(store, w.Module(engine, module))
            start = inst.exports(store).get("_start")
            if start is None:
                return {"status": "failed", "returncode": None, "stdout": "",
                        "stderr": "the module has no _start", "fuel": 0}  # fmt: skip
            start(store)
        except w.ExitTrap as e:
            code = e.code
            status = "completed" if code == 0 else "failed"
        except w.Trap as e:
            status = "out of fuel" if store.get_fuel() == 0 else "failed"
            code = None
            err.extend(str(e).splitlines()[0].encode()[:300])
        except w.WasmtimeError as e:
            status, code = "failed", None
            err.extend(str(e).splitlines()[0].encode()[:300])
        used = fuel - store.get_fuel()
    text = out.decode("utf-8", "replace")
    cut = len(text) > OUTPUT
    return {"status": status, "returncode": code, "stdout": text[:OUTPUT], "cut": cut,
            "stderr": err.decode("utf-8", "replace"), "fuel": used}  # fmt: skip


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
    if importlib.util.find_spec("wasmtime") is None:
        return refuse(
            "Wasmtime isn't installed: pip install -r adapters/deps/wasm/requirements.txt"
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
    runtime = opts.get("--runtime")
    if runtime is not None:
        try:
            module = Path(runtime).read_bytes()
        except OSError as e:
            return refuse(f"can't read the runtime {runtime}: {type(e).__name__}")
        if module[:4] != b"\0asm":
            return refuse(f"{runtime} isn't a WebAssembly module")
        script, tools = prop["data"], {"runtime": hashlib.sha256(module).hexdigest()}
    else:
        module, why = module_bytes(prop["data"])
        if why:
            return refuse(why)
        script, tools = None, {"module": hashlib.sha256(module).hexdigest()}
    to = Path(opts["--to"])
    why = share.new_file(to, "", 0o600, box)  # new, outside the box and folder
    if why:
        return refuse(why)
    pile = Path(kernel.config(box)["pile"]).resolve()
    if os.path.realpath(box).startswith(str(pile) + os.sep):
        return refuse("the box is inside the folder; a job would see it")
    result = execute(module, pile, script, fuel)
    out, status = result["stdout"], result["status"]
    to.write_text(out, encoding="utf-8")
    import importlib.metadata as md  # noqa: PLC0415

    held = kart.shaped(out, shape) if status == "completed" else None
    row = kernel.append(
        box, ts, "ran", who="wasm", job=subj, status=status,
        returncode=result["returncode"], output_sha256=kernel.h256(out),
        engine=f"wasmtime {md.version('wasmtime')}", network="none",
        bound_ro=[str(pile)] + (["<the script>"] if script is not None else []),
        bound_rw=0, tools=tools, fuel=result["fuel"], cut=result["cut"],
        refused=result["stderr"][:300] or None if status != "completed" else None,
        shape=shape, held_shape=held,
    )  # fmt: skip
    print(f"ran    {subj}  {status}, exit {result['returncode']}, row {row['n']}")
    print(f"output written to {to} ({len(out)} characters)")
    if status != "completed":
        print(f"  {result['stderr'].strip()[:300]}")
        return kernel.ESCALATE
    if not held:
        print(
            f"  its output isn't {shape}, the shape you asked for: nothing is proposed"
        )
        return kernel.ESCALATE
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    how = "on a runtime of yours" if script is not None else "as a module"
    res = {"path": f"kart/results/{subj[9:21]}.txt", "data": out[: kart.OUTPUT], "cites": [],
           "claim": f"what job {subj} printed, run at row {row['n']} over this folder "
                    f"read-only {how} in wasmtime, with no network"
                    f"{', held to ' + shape if shape else ''}; "
                    f"tools {kernel.h256(kernel.canon(tools))}; "
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
