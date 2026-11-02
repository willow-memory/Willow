"""model_fit.py: whether this machine can run a local model, before you download one.

    python adapters/stdlib/model-fit/model_fit.py check [--model FILE] [--measure] [--root DIR]

It reads what this machine has: memory, the CPU, each GPU and NPU, from
Linux's /proc and /sys (under DIR when given, `/` when not) or from macOS's
sysctl, and nvidia-smi when it is installed.

    memory   15.7 GiB, 15.2 GiB free now
    cpu      Intel(R) Xeon(R) Processor @ 2.10GHz, 4 threads, avx2 avx512f
    gpu      NVIDIA GeForce RTX 4070, 12.0 GiB of its own memory
    npu      intel_vpu (accel0), which no runtime here is told to use

A model needs its weights and a fifth more for its context and the runtime.
Without `--model` it says the largest model each place holds; with one (a
weights file, or a model card from weights-card) it says where that one fits:

    model    gemma-3-4b-it-Q4_K_M.gguf, 2.3 GiB of weights, about 2.8 GiB to run
    fits     on the GPU NVIDIA GeForce RTX 4070 (12.0 GiB)
    fits     in memory, on the CPU (15.2 GiB free now)

On Apple silicon the GPU shares memory, and macOS lets it use about two
thirds of it (three quarters past 36 GiB). The speed is only guessed with
`--measure`, which times a memory copy here: a token reads every weight
once, so tokens a second are about the bytes a second over the weights'
size. A measurement differs run to run, so without `--measure` the same
machine gives the same lines.

Exit codes, the kernel's: 0 read, and the model fits somewhere; 42 the
model fits nowhere, or nothing about this machine could be read; 2 refused
(a bad command line, a model file that isn't one).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: model_fit.py check [--model FILE] [--measure] [--root DIR]"
GIB = 1024**3
#: a model runs in its weights and about a fifth more: the context and the runtime
OVERHEAD = 1.2
VENDORS = {"0x10de": "NVIDIA", "0x1002": "AMD", "0x8086": "Intel"}
#: CPU features the runtimes use to go faster
FEATURES = ("avx2", "avx512f", "asimd", "sve")
MARKER = "<!-- willow-model"


def gib(n: float) -> str:
    if n < GIB:
        return f"{n / 1024**2:.0f} MiB"
    return f"{n / GIB:.1f} GiB"


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def meminfo(text: str) -> dict[str, int]:
    out = {}
    for line in text.splitlines():
        m = re.match(r"(\w+):\s+(\d+) kB", line)
        if m:
            out[m.group(1)] = int(m.group(2)) * 1024
    return out


def cpuinfo(text: str) -> tuple[str, int, list[str]]:
    name, threads, flags = "", 0, set()
    for line in text.splitlines():
        key, _, value = line.partition(":")
        key = key.strip()
        if key == "processor":
            threads += 1
        elif key in ("model name", "Model") and not name:
            name = value.strip()
        elif key in ("flags", "Features"):
            flags |= set(value.split())
    return name, threads, [f for f in FEATURES if f in flags]


def linux(root: Path) -> dict:
    """Memory, CPU, GPUs and NPUs from /proc and /sys under root."""
    mem = meminfo(read(root / "proc/meminfo"))
    name, threads, flags = cpuinfo(read(root / "proc/cpuinfo"))
    gpus = []
    nvidia = sorted((root / "proc/driver/nvidia/gpus").glob("*/information"))
    for info in nvidia:
        m = re.search(r"^Model:\s*(.+)$", read(info), re.M)
        if m:
            gpus.append({"name": m.group(1).strip(), "vram": None})
    for card in sorted((root / "sys/class/drm").glob("card*")):
        if not re.fullmatch(r"card\d+", card.name):
            continue
        vendor = VENDORS.get(read(card / "device/vendor").strip(), "")
        if not vendor or (vendor == "NVIDIA" and nvidia):
            continue
        device = read(card / "device/device").strip()
        vram = read(card / "device/mem_info_vram_total").strip()
        gpus.append({"name": f"{vendor} GPU {device}".strip(),
                     "vram": int(vram) if vram.isdigit() else None})  # fmt: skip
    npus = []
    for accel in sorted((root / "sys/class/accel").glob("accel*")):
        try:
            driver = os.path.basename(os.readlink(accel / "device/driver"))
        except OSError:
            driver = "an NPU"
        npus.append(f"{driver} ({accel.name})")
    return {
        "memory": mem.get("MemTotal"),
        "free": mem.get("MemAvailable"),
        "cpu": name,
        "threads": threads,
        "flags": flags,
        "gpus": gpus,
        "npus": npus,
        "apple": False,
    }


def darwin(sysctl: str) -> dict:
    """The same from `sysctl hw.memsize machdep.cpu.brand_string hw.ncpu`."""
    got = {}
    for line in sysctl.splitlines():
        key, _, value = line.partition(":")
        got[key.strip()] = value.strip()
    memory = int(got["hw.memsize"]) if got.get("hw.memsize", "").isdigit() else None
    brand = got.get("machdep.cpu.brand_string", "")
    threads = int(got["hw.ncpu"]) if got.get("hw.ncpu", "").isdigit() else 0
    apple = brand.startswith("Apple")
    return {
        "memory": memory,
        "free": None,
        "cpu": brand,
        "threads": threads,
        "flags": [],
        "gpus": [],
        "npus": ["the Neural Engine"] if apple else [],
        "apple": apple,
    }


def nvidia_smi() -> list[dict]:
    """Each NVIDIA GPU and its memory, when nvidia-smi is installed."""
    exe = shutil.which("nvidia-smi")
    if not exe:
        return []
    try:
        out = subprocess.run([exe, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=30).stdout  # fmt: skip
    except (OSError, subprocess.SubprocessError):
        return []
    gpus = []
    for line in out.splitlines():
        name, _, mib = line.rpartition(",")
        if name.strip() and mib.strip().isdigit():
            gpus.append({"name": name.strip(), "vram": int(mib) * 1024**2})
    return gpus


def apple_gpu_share(memory: int) -> int:
    """macOS's default limit on what the GPU may use of shared memory."""
    return memory * 3 // 4 if memory > 36 * GIB else memory * 2 // 3


def model_bytes(path: Path) -> tuple[str, int] | None:
    """(name, bytes of weights) from a weights file or a willow-model card."""
    with path.open("rb") as f:
        head = f.read(len(MARKER))
    if head == MARKER.encode():
        text = read(path)
        size = re.search(r"^bytes:\s*(\d+)\s*$", text, re.M)
        named = re.search(r"^file:\s*(.+?)\s*$", text, re.M)
        if not size:
            return None
        return (named.group(1) if named else path.name), int(size.group(1))
    return path.name, path.stat().st_size


def measure() -> float:
    """Bytes a second through memory: the best of three copies of 256 MiB
    into memory already in use, so no page is mapped while it is timed."""
    block = bytearray(256 * 1024**2)
    into = bytearray(len(block))
    into[:] = block
    best = float("inf")
    for _ in range(3):
        start = time.perf_counter()
        into[:] = block
        best = min(best, time.perf_counter() - start)
    return 2 * len(block) / best  # each byte read once and written once


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--model", "--root"):
            opts[a] = next(it, "")
        elif a == "--measure":
            opts[a] = "yes"
        else:
            args.append(a)
    if args != ["check"] or "" in (opts.get("--model"), opts.get("--root")):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    model = None
    if "--model" in opts:
        path = Path(opts["--model"])
        if not path.is_file():
            print(f"refused: not a file: {path}", file=sys.stderr)
            return kernel.REFUSED
        model = model_bytes(path)
        if model is None:
            print(f"refused: {path.name} is a model card with no size", file=sys.stderr)
            return kernel.REFUSED
    if sys.platform == "darwin" and "--root" not in opts:
        try:
            out = subprocess.run(["sysctl", "hw.memsize", "machdep.cpu.brand_string", "hw.ncpu"],
                                 capture_output=True, text=True, timeout=30).stdout  # fmt: skip
        except (OSError, subprocess.SubprocessError):
            out = ""
        facts = darwin(out)
    else:
        facts = linux(Path(opts.get("--root", "/")))
    by_smi = nvidia_smi()
    if by_smi:
        facts["gpus"] = [g for g in facts["gpus"] if not g["name"].startswith("NVIDIA")]
        facts["gpus"] = by_smi + facts["gpus"]
    if not facts["memory"] and not facts["cpu"]:
        print(
            "could not read this machine: only Linux's /proc and /sys and macOS's sysctl are read"
        )
        return kernel.ESCALATE

    memory, free = facts["memory"], facts["free"]
    if memory:
        now = f", {gib(free)} free now" if free else ""
        print(f"memory   {gib(memory)}{now}")
    else:
        print("memory   not read")
    cpu = facts["cpu"] or "not named"
    threads = f", {facts['threads']} threads" if facts["threads"] else ""
    flags = f", {' '.join(facts['flags'])}" if facts["flags"] else ""
    print(f"cpu      {cpu}{threads}{flags}")
    places = []  # (where, bytes it holds)
    if facts["apple"] and memory:
        share = apple_gpu_share(memory)
        print(
            f"gpu      Apple silicon's, sharing memory: {gib(share)} of it for the GPU"
        )
        places.append((f"on the GPU, sharing memory ({gib(share)})", share))
    for g in facts["gpus"]:
        if g["vram"]:
            print(f"gpu      {g['name']}, {gib(g['vram'])} of its own memory")
            places.append((f"on the GPU {g['name']} ({gib(g['vram'])})", g["vram"]))
        else:
            print(f"gpu      {g['name']}, its memory not read")
    if not facts["gpus"] and not facts["apple"]:
        print("gpu      none found")
    for n in facts["npus"]:
        print(f"npu      {n}, which no runtime here is told to use")
    room = free or memory
    if room:
        said = "free now" if free else "in all"
        places.append((f"in memory, on the CPU ({gib(room)} {said})", room))

    if model is None:
        for where, holds in places:
            print(f"holds    up to about {gib(holds / OVERHEAD)} of weights {where}")
        speed = None
    else:
        name, size = model
        need = size * OVERHEAD
        print(f"model    {name}, {gib(size)} of weights, about {gib(need)} to run")
        fits = [where for where, holds in places if need <= holds]
        for where in fits:
            print(f"fits     {where}")
        if not fits:
            print(f"fits     nowhere here: {gib(need)} is more than any place holds")
        speed = size
    if "--measure" in opts:
        rate = measure()
        print(f"measured {rate / 1e9:.1f} GB a second through memory, copied now")
        if speed:
            print(f"speed    about {rate / speed:.1f} tokens a second on the CPU, "
                  "if it reads the weights as fast as that copy")  # fmt: skip
    if model is not None and not fits:
        return kernel.ESCALATE
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
