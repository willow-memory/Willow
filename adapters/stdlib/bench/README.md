<!-- willow-addon
section: For maintainers
line: How fast the kernel answers on boxes of set sizes, per release, so a slowdown is seen.
source: new
added: 2026-10-26
writes: nothing
network: none
tags: no-install, offline, read-only, maintainers
-->
# bench

The kernel reads the whole folder and ranks it on every question — that is its
promise and its cost, and the cost grows with the folder. `bench` measures it:
it builds a pile of each size, reads and ranks it the way a `bite` answers one
question, and reports the median time.

    python adapters/stdlib/bench/bench.py run [--sizes 100,1000,5000] [--repeat 5]

    kernel a1b2c3d4e5f6
       100 passages     0.4 ms
      1000 passages     4.2 ms
      5000 passages    23.1 ms

Run it each release and watch for a size whose time jumped — a slowdown the
vectors (which check answers, not speed) wouldn't catch. `--sizes` is a comma
list of passage counts; `--repeat` is how many runs each size is timed over
(the median is reported).

The pile is synthetic and the times are **this machine's**, so the numbers are
a trend to compare against the same machine's last run, not a fixed vector —
the kernel's version is printed so a comparison is of like with like.

## what it reads and writes

It builds each pile with `tempfile` and reads it; it writes no box, no file of
yours, reads no key, and reaches no network. Exit codes, the kernel's: `0` it
ran; `2` refused (a bad command line — no `run`, a size that isn't a positive
number, or a repeat below 1).
