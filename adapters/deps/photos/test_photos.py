"""photos: each photo's date, place and camera from its EXIF, as a dated
passage in a mirror the kernel searches; the shared reader contract; and a
refusal, never a quiet skip, without Pillow."""

from __future__ import annotations

import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "photos.py"
spec = importlib.util.spec_from_file_location("photos", SCRIPT)
ph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph)
NOW = ["--now", "2026-10-29T09:00:00Z"]


def ifd(entries: dict, at: int) -> tuple[bytes, bytes]:
    """One little-endian TIFF directory at offset `at`: (its entries, the data
    too long to sit in an entry, placed right after it). Values: str (ASCII),
    int (a LONG, for a sub-directory's offset) or a tuple of floats (RATIONALs
    over 1000)."""
    head = 2 + 12 * len(entries) + 4
    body, extra = bytearray(struct.pack("<H", len(entries))), bytearray()
    for tag in sorted(entries):
        v = entries[tag]
        if isinstance(v, str):
            kind, data = 2, v.encode() + b"\0"
        elif isinstance(v, int):
            kind, data = 4, struct.pack("<I", v)
        else:
            kind = 5
            data = b"".join(struct.pack("<II", round(x * 1000), 1000) for x in v)
        count = len(data) if kind == 2 else len(data) // (4 if kind == 4 else 8)
        if len(data) <= 4:
            field = data.ljust(4, b"\0")
        else:
            field = struct.pack("<I", at + head + len(extra))
            extra += data + b"\0" * (len(data) % 2)
        body += struct.pack("<HHI", tag, kind, count) + field
    return bytes(body + b"\0\0\0\0"), bytes(extra)


def exif_bytes(top: dict, sub: dict, gps: dict) -> bytes:
    """EXIF written by hand, as a camera lays it out, not by Pillow, whose
    writer at the floor drops sub-directories it reads."""
    out = bytearray(b"II*\0" + struct.pack("<I", 8))
    order = [("top", dict(top)), ("sub", sub), ("gps", gps)]
    # each directory's offset depends on the ones before it: lay them out
    # once to size the pointers, once to place them, once to write them
    for _ in range(3):
        out, at, where = bytearray(b"II*\0" + struct.pack("<I", 8)), 8, {}
        for name, entries in order:
            if name != "top" and not entries:
                continue
            where[name] = at
            body, extra = ifd(entries, at)
            out += body + extra
            at = len(out)
        if sub:
            order[0][1][ph.EXIF] = where.get("sub", 0)
        if gps:
            order[0][1][ph.GPS] = where.get("gps", 0)
    return b"Exif\0\0" + bytes(out)


def photo(path: Path, taken=None, gps=None, make=None, model=None, kind="JPEG"):
    """A 4x4 picture with the EXIF a camera would write."""
    from PIL import Image

    top = {k: v for k, v in ((ph.MAKE, make), (ph.MODEL, model)) if v}
    blob = exif_bytes(top, {ph.TAKEN: taken} if taken else {}, gps or {})
    Image.new("RGB", (4, 4), "green").save(path, kind, exif=blob)


EIFFEL = {1: "N", 2: (48.0, 51.0, 30.132), 3: "E", 4: (2.0, 17.0, 40.128)}
RIO = {1: "S", 2: (22.0, 57.0, 6.0), 3: "W", 4: (43.0, 12.0, 36.0)}


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def folder(tmp_path: Path) -> Path:
    src = tmp_path / "pictures"
    (src / "holidays").mkdir(parents=True)
    photo(src / "holidays" / "eiffel.jpg", "2024:07:14 09:32:10", EIFFEL,
          "Apple", "iPhone 12")  # fmt: skip
    photo(src / "holidays" / "beach.png", "2023:01:02 17:05:00", RIO,
          "Canon", "Canon EOS 5D", kind="PNG")  # fmt: skip
    photo(src / "scan.jpg")  # no date, no place
    (src / "broken.jpg").write_bytes(b"\xff\xd8 not a real jpeg")
    (src / ".hidden").mkdir()
    photo(src / ".hidden" / "x.jpg", "2020:01:01 00:00:00")
    (src / "notes.txt").write_text("not a photo\n")
    return src


def mirror(src: Path, dst: Path) -> subprocess.CompletedProcess:
    return run(str(SCRIPT), "mirror", "--from", str(src), "--to", str(dst))


def test_each_photo_becomes_a_dated_passage(tmp_path):
    src, dst = folder(tmp_path), tmp_path / "mirror"
    got = mirror(src, dst)
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip().endswith("; 1 with no date or place; skipped 1")
    assert (dst / "holidays" / "eiffel.jpg.txt").read_text() == (
        "2024-07-14 09:32:10 holidays/eiffel.jpg\n"
        "at 48.858370 N, 2.294480 E\n"
        "camera Apple iPhone 12\n"
    )
    assert (dst / "holidays" / "beach.png.txt").read_text() == (
        "2023-01-02 17:05:00 holidays/beach.png\n"
        "at 22.951667 S, 43.210000 W\n"
        "camera Canon EOS 5D\n"
    )
    assert sorted(p.name for p in dst.rglob("*") if p.is_file()) == [
        "beach.png.txt", "eiffel.jpg.txt"]  # fmt: skip


def test_a_place_without_a_date_and_a_date_without_a_place(tmp_path):
    src = tmp_path / "p"
    src.mkdir()
    photo(src / "a.jpg", gps=EIFFEL)
    photo(src / "b.jpg", taken="2022:05:06 07:08:09")
    photo(src / "c.jpg", taken="0000:00:00 00:00:00")  # a camera's unset clock
    got = mirror(src, tmp_path / "m")
    assert got.returncode == 0 and "1 with no date or place" in got.stdout
    assert (tmp_path / "m" / "a.jpg.txt").read_text() == (
        "a.jpg\nat 48.858370 N, 2.294480 E\n"
    )
    assert (tmp_path / "m" / "b.jpg.txt").read_text() == "2022-05-06 07:08:09 b.jpg\n"


def test_the_readings_of_a_stamp_and_a_position():
    assert ph.when("2024:07:14 09:32:10\0") == "2024-07-14 09:32:10"
    assert ph.when("yesterday") == ph.when(None) == ""
    assert ph.where({1: "N", 2: (91.0, 0.0, 0.0), 3: "E", 4: (0.0, 0.0, 0.0)}) == ""
    assert ph.where({1: "N", 2: ("x",)}) == ""


def test_the_kernel_finds_where_and_when_a_photo_was_taken(tmp_path):
    src, dst = folder(tmp_path), tmp_path / "mirror"
    mirror(src, dst)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(dst),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    got = json.loads(
        run(str(KERNEL), "bite", "--box", str(b), *NOW, "eiffel holidays").stdout
    )
    assert got["state"] == "populated"
    assert got["served"][0]["where"] == "holidays/eiffel.jpg.txt:1"
    assert "2024-07-14" in got["served"][0]["text"]


def test_the_same_photo_gives_the_same_bytes_and_originals_are_untouched(tmp_path):
    src = folder(tmp_path)
    before = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    for name in ("one", "two"):
        mirror(src, tmp_path / name)
    a = (tmp_path / "one" / "holidays" / "eiffel.jpg.txt").read_bytes()
    assert a == (tmp_path / "two" / "holidays" / "eiffel.jpg.txt").read_bytes()
    assert {p: p.read_bytes() for p in src.rglob("*") if p.is_file()} == before


def test_refusals_and_nothing_readable(tmp_path):
    src = folder(tmp_path)
    assert mirror(src, src / "m").returncode == 2
    assert mirror(src, tmp_path).returncode == 2
    assert run(str(SCRIPT), "mirror", "--from", str(src)).returncode == 2
    assert mirror(tmp_path / "nowhere", tmp_path / "m").returncode == 2
    empty = tmp_path / "empty"
    empty.mkdir()
    photo(empty / "plain.jpg")
    assert mirror(empty, tmp_path / "m2").returncode == 42


def test_without_pillow_it_refuses_and_names_the_install(tmp_path):
    blocker = tmp_path / "block"
    (blocker / "PIL").mkdir(parents=True)
    (blocker / "PIL" / "__init__.py").write_text("raise ImportError('hidden')\n")
    src = folder(tmp_path)
    script = (
        "import runpy, sys\n"
        f"sys.path.insert(0, {str(blocker)!r})\n"
        f"sys.argv = [{str(SCRIPT)!r}] + sys.argv[1:]\n"
        f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')\n"
    )
    got = run("-c", script, "mirror", "--from", str(src), "--to", str(tmp_path / "m"))
    assert got.returncode == 2 and "requirements.txt" in got.stderr
