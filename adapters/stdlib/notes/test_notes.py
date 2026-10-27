"""notes: vaults in, mirror out. Every vault is built here as text, nothing is a
fixture file, and the mirror is always run the way a person runs it."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE / "notes.py"
KERNEL = HERE.parents[2] / "kernel.py"
#: what a note with no links ends with: absence said, not left out
NONE = "\n\nlinked from: none\n\nlinks to: none\n"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def mirror(src: Path, dst: Path) -> subprocess.CompletedProcess:
    return run(str(NOTES), "mirror", "--from", str(src), "--to", str(dst))


def build(root: Path, files: dict[str, str | bytes]) -> Path:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(
            content if isinstance(content, bytes) else content.encode("utf-8")
        )
    return root


def out(dst: Path, rel: str) -> str:
    return (dst / (rel + ".txt")).read_bytes().decode("utf-8")


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_each_wikilink_form_becomes_its_shown_words(tmp_path):
    vault = build(
        tmp_path / "vault",
        {
            "Hub.md": "See [[Alpha]], [[Beta|the second one]], [[Gamma#Setup]] "
            "and [[Delta#Setup|the delta steps]].\n"
        },
    )
    dst = tmp_path / "mirror"
    assert mirror(vault, dst).returncode == 0
    # the links are also listed, so the whole file is checked, not one line
    assert out(dst, "Hub.md") == (
        "See Alpha, the second one, Gamma and the delta steps.\n"
        "\n"
        "linked from: none\n"
        "\n"
        "links to: Alpha, Beta, Delta, Gamma\n"
    )


def test_tags_from_body_front_matter_and_logseq_properties(tmp_path):
    vault = build(
        tmp_path / "vault",
        {
            "a.md": "---\ntags: [writing, Ideas]\n---\n"
            "Plans for #garden, see https://example.org/#frag\n"
            "# Heading stays a heading\n",
            "b.md": '---\ntags:\n  - "project"\n  - #drafts\n---\nBody.\n',
            "c.md": "---\ntags: food, travel\n---\nBody.\n",
            "d.md": "- tags:: [[reading]], travel\n- A block with #music\n",
        },
    )
    dst = tmp_path / "mirror"
    assert mirror(vault, dst).returncode == 0
    assert out(dst, "a.md").splitlines()[0] == "tags: garden, Ideas, writing"
    assert "# Heading stays a heading" in out(dst, "a.md")
    assert "https://example.org/#frag" in out(dst, "a.md")
    assert out(dst, "b.md") == "tags: drafts, project\n\nBody." + NONE
    assert out(dst, "c.md") == "tags: food, travel\n\nBody." + NONE
    # the tags:: line is collected, not kept; the #music in the body still counts
    assert (
        out(dst, "d.md") == "tags: music, reading, travel\n\nA block with #music" + NONE
    )


def test_front_matter_removed_but_iso_date_kept(tmp_path):
    vault = build(
        tmp_path / "vault",
        {
            "daily.md": "---\ntitle: Walk notes\naliases: [walk]\n"
            "created: 2024-03-03T09:15\n---\nWent for a walk.\n",
            "bad.md": '---\ndate: "2024-02-30"\n---\nNo real date.\n',
            "open.md": "---\ntitle: never closed\nNo close line here.\n",
        },
    )
    dst = tmp_path / "mirror"
    assert mirror(vault, dst).returncode == 0
    assert out(dst, "daily.md") == "date: 2024-03-03\n\nWent for a walk." + NONE
    assert out(dst, "bad.md") == "No real date." + NONE
    # not front matter (the header never closes as YAML), so every line is kept
    assert out(dst, "open.md") == "---\ntitle: never closed\nNo close line here." + NONE


def test_logseq_bullets_and_id_lines_dropped(tmp_path):
    vault = build(
        tmp_path / "vault",
        {
            "Alpha.md": "x\n",
            "page.md": "- First block\n\t- Nested with [[Alpha]]\n"
            "\t\tid:: 6503f1a2-0000-0000-0000-000000000000\n- Last block\n",
        },
    )
    dst = tmp_path / "mirror"
    assert mirror(vault, dst).returncode == 0
    assert out(dst, "page.md") == (
        "First block\nNested with Alpha\nLast block\n\nlinked from: none\n\nlinks to: Alpha\n"
    )


def test_backlinks_and_links_to_match_names_without_case(tmp_path):
    vault = build(
        tmp_path / "vault",
        {
            "Alpha.md": "Alpha is the start. See [[beta]] and [[Gamma]].\n",
            "beta.md": "Beta. Back to [[ALPHA|the first note]].\n",
            "Gamma.md": "Gamma links [[Beta]] only.\n",
        },
    )
    dst = tmp_path / "mirror"
    assert mirror(vault, dst).returncode == 0
    assert out(dst, "Alpha.md") == (
        "Alpha is the start. See beta and Gamma.\n"
        "\nlinked from: beta\n"
        "\nlinks to: beta, Gamma\n"
    )
    assert out(dst, "beta.md") == (
        "Beta. Back to the first note.\n"
        "\nlinked from: Alpha, Gamma\n"
        "\nlinks to: Alpha\n"
    )
    assert out(dst, "Gamma.md") == (
        "Gamma links Beta only.\n\nlinked from: Alpha\n\nlinks to: beta\n"
    )


def test_obsidian_and_trash_folders_and_hidden_files_skipped(tmp_path):
    vault = build(
        tmp_path / "vault",
        {
            ".obsidian/app.md": "hidden config\n",
            ".trash/old.md": "deleted note\n",
            ".hidden.md": "hidden file\n",
            "visible.md": "a visible note\n",
        },
    )
    dst = tmp_path / "mirror"
    got = mirror(vault, dst)
    assert got.returncode == 0
    assert got.stdout.strip().endswith("skipped 0")
    assert sorted(p.name for p in dst.rglob("*") if p.is_file()) == ["visible.md.txt"]


def test_non_utf8_and_nul_files_skipped_and_counted(tmp_path):
    vault = build(
        tmp_path / "vault",
        {
            "ok.md": "readable\n",
            "latin.md": b"caf\xe9 not utf-8\n",
            "nul.md": b"text\x00more\n",
        },
    )
    dst = tmp_path / "mirror"
    got = mirror(vault, dst)
    assert got.returncode == 0
    assert got.stdout.strip().endswith("; skipped 2")
    assert [p.name for p in dst.rglob("*") if p.is_file()] == ["ok.md.txt"]


def test_nothing_readable_exits_42(tmp_path):
    vault = build(tmp_path / "vault", {"latin.md": b"caf\xe9\n", "note.txt": "no\n"})
    got = mirror(vault, tmp_path / "mirror")
    assert got.returncode == 42
    assert (
        got.stdout.strip()
        == f"wrote 0 files to {(tmp_path / 'mirror').resolve()}; skipped 1"
    )


def test_mirror_inside_folder_is_refused(tmp_path):
    vault = build(tmp_path / "vault", {"a.md": "x\n"})
    got = mirror(vault, vault / "out")
    assert got.returncode == 2
    assert got.stderr.startswith("refused:")
    assert not (vault / "out").exists()


def test_folder_inside_mirror_is_refused(tmp_path):
    vault = build(tmp_path / "mirror" / "vault", {"a.md": "x\n"})
    got = mirror(vault, tmp_path / "mirror")
    assert got.returncode == 2
    assert got.stderr.startswith("refused:")


def test_folder_that_is_not_a_folder_is_refused(tmp_path):
    got = mirror(tmp_path / "missing", tmp_path / "mirror")
    assert got.returncode == 2
    assert got.stderr.startswith("refused:")


def test_originals_are_unchanged(tmp_path):
    vault = build(
        tmp_path / "vault",
        {
            "Alpha.md": "---\ntags: [x]\n---\nSee [[beta]] #tag\n",
            "beta.md": "- bullet [[Alpha]]\n\tid:: 1\n",
            "latin.md": b"caf\xe9\n",
        },
    )
    before = snapshot(vault)
    assert mirror(vault, tmp_path / "mirror").returncode == 0
    assert snapshot(vault) == before


def test_two_runs_give_identical_bytes(tmp_path):
    vault = build(
        tmp_path / "vault",
        {
            "Alpha.md": "---\ndate: 2024-03-03\n---\n[[beta|Second]] and #tag\n",
            "beta.md": "- Back to [[Alpha]]\n",
            "daily/2024-03-03.md": "Walk. #outdoors\n",
        },
    )
    one, two = tmp_path / "one", tmp_path / "two"
    assert mirror(vault, one).returncode == 0
    assert mirror(vault, two).returncode == 0
    assert snapshot(one) == snapshot(two)
    assert "daily/2024-03-03.md.txt" in {
        p.relative_to(one).as_posix() for p in one.rglob("*.txt")
    }


def test_code_fences_are_kept_as_written(tmp_path):
    vault = build(
        tmp_path / "vault",
        {
            "code.md": "```\n- [[Alpha]] #notatag\n```\n",
            "Alpha.md": "x\n",
        },
    )
    dst = tmp_path / "mirror"
    assert mirror(vault, dst).returncode == 0
    assert out(dst, "code.md") == "```\n- [[Alpha]] #notatag\n```" + NONE


def test_bite_finds_a_word_that_only_a_link_shows(tmp_path):
    vault = build(
        tmp_path / "vault",
        {
            "plans/Q3 Review.md": "The money went to [[Budget Sheet|zebrafish allowance]].\n",
            "Budget Sheet.md": "Totals by month.\n",
        },
    )
    dst = tmp_path / "mirror"
    assert mirror(vault, dst).returncode == 0
    box = tmp_path / "box"
    key = tmp_path / "key"
    assert (
        run(
            str(KERNEL),
            "init",
            "--box",
            str(box),
            "--pile",
            str(dst),
            "--key",
            str(key),
            *NOW,
        ).returncode
        == 0
    )
    got = run(str(KERNEL), "bite", "--box", str(box), *NOW, "zebrafish")
    assert got.returncode == 0, got.stderr
    doc = json.loads(got.stdout)
    assert doc["state"] == "populated"
    served = [s for s in doc["served"] if "Q3 Review" in s["where"]]
    assert served and "zebrafish allowance" in served[0]["text"]
    assert "[[" not in served[0]["text"]


def test_a_link_with_no_name_and_no_heading_stays_as_written(tmp_path):
    vault = build(tmp_path / "vault", {"Hub.md": "See [[.md]] and [[#Setup]].\n"})
    dst = tmp_path / "mirror"
    assert mirror(vault, dst).returncode == 0
    assert out(dst, "Hub.md").startswith("See [[.md]] and Setup.\n")
