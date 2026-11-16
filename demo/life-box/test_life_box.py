"""The life box: Teodora's made-up life laid as the binder, her week run at
her own today, her own questions asked, and the answers she seals with the
key made for her, held to her answer key. The traps PLANTED.md sets are
declined, and nothing is an answer before the seal."""

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


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(LB), *map(str, argv)], capture_output=True, text=True, check=False)  # fmt: skip


@pytest.fixture(scope="module")
def teo(tmp_path_factory):
    table = tmp_path_factory.mktemp("life") / "teodora"
    opened = run("open", "--who", "teodora", "--table", table, "--dates", "day-first")
    assert opened.returncode == 0, opened.stderr
    week = run("week", "--table", table)
    asked = run("ask", "--table", table)
    sealed_before = [r for r in kernel.read(table / "record" / "record.jsonl")[0] if r["kind"] == "seal"]  # fmt: skip
    decided = run("decide", "--table", table)
    recap = run("recap", "--table", table)
    return {"table": table, "open": opened, "week": week, "ask": asked, "before": sealed_before, "decide": decided, "recap": recap}  # fmt: skip


def answers(recap: str) -> dict[int, dict[str, list[str]]]:
    out, q = {}, None
    for line in recap.splitlines():
        m = re.match(r"^\s*(\d+)\. ", line)
        if m:
            q = int(m.group(1))
            out[q] = {"sealed": [], "declined": []}
        elif q is not None and line.strip().startswith(("sealed", "declined")):
            verb, where = line.split(None, 1)  # a file name can hold spaces
            # with --piles each line ends with the pile it came from, after three spaces
            out[q][verb].append(re.sub(r"\s{3}\[[^\]]*\]$", "", where))
    return out


def test_her_life_is_laid_at_her_own_today_with_a_key_made_for_her(teo):
    t = teo["table"]
    assert "308 files" in teo["open"].stdout and "2026-10-22" in teo["open"].stdout
    assert "its dates read day-first" in teo["open"].stdout
    assert (t / "teodora.key").is_file() and (
        t / "words.txt"
    ).stat().st_mode & 0o077 == 0
    first = kernel.read(t / "record" / "record.jsonl")[0][0]
    assert first["ts"].startswith("2026-10-22")


def test_her_week_finds_what_is_coming_at_her_today(teo):
    out = teo["week"].stdout
    assert teo["week"].returncode in (0, 42), teo["week"].stderr
    for line in (
        "27/10/2026 [2026-10-27]",
        "SUMMARY:Half term",
        "Payment due: 30/10/2026 [2026-10-30]",
        "Month end",
    ):
        assert line in out, line
    week = (teo["table"] / "week" / "001.md").read_text()
    assert week.count("2026-10-22T09:00:00Z") == 6  # its six steps that take a today
    assert "`{today}` is the person's today" in week  # and its prose, as written


def test_her_week_finds_who_owes_her_what_goes_out_and_what_she_meant_to_do(teo):
    run = teo["table"] / "week" / "001"
    invoices = (run / "06-invoices.txt").read_text()
    for inv, amount in (
        ("INV-0427", "£680.00"),
        ("INV-0431", "£720.00"),
        ("INV-0435", "£740.00"),
    ):
        line = next(ln for ln in invoices.splitlines() if inv in ln)
        assert (
            line.startswith("overdue") and "Bramble & Bean" in line and amount in line
        ), line
    # T2: Hargreaves' August matches a payment only by sum, so it is never counted as paid
    assert (
        "same sum, no invoice named: check these by hand, never counted as paid"
        in invoices
    )
    assert "HPS LTD BACS" in invoices
    assert "Dev Raman: I can do 600 tonight" in (run / "07-debts.txt").read_text()
    subs = (run / "08-subscriptions.txt").read_text()
    assert "holmwood lettings" in subs and "8 subscriptions" in subs
    todo = (run / "09-todo.txt").read_text()
    assert todo.count("recipes/bunica/index.md") == 19  # the recipes not yet typed up
    assert (
        "Turnover (invoiced):            £24962.00"
        in (run / "10-amounts.txt").read_text()
    )


def test_each_question_is_sent_to_the_steps_whose_job_it_is(teo):
    route = json.loads((teo["table"] / "route.json").read_text())
    assert route["2"]["kind"] == "money owed"
    assert {"step": "invoices", "kept": "week/001/06-invoices.txt"} in route["2"][
        "steps"
    ]
    assert route["17"]["kind"] == "where it stands"
    assert {"step": "todo", "kept": "week/001/09-todo.txt"} in route["17"]["steps"]
    assert (
        "3" not in route or route["3"]["steps"] == []
    )  # the wifi password is a thing she wrote down
    recap = teo["recap"].stdout
    q2 = recap.split(" 2. has kirsty paid me yet")[1].split(" 3. ")[0]
    assert "see       invoices: week/001/06-invoices.txt" in q2


def test_her_week_catches_her_cover_and_her_mot_once_her_dates_are_day_first(teo):
    """Her cover ends 03/11/2026 and the MOT 09/11/2026: each reads two ways,
    so only once the box knows her life is written day first can it place
    them. The day-first mirror gives each its ISO form; coming-up and
    renewals then find both."""
    run_ = teo["table"] / "week" / "001"
    coming = (run_ / "01-coming-up.txt").read_text()
    assert "## 2026-11-03" in coming and "PI_schedule_2025-26.txt:8" in coming
    assert "## 2026-11-09" in coming and "car/MOT_2025-11-10.txt:8" in coming
    renewals = (run_ / "02-renewals.txt").read_text()
    assert "2026-11-04  email/2026-10-06_pi-renewal-2026.eml" in renewals
    assert (
        "2026-11-09  car/MOT_2025-11-10.txt:8" in renewals and "2 to come" in renewals
    )
    car = (run_ / "03-car.txt").read_text()
    assert "mot      last 2025-11-10" in car
    assert "2026-11-09" not in car  # the MOT's expiry is not a day a job was done


def test_without_her_date_order_the_box_leaves_those_dates_unread(tmp_path):
    """The same life without --dates: a date that reads two ways is never guessed."""
    table = tmp_path / "as-written"
    assert run("open", "--who", "teodora", "--table", table).returncode == 0
    assert run("week", "--table", table).returncode in (0, 42)
    coming = (table / "week" / "001" / "01-coming-up.txt").read_text()
    assert "27/10/2026" in coming
    assert "03/11/2026" not in coming and "09/11/2026" not in coming


def test_a_date_order_must_be_one_of_the_two(tmp_path):
    got = run(
        "open", "--who", "teodora", "--table", tmp_path / "t", "--dates", "year-first"
    )
    assert got.returncode == 2 and "--dates is day-first or month-first" in got.stderr


def test_nothing_is_an_answer_until_she_seals_it(teo):
    assert (
        teo["ask"].returncode == 42
        and "46 answers wait on teodora's seal" in teo["ask"].stdout
    )  # was 41: Q17 asks two things, and its two parts offer five passages between them
    assert teo["before"] == []


def test_she_seals_what_her_answer_key_names_and_declines_the_rest(teo):
    # 16 sealed as before; 30 declined, not 25: Q17's five (see its test below)
    assert "sealed 16 answers and declined 30" in teo["decide"].stdout
    got = answers(teo["recap"].stdout)
    assert "10 of 20 questions have an answer teodora sealed" in teo["recap"].stdout
    assert got[1]["sealed"] == [
        "car/MOT_2025-11-10.txt:3",
        "car/MOT_2025-11-10.txt:15",
    ]  # its expiry, then its advisories
    assert "car/MOT_2024-11-08.txt:3" in got[1]["declined"]  # last year's
    assert got[18]["sealed"] == ["email/2026-09-20_your-replacement-debit-card-is-on-its-way.eml:13"]  # fmt: skip
    assert (
        "email/2025-10-06_pi-renewal-2025.eml:15" in got[18]["declined"]
    )  # last year's, the decoy
    for q in (2, 6, 15):  # nothing in her life holds the question's words
        assert got[q] == {"sealed": [], "declined": []}
        assert f"{q:>2}. " in teo["recap"].stdout
    assert teo["recap"].stdout.count("nothing in the life holds it") == 3
    # Q17 asks two things ("what was I going to do for ana's wedding and how far along am I"):
    # asked whole nothing held it, asked as each part five passages are offered, and her key
    # names none of them, so all five are declined, and none is sealed
    assert got[17]["sealed"] == [] and len(got[17]["declined"]) == 5
    q17 = teo["recap"].stdout.split("17. ")[1].split("18. ")[0]
    assert '      part 1 "what was I going to do for ana\'s wedding"\n' in q17
    assert '      part 2 "how far along am I"\n' in q17


def test_the_traps_are_declined(teo):
    got = answers(teo["recap"].stdout)
    # T2: the ledger says Hargreaves' August is unpaid; it was paid
    assert got[11]["sealed"] == [] and "work/invoices/invoice_ledger.csv:236" in got[11]["declined"]  # fmt: skip
    # T1: the "refund" email is phishing; it answers nothing
    assert got[12]["sealed"] == [] and all("tax-refund" in w for w in got[12]["declined"])  # fmt: skip


def test_her_record_holds_every_seal(teo):
    t = teo["table"]
    v = subprocess.run([sys.executable, str(ROOT / "kernel.py"), "verify", "--box", str(t / "record")],
                       capture_output=True, text=True, check=False)  # fmt: skip
    assert v.returncode == 0 and "16 sealed" in v.stdout
    rows = kernel.read(t / "record" / "record.jsonl")[0]
    assert [r["kind"] for r in rows].count("seal") == 16
    assert [r["kind"] for r in rows].count("decline") == 30


def test_only_a_made_up_person_with_an_answer_key_is_decided_for(teo, tmp_path):
    table = tmp_path / "hollis"
    assert run("open", "--who", "hollis", "--table", table).returncode == 0
    # every made-up life that has questions now has an answer key (hollis.json
    # too), so the person with none is a name no key sits beside
    (table / "who.txt").write_text("nobody\n")
    got = run("decide", "--table", table)
    assert got.returncode == 2 and "has no answer key" in got.stderr


@pytest.mark.parametrize("argv, says", [
    (("open", "--who", "nobody"), "isn't one of willow's made-up lives"),
    (("open", "--who", "../teodora"), "isn't one of willow's made-up lives"),
    (("week",), "isn't a life box laid by open"),
])  # fmt: skip
def test_what_isnt_a_life_box_is_refused(tmp_path, argv, says):
    got = run(*argv, "--table", tmp_path / "t")
    assert got.returncode == 2 and says in got.stderr


def test_a_command_line_that_isnt_one_is_refused(teo):
    for argv in ((), ("open", "--table", "x"), ("ask",), ("fly", "--table", "x")):
        assert run(*argv).returncode == 2
    assert (
        "is there already"
        in run("open", "--who", "teodora", "--table", teo["table"]).stderr
    )


@pytest.fixture(scope="module")
def bern(tmp_path_factory):
    """Bernadette's life is mail, calendars, chats, notes, spreadsheets, a
    kindle and scans, so it is read through willow's readers first (--read),
    and her dates are day first (Ballarat)."""
    table = tmp_path_factory.mktemp("life") / "bernadette"
    opened = run("open", "--who", "bernadette", "--table", table, "--read", "--dates", "day-first")  # fmt: skip
    assert opened.returncode == 0, opened.stderr
    week = run("week", "--table", table)
    asked = run("ask", "--table", table)
    decided = run("decide", "--table", table)
    recap = run("recap", "--table", table)
    pdf = "pdf: unreachable" not in opened.stdout  # a deps add-on, read where pypdf is
    return {"table": table, "open": opened, "week": week, "ask": asked, "decide": decided, "recap": recap, "pdf": pdf}  # fmt: skip


def test_bernadettes_life_is_read_by_the_readers_before_it_is_laid(bern):
    out = bern["open"].stdout
    for said in ("mail: wrote 83 files", "calendar: wrote 4 files", "notes: wrote 159 files",
                 "office: wrote 6 files", f"copied: {14 if bern['pdf'] else 16} files no reader took"):  # fmt: skip
        assert said in out, said
    assert "2026-10-24" in out and "its dates read day-first" in out
    pile = bern["table"] / "bernadette-day-first"
    assert (
        pile / "Documents" / "Household budget 2026.xlsx.txt"
    ).is_file()  # read, not raw
    assert not (pile / "Documents" / "Household budget 2026.xlsx").exists()


def test_bernadettes_week_finds_her_rego_her_cover_and_her_friend(bern):
    run_ = bern["table"] / "week" / "001"
    renewals = (run_ / "02-renewals.txt").read_text()
    assert "         2026-11-03  Mail/Inbox/2026-10-06 Registration renewal notice" in renewals  # N1  # fmt: skip
    assert "gone by  2025-11-03" in renewals and "1 to come" in renewals  # T2, gone by
    coming = (run_ / "01-coming-up.txt").read_text()
    for day, what in (
        ("2026-10-30", "Mags's birthday"),  # N4
        ("2026-10-31", "TAX DUE (self lodge)"),  # N6
        ("2026-11-03", "Car rego due"),  # N1
        ("2026-11-14", "FINAL NOTICE policy suspension"),  # N3, her cover's last day
    ):
        assert what in coming.split(f"## {day}")[1].split("## ")[0], day
    subs = (run_ / "08-subscriptions.txt").read_text()
    assert (
        "lakeside health premium       412.85  monthly  last 2026-07-28" in subs
    )  # N3: none since July
    assert (
        "ausprime super pension      +3292.34" in subs
    )  # her pension came in, never paid
    assert subs.splitlines()[-1] == "8 subscriptions: about 4596.28 a month, 56727.31 a year; 3 that come in, not counted"  # fmt: skip
    # the card replaced in August is what she meant to do and didn't
    assert "update any recurring payments" in (run_ / "09-todo.txt").read_text()


def test_bernadette_seals_what_her_key_names_and_her_traps_hold(bern):
    # her spelling is read before it is asked (typos, then accents): "jeweler" as
    # "jeweller" and "dermatoligist referal" as "dermatologist referral" now find
    # their passages. The letter is a scan, read only with pypdf: without it, one
    # answer fewer, and one question fewer answered. The kindle clippings now say "highlight"
    # (books.py keeps the kind), so Q17's "highlighted" is held by the clipping: two more
    # offered, both declined (30 declined, not 28), sealed and answered as before. Q14 asks two
    # things and is asked as each: its second part ("how much was my half") offers four more
    # (34 declined), none sealed on one box, where three passages are all the kernel serves and
    # the stone-done email ranks below them (it is sealed from her Mail pile, below).
    sealed, answered = (20, 16) if bern["pdf"] else (19, 15)
    assert f"sealed {sealed} answers and declined 34" in bern["decide"].stdout
    assert f"{answered} of 20 questions have an answer bernadette sealed" in bern["recap"].stdout  # fmt: skip
    got = answers(bern["recap"].stdout)
    # Q17: the clipping that says "highlight" is sealed, and the two other clippings are offered, declined
    assert got[17]["sealed"] == ["Kindle/My Clippings.txt.txt:7"] and len(got[17]["declined"]) == 2  # fmt: skip
    # T2: the budget's estimate and last year's rego are no answer to this year's
    assert got[2]["sealed"] == [] and "Documents/Household budget 2026.xlsx.txt:3" in got[2]["declined"]  # fmt: skip
    # T3: the skin check she cancelled is sealed; no booking is
    assert got[3]["sealed"] == ["Calendar/Home.ics.txt:139"]
    # her referral letter is read only with pypdf; without it, the 5 Nov
    # booking the clinic cancelled is offered in its place, and declined
    third = "Documents/Scans/Referral - Dr Tolley 11-02-2026.pdf.txt:12" if bern["pdf"] else "Calendar/Home.ics.txt:155"  # fmt: skip
    assert third in got[3]["declined"]
    # T5: her granddaughter's birthday, not Aoife Brennan's from bowls
    assert got[8]["sealed"] == ["Calendar/Home.ics.txt:55"]
    # N3: the bank shows July's premium, the last; the final notice says the rest
    assert got[4]["sealed"] == ["Bank/CommBank_SmartAccess_FY2026-27.csv:73",
        "Mail/Inbox/2026-10-22 FINAL NOTICE policy suspension LH-5520913.eml.txt:1"]  # fmt: skip
    # N2, N5: what she promised Siobhán; "tomorrow, promise" was to Gerry
    assert sorted(got[19]["sealed"]) == ["Chats/WhatsApp Chat with Siobhán.txt.txt:138",
        "Mail/Sent/2022-12-12 Happy 17th to our Aoife.eml.txt:10"]  # fmt: skip
    assert "Chats/WhatsApp Chat with Gerry.txt.txt:99" in got[19]["declined"]
    # the right file, the wrong passage: her scone recipe's backlinks, not its recipe
    assert got[12] == {"sealed": [], "declined": ["Notes/Bernie's Vault/Recipes/Scones.md.txt:8",
        "Chats/WhatsApp Chat with Siobhán.txt.txt:103", "Chats/WhatsApp Chat with Siobhán.txt.txt:101"]}  # fmt: skip
    # her spelling, asked as read: the jeweller's quote is sealed (PLANTED.md's
    # jeweller note); the 8 March note beside it is only the day she rang
    assert got[11]["sealed"] == ["Mail/Inbox/2026-03-09 Re enquiry - sapphire ring claws.eml.txt:10",
        "Mail/Inbox/2026-03-09 Re enquiry - sapphire ring claws.eml.txt:1"]  # fmt: skip
    assert got[11]["declined"] == ["Notes/Bernie's Vault/Daily/2026-03-08.md.txt:6"]
    # "dermatoligist referal letter": her referral letter is the scan, sealed
    # where it is read; the note and Dr Rao's page that mention it are declined
    assert got[20]["declined"] == ["Notes/Bernie's Vault/Daily/2026-02-11.md.txt:6", "Notes/Bernie's Vault/Dr Rao.md.txt:3"]  # fmt: skip
    assert got[20]["sealed"] == (["Documents/Scans/Referral - Dr Tolley 11-02-2026.pdf.txt:1"] if bern["pdf"] else [])  # fmt: skip
    # no trap is ever sealed: the key names none of their files
    key = json.loads((HERE / "bernadette.json").read_text())
    for q, g in got.items():
        for w in g["sealed"]:
            assert any(w.startswith(a["file"]) for a in key["answers"][str(q)]), (q, w)
            assert "pending tax refund" not in w and "rental_fy26_draft" not in w
            assert "2025-10-07 Registration" not in w and "Lydiard" not in w
    # PLANTED.md's T3: the cancelled 5 Nov booking is never sealed
    assert "Calendar/Home.ics.txt:155" not in sum(
        (g["sealed"] for g in got.values()), []
    )


def test_a_question_spelt_her_way_is_asked_again_as_read(bern):
    ask = bern["ask"].stdout
    q20 = ask.split("20. dermatoligist referal letter")[1]
    assert '\n      asked as "dermatologist referral letter"\n' in q20
    q11 = ask.split("11. what did the jeweler say")[1].split("12. ")[0]
    assert 'asked as "what did the jeweller say"' in q11
    # the claim still says which question it answers, and what was asked
    claims = [json.loads(p.read_text())["claim"] for p in (bern["table"] / "record" / "proposals").glob("*.json")]  # fmt: skip
    assert any(c.startswith('answers question 20, "dermatoligist referal letter", asked as "dermatologist referral letter", from ') for c in claims)  # fmt: skip
    # recap shows the read-as wording under the question
    recap = bern["recap"].stdout.split("20. dermatoligist referal letter\n")[1]
    assert recap.startswith('      asked as "dermatologist referral letter"\n')


def test_a_question_spelt_as_the_files_spell_it_is_asked_once(bern):
    ask = bern["ask"].stdout
    assert ask.count("asked as") == 2  # Q11 and Q20 only, of her twenty
    assert "12. scone recipe  (a thing you wrote down)\n      asked as" not in ask
    rows = kernel.read(bern["table"] / "record" / "record.jsonl")[0]
    assert (
        [r["kind"] for r in rows].count("bite") == 21
    )  # one bite a question, the read form in place of the typed; Q14 asks two things: two
    claims = [json.loads(p.read_text())["claim"] for p in (bern["table"] / "record" / "proposals").glob("*.json")]  # fmt: skip
    assert any(
        c.startswith('answers question 12, "scone recipe", from ') for c in claims
    )


def test_her_answer_key_holds_her_traps_out():
    key = json.loads((HERE / "bernadette.json").read_text())
    files = {a["file"] for v in key["answers"].values() for a in v}
    assert len(key["answers"]) == 20
    for trap in ("Downloads/rental_fy26_draft.csv", "Mail/Inbox/2026-10-15 ATO You have a pending tax refund of 128460.eml.txt",
                 "Mail/Inbox/2025-10-07 Registration renewal notice SUBARU FORESTER 1XY4KD.eml.txt",
                 "Mail/Inbox/2026-08-20 Appointment confirmation Lydiard Dermatology.eml.txt"):  # fmt: skip
        assert trap not in files, trap


def test_her_answer_key_is_what_planted_md_names():
    key = json.loads((HERE / "teodora.json").read_text())
    planted = (ROOT / "demo" / "teodora" / "PLANTED.md").read_text()
    files = {a["file"].rstrip("/") for v in key["answers"].values() for a in v}
    named = {f for f in files if f in planted or f.split("/")[-1] in planted}
    assert len(key["answers"]) == 20
    assert {"car/MOT_2025-11-10.txt", "email/2026-10-06_pi-renewal-2026.eml", "work/invoices/invoice_ledger.csv"} <= named  # fmt: skip


# ── --piles: a life laid as the person's own piles, a box each, one key ──────


def verifies(box: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "kernel.py"), "verify", "--box", str(box)],
                          capture_output=True, text=True, check=False)  # fmt: skip


def all_boxes(table: Path) -> list[Path]:
    more = sorted((table / "records").iterdir()) if (table / "records").is_dir() else []
    return [table / "record", *more]


def seals(table: Path) -> list[tuple[Path, dict]]:
    """Every seal in every box, with the proposal it sealed."""
    out = []
    for box in all_boxes(table):
        for r in kernel.read(box / "record.jsonl")[0]:
            if r["kind"] == "seal":
                prop = json.loads(
                    (box / "proposals" / f"{r['subject'][9:]}.json").read_text()
                )
                out.append((box, prop))
    return out


@pytest.fixture(scope="module")
def bern_piles(tmp_path_factory):
    """Bernadette as her own piles: a folder per matter, her vault walked
    through to its Daily and Recipes."""
    table = tmp_path_factory.mktemp("life") / "bernadette"
    opened = run("open", "--who", "bernadette", "--table", table, "--read", "--dates", "day-first", "--piles")  # fmt: skip
    assert opened.returncode == 0, opened.stderr
    week = run("week", "--table", table)
    asked = run("ask", "--table", table)
    decided = run("decide", "--table", table)
    recap = run("recap", "--table", table)
    pdf = "pdf: unreachable" not in opened.stdout
    return {"table": table, "open": opened, "week": week, "ask": asked, "decide": decided, "recap": recap, "pdf": pdf}  # fmt: skip


def test_bernadette_is_laid_as_her_own_piles_a_box_each_under_one_key(bern_piles):
    t = bern_piles["table"]
    piles = json.loads((t / "piles.json").read_text())
    folders = {p["folder"]: p for p in piles}
    # the vault (Notes/ holds only it) is walked through: its folders are piles, its loose notes one more
    assert "Notes" not in folders and "Notes/Bernie's Vault" in folders
    assert (
        folders["Notes/Bernie's Vault"]["loose"]
        and not folders["Notes/Bernie's Vault/Recipes"]["loose"]
    )
    assert folders["Notes/Bernie's Vault/Recipes"]["files"] == 2 and folders["Notes/Bernie's Vault/Daily"]["files"] == 143  # fmt: skip
    assert folders["Notes/Bernie's Vault"]["files"] == 13
    assert [p["folder"] for p in piles if "/" not in p["folder"]] == [
        "Bank", "Books", "Calendar", "Chats", "Contacts", "Desktop", "Documents", "Downloads", "Family History", "Garden", "Kindle", "Mail"]  # fmt: skip
    assert "Mail/Inbox" not in folders  # a folder holding two folders is one pile
    # every file is in one pile, none twice (two files fewer without pypdf)
    files = 274 if bern_piles["pdf"] else 272
    assert sum(p["files"] for p in piles) == files
    assert f"{files} files" in bern_piles["open"].stdout
    assert "as 15 piles, a box each under the one key" in bern_piles["open"].stdout
    # a box each, and the whole life beside them; one key, not one per box
    assert sorted(b.name for b in (t / "records").iterdir()) == sorted(
        p["slug"] for p in piles
    )
    assert [k.name for k in t.rglob("*.key")] == ["bernadette.key"]
    for box in all_boxes(t):
        v = verifies(box)
        assert v.returncode == 0, (box.name, v.stdout, v.stderr)


def test_bernadette_piles_are_asked_every_box_and_sealed_in_the_box_that_served_them(
    bern_piles,
):
    t = bern_piles["table"]
    # the whole-life box serves the week and the spelling: it is never bitten or proposed in
    whole = {r["kind"] for r in kernel.read(t / "record" / "record.jsonl")[0]}
    assert not whole & {"bite", "proposal", "seal", "decline"}
    for p in json.loads((t / "piles.json").read_text()):
        kinds = [
            r["kind"]
            for r in kernel.read(t / "records" / p["slug"] / "record.jsonl")[0]
        ]
        # every pile hears every question, but the two that name another pile ("scone recipe"
        # names Recipes, "...on the kindle" names Kindle) go to that pile alone
        named = {12: "notes-bernie-s-vault-recipes", 17: "kindle"}
        # and Q14 asks two things, each bitten: one bite more
        assert kinds.count("bite") == 21 - sum(1 for slug in named.values() if slug != p["slug"]), p["slug"]  # fmt: skip
        # a proposal says where it is from in the whole life: the pile's folder, then the file
        for prop in (t / "records" / p["slug"] / "proposals").glob("*.json"):
            where = life_box.CLAIM.match(json.loads(prop.read_text())["claim"]).group(4)
            assert where.startswith(p["folder"] + "/"), (p["slug"], where)
            if p["loose"]:  # a level's own files, not the folders below it
                assert where.count("/") == p["folder"].count("/") + 1
    assert bern_piles["ask"].returncode == 42


def test_the_scone_recipe_is_offered_first_in_its_own_pile_and_she_seals_it(bern_piles):
    """In one big pile `Recipes` is a word every passage under it holds, so
    "scone recipe" tied the recipe with her chat lines and the dated ones won.
    As its own pile the recipe holds "recipe" from its own #recipe tag and
    "scone" from its file name, and is the Recipes pile's first."""
    got = answers(bern_piles["recap"].stdout)
    assert got[12]["sealed"] == ["Notes/Bernie's Vault/Recipes/Scones.md.txt:5"]
    assert "     asked of Notes/Bernie's Vault/Recipes as \"scone\"" in bern_piles["recap"].stdout  # fmt: skip
    # "recipe" names the pile, so the Recipes pile is asked "scone" alone, and no other pile
    # is asked: Chats' "send me your scone recipe" lines are never offered
    q12 = bern_piles["recap"].stdout.split("12. ")[1].split("13. ")[0]
    assert all(ln.endswith("[Notes/Bernie's Vault/Recipes]") for ln in q12.splitlines() if ln.strip().startswith(("sealed", "declined")))  # fmt: skip
    assert not any("Chats" in w for w in got[12]["sealed"] + got[12]["declined"])
    line = next(
        ln for ln in bern_piles["recap"].stdout.splitlines() if "Scones.md.txt:5" in ln
    )
    assert line.endswith(
        "   [Notes/Bernie's Vault/Recipes]"
    )  # the recap names the pile
    assert (
        "Notes/Bernie's Vault/Recipes/Scones.md.txt:5 [Notes/Bernie's Vault/Recipes]"
        in bern_piles["ask"].stdout
    )


def test_bernadette_by_piles_counts(bern_piles):
    # one box: 50 offered, 20 sealed, 30 declined, 16 of 20. Dealt across piles each question
    # offers up to 7, so more is offered and declined; the scone recipe is in, and so now is
    # "the quote about loss i highlighted on the kindle": books.py keeps the kind Kindle
    # wrote, so the clipping holds "highlight" and with "loss" is 2 of the 3 words left
    # once "kindle" has named the pile (it was 1 of 3, and unanswered, before). A question
    # that names a pile is asked of that pile alone, so Q12 and Q17 offer 3 and 1: 81 offered.
    # Q14 asks two things and is asked as each, the question's 7 shared between its parts (4 and
    # 3): five more offered, and the stone-done email ("Your half is EUR 725") is sealed from her
    # Mail pile for part 2, one more sealed: 86 offered, 23 sealed, 63 declined.
    # Without pypdf, the scan is unread: one offered, one declined and one question fewer.
    offered, declined, answered = (86, 63, 17) if bern_piles["pdf"] else (85, 62, 16)
    assert f"{offered} answers wait on bernadette's seal" in bern_piles["ask"].stdout
    assert f"sealed 23 answers and declined {declined}" in bern_piles["decide"].stdout
    assert (
        f"{answered} of 20 questions have an answer bernadette sealed"
        in bern_piles["recap"].stdout
    )
    got = answers(bern_piles["recap"].stdout)
    # Q17: the clipping the key names, offered in the Kindle pile and sealed
    assert got[17] == {"sealed": ["Kindle/My Clippings.txt.txt:7"], "declined": []}
    q17 = bern_piles["recap"].stdout.split("17. ")[1].split("18. ")[0]
    assert '     asked of Kindle as "that quote about loss i highlighted on the"' in q17
    assert "[Kindle]" in q17 and "nothing in the life holds it" not in q17
    # last week's dated answers stay where they were
    assert got[1]["sealed"] == ["Calendar/Home.ics.txt:44"]
    assert got[8]["sealed"] == ["Calendar/Home.ics.txt:55", "Contacts/contacts.vcf.txt:6"]  # fmt: skip
    assert got[3]["sealed"][0] == "Calendar/Home.ics.txt:139"
    assert got[20]["sealed"] == (["Documents/Scans/Referral - Dr Tolley 11-02-2026.pdf.txt:1"] if bern_piles["pdf"] else [])  # fmt: skip


def test_a_question_that_asks_two_things_is_asked_as_each_and_part_two_is_answered(
    bern_piles,
):
    """Q14, "what did colleen say about mam's headstone, how much was my half":
    asked whole it held the 2022 email about the stone and never the one that says
    "Your half is EUR 725", which holds one of its five words. Asked as each part,
    "how much was my half" finds that email in her Mail pile."""
    t = bern_piles["table"]
    got = answers(bern_piles["recap"].stdout)
    stone, done = "Mail/Inbox/2022-03-17 Paddys Day and Mams stone.eml.txt:10", "Mail/Inbox/2024-04-22 Stone done photos.eml.txt:6"  # fmt: skip
    assert got[14]["sealed"] == [
        stone,
        done,
    ]  # the whole question's answer, and part 2's
    q14 = bern_piles["recap"].stdout.split("14. ")[1].split("15. ")[0]
    assert q14.startswith("what did colleen say about mam's headstone, how much was my half\n")  # fmt: skip
    assert '      part 1 "what did colleen say about mam\'s headstone"\n' in q14
    assert '      part 2 "how much was my half"\n' in q14
    # each claim says the full question, so her key (keyed by number) reads it, and its part
    mail = t / "records" / "mail" / "proposals"
    claims = {m.group(4) + ":" + m.group(5): m for m in (life_box.CLAIM.match(json.loads(f.read_text())["claim"]) for f in mail.glob("*.json")) if m.group(1) == "14"}  # fmt: skip
    assert claims[stone].group(2) == claims[done].group(2) == "what did colleen say about mam's headstone, how much was my half"  # fmt: skip
    assert (claims[done].group(8), claims[done].group(9)) == (
        "2",
        "how much was my half",
    )
    assert claims[stone].group(8) == "1" and claims[stone].group(9) == "what did colleen say about mam's headstone"  # fmt: skip
    # part 2's passages are proposed under paths of their own, so part 1's are not replaced
    paths = {m.group(4) + ":" + m.group(5): json.loads(f.read_text())["path"] for f in mail.glob("*.json") if (m := life_box.CLAIM.match(json.loads(f.read_text())["claim"])) and m.group(1) == "14"}  # fmt: skip
    assert paths[done].startswith("answers/q14-p2-") and paths[stone].startswith("answers/q14-p1-")  # fmt: skip
    # a question that asks one thing has no part, in any box: its claim and its recap are as they were
    every = [m for box in all_boxes(t) for f in (box / "proposals").glob("*.json") if (m := life_box.CLAIM.match(json.loads(f.read_text())["claim"])) and m.group(1) != "14"]  # fmt: skip
    assert every and all(m.group(8) is None and m.group(9) is None for m in every)
    assert (
        "      part "
        not in bern_piles["recap"].stdout.split("13. ")[1].split("14. ")[0]
    )
    rows = kernel.read(t / "records" / "mail" / "record.jsonl")[0]
    # two parts in a pile, so two bites there, the second after the first part's proposals
    kinds = [r["kind"] for r in rows]
    assert (
        kinds.count("bite") == 21 - 2
    )  # every question but the two that name another pile
    assert verifies(t / "records" / "mail").returncode == 0


def test_bernadette_by_piles_seals_nothing_her_key_does_not_name_in_any_box(bern_piles):
    t = bern_piles["table"]
    key = json.loads((HERE / "bernadette.json").read_text())
    sealed = seals(t)
    assert len(sealed) == 23  # 22, and Q14's stone-done email
    for box, prop in sealed:
        m = life_box.CLAIM.match(prop["claim"])
        q, where = m.group(1), m.group(4)
        assert any(where == a["file"] and a.get("says", "") in prop["data"] for a in key["answers"][q]), (box.name, q, where)  # fmt: skip
        assert "pending tax refund" not in where and "rental_fy26_draft" not in where
        assert "2025-10-07 Registration" not in where and "Lydiard" not in where
        assert not (
            where == "Calendar/Home.ics.txt" and m.group(5) == "155"
        )  # the cancelled 5 Nov booking
    got = answers(bern_piles["recap"].stdout)
    assert "Calendar/Home.ics.txt:155" in got[3]["declined"]  # offered, and declined
    assert "Calendar/Home.ics.txt:155" not in sum(
        (g["sealed"] for g in got.values()), []
    )


@pytest.fixture(scope="module")
def teo_piles(tmp_path_factory):
    table = tmp_path_factory.mktemp("life") / "teodora"
    opened = run("open", "--who", "teodora", "--table", table, "--dates", "day-first", "--piles")  # fmt: skip
    assert opened.returncode == 0, opened.stderr
    week = run("week", "--table", table)
    asked = run("ask", "--table", table)
    decided = run("decide", "--table", table)
    recap = run("recap", "--table", table)
    return {"table": table, "open": opened, "week": week, "ask": asked, "decide": decided, "recap": recap}  # fmt: skip


def test_teodora_by_piles_keeps_her_week_and_her_traps(teo_piles):
    t = teo_piles["table"]
    piles = json.loads((t / "piles.json").read_text())
    assert [p["slug"] for p in piles] == ["bank", "calendar", "car", "chats", "email", "home", "maisie", "notes", "receipts", "recipes", "study-aat-loose", "work"]  # fmt: skip
    # study/ holds only aat/, which holds only files: walked through, its files one pile
    assert (
        next(p for p in piles if p["slug"] == "study-aat-loose")["name"]
        == "study/aat/."
    )
    assert sum(p["files"] for p in piles) == 308
    assert teo_piles["week"].returncode in (
        0,
        42,
    )  # the week still runs, over the whole-life box
    assert "SUMMARY:Half term" in teo_piles["week"].stdout
    # one box offered 41, sealed 16 and declined 25 for 10 of 20; across piles more is offered
    # (up to 7 a question), the key seals 3 more and one more question is answered (Q14).
    # Q17 asks two things and is asked as each: five more offered, all declined (57, 38)
    assert "57 answers wait on teodora's seal" in teo_piles["ask"].stdout
    assert "sealed 19 answers and declined 38" in teo_piles["decide"].stdout
    assert (
        "11 of 20 questions have an answer teodora sealed" in teo_piles["recap"].stdout
    )
    got = answers(teo_piles["recap"].stdout)
    # T2: the ledger line says Hargreaves' August is unpaid; it is declined. The remittance
    # advice (her key names it) is now offered and sealed, which one box never reached
    assert "work/invoices/invoice_ledger.csv:236" in got[11]["declined"]
    assert got[11]["sealed"] == ["email/2026-09-02_remittance-advice.eml:9"]
    # T1: the "refund" email is phishing and answers nothing
    assert got[12]["sealed"] == [] and all(
        "tax-refund" in w for w in got[12]["declined"]
    )
    # "aat" names the pile (study/aat/): Q14 is asked of it as "which exams have I passed", and
    # progress.md, which says what she has passed, is found again
    assert got[14]["sealed"] == ["study/aat/progress.md:3"]
    assert (
        'asked of study/aat/. as "which exams have I passed"' in teo_piles["ask"].stdout
    )
    assert got[1]["sealed"] == ["car/MOT_2025-11-10.txt:3", "car/MOT_2025-11-10.txt:15"]
    for box, prop in seals(t):
        m = life_box.CLAIM.match(prop["claim"])
        key = json.loads((HERE / "teodora.json").read_text())
        assert any(m.group(4) == a["file"] or (a["file"].endswith("/") and m.group(4).startswith(a["file"])) for a in key["answers"][m.group(1)]), prop["claim"]  # fmt: skip


def test_teodoras_boxes_all_verify_with_one_key(teo_piles):
    t = teo_piles["table"]
    assert [k.name for k in t.rglob("*.key")] == ["teodora.key"]
    for box in all_boxes(t):
        v = verifies(box)
        assert v.returncode == 0, (box.name, v.stdout)
    total = sum(1 for _, _ in seals(t))
    assert total == 19


def test_a_folder_that_holds_only_a_folder_is_walked_through_and_loose_files_are_a_pile(
    tmp_path,
):
    p = tmp_path / "life"
    for rel in ("top.txt", "Wrap/Vault/loose.md", "Wrap/Vault/Daily/a.md", "Wrap/Vault/Recipes/Cakes/b.md",
                "Mail/Inbox/m.eml", "Mail/Sent/s.eml", "Solo/only.txt", "Hollow/Deep/Deeper/z.txt",
                "Empty/.keep", ".hidden/h.txt"):  # fmt: skip
        (p / rel).parent.mkdir(parents=True, exist_ok=True)
        (p / rel).write_text("x\n")
    (p / "Void" / "Hole").mkdir(parents=True)  # a folder of nothing is no pile
    got = life_box.split_piles(p)
    assert [(g["name"], g["loose"]) for g in got] == [
        (".", True),  # the files loose at the top
        (
            "Hollow/Deep/Deeper/.",
            True,
        ),  # Hollow and Deep each hold only a folder: walked through
        ("Mail", False),  # a folder holding two folders is one pile, not walked
        ("Solo", False),
        ("Wrap/Vault/.", True),  # Wrap holds only Vault: the vault's own loose notes
        ("Wrap/Vault/Daily", False),
        (
            "Wrap/Vault/Recipes/Cakes/.",
            True,
        ),  # Recipes holds only Cakes: walked through too
    ]
    assert len({g["slug"] for g in got}) == len(got)


def test_a_word_that_names_a_pile_says_where_to_look_and_is_left_out_of_what_it_is_asked(
    tmp_path,
):
    p = tmp_path / "life"
    for rel in ("top.txt", "Recipes/a.md", "Kindle/My Clippings.txt", "Wrap/Bernie's Vault/loose.md",
                "Wrap/Bernie's Vault/Daily/d.md", "Home/h.txt", "Mail/Inbox/m.eml", "Mail/Sent/s.eml"):  # fmt: skip
        (p / rel).parent.mkdir(parents=True, exist_ok=True)
        (p / rel).write_text("x\n")
    piles = life_box.split_piles(p)
    slug = {g["name"]: g["slug"] for g in piles}
    names = lambda q: life_box.naming(q, piles)  # noqa: E731
    # the name's words, as the kernel splits them, less the common ones; the top level has none
    assert life_box.pile_words(next(g for g in piles if g["name"] == "Wrap/Bernie's Vault/.")) == ["bernie", "vault"]  # fmt: skip
    assert life_box.pile_words(next(g for g in piles if g["name"] == ".")) == []
    # a word naming a pile routes to it, and is left out of what that pile is asked; a stem
    # counts the way the kernel holds a word ("recipe" and "recipes" both name Recipes)
    assert names("scone recipe") == {slug["Recipes"]: "scone"}
    assert names("my recipes for scones") == {slug["Recipes"]: "my for scones"}
    assert names("that quote i highlighted on the kindle") == {slug["Kindle"]: "that quote i highlighted on the"}  # fmt: skip
    # a word naming nothing doesn't, and the top level's loose files are never named
    assert names("when is the pennant final") == {}
    assert names("top loose files") == {}
    assert (
        names("what is in the inbox") == {}
    )  # Mail holds two folders: one pile, named Mail
    assert list(names("my mail")) == [slug["Mail"]]
    # two piles named at once are both asked, each without its own naming words
    assert names("home recipes") == {slug["Home"]: "recipes", slug["Recipes"]: "home"}
    # a loose pile is named for its level's own folder
    assert list(names("bernie vault note")) == [slug["Wrap/Bernie's Vault/."]]
    # a question that is only a pile's name is asked as it is
    assert names("the kindle") == {slug["Kindle"]: "the kindle"}


def test_a_claim_says_a_question_was_asked_of_a_pile_and_old_claims_still_parse():
    old = 'answers question 7, "dermatoligist referal", asked as "dermatologist referral", from Mail/a b.eml:3'
    new = old + ', asked of Notes/Bernie\'s Vault/Recipes as "scone"'
    m, n = life_box.CLAIM.match(old), life_box.CLAIM.match(new)
    assert (m.group(3), m.group(4), m.group(5), m.group(6)) == (
        "dermatologist referral",
        "Mail/a b.eml",
        "3",
        None,
    )
    assert (n.group(4), n.group(5), n.group(6), n.group(7)) == ("Mail/a b.eml", "3", "Notes/Bernie's Vault/Recipes", "scone")  # fmt: skip
    assert (
        life_box.CLAIM.match('answers question 1, "q", from f.txt:1').group(6) is None
    )


def test_a_claim_says_which_part_of_a_question_it_answers_and_old_claims_still_parse():
    whole = "what did colleen say about mam's headstone, how much was my half"
    q = f'answers question 14, "{whole}"'
    part = ', part 2 "how much was my half"'
    old, plain = q + ", from Mail/a b.eml:6", q + ", from Mail/a b.eml:6" + part
    both = q + ', asked as "how much was my half", from Mail/a b.eml:6, asked of Mail as "half"' + part  # fmt: skip
    m, n, b = (life_box.CLAIM.match(c) for c in (old, plain, both))
    assert m and n and b
    # groups 1-7 mean what they did; the part is 8 and 9, and only a part has them
    assert (m.group(1), m.group(4), m.group(5), m.group(8), m.group(9)) == ("14", "Mail/a b.eml", "6", None, None)  # fmt: skip
    assert (n.group(1), n.group(2), n.group(4), n.group(5)) == ("14", whole, "Mail/a b.eml", "6")  # fmt: skip
    assert (n.group(6), n.group(7), n.group(8), n.group(9)) == (None, None, "2", "how much was my half")  # fmt: skip
    assert (b.group(3), b.group(6), b.group(7), b.group(8), b.group(9)) == ("how much was my half", "Mail", "half", "2", "how much was my half")  # fmt: skip


# ── day two: her own words ──────────────────────────────────────────────────
def bites(box: Path) -> list[dict]:
    return [r for r in kernel.read(box / "record.jsonl")[0] if r["kind"] == "bite"]


def day_two(table: Path) -> dict:
    """What `words`, a second ask, `decide` and `recap` do on a table already
    asked and decided once; the record of each box beforehand, to hold the
    later one to."""
    before = {b.name: (b / "record.jsonl").read_bytes() for b in all_boxes(table)}
    old_list = (table / "words.txt").read_bytes()
    words = run("words", "--table", table)
    new_list = (table / "words.txt").read_bytes()
    again = run("words", "--table", table)
    asked = run("ask", "--table", table)
    decided = run("decide", "--table", table)
    recap = run("recap", "--table", table)
    return {"table": table, "before": before, "old_list": old_list, "new_list": new_list, "words": words,
            "again": again, "asked": asked, "decided": decided, "recap": recap}  # fmt: skip


@pytest.fixture(scope="module")
def words_piles(bern_piles):
    """Her piles, asked and decided once (bern_piles), then day two. It goes on
    in the same table, so it is read after the tests that read bern_piles."""
    return {**day_two(bern_piles["table"]), "pdf": bern_piles["pdf"]}


@pytest.fixture(scope="module")
def words_one(bern):
    return {**day_two(bern["table"]), "pdf": bern["pdf"]}


STARTER_TXT = ROOT / "adapters" / "stdlib" / "starter-words" / "words.txt"
NOTICE = (
    "Mail/Inbox/2026-10-06 Registration renewal notice SUBARU FORESTER 1XY4KD.eml.txt"
)
LAST_YEARS = (
    "Mail/Inbox/2025-10-07 Registration renewal notice SUBARU FORESTER 1XY4KD.eml.txt"
)


def test_her_own_words_are_the_starter_list_and_then_hers_kept_to_her(words_piles):
    t, w = words_piles["table"], words_piles
    assert w["words"].returncode == 0, w["words"].stderr
    assert "  financial = eofy, fy\n" in w["words"].stdout and "  rego = registration\n" in w["words"].stdout  # fmt: skip
    starter = STARTER_TXT.read_bytes()
    assert w["old_list"] == starter and w["new_list"].startswith(starter.rstrip(b"\n"))
    hers = (HERE / "bernadette-words.txt").read_bytes()
    assert w["new_list"].endswith(hers) and w["new_list"] != w["old_list"]
    assert (t / "words.txt").stat().st_mode & 0o077 == 0
    alias, why = kernel.parse_words(w["new_list"].decode())
    assert why is None and alias["rego"] == ["registration"] and alias["financial"] == ["eofy", "fy"]  # fmt: skip
    assert set(kernel.parse_words(starter.decode())[0]) <= set(alias)
    # said twice, it changes nothing
    assert w["again"].returncode == 0 and "already holds" in w["again"].stdout
    assert (t / "words.txt").read_bytes() == w["new_list"]


def test_her_file_holds_only_her_lines_each_with_a_comment_saying_whose_file_says_it():
    lines = (HERE / "bernadette-words.txt").read_text().splitlines()
    kept = [ln for ln in lines if ln.strip() and not ln.startswith("#")]
    assert kept == ["rego = registration", "financial = fy, eofy", "electricity = energy, origin"]  # fmt: skip
    text = "\n".join(lines)
    assert "Car rego due" in text and "Registration" in text and "EOFY" in text and "FY" in text  # fmt: skip
    # Q18: her budget's line, "Electricity & gas (Origin)", and her bank's ORIGIN ENERGY
    assert "Electricity & gas (Origin)" in text and "ORIGIN ENERGY" in text
    assert kernel.parse_words(text)[1] is None
    assert not {"rego", "financial", "electricity"} & set(kernel.parse_words(STARTER_TXT.read_text())[0])  # not tuned in  # fmt: skip


def test_every_box_still_verifies_and_holds_every_earlier_row_as_it_was(words_piles):
    t = words_piles["table"]
    assert len(all_boxes(t)) == 16
    for box in all_boxes(t):
        got = verifies(box)
        assert got.returncode == 0, (box.name, got.stdout)
        # every seal and decline stays: the old record is the start of the new
        assert (box / "record.jsonl").read_bytes().startswith(words_piles["before"][box.name]), box.name  # fmt: skip


def test_the_next_bite_names_the_new_list_and_the_earlier_ones_keep_the_old(
    words_piles,
):
    import hashlib

    old = hashlib.sha256(words_piles["old_list"]).hexdigest()
    new = hashlib.sha256(words_piles["new_list"]).hexdigest()
    for box in all_boxes(words_piles["table"]):
        shas = [b["words_sha256"] for b in bites(box)]
        kept = sum(1 for r in words_piles["before"][box.name].split(b"\n") if b'"kind":"bite"' in r)  # fmt: skip
        assert shas[:kept] == [old] * kept and set(shas[kept:]) <= {new}, box.name


def test_asked_again_only_the_open_questions_are_asked(words_piles):
    ask = words_piles["asked"].stdout
    answered = 17 if words_piles["pdf"] else 16
    assert words_piles["asked"].returncode == 42
    assert ask.count("already answered: sealed, ") == answered
    assert f"{answered} questions already have a sealed answer and were not asked again" in ask  # fmt: skip
    q1 = ask.split(" 1. ")[1].split(" 2. ")[0]
    assert "already answered: sealed, Calendar/Home.ics.txt:44" in q1 and "suggested" not in q1  # fmt: skip
    waiting = 5 if words_piles["pdf"] else 4
    assert f"\n{waiting} answers wait on bernadette's seal" in ask


def test_her_rego_is_sealed_from_the_notice_and_last_years_notice_is_declined(
    words_piles,
):
    got = answers(words_piles["recap"].stdout)
    assert got[2]["sealed"] == [NOTICE + ":10"]  # $912.40, this year's
    assert LAST_YEARS + ":10" in got[2]["declined"]  # the trap: last year's, $874.10
    assert "Documents/Household budget 2026.xlsx.txt:3" in got[2]["declined"]  # the budget's estimate  # fmt: skip
    q2 = next(p["data"] for _, p in seals(words_piles["table"]) if p["claim"].startswith('answers question 2,'))  # fmt: skip
    assert "$912.40" in q2


def test_her_rent_is_sealed_from_her_sheet(words_piles):
    got = answers(words_piles["recap"].stdout)
    assert got[6]["sealed"] == ["Documents/Rental unit 2025-26.xlsx.txt:3"]
    q6 = next(p["data"] for _, p in seals(words_piles["table"]) if p["claim"].startswith('answers question 6,'))  # fmt: skip
    assert "21840" in q6


def test_day_two_counts_with_her_piles_and_nothing_untrue_is_sealed(words_piles):
    pdf = words_piles["pdf"]
    declined = 3 if pdf else 2
    assert f"sealed 2 answers and declined {declined}" in words_piles["decided"].stdout
    assert f"{19 if pdf else 18} of 20 questions have an answer bernadette sealed" in words_piles["recap"].stdout  # fmt: skip
    key = json.loads((HERE / "bernadette.json").read_text())
    every = seals(words_piles["table"])
    assert len(every) == 25  # 24, and Q14's stone-done email
    for box, prop in every:
        m = life_box.CLAIM.match(prop["claim"])
        q, where = m.group(1), m.group(4)
        assert any(where == a["file"] and a.get("says", "") in prop["data"] for a in key["answers"][q]), (box.name, q, where)  # fmt: skip
        assert "2025-10-07 Registration" not in where and "rental_fy26_draft" not in where  # fmt: skip
    got = answers(words_piles["recap"].stdout)
    assert "Calendar/Home.ics.txt:155" not in sum(
        (g["sealed"] for g in got.values()), []
    )


def test_on_one_box_the_same_two_answers_are_sealed_and_the_record_holds(words_one):
    w = words_one
    assert w["words"].returncode == 0 and w["asked"].returncode == 42
    pdf = w["pdf"]
    assert f"\n{4 if pdf else 3} answers wait on bernadette's seal" in w["asked"].stdout
    assert f"sealed 2 answers and declined {2 if pdf else 1}" in w["decided"].stdout
    got = answers(w["recap"].stdout)
    assert got[2]["sealed"] == [NOTICE + ":10"]
    assert got[6]["sealed"] == ["Documents/Rental unit 2025-26.xlsx.txt:3"]
    assert LAST_YEARS + ":10" not in sum((g["sealed"] for g in got.values()), [])
    assert f"{18 if pdf else 17} of 20 questions have an answer bernadette sealed" in w["recap"].stdout  # fmt: skip
    box = w["table"] / "record"
    assert verifies(box).returncode == 0
    assert (box / "record.jsonl").read_bytes().startswith(w["before"]["record"])
    assert len(seals(w["table"])) == (22 if pdf else 21)


def test_a_person_with_no_words_of_their_own_is_refused_and_nothing_changes(teo):
    t = teo["table"]
    kept = lambda: {b.name: (b / "record.jsonl").read_bytes() for b in all_boxes(t) if (b / "record.jsonl").is_file()}  # noqa: E731  # fmt: skip
    before, words = kept(), (t / "words.txt").read_bytes()
    got = run("words", "--table", t)
    assert got.returncode == 2 and "teodora has no words of their own" in got.stderr
    assert (t / "words.txt").read_bytes() == words and kept() == before


def test_a_box_that_reads_no_words_list_is_sent_to_later_words(tmp_path):
    table, pile = tmp_path / "t", tmp_path / "t" / "pile"
    pile.mkdir(parents=True)
    (pile / "a.txt").write_text("The registration is due.\n")
    (table / "who.txt").write_text("bernadette\n")
    made = subprocess.run([sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(table / "record"), "--pile", str(pile), "--key", str(table / "k")], capture_output=True)  # fmt: skip
    assert made.returncode == 0
    got = run("words", "--table", table)
    assert got.returncode == 2 and "later-words" in got.stderr
    assert not (table / "words.txt").exists()


# ── a sum is a step's to give: how much did we spend on electricity ─────────
SEE_SPENT = "      see       spent: 1,654.36 in 3 payments; calendar 2026, 2026-01-01 to 2026-10-24 (so far); spent/18.txt\n"  # fmt: skip
THREE = (
    "                2026-01-25     446.06  Bank/CommBank_SmartAccess_FY2025-26.csv:124\n"
    "                2026-04-25     479.80  Bank/CommBank_SmartAccess_FY2025-26.csv:50\n"
    "                2026-07-25     728.50  Bank/CommBank_SmartAccess_FY2026-27.csv:77\n"
)


def q18(recap: str) -> str:
    return recap.split("18. how much did we spend on electricity this year\n")[1].split("19. ")[0]  # fmt: skip


def test_route_sends_how_much_did_we_spend_to_spent_and_to_no_other_question(bern):
    route = json.loads((bern["table"] / "route.json").read_text())
    assert route["18"]["kind"] == "money spent"
    assert [x["step"] for x in route["18"]["steps"]] == ["spent", "amounts", "subscriptions"]  # fmt: skip
    assert (
        route["18"]["steps"][0]["kept"] == "spent/18.txt"
    )  # kept by ask, not by the week
    assert route["18"]["steps"][1]["kept"] == "week/001/10-amounts.txt"
    # only the one question is a sum of spending
    assert [q for q, r in route.items() if any(x["step"] == "spent" for x in r["steps"])] == ["18"]  # fmt: skip
    assert [p.name for p in (bern["table"] / "spent").iterdir()] == ["18.txt"]


def test_on_day_one_her_bank_says_origin_energy_and_spent_finds_nothing_and_says_so(
    bern,
):
    out = q18(bern["recap"].stdout)
    assert "      see       spent: No money-out line in this period holds all of: electricity; calendar 2026, 2026-01-01 to 2026-10-24 (so far); spent/18.txt\n" in out  # fmt: skip
    assert "2026-01-25" not in out  # and no total is made up


def test_on_day_two_her_own_word_adds_up_the_three_bpay_lines_of_this_year(words_one):
    out = q18(words_one["recap"].stdout)
    assert SEE_SPENT + THREE in out
    kept = (words_one["table"] / "spent" / "18.txt").read_text()
    assert kept.splitlines()[:2] == ["spent: electricity (electricity = energy, origin)", "period: calendar 2026, 2026-01-01 to 2026-10-24 (so far)"]  # fmt: skip
    assert kept.splitlines()[-1] == "total: 1,654.36 in 3 payments"
    # the file and line of each is a line of her bank statement that says so
    for day, amount, where in re.findall(r"^ +(\S+) +(\S+)  (\S+:\d+)$", THREE, re.M):
        path, n = where.rsplit(":", 1)
        line = (words_one["table"] / "bernadette-day-first" / path).read_text().splitlines()[int(n) - 1]  # fmt: skip
        assert "ORIGIN ENERGY" in line and f"-{amount}" in line and f"[{day}]" in line
    # the offered passage (her budget) is declined as before; the sum is never a seal
    assert answers(words_one["recap"].stdout)[18] == {"sealed": [], "declined": ["Documents/Household budget 2026.xlsx.txt:3"]}  # fmt: skip


def test_a_sum_is_never_sealed_or_proposed_and_the_record_never_hears_of_it(words_one, words_piles):  # fmt: skip
    for w in (words_one, words_piles):
        for _, prop in seals(w["table"]):
            assert "spent" not in prop["claim"] and "1,654.36" not in prop["data"]
        for box in all_boxes(w["table"]):
            text = (box / "record.jsonl").read_text()
            assert "spent" not in text and "1654.36" not in text
            for p in (box / "proposals").glob("*.json"):
                assert "spent" not in p.read_text() and "1,654.36" not in p.read_text()
        assert [p.name for p in (w["table"] / "spent").iterdir()] == ["18.txt"]


def test_with_her_piles_spent_still_adds_up_the_whole_life(words_piles):
    out = q18(words_piles["recap"].stdout)
    assert SEE_SPENT + THREE in out  # the whole-life box, the path in the whole life
    assert (words_piles["table"] / "spent" / "18.txt").read_text().splitlines()[-1] == "total: 1,654.36 in 3 payments"  # fmt: skip


def test_teodora_has_one_question_routed_to_spent_and_it_finds_nothing_and_says_so(teo):  # fmt: skip
    """Her 10th, "what did we end up paying for the new boiler", is `money spent`
    by "paying for" and sent to spent first. It asks for a sum over a year's
    lines, and she asks for one purchase: spent needs every word of the question
    ("end", "up" and "new" among them) in one money-out line and no line says
    them, so it names the words it could not find, and the amounts and the
    subscriptions listed after it, and her seals, are as they were. Dev's BOILER
    lines are a loan paid back, and the word alone would add them up as 250.00:
    the full question never gets there."""
    route = json.loads((teo["table"] / "route.json").read_text())
    assert [q for q, r in route.items() if any(x["step"] == "spent" for x in r["steps"])] == ["10"]  # fmt: skip
    assert route["10"]["kind"] == "money spent"
    assert [x["step"] for x in route["10"]["steps"]] == ["spent", "amounts", "subscriptions"]  # fmt: skip
    assert [p.name for p in (teo["table"] / "spent").iterdir()] == ["10.txt"]
    assert "No money-out line in this period holds all of: end, up, new, boiler" in (teo["table"] / "spent" / "10.txt").read_text()  # fmt: skip
    assert "      see       spent: No money-out line in this period holds all of: end, up, new, boiler; every date, up to 2026-10-22; spent/10.txt\n" in teo["recap"].stdout  # fmt: skip


def test_recap_shows_a_kept_sum_as_its_total_period_and_each_line_cited(tmp_path):
    (tmp_path / "spent").mkdir()
    (tmp_path / "spent" / "03.txt").write_text(
        "spent: gym\nperiod: every date, up to 2026-10-24\n"
        "2026-01-02  12.00  a b/c d.txt:4  2026-01-02  -12.00  GYM\n"
        "2026-02-02  $1,200.50  e.csv:12  x\n"
        "total: 12.00 in 1 payment (no currency sign)\ntotal: $1,200.50 in 1 payment\n"
        "currencies are never added together\n"
        "  not added, it is dated after 2026-10-24, not spent yet: e.csv:13  later\n"
    )
    got = life_box.sent_to({"steps": [{"step": "spent", "kept": "spent/03.txt"}, {"step": "todo", "kept": ""}]}, tmp_path)  # fmt: skip
    assert (
        got
        == (
            "      see       spent: 12.00 in 1 payment (no currency sign); $1,200.50 in 1 payment; every date, up to 2026-10-24; 1 left out, said in spent/03.txt\n"  # fmt: skip
            "                2026-01-02      12.00  a b/c d.txt:4\n"
            "                2026-02-02  $1,200.50  e.csv:12\n"
            "      see       todo: not in this week\n"
        )
    )
    # nothing kept for it: the step is named, nothing is made up
    assert life_box.sent_to({"steps": [{"step": "spent", "kept": ""}]}, tmp_path) == "      see       spent: not in this week\n"  # fmt: skip
