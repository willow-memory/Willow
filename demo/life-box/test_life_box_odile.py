"""The life box: Odile's made-up life laid as the binder at her own today, her
own questions (lifted unchanged from STRIP.md's first pass) asked, and the
answers she seals with the key made for her, held to her answer key. Her
files are plain text, csv and one calendar, so she is opened with --read (her
calendar is the one file only a reader turns into dated lines) and --piles
(a folder per matter). The traps PLANTED.md sets are never sealed."""

from __future__ import annotations

import json
import os
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
ODILE = ROOT / "demo" / "odile"
KEY = json.loads((HERE / "odile.json").read_text(encoding="utf-8"))
UNANSWERED = {1, 2, 5, 6, 8, 9, 11}


def run(*argv, env=None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(LB), *map(str, argv)], capture_output=True, text=True, check=False, env=env)  # fmt: skip


def lay(table: Path, *opts, env=None) -> dict:
    opened = run("open", "--who", "odile", "--table", table, *opts, env=env)
    assert opened.returncode == 0, opened.stderr
    week = run("week", "--table", table, env=env)
    asked = run("ask", "--table", table, env=env)
    decided = run("decide", "--table", table, env=env)
    recap = run("recap", "--table", table, env=env)
    return {"table": table, "open": opened, "week": week, "ask": asked, "decide": decided, "recap": recap}  # fmt: skip


@pytest.fixture(scope="module")
def odile(tmp_path_factory):
    return lay(tmp_path_factory.mktemp("life") / "odile", "--read", "--piles")


@pytest.fixture(scope="module")
def one_box(tmp_path_factory):
    return lay(tmp_path_factory.mktemp("life") / "odile", "--read")


@pytest.fixture(scope="module")
def no_pypdf(tmp_path_factory):
    """pdf is a deps add-on: she has no scan, but the box must not need pypdf."""
    block = tmp_path_factory.mktemp("nopypdf")
    (block / "pypdf").mkdir()
    (block / "pypdf" / "__init__.py").write_text('raise ModuleNotFoundError("No module named \'pypdf\'")\n')  # fmt: skip
    env = {**os.environ, "PYTHONPATH": str(block)}
    return lay(tmp_path_factory.mktemp("life") / "odile", "--read", "--piles", env=env)


def answers(recap: str) -> dict[int, dict[str, list[str]]]:
    out, q = {}, None
    for line in recap.splitlines():
        m = re.match(r"^\s*(\d+)\. ", line)
        if m:
            q = int(m.group(1))
            out[q] = {"sealed": [], "declined": []}
        elif q is not None and line.strip().startswith(("sealed", "declined")):
            verb, where = line.split(None, 1)  # a file name can hold spaces
            out[q][verb].append(re.sub(r"\s{3}\[[^\]]*\]$", "", where))  # less its pile
    return out


def see_readings(recap: str, q: int) -> list[str]:
    """The `see readings:` lines under question q of an ask or a recap."""
    mine = re.split(rf"^\s*{q}\. ", recap, flags=re.M)[1]
    mine = re.split(r"^\s*\d+\. ", mine, flags=re.M)[0]
    return [x.strip() for x in mine.splitlines() if x.strip().startswith("see readings:")]  # fmt: skip


def strips_first_pass() -> list[str]:
    """The questions in the first pass's table of STRIP.md (its "Asked" column),
    each once, in the order they appear."""
    text = (ODILE / "STRIP.md").read_text(encoding="utf-8")
    first = text.split("## What it found")[1].split("## What the misses")[0]
    found: list[str] = []
    for row in first.splitlines():
        cells = row.split("|")
        if row.startswith("| N") and len(cells) > 3:
            found += [q for q in re.findall(r'"([^"]+)"', cells[2]) if q not in found]
    return found


def test_her_questions_are_lifted_from_strip_unchanged():
    asked = life_box.questions("odile")
    assert len(asked) == 11 and asked == strips_first_pass()
    text = (ODILE / "STRIP.md").read_text(encoding="utf-8")
    for q in asked:
        assert f'"{q}"' in text  # her words, verbatim, in the strip
    assert "unchanged" in (ODILE / "QUESTIONS.md").read_text(encoding="utf-8")


def test_nothing_of_hers_is_frozen_and_she_has_no_words_of_her_own_to_add():
    assert not list(ODILE.rglob("FROZEN.json"))
    for f in ROOT.rglob("FROZEN.json"):
        assert "demo/odile" not in f.read_text(encoding="utf-8")
    # the starter list already says due = next, and her own lines moved nothing
    # on her box, so no odile-words.txt is kept beside her key
    assert not (HERE / "odile-words.txt").exists()


def test_her_life_is_laid_at_her_own_today_with_a_key_made_for_her(odile):
    t, out = odile["table"], odile["open"].stdout
    assert "254 files" in out and "2026-10-22" in out
    assert (
        "calendar: wrote 1 files" in out and "copied: 253 files no reader took" in out
    )
    assert "as 8 piles" in out and "its dates read" not in out
    assert (t / "odile.key").is_file() and (t / "words.txt").stat().st_mode & 0o077 == 0
    first = kernel.read(t / "record" / "record.jsonl")[0][0]
    assert first["ts"].startswith("2026-10-22")
    assert (t / "odile-read" / "calendar.ics.txt").is_file()
    assert not (t / "odile-read" / "calendar.ics").exists()  # read, not raw


def test_her_week_finds_what_is_coming_at_her_today(odile):
    assert odile["week"].returncode in (0, 42), odile["week"].stderr
    coming = (odile["table"] / "week" / "001" / "01-coming-up.txt").read_text()
    assert "calendar.ics.txt:982  2026-10-28  Tune - Benedikt Ybarra" in coming
    assert "Dad - pharmacy refills" in coming and "2026-11-07" in coming


def test_nothing_is_an_answer_until_she_seals_it(odile):
    assert odile["ask"].returncode == 42
    assert "41 answers wait on odile's seal" in odile["ask"].stdout
    before = kernel.read(odile["table"] / "record" / "record.jsonl")[0]
    assert [r for r in before if r["kind"] == "seal"] == []


def test_she_seals_what_her_key_names_and_declines_the_rest(odile):
    assert "sealed 9 answers and declined 32" in odile["decide"].stdout
    assert "4 of 11 questions have an answer odile sealed" in odile["recap"].stdout
    got = answers(odile["recap"].stdout)
    assert {q for q, g in got.items() if g["sealed"]} == {3, 4, 7, 10}
    assert {q for q in range(1, 12)} - {q for q, g in got.items() if g["sealed"]} == UNANSWERED  # fmt: skip
    assert sum(len(g["sealed"]) for g in got.values()) == 9
    assert sum(len(g["declined"]) for g in got.values()) == 32


def test_every_seal_is_from_a_file_her_key_names_for_that_question(odile):
    sealed = life_box.sealed_answers(odile["table"])
    assert sorted(sealed) == [3, 4, 7, 10]
    for q, wheres in sealed.items():
        named = [a["file"] for a in KEY["answers"][str(q)]]
        for where in wheres:
            path = where.rsplit(":", 1)[0]
            assert any(path == f or (f.endswith("/") and path.startswith(f)) for f in named), (q, where)  # fmt: skip


def test_what_her_needs_say_is_sealed(odile):
    got = answers(odile["recap"].stdout)
    # N2: the cardiologist's line, call if more than 2 kg in a week
    assert got[3]["sealed"] == ["dad/cardiology-2026-07-30.txt:8"]
    # N3 and N6, unasked: the county's 180 days, and the van's rider
    assert got[4]["sealed"] == ["mail/2026-03-20-county.txt:12", "memos/2021-05-14_1502.txt:1"]  # fmt: skip
    # N5: the passages holding hive 4's last three inspections, no eggs, no brood
    assert got[7]["sealed"] == ["hives/2026.txt:136", "hives/2026.txt:129"]
    hive = (odile["table"] / "odile-read" / "hives" / "2026.txt").read_text().splitlines()  # fmt: skip
    assert sum("H4: 7 fr bees, eggs none, brood none" in ln for ln in hive[125:]) == 3
    # N7, the one nobody asks: "I'm tired" finds her night memo and what she told Kati
    assert got[10]["sealed"] == [
        "memos/2026-07-21_2208.txt:1",
        "texts/kati.txt:617",
        "texts/kati.txt:604",
        "texts/kati.txt:592",
    ]
    q10 = odile["recap"].stdout.split("10. ")[1].split("11. ")[0]
    assert "[memos]" in q10 and "[texts]" in q10


def test_the_traps_are_never_sealed(odile):
    got = answers(odile["recap"].stdout)
    every_seal = [w for g in got.values() for w in g["sealed"]]
    # T1: the client named Weight is no answer to Dad's weight, nor to "I'm tired"
    assert all("Weight" not in w for w in every_seal)
    assert (
        "tuning/2026.txt:139" in got[10]["declined"]
    )  # Harriet Weight, offered, declined
    assert (
        "dad/care-log.csv:1" in got[3]["declined"]
    )  # the log's first rows, not the rise
    # T2: the 2024 county letter is never sealed (the new one is, for Q4)
    assert not any("2024-04" in w for w in every_seal)
    # T3: Dry Creek's cash order: her memo says it was paid; it is no answer to "invoice not paid"
    assert (
        got[6]["sealed"] == [] and "memos/2023-03-09_2015.txt:1" in got[6]["declined"]
    )
    assert "memos/2023-03-09_2015.txt:1" not in every_seal
    # the van memo answers what she needs to do, but the shopping memo does not
    assert "memos/2026-06-08_1101.txt:1" in got[4]["declined"]


def test_the_questions_nothing_answers_are_said_so(odile):
    got = answers(odile["recap"].stdout)
    recap = odile["recap"].stdout
    for q in UNANSWERED:
        assert got[q]["sealed"] == []
    # "Dad" names her dad/ pile, so Q2 and Q11 ask it "how's doing", "is okay": nothing
    for q in (2, 8, 9, 11):
        assert got[q] == {"sealed": [], "declined": []}
    assert recap.count("nothing in the life holds it") == 4
    # who's due, and the schools, are offered and declined: right files, wrong rows
    assert got[1]["sealed"] == [] and "tuning/2026.txt:190" in got[1]["declined"]
    assert got[5]["sealed"] == [] and "money/invoices/CUSD-PO-2026-103.txt:4" in got[5]["declined"]  # fmt: skip


def test_her_record_holds_every_seal_in_every_pile(odile):
    t = odile["table"]
    sealed = declined = 0
    for p in life_box.piles_of(t):
        box = t / "records" / p["slug"]
        v = subprocess.run([sys.executable, str(ROOT / "kernel.py"), "verify", "--box", str(box)],
                           capture_output=True, text=True, check=False)  # fmt: skip
        assert v.returncode == 0, (p["slug"], v.stdout)
        rows = kernel.read(box / "record.jsonl")[0]
        sealed += [r["kind"] for r in rows].count("seal")
        declined += [r["kind"] for r in rows].count("decline")
    assert (sealed, declined) == (9, 32)


def test_one_box_seals_the_same_needs_but_answers_a_different_four(one_box):
    """Why piles: one box offers 30, seals 7 and answers Q3, Q4, Q7, Q8, but "I'm
    tired" serves her tuning log before her memos, so her night memo and what she
    told Kati are never offered. Her folders are a folder per matter, and as
    piles "I'm tired" finds both; the cost is Q8, where "hives" names the pile
    and leaves "is anything wrong with the", which the hive notes don't say."""
    assert "30 answers wait on odile's seal" in one_box["ask"].stdout
    assert "sealed 7 answers and declined 23" in one_box["decide"].stdout
    assert "4 of 11 questions have an answer odile sealed" in one_box["recap"].stdout
    got = answers(one_box["recap"].stdout)
    assert {q for q, g in got.items() if g["sealed"]} == {3, 4, 7, 8}
    assert got[10]["sealed"] == [] and got[11]["sealed"] == []
    assert (
        got[11]["declined"][0] == "memos/2026-10-09_0045.txt:1"
    )  # her "Okay.", not Dad's


def test_the_box_does_not_need_pypdf(odile, no_pypdf):
    """She has no scan: without pypdf, the same counts and the same seals."""
    assert "pdf: unreachable" in no_pypdf["open"].stdout
    # with pypdf, the pdf reader finds no scan of hers; where this whole run has
    # none, it is unreachable in her normal box too, and what follows still holds
    try:
        import pypdf  # noqa: F401

        has_pypdf = True
    except ModuleNotFoundError:
        has_pypdf = False
    said = "pdf: wrote 0 files" if has_pypdf else "pdf: unreachable"
    assert said in odile["open"].stdout
    for part in ("ask", "decide"):
        assert no_pypdf[part].stdout == odile[part].stdout.replace(str(odile["table"]), str(no_pypdf["table"]))  # fmt: skip
    assert answers(no_pypdf["recap"].stdout) == answers(odile["recap"].stdout)
    # and the same readings beside the same two questions: they read text and a csv
    assert [see_readings(no_pypdf["recap"].stdout, q) for q in (1, 3)] == [see_readings(odile["recap"].stdout, q) for q in (1, 3)] == [[DUE + "tuning/: 7 of 66 headings, as of 2026-10-22"], [WEIGHT, PULSE]]  # fmt: skip


def test_she_has_no_words_of_her_own_so_words_is_refused(odile):
    got = run("words", "--table", odile["table"])
    assert got.returncode == 2 and "has no words of their own" in got.stderr


#: what readings says beside "something that tells me who's due": her tuning
#: log's seven (STRIP.md's second pass), four of them truly due
DUE = (
    "see readings: gone by, nothing written since: "
    "Everett Montaño - Samick console (1999), 2203 Pinon St (Jan 2023); "
    "Ada Kerrigan - Story & Clark console (1984), 983 Cholla St (Jul 2023); "
    "Winifred Marchetti - Steinway K-52 (1981), 1657 Railroad St (Nov 2023); "
    "Renata Lindahl - Chickering upright (1908), 1763 Railroad St (Jun 2026); "
    "Loretta Tremaine - Mason & Hamlin A (1919), 2140 Cholla St (Aug 2026); "
    "Imogen Sandoval - Everett studio (1974), 725 Cholla St (Sep 2026); "
    "Benedikt Ybarra - Wurlitzer console (1971), 904 Pinon St (Oct 2026)  "
)
#: and beside "Dad's weight": Laszlo's weight, 2.5 kg in one week, past the 2 kg line
WEIGHT = (
    "see readings: weight_kg: 75.1 on 2026-10-21, up 1.9 from 73.2 on 2026-10-14; "
    "the most in one week of the last 4: up 2.5, 2026-10-09 to 2026-10-16  "
    "dad/care-log.csv: 430 dated rows, 2025-08-18 to 2026-10-21"
)
PULSE = (
    "see readings: pulse: 64 on 2026-10-21, down 5 from 69 on 2026-10-14; "
    "the most in one week of the last 4: up 14, 2026-09-23 to 2026-09-30  "
    "dad/care-log.csv: 430 dated rows, 2025-08-18 to 2026-10-21"
)


def test_readings_beside_her_questions_say_who_is_due_and_her_fathers_weight(odile, one_box):  # fmt: skip
    """STRIP.md's second pass, in the box: "who's due" gets the seven gone by with
    nothing written since, and "Dad's weight" the 2.5 kg week, in ask and in recap,
    as piles and as one box. Only those two questions are hinted, and the care
    log's other column, the pulse, comes with the weight."""
    for got in (odile, one_box):
        for part in ("ask", "recap"):
            text = got[part].stdout
            assert see_readings(text, 1) == [DUE + "tuning/: 7 of 66 headings, as of 2026-10-22"]  # fmt: skip
            assert see_readings(text, 3) == [WEIGHT, PULSE]
            assert [q for q in range(1, 12) if see_readings(text, q)] == [1, 3]
    kept = sorted(p.name for p in (odile["table"] / "readings").iterdir())
    assert kept == ["01.txt", "03.txt"]  # beside the week, as spent's are kept
    assert (odile["table"] / "readings" / "03.txt").read_text().splitlines() == [WEIGHT, PULSE]  # fmt: skip


def test_a_reading_is_never_proposed_or_sealed(odile, one_box):
    """A hint is a place to look, not a passage a bite served: nothing in a
    proposal, a seal or the record says one, and every proposal still cites a
    passage."""
    for got in (odile, one_box):
        for box in life_box.boxes_of(got["table"]):
            record = (box / "record.jsonl").read_text(encoding="utf-8")
            for said in ("gone by, nothing written", "dated rows", "weight_kg: 75.1", "readings"):  # fmt: skip
                assert said not in record, (box.name, said)
            for f in (box / "proposals").glob("*.json"):
                prop = json.loads(f.read_text(encoding="utf-8"))
                assert life_box.CLAIM.match(prop["claim"]) and len(prop["cites"]) == 1
                for said in ("gone by, nothing written", "dated rows", "see readings"):
                    assert said not in f.read_text(encoding="utf-8"), (f.name, said)


def test_the_readings_bite_serves_what_the_kernels_does_and_writes_its_row(one_box, tmp_path):  # fmt: skip
    """On boxes of her whole life, one made fresh over each (the asked ones hold
    their answers), the bite through readings is the kernel's own: the passages
    served, the row written and the exit code, byte for byte, so a proposal still
    cites the last bite and the kernel still checks it."""
    key = tmp_path / "k" / "odile.key"  # a key made for her, who is made up
    now = life_box.today_of("odile")
    read = one_box["table"] / "odile-read"
    for n, text in enumerate(("something that tells me who's due", "Dad's weight", "I'm tired", "how are the bees")):  # fmt: skip
        for how in ("kernel", "readings"):
            box = tmp_path / f"{how}{n}"
            made = subprocess.run([sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(box), "--pile", str(read),
                                   "--key", str(key), "--words", str(one_box["table"] / "words.txt"), "--now", now],
                                  capture_output=True, text=True, check=False)  # fmt: skip
            assert made.returncode == 0, made.stderr
        plain = subprocess.run([sys.executable, str(ROOT / "kernel.py"), "bite", "--box", str(tmp_path / f"kernel{n}"), "--now", now, text],
                               capture_output=True, text=True, check=False)  # fmt: skip
        more = subprocess.run([sys.executable, str(life_box.READINGS), "bite", "--box", str(tmp_path / f"readings{n}"), "--now", now, text],
                              capture_output=True, text=True, check=False)  # fmt: skip
        served, see = life_box.bite_of(tmp_path / f"readings{n}", now, text)
        # the box that bite_of bit is bitten twice now: compare the first two to the kernel's
        a, b = json.loads(plain.stdout), json.loads(more.stdout)
        assert plain.returncode == more.returncode
        assert a["served"] == b["served"] and a["bite_key"] == b["bite_key"] and a["state"] == b["state"]  # fmt: skip
        rows = [(tmp_path / f"{h}{n}" / "record.jsonl").read_bytes().splitlines() for h in ("kernel", "readings")]  # fmt: skip
        assert (
            rows[0][:2] == rows[1][:2]
        )  # the boot row and the bite row, as the kernel writes them
        assert served == a["served"]  # what bite_of hands on is what the kernel served
        assert bool(see) == (
            n < 2
        )  # hints on the first two of these four, and only there
    for key_file in (tmp_path / "k").glob("*.key"):
        subprocess.run(["shred", "-u", str(key_file)], check=False)


def test_where_readings_cannot_run_the_kernel_bites_it_and_nothing_is_hinted(tmp_path, monkeypatch):  # fmt: skip
    """A box of sources is read where its files are kept, and readings reads it
    the same way. A box that can't be bitten at all, or a readings that fails,
    is bitten by the kernel as before, hinted nothing, and the one line says so."""
    log = tmp_path / "kept" / "tuning"
    log.mkdir(parents=True)
    (log / "2026.txt").write_text("2026-01-02  Ann - upright\n  next: May 2026\n")
    key, now, box = tmp_path / "k" / "who.key", "2026-10-22T09:00:00Z", tmp_path / "box"
    made = subprocess.run([sys.executable, str(ROOT / "kernel.py"), "init", "--box", str(box), "--from", f"tuning={log}",
                           "--key", str(key), "--now", now], capture_output=True, text=True, check=False)  # fmt: skip
    assert made.returncode == 0, made.stderr
    served, see = life_box.bite_of(box, now, "next tuning")
    assert [s["where"] for s in served] == ["tuning/2026.txt:1"]
    assert len(see) == 1 and see[0].startswith("see readings: gone by, nothing written since: Ann - upright (May 2026)")  # fmt: skip
    assert see[0].endswith("tuning/: 1 of 1 headings, as of 2026-10-22")
    gone = tmp_path / "no-such-box"
    assert life_box.bite_of(gone, now, "next tuning")[0] == []
    assert life_box.bite_of(gone, now, "next tuning")[1] == ["see readings: not run on no-such-box: refused: not a kernel box; init first; the kernel bit it alone"]  # fmt: skip
    broken = tmp_path / "broken.py"
    broken.write_text("import sys\nprint('boom', file=sys.stderr)\nsys.exit(1)\n")
    monkeypatch.setattr(life_box, "READINGS", broken)
    served, see = life_box.bite_of(box, now, "next tuning")
    assert [s["where"] for s in served] == [
        "tuning/2026.txt:1"
    ]  # the kernel's, as before
    assert see == ["see readings: not run on box: boom; the kernel bit it alone"]
    for key_file in (tmp_path / "k").glob("*.key"):
        subprocess.run(["shred", "-u", str(key_file)], check=False)
