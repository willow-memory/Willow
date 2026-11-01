"""texts: Android and iPhone text backups mirrored as dated lines, read by the kernel."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEXTS = HERE / "texts.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]
DEC3 = 1733184000  # 2024-12-03 00:00 UTC
HEAD = (
    "<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>\n"
    "<!--File Created By SMS Backup & Restore v10.20.002-->\n"
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def mirror(folder: Path, to: Path, *flags: str) -> subprocess.CompletedProcess:
    return run(str(TEXTS), "mirror", "--from", str(folder), "--to", str(to), *flags)


def put(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def out_of(to: Path, rel: str) -> str:
    return (to / f"{rel}.txt").read_bytes().decode("utf-8")


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def ms(seconds: int) -> str:
    return str(seconds * 1000)


def sms(seconds: int, kind: str, body: str, name: str = "Dev Raman", number: str = "+15550100") -> str:  # fmt: skip
    return (
        f'<sms address="{number}" date="{ms(seconds)}" type="{kind}" '
        f'body="{body}" contact_name="{name}" />\n'
    )


def test_texts_and_picture_messages_one_line_each_a_paragraph_a_day(tmp_path):
    folder, to = tmp_path / "phone", tmp_path / "mirror"
    put(
        folder,
        "backup/sms-20241205.xml",
        HEAD
        + '<smses count="6">\n'
        + sms(DEC3 + 29400, "1", "I can do   600 tonight")
        + sms(DEC3 + 29520, "2", "Done")
        + sms(DEC3 + 29600, "3", "a draft never sent")
        + sms(DEC3 + 29700, "5", "a send that failed")
        + sms(DEC3 + 86400 + 60, "1", "Who is this?", "(Unknown)", "+15550199")
        + f'<mms date="{ms(DEC3 + 86400 + 300)}" msg_box="1" address="+15550100" '
        'contact_name="Dev Raman"><parts><part ct="application/smil" text="&lt;smil/&gt;"/>'
        '<part ct="image/jpeg"/><part ct="text/plain" text="the roof"/></parts></mms>\n'
        + f'<mms date="{ms(DEC3 + 86400 + 400)}" msg_box="2" address="+15550100" '
        'contact_name="Dev Raman"><parts><part ct="video/mp4"/></parts></mms>\n'
        + "</smses>\n",
    )
    got = mirror(folder, to, "--tz", "UTC", "--me", "Ana")
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip() == f"wrote 1 files to {to}; skipped 0"
    assert out_of(to, "backup/sms-20241205.xml") == (
        "# +15550199\n"
        "\n"
        "2024-12-04 00:01  +15550199: Who is this?\n"
        "\n"
        "# Dev Raman\n"
        "\n"
        "2024-12-03 08:10  Dev Raman: I can do 600 tonight\n"
        "2024-12-03 08:12  Ana: Done\n"
        "\n"
        "2024-12-04 00:05  Dev Raman: [picture] the roof\n"
        "2024-12-04 00:06  Ana: [video]\n"
    )


def test_your_own_messages_are_me_unless_named(tmp_path):
    folder, to = tmp_path / "phone", tmp_path / "mirror"
    put(folder, "sms.xml", HEAD + "<smses>\n" + sms(DEC3, "2", "") + "</smses>\n")
    assert mirror(folder, to, "--tz", "UTC").returncode == 0
    assert out_of(to, "sms.xml").endswith("2024-12-03 00:00  me: (no text)\n")


def test_calls_with_their_kind_and_length(tmp_path):
    folder, to = tmp_path / "phone", tmp_path / "mirror"
    put(
        folder,
        "calls.xml",
        HEAD
        + "<calls>\n"
        + f'<call number="+15550100" duration="185" date="{ms(DEC3 + 3600)}" type="2" contact_name="Dev Raman"/>\n'
        + f'<call number="+15550100" duration="0" date="{ms(DEC3 + 7200)}" type="3" contact_name="Dev Raman"/>\n'
        + f'<call number="+15550100" duration="45" date="{ms(DEC3 + 7300)}" type="1" contact_name="Dev Raman"/>\n'
        + f'<call number="+15550111" duration="x" date="{ms(DEC3 + 7400)}" type="9" contact_name=""/>\n'
        + "</calls>\n",
    )  # fmt: skip
    assert mirror(folder, to, "--tz", "UTC").returncode == 0
    assert out_of(to, "calls.xml") == (
        "# +15550111\n"
        "\n"
        "2024-12-03 02:03  call of type 9\n"
        "\n"
        "# Dev Raman\n"
        "\n"
        "2024-12-03 01:00  outgoing call, 3 min\n"
        "2024-12-03 02:00  missed call\n"
        "2024-12-03 02:01  incoming call, 45 s\n"
    )


def test_tz_names_the_zone_the_times_are_written_in(tmp_path):
    folder, to = tmp_path / "phone", tmp_path / "mirror"
    put(
        folder,
        "sms.xml",
        HEAD + "<smses>\n" + sms(DEC3 + 3600, "1", "hi") + "</smses>\n",
    )
    assert mirror(folder, to, "--tz", "America/Denver").returncode == 0
    assert "2024-12-02 18:00  Dev Raman: hi" in out_of(to, "sms.xml")


def test_a_zone_it_does_not_know_is_refused_and_writes_nothing(tmp_path):
    folder, to = tmp_path / "phone", tmp_path / "mirror"
    put(folder, "sms.xml", HEAD + "<smses>\n" + sms(DEC3, "1", "hi") + "</smses>\n")
    got = mirror(folder, to, "--tz", "Mars/Olympus")
    assert got.returncode == 2 and got.stderr.startswith("refused"), got.stderr
    assert not to.exists()


def attributed(text: str) -> bytes:
    """An attributedBody as an iPhone writes one: the words after NSString."""
    data = text.encode("utf-8")
    size = bytes([len(data)]) if len(data) < 0x80 else b"\x81" + len(data).to_bytes(2, "little")  # fmt: skip
    return (
        b"\x04\x0bstreamtyped\x81\xe8\x03\x84\x01@\x84\x84\x84\x12NSAttributedString"
        b"\x00\x84\x84\x08NSObject\x00\x85\x92\x84\x84\x84\x08NSString\x01\x94\x84\x01+"
        + size
        + data
        + b"\x86\x84\x02iI\x01"
    )


def iphone_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.executescript(
        "CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT);"
        "CREATE TABLE message (ROWID INTEGER PRIMARY KEY, date INTEGER, is_from_me INTEGER,"
        " text TEXT, attributedBody BLOB, handle_id INTEGER);"
        "CREATE TABLE chat (ROWID INTEGER PRIMARY KEY, chat_identifier TEXT, display_name TEXT);"
        "CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER);"
        "INSERT INTO handle VALUES (1, '+15550100'), (2, 'sam@example.org');"
        "INSERT INTO chat VALUES (1, '+15550100', ''), (2, 'chat123', 'Roof crew');"
    )  # fmt: skip
    apple = DEC3 - 978307200
    long = "a long one " * 20
    rows = [
        (1, (apple + 29400) * 10**9, 0, "I can do 600 tonight", None, 1, 1),
        (2, (apple + 29520) * 10**9, 1, None, attributed("Done"), 0, 1),
        (3, apple + 29580, 1, None, attributed(long), 0, 1),  # seconds, before iOS 11
        (4, (apple + 40000) * 10**9, 0, "Tiles on Friday", None, 2, 2),
        (5, (apple + 40060) * 10**9, 1, None, None, 0, 2),
    ]
    for rowid, date, mine, text, body, handle, chat in rows:
        con.execute("INSERT INTO message VALUES (?, ?, ?, ?, ?, ?)", (rowid, date, mine, text, body, handle))  # fmt: skip
        con.execute("INSERT INTO chat_message_join VALUES (?, ?)", (chat, rowid))
    con.commit()
    con.close()


def test_an_iphone_sms_db_under_its_hashed_name(tmp_path):
    folder, to = tmp_path / "phone", tmp_path / "mirror"
    iphone_db(folder / "3d" / "3d0d7e5fb2ce288813306e4d4636395e047a3d28")
    before = snapshot(folder)
    got = mirror(folder, to, "--tz", "UTC", "--me", "Ana")
    assert got.returncode == 0, got.stderr
    assert snapshot(folder) == before, "the database is opened read-only"
    assert out_of(to, "3d/3d0d7e5fb2ce288813306e4d4636395e047a3d28") == (
        "# +15550100\n"
        "\n"
        "2024-12-03 08:10  +15550100: I can do 600 tonight\n"
        "2024-12-03 08:12  Ana: Done\n"
        "2024-12-03 08:13  Ana: " + " ".join(("a long one " * 20).split()) + "\n"
        "\n"
        "# Roof crew\n"
        "\n"
        "2024-12-03 11:06  sam@example.org: Tiles on Friday\n"
        "2024-12-03 11:07  Ana: (no text)\n"
    )


def test_an_older_iphone_db_without_chats_or_attributed_bodies(tmp_path):
    folder, to = tmp_path / "phone", tmp_path / "mirror"
    folder.mkdir()
    con = sqlite3.connect(folder / "sms.db")
    con.executescript(
        "CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT);"
        "CREATE TABLE message (ROWID INTEGER PRIMARY KEY, date INTEGER, is_from_me INTEGER,"
        " text TEXT, handle_id INTEGER);"
        "INSERT INTO handle VALUES (1, '+15550100');"
        f"INSERT INTO message VALUES (1, {DEC3 - 978307200}, 0, 'hello', 1);"
        "INSERT INTO message VALUES (2, NULL, 0, 'no date', 1);"
    )
    con.close()
    assert mirror(folder, to, "--tz", "UTC").returncode == 0
    assert out_of(to, "sms.db") == "# +15550100\n\n2024-12-03 00:00  +15550100: hello\n"


def test_what_is_not_a_phone_backup_is_not_counted(tmp_path):
    folder, to = tmp_path / "phone", tmp_path / "mirror"
    put(folder, "feed.xml", "<?xml version='1.0'?>\n<rss><channel/></rss>\n")
    put(folder, "notes.txt", "<smses> is a word in this note\n")
    con = sqlite3.connect(folder / "other.db")
    con.execute("CREATE TABLE message (date INTEGER)")
    con.close()
    got = mirror(folder, to)
    assert got.returncode == 42
    assert got.stdout.strip() == f"wrote 0 files to {to}; skipped 0"


def test_a_backup_it_cannot_read_is_skipped_and_counted(tmp_path):
    folder, to = tmp_path / "phone", tmp_path / "mirror"
    put(folder, "broken.xml", HEAD + "<smses>\n<sms date='1' \n")
    put(folder, "empty.xml", HEAD + "<smses count='0'>\n</smses>\n")
    put(folder, "nodate.xml", HEAD + "<smses>\n<sms type='1' body='hi'/>\n</smses>\n")
    put(folder, "good.xml", HEAD + "<smses>\n" + sms(DEC3, "1", "hi") + "</smses>\n")
    got = mirror(folder, to, "--tz", "UTC")
    assert got.returncode == 0
    assert got.stdout.strip() == f"wrote 1 files to {to}; skipped 3"
    assert "skipped broken.xml: not valid XML" in got.stderr
    assert "skipped empty.xml: no message or call in it" in got.stderr
    assert "skipped nodate.xml: a sms with no date it can read" in got.stderr
    assert sorted(snapshot(to)) == ["good.xml.txt"]


def test_the_kernel_serves_a_day_of_texts(tmp_path):
    folder, pile, box = tmp_path / "phone", tmp_path / "pile", tmp_path / "box"
    put(
        folder,
        "sms.xml",
        HEAD + "<smses>\n" + sms(DEC3 + 29400, "1", "I can do 600 tonight")
        + sms(DEC3 + 29520, "2", "Done") + "</smses>\n",
    )  # fmt: skip
    assert mirror(folder, pile, "--tz", "UTC").returncode == 0
    init = run(str(KERNEL), "init", "--box", str(box), "--pile", str(pile),
               "--key", str(tmp_path / "key"), *NOW)  # fmt: skip
    assert init.returncode == 0, init.stderr
    got = run(str(KERNEL), "bite", "--box", str(box), *NOW, "Dev Raman 600 tonight")
    assert got.returncode == 0, got.stderr
    served = json.loads(got.stdout)["served"]
    assert any(
        "2024-12-03 08:10  Dev Raman: I can do 600 tonight\n2024-12-03 08:12  me: Done"
        in s["text"]
        for s in served
    )
