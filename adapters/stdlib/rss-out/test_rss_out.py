"""rss-out: each approved answer as an RSS 2.0 item, newest first, its title
the answer's first line, its date when it was approved, its id the suggestion's
subject; escaped, parseable, filtered by --since; a forged approval never
exported and a changed proposal left out and said; the same bytes twice;
written once and private; refusals."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "rss_out.py"
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("kernel_for_rss", KERNEL)
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)
spec2 = importlib.util.spec_from_file_location("rss_out", SCRIPT)
ro = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(ro)


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def subject(row: dict) -> str:
    canon = json.dumps(
        {x: row[x] for x in ("path", "data", "cites", "claim")},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return "proposal:" + hashlib.sha256(canon.encode()).hexdigest()


def box(
    tmp_path: Path, answers: list[tuple[str, str]] | None = None, seal: bool = True
) -> tuple[Path, list[str]]:
    """A box with one approved answer for each (day, text), approved on that day."""
    tmp_path.mkdir(exist_ok=True)
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text(
        "Tomatoes want six hours of sun.\n\nBeans like it cooler & damp.\n"
    )
    b = tmp_path / "box"
    assert (
        k(
            "init",
            "--box",
            str(b),
            "--pile",
            str(pile),
            "--key",
            str(tmp_path / "key"),
            "--now",
            "2026-10-20T00:00:00Z",
        ).returncode
        == 0
    )
    subjects = []
    for n, (day, text) in enumerate(answers or [("2026-10-24", "Six hours of sun.")]):
        now = f"{day}T09:30:00Z"
        served = json.loads(
            k(
                "bite",
                "--box",
                str(b),
                "--now",
                now,
                f"how much sun do tomatoes want {n}"
                if n
                else "how much sun do tomatoes want",
            ).stdout
        )["served"]
        row = {
            "path": f"a{n}.md",
            "data": text,
            "cites": [served[0]["id"]],
            "claim": f"the garden notes {n}",
        }
        (tmp_path / "r.jsonl").write_text(json.dumps(row) + "\n")
        assert (
            k(
                "propose",
                "--box",
                str(b),
                "--file",
                str(tmp_path / "r.jsonl"),
                "--now",
                now,
            ).returncode
            == 42
        )
        if seal:
            assert (
                k("seal", "--box", str(b), subject(row), "--now", now).returncode == 0
            )
        subjects.append(subject(row))
    return b, subjects


def feed(b: Path, tmp_path: Path, *extra: str):
    to = tmp_path / "f.xml"
    to.unlink(missing_ok=True)
    got = run("--box", str(b), "--to", str(to), *extra)
    return got, ET.fromstring(to.read_text()) if to.exists() else None


def test_an_approved_answer_is_an_item_with_title_description_date_and_id(tmp_path):
    b, (subj,) = box(tmp_path)
    got, root = feed(b, tmp_path)
    assert got.returncode == 0, got.stderr
    assert root.tag == "rss" and root.get("version") == "2.0"
    ch = root.find("channel")
    assert (
        ch.findtext("title") == "Willow: approved answers"
        and ch.findtext("link") == "http://localhost/"
    )
    (item,) = ch.findall("item")
    assert item.findtext("title") == "Six hours of sun."
    assert (
        item.findtext("description")
        == "Six hours of sun.\n\nWhy: the garden notes 0\nFrom: garden.md:1"
    )
    assert (
        item.findtext("pubDate") == "Sat, 24 Oct 2026 09:30:00 +0000"
        and ch.findtext("lastBuildDate") == "Sat, 24 Oct 2026 09:30:00 +0000"
    )
    guid = item.find("guid")
    assert guid.text == subj and guid.get("isPermaLink") == "false"
    assert got.stdout.strip() == f"wrote {tmp_path / 'f.xml'}: 1 item"


def test_items_are_newest_first(tmp_path):
    b, subjects = box(
        tmp_path,
        [("2026-10-20", "Oldest"), ("2026-10-22", "Middle"), ("2026-10-24", "Newest")],
    )
    _, root = feed(b, tmp_path)
    assert [i.findtext("title") for i in root.iter("item")] == [
        "Newest",
        "Middle",
        "Oldest",
    ]
    assert (
        root.find("channel").findtext("lastBuildDate")
        == "Sat, 24 Oct 2026 09:30:00 +0000"
    )


def test_since_keeps_only_answers_approved_on_or_after_it(tmp_path):
    b, _ = box(
        tmp_path,
        [("2026-10-20", "Oldest"), ("2026-10-22", "Middle"), ("2026-10-24", "Newest")],
    )
    _, root = feed(b, tmp_path, "--since", "2026-10-22")
    assert [i.findtext("title") for i in root.iter("item")] == ["Newest", "Middle"]


def test_text_is_escaped_and_the_title_is_cut_at_eighty_characters(tmp_path):
    long = "A & B <tag> " + "x" * 100
    b, _ = box(tmp_path, [("2026-10-24", long + "\nsecond line")])
    _, root = feed(b, tmp_path)
    item = root.find("channel/item")
    assert (
        item.findtext("title") == (long[:79] + "…")
        and len(item.findtext("title")) == 80
    )
    assert "<tag>" in item.findtext("description") and "second line" in item.findtext(
        "description"
    )
    assert "&amp; B &lt;tag&gt;" in (tmp_path / "f.xml").read_text()
    assert (
        ro.title_of("short") == "short"
        and ro.title_of("\n\n  first  \nsecond") == "first"
        and ro.title_of("") == "(empty answer)"
    )
    assert ro.title_of("x" * 80) == "x" * 80


def test_link_and_title_are_taken_and_checked(tmp_path):
    b, _ = box(tmp_path)
    _, root = feed(
        b, tmp_path, "--link", "https://example.org/feed", "--title", "My answers"
    )
    ch = root.find("channel")
    assert (
        ch.findtext("link") == "https://example.org/feed"
        and ch.findtext("title") == "My answers"
    )


def test_the_date_is_rfc_822_in_utc():
    assert ro.rfc822("2026-10-24T00:00:00Z") == "Sat, 24 Oct 2026 00:00:00 +0000"
    assert ro.rfc822("2026-01-05T13:04:09Z") == "Mon, 05 Jan 2026 13:04:09 +0000"
    assert ro.rfc822("2026-12-31T23:59:59Z") == "Thu, 31 Dec 2026 23:59:59 +0000"


def test_nothing_approved_is_an_empty_channel(tmp_path):
    b, _ = box(tmp_path, seal=False)
    got, root = feed(b, tmp_path)
    assert (
        got.returncode == 0
        and root.findall("channel/item") == []
        and root.find("channel/lastBuildDate") is None
    )
    assert "0 items" in got.stdout


def test_a_forged_approval_is_in_no_feed_and_a_changed_proposal_is_left_out_and_said(
    tmp_path,
):
    b, (subj,) = box(tmp_path, seal=False)
    kernel.append(
        b, "2026-10-24T00:00:00Z", "seal", who="human", subject=subj, proof="0" * 64
    )
    got, root = feed(b, tmp_path)
    assert got.returncode == 0 and root.findall("channel/item") == []
    b2, (s2,) = box(tmp_path / "two")
    f = b2 / "proposals" / f"{s2[9:]}.json"
    f.write_text(f.read_text().replace("Six", "Ten"))
    got, root = feed(b2, tmp_path / "two")
    assert (
        got.returncode == 42
        and root.findall("channel/item") == []
        and "1 approval left out" in got.stderr
    )


def test_the_same_record_gives_the_same_bytes_and_the_file_is_written_once_private(
    tmp_path,
):
    b, _ = box(tmp_path)
    to = tmp_path / "f.xml"
    assert run("--box", str(b), "--to", str(to)).returncode == 0
    assert stat.S_IMODE(os.stat(to).st_mode) == 0o600
    one = to.read_bytes()
    again = run("--box", str(b), "--to", str(to))
    assert again.returncode == 2 and "could not write" in again.stderr
    to.unlink()
    run("--box", str(b), "--to", str(to))
    assert to.read_bytes() == one
    assert (
        run("--box", str(b), "--to", str(tmp_path / "nope" / "f.xml")).returncode == 2
    )


def test_a_record_that_does_not_verify_is_refused(tmp_path):
    b, _ = box(tmp_path)
    rec = b / "record.jsonl"
    rec.write_text(rec.read_text().replace("2026-10-20", "2025-10-20", 1))
    got = run("--box", str(b), "--to", str(tmp_path / "f.xml"))
    assert got.returncode == 2 and not (tmp_path / "f.xml").exists()


def test_the_box_is_not_changed(tmp_path):
    b, _ = box(tmp_path)
    before = {p: p.read_bytes() for p in b.rglob("*") if p.is_file()}
    run("--box", str(b), "--to", str(tmp_path / "f.xml"))
    assert {p: p.read_bytes() for p in b.rglob("*") if p.is_file()} == before


def test_a_bad_command_line_says_how_to_run_it(tmp_path):
    b, _ = box(tmp_path)
    to = str(tmp_path / "f.xml")
    for argv in ([], ["--box", str(b)], ["--to", to], ["--box", str(b), "--to", to, "stray"], ["--box", str(b), "--to", to, "--link", "ftp://x"],
                 ["--box", str(b), "--to", to, "--link"], ["--box", str(b), "--to", to, "--title", " "], ["--box", str(b), "--to", to, "--since", "yesterday"],
                 ["--box", str(tmp_path), "--to", to]):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert "rss_out.py" in run().stderr
