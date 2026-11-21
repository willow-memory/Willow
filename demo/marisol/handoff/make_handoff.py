"""make_handoff.py: the handoff zip, built the same way every time.

    python3 demo/marisol/handoff/make_handoff.py [--check]

Writes marisol-handoff.zip from this folder's README.md, FOR-FELIPE.md,
suggestions.jsonl and pile/, and the repo's kernel.py as it is now, with fixed
dates and order so the same files give the same bytes. `--check` says whether
the zip on disk is what this would write. The zip never holds a key, a box or
anyone's personal documents.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NAME = "marisol-handoff"
DATE = (2026, 11, 12, 0, 0, 0)


def members() -> list[tuple[str, bytes]]:
    out = [
        ("README.md", (HERE / "README.md").read_bytes()),
        ("FOR-FELIPE.md", (HERE / "FOR-FELIPE.md").read_bytes()),
        ("suggestions.jsonl", (HERE / "suggestions.jsonl").read_bytes()),
        ("kernel.py", (ROOT / "kernel.py").read_bytes()),
    ]
    for p in sorted((HERE / "pile").rglob("*")):
        if p.is_file():
            out.append(
                (f"pile/{p.relative_to(HERE / 'pile').as_posix()}", p.read_bytes())
            )
    return sorted(out)


def build() -> bytes:
    import io

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in members():
            info = zipfile.ZipInfo(f"{NAME}/{name}", DATE)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    return buf.getvalue()


def main(argv: list[str]) -> int:
    target = HERE / f"{NAME}.zip"
    if argv == ["--check"]:
        same = target.is_file() and target.read_bytes() == build()
        print(
            "the zip is what this would write"
            if same
            else "the zip differs from a fresh build"
        )
        return 0 if same else 1
    if argv:
        print("usage: make_handoff.py [--check]", file=sys.stderr)
        return 2
    target.write_bytes(build())
    print(f"wrote {target.name}, {target.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
