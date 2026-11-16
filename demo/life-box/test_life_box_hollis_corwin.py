"""The life box for Hollis (a piano tuner) and Corwin (an electrician who keeps
a ledger about zero): each made-up life laid once as the binder, its week run
at its own today, its own twenty questions asked, the answers sealed with the
key made for that person and held to their answer key, then their own words
added on day two and the open questions asked again. The traps PLANTED.md
sets are never sealed, and nothing is an answer before the seal.

Each person is laid once (module-scoped fixtures), about forty seconds
apiece; the file runs in about eighty seconds."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

sys.path.insert(0, str(HERE))
import life_box  # noqa: E402

LB = HERE / "life_box.py"
STARTER = ROOT / "adapters" / "stdlib" / "starter-words" / "words.txt"


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(LB), *map(str, argv)], capture_output=True, text=True, check=False)  # fmt: skip


def answers(recap: str) -> dict[int, dict[str, list[str]]]:
    out, q = {}, None
    for line in recap.splitlines():
        m = re.match(r"^\s*(\d+)\. ", line)
        if m:
            q = int(m.group(1))
            out[q] = {"sealed": [], "declined": []}
        elif q is not None and line.strip().startswith(("sealed", "declined")):
            verb, where = line.split(None, 1)  # a file name can hold spaces
            out[q][verb].append(where.strip())
    return out


def decisions(table: Path) -> list[tuple[int, str, str, str, dict]]:
    """Every proposal in the record: (question, file, line, "seal" or
    "decline", the proposal)."""
    box = table / "record"
    rows, _ = kernel.read(box / "record.jsonl")
    verb = {
        r["subject"][9:]: r["kind"] for r in rows if r["kind"] in ("seal", "decline")
    }
    out = []
    for f in sorted((box / "proposals").glob("*.json")):
        prop = json.loads(f.read_text(encoding="utf-8"))
        m = life_box.CLAIM.match(prop["claim"])
        out.append((int(m.group(1)), m.group(4), m.group(5), verb[f.stem], prop))
    return out


def lay(tmp_path_factory, who: str):
    """The whole scenario for one person: open, week, ask, decide, words, ask
    again, decide again, recap. The key made for them is shredded at the end."""
    table = tmp_path_factory.mktemp("life") / who
    opened = run("open", "--who", who, "--table", table)
    assert opened.returncode == 0, opened.stderr
    week = run("week", "--table", table)
    asked = run("ask", "--table", table)
    decided = run("decide", "--table", table)
    recap1 = run("recap", "--table", table)
    words = run("words", "--table", table)
    asked2 = run("ask", "--table", table)
    decided2 = run("decide", "--table", table)
    recap = run("recap", "--table", table)
    got = {"table": table, "open": opened, "week": week, "ask": asked, "decide": decided, "recap1": recap1,
           "words": words, "ask2": asked2, "decide2": decided2, "recap": recap}  # fmt: skip
    yield got
    for key in table.glob("*.key"):
        subprocess.run(["shred", "-u", str(key)], check=False)


@pytest.fixture(scope="module")
def hollis(tmp_path_factory):
    yield from lay(tmp_path_factory, "hollis")


@pytest.fixture(scope="module")
def corwin(tmp_path_factory):
    yield from lay(tmp_path_factory, "corwin")


def key_of(who: str) -> dict:
    return json.loads((HERE / f"{who}.json").read_text(encoding="utf-8"))


def named(key: dict) -> set[str]:
    return {a["file"] for v in key["answers"].values() for a in v}


def sealed_pairs(table: Path) -> set[tuple[int, str]]:
    return {(q, f) for q, f, _, v, _ in decisions(table) if v == "seal"}


def verifies(box: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "kernel.py"), "verify", "--box", str(box)],
                          capture_output=True, text=True, check=False)  # fmt: skip


# ── both: what their lives are, and the options each is laid with ────────────


@pytest.mark.parametrize("who, files", [("hollis", 395), ("corwin", 302)])
def test_the_life_is_plain_files_no_reader_has_anything_to_read(
    hollis, corwin, who, files
):
    # no --read: every file is a .csv, .eml, .ics or .txt the kernel reads as it is
    t = {"hollis": hollis, "corwin": corwin}[who]["table"]
    life = t / who / "life"
    found = [p for p in life.rglob("*") if p.is_file()]
    assert len(found) == files
    assert {p.suffix for p in found} == {".csv", ".eml", ".ics", ".txt"}
    for eml in life.rglob("*.eml"):
        head = eml.read_text(encoding="utf-8").split("\n\n", 1)[0]
        assert "Content-Type: text/plain; charset=utf-8" in head
        assert not re.search(r"Content-Transfer-Encoding: (?!8bit)", head), eml.name
        assert (
            "multipart" not in head.lower()
        )  # no attachment for the mail reader to open
    # laid as one pile, with nothing marked and nothing read first
    assert f"{files} files" in {"hollis": hollis, "corwin": corwin}[who]["open"].stdout
    assert "read:" not in {"hollis": hollis, "corwin": corwin}[who]["open"].stdout
    assert (
        "its dates read" not in {"hollis": hollis, "corwin": corwin}[who]["open"].stdout
    )


def test_hollis_writes_no_date_that_reads_two_ways_so_no_order_is_said(hollis):
    life = hollis["table"] / "hollis" / "life"
    both = re.compile(r"(?<![\d/.])\d{1,2}[/.]\d{1,2}[/.]\d{2,4}(?![\d/])")
    assert [
        p.name
        for p in life.rglob("*.txt")
        if both.search(p.read_text(encoding="utf-8"))
    ] == []
    assert [
        p.name
        for p in life.rglob("*.eml")
        if both.search(p.read_text(encoding="utf-8"))
    ] == []


def test_corwin_writes_month_first_but_the_month_first_mirror_would_leave_out_his_csv(
    corwin, tmp_path
):
    life = corwin["table"] / "corwin" / "life"
    numbered = []
    for p in life.rglob("*.txt"):
        numbered += re.findall(
            r"(?<![\d/])\d{2}/\d{2}/\d{4}(?![\d/])", p.read_text(encoding="utf-8")
        )
    # five numbered dates, all month first: his licence card, its certificates and the CE receipt
    assert sorted(numbered) == [
        "11/14/2026",
        "11/19/2023",
        "11/20/2023",
        "11/30/2026",
        "12/01/2023",
    ]
    # the month-first add-on writes only the .txt/.md/.html it is given, so 302 files become 188:
    # his job logs, bank, catalogue (.csv), mail (.eml) and calendar (.ics) are not in the mirror
    got = subprocess.run([sys.executable, str(ROOT / "adapters/stdlib/month-first/month_first.py"), "mirror",
                          "--from", str(life), "--to", str(tmp_path / "mf")], capture_output=True, text=True, check=False)  # fmt: skip
    assert got.returncode == 0 and "wrote 188 files" in got.stdout
    left = {p.suffix for p in (tmp_path / "mf").rglob("*") if p.is_file()}
    assert left == {".txt"}
    assert not list((tmp_path / "mf").rglob("*.csv.txt")) and not list(
        (tmp_path / "mf").rglob("*.eml.txt")
    )


# ── Hollis ───────────────────────────────────────────────────────────────────


def test_hollis_is_laid_at_his_own_today_with_a_key_made_for_him(hollis):
    t = hollis["table"]
    assert "2026-10-22" in hollis["open"].stdout
    assert (t / "hollis.key").is_file() and (
        t / "words.txt"
    ).stat().st_mode & 0o077 == 0
    assert kernel.read(t / "record" / "record.jsonl")[0][0]["ts"].startswith(
        "2026-10-22"
    )


def test_hollis_week_finds_his_referral_running_out_and_misses_the_theatre_by_the_id_it_is_told(
    hollis,
):
    run_ = hollis["table"] / "week" / "001"
    assert hollis["week"].returncode in (0, 42), hollis["week"].stderr
    # his referral to the hearing centre, valid through 10 November
    assert "2026-11-10" in (run_ / "02-renewals.txt").read_text() and "valid through November 10, 2026" in (run_ / "02-renewals.txt").read_text()  # fmt: skip
    # the week's invoices step is told Teodora's id, INV-\d+, which reads INV-2026 off his INV-2026-011:
    assert "6 invoices: 6 paid, 0 overdue" in (run_ / "06-invoices.txt").read_text()
    # told his own (INV-YYYY-NNN, an existing add-on's flag), it finds what he is owed
    got = subprocess.run([sys.executable, str(ROOT / "adapters/stdlib/invoices/invoices.py"), "--box", str(hollis["table"] / "record"),
                          "--id", r"INV-\d{4}-\d+", "--now", "2026-10-22T09:00:00Z"], capture_output=True, text=True, check=False)  # fmt: skip
    assert (
        "overdue  INV-2026-011  Larkfield Community Theatre  $640.00  due 2026-06-27"
        in got.stdout
    )
    assert "1 overdue ($640.00)" in got.stdout
    # his Q3 estimate is a yearly line whose next date has gone by, which no step calls missed
    subs = (run_ / "08-subscriptions.txt").read_text()
    assert "sep paid conf" in subs and "next about 2026-09-15" in subs


def test_nothing_is_an_answer_until_he_seals_it_and_day_one_has_one_question_finding_nothing(
    hollis,
):
    assert (
        hollis["ask"].returncode == 42
        and "52 answers wait on hollis's seal" in hollis["ask"].stdout
    )
    assert "sealed 12 answers and declined 40" in hollis["decide"].stdout
    assert "7 of 20 questions have an answer hollis sealed" in hollis["recap1"].stdout
    # "who still owes me money": his files say invoice; the starter list reads owe as invoice but not owes
    q7 = hollis["recap1"].stdout.split(" 7. ")[1].split(" 8. ")[0]
    assert "nothing in the life holds it" in q7


def test_his_own_words_are_added_on_day_two_and_the_theatre_is_found(hollis):
    t, w = hollis["table"], hollis["words"]
    assert (
        w.returncode == 0
        and "  money = invoice\n" in w.stdout
        and "  owes = invoice\n" in w.stdout
    )
    starter = STARTER.read_bytes()
    assert (t / "words.txt").read_bytes().startswith(starter.rstrip(b"\n"))
    assert (
        (t / "words.txt")
        .read_bytes()
        .endswith((HERE / "hollis-words.txt").read_bytes())
    )
    assert "3 answers wait on hollis's seal" in hollis["ask2"].stdout
    assert (
        "7 questions already have a sealed answer and were not asked again"
        in hollis["ask2"].stdout
    )
    assert "sealed 2 answers and declined 1" in hollis["decide2"].stdout
    got = answers(hollis["recap"].stdout)
    assert got[7]["sealed"] == ["mail/sent/2026-09-15_invoice_inv_2026_011_108_days.eml:7", "mail/sent/2026-09-15_invoice_inv_2026_011_108_days.eml:1"]  # fmt: skip
    assert "nothing in the life holds it" not in hollis["recap"].stdout
    assert "8 of 20 questions have an answer hollis sealed" in hollis["recap"].stdout


def test_hollis_seals_what_his_key_names_and_the_rest_wait_for_a_better_ask(hollis):
    got = answers(hollis["recap"].stdout)
    assert [q for q, g in got.items() if g["sealed"]] == [
        5,
        7,
        8,
        10,
        12,
        13,
        17,
        20,
    ]
    assert got[5]["sealed"] == [
        "van/service_history.txt:5"
    ]  # the belt: "due at 158,000 mi"
    assert got[8]["sealed"] == ["work/client_notes.txt:26"]  # Aldous Pell
    assert got[10]["sealed"] == ["weiler/restoration_log.txt:10", "mail/inbox/2022-03-08_order_m22_1180_confirmed.eml:7"]  # fmt: skip
    assert got[12]["sealed"] == ["mail/inbox/2026-02-10_your_referral_from_dr_lindqvist.eml:11", "mail/inbox/2026-07-20_we_d_like_to_reschedule_you.eml:7"]  # fmt: skip
    assert got[13]["sealed"] == ["notes/2022-02-26_house_done.txt:1"]
    # Ruth's number is under her name with no word "phone" beside it, and every
    # number in his made-up life is 555-0xxx: "phone = 555" would be tuned to
    # the demo's fiction, not a word he says, so it isn't in his words. The
    # question goes to the people page, as a person's question should.
    assert (
        got[16]["sealed"] == []
        and "see       people:"
        in hollis["recap"].stdout.split("16. ")[1].split("17. ")[0]
    )
    assert got[17]["sealed"] == [
        "calendar/hollis_calendar.ics:1975",
        "messages/sms_nell_2026.txt:97",
    ]
    assert sorted(got[20]["sealed"]) == sorted([
        "mail/sent/2024-05-22_fwd_letter_about_2023.eml:7", "money/taxes/2024-05-20_notice_balance_due.txt:11",
        "money/taxes/2024-07-15_notice_paid_zero.txt:1"])  # fmt: skip
    # the eleven with no sealed answer, and the one thing each is waiting on
    assert [q for q, g in got.items() if not g["sealed"]] == [1, 2, 3, 4, 6, 9, 11, 14, 15, 16, 18, 19]  # fmt: skip
    key = key_of("hollis")
    assert [q for q in ("3", "9", "15", "18") if key["answers"][q] == []] == [
        "3",
        "9",
        "15",
        "18",
    ]  # nothing he would seal
    # question 1: his church row is there, but 41 passages tie and the kernel serves three
    assert (
        got[1]["sealed"] == []
        and "work/tuning_log_2026.csv:182" not in got[1]["declined"]
    )


def test_hollis_traps_are_never_sealed(hollis):
    t = hollis["table"]
    seen = decisions(t)
    sealed = {(q, f) for q, f, _, v, _ in seen if v == "seal"}
    offered = {(q, f) for q, f, _, _, _ in seen}
    # T1: the "URGENT ... past due" email is phishing; it is never even offered
    assert not any("urgent_your_account_is_past_due" in f for _, f in offered)
    # T2: the 2021 house emails were settled in 2022; offered for "the papers", declined
    for f in (
        "mail/sent/2021-04-11_re_the_house.eml",
        "mail/inbox/2021-06-30_re_the_house.eml",
    ):
        assert (13, f) in offered and (13, f) not in sealed
    assert not any("2021" in f and "the_house" in f for _, f in sealed)
    # T3: Aldous Pell's deafness is a client's. It answers "what's his name" (8) and is offered, declined, for "how damp" (15)
    assert {q for q, f in sealed if f == "work/client_notes.txt"} == {8}
    assert not any(
        q == 12 and "client_notes" in f for q, f in offered
    )  # never offered for the ear doctor
    # T4: the 2024 notice was paid. Declined for "did I pay all my taxes" (6); it is what 20 asks for, with its $0.00 follow-up
    for f in (
        "money/taxes/2024-05-20_notice_balance_due.txt",
        "money/taxes/2024-07-15_notice_paid_zero.txt",
    ):
        assert (6, f) in offered and (6, f) not in sealed and (20, f) in sealed
    # T5: the 2023 check-engine light was an O2 sensor, not the belt: offered for "is the van due", declined
    assert (5, "notes/2023-08-02_van_light.txt") in offered and (
        5,
        "notes/2023-08-02_van_light.txt",
    ) not in sealed


def test_every_seal_is_from_a_file_his_key_names_for_that_question(hollis):
    key = key_of("hollis")
    seen = decisions(hollis["table"])
    assert [v for *_, v, _ in seen].count("seal") == 14 and [
        v for *_, v, _ in seen
    ].count("decline") == 41
    for q, f, _, v, prop in seen:
        assert (v == "seal") == life_box.accepted(key, prop), (q, f, v)


def test_his_record_verifies_with_every_seal(hollis):
    got = verifies(hollis["table"] / "record")
    assert got.returncode == 0 and "14 sealed" in got.stdout


def test_hollis_answer_key_names_files_that_are_in_his_life_and_holds_his_traps_out(
    hollis,
):
    key = key_of("hollis")
    life = hollis["table"] / "hollis" / "life"
    assert len(key["answers"]) == 20
    for v in key["answers"].values():
        for a in v:
            path = life / a["file"]
            assert path.is_dir() if a["file"].endswith("/") else path.is_file(), a[
                "file"
            ]
            if a.get("says") and path.is_file():
                assert a["says"] in path.read_text(encoding="utf-8"), a
    files = named(key)
    assert not any("urgent_your_account" in f or "2021-04-10_the_house" in f or "2021-09-14" in f or "van_light" in f for f in files)  # fmt: skip
    assert {
        f
        for q, v in key["answers"].items()
        for a in v
        for f in [a["file"]]
        if "the_house" in f
    } == set()
    assert [
        q
        for q, v in key["answers"].items()
        if any(a["file"] == "work/client_notes.txt" for a in v)
    ] == ["8"]
    assert [
        q
        for q, v in key["answers"].items()
        if any("notice_balance_due" in a["file"] for a in v)
    ] == ["20"]
    planted = (ROOT / "demo" / "hollis" / "PLANTED.md").read_text(encoding="utf-8")
    for f in ("van/service_history.txt", "mail/inbox/2026-08-19_your_dad.eml", "work/invoices/INV-2026-011.txt", "money/taxes/estimates_2026.txt"):  # fmt: skip
        assert f in files and f in planted


def test_hollis_words_file_holds_only_his_lines_each_with_a_comment_naming_his_own_file():
    text = (HERE / "hollis-words.txt").read_text()
    kept = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    assert kept == ["owes = invoice", "money = invoice"]
    assert (
        "mail/sent/2026-09-15_invoice_inv_2026_011_108_days.eml" in text
        and "work/invoices/INV-2026-011.txt" in text
    )
    assert kernel.parse_words(text)[1] is None
    starter = kernel.parse_words(STARTER.read_text())[0]
    assert not {"owes", "money"} & set(starter)  # not tuned in


# ── Corwin ───────────────────────────────────────────────────────────────────


def test_corwin_is_laid_at_his_own_today_with_a_key_made_for_him(corwin):
    t = corwin["table"]
    assert "2026-11-04" in corwin["open"].stdout
    assert (t / "corwin.key").is_file() and (
        t / "words.txt"
    ).stat().st_mode & 0o077 == 0
    assert kernel.read(t / "record" / "record.jsonl")[0][0]["ts"].startswith(
        "2026-11-04"
    )
    # the papers fetch.py would add to sources/ are not in the laid life, so none of his answers rests on one
    assert sorted(p.name for p in (t / "corwin" / "life" / "sources").iterdir()) == [
        "README.txt",
        "catalogue.csv",
    ]


def test_corwin_week_finds_his_licence_running_out_and_misses_his_invoices_by_the_id_it_is_told(
    corwin,
):
    run_ = corwin["table"] / "week" / "001"
    assert corwin["week"].returncode in (0, 42), corwin["week"].stderr
    renewals = (run_ / "02-renewals.txt").read_text()
    assert (
        "2026-11-30  license/license_card_ME-27714.txt:8" in renewals
        and "Expires:     11/30/2026" in renewals
    )
    assert (
        "6 renewals: 1 gone by, 5 to come" in renewals
    )  # the one gone by is the 2023 deficiency, last cycle's
    assert (
        "no invoice in your folder is numbered like INV-\\d+"
        in (run_ / "06-invoices.txt").read_text()
    )
    got = subprocess.run([sys.executable, str(ROOT / "adapters/stdlib/invoices/invoices.py"), "--box", str(corwin["table"] / "record"),
                          "--id", r"TE-\d{4}-\d+", "--now", "2026-11-04T09:00:00Z"], capture_output=True, text=True, check=False)  # fmt: skip
    assert "81 invoices: 77 paid, 0 overdue" in got.stdout
    assert (
        "calendar/corwin_calendar.ics:921" in (run_ / "01-coming-up.txt").read_text()
    )  # the slides, due the 12th
    assert "Hallett contract due" in (run_ / "01-coming-up.txt").read_text()


def test_corwin_day_one_every_question_is_offered_something_and_he_seals_what_his_key_names(
    corwin,
):
    assert (
        corwin["ask"].returncode == 42
        and "55 answers wait on corwin's seal" in corwin["ask"].stdout
    )
    assert "sealed 26 answers and declined 29" in corwin["decide"].stdout
    assert "13 of 20 questions have an answer corwin sealed" in corwin["recap1"].stdout
    assert "nothing in the life holds it" not in corwin["recap1"].stdout


def test_his_own_words_are_added_on_day_two_and_zermelo_and_the_course_are_found(
    corwin,
):
    t, w = corwin["table"], corwin["words"]
    assert (
        w.returncode == 0
        and "  find = found\n" in w.stdout
        and "  open = access\n" in w.stdout
    )
    assert (
        (t / "words.txt")
        .read_bytes()
        .endswith((HERE / "corwin-words.txt").read_bytes())
    )
    assert "4 answers wait on corwin's seal" in corwin["ask2"].stdout
    assert (
        "13 questions already have a sealed answer and were not asked again"
        in corwin["ask2"].stdout
    )
    assert "sealed 3 answers and declined 1" in corwin["decide2"].stdout
    got = answers(corwin["recap"].stdout)
    # 13: "did I ever find zermelo" had been served only the todo that says he hadn't; now the one that says he had
    assert got[13]["sealed"] == [
        "todo/todo_2025-06-09.txt:1",
        "sources/catalogue.csv:14",
    ]
    assert "todo/todo_2024-03-04.txt:1" in got[13]["declined"]
    assert got[7]["sealed"] == ["receipts/2026-03-14_brightwire_ce.txt:1"]
    assert "15 of 20 questions have an answer corwin sealed" in corwin["recap"].stdout


def test_corwin_seals_what_his_key_names_and_five_wait(corwin):
    got = answers(corwin["recap"].stdout)
    assert [q for q, g in got.items() if not g["sealed"]] == [4, 5, 15, 17, 19]
    assert got[2]["sealed"] == ["notes/2026-03-24_batch_6.txt:1", "mail/inbox/2025-11-09_batch_5_l37_l47_rev_3.eml:14"]  # Ottilie's objection, and that he put it off  # fmt: skip
    assert got[3]["sealed"] == [
        "reading_log.txt:28",
        "notes/2025-08-30_dedekind_73.txt:1",
    ]  # Dedekind's, not Frege's
    assert got[6]["sealed"] == ["license/license_card_ME-27714.txt:5", "mail/inbox/2026-10-15_reminder_me_27714_expires_november_30_2026.eml:12"]  # fmt: skip
    assert got[8]["sealed"] == [
        "calendar/corwin_calendar.ics:944",
        "notes/2026-09-28_hallett.txt:1",
    ]
    assert got[16]["sealed"] == ["notes/2024-01-29_dario.txt:1"]
    assert got[20]["sealed"] == [
        "notes/2024-03-10_planck_hash.txt:1",
        "reading_log.txt:8",
    ]
    # 1: his own reading of Planck, written while the PDF was open, not the ledger's L21
    assert got[1]["sealed"] == ["reading_log.txt:12"]
    # 5 and 15 are served, below the three the kernel gives; 17 is a sum; 4 and 19 hold none of his words
    assert got[17]["sealed"] == [] and key_of("corwin")["answers"]["17"] == []


def test_corwin_traps_and_false_lines_are_never_sealed(corwin):
    seen = decisions(corwin["table"])
    sealed = {(q, f) for q, f, _, v, _ in seen if v == "seal"}
    offered = {(q, f) for q, f, _, _, _ in seen}
    # T1: the Planck hash that "didn't match" was the unfinished .part download; the note says so and is what 20 asks for, never 1
    assert (20, "notes/2024-03-10_planck_hash.txt") in sealed and not any(q != 20 and "planck_hash" in f for q, f in sealed)  # fmt: skip
    # T2: Ottilie's doubt about the von Neumann line was answered and withdrawn: batch 3 is offered once, for "still open", declined
    assert (7, "mail/inbox/2025-01-26_batch_3_l08_l12.eml") in offered and not any(
        "batch_3" in f for _, f in sealed
    )
    # T3: the 2023 CE deficiency and the spam about his CE hours are never offered for his licence
    assert not any("2023-11-08_board" in f or "/junk/" in f for _, f in offered)
    # T4: the todo that says "find Zermelo" is offered for 13 and declined
    assert (13, "todo/todo_2024-03-04.txt") in offered and (
        13,
        "todo/todo_2024-03-04.txt",
    ) not in sealed
    # the lines that are wrong in his ledger are never sealed: L47's empty set under Weyl's name, L04's Frege, L21's vacuum
    for _, _, _, v, prop in seen:
        if v == "seal":
            assert (
                "physical empty set" not in prop["data"]
                and "frege-1884" not in prop["data"]
            ), prop["claim"]
            assert "Even the vacuum performs vibrations" not in prop["data"], prop[
                "claim"
            ]


def test_every_corwin_seal_is_from_a_file_his_key_names_for_that_question(corwin):
    key = key_of("corwin")
    seen = decisions(corwin["table"])
    assert [v for *_, v, _ in seen].count("seal") == 29 and [
        v for *_, v, _ in seen
    ].count("decline") == 30
    for q, f, _, v, prop in seen:
        assert (v == "seal") == life_box.accepted(key, prop), (q, f, v)
    got = verifies(corwin["table"] / "record")
    assert got.returncode == 0 and "29 sealed" in got.stdout


def test_corwins_answer_key_names_files_that_are_in_his_life_and_holds_his_traps_out(
    corwin,
):
    key = key_of("corwin")
    life = corwin["table"] / "corwin" / "life"
    assert len(key["answers"]) == 20
    for v in key["answers"].values():
        for a in v:
            path = life / a["file"]
            assert path.is_file(), a["file"]
            if a.get("says"):
                assert a["says"] in path.read_text(encoding="utf-8"), a
    files = named(key)
    for trap in (
        "license/2023-11-08_board_ce_deficiency.txt",
        "todo/todo_2024-03-04.txt",
        "todo/todo_2024-11-25.txt",
        "mail/inbox/2025-01-26_batch_3_l08_l12.eml",
        "mail/inbox/2025-01-30_re_batch_3_l08_l12.eml",
    ):
        assert trap not in files, trap
    # the three lines of his ledger that carry a wrong source are in no answer: L21 (any revision), L04, L47
    for q, v in key["answers"].items():
        for a in v:
            if a["file"].startswith("ledger/"):
                assert a.get("says") in ("Dedekind: ", "Einstein & Stern 1913", "Weyl on Riemann", "zermelo-1908", "SPECULATIVE, mine", "Changes since rev 3", "L24 note", "L51-L55 new"), a  # fmt: skip
    planted = (ROOT / "demo" / "corwin" / "PLANTED.md").read_text(encoding="utf-8")
    for f in ("license/license_card_ME-27714.txt", "mail/inbox/2025-11-09_batch_5_l37_l47_rev_3.eml", "notes/2025-06-03_zenodo.txt", "notes/2024-03-10_planck_hash.txt"):  # fmt: skip
        assert f in files and f in planted


def test_corwins_words_file_holds_only_his_lines_each_with_a_comment_naming_his_own_file():
    text = (HERE / "corwin-words.txt").read_text()
    kept = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    assert kept == ["find = found", "open = access"]
    for own in ("todo/todo_2025-06-09.txt", "todo/todo_2024-11-25.txt", "receipts/2026-03-14_brightwire_ce.txt", "mail/inbox/2026-10-01_your_access_ends_in_44_days.eml"):  # fmt: skip
        assert own in text
    assert kernel.parse_words(text)[1] is None
    assert not {"find", "open"} & set(
        kernel.parse_words(STARTER.read_text())[0]
    )  # not tuned in


@pytest.mark.parametrize("who", ["hollis", "corwin"])
def test_readings_have_nothing_to_say_beside_either_of_them(who, hollis, corwin):
    """Readings' two hints read a dated log and a dated table. Neither life's
    questions are served one (STRIP.md took out "what isn't there" for the noise
    it made on Hollis's piano model numbers), so on both days, in every ask and
    recap, no hint is said, none is kept, and counts and seals are what they
    were without readings."""
    got = {"hollis": hollis, "corwin": corwin}[who]
    for part in ("ask", "recap1", "ask2", "recap"):
        assert "see readings" not in got[part].stdout
    assert not (got["table"] / "readings").exists()
