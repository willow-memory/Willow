"""index-cache: a folder's scan index kept between runs, rebuilt only when the
folder changed, or of a list's files where they are kept (`--from @LIST`). It
builds the first time, reports "current" when every indexed
file's hash still matches, rebuilds on an edit, add or removal (and says which),
ignores a change to a file the index never read, and refuses a bad command
line. The cached index answers through scan."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IC = HERE / "index_cache.py"
SCAN = HERE.parent / "batch-ask" / "scan.py"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(IC), *argv], capture_output=True, text=True
    )


def a_folder(tmp: Path) -> tuple[Path, Path]:
    """A two-file folder and an index path beside it; (folder, index)."""
    folder = tmp / "folder"
    folder.mkdir()
    (folder / "roof.md").write_text("2026-03-01 The roof estimate was 4200.\n")
    (folder / "mould.md").write_text("2026-03-02 Reported the mould.\n")
    return folder, tmp / "ix"


def cache(folder: Path, index: Path) -> subprocess.CompletedProcess:
    return run("--from", str(folder), "--to", str(index))


def test_it_builds_then_reports_current(tmp_path):
    folder, index = a_folder(tmp_path)
    first = cache(folder, index)
    assert first.returncode == 0 and "rebuilt" in first.stdout, (
        first.stdout + first.stderr
    )
    assert (index / "cache.json").exists() and (index / "index.json").exists()
    again = cache(folder, index)
    assert again.returncode == 0 and "current" in again.stdout, again.stdout


def test_an_edited_file_rebuilds(tmp_path):
    folder, index = a_folder(tmp_path)
    cache(folder, index)
    (folder / "mould.md").write_text("2026-03-02 The mould spread to the hall.\n")
    got = cache(folder, index)
    assert got.returncode == 0 and "rebuilt" in got.stdout
    assert "~1 changed" in got.stdout


def test_an_added_then_removed_file_each_rebuild(tmp_path):
    folder, index = a_folder(tmp_path)
    cache(folder, index)
    (folder / "garden.md").write_text("Tomatoes want sun.\n")
    added = cache(folder, index)
    assert added.returncode == 0 and "+1 new" in added.stdout
    (folder / "garden.md").unlink()
    removed = cache(folder, index)
    assert removed.returncode == 0 and "-1 removed" in removed.stdout


def test_a_manifest_from_another_kernel_forces_a_rebuild(tmp_path):
    import json

    folder, index = a_folder(tmp_path)
    cache(folder, index)
    # a manifest whose files still match, but written by another kernel.py:
    # the index's passages were that kernel's, so it must be rebuilt, not reused
    manifest = index / "cache.json"
    head = json.loads(manifest.read_text())
    head["kernel"] = "some-other-kernel-version"
    manifest.write_text(json.dumps(head))
    got = cache(folder, index)
    assert got.returncode == 0 and "rebuilt" in got.stdout, got.stdout
    assert "current" not in got.stdout  # a stale-kernel manifest is never "current"


def test_a_change_to_an_unread_file_does_not_rebuild(tmp_path):
    folder, index = a_folder(tmp_path)
    cache(folder, index)
    (folder / ".hidden.md").write_text("a dotfile the index never read\n")
    (folder / "picture.bin").write_bytes(b"\x00\x01\x02binary\x00")
    got = cache(folder, index)
    assert got.returncode == 0 and "current" in got.stdout, got.stdout


def test_the_cached_index_answers_with_scan(tmp_path):
    folder, index = a_folder(tmp_path)
    cache(folder, index)
    qs = tmp_path / "q.txt"
    qs.write_text("roof estimate\n")
    got = subprocess.run(
        [sys.executable, str(SCAN), "scan", "--index", str(index),
         "--questions", str(qs), "--top", "1"],
        capture_output=True, text=True,
    )  # fmt: skip
    assert got.returncode == 0 and "roof estimate was 4200" in got.stdout


def test_an_empty_folder_escalates(tmp_path):
    folder = tmp_path / "empty"
    folder.mkdir()
    got = cache(folder, tmp_path / "ix")
    assert got.returncode == 42, got.stdout + got.stderr


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    folder, index = a_folder(tmp_path)
    for argv in (
        [],  # nothing
        ["--from", str(folder)],  # no --to
        ["--to", str(index)],  # no --from
        ["--from", str(folder), "--to", str(index), "--stray"],  # unknown flag
    ):
        got = run(*argv)
        assert got.returncode == 2 and "index_cache.py" in got.stderr, (
            argv,
            got.stderr,
        )


def test_a_from_that_is_not_a_folder_is_refused(tmp_path):
    got = run("--from", str(tmp_path / "missing"), "--to", str(tmp_path / "ix"))
    assert got.returncode == 2 and "is not a folder" in got.stderr


def test_an_edit_and_an_untouched_file_count_only_the_edit(tmp_path):
    folder, index = a_folder(tmp_path)
    (folder / "garden.md").write_text("Tomatoes want sun.\n")
    cache(folder, index)
    (folder / "mould.md").write_text("2026-03-02 The mould spread to the hall.\n")
    got = cache(folder, index)
    assert "+0 new, ~1 changed, -0 removed" in got.stdout, got.stdout


# ── --from @LIST: a list's files where they are kept (CONST-VI-9) ─────────────
def a_list(tmp: Path) -> tuple[Path, Path, Path]:
    """The two-file folder, a third file the list leaves out, and a list of the
    two kept apart from them; (folder, list, index)."""
    folder, index = a_folder(tmp)
    (folder / "unlisted.md").write_text("The shed door sticks.\n")
    lst = tmp / "lists" / "home.list"
    lst.parent.mkdir()
    lst.write_text(f"{folder / 'roof.md'}\n# a note\n\n{folder / 'mould.md'}\n")
    return folder, lst, index


def test_a_list_builds_then_reports_current(tmp_path):
    folder, lst, index = a_list(tmp_path)
    first = run("--from", f"@{lst}", "--to", str(index))
    assert first.returncode == 0 and "+2 new" in first.stdout, (
        first.stdout + first.stderr
    )
    again = run("--from", f"@{lst}", "--to", str(index))
    assert again.returncode == 0 and "current: 2 files" in again.stdout, again.stdout


def test_a_list_reads_what_the_kernel_reads_of_it(tmp_path):
    sys.path.insert(0, str(HERE.parent / "batch-ask"))
    sys.path.insert(0, str(HERE.parents[2]))
    import kernel
    import scan

    folder, lst, index = a_list(tmp_path)
    run("--from", f"@{lst}", "--to", str(index))
    kept = [(c["path"], c["id"]) for c in scan.passages(index)]
    assert kept == [(c["path"], c["id"]) for c in kernel.list_chunks(lst)]
    assert {p for p, _ in kept} == {"roof.md", "mould.md"}  # never unlisted.md


def test_a_list_rebuilds_on_a_listed_file_and_not_an_unlisted_one(tmp_path):
    folder, lst, index = a_list(tmp_path)
    run("--from", f"@{lst}", "--to", str(index))
    (folder / "unlisted.md").write_text("The shed door is fixed.\n")
    quiet = run("--from", f"@{lst}", "--to", str(index))
    assert "current" in quiet.stdout, quiet.stdout
    (folder / "roof.md").write_text("2026-03-01 The roof estimate was 4500.\n")
    moved = run("--from", f"@{lst}", "--to", str(index))
    assert "+0 new, ~1 changed, -0 removed" in moved.stdout, moved.stdout


def test_a_listed_file_gone_counts_as_removed(tmp_path):
    folder, lst, index = a_list(tmp_path)
    run("--from", f"@{lst}", "--to", str(index))
    (folder / "mould.md").unlink()
    got = run("--from", f"@{lst}", "--to", str(index))
    assert got.returncode == 0 and "-1 removed" in got.stdout, got.stdout


def test_an_index_beside_the_listed_files_is_fine_but_one_holding_them_is_not(
    tmp_path,
):
    folder, lst, _ = a_list(tmp_path)
    beside = run("--from", f"@{lst}", "--to", str(folder / "ix"))
    assert beside.returncode == 0, beside.stderr
    holds = run("--from", f"@{lst}", "--to", str(tmp_path / "lists"))
    assert holds.returncode == 2 and "hold each other" in holds.stderr


def test_a_list_that_is_not_there_is_refused(tmp_path):
    got = run("--from", f"@{tmp_path / 'missing.list'}", "--to", str(tmp_path / "ix"))
    assert got.returncode == 2 and "is not a list of files" in got.stderr


# ── --box BOX: everything a box reads, as the kernel's pile_of_box names it ───
KERNEL = HERE.parents[2] / "kernel.py"


def a_box(tmp: Path, *froms: str, pile: Path | None = None) -> Path:
    b = tmp / "box"
    argv = [sys.executable, str(KERNEL), "init", "--box", str(b)]
    argv += ["--pile", str(pile)] if pile else []
    for f in froms:
        argv += ["--from", f]
    got = subprocess.run(
        argv + ["--key", str(tmp / "k")], capture_output=True, text=True
    )
    assert got.returncode == 0, got.stderr
    return b


def test_a_box_from_several_places_is_indexed_as_the_kernel_reads_it(tmp_path):
    sys.path.insert(0, str(HERE.parent / "batch-ask"))
    sys.path.insert(0, str(HERE.parents[2]))
    import kernel
    import scan

    folder, lst, index = a_list(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    (other / "garden.md").write_text("Tomatoes want sun.\n")
    b = a_box(tmp_path, f"home=@{lst}", f"garden={other}")
    first = run("--box", str(b), "--to", str(index))
    assert first.returncode == 0 and "+3 new" in first.stdout, (
        first.stdout + first.stderr
    )
    kept = [(c["path"], c["id"]) for c in scan.passages(index)]
    read = kernel.pile_of_box(kernel.config(b))
    assert kept == [(c["path"], c["id"]) for c in read]
    assert "current: 3 files" in run("--box", str(b), "--to", str(index)).stdout
    (folder / "unlisted.md").write_text("Still not listed.\n")
    assert "current" in run("--box", str(b), "--to", str(index)).stdout
    (other / "garden.md").write_text("Tomatoes want more sun.\n")
    moved = run("--box", str(b), "--to", str(index))
    assert "+0 new, ~1 changed, -0 removed" in moved.stdout, moved.stdout


def test_a_pile_box_keeps_the_pile_folders_index(tmp_path):
    folder, index = a_folder(tmp_path)
    b = a_box(tmp_path, pile=folder)
    cache(folder, index)  # made with --from PILE
    again = run("--box", str(b), "--to", str(index))
    assert again.returncode == 0 and "current" in again.stdout, again.stdout


def test_a_box_index_is_refused_inside_the_box_or_what_it_reads(tmp_path):
    folder, index = a_folder(tmp_path)
    b = a_box(tmp_path, f"home={folder}")
    for at in (b / "ix", folder / "ix"):
        got = run("--box", str(b), "--to", str(at))
        assert got.returncode == 2 and "hold each other" in got.stderr, at


def test_a_box_that_is_not_one_or_both_kinds_of_from_is_refused(tmp_path):
    folder, index = a_folder(tmp_path)
    got = run("--box", str(tmp_path / "nobox"), "--to", str(index))
    assert got.returncode == 2 and "is not a box" in got.stderr
    both = run("--box", str(tmp_path), "--from", str(folder), "--to", str(index))
    assert both.returncode == 2 and "index_cache.py" in both.stderr
