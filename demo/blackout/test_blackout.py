"""blackout: the sources are pinned by address and hash, the contact goes to
sec.gov alone and into no file, and a fetch refuses once the study is frozen."""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch  # noqa: E402

SOURCES = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))


def test_every_source_is_pinned_by_address_and_hash():
    got = SOURCES["sources"]
    assert not SOURCES["failed"] and len(got) == len(fetch.LIST)
    assert {(s["folder"], s["file"], s["url"]) for s in got} == set(fetch.LIST)
    for s in got:
        assert s["url"].startswith("https://") and len(s["sha256"]) == 64
        assert s["bytes"] > 0


def test_the_rules_the_story_asks_about_are_among_them():
    names = {s["file"] for s in SOURCES["sources"]}
    for wanted in ("17-cfr-240.10b5-1.xml", "17-cfr-243.100.xml", "form8-k.pdf"):
        assert wanted in names


def test_no_file_in_this_folder_holds_an_email_address():
    for p in HERE.iterdir():
        if p.is_file() and p.suffix in (".py", ".json", ".md", ".txt"):
            text = p.read_text(encoding="utf-8")
            assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text), p.name


def test_the_contact_goes_to_sec_gov_alone_judged_by_host():
    assert fetch.is_sec("https://www.sec.gov/files/form8-k.pdf")
    assert fetch.is_sec("https://sec.gov/x")
    for other in (
        "https://www.ecfr.gov/api/x?sec.gov",
        "https://sec.gov.evil.example/x",
        "https://notsec.gov/x",
        "http://www.sec.gov/x",
    ):
        assert not fetch.is_sec(other), other
    contact = "someone" + chr(64) + "example.invalid"  # no address is written out here
    assert contact in fetch.agent("https://www.sec.gov/f", contact)
    assert contact not in fetch.agent("https://www.ecfr.gov/f", contact)
    assert "@" not in fetch.agent("https://www.sec.gov/f", None)


def test_check_says_holds_differs_and_missing_offline(tmp_path, capsys):
    s = SOURCES["sources"]
    assert fetch.check(tmp_path) == 1
    assert capsys.readouterr().out.count("missing") == len(s)
    first = tmp_path / s[0]["folder"]
    first.mkdir(parents=True)
    (first / s[0]["file"]).write_bytes(b"not the rule")
    fetch.check(tmp_path)
    assert f"DIFFERS  {s[0]['folder']}/{s[0]['file']}" in capsys.readouterr().out


def test_a_fetch_is_refused_once_the_study_is_frozen(tmp_path, monkeypatch, capsys):
    frozen = HERE / "FROZEN.json"
    if not frozen.exists():
        monkeypatch.setattr(fetch, "HERE", tmp_path)
        (tmp_path / "FROZEN.json").write_text("{}")
    assert fetch.fetch(tmp_path / "pile", None) == 2
    assert "FROZEN.json exists" in capsys.readouterr().out


# ── the piles ────────────────────────────────────────────────────────────────
import make_life  # noqa: E402


def made(tmp_path, monkeypatch, rules=None):
    monkeypatch.setattr(make_life, "LIFE", tmp_path / "life")
    make_life.write(rules)
    return tmp_path / "life"


def test_the_piles_are_the_same_bytes_every_time(tmp_path, monkeypatch):
    life = made(tmp_path, monkeypatch)
    first = {
        p.relative_to(life): p.read_bytes() for p in life.rglob("*") if p.is_file()
    }
    made(tmp_path, monkeypatch)
    again = {
        p.relative_to(life): p.read_bytes() for p in life.rglob("*") if p.is_file()
    }
    assert first == again and len({r.parts[0] for r in first}) == 8


def test_the_planted_lines_are_held(tmp_path, monkeypatch, capsys):
    made(tmp_path, monkeypatch)
    assert make_life.check() == 0
    assert "11/11 planted lines held" in capsys.readouterr().out


def test_only_the_filing_and_the_release_are_in_every_box(tmp_path, monkeypatch):
    life = made(tmp_path, monkeypatch)
    seen: dict[str, set[str]] = {}
    for p in life.rglob("*.txt"):
        box = p.relative_to(life).parts[0]
        for ln in p.read_text(encoding="utf-8").splitlines():
            if len(ln) > 40:
                seen.setdefault(ln, set()).add(box)
    shared = {ln for ln, boxes in seen.items() if len(boxes) > 1}
    public = {
        ln
        for text in make_life.PUBLIC.values()
        for ln in text.splitlines()
        if len(ln) > 40
    }
    assert shared == public and all(len(seen[ln]) == 8 for ln in shared)


def test_the_story_is_in_the_numbers(tmp_path, monkeypatch):
    life = made(tmp_path, monkeypatch)
    sales = (life / "plan/trades/plan-sales-2026-q4.txt").read_text()
    sold = [ln.split()[0] for ln in sales.splitlines() if ln.startswith("E-")]
    roster = (life / "steward/roster/seniority-list.txt").read_text()
    dept = {ln.split()[0]: ln for ln in roster.splitlines() if ln.startswith("E-")}
    assert len(sold) == 11
    # nine are on the melt shop's or the rolling mill's list, one is a parts
    # clerk, and one (the plant manager) is on no union list at all
    assert sum(("melt shop" in dept.get(e, "")) or ("rolling mill" in dept.get(e, ""))
               for e in sold) == 9  # fmt: skip
    assert [e for e in sold if e not in dept and e != "E-0007"] == []
    # the window moved: 14 days before 2026-11-05 is 10-22, 7 days is 10-29
    from datetime import date, timedelta

    release = date(2026, 11, 5)
    assert release - timedelta(14) == date(2026, 10, 22)
    assert release - timedelta(7) == date(2026, 10, 29)
    assert all(date(2026, 10, 22) <= date.fromisoformat(ln.split()[1]) < date(2026, 10, 29)
               for ln in sales.splitlines() if ln.startswith("E-"))  # fmt: skip


def test_the_rules_are_mirrored_into_every_box_only_when_asked(tmp_path, monkeypatch):
    pile = tmp_path / "rules-pile" / "ecfr"
    pile.mkdir(parents=True)
    (pile / "17-cfr-243.100.xml").write_text(
        "<DIV><HEAD>A rule &amp; its words</HEAD></DIV>"
    )
    plain = made(tmp_path, monkeypatch)
    assert not list(plain.rglob("rules"))
    ruled = made(tmp_path, monkeypatch, tmp_path / "rules-pile")
    got = [ruled / b / "rules/17-cfr-243.100.txt" for b in make_life.BOXES]
    assert all(p.read_text() == "A rule & its words\n" for p in got)


# ── the scene ────────────────────────────────────────────────────────────────
import subprocess  # noqa: E402

import pytest  # noqa: E402


def py(*argv, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *map(str, argv)], capture_output=True, text=True,
                          cwd=cwd)  # fmt: skip


@pytest.fixture(scope="module")
def played(tmp_path_factory) -> dict:
    tmp = tmp_path_factory.mktemp("blackout")
    shutil.copy(HERE / "make_life.py", tmp / "make_life.py")
    assert py(tmp / "make_life.py", cwd=tmp).returncode == 0
    to = tmp / "scene"
    got = py(HERE / "scene.py", "run", "--life", tmp / "life", "--to", to)
    return {"got": got, "doc": json.loads((to / "scene.json").read_text()), "tmp": tmp}


def test_the_scene_plays_as_told(played):
    assert played["got"].returncode == 0, played["got"].stdout + played["got"].stderr
    assert played["doc"]["wrong"] == []
    assert {v["state"] for v in played["doc"]["rules"].values()} == {"pass"}


def test_the_stack_arrives_with_two_signatures_and_the_auditor_declines(played):
    out = played["got"].stdout
    for who in ("trainee", "ir", "floor", "plan", "steward", "audit"):
        assert (
            f"{who:10} receives it: 2 signatures, every pin the same code here" in out
        )
    assert played["doc"]["ran"]["audit"] == {"taken": False}
    assert all(v["held"] for v in played["doc"]["boxes"].values())


def test_each_box_seals_what_its_owner_sealed_and_audit_seals_nothing(played):
    seals = {b: v["seals"] for b, v in played["doc"]["boxes"].items()}
    assert seals == {"trainee": 3, "compliance": 2, "legal": 3, "ir": 2, "floor": 3,
                     "plan": 2, "steward": 2, "audit": 0}  # fmt: skip


def test_fixity_names_the_edited_key_and_only_that(played):
    ran = played["doc"]["ran"]
    assert any(
        "quiz-key" in ln and ln.startswith("edited")
        for ln in ran["compliance"]["flagged"]
    )
    assert all(
        r["flagged"] == [] for b, r in ran.items() if r["taken"] and b != "compliance"
    )
    assert ran["ir"]["first"] == "2026-10-27"
    assert {ran[b]["first"] for b in ("trainee", "floor", "plan", "steward")} == {
        "2026-11-05"
    }


def test_audit_sees_the_two_clashes_no_one_box_could(played):
    clash = played["doc"]["found"]["clash"]
    assert sorted(tuple(sorted(c["values"])) for c in clash) == [
        ("14 days", "7 days"), ("28 percent", "33 percent")]  # fmt: skip
    assert all(len(set(c["senders"])) == 2 for c in clash)
    assert played["doc"]["found"]["join"] == {"melt shop": 7, "rolling mill": 2,
                                              "plant services": 1, "on no list": 1}  # fmt: skip
    assert set(played["doc"]["found"]["witness"].values()) == {"holds"}


def test_the_scene_edits_its_own_copy_and_never_the_repo(played):
    edited = played["tmp"] / "scene/_pile/compliance/course/quiz-key.txt"
    assert "4. 7 days." in edited.read_text()
    assert "4. 14 days." in make_life.FILES["compliance/course/quiz-key.txt"]


def test_the_scene_refuses_a_folder_that_is_there(played):
    got = py(HERE / "scene.py", "run", "--life", played["tmp"] / "life",
             "--to", played["tmp"] / "scene")  # fmt: skip
    assert got.returncode == 2


def study_rows(box: Path) -> list[dict]:
    rows = [json.loads(x) for x in (box / "record.jsonl").read_text().splitlines()]
    return [r for r in rows if r["kind"] == "verdict"]


def test_a_real_run_scores_every_rule_as_a_kernel_row(played, tmp_path):
    box = tmp_path / "study"
    got = py(HERE / "scene.py", "run", "--life", played["tmp"] / "life", "--to",
             tmp_path / "again", "--box", box)  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
    rows = study_rows(box)
    assert [r["gate"] for r in rows] == [f"blackout:R{i}" for i in range(1, 8)]
    assert {r["state"] for r in rows} == {"pass"}
    assert py(HERE.parents[1] / "kernel.py", "verify", "--box", box).returncode == 0


def test_the_dry_run_wires_every_step_and_scores_nothing(played, tmp_path):
    box = tmp_path / "study"
    got = py(HERE / "scene.py", "run", "--life", played["tmp"] / "life", "--to",
             tmp_path / "dry", "--dry", "--box", box)  # fmt: skip
    assert got.returncode == 0, got.stdout + got.stderr
    rows = study_rows(box)
    assert [r["gate"] for r in rows] == [f"blackout:dry:R{i}" for i in range(1, 8)]
    assert {r["state"] for r in rows} == {"wired"}
    doc = json.loads((tmp_path / "dry" / "scene.json").read_text())
    assert doc["dry"] is True and all(b["held"] for b in doc["boxes"].values())
    # every answer is nonsense: no real line of any pile was sealed or sent
    assert all(
        "nonsense answer" in a["data"] for b in doc["boxes"].values() for a in b["said"]
    )


def test_frozen_files_are_as_frozen_or_the_study_says_it_is_a_draft():
    import hashlib

    frozen = HERE / "FROZEN.json"
    if not frozen.exists():
        assert "DRAFT" in (HERE / "STORY.md").read_text(encoding="utf-8")
        return
    # FROZEN.json, then FROZEN-2.json and on, each in its own commit and never
    # edited after: a file is held to the hash of the latest freeze naming it
    freezes = [frozen] + sorted(
        HERE.glob("FROZEN-*.json"), key=lambda p: int(p.stem.split("-")[1])
    )
    held: dict[str, tuple[str, str]] = {}
    for f in freezes:
        for rel, sha in json.loads(f.read_text(encoding="utf-8"))["files"].items():
            held[rel] = (sha, f.name)
    for rel, (sha, name) in held.items():
        got = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
        assert got == sha, f"{rel} changed after {name}; a change is a new freeze"


def test_the_kiosk_is_one_page_from_2013(played, tmp_path):
    page = tmp_path / "kiosk.html"
    got = py(
        HERE / "kiosk.py", "build", "--scene", played["tmp"] / "scene", "--to", page
    )
    assert got.returncode == 0, got.stderr
    html = page.read_text(encoding="utf-8")
    data = json.loads(html.split('type="application/json">')[1].split("</script>")[0])
    assert len(data["boxes"]) == 8 and data["found"]["join"]["on no list"] == 1
    script = html.split("<script>")[1].split("</script>")[0]
    # nothing on that machine is newer than that machine
    for newer in ("=>", "let ", "const ", "`", "fetch(", "async ", "class ", ".includes(",
                  ".padEnd(", "Object.entries", "Promise", "?."):  # fmt: skip
        assert newer not in script, newer
    assert not re.search(r"[(\[,]\s*\.\.\.[A-Za-z_]", script), "spread syntax"
    for newer in ("display:flex", "display: flex", "grid", "var(--", "@supports"):
        assert newer not in html, newer
    # no network, and no address of anyone's in it
    assert "http://" not in html and "https://" not in html and "src=" not in html
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", html)
    assert "2:10 AM" in html and "10/18/2026" in html


def test_the_kiosk_refuses_a_bad_command_line():
    assert py(HERE / "kiosk.py", "build").returncode == 2
