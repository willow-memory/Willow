"""session_cost.py: tokens each agent session spent, by day and by repo.

    python adapters/stdlib/session-cost/session_cost.py --from FOLDER \\
        [--prices FILE]

Walks FOLDER for `.jsonl` session files and sums the usage they already
recorded (input and output tokens, by model). Sessions are grouped by the
day and the repo in the file (the folder name of `cwd`, or `gitBranch`).
`--prices` is a table you keep, one `model in_per_million out_per_million`
line, dollars per million tokens; without it, only tokens are said.

    session-cost: 2 sessions, 1 day
    2026-10-30  Willow  claude-opus-5-5  in 100 out 50

It only reads. Hidden folders and files are skipped. A file that is not a
session, or that recorded no usage, is skipped and not counted as a
session. Exit codes, the kernel's: 0 some usage; 42 nothing there; 2
refused.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: session_cost.py --from FOLDER [--prices FILE]"


def prices_of(raw: str) -> dict[str, tuple[float, float]]:
    """{model: (in_per_million, out_per_million)} from a table you keep."""
    out = {}
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) != 3:
            continue
        try:
            out[parts[0]] = (float(parts[1]), float(parts[2]))
        except ValueError:
            continue
    return out


def _usage(obj: dict) -> list[tuple[str, int, int]]:
    """[(model, input, output)] from one JSONL object."""
    msg = obj.get("message") if isinstance(obj.get("message"), dict) else {}
    usage = obj.get("usage") or msg.get("usage")
    if not isinstance(usage, dict):
        return []
    model = str(obj.get("model") or msg.get("model") or "unknown")
    inn = int(usage.get("input_tokens") or 0)
    out = int(usage.get("output_tokens") or 0)
    if inn == 0 and out == 0:
        return []
    return [(model, inn, out)]


def _day(obj: dict) -> str:
    ts = str(obj.get("timestamp") or "")
    return ts[:10] if len(ts) >= 10 and ts[4] == "-" else "unknown"


def _repo(obj: dict) -> str:
    cwd = str(obj.get("cwd") or "")
    if cwd:
        return Path(cwd).name or cwd
    return str(obj.get("gitBranch") or "unknown")


def sessions_of(folder: Path) -> list[tuple[str, str, str, int, int]]:
    """[(day, repo, model, input, output), ...] one row a session-model."""
    rows = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            if name.startswith(".") or not name.endswith(".jsonl"):
                continue
            path = Path(dirpath) / name
            if not path.is_file():
                continue
            tallies: dict[tuple[str, str, str], list[int]] = {}
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for line in text.splitlines():
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    tallies = {}
                    break
                if not isinstance(obj, dict):
                    continue
                for model, inn, out in _usage(obj):
                    key = (_day(obj), _repo(obj), model)
                    got = tallies.setdefault(key, [0, 0])
                    got[0] += inn
                    got[1] += out
            for (day, repo, model), (inn, out) in sorted(tallies.items()):
                rows.append((day, repo, model, inn, out))
    return rows


def render(rows: list[tuple[str, str, str, int, int]], prices: dict) -> str:
    days = {r[0] for r in rows}
    n = len({(r[0], r[1], r[2]) for r in rows})
    lines = [
        f"session-cost: {n} session{'s' if n != 1 else ''}, {len(days)} day"
        f"{'' if len(days) == 1 else 's'}"
    ]
    tin = tout = 0.0
    billed = bool(prices)
    for day, repo, model, inn, out in rows:
        tin += inn
        tout += out
        extra = ""
        if billed and model in prices:
            pin, pout = prices[model]
            extra = f"  ${inn / 1e6 * pin + out / 1e6 * pout:.2f}"
        lines.append(f"{day}  {repo}  {model}  in {inn} out {out}{extra}")
    lines.append(f"total  in {int(tin)} out {int(tout)}")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--from", "--prices"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--from") or args:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    folder = Path(opts["--from"])
    if not folder.is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    prices = {}
    if opts.get("--prices"):
        path = Path(opts["--prices"])
        if not path.is_file():
            print(f"refused: not a file: {opts['--prices']}", file=sys.stderr)
            return kernel.REFUSED
        prices = prices_of(path.read_text(encoding="utf-8"))
    rows = sessions_of(folder)
    if not rows:
        print("nothing there: no session recorded any usage")
        return kernel.ESCALATE
    print(render(rows, prices), end="")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
