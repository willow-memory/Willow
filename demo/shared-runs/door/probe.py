"""probe.py: a small notebook that asks Kaggle three things nothing on its
pages answers. Run as a private CPU script notebook; it steps nothing.

    python demo/shared-runs/door/probe.py            # as Kaggle runs it
    PROBE_SECONDS=0 python demo/shared-runs/door/probe.py   # at once, to try it

What it is for, and what whoever pushes it does beside it:

    1  Can a run hand something out before it ends? Every `PROBE_EVERY`
       seconds it writes a numbered line to `ticks.txt` in its output
       folder and prints the same line. While it runs, ask for its output
       and its log from outside. If a tick written a minute ago can be
       read while the run goes on, a door could look in mid-run.
    2  Is there a value that outlasts a run and stays out of its output?
       If the account has a secret named SHARED_RUNS_PROBE, it says that
       it found one and how long it is, and never the value.
    3  What happens when it is pushed again while it runs? Push it a
       second time halfway through and see: queued, refused, or stopped.
       Each run prints the moment it began, so the two can be told apart.

It also says what machine it is on at the start and at the end, to see
whether a session keeps one. It reaches no network, reads nothing of the
account's but that one secret's presence, and writes two small files to
its own output folder. Exit 0 always: every answer is a line it prints.
"""

from __future__ import annotations

import json
import os
import platform
import time
from pathlib import Path


def machine() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.partition(":")[2].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def secret() -> str:
    """Whether the account holds the probe's secret, and never what it is."""
    try:
        from kaggle_secrets import UserSecretsClient  # only there on Kaggle
    except ImportError:
        return "no secrets client here: not on Kaggle, or it is not offered"
    try:
        value = UserSecretsClient().get_secret("SHARED_RUNS_PROBE")
    except Exception as why:  # the client's own errors differ by version
        return f"the client is here; no secret of that name was given ({type(why).__name__})"
    return f"a secret of that name was given, {len(value)} characters long; its value is not said"


def main() -> int:
    seconds = int(os.environ.get("PROBE_SECONDS", "240"))
    every = max(1, int(os.environ.get("PROBE_EVERY", "30")))
    out = Path(os.environ.get("PROBE_OUT", "/kaggle/working"))
    out.mkdir(parents=True, exist_ok=True)
    began = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    said = {"began": began, "machine_at_start": machine(), "secret": secret(),
            "seconds": seconds, "every": every}  # fmt: skip
    print("probe:", json.dumps(said, sort_keys=True), flush=True)
    ticks = out / "ticks.txt"
    start, n = time.time(), 0
    while True:
        line = f"tick {n} of run {began}, {round(time.time() - start)} s in"
        with ticks.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        print(line, flush=True)
        if time.time() - start >= seconds:
            break
        time.sleep(min(every, max(0, seconds - (time.time() - start))))
        n += 1
    said.update(machine_at_end=machine(), ticks=n + 1,
                same_machine=said["machine_at_start"] == machine())  # fmt: skip
    (out / "probe.json").write_text(json.dumps(said, indent=1, sort_keys=True) + "\n")
    print("probe ended:", json.dumps(said, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
