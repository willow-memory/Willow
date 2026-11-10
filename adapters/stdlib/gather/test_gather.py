"""gather: the folders and files named are copied under --to, a folder under
its own name and a file straight in; only the kinds kept, never a name
skipped, a key, a file over 1 MB, a hidden folder or a link; run again it
refreshes its own copies and nothing else; the places named are only read;
and what it did is said as a report (and --json the same)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def gather(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "gather.py"), *map(str, argv)],
        capture_output=True,
        text=True,
    )


def put(root: Path, files: dict) -> Path:
    for rel, data in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else data.encode())
    return root


def held(root: Path) -> dict:
    """Every file under a folder, by its path from it."""
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def project(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A folder of two files, one of them a folder down, a single file, and
    the pile they go to (not made yet)."""
    panes = put(tmp_path / "work" / "panes", {"a.py": "a = 1\n", "sub/b.md": "# b\n"})
    app = put(tmp_path / "work", {"app.py": "print('app')\n"}) / "app.py"
    return panes, app, tmp_path / "pile"


def test_a_bad_command_line_is_refused_and_names_the_script():
    got = subprocess.run(
        [sys.executable, str(HERE / "gather.py")], capture_output=True, text=True
    )
    assert got.returncode == 2 and "gather.py" in got.stderr


def test_a_folder_goes_in_under_its_own_name_and_a_file_straight_in(tmp_path):
    panes, app, pile = project(tmp_path)
    got = gather("--from", panes, "--from", app, "--to", pile)
    assert got.returncode == 0 and got.stderr == ""
    assert got.stdout == (
        "gather: populated, 3 files copied from 2 places\n"
        "  panes   2 files\n"
        "  app.py  1 file\n"
    )
    assert held(pile) == {
        "panes/a.py": b"a = 1\n",
        "panes/sub/b.md": b"# b\n",
        "app.py": b"print('app')\n",
    }


def test_json_gives_the_same_report_as_one_object(tmp_path):
    panes, app, pile = project(tmp_path)
    put(panes, {"big.bin": "x", "c.txt": "c"})
    argv = ["--from", panes, "--from", app, "--to", pile, "--keep", "py,md"]
    got = gather(*argv, "--json")
    assert got.returncode == 0
    assert json.loads(got.stdout) == {
        "addon": "gather",
        "state": "populated",
        "said": "3 files copied from 2 places, 2 left out",
        "groups": [
            {
                "name": None,
                "rows": [
                    {"where": "panes", "what": "2 files"},
                    {"where": "app.py", "what": "1 file"},
                ],
            },
            {
                "name": "left out",
                "rows": [{"where": "not a kind you keep", "what": "2 files"}],
            },
        ],
    }
    assert got.stdout.count("\n") == 1  # one object, on one line
    assert gather(*argv).stdout == (
        "gather: populated, 3 files copied from 2 places, 2 left out\n"
        "  panes                2 files\n"
        "  app.py               1 file\n"
        "## left out\n"
        "  not a kind you keep  2 files\n"
    )


def test_keep_is_the_endings_that_go_in_dot_or_not_in_any_case(tmp_path):
    src = put(
        tmp_path / "src",
        {"a.py": "a", "B.PY": "b", "c.md": "c", "d.txt": "d", "e": "e", "f.pyc": "f"},
    )
    got = gather("--from", src, "--to", tmp_path / "pile", "--keep", "py, .MD")
    assert got.returncode == 0
    assert sorted(held(tmp_path / "pile")) == ["src/B.PY", "src/a.py", "src/c.md"]
    assert got.stdout.splitlines() == [
        "gather: populated, 3 files copied from 1 place, 3 left out",
        "  src                  3 files",
        "## left out",
        "  not a kind you keep  3 files",
    ]


def test_every_kind_goes_in_when_no_keep_is_given(tmp_path):
    src = put(tmp_path / "src", {"a.py": "a", "d.txt": "d", "e": "e", ".hidden": "h"})
    got = gather("--from", src, "--to", tmp_path / "pile")
    assert got.returncode == 0
    assert sorted(held(tmp_path / "pile")) == [
        "src/.hidden",
        "src/a.py",
        "src/d.txt",
        "src/e",
    ]


def test_skip_leaves_out_a_folder_or_a_file_by_name_with_a_star_for_anything(tmp_path):
    src = put(
        tmp_path / "src",
        {
            "a.py": "a",
            "test_a.py": "t",
            "Test_B.py": "t",
            "tests/one.py": "1",
            "tests/two.py": "2",
            "deep/data/rows.csv": "r",
            "deep/keep.py": "k",
        },
    )
    got = gather(
        "--from", src, "--to", tmp_path / "pile", "--skip", "tests, data,test_*.py"
    )
    assert got.returncode == 0
    assert sorted(held(tmp_path / "pile")) == ["src/a.py", "src/deep/keep.py"]
    # a folder skipped is never walked, so only the two files skipped by name are counted
    assert got.stdout.splitlines() == [
        "gather: populated, 2 files copied from 1 place, 2 left out",
        "  src              2 files",
        "## left out",
        "  a name you skip  2 files",
    ]


def test_a_file_that_looks_like_a_key_is_never_copied(tmp_path):
    keys = [
        "server.key",
        "CERT.PEM",
        ".env",
        ".env.local",
        "my_secret_notes.md",
        "id_rsa",
        "id_rsa.pub",
        "id_ed25519",
        "store.p12",
    ]
    src = put(tmp_path / "src", {**dict.fromkeys(keys, "hush"), "notes.md": "n"})
    put(src, {"deep/down/api.key": "hush"})
    pile = tmp_path / "pile"
    # asking for it by its ending doesn't bring it, and a key is said as a key
    # even when its name is also one skipped
    got = gather(
        "--from", src, "--to", pile, "--keep", ".md,.key,.pem", "--skip", "id_rsa"
    )
    assert got.returncode == 0
    assert held(pile) == {"src/notes.md": b"n"}
    assert got.stdout.splitlines() == [
        "gather: populated, 1 file copied from 1 place, 10 left out",
        "  src               1 file",
        "## left out",
        "  looks like a key  10 files",
    ]
    # nor named by hand
    alone = gather("--from", src / "server.key", "--to", pile)
    assert alone.returncode == 42
    assert alone.stdout.splitlines() == [
        "gather: empty, 0 files copied from 1 place, 1 left out",
        "  server.key        0 files",
        "## left out",
        "  looks like a key  1 file",
    ]
    assert held(pile) == {"src/notes.md": b"n"}


def test_a_file_over_one_megabyte_is_left_out_and_one_of_exactly_that_goes_in(tmp_path):
    src = put(
        tmp_path / "src",
        {"fits.txt": b"x" * 1_000_000, "over.txt": b"x" * 1_000_001},
    )
    got = gather("--from", src, "--to", tmp_path / "pile")
    assert got.returncode == 0
    assert sorted(held(tmp_path / "pile")) == ["src/fits.txt"]
    assert got.stdout.splitlines() == [
        "gather: populated, 1 file copied from 1 place, 1 left out",
        "  src        1 file",
        "## left out",
        "  over 1 MB  1 file",
    ]


def test_hidden_folders_and_the_ones_no_one_reads_are_left_out_uncounted(tmp_path):
    src = put(
        tmp_path / "src",
        {
            "a.py": "a",
            ".git/config": "c",
            ".cache/x.py": "x",
            "node_modules/pkg/index.js": "j",
            "venv/lib/site.py": "s",
            "__pycache__/a.pyc": "p",
            "dist/a.whl": "w",
            "build/a.o": "o",
            "lib/node_modules/deep.js": "j",
            "lib/b.py": "b",
            "builder/c.py": "c",
        },
    )
    got = gather("--from", src, "--to", tmp_path / "pile")
    assert got.returncode == 0
    assert sorted(held(tmp_path / "pile")) == [
        "src/a.py",
        "src/builder/c.py",
        "src/lib/b.py",
    ]
    assert (
        got.stdout == "gather: populated, 3 files copied from 1 place\n  src  3 files\n"
    )


def test_links_are_left_out(tmp_path):
    src = put(tmp_path / "src", {"a.py": "a"})
    elsewhere = put(tmp_path / "elsewhere", {"far.py": "far", "more/deep.py": "deep"})
    os.symlink(elsewhere / "far.py", src / "link.py")
    os.symlink(elsewhere / "more", src / "linked")
    os.symlink(src / "nowhere", src / "broken.py")
    got = gather("--from", src, "--to", tmp_path / "pile")
    assert got.returncode == 0
    assert held(tmp_path / "pile") == {"src/a.py": b"a"}
    assert (
        got.stdout == "gather: populated, 1 file copied from 1 place\n  src  1 file\n"
    )


def test_a_file_named_by_hand_goes_in_whatever_keep_says(tmp_path):
    src = put(tmp_path / "src", {"a.py": "a", "b.txt": "b"})
    one = put(tmp_path, {"LICENSE": "free\n"}) / "LICENSE"
    pile = tmp_path / "pile"
    got = gather("--from", src, "--from", one, "--to", pile, "--keep", ".py")
    assert got.returncode == 0
    assert held(pile) == {"src/a.py": b"a", "LICENSE": b"free\n"}
    assert got.stdout.splitlines()[0] == (
        "gather: populated, 2 files copied from 2 places, 1 left out"
    )


def test_a_file_named_by_hand_is_still_held_to_skip_and_to_size(tmp_path):
    put(tmp_path, {"notes.txt": "n", "huge.txt": b"x" * 1_000_001, "ok.txt": "ok"})
    pile = tmp_path / "pile"
    got = gather(
        "--from", tmp_path / "notes.txt", "--from", tmp_path / "huge.txt",
        "--from", tmp_path / "ok.txt", "--to", pile, "--skip", "notes.*",
    )  # fmt: skip
    assert got.returncode == 0
    assert held(pile) == {"ok.txt": b"ok"}
    assert got.stdout.splitlines() == [
        "gather: populated, 1 file copied from 3 places, 2 left out",
        "  notes.txt        0 files",
        "  huge.txt         0 files",
        "  ok.txt           1 file",
        "## left out",
        "  a name you skip  1 file",
        "  over 1 MB        1 file",
    ]


def test_the_reasons_a_file_was_left_out_are_said_in_one_order(tmp_path):
    src = put(
        tmp_path / "src",
        {
            "a.py": "a",
            "b.txt": "b",
            "c.txt": "c",
            "skipped.py": "s",
            "x.pem": "k",
            "big.py": b"x" * 1_000_001,
        },
    )
    got = gather(
        "--from",
        src,
        "--to",
        tmp_path / "pile",
        "--keep",
        ".py",
        "--skip",
        "skipped.py",
        "--json",
    )
    assert got.returncode == 0
    doc = json.loads(got.stdout)
    assert doc["said"] == "1 file copied from 1 place, 5 left out"
    assert doc["groups"][1] == {
        "name": "left out",
        "rows": [
            {"where": "not a kind you keep", "what": "2 files"},
            {"where": "a name you skip", "what": "1 file"},
            {"where": "looks like a key", "what": "1 file"},
            {"where": "over 1 MB", "what": "1 file"},
        ],
    }


def test_run_again_it_refreshes_a_file_gone_from_the_source_goes_from_the_copy(
    tmp_path,
):
    panes, app, pile = project(tmp_path)
    put(panes, {"old/gone.py": "gone", "old/deeper/gone.md": "gone", "sub/c.md": "c"})
    argv = ["--from", panes, "--from", app, "--to", pile]
    assert gather(*argv).returncode == 0
    assert len(held(pile)) == 6
    (panes / "old" / "gone.py").unlink()
    (panes / "old" / "deeper" / "gone.md").unlink()
    (panes / "sub" / "c.md").unlink()
    (panes / "a.py").write_text("a = 2\n")
    app.write_text("print('new')\n")
    put(panes, {"fresh.py": "fresh"})
    got = gather(*argv)
    assert got.returncode == 0
    assert got.stdout == (
        "gather: populated, 4 files copied from 2 places, 3 removed as gone\n"
        "  panes   3 files\n"
        "  app.py  1 file\n"
    )
    assert held(pile) == {
        "panes/a.py": b"a = 2\n",
        "panes/fresh.py": b"fresh",
        "panes/sub/b.md": b"# b\n",
        "app.py": b"print('new')\n",
    }
    # the folders that left empty went too; one still holding a file stays
    assert not (pile / "panes" / "old").exists()
    assert (pile / "panes" / "sub").is_dir()
    # and with nothing changed, nothing is removed
    assert gather(*argv).stdout == (
        "gather: populated, 4 files copied from 2 places\n  panes   3 files\n  app.py  1 file\n"
    )


def test_a_file_no_longer_kept_goes_from_the_copy_on_the_next_run(tmp_path):
    src = put(tmp_path / "src", {"a.py": "a", "b.txt": "b"})
    pile = tmp_path / "pile"
    assert gather("--from", src, "--to", pile).returncode == 0
    got = gather("--from", src, "--to", pile, "--keep", ".py")
    assert got.returncode == 0
    assert held(pile) == {"src/a.py": b"a"}
    assert got.stdout.splitlines()[0] == (
        "gather: populated, 1 file copied from 1 place, 1 left out, 1 removed as gone"
    )


def test_a_refresh_removes_only_inside_the_copies_it_made(tmp_path):
    panes, app, pile = project(tmp_path)
    mine = {"my-notes.md": "mine\n", "other/kept.md": "kept\n", "other/empty/.keep": ""}
    put(pile, mine)
    (pile / "bare").mkdir()
    argv = ["--from", panes, "--from", app, "--to", pile]
    assert gather(*argv).returncode == 0
    (panes / "a.py").unlink()
    app.unlink()  # a single file that went is said, and its copy is left
    got = gather(*argv)
    assert got.returncode == 42
    assert got.stdout.splitlines()[0] == (
        "gather: populated, 1 file copied from 1 place, 1 removed as gone, 1 place not there"
    )
    assert held(pile) == {
        **{rel: data.encode() for rel, data in mine.items()},
        "panes/sub/b.md": b"# b\n",
        "app.py": b"print('app')\n",
    }
    assert (pile / "bare").is_dir()


def test_a_copy_that_already_holds_the_same_bytes_is_not_written_again(tmp_path):
    panes, app, pile = project(tmp_path)
    argv = ["--from", panes, "--from", app, "--to", pile]
    assert gather(*argv).returncode == 0
    copies = [pile / "panes" / "a.py", pile / "panes" / "sub" / "b.md", pile / "app.py"]
    for path in copies:
        os.utime(path, (1_000_000_000, 1_000_000_000))
    (panes / "a.py").write_text("a = 2\n")
    assert gather(*argv).returncode == 0
    assert copies[0].read_text() == "a = 2\n"
    assert copies[0].stat().st_mtime != 1_000_000_000
    assert [p.stat().st_mtime for p in copies[1:]] == [1_000_000_000, 1_000_000_000]


def test_the_places_named_are_only_read(tmp_path):
    panes, app, pile = project(tmp_path)
    put(
        panes,
        {
            "x.key": "hush",
            "tests/t.py": "t",
            ".git/config": "c",
            "big.bin": b"x" * 1_000_001,
        },
    )
    work = tmp_path / "work"

    def seen() -> dict:
        return {
            p.relative_to(work).as_posix(): (p.stat().st_mtime_ns, p.is_file() and p.read_bytes())
            for p in sorted(work.rglob("*"))
        }  # fmt: skip

    before = seen()
    argv = [
        "--from",
        panes,
        "--from",
        app,
        "--to",
        pile,
        "--keep",
        ".py",
        "--skip",
        "tests",
    ]
    assert gather(*argv).returncode == 0
    assert gather(*argv, "--json").returncode == 0  # and a refresh
    assert seen() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["pile", "work"]


def test_a_place_that_isnt_there_is_said_and_the_rest_is_still_copied(tmp_path):
    panes, app, pile = project(tmp_path)
    nowhere = tmp_path / "work" / "nowhere"
    argv = ["--from", nowhere, "--from", panes, "--to", pile]
    got = gather(*argv)
    assert got.returncode == 42 and got.stderr == ""
    where = str(nowhere)
    assert got.stdout.splitlines() == [
        "gather: populated, 2 files copied from 1 place, 1 place not there",
        f"  {'panes':<{min(len(where), 60)}}  2 files",
        "## not there",
        f"  {where}  named, and not a file or folder",
    ]
    assert sorted(held(pile)) == ["panes/a.py", "panes/sub/b.md"]
    data = gather(*argv, "--json")
    assert data.returncode == 42
    doc = json.loads(data.stdout)
    assert doc["state"] == "populated"
    assert doc["groups"][-1] == {
        "name": "not there",
        "rows": [{"where": where, "what": "named, and not a file or folder"}],
    }


def test_when_no_place_named_is_there_it_couldnt_look(tmp_path):
    pile = tmp_path / "pile"
    got = gather(
        "--from", tmp_path / "one", "--from", tmp_path / "two", "--to", pile, "--json"
    )
    assert got.returncode == 42
    doc = json.loads(got.stdout)
    assert doc["state"] == "unreachable"
    assert doc["said"] == "0 files copied from 0 places, 2 places not there"
    assert [g["name"] for g in doc["groups"]] == ["not there"]
    assert [r["where"] for r in doc["groups"][0]["rows"]] == [
        str(tmp_path / "one"),
        str(tmp_path / "two"),
    ]
    assert held(pile) == {}


def test_a_place_gone_with_nothing_else_copied_couldnt_look_either(tmp_path):
    src = put(tmp_path / "src", {"a.txt": "a"})
    got = gather(
        "--from",
        src,
        "--from",
        tmp_path / "gone",
        "--to",
        tmp_path / "pile",
        "--keep",
        ".py",
    )
    assert got.returncode == 42
    assert got.stdout.splitlines()[0] == (
        "gather: unreachable, 0 files copied from 1 place, 1 left out, 1 place not there"
    )


def test_nothing_copied_is_empty_and_waits_on_you(tmp_path):
    src = put(tmp_path / "src", {"a.txt": "a", "b.txt": "b"})
    pile = tmp_path / "pile"
    got = gather("--from", src, "--to", pile, "--keep", ".py")
    assert got.returncode == 42
    assert got.stdout.splitlines() == [
        "gather: empty, 0 files copied from 1 place, 2 left out",
        "  src                  0 files",
        "## left out",
        "  not a kind you keep  2 files",
    ]
    assert held(pile) == {}
    bare = tmp_path / "bare"
    bare.mkdir()
    got = gather("--from", bare, "--to", pile)
    assert got.returncode == 42
    assert got.stdout == "gather: empty, 0 files copied from 1 place\n  bare  0 files\n"


def test_the_where_column_is_as_wide_as_its_longest_up_to_sixty(tmp_path):
    panes, _, pile = project(tmp_path)
    long = tmp_path / ("n" * 70)
    got = gather("--from", panes, "--from", long, "--to", pile)
    assert got.returncode == 42
    lines = got.stdout.splitlines()
    assert lines[1] == "  " + "panes".ljust(60) + "  2 files"
    assert lines[3] == f"  {long}  named, and not a file or folder"
    short = put(tmp_path / ("m" * 59), {"a.py": "a"})
    got = gather("--from", panes, "--from", short, "--to", pile)
    assert got.returncode == 0
    assert got.stdout.splitlines()[1:] == [
        "  " + "panes".ljust(59) + "  2 files",
        "  " + "m" * 59 + "  1 file",
    ]


def refused(got: subprocess.CompletedProcess) -> str:
    assert got.returncode == 2 and got.stdout == "", (got.returncode, got.stdout)
    return got.stderr


def test_a_command_line_missing_a_part_or_holding_a_stray_one_is_refused(tmp_path):
    panes, app, pile = project(tmp_path)
    for argv in (
        ["--from", panes],  # nowhere to put it
        ["--to", pile],  # nothing to gather
        ["--from", panes, "--to"],  # --to with no folder after it
        ["--to", pile, "--from"],  # --from with no place after it
        ["--from", panes, "--from", "", "--to", pile],
        ["--from", panes, "--to", pile, "stray"],
        ["--from", panes, "--to", pile, "--stray", "more"],
        [panes, pile],
    ):
        assert refused(gather(*argv)).startswith("usage: gather.py --from PATH"), argv
        assert not pile.exists(), argv


def test_a_pile_inside_a_source_or_a_source_inside_the_pile_is_refused(tmp_path):
    panes, app, _ = project(tmp_path)
    work = tmp_path / "work"
    for src, to in (
        (work, panes),  # the pile inside the source
        (work, panes / "deep" / "pile"),
        (panes, work),  # the source inside the pile
        (panes / "sub", work),
        (app, work),  # a single file inside the pile
        (panes, panes),  # the same folder
    ):
        before = held(tmp_path)
        said = refused(
            gather("--from", tmp_path / "elsewhere", "--from", src, "--to", to)
        )
        assert said.startswith(f"refused: {src} and {to} hold one another"), said
        assert held(tmp_path) == before and not (panes / "deep").exists()
    # side by side is fine
    assert gather("--from", panes, "--to", work / "pile").returncode == 0


def test_two_places_with_the_same_name_are_refused(tmp_path):
    panes, app, pile = project(tmp_path)
    twin = put(tmp_path / "other" / "panes", {"z.py": "z"})
    said = refused(gather("--from", panes, "--from", app, "--from", twin, "--to", pile))
    assert said.startswith("refused: two places are both named panes;")
    assert not pile.exists()
    # the same place named twice is the same mistake
    assert "both named app.py" in refused(
        gather("--from", app, "--from", app, "--to", pile)
    )
    # three places, three names: nothing to refuse
    put(tmp_path / "other", {"tools/t.py": "t"})
    got = gather(
        "--from",
        panes,
        "--from",
        app,
        "--from",
        tmp_path / "other" / "tools",
        "--to",
        pile,
    )
    assert got.returncode == 0


def test_the_pile_is_made_when_it_isnt_there_and_used_when_it_is(tmp_path):
    panes, app, pile = project(tmp_path)
    assert not pile.exists()
    assert gather("--from", app, "--to", pile).returncode == 0
    assert held(pile) == {"app.py": b"print('app')\n"}
    assert gather("--from", panes, "--to", pile).returncode == 0
    assert sorted(held(pile)) == ["app.py", "panes/a.py", "panes/sub/b.md"]


def test_called_in_process_it_gives_the_same_report_and_exit_codes(
    tmp_path, monkeypatch, capsys
):
    sys.path.insert(0, str(HERE))
    try:
        import gather as addon
    finally:
        sys.path.remove(str(HERE))
    panes, app, pile = project(tmp_path)
    argv = ["--from", str(panes), "--from", str(app), "--to", str(pile)]
    monkeypatch.setattr(sys, "argv", ["gather.py", *argv])  # the guard reads --to here
    assert addon.main(argv) == 0
    assert capsys.readouterr().out == gather(*argv).stdout
    assert addon.main([*argv, "--from", str(tmp_path / "nowhere")]) == 42
    assert addon.main(["--from", str(panes)]) == 2
    assert capsys.readouterr().err.startswith("usage: gather.py")
