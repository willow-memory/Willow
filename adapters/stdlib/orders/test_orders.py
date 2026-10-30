"""orders: an order history as dated lines of items with what they cost; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "orders.py"
spec = importlib.util.spec_from_file_location("orders", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = (
    b"Website,Order ID,Order Date,Currency,Unit Price,Total Owed,Product Name,Order Status\n"
    b'Amazon.co.uk,026-1234567-8901234,2024-03-02T08:15:00Z,GBP,4.5,"4.50","Basil seeds, 3 packets",Closed\n'
    b"Amazon.co.uk,026-7654321-0987654,2024-03-09T10:00:00Z,GBP,6.99,6.99,Garden twine,Closed\n"
)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def mirror_of(
    tmp_path: Path, files: dict[str, bytes]
) -> tuple[subprocess.CompletedProcess, Path]:
    src = tmp_path / "src"
    for rel, data in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    out = tmp_path / "out"
    return run("mirror", "--from", str(src), "--to", str(out)), out


def test_items_come_oldest_first_with_name_cost_currency_and_order():
    csv = (
        b"Order ID,Order Date,Currency,Total Owed,Product Name\n026-1,2024-03-09T10:00:00Z,GBP,6.99,Garden twine\n"
        b'026-2,2024-03-02T08:15:00Z,GBP,"1,204.50",Basil   seeds\n'
    )
    assert mod.convert(csv) == (
        "2024-03-02  Basil seeds  GBP 1204.50  (order 026-2)\n"
        "2024-03-09  Garden twine  GBP 6.99  (order 026-1)\n"
    )


def test_the_older_report_and_other_shops_columns_are_found():
    old = b"Order Date,Order ID,Title,Item Total\n2024-03-02,111,A book,$12.99\n"
    assert mod.convert(old) == "2024-03-02  A book  12.99  (order 111)\n"
    other = b"Date,Item,Amount\n2024-03-02,A thing,3\n"
    assert mod.convert(other) == "2024-03-02  A thing  3.00\n"


def test_the_first_column_of_each_kind_wins_and_the_kinds_are_not_mixed():
    csv = b"Date,Order Date,Description,Product Name,Total,Total Owed\n2020-01-01,2024-03-02,Desc,Prod,1,2\n"
    assert (
        mod.first(["Date", "Order Date"], mod.DATES) == "Order Date"
        and mod.first(["x"], mod.DATES) == ""
    )
    assert mod.convert(csv) == "2024-03-02  Prod  2.00\n"


def test_money_is_read_with_symbols_and_thousands_and_nothing_else():
    m = mod.money
    assert (
        m("4.5") == "4.50"
        and m("1,204.5") == "1204.50"
        and m("$12.99") == "12.99"
        and m("£3") == "3.00"
        and m(" 7 ") == "7.00"
    )
    assert (
        m("") == ""
        and m("free") == ""
        and m("nan") == ""
        and m(None) == ""
        and m(5) == ""
    )


def test_a_date_that_reads_either_way_round_is_never_guessed_and_the_row_is_written_without_it():
    csv = b"Order Date,Product Name,Total\n03/04/2024,Ambiguous,5\n13/04/2024,Clear,6\n"
    assert mod.convert(csv).splitlines() == [
        "Ambiguous  5.00",
        "2024-04-13  Clear  6.00",
    ]


def test_a_row_with_no_name_is_skipped_and_no_cost_is_left_out_and_the_order_for_same_day_rows():
    csv = b"Order Date,Product Name,Total\n2024-03-02,,5\n2024-03-02,Zed,\n2024-03-02,Alpha,2\n"
    assert mod.convert(csv).splitlines() == [
        "2024-03-02  Zed",
        "2024-03-02  Alpha  2.00",
    ]


def test_a_csv_that_is_not_an_order_history_is_not_a_result_and_bad_encoding_is_an_error():
    for other in (
        b"",
        b"a,b\n1,2\n",
        b"Order Date,Product Name\n2024-03-02,x\n",
        b"Product Name,Total\nx,1\n",
        b"Order Date,Total\n2024-03-02,1\n",
        b"Order Date,Product Name,Total\n",
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"\xff\xfe\x00 bad")
    except UnicodeDecodeError:
        pass
    else:
        raise AssertionError("bad bytes")


def test_a_csv_that_is_no_order_history_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path, {"Retail.OrderHistory.1.csv": SAMPLE, "other.csv": b"a,b\n1,2\n"}
    )
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"amazon/Retail.OrderHistory.1.csv": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "amazon/Retail.OrderHistory.1.csv.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "amazon/Retail.OrderHistory.1.csv": SAMPLE,
            ".hid/amazon/Retail.OrderHistory.1.csv": SAMPLE,
            ".amazon/Retail.OrderHistory.1.csv": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["amazon/Retail.OrderHistory.1.csv.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"amazon/Retail.OrderHistory.1.csv": SAMPLE})
    before = (tmp_path / "src" / "amazon/Retail.OrderHistory.1.csv").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "amazon/Retail.OrderHistory.1.csv.txt").read_bytes() == (
        out / "amazon/Retail.OrderHistory.1.csv.txt"
    ).read_bytes()
    assert (
        tmp_path / "src" / "amazon/Retail.OrderHistory.1.csv"
    ).read_bytes() == before


def test_a_file_it_cannot_read_is_skipped_and_counted_not_a_crash(tmp_path):
    got, out = mirror_of(
        tmp_path, {"good.csv": SAMPLE, "bad.csv": b"\xff\xfe\x00 not csv"}
    )
    assert got.returncode == 0, got.stderr
    assert "wrote 1 files" in got.stdout and "skipped 1" in got.stdout
    assert (out / "good.csv.txt").is_file() and not (out / "bad.csv.txt").exists()


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"notes.md": b"nothing here\n"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    (tmp_path / "src").mkdir()
    for to in (tmp_path / "src" / "m", tmp_path):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    assert (
        run(
            "mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m")
        ).returncode
        == 2
    )


def test_a_bad_command_line_says_how_to_run_it():
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", "a"],
        ["nope", "--from", "a", "--to", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "orders.py" in got.stderr
