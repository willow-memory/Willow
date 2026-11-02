"""Tests for apple_mail.py. Every .emlx is built here as Apple Mail writes one
(the byte count on its own line, the message, then an XML property list),
from example.org addresses; nothing is read from a fixture file."""

from __future__ import annotations

import json
import plistlib
import subprocess
import sys
from email.message import EmailMessage
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "apple_mail.py"
MAIL = HERE.parent / "mail" / "mail.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = "2026-11-02T00:00:00Z"

PLAIN = (
    "From: Ada Example <ada@example.org>\n"
    "To: Ben Example <ben@example.org>\n"
    "Date: Thu, 14 Oct 2026 09:15:00 +0100\n"
    "Subject: Roof estimate\n"
    "\n"
    "The estimate is in.\n"
    "\n"
    "The total is 4,200.\n"
).encode()

RENDERED = (
    "From: Ada Example <ada@example.org>\n"
    "To: Ben Example <ben@example.org>\n"
    "Date: 2026-10-14 09:15\n"
    "Subject: Roof estimate\n"
    "\n"
    "The estimate is in.\n"
    "\n"
    "The total is 4,200.\n"
)

#: 2026-10-14 07:46:40 UTC
RECEIVED = 1791964000


def plist(**extra) -> bytes:
    fields = {"date-received": RECEIVED, "flags": 8590195713, "remote-id": "4471"}
    fields.update(extra)
    return plistlib.dumps(fields, fmt=plistlib.FMT_XML)


def emlx(message: bytes, tail: bytes | None = None) -> bytes:
    """As Apple Mail writes it: the count padded with spaces, then the message."""
    return (
        f"{len(message):<10}\n".encode() + message + (plist() if tail is None else tail)
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def mirror_of(tmp_path: Path, files: dict[str, bytes], script: Path = SCRIPT):
    src = tmp_path / "src"
    for rel, data in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    out = tmp_path / "out"
    return run(str(script), "mirror", "--from", str(src), "--to", str(out)), out


def tree(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_an_emlx_reads_as_its_message_with_sender_date_and_subject(tmp_path):
    got, out = mirror_of(tmp_path, {"INBOX.mbox/Messages/12.emlx": emlx(PLAIN)})
    assert got.returncode == 0, got.stderr
    assert got.stdout == f"wrote 1 files to {out}; skipped 0\n"
    text = (out / "INBOX.mbox" / "Messages" / "12.emlx.txt").read_text("utf-8")
    assert text == RENDERED


def test_the_text_is_the_same_as_mails_text_of_the_same_message(tmp_path):
    msg = EmailMessage()
    msg["From"] = "Ada <ada@example.org>"
    msg["To"] = "Ben <ben@example.org>, Cy <cy@example.org>"
    msg["Date"] = "Wed, 21 Oct 2026 16:30:00 +0000"
    msg["Subject"] = "Plans for the allotment"
    msg.set_content("Plot 14 has the gate that sticks.\n")
    msg.add_alternative("<p>Plot 14 has the <b>gate</b> that sticks.</p>", "html")
    msg.add_attachment(b"%PDF", "application", "pdf", filename="plan.pdf")
    raw = msg.as_bytes()
    apple, a_out = mirror_of(tmp_path / "a", {"1.emlx": emlx(raw)})
    plain, m_out = mirror_of(tmp_path / "m", {"1.eml": raw}, MAIL)
    assert apple.returncode == plain.returncode == 0
    text = (a_out / "1.emlx.txt").read_text("utf-8")
    assert text == (m_out / "1.eml.txt").read_text("utf-8")
    assert "Plot 14 has the gate that sticks." in text
    assert text.endswith("\nAttachment: plan.pdf\n")


def test_a_partial_emlx_is_read_and_still_names_its_attachment(tmp_path):
    raw = (
        b"From: Ada <ada@example.org>\nTo: Ben <ben@example.org>\n"
        b"Date: Wed, 21 Oct 2026 16:30:00 +0000\nSubject: The quote\n"
        b'MIME-Version: 1.0\nContent-Type: multipart/mixed; boundary="b1"\n\n'
        b"--b1\nContent-Type: text/plain\n\nThe quote is attached.\n"
        b'--b1\nContent-Type: application/pdf; name="quote.pdf"\n'
        b'Content-Disposition: attachment; filename="quote.pdf"\n'
        b"X-Apple-Content-Length: 48211\n\n\n--b1--\n"
    )
    got, out = mirror_of(tmp_path, {"Messages/7.partial.emlx": emlx(raw)})
    assert got.returncode == 0, got.stderr
    text = (out / "Messages" / "7.partial.emlx.txt").read_text("utf-8")
    assert text == (
        "From: Ada <ada@example.org>\nTo: Ben <ben@example.org>\n"
        "Date: 2026-10-21 16:30\nSubject: The quote\n\n"
        "The quote is attached.\n\nAttachment: quote.pdf\n"
    )


def test_the_messages_own_date_comes_before_the_date_received(tmp_path):
    got, out = mirror_of(tmp_path, {"1.emlx": emlx(PLAIN)})
    text = (out / "1.emlx.txt").read_text("utf-8")
    assert "\nDate: 2026-10-14 09:15\n" in text
    assert "received" not in text and "07:46" not in text


def test_with_no_date_header_the_date_received_is_used_and_counted(tmp_path):
    raw = PLAIN.replace(b"Date: Thu, 14 Oct 2026 09:15:00 +0100\n", b"")
    files = {"1.emlx": emlx(raw), "2.emlx": emlx(raw), "3.emlx": emlx(PLAIN)}
    got, out = mirror_of(tmp_path, files)
    assert got.returncode == 0, got.stderr
    assert got.stdout == (
        "2 had no Date header; their Date is Apple Mail's date received, in UTC\n"
        f"wrote 3 files to {out}; skipped 0\n"
    )
    # in the text, only the date: no word of its own on every such message
    want = RENDERED.replace("Date: 2026-10-14 09:15\n", "Date: 2026-10-14 07:46\n")
    assert (out / "1.emlx.txt").read_text("utf-8") == want
    assert (out / "3.emlx.txt").read_text("utf-8") == RENDERED


def test_an_empty_date_header_counts_as_none(tmp_path):
    raw = PLAIN.replace(b"Thu, 14 Oct 2026 09:15:00 +0100", b"")
    got, out = mirror_of(tmp_path, {"1.emlx": emlx(raw)})
    text = (out / "1.emlx.txt").read_text("utf-8")
    assert "\nDate: 2026-10-14 07:46\n" in text
    assert got.stdout.startswith("1 had no Date header;")


def test_with_neither_date_the_date_line_says_none(tmp_path):
    raw = PLAIN.replace(b"Date: Thu, 14 Oct 2026 09:15:00 +0100\n", b"")
    files = {
        "nolist.emlx": emlx(raw, b""),
        "broken.emlx": emlx(raw, b"<?xml not a plist"),
        "nodate.emlx": emlx(raw, plistlib.dumps({"flags": 1}, fmt=plistlib.FMT_XML)),
        "words.emlx": emlx(raw, plist(**{"date-received": "yesterday"})),
        "yes.emlx": emlx(raw, plist(**{"date-received": True})),
        "far.emlx": emlx(raw, plist(**{"date-received": 10**18})),
        "array.emlx": emlx(raw, plistlib.dumps([1, 2], fmt=plistlib.FMT_XML)),
    }
    got, out = mirror_of(tmp_path, files)
    assert got.returncode == 0, got.stderr
    assert got.stdout == f"wrote 7 files to {out}; skipped 0\n"
    for name in files:
        text = (out / f"{name}.txt").read_text("utf-8")
        assert "\nDate: none\n" in text, name


def test_a_bad_count_or_a_short_file_is_skipped_and_counted(tmp_path):
    files = {
        "a-words.emlx": b"twelve\n" + PLAIN + plist(),
        "b-none.emlx": PLAIN,
        "c-short.emlx": f"{len(PLAIN) + 1}\n".encode() + PLAIN,
        "d-empty.emlx": b"",
        "e-onlycount.emlx": b"120",
        "f-ok.emlx": emlx(PLAIN),
        "g-negative.emlx": f"-{len(PLAIN)}\n".encode() + PLAIN,
        "h-zero.emlx": b"0\n" + PLAIN,
    }
    got, out = mirror_of(tmp_path, files)
    assert got.returncode == 0, got.stderr
    assert got.stdout == f"wrote 1 files to {out}; skipped 7\n"
    assert sorted(tree(out)) == ["f-ok.emlx.txt"]


def test_exactly_the_counted_bytes_are_the_message(tmp_path):
    files = {
        "bare.emlx": f"{len(PLAIN)}\n".encode() + PLAIN,
        "crlf.emlx": f"{len(PLAIN)}\r\n".encode() + PLAIN + plist(),
    }
    got, out = mirror_of(tmp_path, files)
    assert got.returncode == 0, got.stderr
    assert got.stdout.endswith("; skipped 0\n")
    for name in files:
        assert (out / f"{name}.txt").read_text("utf-8") == RENDERED, name


def test_an_8bit_utf8_subject_is_read_as_utf8(tmp_path):
    raw = PLAIN.replace(b"Roof estimate", "Roof estimate — £4,200".encode())
    got, out = mirror_of(tmp_path, {"1.emlx": emlx(raw)})
    text = (out / "1.emlx.txt").read_text("utf-8")
    assert "\nSubject: Roof estimate — £4,200\n" in text


def test_not_a_message_or_binary_is_skipped_and_counted(tmp_path):
    files = {
        "notes.emlx": emlx(b"just some words\nand more\n"),
        "nul.emlx": emlx(PLAIN.replace(b"The total", b"The\0total")),
    }
    got, out = mirror_of(tmp_path, files)
    assert got.returncode == 42
    assert got.stdout == f"wrote 0 files to {out}; skipped 2\n"
    assert tree(out) == {}


def test_only_emlx_is_read_and_hidden_names_are_skipped(tmp_path):
    files = {
        "Messages/1.emlx": emlx(PLAIN),
        "Messages/2.EMLX": emlx(PLAIN),
        "Attachments/1/2/quote.emlxpart": b"%PDF",
        "Messages/1.eml": PLAIN,
        ".hidden/3.emlx": emlx(PLAIN),
        "Messages/.4.emlx": emlx(PLAIN),
    }
    got, out = mirror_of(tmp_path, files)
    assert got.returncode == 0, got.stderr
    assert got.stdout == f"wrote 2 files to {out}; skipped 0\n"
    assert sorted(tree(out)) == ["Messages/1.emlx.txt", "Messages/2.EMLX.txt"]


def test_the_same_folder_gives_the_same_bytes_and_is_never_changed(tmp_path):
    src = tmp_path / "src"
    (src / "Messages").mkdir(parents=True)
    (src / "Messages" / "1.emlx").write_bytes(emlx(PLAIN))
    before = tree(src)
    one, two = tmp_path / "one", tmp_path / "two"
    assert (
        run(str(SCRIPT), "mirror", "--from", str(src), "--to", str(one)).returncode == 0
    )
    assert (
        run(str(SCRIPT), "mirror", "--from", str(src), "--to", str(two)).returncode == 0
    )
    assert tree(one) == tree(two) and tree(one)
    assert tree(src) == before


def test_refusals(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "1.emlx").write_bytes(emlx(PLAIN))
    afile = tmp_path / "afile"
    afile.write_text("x")
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", str(src)],
        ["copy", "--from", str(src), "--to", str(tmp_path / "o")],
        ["mirror", "--to", str(src), "--from", str(tmp_path / "o")],
        ["mirror", "--from", str(src), "--at", str(tmp_path / "o")],
        ["mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "o")],
        ["mirror", "--from", str(src), "--to", str(afile)],
        ["mirror", "--from", str(src), "--to", str(src)],
        ["mirror", "--from", str(src), "--to", str(src / "inside")],
        ["mirror", "--from", str(src), "--to", str(tmp_path)],
    ):
        got = run(str(SCRIPT), *argv)
        assert got.returncode == 2, argv
        assert got.stderr.startswith("refused"), argv
    assert sorted(tree(src)) == ["1.emlx"]
    assert not (tmp_path / "o").exists()


def test_a_mirror_that_cannot_be_written_is_refused(tmp_path):
    src = tmp_path / "src"
    (src / "Messages").mkdir(parents=True)
    (src / "Messages" / "1.emlx").write_bytes(emlx(PLAIN))
    out = tmp_path / "out"
    out.mkdir()
    (out / "Messages").write_text("in the way")
    got = run(str(SCRIPT), "mirror", "--from", str(src), "--to", str(out))
    assert got.returncode == 2
    assert got.stderr.startswith("refused: cannot write")


def test_the_kernel_finds_the_date_received_beside_its_message(tmp_path):
    """Asked about the message, the kernel serves the passage with its date."""
    raw = PLAIN.replace(b"Date: Thu, 14 Oct 2026 09:15:00 +0100\n", b"")
    got, out = mirror_of(tmp_path, {"Messages/1.emlx": emlx(raw)})
    assert got.returncode == 0, got.stderr
    box, key = tmp_path / "box", tmp_path / "key"
    init = run(
        str(KERNEL), "init", "--box", str(box), "--pile", str(out),
        "--key", str(key), "--now", NOW,
    )  # fmt: skip
    assert init.returncode == 0, init.stderr
    bite = run(
        str(KERNEL), "bite", "--box", str(box), "--now", NOW,
        "when did the roof estimate come",
    )  # fmt: skip
    assert bite.returncode == 0, bite.stdout + bite.stderr
    doc = json.loads(bite.stdout)
    assert doc["state"] == "populated"
    assert any(
        s["where"].startswith("Messages/1.emlx.txt:")
        and "2026-10-14 07:46" in s["text"]
        for s in doc["served"]
    )


def test_a_question_about_what_the_folder_lacks_is_not_answered(tmp_path):
    """The reader adds no word of its own to a message, so a word it might
    have added ("received", "utc", "header", "emlx"), paired with one the
    folder doesn't hold, is never answered; real questions still are."""
    sys.path.insert(0, str(KERNEL.parent))
    import kernel

    bare = PLAIN.replace(b"Date: Thu, 14 Oct 2026 09:15:00 +0100\n", b"")
    other = bare.replace(b"Roof estimate", b"Allotment gate").replace(
        b"The estimate is in.", b"Plot 14 has the gate that sticks."
    )
    files = {f"Messages/{n}.emlx": emlx(m) for n, m in enumerate((bare, other, bare))}
    got, out = mirror_of(tmp_path, files)
    assert got.returncode == 0, got.stderr
    pile = kernel.chunks(out)
    for absent in (
        "volcano received",
        "volcano utc",
        "volcano header",
        "volcano apple",
    ):
        assert kernel.rank(pile, absent) == [], absent
    assert kernel.rank(pile, "allotment gate")
    assert kernel.rank(pile, "roof estimate")
