"""bank: a bank statement as dated lines with monthly totals; hidden files and folders skipped, an unreadable file skipped
and counted, the same bytes twice, originals unchanged, and MIRROR and FOLDER
kept apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "bank.py"
spec = importlib.util.spec_from_file_location("bank", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = b"Date,Description,Amount,Balance\n2024-03-05,ACME PAYROLL,2000.00,3000.00\n2024-03-02,TESCO STORES 3241,-45.20,1000.00\n"


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


def test_a_csv_statement_gives_dated_lines_oldest_first_and_the_months():
    assert mod.convert(SAMPLE) == (
        "2024-03-02  -45.20  TESCO STORES 3241\n2024-03-05  2000.00  ACME PAYROLL\n\n"
        "monthly totals\n2024-03  spent 45.20  received 2000.00  net 1954.80  (2 transactions)\n"
    )


OFX = (
    b"OFXHEADER:100\nDATA:OFXSGML\n\n<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>GBP<BANKACCTFROM><ACCTID>12345678<BANKTRANLIST>"
    b"<STMTTRN><TRNTYPE>DEBIT<DTPOSTED>20240302120000[0:GMT]<TRNAMT>-45.20<FITID>1<NAME>TESCO STORES<MEMO>CARD 3241</STMTTRN>"
    b"<STMTTRN><TRNTYPE>CREDIT<DTPOSTED>20240402<TRNAMT>2000.00<FITID>2<NAME>ACME PAYROLL</STMTTRN>"
    b"</BANKTRANLIST><LEDGERBAL><BALAMT>1000.00</STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
)


def test_an_ofx_statement_in_sgml_gives_the_same_with_name_and_memo_and_no_account_number():
    out = mod.convert(OFX)
    assert out == (
        "2024-03-02  -45.20  TESCO STORES CARD 3241\n2024-04-02  2000.00  ACME PAYROLL\n\n"
        "monthly totals\n2024-03  spent 45.20  received 0.00  net -45.20  (1 transaction)\n"
        "2024-04  spent 0.00  received 2000.00  net 2000.00  (1 transaction)\n"
    )
    assert "12345678" not in out


def test_an_ofx_statement_in_xml_is_read_too():
    xml = b"<OFX><STMTTRN><DTPOSTED>20240302</DTPOSTED><TRNAMT>-3.50</TRNAMT><NAME>COFFEE</NAME></STMTTRN></OFX>"
    assert mod.convert(xml).startswith("2024-03-02  -3.50  COFFEE\n")


def test_money_out_and_money_in_columns_become_signed_amounts():
    for out_col, in_col in (
        ("Debit", "Credit"),
        ("Paid out", "Paid in"),
        ("Money out", "Money in"),
        ("Withdrawals", "Deposits"),
    ):
        csv = f"Date,Description,{out_col},{in_col}\n2024-03-02,Shop,12.50,\n2024-03-03,Pay,,100\n".encode()
        assert mod.convert(csv).splitlines()[:2] == [
            "2024-03-02  -12.50  Shop",
            "2024-03-03  100.00  Pay",
        ], out_col
    both = b"Date,Description,Debit,Credit\n2024-03-02,Refund,-5,\n"
    assert mod.convert(both).splitlines()[0] == "2024-03-02  -5.00  Refund"


def test_amounts_dates_and_brackets():
    a = mod.amount
    assert (
        a("-45.20") == -45.2
        and a("1,204.50") == 1204.5
        and a("£-3") == -3
        and a("(12.00)") == -12
        and a("") is None
        and a("n/a") is None
        and a("nan") is None
        and a(None) is None
    )
    assert (
        mod.iso("2024-03-02") == "2024-03-02"
        and mod.iso("13/04/2024") == "2024-04-13"
        and mod.iso("03/04/2024") == ""
        and mod.iso("") == ""
        and mod.iso(None) == ""
    )


def test_a_date_that_reads_either_way_round_leaves_the_row_undated_and_out_of_the_months():
    csv = b"Date,Description,Amount\n03/04/2024,Ambiguous,-5\n13/04/2024,Clear,-6\n"
    assert (
        mod.convert(csv)
        == "-5.00  Ambiguous\n2024-04-13  -6.00  Clear\n\nmonthly totals\n2024-04  spent 6.00  received 0.00  net -6.00  (1 transaction)\n"
    )


def test_the_order_keeps_the_files_order_for_the_same_day():
    csv = b"Date,Description,Amount\n2024-03-02,Zed,-1\n2024-03-02,Alpha,-2\n2024-03-01,Early,-3\n"
    assert mod.convert(csv).splitlines()[:3] == [
        "2024-03-01  -3.00  Early",
        "2024-03-02  -1.00  Zed",
        "2024-03-02  -2.00  Alpha",
    ]


def test_a_csv_that_is_not_a_statement_is_not_a_result_and_bad_encoding_is_an_error():
    for other in (
        b"",
        b"a,b\n1,2\n",
        b"Date,Description\n2024-03-02,x\n",
        b"Date,Amount\n2024-03-02,5\n",
        b"Description,Amount\nx,5\n",
        b"Date,Description,Amount\n",
        b"Date,Description,Amount\n2024-03-02,,5\n",
        b"Date,Description,Amount\n2024-03-02,x,n/a\n",
        b"<OFX></OFX>",
    ):
        assert mod.convert(other) is None, other
    try:
        mod.convert(b"\xff\xfe\x00 bad")
    except UnicodeDecodeError:
        pass
    else:
        raise AssertionError("bad bytes")


def test_a_csv_that_is_no_statement_is_skipped_and_counted(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"statement.csv": SAMPLE, "march.ofx": OFX, "other.csv": b"a,b\n1,2\n"},
    )
    assert "wrote 2 files" in got.stdout and "skipped 1" in got.stdout


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(tmp_path, {"bank/statement.csv": SAMPLE})
    assert got.returncode == 0, got.stderr
    assert (
        (out / "bank/statement.csv.txt").is_file()
        and "wrote 1 files to" in got.stdout
        and got.stdout.strip().endswith("skipped 0")
    )


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {
            "bank/statement.csv": SAMPLE,
            ".hid/bank/statement.csv": SAMPLE,
            ".bank/statement.csv": SAMPLE,
        },
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["bank/statement.csv.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"bank/statement.csv": SAMPLE})
    before = (tmp_path / "src" / "bank/statement.csv").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "bank/statement.csv.txt").read_bytes() == (
        out / "bank/statement.csv.txt"
    ).read_bytes()
    assert (tmp_path / "src" / "bank/statement.csv").read_bytes() == before


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
        assert got.returncode == 2 and "bank.py" in got.stderr


def test_a_header_is_read_in_any_case():
    """A bank that writes its columns in lower case, as teodora's does
    (date,type,description,reference,amount,balance), or in capitals, is the
    same statement as one written Date,Description,Amount."""
    want = mod.convert(SAMPLE)
    lower = (
        b"date,type,description,reference,amount,balance\n"
        b"2024-03-05,BGC,ACME PAYROLL,PAY,2000.00,3000.00\n"
        b"2024-03-02,DEB,TESCO STORES 3241,,-45.20,1000.00\n"
    )
    upper = b"DATE,DESCRIPTION,AMOUNT\n2024-03-05,ACME PAYROLL,2000.00\n2024-03-02,TESCO STORES 3241,-45.20\n"
    assert mod.convert(lower) == want
    assert mod.convert(upper) == want
    pair = b"Date,Details,paid out,PAID IN\n2024-03-02,TESCO STORES 3241,45.20,\n2024-03-05,ACME PAYROLL,,2000.00\n"
    assert mod.convert(pair) == want


def test_only_a_bracket_on_both_sides_marks_money_out():
    """An accountant writes money out as (45.20); a stray bracket on one side
    is a typo, not a minus sign."""
    assert mod.amount("(45.20)") == -45.20
    assert mod.amount("£(1,045.20)") == -1045.20
    assert mod.amount("45.20)") == 45.20
    assert mod.amount("(45.20") == 45.20
