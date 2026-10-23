"""Tests for mail.py. Every sample message is built here, from example.org
addresses; nothing is read from a fixture file."""

from __future__ import annotations

import base64
import json
import subprocess
import sys
from email.message import EmailMessage
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIL = HERE / "mail.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = "2026-10-23T00:00:00Z"

PLAIN = (
    "From: Ada Example <ada@example.org>\n"
    "To: Ben Example <ben@example.org>\n"
    "Date: Thu, 14 Oct 2026 09:15:00 +0100\n"
    "Subject: Roof estimate\n"
    "\n"
    "The estimate is in.\n"
    "\n"
    "The total is 4,200.\n"
)

MBOX = (
    "From ada@example.org Wed Oct 21 16:30:00 2026\n"
    "From: Ada <ada@example.org>\n"
    "To: Ben <ben@example.org>\n"
    "Date: Wed, 21 Oct 2026 16:30:00 +0000\n"
    "Subject: First\n"
    "\n"
    "first body\n"
    "\n"
    "From ben@example.org Thu Oct 22 08:00:00 2026\n"
    "From: Ben <ben@example.org>\n"
    "To: Ada <ada@example.org>\n"
    "Date: Thu, 22 Oct 2026 08:00:00 +0000\n"
    "Subject: Second\n"
    "\n"
    "second body\n"
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def mirror(folder: Path, dest: Path) -> subprocess.CompletedProcess:
    return run(str(MAIL), "mirror", "--from", str(folder), "--to", str(dest))


def put(root: Path, rel: str, data: str | bytes) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    return path


def tree(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_plain_eml_becomes_header_block_and_body(tmp_path):
    folder, dest = tmp_path / "src", tmp_path / "out"
    put(folder, "inbox/a.eml", PLAIN)
    got = mirror(folder, dest)
    assert got.returncode == 0, got.stderr
    assert got.stdout == f"wrote 1 files to {dest}; skipped 0\n"
    assert (dest / "inbox" / "a.eml.txt").read_text(encoding="utf-8") == (
        "From: Ada Example <ada@example.org>\n"
        "To: Ben Example <ben@example.org>\n"
        "Date: 2026-10-14 09:15\n"
        "Subject: Roof estimate\n"
        "\n"
        "The estimate is in.\n"
        "\n"
        "The total is 4,200.\n"
    )


def test_date_is_iso_in_the_senders_own_clock(tmp_path):
    raw = PLAIN.replace(
        "Thu, 14 Oct 2026 09:15:00 +0100", "Mon, 19 Oct 2026 23:30:00 -0500"
    )
    folder, dest = tmp_path / "src", tmp_path / "out"
    put(folder, "a.eml", raw)
    assert mirror(folder, dest).returncode == 0
    out = (dest / "a.eml.txt").read_text(encoding="utf-8")
    # 23:30 at -0500 stays 23:30: no conversion, so the line is the same every run
    assert "\nDate: 2026-10-19 23:30\n" in out


def test_multipart_keeps_text_and_names_attachment_not_content(tmp_path):
    msg = EmailMessage()
    msg["From"] = "Ada <ada@example.org>"
    msg["To"] = "Ben <ben@example.org>"
    msg["Date"] = "Wed, 21 Oct 2026 16:30:00 +0000"
    msg["Subject"] = "Estimate attached"
    msg.set_content("The PDF is attached.\n")
    msg.add_attachment(
        b"SECRETPAYLOAD",
        maintype="application",
        subtype="pdf",
        filename="estimate.pdf",
    )
    folder, dest = tmp_path / "src", tmp_path / "out"
    put(folder, "m/b.eml", msg.as_bytes())
    assert mirror(folder, dest).returncode == 0
    out = (dest / "m" / "b.eml.txt").read_text(encoding="utf-8")
    assert "The PDF is attached." in out
    assert out.endswith("\n\nAttachment: estimate.pdf\n")
    assert "SECRETPAYLOAD" not in out
    assert base64.b64encode(b"SECRETPAYLOAD").decode() not in out


def test_an_unnamed_attachment_is_listed_and_its_text_never_read(tmp_path):
    """A text part marked as an attachment, with no file name: still an
    attachment, so its words never become the body (added by review)."""
    msg = EmailMessage()
    msg["From"] = "Ada <ada@example.org>"
    msg["To"] = "Ben <ben@example.org>"
    msg["Date"] = "Wed, 21 Oct 2026 16:30:00 +0000"
    msg["Subject"] = "Notes attached"
    msg.set_content("See the attached notes.\n")
    msg.add_attachment("HIDDENWORDS in an attachment\n", disposition="attachment")
    folder, dest = tmp_path / "src", tmp_path / "out"
    put(folder, "m/c.eml", msg.as_bytes())
    assert mirror(folder, dest).returncode == 0
    out = (dest / "m" / "c.eml.txt").read_text(encoding="utf-8")
    assert "See the attached notes." in out
    assert "HIDDENWORDS" not in out
    assert "Attachment: (unnamed text/plain)" in out


def test_html_only_message_has_its_tags_stripped(tmp_path):
    raw = (
        "From: Cy <cy@example.org>\n"
        "To: Ben <ben@example.org>\n"
        "Date: Mon, 19 Oct 2026 10:00:00 +0000\n"
        "Subject: Offer\n"
        "Content-Type: text/html; charset=utf-8\n"
        "\n"
        "<html><head><style>p{color:red}</style></head><body>"
        "<p>Hello <b>there</b></p><p>Second&nbsp;para &amp; more</p>"
        "<script>alert(1)</script></body></html>\n"
    )
    folder, dest = tmp_path / "src", tmp_path / "out"
    put(folder, "a.eml", raw)
    assert mirror(folder, dest).returncode == 0
    out = (dest / "a.eml.txt").read_text(encoding="utf-8")
    body = out.split("\n\n", 1)[1]  # the header's own "<cy@example.org>" stays
    assert "<" not in body and "alert" not in out and "color:red" not in out
    assert body == "Hello there\n\nSecond para & more\n"


def test_encoded_subject_and_quoted_printable_body_are_decoded(tmp_path):
    raw = (
        "From: Dee <dee@example.org>\n"
        "To: Ben <ben@example.org>\n"
        "Date: Tue, 20 Oct 2026 12:00:00 +0000\n"
        "Subject: =?utf-8?q?Caf=C3=A9_menu_for_Ana?=\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "Content-Transfer-Encoding: quoted-printable\n"
        "\n"
        "Price is =E2=82=AC40 for the tour,=\n"
        "starting Monday.\n"
    )
    folder, dest = tmp_path / "src", tmp_path / "out"
    put(folder, "a.eml", raw)
    assert mirror(folder, dest).returncode == 0
    out = (dest / "a.eml.txt").read_text(encoding="utf-8")
    assert "\nSubject: Café menu for Ana\n" in out
    assert "Price is €40 for the tour,starting Monday." in out


def test_mbox_with_two_messages_is_numbered(tmp_path):
    folder, dest = tmp_path / "src", tmp_path / "out"
    put(folder, "mail/all.mbox", MBOX)
    assert mirror(folder, dest).returncode == 0
    out = (dest / "mail" / "all.mbox.txt").read_text(encoding="utf-8")
    assert out.startswith("== message 1\n\nFrom: Ada <ada@example.org>\n")
    assert "body\n\n== message 2\n\nFrom: Ben <ben@example.org>\n" in out
    assert "first body" in out and "second body" in out
    assert "From ada@example.org" not in out


def test_mirror_path_is_the_same_path_with_txt_added(tmp_path):
    folder, dest = tmp_path / "src", tmp_path / "out"
    put(folder, "inbox/a.eml", PLAIN)
    put(folder, "Old Mail/Box.MBOX", MBOX)
    put(folder, ".hidden/x.eml", PLAIN)
    put(folder, ".dot.eml", PLAIN)
    put(folder, "notes.txt", "not mail")
    got = mirror(folder, dest)
    assert got.returncode == 0, got.stderr
    assert got.stdout == f"wrote 2 files to {dest}; skipped 0\n"
    assert sorted(tree(dest)) == ["Old Mail/Box.MBOX.txt", "inbox/a.eml.txt"]


def test_file_that_is_not_a_message_is_skipped_and_counted(tmp_path):
    folder, dest = tmp_path / "src", tmp_path / "out"
    put(folder, "a.eml", PLAIN)
    put(folder, "junk.eml", "just some words\nwith no headers\n")
    put(folder, "bin.eml", b"\x00\x01\x02")
    got = mirror(folder, dest)
    assert got.returncode == 0, got.stderr
    assert got.stdout == f"wrote 1 files to {dest}; skipped 2\n"
    assert sorted(tree(dest)) == ["a.eml.txt"]


def test_nothing_readable_exits_42(tmp_path):
    folder, dest = tmp_path / "src", tmp_path / "out"
    put(folder, "junk.eml", "just some words\n")
    got = mirror(folder, dest)
    assert got.returncode == 42
    assert got.stdout == f"wrote 0 files to {dest}; skipped 1\n"


def test_mirror_inside_folder_is_refused(tmp_path):
    folder = tmp_path / "src"
    put(folder, "a.eml", PLAIN)
    dest = folder / "out"
    got = mirror(folder, dest)
    assert got.returncode == 2
    assert got.stderr.startswith("refused:")
    assert not dest.exists()


def test_folder_inside_mirror_is_refused(tmp_path):
    dest = tmp_path / "out"
    folder = dest / "src"
    put(folder, "a.eml", PLAIN)
    got = mirror(folder, dest)
    assert got.returncode == 2
    assert got.stderr.startswith("refused:")
    assert tree(dest) == {"src/a.eml": PLAIN.encode("utf-8")}


def test_folder_that_is_not_a_folder_is_refused(tmp_path):
    notes = put(tmp_path, "notes.txt", "a file, not a folder")
    got = mirror(notes, tmp_path / "out")
    assert got.returncode == 2
    assert got.stderr.startswith("refused:")


def test_originals_are_unchanged(tmp_path):
    folder, dest = tmp_path / "src", tmp_path / "out"
    put(folder, "inbox/a.eml", PLAIN)
    put(folder, "mail/all.mbox", MBOX)
    put(folder, "junk.eml", "just some words\n")
    before = {
        p: (p.read_bytes(), p.stat().st_mtime_ns)
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }
    assert mirror(folder, dest).returncode == 0
    after = {
        p: (p.read_bytes(), p.stat().st_mtime_ns)
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }
    assert after == before


def test_two_runs_give_identical_bytes(tmp_path):
    folder, dest = tmp_path / "src", tmp_path / "out"
    put(folder, "inbox/a.eml", PLAIN)
    put(folder, "mail/all.mbox", MBOX)
    assert mirror(folder, dest).returncode == 0
    first = tree(dest)
    assert mirror(folder, dest).returncode == 0
    assert tree(dest) == first and first
    assert all(body.endswith(b"\n") and b"\r" not in body for body in first.values())


def test_kernel_bite_finds_a_word_only_inside_a_base64_body(tmp_path):
    body = base64.encodebytes(b"The marmalade order arrived on Tuesday.\n").decode()
    raw = (
        "From: Eve <eve@example.org>\n"
        "To: Ben <ben@example.org>\n"
        "Date: Fri, 16 Oct 2026 07:45:00 +0000\n"
        "Subject: Order\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "Content-Transfer-Encoding: base64\n"
        "\n" + body
    )
    assert "marmalade" not in raw
    folder, pile = tmp_path / "src", tmp_path / "pile"
    put(folder, "inbox/order.eml", raw)
    assert mirror(folder, pile).returncode == 0
    box, key = tmp_path / "box", tmp_path / "key"
    init = run(
        str(KERNEL), "init", "--box", str(box), "--pile", str(pile),
        "--key", str(key), "--now", NOW,
    )  # fmt: skip
    assert init.returncode == 0, init.stderr
    bite = run(str(KERNEL), "bite", "--box", str(box), "--now", NOW, "marmalade")
    assert bite.returncode == 0, bite.stderr
    doc = json.loads(bite.stdout)
    assert doc["state"] == "populated"
    assert any(
        s["where"].startswith("inbox/order.eml.txt:") and "marmalade" in s["text"]
        for s in doc["served"]
    )
