"""ocr: text read by tesseract from pictures and from scanned PDF pages,
into a mirror the kernel searches; a PDF page with text of its own left to
the pdf add-on; the shared reader contract; and a refusal, never a quiet
skip, without what it needs."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "ocr.py"
NOW = ["--now", "2026-10-30T09:00:00Z"]
spec = importlib.util.spec_from_file_location("ocr", SCRIPT)
ocr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocr)


def page(*lines: str):
    """A clean picture of a page: black text, large, on white."""
    from PIL import Image, ImageDraw, ImageFont

    im = Image.new("L", (1000, 100 + 90 * len(lines)), 255)
    draw, font = ImageDraw.Draw(im), ImageFont.load_default(size=44)
    for i, line in enumerate(lines):
        draw.text((30, 40 + 90 * i), line, fill=0, font=font)
    return im


def text_pdf(text: str) -> bytes:
    """A one-page PDF with a text layer, written by hand as the pdf add-on's
    tests write theirs."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objs = ["<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [4 0 R] /Count 1 >>",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            "/Resources << /Font << /F1 3 0 R >> >> /Contents 5 0 R >>",
            f"<< /Length {len(stream)} >>\nstream\n{stream.decode()}\nendstream"]  # fmt: skip
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n".encode()
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets).encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def run(*argv: str, **kw) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True, **kw)


def folder(tmp_path: Path) -> Path:
    src = tmp_path / "post"
    (src / "letters").mkdir(parents=True)
    page("Notice of determination", "File within 180 days").save(
        src / "letters" / "county.png"
    )
    first, second = page("Dear Odile"), page("The van is sold")
    first.save(src / "letters" / "two.tif", save_all=True, append_images=[second])
    buf = io.BytesIO()
    page("Gas bill paid in March").convert("RGB").save(buf, "PDF", resolution=100)
    (src / "scan.pdf").write_bytes(buf.getvalue())
    (src / "typed.pdf").write_bytes(text_pdf("Typed, with text of its own"))
    page().save(src / "blank.png")
    (src / "broken.jpg").write_bytes(b"\xff\xd8 not a picture")
    (src / ".hidden").mkdir()
    page("hidden").save(src / ".hidden" / "x.png")
    (src / "notes.txt").write_text("not a picture\n")
    return src


def mirror(src: Path, dst: Path, *more: str, **kw) -> subprocess.CompletedProcess:
    return run(str(SCRIPT), "mirror", "--from", str(src), "--to", str(dst), *more, **kw)


def test_pictures_and_scanned_pages_are_read(tmp_path):
    src, dst = folder(tmp_path), tmp_path / "mirror"
    got = mirror(src, dst)
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip().endswith(
        "; 1 with no text to read; 1 PDFs with text of their own, the pdf add-on's; skipped 1"
    )
    assert (dst / "letters" / "county.png.txt").read_text() == (
        "Notice of determination\n\nFile within 180 days\n"
    )
    assert (dst / "letters" / "two.tif.txt").read_text() == (
        "== page 1\nDear Odile\n\n== page 2\nThe van is sold\n"
    )
    assert (dst / "scan.pdf.txt").read_text() == "== page 1\nGas bill paid in March\n"
    assert sorted(p.name for p in dst.rglob("*") if p.is_file()) == [
        "county.png.txt", "scan.pdf.txt", "two.tif.txt"]  # fmt: skip


def test_tidy_keeps_paragraphs_and_drops_the_rest():
    assert ocr.tidy("a  \n\n\n\nb\x0c\n\n") == "a\n\nb"
    assert ocr.tidy("\n\n") == ""


def test_the_kernel_finds_what_was_only_in_a_picture(tmp_path):
    src, dst = folder(tmp_path), tmp_path / "mirror"
    mirror(src, dst)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(dst),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    got = json.loads(run(str(KERNEL), "bite", "--box", str(b), *NOW, "gas bill").stdout)
    assert got["state"] == "populated"
    assert got["served"][0]["where"] == "scan.pdf.txt:1"


def test_the_same_file_gives_the_same_bytes_and_originals_are_untouched(tmp_path):
    src = folder(tmp_path)
    before = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    for name in ("one", "two"):
        mirror(src, tmp_path / name)
    for rel in ("letters/county.png.txt", "letters/two.tif.txt", "scan.pdf.txt"):
        assert (tmp_path / "one" / rel).read_bytes() == (
            tmp_path / "two" / rel
        ).read_bytes()
    assert {p: p.read_bytes() for p in src.rglob("*") if p.is_file()} == before


def test_refusals_and_nothing_readable(tmp_path):
    src = folder(tmp_path)
    assert mirror(src, src / "m").returncode == 2
    assert mirror(src, tmp_path).returncode == 2
    assert mirror(tmp_path / "nowhere", tmp_path / "m").returncode == 2
    assert run(str(SCRIPT), "mirror", "--from", str(src)).returncode == 2
    bad = mirror(src, tmp_path / "m", "--lang", "klingon")
    assert bad.returncode == 2 and "no language pack for klingon" in bad.stderr
    empty = tmp_path / "empty"
    empty.mkdir()
    page().save(empty / "blank.png")
    assert mirror(empty, tmp_path / "m2").returncode == 42


def test_without_tesseract_it_refuses_and_names_the_install(tmp_path):
    src = folder(tmp_path)
    got = mirror(src, tmp_path / "m", env={"PATH": str(tmp_path / "nothing"),
                                            "PYTHONPATH": ":".join(sys.path)})  # fmt: skip
    assert got.returncode == 2 and "tesseract-ocr" in got.stderr


def test_without_pypdf_it_refuses_and_names_the_install(tmp_path):
    blocker = tmp_path / "block"
    blocker.mkdir()
    (blocker / "pypdf.py").write_text("raise ImportError('hidden', name='pypdf')\n")
    src = folder(tmp_path)
    script = (
        "import runpy, sys\n"
        f"sys.path.insert(0, {str(blocker)!r})\n"
        f"sys.argv = [{str(SCRIPT)!r}] + sys.argv[1:]\n"
        f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')\n"
    )
    got = run("-c", script, "mirror", "--from", str(src), "--to", str(tmp_path / "m"))
    assert got.returncode == 2 and "requirements.txt" in got.stderr
