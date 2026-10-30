r"""logs.py: System and app logs (syslog, journald's export, nginx): each line dated. Python 3.9+.

    python adapters/stdlib/logs/logs.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .log files that are one of three kinds of log (hidden folders
and files skipped; any other .log skipped and counted) and writes each entry as a
dated line, so you can ask when something started:

    2024-03-02 08:15  host sshd: Accepted publickey for ana from 10.0.0.2
    Mar 02 08:16  host cron: (root) CMD (run-parts /etc/cron.hourly)
    2024-03-02 08:17  192.0.2.7 GET /garden 200 1234

Syslog (`Mar  2 08:15:30 host sshd[1234]: message`, or the ISO form rsyslog writes,
`2024-03-02T08:15:30+00:00 host sshd[1234]: message`), journald's export format
(`journalctl -o export`: KEY=value blocks with `__REALTIME_TIMESTAMP`, `MESSAGE`
and `SYSLOG_IDENTIFIER`) and the web servers' access log (nginx and Apache's
combined format). A classic syslog line has no year, and none is invented: it
keeps its month and day as written. Process ids are taken off. Lines that are not
entries (a stack trace under an error) are left out. A file is a log of one of the
kinds when most of its first twenty lines are; one over 50 MB is not read.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

BIGGEST = 50 * 1024 * 1024
SYSLOG = re.compile(
    r"^(?P<mon>[A-Z][a-z]{2}) {1,2}(?P<day>\d{1,2}) (?P<hm>\d{2}:\d{2}):\d{2} (?P<host>\S+) (?P<proc>[^\s:\[]+)(?:\[\d+\])?: ?(?P<msg>.*)$"
)
ISO = re.compile(
    r"^(?P<d>\d{4}-\d{2}-\d{2})[T ](?P<hm>\d{2}:\d{2})[\d:.]*(?:Z|[+-]\d{2}:?\d{2})? (?P<host>\S+) (?P<proc>[^\s:\[]+)(?:\[\d+\])?: ?(?P<msg>.*)$"
)
ACCESS = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<d>\d{2})/(?P<mon>[A-Z][a-z]{2})/(?P<y>\d{4}):(?P<hm>\d{2}:\d{2}):\d{2} [^\]]*\] "(?P<req>[^"]*)" (?P<status>\d{3}) (?P<size>\S+)'
)
MONTHS = {
    m: i
    for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)
}


def entry(line: str) -> str:
    """A log line as a dated line, or "" when it is not an entry of a known kind."""
    if m := ISO.match(line):
        return (
            f"{m['d']} {m['hm']}  {m['host']} {m['proc']}: {m['msg'].strip()}".rstrip(
                ": "
            )
        )
    if m := SYSLOG.match(line):
        if m["mon"] in MONTHS:
            return f"{m['mon']} {int(m['day']):02d} {m['hm']}  {m['host']} {m['proc']}: {m['msg'].strip()}".rstrip(
                ": "
            )
    if m := ACCESS.match(line):
        if m["mon"] in MONTHS:
            parts = m["req"].split()
            what = " ".join(parts[:2]) if len(parts) >= 2 else m["req"]
            return f"{m['y']}-{MONTHS[m['mon']]:02d}-{m['d']} {m['hm']}  {m['ip']} {what} {m['status']} {m['size']}"
    return ""


def journal(text: str) -> list[str]:
    out = []
    for block in text.replace("\r\n", "\n").split("\n\n"):
        fields = dict(
            ln.split("=", 1)
            for ln in block.split("\n")
            if "=" in ln and ln.split("=", 1)[0].isupper()
        )
        stamp, msg = (
            fields.get("__REALTIME_TIMESTAMP", ""),
            fields.get("MESSAGE", "").strip(),
        )
        if stamp.isdigit() and msg:
            try:
                when = datetime.fromtimestamp(
                    int(stamp) / 1_000_000, tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M")
            except (OverflowError, OSError, ValueError):
                continue
            who = " ".join(
                x
                for x in (
                    fields.get("_HOSTNAME", ""),
                    fields.get("SYSLOG_IDENTIFIER", ""),
                )
                if x
            )
            out.append(f"{when}  {who}: {msg}" if who else f"{when}  {msg}")
    return out


def convert(data: bytes) -> str | None:
    if len(data) > BIGGEST:
        raise ValueError("a log over 50 MB is not read")
    text = data.decode("utf-8-sig", errors="replace")
    head = [ln for ln in text.split("\n") if ln.strip()][:20]
    if "__REALTIME_TIMESTAMP=" in text[:5000]:
        found = journal(text)
    else:
        lines = [entry(ln.rstrip()) for ln in text.split("\n")]
        if not head or sum(1 for ln in head if entry(ln.rstrip())) * 2 < len(head):
            return None
        found = [x for x in lines if x]
    return "\n".join(found) + "\n" if found else None


EXTS = (".log",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: logs.py mirror --from FOLDER --to MIRROR"


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and name.lower().endswith(EXTS) and p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            text = convert(path.read_bytes())
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except ERRORS:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src = Path(opts["--from"]).resolve()
    dst = Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
