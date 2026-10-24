"""privacy: personal data and keys withheld from what a question prints, by
shape and checksum, and counted; never what the kernel serves or records."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("privacy", HERE / "privacy.py")
pv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pv)
NOW = ["--now", "2026-10-23T00:00:00Z"]


@pytest.mark.parametrize(
    "text, kind",
    [
        ("call (555) 010-0142 today", "phone"),
        ("call +442079460123 today", "phone"),
        ("call 0113 555 0122 today", "phone"),  # national, from its trunk 0
        ("mobile 07700 900123", "phone"),
        ("freephone 0800 123 456", "phone"),  # ten digits
        ("Northbank sort code 00-00-00", "account"),
        ("pay into account 00012345", "account"),
        ("Account No. 000123456789", "account"),
        ("routing number 011000015", "account"),
        ("write to ana@example.org", "email"),
        ("card 4111 1111 1111 1111", "card"),
        ("card 4111111111111111", "card"),
        ("IBAN GB82 WEST 1234 5698 7654 32", "iban"),
        ("SSN 078-05-1120", "ssn"),
        ("router at 192.0.2.10", "ip"),
        ("token sk-ant-abcdefghijklmnopqrstuvwxyz0123", "key"),
        ("token ghp_abcdefghijklmnopqrstuvwxyz0123456789", "key"),
        ("-----BEGIN PRIVATE KEY-----\nMIIB\n-----END PRIVATE KEY-----", "key"),
    ],
)
def test_each_kind_is_withheld_and_counted(text, kind):
    found = {}
    out = pv.scrub(text, found)
    assert f"[withheld: {kind}]" in out and found == {kind: 1}


@pytest.mark.parametrize(
    "text",
    [
        "order 4111111111111112",  # fails Luhn: an order number, not a card
        "IBAN GB00 WEST 1234 5698 7654 32",  # fails mod-97
        "loopback 127.0.0.1 and 0.0.0.0",
        "version 1.2.3.4.5 of the tuner",
        "met at 7.30 on 12/10",
        "shifts 0900 1200 1730",  # times, too few digits for a phone
        "build 0113 555",  # too few digits for a phone
        "part 011 555 012",  # nine digits: too few for a phone
        "account 2026-10-22 statement",  # a date, not a bank number
        "accounting for 123456 widgets",  # not the label
        "account 1234",  # too short for a bank number
    ],
)
def test_lookalikes_are_left(text):
    found = {}
    assert pv.scrub(text, found) == text and found == {}


def test_a_bank_number_keeps_its_label_so_the_line_still_reads():
    found = {}
    got = pv.scrub("Pay by bank transfer: sort code 00-00-00 account 00012345.", found)
    assert got == (
        "Pay by bank transfer: sort code [withheld: account] account [withheld: account]."
    )
    assert found == {"account": 2}


def test_a_bite_serves_the_same_passages_with_the_data_withheld(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "clients.md").write_text(
        "Harriet Vale tunes in spring: (555) 010-0177, h@example.net\n"
    )
    b = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
                    "--key", str(tmp_path / "k"), *NOW], check=True, capture_output=True)  # fmt: skip
    q = "when does harriet tune"
    got = subprocess.run([sys.executable, str(HERE / "privacy.py"), "bite", "--box", str(b), *NOW, q],
                         capture_output=True, text=True)  # fmt: skip
    plain = subprocess.run([sys.executable, str(KERNEL), "bite", "--box", str(b), *NOW, q],
                           capture_output=True, text=True)  # fmt: skip
    mine, theirs = json.loads(got.stdout), json.loads(plain.stdout)
    assert got.returncode == plain.returncode == 0
    assert [s["id"] for s in mine["served"]] == [s["id"] for s in theirs["served"]]
    assert (
        "010-0177" not in got.stdout and "example.net" not in got.stdout
    )  # not "555": hashes hold it
    assert (
        "010-0177" in plain.stdout
    )  # the kernel itself prints it: that's this add-on's job
    assert mine["withheld"] == {"email": 1, "phone": 1}
    assert "010-0177" not in (b / "record.jsonl").read_text()
