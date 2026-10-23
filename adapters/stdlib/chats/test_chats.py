"""chats: WhatsApp and Telegram exports mirrored as dated lines, read by the kernel."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHATS = HERE / "chats.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def mirror(folder: Path, to: Path, *flags: str) -> subprocess.CompletedProcess:
    return run(str(CHATS), "mirror", "--from", str(folder), "--to", str(to), *flags)


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


def test_both_whatsapp_shapes_and_pm_time(tmp_path):
    folder, to = tmp_path / "exports", tmp_path / "mirror"
    put(
        folder,
        "chats/Dev.txt",
        "[03/12/2024, 08:10:00] Dev Raman: I can do 600 tonight\n"
        "15/10/2026, 5:02 PM - Sam Okafor: Sent the invoice\n",
    )
    got = mirror(folder, to)
    assert got.returncode == 0, got.stderr
    assert out_of(to, "chats/Dev.txt") == (
        "2024-12-03 08:10  Dev Raman: I can do 600 tonight\n"
        "\n"
        "2026-10-15 17:02  Sam Okafor: Sent the invoice\n"
    )


def test_continuation_line_joins_its_message(tmp_path):
    folder, to = tmp_path / "exports", tmp_path / "mirror"
    put(
        folder,
        "Dev.txt",
        "15/10/2026, 17:45 - Sam Okafor: Sent the invoice,\n"
        "the second half is on the next line\n"
        "and the third\n"
        "\n"
        "15/10/2026, 17:50 - Dev Raman: Thanks\n"
        "15/10/2026, 17:51 - Sam Okafor: Good\n",
    )
    assert mirror(folder, to).returncode == 0
    assert out_of(to, "Dev.txt") == (
        "2026-10-15 17:45  Sam Okafor: Sent the invoice, the second half is on "
        "the next line and the third\n"
        "2026-10-15 17:50  Dev Raman: Thanks\n"
        "2026-10-15 17:51  Sam Okafor: Good\n"
    )


def test_day_first_decided_by_a_date_like_15_10_2026(tmp_path):
    folder, to = tmp_path / "exports", tmp_path / "mirror"
    put(
        folder,
        "Dev.txt",
        "15/10/2026, 17:45 - Sam Okafor: Sent the invoice\n"
        "04/05/2026, 09:00 - Dev Raman: Paid\n",
    )
    assert mirror(folder, to).returncode == 0
    text = out_of(to, "Dev.txt")
    assert "2026-05-04 09:00  Dev Raman: Paid" in text
    assert "(date order unknown)" not in text


def test_month_first_decided_by_a_date_like_10_15_2026(tmp_path):
    folder, to = tmp_path / "exports", tmp_path / "mirror"
    put(
        folder,
        "Dev.txt",
        "10/15/2026, 17:45 - Sam Okafor: Sent the invoice\n"
        "03/07/2026, 09:00 - Dev Raman: Paid\n",
    )
    assert mirror(folder, to).returncode == 0
    text = out_of(to, "Dev.txt")
    assert "2026-03-07 09:00  Dev Raman: Paid" in text
    assert "2026-10-15 17:45  Sam Okafor: Sent the invoice" in text


def test_undecidable_file_is_written_as_given_and_flag_settles_it(tmp_path):
    folder = tmp_path / "exports"
    put(
        folder,
        "Dev.txt",
        "03/12/2024, 08:10 - Dev Raman: I can do 600 tonight\n"
        "05/06/2024, 09:00 - Sam Okafor: Boiler is off\n",
    )
    as_given, settled = tmp_path / "given", tmp_path / "settled"
    assert mirror(folder, as_given).returncode == 0
    assert out_of(as_given, "Dev.txt") == (
        "(date order unknown)\n"
        "\n"
        "03/12/2024 08:10  Dev Raman: I can do 600 tonight\n"
        "\n"
        "05/06/2024 09:00  Sam Okafor: Boiler is off\n"
    )
    assert mirror(folder, settled, "--day-first").returncode == 0
    assert out_of(settled, "Dev.txt") == (
        "2024-12-03 08:10  Dev Raman: I can do 600 tonight\n"
        "\n"
        "2024-06-05 09:00  Sam Okafor: Boiler is off\n"
    )


def test_a_flag_that_contradicts_the_file_skips_it(tmp_path):
    folder, to = tmp_path / "exports", tmp_path / "mirror"
    put(folder, "Dev.txt", "15/10/2026, 17:45 - Sam Okafor: Sent the invoice\n")
    got = mirror(folder, to, "--month-first")
    assert got.returncode == 42
    assert "wrote 0 files" in got.stdout and "skipped 1" in got.stdout
    assert "its dates say day-first" in got.stderr


def test_telegram_list_text_and_service_message(tmp_path):
    folder, to = tmp_path / "exports", tmp_path / "mirror"
    export = {
        "name": "Sam Okafor",
        "type": "personal_chat",
        "messages": [
            {
                "id": 1,
                "type": "service",
                "date": "2024-12-02T19:00:00",
                "actor": "Sam Okafor",
                "action": "pin_message",
            },
            {
                "id": 2,
                "type": "message",
                "date": "2024-12-03T08:10:00",
                "from": "Dev Raman",
                "text": "I can do 600 tonight",
            },
            {
                "id": 3,
                "type": "message",
                "date": "2024-12-03T09:00:00",
                "from": "Sam Okafor",
                "text": ["Check the ", {"type": "link", "text": "boiler"}, " note"],
            },
        ],
    }
    put(folder, "tg/result.json", json.dumps(export))
    assert mirror(folder, to).returncode == 0
    assert out_of(to, "tg/result.json") == (
        "2024-12-03 08:10  Dev Raman: I can do 600 tonight\n"
        "2024-12-03 09:00  Sam Okafor: Check the boiler note\n"
    )


def test_one_paragraph_per_day(tmp_path):
    folder, to = tmp_path / "exports", tmp_path / "mirror"
    put(
        folder,
        "Dev.txt",
        "15/10/2026, 08:00 - Dev Raman: Morning\n"
        "15/10/2026, 09:00 - Dev Raman: Still morning\n"
        "16/10/2026, 08:00 - Dev Raman: New day\n",
    )
    assert mirror(folder, to).returncode == 0
    assert out_of(to, "Dev.txt") == (
        "2026-10-15 08:00  Dev Raman: Morning\n"
        "2026-10-15 09:00  Dev Raman: Still morning\n"
        "\n"
        "2026-10-16 08:00  Dev Raman: New day\n"
    )


def test_a_txt_that_is_not_a_chat_is_not_counted(tmp_path):
    folder, to = tmp_path / "exports", tmp_path / "mirror"
    put(folder, "memo.txt", "Dinner at seven.\n\nRemember the 15/10/2026 meeting.\n")
    put(folder, "Dev.txt", "15/10/2026, 17:45 - Sam Okafor: Sent the invoice\n")
    got = mirror(folder, to)
    assert got.returncode == 0
    assert "skipped 0" in got.stdout and "wrote 1 files" in got.stdout
    assert not (to / "memo.txt.txt").exists()


def test_mirror_inside_folder_and_folder_inside_mirror_are_refused(tmp_path):
    folder = tmp_path / "exports"
    put(folder, "Dev.txt", "15/10/2026, 17:45 - Sam Okafor: Sent the invoice\n")
    inside = mirror(folder, folder / "out")
    assert inside.returncode == 2 and inside.stderr.startswith("refused:")
    around = mirror(folder, tmp_path)
    assert around.returncode == 2 and around.stderr.startswith("refused:")
    assert not (folder / "out").exists()
    not_dir = run(
        str(CHATS),
        "mirror",
        "--from",
        str(folder / "Dev.txt"),
        "--to",
        str(tmp_path / "m"),
    )
    assert not_dir.returncode == 2 and not_dir.stderr.startswith("refused:")


def test_nothing_readable_exits_42(tmp_path):
    folder, to = tmp_path / "exports", tmp_path / "mirror"
    put(folder, "notes.txt", "Just words.\n")
    put(folder, "photo.jpg", "not text")
    got = mirror(folder, to)
    assert got.returncode == 42
    assert got.stdout.strip() == f"wrote 0 files to {to}; skipped 0"


def test_unreadable_chats_are_skipped_and_counted(tmp_path):
    folder, to = tmp_path / "exports", tmp_path / "mirror"
    put(folder, "broken.json", '{"messages": [{"date": "2024-12-03T08:10:00", ')
    put(folder, "Dev.txt", "15/10/2026, 17:45 - Sam Okafor: Sent the invoice\n")
    got = mirror(folder, to)
    assert got.returncode == 0
    assert "skipped 1" in got.stdout and "wrote 1 files" in got.stdout
    assert not (to / "broken.json.txt").exists()


def test_originals_are_unchanged_and_nothing_is_added_to_the_folder(tmp_path):
    folder, to = tmp_path / "exports", tmp_path / "mirror"
    put(folder, "chats/Dev.txt", "03/12/2024, 08:10 - Dev Raman: Hi\n")
    put(
        folder,
        "tg/result.json",
        json.dumps(
            {"messages": [{"date": "2024-12-03T08:10:00", "from": "A", "text": "x"}]}
        ),
    )
    before = snapshot(folder)
    assert mirror(folder, to).returncode == 0
    assert snapshot(folder) == before


def test_two_runs_give_identical_bytes(tmp_path):
    folder = tmp_path / "exports"
    put(
        folder,
        "chats/Dev.txt",
        "03/12/2024, 08:10 - Dev Raman: Hi\n15/10/2026, 08:00 - Sam: Yo\n",
    )
    put(
        folder,
        "tg/result.json",
        json.dumps(
            {"messages": [{"date": "2024-12-03T08:10:00", "from": "A", "text": "x"}]}
        ),
    )
    first, second = tmp_path / "one", tmp_path / "two"
    assert mirror(folder, first, "--day-first").returncode == 0
    assert mirror(folder, second, "--day-first").returncode == 0
    assert snapshot(first) == snapshot(second)
    for body in snapshot(first).values():
        assert body.endswith(b"\n") and b"\r" not in body


def test_the_kernel_serves_a_message_line(tmp_path):
    folder = tmp_path / "exports"
    put(
        folder,
        "chats/Dev.txt",
        "[03/12/2024, 08:10:00] Dev Raman: I can do 600 tonight\n"
        "15/10/2026, 17:45 - Sam Okafor: Sent the invoice\n",
    )
    pile, box = tmp_path / "pile", tmp_path / "box"
    assert mirror(folder, pile).returncode == 0
    init = run(
        str(KERNEL),
        "init",
        "--box",
        str(box),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "key"),
        *NOW,
    )
    assert init.returncode == 0, init.stderr
    got = run(str(KERNEL), "bite", "--box", str(box), *NOW, "Dev Raman 600 tonight")
    assert got.returncode == 0, got.stderr
    served = json.loads(got.stdout)["served"]
    assert any(
        "2024-12-03 08:10  Dev Raman: I can do 600 tonight" in s["text"] for s in served
    )


def test_json_whose_messages_carry_no_dates_is_not_a_chat_and_not_counted(tmp_path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    src.mkdir()
    (src / "settings.json").write_text('{"messages": [{"text": "hello"}]}')
    (src / "chat.txt").write_text("[13/12/2024, 08:10:00] Dev Raman: I can do 600\n")
    got = mirror(src, dst)
    assert got.returncode == 0 and got.stdout.strip().endswith("; skipped 0")
    assert not (dst / "settings.json.txt").exists()


def test_a_telegram_export_not_in_utf8_is_skipped_and_counted(tmp_path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    src.mkdir()
    (src / "result.json").write_bytes(
        '{"messages": [{"date": "2024-12-13T08:10:00", "from": "Andr\u00e9", "text": "caf\u00e9"}]}'.encode(
            "latin-1"
        )
    )
    (src / "chat.txt").write_text("[13/12/2024, 08:10:00] Dev Raman: I can do 600\n")
    got = mirror(src, dst)
    assert got.stdout.strip().endswith("; skipped 1")
    assert "result.json: not UTF-8" in got.stderr
