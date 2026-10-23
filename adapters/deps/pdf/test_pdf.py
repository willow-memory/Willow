"""pdf: page text out of PDFs into a mirror the kernel searches; the shared
reader contract; and a refusal, never a quiet skip, without pypdf."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def make_pdf(pages: list[str]) -> bytes:
    """A minimal PDF, written by hand: one Helvetica line per page."""
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", None,
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]  # fmt: skip
    kids = []
    for text in pages:
        stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
        objs.append(
            f"<< /Length {len(stream)} >>\nstream\n{stream.decode()}\nendstream"
        )
        content = len(objs)
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                    f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content} 0 R >>")  # fmt: skip
        kids.append(f"{len(objs)} 0 R")
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>"
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n".encode()
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets).encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def folder(tmp_path: Path) -> Path:
    src = tmp_path / "papers"
    (src / "letters").mkdir(parents=True)
    (src / "letters" / "county.pdf").write_bytes(
        make_pdf(["Notice of determination", "You may file a response within 180 days"])
    )
    (src / "broken.pdf").write_bytes(b"%PDF-1.4\nthis is not a real pdf\n")
    (src / ".hidden").mkdir()
    (src / ".hidden" / "x.pdf").write_bytes(make_pdf(["hidden"]))
    (src / "notes.txt").write_text("not a pdf\n")
    return src


def test_each_page_becomes_a_headed_paragraph(tmp_path):
    src, dst = folder(tmp_path), tmp_path / "mirror"
    got = run(str(HERE / "pdf.py"), "mirror", "--from", str(src), "--to", str(dst))
    assert got.returncode == 0, got.stderr
    assert got.stdout.startswith("wrote 1 files to") and got.stdout.strip().endswith(
        "skipped 1"
    )
    text = (dst / "letters" / "county.pdf.txt").read_text()
    assert text == (
        "== page 1\nNotice of determination\n\n"
        "== page 2\nYou may file a response within 180 days\n"
    )
    assert not (dst / ".hidden").exists() and not (dst / "notes.txt.txt").exists()


def test_the_kernel_finds_what_was_only_inside_a_pdf(tmp_path):
    src, dst = folder(tmp_path), tmp_path / "mirror"
    run(str(HERE / "pdf.py"), "mirror", "--from", str(src), "--to", str(dst))
    b = tmp_path / "box"
    run(
        str(KERNEL),
        "init",
        "--box",
        str(b),
        "--pile",
        str(dst),
        "--key",
        str(tmp_path / "k"),
        *NOW,
    )
    got = json.loads(run(str(KERNEL), "bite", "--box", str(b), *NOW,
                         "how long to file a response").stdout)  # fmt: skip
    assert got["state"] == "populated"
    assert got["served"][0]["where"] == "letters/county.pdf.txt:4"
    assert "page 2" in got["served"][0]["text"]


def test_the_same_pdf_gives_the_same_bytes_and_originals_are_untouched(tmp_path):
    src = folder(tmp_path)
    before = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    for name in ("one", "two"):
        run(
            str(HERE / "pdf.py"),
            "mirror",
            "--from",
            str(src),
            "--to",
            str(tmp_path / name),
        )
    a = (tmp_path / "one" / "letters" / "county.pdf.txt").read_bytes()
    assert a == (tmp_path / "two" / "letters" / "county.pdf.txt").read_bytes()
    assert {p: p.read_bytes() for p in src.rglob("*") if p.is_file()} == before


def test_refusals_and_nothing_readable(tmp_path):
    src = folder(tmp_path)
    inside = run(
        str(HERE / "pdf.py"), "mirror", "--from", str(src), "--to", str(src / "m")
    )
    assert inside.returncode == 2 and inside.stderr.startswith("refused:")
    around = run(
        str(HERE / "pdf.py"), "mirror", "--from", str(src), "--to", str(tmp_path)
    )
    assert around.returncode == 2
    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "a.txt").write_text("x\n")
    none = run(
        str(HERE / "pdf.py"),
        "mirror",
        "--from",
        str(empty),
        "--to",
        str(tmp_path / "m2"),
    )
    assert none.returncode == 42


def test_without_pypdf_it_refuses_and_names_the_install(tmp_path):
    """Run with pypdf hidden: a refusal naming the install, never exit 0 or 42."""
    blocker = tmp_path / "block"
    blocker.mkdir()
    (blocker / "pypdf.py").write_text("raise ImportError('hidden for the test')\n")
    src = folder(tmp_path)
    script = (
        "import runpy, sys\n"
        f"sys.path.insert(0, {str(blocker)!r})\n"
        f"sys.argv = [{str(HERE / 'pdf.py')!r}] + sys.argv[1:]\n"
        f"runpy.run_path({str(HERE / 'pdf.py')!r}, run_name='__main__')\n"
    )
    got = run("-c", script, "mirror", "--from", str(src), "--to", str(tmp_path / "m"))
    assert got.returncode == 2 and "requirements.txt" in got.stderr
