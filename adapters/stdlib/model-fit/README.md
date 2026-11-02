<!-- willow-addon
section: Assistants
line: Whether this machine's GPU, NPU or Apple silicon can run a local model, and about how fast, before you download one.
source: new
added: 2026-11-02
writes: nothing
network: none
-->
# model-fit

Whether this machine can run a local model, and where, before you download
one: its memory, CPU, GPUs and NPUs, read from the machine's own files.

```
python adapters/stdlib/model-fit/model_fit.py check [--model FILE] [--measure] [--root DIR]

memory   15.7 GiB, 15.2 GiB free now
cpu      Intel(R) Xeon(R) Processor @ 2.10GHz, 4 threads, avx2 avx512f
gpu      NVIDIA GeForce RTX 4070, 12.0 GiB of its own memory
model    gemma-3-4b-it-Q4_K_M.gguf, 2.3 GiB of weights, about 2.8 GiB to run
fits     on the GPU NVIDIA GeForce RTX 4070 (12.0 GiB)
fits     in memory, on the CPU (15.2 GiB free now)
```

**Where it reads.** On Linux: memory and the CPU from /proc, each GPU
from /sys/class/drm (its own memory where the driver says it, as AMD's
does), NVIDIA's from its driver under /proc and, when `nvidia-smi` is
installed, its memory from that, and each NPU from /sys/class/accel.
`--root DIR` reads those under DIR instead of /. On macOS: `sysctl`; on
Apple silicon the GPU shares memory, and macOS lets it use about two thirds
of it, three quarters past 36 GiB. A GPU whose memory isn't read says so,
and holds nothing in the sums. An NPU is named, and said to be one no
runtime here is told to use.

**Where a model fits.** A model needs its weights and a fifth more, for its
context and the runtime. `--model` takes a weights file (its size) or a
model card from [weights-card](../weights-card/) (its `bytes`), and each
place that holds that much is said; none is `fits nowhere here`, 42.
Without `--model`, it says the most weights each place holds. Memory is
counted as what's free now, where Linux says it.

**How fast**, only with `--measure`: it times copying 256 MiB through
memory, and since each token reads every weight once, tokens a second are
about that rate over the weights' size, on the CPU. It is a guess from one
copy, not a benchmark of any runtime, and it differs run to run, so
without `--measure` the same machine gives the same lines.

Exit codes, the kernel's: 0 read, and the model fits somewhere; 42 it fits
nowhere, or nothing about this machine could be read; 2 refused (a bad
command line, `--model` not a file, or a card with no size).

**Uses:** the kernel's exit codes.

**Never:** downloads or runs a model, goes online, writes anything, or
reads your key.
