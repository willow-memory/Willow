"""pii-audit: every number is checked, not guessed; a run passing nothing is
nobody's; the audit never repeats a number; and silence names its limits."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("pii_audit", HERE / "pii_audit.py")
pa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa)
NOW = ["--now", "2026-10-23T00:00:00Z"]

CARD = "4242 4242 4242 4242"  # a well-known Luhn-valid test number
NHS = "9434765919"  # the NHS's own example number
MEDICARE = "2123 45670 1"[:10].replace(" ", "")  # built to its weighted check
TFN = "123456782"  # passes the weighted mod-11 check


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def folder(tmp_path: Path, files: dict) -> Path:
    root = tmp_path / "docs"
    for name, text in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return root


def test_a_card_number_passes_luhn_or_is_nobodys():
    assert pa.kinds_of(CARD) == ["a card number"]
    assert pa.kinds_of("4242-4242-4242-4242") == ["a card number"]
    assert pa.kinds_of("4242 4242 4242 4243") == [], "one digit off fails Luhn"
    assert pa.kinds_of("1242 4242 4242 4242") == [], "no card starts with 1"
    assert pa.luhn("4242424242424242") and not pa.luhn("4242424242424241")


def test_nhs_medicare_and_tfn_need_their_check_and_their_name():
    assert pa.kinds_of(NHS, "NHS number: 9434765919") == ["an NHS number"]
    assert pa.kinds_of(NHS, "ring after 9434765919") == [], (
        "one run in ten passes the check by luck; the audit doesn't flip coins"
    )
    assert pa.kinds_of("9434765918", "NHS 9434765918") == [], "the check still rules"
    assert pa.kinds_of(TFN, "my tax file number") == ["a tax file number"]
    assert pa.kinds_of(TFN, "TFN on the form") == ["a tax file number"]
    assert pa.kinds_of(TFN, "order 123456782") == []
    assert pa.kinds_of("2123456701", "Medicare card") == ["a Medicare number"]
    assert pa.kinds_of("2123456701", "a timestamp") == []
    assert pa.kinds_of("2123456711", "Medicare card") == []


def test_a_run_passing_two_checks_says_both():
    line = "nhs and medicare both named here"
    hits = [r for r in range(2 * 10**9, 2 * 10**9 + 100000)
            if len(pa.kinds_of(str(r), line)) > 1]  # fmt: skip
    assert hits and all(pa.kinds_of(str(r), line) ==
                        ["an NHS number", "a Medicare number"] for r in hits), (
        "when digits satisfy two checks, both kinds are said"
    )  # fmt: skip


def test_shapes_without_checksums_say_so():
    pile = [{"path": "a.md", "line": 1,
             "text": "SSN 123-45-6789 and NI QQ 12 34 56 C\nAB 12 34 56 C ok\n"}]  # fmt: skip
    got = pa.audit(pile)
    kinds = [k for k, *_ in got]
    assert "a Social Security number, by shape" in kinds
    assert ["a National Insurance number, by shape"] == [
        k for k in kinds if "Insurance" in k
    ], "QQ is no NI prefix; AB is"
    assert pa.audit([{"path": "a.md", "line": 1, "text": "SSN 000-45-6789\n"}]) == []


def test_the_audit_never_repeats_the_number(tmp_path):
    root = folder(tmp_path, {"money/orders.csv": f"paid with {CARD} yesterday\n"})
    got = run(str(HERE / "pii_audit.py"), "--from", str(root))
    assert got.returncode == 42
    assert "4242424242424242" not in got.stdout and CARD not in got.stdout
    assert "···· 4242" in got.stdout and "money/orders.csv:1" in got.stdout
    assert got.stdout.splitlines()[-1] == "1 personal number in 1 of 1 files"
    assert got.stdout == run(str(HERE / "pii_audit.py"), "--from", str(root)).stdout


def test_plain_numbers_dates_and_phones_are_nobodys(tmp_path):
    root = folder(tmp_path, {"a.md": (
        "ring 0412 345 678 about invoice 20261027\n"
        "2026-10-04 16:49  Kati: how's Dad?\n"
        "order 123456789012 was £45\ncall 555-0100\n")})  # fmt: skip
    got = run(str(HERE / "pii_audit.py"), "--from", str(root))
    assert got.returncode == 0
    assert "what has no checkable shape, this cannot see" in got.stdout


def test_a_box_names_its_pile_and_refusals(tmp_path):
    pile = folder(tmp_path, {"n.md": f"card on file: {CARD}\n"})
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    got = run(str(HERE / "pii_audit.py"), "--box", str(b))
    assert got.returncode == 42 and "a card number" in got.stdout
    got = run(str(HERE / "pii_audit.py"))
    assert got.returncode == 2 and "pii_audit.py" in got.stderr
    got = run(str(HERE / "pii_audit.py"), "--box", str(b), "--from", str(pile))
    assert got.returncode == 2, "one place, not two"
    got = run(str(HERE / "pii_audit.py"), "--from", str(tmp_path / "gone"))
    assert got.returncode == 2 and "isn't a folder" in got.stderr
