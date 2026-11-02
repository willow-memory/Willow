"""model-fit: what this machine holds, read from its own files, and where a
model of a given size fits."""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "model_fit.py"
_spec = importlib.util.spec_from_file_location("model_fit", SCRIPT)
mf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mf)
GIB = 1024**3
#: a PATH with no nvidia-smi on it, unless a test puts one there
BARE = {**os.environ, "PATH": os.path.dirname(sys.executable)}


def run(*argv, env=None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True, encoding="utf-8",
                          env=env or BARE)  # fmt: skip


def put(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def machine(root: Path, total_kb=16 * 1024**2, free_kb=12 * 1024**2) -> Path:
    mem = f"MemTotal:       {total_kb} kB\nMemFree:  1 kB\n"
    if free_kb is not None:
        mem += f"MemAvailable:   {free_kb} kB\n"
    put(root / "proc/meminfo", mem)
    put(root / "proc/cpuinfo",
        "processor\t: 0\nmodel name\t: Ryzen 7\nflags\t\t: fpu sse2 avx2\n\n"
        "processor\t: 1\nmodel name\t: Ryzen 7\nflags\t\t: fpu sse2 avx2\n")  # fmt: skip
    return root


def amd(root: Path, card: str, vram: int) -> None:
    put(root / f"sys/class/drm/{card}/device/vendor", "0x1002\n")
    put(root / f"sys/class/drm/{card}/device/device", "0x15bf\n")
    put(root / f"sys/class/drm/{card}/device/mem_info_vram_total", f"{vram}\n")


def weights(tmp_path: Path, size: int) -> Path:
    p = tmp_path / "m.gguf"
    with p.open("wb") as f:
        f.truncate(size)
    return p


def test_what_the_machine_holds_without_a_model(tmp_path):
    root = machine(tmp_path / "root")
    amd(root, "card1", 6 * GIB)
    put(
        root / "sys/class/drm/card1-DP-1/device/vendor", "0x1002\n"
    )  # a port, not a card
    put(root / "sys/class/drm/card2/device/vendor", "0x8086\n")
    put(root / "sys/class/drm/card3/device/vendor", "0x1234\n")  # nobody's GPU it knows
    (root / "sys/class/accel/accel0/device").mkdir(parents=True)
    (root / "drivers/intel_vpu").mkdir(parents=True)
    os.symlink(
        root / "drivers/intel_vpu", root / "sys/class/accel/accel0/device/driver"
    )
    (root / "sys/class/accel/accel1").mkdir(parents=True)
    got = run("check", "--root", root)
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        "memory   16.0 GiB, 12.0 GiB free now",
        "cpu      Ryzen 7, 2 threads, avx2",
        "gpu      AMD GPU 0x15bf, 6.0 GiB of its own memory",
        "gpu      Intel GPU, its memory not read",
        "npu      intel_vpu (accel0), which no runtime here is told to use",
        "npu      an NPU (accel1), which no runtime here is told to use",
        "holds    up to about 5.0 GiB of weights on the GPU AMD GPU 0x15bf (6.0 GiB)",
        "holds    up to about 10.0 GiB of weights in memory, on the CPU (12.0 GiB free now)",
    ]


def test_a_model_fits_where_its_weights_and_a_fifth_fit(tmp_path):
    root = machine(tmp_path / "root")
    amd(root, "card0", 6 * GIB)
    got = run("check", "--root", root, "--model", weights(tmp_path, 5 * GIB))
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines()[-3:] == [
        "model    m.gguf, 5.0 GiB of weights, about 6.0 GiB to run",
        "fits     on the GPU AMD GPU 0x15bf (6.0 GiB)",
        "fits     in memory, on the CPU (12.0 GiB free now)",
    ]
    amd(root, "card0", 6 * GIB - 1)
    got = run("check", "--root", root, "--model", tmp_path / "m.gguf")
    assert "fits     on the GPU" not in got.stdout
    assert got.stdout.endswith("fits     in memory, on the CPU (12.0 GiB free now)\n")


def test_a_model_too_big_for_anywhere_is_42(tmp_path):
    root = machine(tmp_path / "root", free_kb=None)
    got = run("check", "--root", root, "--model", weights(tmp_path, 14 * GIB))
    assert got.returncode == 42
    assert "memory   16.0 GiB\n" in got.stdout
    assert "gpu      none found\n" in got.stdout
    assert got.stdout.endswith(
        "fits     nowhere here: 16.8 GiB is more than any place holds\n"
    )
    small = weights(tmp_path, 13 * GIB)
    got = run("check", "--root", root, "--model", small)
    assert got.returncode == 0
    assert got.stdout.endswith("fits     in memory, on the CPU (16.0 GiB in all)\n")


def test_a_model_card_gives_the_size(tmp_path):
    root = machine(tmp_path / "root")
    card = tmp_path / "gemma.md"
    put(
        card,
        f"<!-- willow-model\nfile: gemma.gguf\nsha256: {'0' * 64}\nbytes: 3221225\n-->\n# Gemma\n",
    )
    got = run("check", "--root", root, "--model", card)
    assert "model    gemma.gguf, 3 MiB of weights, about 4 MiB to run\n" in got.stdout
    put(card, "<!-- willow-model\nbytes: 3221225\n-->\n")
    got = run("check", "--root", root, "--model", card)
    assert "model    gemma.md, 3 MiB of weights" in got.stdout
    put(card, "<!-- willow-model\nfile: g.gguf\n-->\n")
    got = run("check", "--root", root, "--model", card)
    assert got.returncode == 2 and "no size" in got.stderr


def test_nvidia_from_its_driver_then_from_nvidia_smi(tmp_path):
    root = machine(tmp_path / "root")
    put(root / "proc/driver/nvidia/gpus/0000:01:00.0/information",
        "Model: \t\t NVIDIA GeForce RTX 4070\nIRQ: 1\n")  # fmt: skip
    put(root / "proc/driver/nvidia/gpus/0000:02:00.0/information", "IRQ: 2\n")
    put(root / "sys/class/drm/card0/device/vendor", "0x10de\n")
    got = run("check", "--root", root)
    assert got.stdout.count("gpu      ") == 1
    assert "gpu      NVIDIA GeForce RTX 4070, its memory not read\n" in got.stdout
    bin_ = tmp_path / "bin"
    put(
        bin_ / "nvidia-smi",
        "#!/bin/sh\necho 'NVIDIA GeForce RTX 4070, 12282'\necho 'junk'\n",
    )
    (bin_ / "nvidia-smi").chmod(0o755)
    env = {**BARE, "PATH": f"{bin_}{os.pathsep}{BARE['PATH']}"}
    got = run("check", "--root", root, "--model", weights(tmp_path, 9 * GIB), env=env)
    assert got.stdout.count("gpu      ") == 1
    assert (
        "gpu      NVIDIA GeForce RTX 4070, 12.0 GiB of its own memory\n" in got.stdout
    )
    assert "fits     on the GPU NVIDIA GeForce RTX 4070 (12.0 GiB)\n" in got.stdout


def test_an_arm_cpu_says_its_features_and_a_nameless_one_says_so(tmp_path):
    root = tmp_path / "root"
    put(root / "proc/meminfo", "MemTotal: 8388608 kB\n")
    put(root / "proc/cpuinfo", "processor\t: 0\nFeatures\t: fp asimd sve\n")
    got = run("check", "--root", root)
    assert "cpu      not named, 1 threads, asimd sve\n" in got.stdout
    put(root / "proc/cpuinfo", "Model\t: Raspberry Pi 5\n")
    got = run("check", "--root", root)
    assert "cpu      Raspberry Pi 5\n" in got.stdout


def test_macos_is_read_from_sysctl_and_its_gpu_shares_memory():
    got = mf.darwin(
        "hw.memsize: 38654705664\nmachdep.cpu.brand_string: Apple M3 Pro\nhw.ncpu: 12\n"
    )
    assert (got["memory"], got["cpu"], got["threads"], got["apple"]) == (
        36 * GIB,
        "Apple M3 Pro",
        12,
        True,
    )
    assert got["npus"] == ["the Neural Engine"]
    intel = mf.darwin(
        "hw.memsize: x\nmachdep.cpu.brand_string: Intel(R) Core(TM) i7\nhw.ncpu: ?\n"
    )
    assert (intel["memory"], intel["threads"], intel["apple"], intel["npus"]) == (
        None,
        0,
        False,
        [],
    )
    assert mf.apple_gpu_share(36 * GIB) == 24 * GIB, "two thirds up to 36 GiB"
    assert mf.apple_gpu_share(48 * GIB) == 36 * GIB, "three quarters past it"


def test_nothing_to_read_is_42(tmp_path):
    got = run("check", "--root", tmp_path)
    assert got.returncode == 42
    assert got.stdout.startswith("could not read this machine")


@pytest.mark.skipif(sys.platform != "linux", reason="reads Linux's own /proc")
def test_this_machine_is_read_from_its_own_files():
    got = run("check")
    assert got.returncode == 0, got.stdout
    assert re.match(r"memory   \d+\.\d GiB", got.stdout)


def test_measure_times_a_copy_and_guesses_a_speed(tmp_path):
    root = machine(tmp_path / "root")
    got = run("check", "--root", root, "--measure", "--model", weights(tmp_path, GIB))
    assert got.returncode == 0
    assert re.search(
        r"\nmeasured \d+\.\d GB a second through memory, copied now\n", got.stdout
    )
    assert re.search(
        r"\nspeed    about \d+\.\d tokens a second on the CPU, if it reads", got.stdout
    )
    got = run("check", "--root", root, "--measure")
    assert "measured " in got.stdout and "speed" not in got.stdout


def test_a_bad_command_line_is_refused(tmp_path):
    for argv in (
        [],
        ["check", "stray"],
        ["check", "--model"],
        ["check", "--root"],
        ["fit"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "model_fit.py" in got.stderr, argv
    got = run("check", "--model", tmp_path / "missing.gguf")
    assert got.returncode == 2 and "not a file" in got.stderr
