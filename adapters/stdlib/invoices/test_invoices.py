"""invoices: an invoice is paid only when a line naming its number says so;
a payment that names no invoice is shown to check by hand, never counted."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import invoices  # noqa: E402

KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "invoices.py"
NOW = "2026-10-22T09:00:00Z"
LEDGER = (
    "Invoice,Date,Client,Amount_GBP,Due,Status,Paid_on\n"
    "INV-0001,2026-06-30,Acme Ltd,680.00,2026-07-30,sent,\n"
    "INV-0002,2026-08-31,Hart & Co,520.00,2026-09-30,sent,\n"
    "INV-0003,2026-08-31,Acme Ltd,100.00,2026-09-30,paid,2026-09-10\n"
    "INV-0004,2026-09-30,Fern Ltd,173.25,2026-10-30,sent,\n"
    "INV-0005,2026-09-30,Fern Ltd,99.00,2026-10-15,paid,\n"
    "INV-0006,2026-09-30,Hart & Co,42.00,2026-10-01,sent,\n"
)
BANK = (
    "date,description,amount\n"
    "2026-07-15,HPS LTD BACS,520.00\n"
    "2026-09-02,HPS LTD BACS,520.00\n"
    "2026-09-03,TESCO,-520.00\n"
)


def box(tmp_path: Path, files: dict[str, str]) -> Path:
    pile = tmp_path / "pile"
    for rel, text in files.items():
        (pile / rel).parent.mkdir(parents=True, exist_ok=True)
        (pile / rel).write_text(text)
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), "--now", NOW], check=True, capture_output=True)  # fmt: skip
    return b


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def ask(b: Path, pattern: str = r"INV-\d+") -> subprocess.CompletedProcess:
    return run("--box", str(b), "--id", pattern, "--now", NOW)


def test_overdue_first_then_not_due_and_paid_counted(tmp_path):
    got = ask(box(tmp_path, {"ledger.csv": LEDGER}))
    assert got.returncode == 0, got.stderr
    heads = [
        ln for ln in got.stdout.splitlines() if ln.startswith(("overdue", "not due"))
    ]
    assert heads == [
        "overdue  INV-0001  Acme Ltd  £680.00  due 2026-07-30, 84 days ago",
        "overdue  INV-0002  Hart & Co  £520.00  due 2026-09-30, 22 days ago",
        "overdue  INV-0006  Hart & Co  £42.00  due 2026-10-01, 21 days ago",
        "not due  INV-0004  Fern Ltd  £173.25  due 2026-10-30, in 8 days",
    ]
    assert "         invoice   ledger.csv:2" in got.stdout
    assert got.stdout.splitlines()[-1] == (
        "6 invoices: 2 paid, 3 overdue (£1,242.00), 1 not due (£173.25)."
    )


def test_a_line_naming_the_number_as_paid_pays_it_and_one_saying_owed_does_not(
    tmp_path,
):
    files = {"ledger.csv": LEDGER,
             "mail/2026-10-01_thanks.txt": "Thanks, INV-0001 was paid in full yesterday.\n",
             "mail/2026-10-02_chase.txt": "INV-0002 is still outstanding: was it paid?\n"}  # fmt: skip
    got = ask(box(tmp_path, files))
    assert "INV-0001" not in got.stdout.split("same sum")[0]
    assert "overdue  INV-0002" in got.stdout
    assert "last said mail/2026-10-02_chase.txt:1" in got.stdout


def test_a_payment_naming_no_invoice_is_shown_by_hand_never_counted(tmp_path):
    files = {"ledger.csv": LEDGER, "bank/2026-09.csv": BANK,
             "mail/2026-09-02_remit.eml": "REMITTANCE ADVICE\nAmount: £520.00\nRef: HPS-AUG\n"}  # fmt: skip
    got = ask(box(tmp_path, files))
    assert "overdue  INV-0002" in got.stdout, "never counted as paid"
    hand = got.stdout.split("check these by hand, never counted as paid\n")[1]
    assert (
        "  INV-0002  £520.00  bank/2026-09.csv  2026-09-02  520.00  HPS LTD BACS"
        in hand
    )
    assert "  INV-0002  £520.00  mail/2026-09-02_remit.eml:2  Amount: £520.00" in hand
    assert "2026-07-15" not in hand, (
        "a credit before the invoice was issued is not its payment"
    )
    assert "-520.00" not in hand and "TESCO" not in hand, "money out is no payment"


def test_an_invoice_file_gives_its_sum_due_date_and_client(tmp_path):
    invoice = ("INVOICE INV-0042\n\nBill to: Bramble & Bean Ltd\nInvoice date: 30/06/2026\n"
               "Payment due: 30/07/2026 (30 days)\n\nTotal due: £680.00\n")  # fmt: skip
    got = ask(box(tmp_path, {"inv/INV-0042_bramble.txt": invoice}))
    assert got.stdout.splitlines()[0] == (
        "overdue  INV-0042  Bramble & Bean Ltd  £680.00  due 2026-07-30, 84 days ago"
    )


def test_a_due_date_either_way_round_is_unread_not_guessed(tmp_path):
    invoice = "INVOICE INV-0043\nPayment due: 09/11/2026\nTotal: £10.00\n"
    got = ask(box(tmp_path, {"INV-0043.txt": invoice}))
    assert got.stdout.splitlines()[0] == "not due  INV-0043  £10.00  due date unread"


def test_nothing_numbered_so_is_42_and_bad_patterns_are_refused(tmp_path):
    b = box(tmp_path, {"notes.txt": "Tomatoes want sun.\n"})
    got = ask(b)
    assert got.returncode == 42 and got.stdout.startswith("no invoice in your folder")
    assert ask(b, "INV-(").returncode == 2
    got = ask(b, "x*")
    assert got.returncode == 2 and "matches nothing at all" in got.stderr
    assert run().returncode == 2
    assert run("--box", str(b)).returncode == 2
    assert run("--box", str(tmp_path / "nobox"), "--id", "x").returncode == 2
    got = run("--box", str(b), "--id", "x", "--stray", "y")
    assert got.returncode == 2 and "invoices.py" in got.stderr


def test_money_and_days_are_read_as_written():
    assert invoices.money("£1,045.20") == 1045.20
    assert invoices.money("520.00") == 520.00
    assert invoices.money("about forty") is None
    assert invoices.day("Payment due: 30/07/2026") == "2026-07-30"
    assert invoices.day("09/11/2026") == ""


HOLLIS = (
    "INVOICE INV-2026-011\nDate: 2026-05-30\n\nBill to:\n  Larkfield Theatre, attn: Gil\n\n"
    "  Pitch raise                    $  140.00\n  Regulation                     $  500.00\n\n"
    "  TOTAL DUE                      $  640.00\n\nTerms: Net 30. Checks payable to Hollis.\n"
)


def test_terms_a_client_on_the_next_line_and_a_sum_set_apart_are_read(tmp_path):
    """Net 30 from the invoice's own date is its due date, as written."""
    got = ask(box(tmp_path, {"work/INV-2026-011.txt": HOLLIS}), r"INV-\d{4}-\d{3}")
    assert got.stdout.splitlines()[0] == (
        "overdue  INV-2026-011  Larkfield Theatre, attn: Gil  $640.00  due 2026-06-29, 115 days ago"
    )
    assert got.stdout.splitlines()[-1] == (
        "1 invoices: 0 paid, 1 overdue ($640.00), 0 not due (0.00)."
    )


def test_a_deposit_that_quotes_the_number_pays_it_and_money_out_does_not(tmp_path):
    files = {"work/INV-2026-011.txt": HOLLIS, "work/INV-2026-012.txt": HOLLIS.replace("011", "012"),
             "bank/2026-07.csv": "Date,Description,Amount\n"
                                 "2026-06-01,OPENING BALANCE IN,10.00\n"
                                 "2026-07-01,DEPOSIT LARKFIELD THEATRE REF INV-2026-011,640.00\n"
                                 "2026-07-02,REFUND REF INV-2026-012,-640.00\n"}  # fmt: skip
    got = ask(box(tmp_path, files), r"INV-\d{4}-\d{3}")
    assert "INV-2026-011" not in got.stdout.split("\n\n")[0]
    assert "overdue  INV-2026-012" in got.stdout
    assert got.stdout.splitlines()[-1].startswith("2 invoices: 1 paid, 1 overdue")


def test_an_invoice_due_before_any_statement_is_not_called_overdue(tmp_path):
    files = {"work/INV-2026-011.txt": HOLLIS,
             "bank/2026-09.csv": "Date,Description,Amount\n2026-09-01,SALARY,640.00\n"}  # fmt: skip
    got = ask(box(tmp_path, files), r"INV-\d{4}-\d{3}")
    assert "overdue  INV" not in got.stdout
    assert "check these by hand" not in got.stdout
    assert (
        "due before your first bank statement (2026-09-01), so nothing here can show "
        "them paid: 1 ($640.00), INV-2026-011"
    ) in got.stdout
    assert got.stdout.splitlines()[-1].endswith(", 1 before your statements.")


def test_sums_in_two_currencies_are_added_up_apart():
    assert invoices.total([{"amount": 1.5, "cur": "$"}, {"amount": 2, "cur": "£"},
                           {"amount": 1, "cur": "$"}]) == "$2.50 + £2.00"  # fmt: skip
    assert invoices.total([]) == "0.00"
    assert invoices.currency("amount_gbp") == "£" and invoices.currency("€ 4") == "€"
    assert invoices.money("TOTAL DUE   $  640.00") == 640.00


def test_not_yet_due_is_soonest_first_and_an_unread_date_last(tmp_path):
    ledger = ("Invoice,Client,Amount,Due,Status\n"
              "INV-0007,Late Co,10.00,2026-11-20,sent\n"
              "INV-0008,Soon Co,20.00,2026-10-25,sent\n"
              "INV-0009,Odd Co,30.00,09/11/2026,sent\n")  # fmt: skip
    got = ask(box(tmp_path, {"ledger.csv": ledger}))
    heads = [
        ln.split()[2] for ln in got.stdout.splitlines() if ln.startswith("not due")
    ]
    assert heads == ["INV-0008", "INV-0007", "INV-0009"]
