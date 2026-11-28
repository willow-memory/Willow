"""kernel.py, the smallest script for anyone: its thirteen beats hold, the whole
loop runs on the command line, and what it serves is what its rules say."""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent / "kernel.py"
spec = importlib.util.spec_from_file_location("kernel", HERE)
k = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k)


def cli(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE), *argv], capture_output=True, text=True
    )


def test_its_twelve_beats_hold():
    p = cli("test")
    assert p.returncode == 0 and "fourteen beats held" in p.stdout, p.stderr


#: For each beat Draft 0.16, 0.17 and 0.18 added, a break planted in a copy of the kernel,
#: and the beat that must catch it: a check that cannot fail is no check
#: (CONST-IV-9). Each is the one promise its clause makes, broken.
PLANTED = {
    # CONST-V-10: out offers a proposal the person declined
    "# 7.": ("and s not in no and", "and"),
    # CONST-V-11: the door offers again what was sealed, declined or waits
    "# 11./door": (
        'why = offered(box, read(box / "record.jsonl")[0], subject_of(prop))',
        "why = None",
    ),
    # CONST-V-11: what waits is counted once a row, not once a thing to decide
    "# 11./once": ("out[s] = r", "out[f\"{s} {r['n']}\"] = r"),
    # CONST-IV-10: the order follows the process's hash seed
    "# 8.": ("key=lambda s: (-s[0],", "key=lambda s: (hash(s[2]) % 3, -s[0],"),
    # CONST-III-6: the core reaches for an add-on, quietly
    "# 9.": (
        "from fractions import Fraction\n",
        "from fractions import Fraction\n\ntry:\n"
        "    import adapters.stdlib.todo  # noqa: F401\nexcept ImportError:\n"
        "    pass\n",
    ),
    # CONST-VI-9: a source's passages lose their source's name
    "# 14./named": (
        """out += [{**c, "path": f"{name}/{c['path']}", "source": name} for c in part]""",
        "out += part",
    ),
    # CONST-VI-9: a source's name is a word every one of its passages holds
    "# 14./words": (
        'return c["path"][len(c["source"]) + 1 :] if c.get("source") else c["path"]',
        'return c["path"]',
    ),
    # CONST-VI-9: a list of files is read as the whole folder it sits in
    "# 14./listed": (
        'part = list_chunks(at) if cfg["sources"][name].startswith("@") else chunks(at)',
        'part = chunks(at.parent) if cfg["sources"][name].startswith("@") else chunks(at)',
    ),
    # CONST-VI-8: a bite's row keeps the question's words
    "# 10.": (
        'append(box, ts, "bite", bite_key=k, served=refs, **listed)',
        'append(box, ts, "bite", bite_key=k, served=refs, asked=text, **listed)',
    ),
}


@pytest.mark.parametrize("beat", sorted(PLANTED))
def test_each_new_beat_fails_on_its_planted_break(tmp_path, beat):
    old, new = PLANTED[beat]
    source = HERE.read_text(encoding="utf-8")
    assert source.count(old) == 1, old  # the break lands, or the test says so
    broken = tmp_path / "kernel.py"
    broken.write_text(source.replace(old, new), encoding="utf-8")
    p = subprocess.run(
        [sys.executable, str(broken), "test"], capture_output=True, text=True
    )
    assert p.returncode != 0 and "beats held" not in p.stdout
    # and the assert that failed is the planted beat's: the last line of the
    # broken copy the traceback names lies between that beat's comment and
    # the next beat's
    lines = broken.read_text(encoding="utf-8").split("\n")
    beats = [i for i, ln in enumerate(lines, 1) if re.match(r"\s*# \d+\. ", ln)]
    at = re.findall(rf'"{re.escape(str(broken))}", line (\d+)', p.stderr)[-1]
    mine = next(i for i in beats if lines[i - 1].strip().startswith(beat.split("/")[0]))
    after = [i for i in beats if i > mine]
    assert mine < int(at) < (after[0] if after else len(lines)), p.stderr


def test_the_whole_loop_on_the_command_line(tmp_path):
    pile, box, key = tmp_path / "pile", tmp_path / "box", tmp_path / "keys" / "me.key"
    pile.mkdir()
    (pile / "notes.md").write_text("The bus leaves at seven from the square.\n")
    b = ["--box", str(box), "--now", "2026-10-22T00:00:00Z"]
    assert cli("init", *b, "--pile", str(pile), "--key", str(key)).returncode == 0
    assert key.stat().st_mode & 0o077 == 0  # theirs alone
    assert cli("bite", *b, "when does the ferry sail").returncode == 42
    got = cli("bite", *b, "when does the bus leave the square")
    assert got.returncode == 0
    cite = json.loads(got.stdout)["served"][0]["id"]
    row = {"path": "bus.md", "data": "Seven.", "cites": [cite], "claim": "notes.md"}
    rows = tmp_path / "rows.jsonl"
    rows.write_text(json.dumps(row) + "\n")
    assert cli("propose", *b, "--file", str(rows)).returncode == 42
    assert cli("out", *b).returncode == 42
    subj = k.subject_of(row)
    assert cli("seal", *b, subj).returncode == 0
    again = cli("bite", *b, "When does the bus leave the square?")
    assert again.returncode == 0 and json.loads(again.stdout)["answer"] == "Seven."
    assert cli("out", *b).returncode == 0 and cli("verify", *b).returncode == 0
    text = (box / "record.jsonl").read_text()
    assert json.loads(text.split("\n")[0])["kind"] == "boot"
    assert "bus" not in text and "Seven" not in text  # hashes and places, never words


def test_a_no_is_proved_like_a_seal_and_is_final(tmp_path):
    """decline: the person's No, an HMAC under their key over "decline" and
    the subject. out stops offering it, seal refuses it, and a No that
    doesn't prove is never counted (LIMITS.md asked for this verb). A no is
    final (CONST-V-10)."""
    pile, box, key = tmp_path / "pile", tmp_path / "box", tmp_path / "keys" / "me.key"
    pile.mkdir()
    (pile / "notes.md").write_text("The bus leaves at seven from the square.\n")
    b = ["--box", str(box), "--now", "2026-10-22T00:00:00Z"]
    cli("init", *b, "--pile", str(pile), "--key", str(key))
    got = cli("bite", *b, "when does the bus leave the square")
    cite = json.loads(got.stdout)["served"][0]["id"]
    rows = tmp_path / "rows.jsonl"
    yes = {"path": "bus.md", "data": "Seven.", "cites": [cite], "claim": "notes.md"}
    no = {**yes, "path": "ferry.md", "data": "Noon."}
    rows.write_text(json.dumps(yes) + "\n" + json.dumps(no) + "\n")
    cli("propose", *b, "--file", str(rows))
    s_yes, s_no = k.subject_of(yes), k.subject_of(no)
    got = cli("decline", *b, s_no)
    assert (got.returncode, got.stdout) == (
        0,
        f"declined {s_no}; it won't be offered again\n",
    )
    row = json.loads((box / "record.jsonl").read_text().splitlines()[-1])
    assert (row["kind"], row["who"], row["subject"]) == ("decline", "human", s_no)
    mine, _ = k.read_key(key, box)
    assert row["proof"] == k.proof(mine, s_no, "decline") != k.proof(mine, s_no)
    out = cli("out", *b)
    assert (
        out.returncode == 42
        and s_no not in out.stdout
        and f"waiting on your seal: {s_yes}" in out.stdout
    )
    sealed = cli("seal", *b, s_no)
    assert (
        sealed.returncode == 2
        and f"you declined {s_no} at row {row['n']}" in sealed.stderr
    )
    assert "declined" in cli("decline", *b, s_no).stderr
    cli("seal", *b, s_yes)
    assert "you sealed" in cli("decline", *b, s_yes).stderr
    assert cli("decline", *b, "proposal:" + "0" * 64).returncode == 2
    assert cli("out", *b).returncode == 0  # nothing left waiting
    assert cli("verify", *b).stdout.startswith("the chain holds:")
    fake = k.append(
        box,
        "2026-10-22T00:00:00Z",
        "decline",
        who="human",
        subject=s_yes,
        proof="0" * 64,
    )
    forged = cli("verify", *b)
    assert forged.returncode == 42
    assert forged.stdout.endswith(
        f"decline rows [{fake['n']}] don't prove under your key\n"
    )
    rows_now, _ = k.read(box / "record.jsonl")
    assert set(k.declined(box, rows_now)) == {s_no}  # the forged No counts for nothing


def sealed_box(tmp_path: Path) -> tuple[Path, list[str], str]:
    """A box with one sealed answer, "Seven.", for the bus question: the box,
    the options every command takes, and the sealed subject."""
    pile, box, key = tmp_path / "pile", tmp_path / "box", tmp_path / "keys" / "me.key"
    pile.mkdir()
    (pile / "notes.md").write_text("The bus leaves at seven from the square.\n")
    b = ["--box", str(box), "--now", "2026-10-22T00:00:00Z"]
    cli("init", *b, "--pile", str(pile), "--key", str(key))
    got = cli("bite", *b, "when does the bus leave the square")
    cite = json.loads(got.stdout)["served"][0]["id"]
    row = {"path": "bus.md", "data": "Seven.", "cites": [cite], "claim": "notes.md"}
    (tmp_path / "rows.jsonl").write_text(json.dumps(row) + "\n")
    cli("propose", *b, "--file", str(tmp_path / "rows.jsonl"))
    subj = k.subject_of(row)
    assert cli("seal", *b, subj).returncode == 0
    return box, b, subj


def edit_proposal(box: Path, subj: str, **fields) -> None:
    f = box / "proposals" / f"{subj[9:]}.json"
    f.write_text(json.dumps({**json.loads(f.read_text()), **fields}))


def test_a_sealed_answer_is_served_only_while_its_bytes_are_the_ones_sealed(tmp_path):
    """The key signs a subject, the hash of the proposal's bytes. seal checks
    the file against it (CONST-0-4); serving must too, or whoever can write
    the box swaps what an approval says without the key."""
    box, b, subj = sealed_box(tmp_path)
    edit_proposal(box, subj, data="Never.")
    got = cli("bite", *b, "when does the bus leave the square")
    assert "Never." not in got.stdout, (
        "an answer the key never approved, served as sealed"
    )
    assert '"state": "sealed"' not in got.stdout


def test_a_sealed_answer_belongs_to_the_question_the_record_says(tmp_path):
    """The question an approval answers is on the hash chain, in the bite the
    proposal names. A file that says another question can't re-point it."""
    box, b, subj = sealed_box(tmp_path)
    other = json.loads(cli("bite", *b, "where is the ferry").stdout)["bite_key"]
    edit_proposal(box, subj, bite_key=other)
    assert cli("bite", *b, "where is the ferry").returncode == 42, "re-pointed"
    again = cli("bite", *b, "When does the bus leave the square?")
    assert again.returncode == 0 and json.loads(again.stdout)["answer"] == "Seven."


def test_a_sealed_answer_stays_with_the_question_it_was_sealed_for(tmp_path):
    """No file is touched: propose is the agent's verb, and a second proposal
    of the same bytes must not carry the person's seal to a new question."""
    box, b, subj = sealed_box(tmp_path)
    other = "which square does the bus leave from at seven"
    served = json.loads(cli("bite", *b, other).stdout)["served"]
    assert served and served[0]["text"].startswith("The bus leaves")  # same passage
    cli("propose", *b, "--file", str(tmp_path / "rows.jsonl"))
    got = cli("bite", *b, other)
    assert '"state": "sealed"' not in got.stdout, "carried to a question never sealed"
    again = cli("bite", *b, "When does the bus leave the square?")
    assert json.loads(again.stdout)["answer"] == "Seven."  # and the first still holds


def test_verify_says_when_a_sealed_proposals_file_no_longer_matches(tmp_path):
    box, b, subj = sealed_box(tmp_path)
    assert cli("verify", *b).returncode == 0
    f = box / "proposals" / f"{subj[9:]}.json"
    held = f.read_text()
    for what, change in (
        ("data", lambda: edit_proposal(box, subj, data="Never.")),
        ("bite_key", lambda: edit_proposal(box, subj, bite_key="0" * 64)),
        ("gone", lambda: f.unlink()),
    ):
        change()
        got = cli("verify", *b)
        assert got.returncode == 42, what
        assert subj in got.stdout and "proposal file" in got.stdout, what
        f.write_text(held)
    assert cli("verify", *b).returncode == 0  # put back, it holds again


def test_a_sealed_proposals_file_gone_never_brings_a_bite_down(tmp_path):
    box, b, subj = sealed_box(tmp_path)
    (box / "proposals" / f"{subj[9:]}.json").unlink()
    got = cli("bite", *b, "when does the bus leave the square")
    assert "Traceback" not in got.stderr and got.returncode in (0, 42)
    assert "Seven." not in got.stdout


def test_on_windows_the_record_is_locked_with_msvcrt(tmp_path, monkeypatch):
    """No fcntl on Windows: the record's first byte is locked with msvcrt,
    tried again while another writer holds it, before the row is written."""
    calls = []

    class Msvcrt:
        LK_LOCK = 1

        @staticmethod
        def locking(fd, mode, n):
            calls.append((mode, n))
            if len(calls) < 3:
                raise OSError("held by another writer")

    monkeypatch.setattr(k, "fcntl", None)
    monkeypatch.setattr(k, "msvcrt", Msvcrt)
    (tmp_path / "record.jsonl").write_text("")
    row = k.append(tmp_path, "2026-10-22T00:00:00Z", "boot")
    assert calls == [(1, 1)] * 3 and row["n"] == 0
    monkeypatch.setattr(k, "msvcrt", None)  # neither: written without a lock
    assert k.append(tmp_path, "2026-10-22T00:00:00Z", "boot")["n"] == 1


def test_a_strangers_files_are_read_by_what_they_hold_not_their_names(tmp_path):
    """quick-stupids' the-box: the answers lived in TODO, login.php, deploy.bat,
    error_log and a .doc that is plain text, none of them on a list of suffixes."""
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "TODO").write_text("TODO: pick a license -- rm, 3/9/1998\n")
    (pile / "deploy.bat").write_text("REM run the deploy from daves machine\r\n")
    (pile / "TEST_PROCEDURE.doc").write_text("compare the screens by eye\n")
    (pile / "Thumbs.db").write_bytes(b"\xd0\xcf\x11\xe0\0\0license deploy\0")
    got = {c["path"] for c in k.chunks(pile)}
    assert got == {"TODO", "deploy.bat", "TEST_PROCEDURE.doc"}  # a NUL is binary


def test_a_42_says_where_to_look():
    pile = [
        {"path": "login.php", "line": 3, "text": "function check_login($u) { }"},
        {"path": "app.py", "line": 1, "text": "def serve():\n    return 1"},
        {"path": "main.py", "line": 9, "text": "serve()"},
    ]
    why = [h["why"] for h in k.look(pile, "where is the database", [])]
    assert why == ["no file in your folder has database"]
    defs = {h["why"]: h["where"] for h in k.look(pile, "login serve", pile[:2])}
    assert defs == {
        "check_login is defined at login.php:3": "nothing else in your folder names it",
        "serve is defined at app.py:1": "also named in main.py",
    }
    assert k.look(pile, "what does this do", [])[0]["why"].startswith("every word")
    made = k.look(pile, "make a login page", [])
    assert made[-1]["why"] == "this asks for something made"


def test_a_key_inside_the_box_and_a_box_not_theirs_are_refused(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    box = tmp_path / "box"
    inside = cli(
        "init", "--box", str(box), "--pile", str(pile), "--key", str(box / "k")
    )
    assert inside.returncode == 2 and not (box / "record.jsonl").exists()
    assert cli("bite", "--box", str(tmp_path / "nobox"), "hello").returncode == 2
    assert cli("bite").returncode == 2  # a bad command line, never run


# The kernel holds a newcomer's own folder and never dials out. The scan is
# homestead-ledger's (I-17: "a money ledger must never dial out"), itself
# ported from marching-arts: no network module, and no eval/exec/compile/
# __import__ that could smuggle one past the import scan.
NET = {
    "socket",
    "ssl",
    "urllib",
    "http",
    "requests",
    "httpx",
    "aiohttp",
    "websockets",
    "urllib3",
    "socketserver",
    "ftplib",
    "telnetlib",
    "smtplib",
    "xmlrpc",
    "poplib",
    "imaplib",
    "nntplib",
    "asyncio",
}
DYNAMIC = {"eval", "exec", "compile", "__import__"}


def reaches(source: str) -> set[str]:
    """The network modules a source imports, and the dynamic calls it makes."""
    out = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            out |= {a.name.split(".")[0] for a in node.names} & NET
        elif isinstance(node, ast.ImportFrom) and node.module:
            out |= {node.module.split(".")[0]} & NET
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            out |= {node.func.id} & DYNAMIC
    return out


def imports(source: str) -> set[str]:
    """The top-level names of every module a source imports."""
    out = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            out |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            out.add(node.module.split(".")[0])
    return out


#: standard library on one system only: the kernel locks with whichever is there
ONE_PLATFORM = {"fcntl", "msvcrt"}


def outside_the_standard_library(names: set[str]) -> set[str]:
    """Those that aren't Python's own: built in, frozen, or under its lib folder."""
    lib = Path(sysconfig.get_paths()["stdlib"]).resolve()
    out = set()
    for name in names:
        if name == "__future__" or name in sys.builtin_module_names:
            continue
        if name in ONE_PLATFORM:  # the standard library's, on the other system
            continue
        spec = importlib.util.find_spec(name)
        origin = spec and spec.origin
        if origin in ("built-in", "frozen"):
            continue
        if (
            not origin
            or "site-packages" in origin
            or lib not in Path(origin).resolve().parents
        ):
            out.add(name)
    return out


def test_it_uses_only_the_standard_library_and_never_an_add_on():
    """The core reaches nothing that extends it (CONST-III-6)."""
    assert (
        outside_the_standard_library(imports(HERE.read_text(encoding="utf-8"))) == set()
    )
    planted = "import json\nimport pytest\nfrom adapters.stdlib import todo\n"
    assert outside_the_standard_library(imports(planted)) == {"pytest", "adapters"}


def test_it_never_dials_out():
    """No network module and no dynamic code: the kernel has no reach but
    what it is given (CONST-III-1), and nothing it holds leaves the machine
    (CONST-III-5)."""
    assert reaches(HERE.read_text(encoding="utf-8")) == set()
    planted = (
        "import json\ndef f(u):\n    from urllib import request\n    return eval(u)\n"
    )
    assert reaches(planted) == {"urllib", "eval"}


def test_a_file_name_with_a_line_separator_doesnt_brick_the_box(tmp_path):
    """A served `where` is a file name, kept raw (canon is ensure_ascii=False):
    U+2028, U+2029 and U+0085 in it must not cut the row when it's read back,
    the way the record is read ("\\n" only)."""
    pile, box, key = tmp_path / "pile", tmp_path / "box", tmp_path / "keys" / "me.key"
    pile.mkdir()
    for sep in (" ", " ", "\u0085"):
        (pile / f"tomato{sep}notes.md").write_text("Tomatoes want six hours of sun.\n")
    b = ["--box", str(box), "--now", "2026-10-22T00:00:00Z"]
    assert cli("init", *b, "--pile", str(pile), "--key", str(key)).returncode == 0
    assert cli("bite", *b, "how much sun do tomatoes want").returncode == 0
    assert cli("verify", *b).returncode == 0
    lines = (box / "record.jsonl").read_text(encoding="utf-8").split("\n")[:-1]
    assert [json.loads(line)["kind"] for line in lines][-1] == "bite"
    assert cli("bite", *b, "how much sun do tomatoes want").returncode == 0


#: A pile found by search (2026-10-21) where the float score's last bit, and so
#: the order of two chunks, followed the hash seed on Python 3.11: 13 runs in
#: 400 ranked it 11, 9, 5 instead of 11, 5, 9.
SEED_PILE = [
    "w1 w6",
    "w3 w1 w0 w2",
    "w4 w2 w0 w5 w3",
    "w2 w3 w0 w4 w1",
    "w4 w1 w3 w5",
    "w2 w6 w1 w3 w0",
    "w5 w0 w2 w1",
    "w5 w1 w0",
    "w2 w4 w1",
    "w3 w6 w1 w4 w5 w2",
    "w5 w3 w6",
    "w1 w2 w3 w6 w0 w4",
    "w5 w2 w4",
]
SEED_BITE = "w4 w2 w6 w1 w3 w0"


def test_the_rank_is_the_same_under_every_hash_seed():
    """Scores are exact (Fraction), so the set's walk order can't move them:
    the same question, the same answer (CONST-IV-10)."""
    pile = [
        {"path": f"f{i:02d}.md", "line": 1, "text": t, "id": str(i)}
        for i, t in enumerate(SEED_PILE)
    ]
    code = (
        "import json,sys,importlib.util as u;"
        f"s=u.spec_from_file_location('k',{str(HERE)!r});k=u.module_from_spec(s);"
        "s.loader.exec_module(k);"
        "print(','.join(c['id'] for c in k.rank(json.loads(sys.argv[1]),sys.argv[2])))"
    )
    # the old Pythons are where a float sum walks in set order: use any here
    pys = [sys.executable] + [
        p for v in ("3.9", "3.10", "3.11") if (p := shutil.which(f"python{v}"))
    ]
    got = {
        subprocess.run(
            [py, "-c", code, json.dumps(pile), SEED_BITE],
            capture_output=True,
            text=True,
            env={"PYTHONHASHSEED": str(seed)},
        ).stdout.strip()
        for seed in (0, 80, 101, 102, 126, 156)
        for py in pys
    }
    assert got == {"11,5,9"}


def test_among_equal_answers_the_newest_comes_first(tmp_path):
    """Odile's bees (demo/odile/STRIP.md): every inspection says "bees", and
    the one she means is the last. A log's date heading covers the lines
    under it, even across a chunk cut, and on one date the later line wins."""
    days = [f"== 2021-0{m}-10\n" + "H1: bees calm\n" * 30 for m in (3, 4)]
    days += [f"== 2026-0{m}-10\n" + "H1: bees calm\n" * 30 for m in (3, 4)]
    (tmp_path / "hives.txt").write_text("".join(days))
    (tmp_path / "notes.md").write_text("bees, no date\n")
    pile = k.chunks(tmp_path)
    got = k.rank(pile, "how are the bees")
    last = max(c["line"] for c in pile if c["path"] == "hives.txt")
    assert (got[0]["path"], got[0]["line"]) == ("hives.txt", last)
    assert "==" not in got[0]["text"]  # dated only by the heading above it
    assert k.dates(pile)[[c["line"] for c in pile].index(last)] == 20260410
    assert k.newest("2026-10-14 20261015 12026-10-16 2026-13-01") == "20261015"


def test_top_and_dated_change_how_many_and_whose_dates_never_the_order(tmp_path):
    """An add-on that lists every match, or an index that has the dates
    already, passes them in; rank is otherwise the same, and a TOP set from
    outside (demo/php2shell/phase6.py does) still holds when top isn't."""
    days = [f"== 2026-0{m}-10\nH1: bees calm, hive {m}\n" for m in range(1, 8)]
    (tmp_path / "hives.txt").write_text("\n".join(days))
    (tmp_path / "notes.md").write_text("bees, no date\n")
    pile = k.chunks(tmp_path)
    where = lambda got: [(c["path"], c["line"]) for c in got]  # noqa: E731
    every = k.rank(pile, "how are the bees", None, 10**9)
    assert len(every) == 8 and len(k.rank(pile, "how are the bees")) == k.TOP
    for top in (1, 3, 5):
        assert where(k.rank(pile, "how are the bees", None, top)) == where(every[:top])
    was = k.TOP
    try:
        k.TOP = 5
        assert where(k.rank(pile, "how are the bees")) == where(every[:5])
    finally:
        k.TOP = was
    assert k.rank(pile, "how are the bees", None, None, k.dates) == every[:3]
    undated = k.rank(pile, "how are the bees", None, 10**9, lambda p: [0] * len(p))
    assert where(undated) != where(every)
    assert sorted(where(undated)) == sorted(where(every))


def test_holding_is_every_passage_rank_weighs(tmp_path):
    """Every passage that holds the bite, in pile order: copies too, and
    none cut at TOP. One holding too few of its words is not among them."""
    (tmp_path / "a.md").write_text("the bees are calm\n\nthe bees are calm\n")
    (tmp_path / "b.md").write_text("bees swarm in May\n\nhow are you\n")
    (tmp_path / "c.md").write_text("calm weather\n")
    pile = k.chunks(tmp_path)
    got = [(c["path"], c["line"]) for c in k.holding(pile, "are the bees calm")]
    assert got == [("a.md", 1), ("a.md", 3), ("b.md", 1), ("c.md", 1)]
    assert {c["id"] for c in k.rank(pile, "are the bees calm", None, 10**9)} == {
        c["id"] for c in k.holding(pile, "are the bees calm")
    }
    assert k.holding(pile, "swarm bees spring") == [pile[2]]
    assert k.holding(pile, "how are the") == []


def test_anything_and_its_kin_name_no_topic(tmp_path):
    """ "did i promise siobhan anything": a file that never says "anything"
    still holds the question, by the promise. Bernadette's demo missed her
    written promise on this one word."""
    (tmp_path / "sent.md").write_text("To Siobhan: I promise Aoife the ring at 21.\n")
    (tmp_path / "other.md").write_text("Anything else for the shop? Someone asked.\n")
    pile = k.chunks(tmp_path)
    got = [c["path"] for c in k.rank(pile, "did i promise siobhan anything")]
    assert got == ["sent.md"]
    for w in ("anything", "something", "nothing", "everything", "anyone", "someone",
              "everyone", "anybody", "somebody", "everybody", "nobody", "anywhere",
              "somewhere", "everywhere", "nowhere"):  # fmt: skip
        assert w in k.FUNCTION, w
    assert k.rank(pile, "is there anything someone") == [], "common words only"


def test_her_words_list_reads_her_word_as_her_folders(tmp_path):
    """Odile asks who's due; her tuning log says `next:` (demo/odile/STRIP.md).
    Her own list, kept like her key, reads one as the other, says so when
    it did, and the record keeps the list's hash, never its words."""
    pile, box, mine = tmp_path / "pile", tmp_path / "box", tmp_path / "mine"
    pile.mkdir()
    (pile / "log.txt").write_text("2026-10-16 Calvin\n  next: Oct 2027\n")
    mine.mkdir(mode=0o700)
    wl = mine / "words.txt"
    wl.write_text("# what I call things\ndue = next, overdue\n")
    wl.chmod(0o600)
    b = ["--box", str(box), "--now", "2026-10-22T00:00:00Z"]
    key = ["--key", str(mine / "k.hex")]
    assert (
        cli("init", *b, "--pile", str(pile), *key, "--words", str(wl)).returncode == 0
    )
    got = cli("bite", *b, "who's due")
    doc = json.loads(got.stdout)
    assert got.returncode == 0 and doc["served"][0]["where"] == "log.txt:1"
    assert {"why": "read due as next, from your words list"} in doc["look"]
    row = json.loads((box / "record.jsonl").read_text().splitlines()[-1])
    assert row["words_sha256"] == k.hashlib.sha256(wl.read_bytes()).hexdigest()
    assert "next" not in json.dumps(row) and "due" not in json.dumps(row)
    wl.chmod(0o644)  # readable by others: refused, nothing written
    before = (box / "record.jsonl").read_text()
    assert cli("bite", *b, "who's due").returncode == 2
    assert (box / "record.jsonl").read_text() == before


def test_a_box_takes_a_words_list_after_it_was_made_and_the_record_says_so(tmp_path):
    """Vocabulary moves. A box made without a list, or with an early one, is
    given one with `words`: it is read from the next ask on, a row says the
    list changed (its hash, never its words), and nothing earlier is rewritten."""
    pile, box, mine = tmp_path / "pile", tmp_path / "box", tmp_path / "mine"
    pile.mkdir()
    (pile / "log.txt").write_text("2026-10-16 Calvin\n  next: Oct 2027\n")
    mine.mkdir(mode=0o700)
    b = ["--box", str(box), "--now", "2026-10-22T00:00:00Z"]
    assert (
        cli("init", *b, "--pile", str(pile), "--key", str(mine / "k.hex")).returncode
        == 0
    )
    assert cli("bite", *b, "who's due").returncode == 42  # no list: "due" finds nothing
    early = (box / "record.jsonl").read_text()
    wl = mine / "words.txt"
    wl.write_text("due = next, overdue\n")
    wl.chmod(0o600)
    got = cli("words", *b, "--words", str(wl))
    assert got.returncode == 0 and got.stdout.startswith(
        f"ready: this box reads {wl} from now on (1 words), row 2 "
    )
    record = (box / "record.jsonl").read_text()
    assert record.startswith(early)  # what was there is as it was
    row = json.loads(record.splitlines()[-1])
    assert row["kind"] == "words" and row["was_sha256"] == ""
    assert row["words_sha256"] == k.hashlib.sha256(wl.read_bytes()).hexdigest()
    assert "next" not in json.dumps(row) and "due" not in json.dumps(row)
    assert k.config(box)["words"] == str(wl.resolve())
    assert cli("bite", *b, "who's due").returncode == 0  # read through the list now
    assert cli("verify", "--box", str(box)).returncode == 0
    # the same list again: nothing to change, and no row
    again = cli("words", *b, "--words", str(wl))
    assert (
        again.returncode == 0
        and again.stdout == f"ready: this box already reads {wl.resolve()}\n"
    )
    assert len((box / "record.jsonl").read_text().splitlines()) == 4
    # another list later: the row names the one it replaced, by hash
    later = mine / "later.txt"
    later.write_text("due = next\nowed = unpaid\n")
    later.chmod(0o600)
    assert cli("words", *b, "--words", str(later)).returncode == 0
    row = json.loads((box / "record.jsonl").read_text().splitlines()[-1])
    assert row["was_sha256"] == k.hashlib.sha256(wl.read_bytes()).hexdigest()
    assert row["words_sha256"] == k.hashlib.sha256(later.read_bytes()).hexdigest()
    assert k.config(box)["words"] == str(later.resolve())
    assert not (box / "kernel.json.new").exists()


def test_the_list_a_words_row_replaced_is_the_one_the_record_last_read(tmp_path):
    """The row names the list the box last asked through, by its hash on the
    record: not the old file as it is now, which may have moved away (every
    ask refused, and `words` the way out) or been edited since."""
    pile, box, mine = tmp_path / "pile", tmp_path / "box", tmp_path / "mine"
    pile.mkdir()
    (pile / "log.txt").write_text("next: Oct 2027\n")
    mine.mkdir(mode=0o700)
    first, second, third = mine / "first.txt", mine / "second.txt", mine / "third.txt"
    for wl, text in ((first, "due = next\n"), (second, "owed = unpaid\n"), (third, "due = next\nowed = unpaid\n")):  # fmt: skip
        wl.write_text(text)
        wl.chmod(0o600)
    b = ["--box", str(box), "--now", "2026-10-22T00:00:00Z"]
    assert cli("init", *b, "--pile", str(pile), "--key", str(mine / "k.hex"),
               "--words", str(first)).returncode == 0  # fmt: skip
    assert cli("bite", *b, "what is due").returncode == 0
    read_through = k.hashlib.sha256(first.read_bytes()).hexdigest()
    first.rename(mine / "moved.txt")  # the list it was made with, gone
    assert cli("bite", *b, "what is due").returncode == 2
    assert cli("words", *b, "--words", str(second)).returncode == 0
    row = json.loads((box / "record.jsonl").read_text().splitlines()[-1])
    assert row["kind"] == "words" and row["was_sha256"] == read_through
    # the list now read is edited before the next one replaces it: the row
    # names the one the record last read (the words row's own), not the edit
    named = row["words_sha256"]
    second.write_text("owed = unpaid, overdue\n")
    assert cli("words", *b, "--words", str(third)).returncode == 0
    row = json.loads((box / "record.jsonl").read_text().splitlines()[-1])
    assert (
        row["was_sha256"] == named != k.hashlib.sha256(second.read_bytes()).hexdigest()
    )
    assert cli("verify", "--box", str(box)).returncode == 0


def test_a_words_list_edited_in_place_is_put_on_the_record_when_named_again(tmp_path):
    """Most lists are edited, not replaced. Named again after an edit, the
    same file is a new list to the record: a row says so by its hash, the
    settings stay as they are, and named again unedited it is no row."""
    pile, box, mine = tmp_path / "pile", tmp_path / "box", tmp_path / "mine"
    pile.mkdir()
    (pile / "log.txt").write_text("next: Oct 2027\n")
    mine.mkdir(mode=0o700)
    wl = mine / "words.txt"
    wl.write_text("due = next\n")
    wl.chmod(0o600)
    b = ["--box", str(box), "--now", "2026-10-22T00:00:00Z"]
    assert cli("init", *b, "--pile", str(pile), "--key", str(mine / "k.hex"),
               "--words", str(wl)).returncode == 0  # fmt: skip
    assert cli("bite", *b, "what is due").returncode == 0
    read_first = k.hashlib.sha256(wl.read_bytes()).hexdigest()
    settings = (box / "kernel.json").read_text()
    wl.write_text("due = next\nowed = unpaid\n")
    got = cli("words", *b, "--words", str(wl))
    assert (
        got.returncode == 0
        and "as it is now, edited since it was last read (2 words)" in got.stdout
    )
    row = json.loads((box / "record.jsonl").read_text().splitlines()[-1])
    assert row["kind"] == "words" and row["was_sha256"] == read_first
    assert row["words_sha256"] == k.hashlib.sha256(wl.read_bytes()).hexdigest()
    assert (box / "kernel.json").read_text() == settings
    rows = len((box / "record.jsonl").read_text().splitlines())
    again = cli("words", *b, "--words", str(wl))
    assert again.returncode == 0 and "already reads" in again.stdout
    assert len((box / "record.jsonl").read_text().splitlines()) == rows


def test_a_words_list_the_kernel_would_not_take_changes_nothing(tmp_path):
    pile, box, mine = tmp_path / "pile", tmp_path / "box", tmp_path / "mine"
    pile.mkdir()
    (pile / "log.txt").write_text("next: Oct 2027\n")
    mine.mkdir(mode=0o700)
    b = ["--box", str(box)]
    assert (
        cli("init", *b, "--pile", str(pile), "--key", str(mine / "k.hex")).returncode
        == 0
    )
    settings, record = (
        (box / "kernel.json").read_text(),
        (box / "record.jsonl").read_text(),
    )
    bad = mine / "bad.txt"
    bad.write_text("due = next week\n")  # two words on the right
    bad.chmod(0o600)
    open_ = mine / "open.txt"
    open_.write_text("due = next\n")
    open_.chmod(0o644)  # readable beyond its owner
    inside = box / "words.txt"
    inside.write_text("due = next\n")
    inside.chmod(0o600)
    for wl, why in ((bad, "words list line 1"), (open_, "readable beyond its owner"),
                    (inside, "can't live inside the box"), (mine / "none.txt", "could not be read")):  # fmt: skip
        got = cli("words", *b, "--words", str(wl))
        assert got.returncode == 2 and why in got.stderr, why
        assert (box / "kernel.json").read_text() == settings
        assert (box / "record.jsonl").read_text() == record
    # no list named, a stray word, or no box: the usage, and nothing changed
    assert cli("words", *b).returncode == 2
    assert cli("words", *b, "--words", str(open_), "extra").returncode == 2
    assert (
        cli("words", "--box", str(tmp_path / "nowhere"), "--words", str(bad)).returncode
        == 2
    )
    # a record that doesn't verify is not built on
    good = mine / "good.txt"
    good.write_text("due = next\n")
    good.chmod(0o600)
    (box / "record.jsonl").write_text(record.replace('"boot"', '"b00t"'))
    got = cli("words", *b, "--words", str(good))
    assert got.returncode == 2 and "doesn't verify; nothing was changed" in got.stderr
    assert (box / "kernel.json").read_text() == settings


def test_a_words_list_line_is_one_word_then_words():
    assert k.parse_words("due = next, overdue\nDUE = Next") == (
        {"due": ["next", "overdue"]},
        None,
    )
    for bad in ("due next", "due =", "a b = c", "due = next,", "due = next soon"):
        assert k.parse_words(bad)[1] == (
            "words list line 1: one word = one or more words, a comma between"
        ), bad


def test_a_folders_name_is_her_word(tmp_path):
    """ "Dad's weight": Laszlo's care log never says Dad, its folder does, and
    a client named Weight shouldn't outrank it (demo/odile, T1)."""
    (tmp_path / "dad").mkdir()
    (tmp_path / "dad" / "care-log.csv").write_text("date,weight_kg\n2026-10-21,75.1\n")
    (tmp_path / "books.csv").write_text("2026-06-08,check Harriet Weight,110\n")
    pile = k.chunks(tmp_path)
    assert k.rank(pile, "Dad's weight")[0]["path"] == "dad/care-log.csv"
    assert not any("dad" in h["why"] for h in k.look(pile, "Dad's weight", []))


def test_said_once_before_said_every_week_and_never_twice(tmp_path):
    """Odile's jar order, dictated every month, pushed out the van memo she
    still has to act on (demo/odile/STRIP.md): one text is one place, and on
    equal scores what was said once comes before what is routine."""
    (tmp_path / "memos").mkdir()
    for m in (3, 5, 7, 9):
        (tmp_path / "memos" / f"2026-0{m}-01.txt").write_text("need forty jars\n")
    (tmp_path / "memos" / "2021-05-14.txt").write_text("need to call the insurer\n")
    (tmp_path / "memos" / "2026-03-20.txt").write_text("you would need a permit\n")
    got = [c["path"] for c in k.rank(k.chunks(tmp_path), "what do I need to do")]
    assert got == [
        "memos/2026-03-20.txt",
        "memos/2021-05-14.txt",
        "memos/2026-09-01.txt",
    ]


def test_word_forms_are_one_word(tmp_path):
    """Hollis's "who still owes me money", Teodora's "how much do I still owe
    dev" (demo/hollis, demo/teodora): owe, owes, owed and owing are one word.
    Only plain ASCII words are touched; irregulars are her list's job."""
    for a, b in (
        ("owe", "owing"),
        ("owes", "owed"),
        ("tune", "tuning"),
        ("pay", "pays"),
    ):
        assert k.stem(a) == k.stem(b), (a, b)
    assert k.stem("paid") != k.stem("pay")
    assert k.stem("café") == "café" and k.stem("x1-2") == "x1-2"
    (tmp_path / "loan.md").write_text("Dev: owed 600, paying it back.\n")
    assert k.rank(k.chunks(tmp_path), "how much do I still owe dev")


def test_a_root_ending_in_eed_keeps_its_d():
    """Bug #308: feed lost its "ed" and became fee, so a sort phrase "feed"
    took every Apache-2.0 licence ("charge a fee"), and feed missed feeds."""
    for w in ("feed", "need", "seed", "speed", "breed", "bleed", "proceed"):
        assert k.stem(w) == k.stem(w + "s") == k.stem(w + "ing"), w
        assert k.stem(w) != k.stem(w[:-1]), w
    assert k.stem("needed") == k.stem("need")
    assert k.stem("fee") == k.stem("fees")


def test_an_accent_typed_one_way_holds_where_it_was_saved_the_other(tmp_path):
    """é is one code point as typed, and often e plus a combining accent as
    macOS saves it. Unmixed, the saved é split into "cafe" and a stray mark,
    and the question found nothing; both are composed (NFC) before words."""
    composed, apart = "Caf\u00e9 Lumi\u00e8re", "Cafe\u0301 Lumie\u0300re"
    assert k.words(apart) == k.words(composed) == ["café", "lumière"]
    (tmp_path / "plans.md").write_text(f"Friday: meet Ana at {apart}, 8pm.\n")
    (tmp_path / "other.md").write_text("Saturday: the market on Rue Cler.\n")
    got = k.rank(k.chunks(tmp_path), "when is the meeting at Caf\u00e9 Lumi\u00e8re")
    assert [c["path"] for c in got] == ["plans.md"]


def test_a_day_and_month_either_way_round_only_when_it_cant_be_misread():
    """Teodora's chats are dd/mm/yyyy; 11/03/2023 could be either, and the
    kernel never guesses."""
    assert k.newest("[15/10/2026, 19:30:00]") == "20261015"
    assert k.newest("10/21/2026") == "20261021"
    assert k.newest("21.10.2026") == "20261021"
    assert k.newest("5/5/2026") == "20260505"
    assert k.newest("[11/03/2023, 20:00:00]") == ""
    assert k.newest("1/300") == "" and k.newest("14/10/20261") == ""


def rehashed(box: Path, rows: list[dict]) -> None:
    """The record rewritten with every hash redone from the first row: the
    rewrite `verify` cannot tell from the original."""
    prev, out = k.GENESIS, []
    for n, r in enumerate(rows):
        r = {x: v for x, v in r.items() if x != "hash"}
        r["n"], r["prev"] = n, prev
        r["hash"] = prev = k.h256(k.canon(r))
        out.append(k.canon(r))
    (box / "record.jsonl").write_text("\n".join(out) + "\n")


def the_key(box: Path) -> bytes:
    return bytes.fromhex(
        Path(json.loads((box / "kernel.json").read_text())["key"]).read_text().strip()
    )


def test_a_seal_names_the_question_and_the_key_signs_it(tmp_path):
    """The person's seal covers which question the answer is for, not only the
    bytes: a seal row carries the question's key, and its proof is over the
    act, the subject and that key (CONST-0-4)."""
    box, b, subj = sealed_box(tmp_path)
    asked = json.loads(cli("bite", *b, "when does the bus leave the square").stdout)
    rows, _ = k.read(box / "record.jsonl")
    seal = next(r for r in rows if r["kind"] == "seal")
    assert seal["bite_key"] == k.bite_key("when does the bus leave the square")
    key = the_key(box)
    assert seal["proof"] == k.proof(key, subj, "seal", seal["bite_key"])
    assert seal["proof"] != k.proof(
        key, subj
    )  # not the form that left the question out
    assert asked["state"] == "sealed" and asked["answer"] == "Seven."


def test_a_rewritten_chain_cannot_re_point_a_sealed_answer(tmp_path):
    """The old binding lived on the hash chain, so a chain rewritten and
    re-hashed (the gap tip-pin exists for) could name another question. The
    key signs the question now, so it can't."""
    box, b, subj = sealed_box(tmp_path)
    other = k.bite_key("where is the ferry")
    cli("bite", *b, "where is the ferry")
    rows, _ = k.read(box / "record.jsonl")
    n_other = next(
        r["n"] for r in rows if r["kind"] == "bite" and r["bite_key"] == other
    )
    for r in rows:
        if r["kind"] == "proposal":
            r["bite_row"] = n_other  # the proposal now says it was made for the ferry
    rehashed(box, rows)
    edit_proposal(box, subj, bite_key=other)
    assert cli("verify", *b).returncode in (0, 42)
    got = cli("bite", *b, "where is the ferry")
    assert '"state": "sealed"' not in got.stdout, "re-pointed with no key"
    again = cli("bite", *b, "when does the bus leave the square")
    assert json.loads(again.stdout)["answer"] == "Seven."


def test_a_seal_rows_question_cannot_be_changed_or_stripped(tmp_path):
    box, b, subj = sealed_box(tmp_path)
    key = the_key(box)
    held, _ = k.read(box / "record.jsonl")
    n = next(r["n"] for r in held if r["kind"] == "seal")
    for what in ("changed", "stripped"):
        rows = [dict(r) for r in held]
        if what == "changed":
            rows[n]["bite_key"] = k.bite_key("where is the ferry")
        else:
            rows[n].pop("bite_key", None)
        rehashed(box, rows)
        got = cli("verify", *b)
        assert got.returncode == 42 and f"seal rows [{n}] don't prove" in got.stdout, (
            what
        )
        served = cli("bite", *b, "when does the bus leave the square")
        assert '"state": "sealed"' not in served.stdout, what
    rehashed(box, held)
    assert cli("verify", *b).returncode == 0 and key  # put back, it holds


def test_a_seal_made_before_the_question_was_signed_still_holds(tmp_path):
    """Existing boxes: a seal row with no question, proved the old way, still
    proves and still serves, its question taken from the record as before."""
    box, b, subj = sealed_box(tmp_path)
    key = the_key(box)
    held, _ = k.read(box / "record.jsonl")
    rows = [dict(r) for r in held]
    n = next(r["n"] for r in rows if r["kind"] == "seal")
    rows[n].pop("bite_key", None)
    rows[n]["proof"] = k.proof(key, subj)
    rehashed(box, rows)
    assert cli("verify", *b).returncode == 0
    got = cli("bite", *b, "When does the bus leave the square?")
    assert got.returncode == 0 and json.loads(got.stdout)["answer"] == "Seven."


@pytest.mark.xfail(
    strict=True, reason="bug #89: a line's text past its 500th character is never read"
)
def test_every_word_of_a_long_line_is_read(tmp_path):
    (tmp_path / "long.txt").write_text(
        "word " * 110 + "the tribble is in the airlock.\n"
    )
    read = " ".join(c["text"] for c in k.chunks(tmp_path))
    assert "airlock" in read


@pytest.mark.xfail(
    strict=True,
    reason="bug #284: html_text splits a word at an inline tag, so re<span>s</span>t reads as re s t",
)
def test_an_inline_tag_inside_a_word_leaves_the_word_whole():
    # Wikisource marks each long s of an old book this way
    page = '<p>remains always <span class="typographic-long-s">s</span>imilar</p>'
    assert k.html_text(page).split() == ["remains", "always", "similar"]
    assert k.html_text("<p>wo<b>rd</b>s</p><p>apart</p>").split() == ["words", "apart"]


def test_a_date_inside_a_web_address_dates_nothing():
    assert (
        k.newest("Nvidia rose 3% (https://example.com/snap/2026-10-24-nvda.html)") == ""
    )
    assert (
        k.newest("See http://example.com/20261024, then check 2026-10-25.")
        == "20261025"
    )


def test_a_day_the_month_does_not_have_dates_nothing():
    # June has thirty days: the 31st is a typo, not a date, and never the newest
    assert k.newest("Born 1984-06-31, moved 1990-01-02") == "19900102"
    for no_day in ("1984-06-31", "2026-04-31", "2023-02-29", "1900-02-29",
                   "20230229", "29/02/2023", "31/04/2026", "4/31/2026"):  # fmt: skip
        assert k.newest(no_day) == "", no_day
    for day in ("1984-06-30", "2026-12-31", "2024-02-29", "2000-02-29", "29/02/2024"):
        assert k.newest(day) != "", day


def test_a_propose_whose_every_suggestion_is_refused_does_not_exit_0(tmp_path):
    pile, box = tmp_path / "pile", tmp_path / "box"
    pile.mkdir()
    (pile / "notes.md").write_text("The bus leaves at seven from the square.\n")
    b = ["--box", str(box), "--now", "2026-10-22T00:00:00Z"]
    assert (
        cli("init", *b, "--pile", str(pile), "--key", str(tmp_path / "k")).returncode
        == 0
    )
    assert cli("bite", *b, "when does the bus leave the square").returncode == 0
    row = {"path": "bus.md", "data": "Seven.", "cites": ["0" * 64], "claim": "notes.md"}
    rows = tmp_path / "rows.jsonl"
    rows.write_text(json.dumps(row) + "\n")
    got = cli("propose", *b, "--file", str(rows))
    assert "refused" in got.stdout
    assert got.returncode == 42


def test_offered_once_counted_once(tmp_path):
    """V.11 on the command line: a suggestion proposed again is refused at
    the door, with why, whether it waits, was sealed or was declined; and a
    record from before the door, with one subject passed twice, is counted
    once (CONST-V-11)."""
    pile, box, key = tmp_path / "pile", tmp_path / "box", tmp_path / "keys" / "me.key"
    pile.mkdir()
    (pile / "notes.md").write_text("The bus leaves at seven from the square.\n")
    b = ["--box", str(box), "--now", "2026-10-22T00:00:00Z"]
    cli("init", *b, "--pile", str(pile), "--key", str(key))
    got = cli("bite", *b, "when does the bus leave the square")
    cite = json.loads(got.stdout)["served"][0]["id"]
    rows = tmp_path / "rows.jsonl"
    yes = {"path": "bus.md", "data": "Seven.", "cites": [cite], "claim": "notes.md"}
    no = {**yes, "path": "ferry.md", "data": "Noon."}
    wait = {**yes, "path": "tram.md", "data": "Eight."}
    rows.write_text("".join(json.dumps(x) + "\n" for x in (yes, no, wait, wait)))
    got = cli("propose", *b, "--file", str(rows))
    said = got.stdout.splitlines()
    assert got.returncode == 42 and said[3].startswith(
        "refused  line 3: already waiting on your seal, row "
    ), said
    assert cli("seal", *b, k.subject_of(yes)).returncode == 0
    assert cli("decline", *b, k.subject_of(no)).returncode == 0
    sealed_file = box / "proposals" / f"{k.subject_of(yes)[9:]}.json"
    before = sealed_file.read_text()
    got = cli("bite", *b, "the bus from the square at seven")  # other words
    assert cite in got.stdout
    got = cli("propose", *b, "--file", str(rows))
    said = got.stdout.splitlines()
    assert [x.split(": ")[1].rsplit(" ", 1)[0] for x in said] == [
        "you approved it at row",
        "you declined it at row",
        "already waiting on your seal, row",
        "already waiting on your seal, row",
    ], said
    record = k.read(box / "record.jsonl")[0]
    refused = [
        r for r in record if r["kind"] == "proposal" and r["verdict"] == "refused"
    ]
    assert len(refused) == 5 and all(r["why"] for r in refused)
    assert sealed_file.read_text() == before, "a refused one writes no file"
    # a record from before the door: the same subject passed twice
    first = next(r for r in record if r.get("subject") == k.subject_of(wait))
    k.append(box, "2026-10-22T00:00:00Z", "proposal", subject=first["subject"],
             verdict="pass", bite_row=first["bite_row"])  # fmt: skip
    got = cli("out", *b)
    assert got.returncode == 42 and got.stdout.count("waiting on your seal") == 1
    assert "; 1 waiting" in got.stdout


def test_a_box_reads_its_sources_where_they_are(tmp_path):
    pile, law, notes = tmp_path / "pile", tmp_path / "law", tmp_path / "notes"
    for d in (pile, law, notes):
        d.mkdir()
    (pile / "garden.md").write_text("Tomatoes want six hours of sun.\n")
    (law / "charter.md").write_text("The shed is painted every fourth spring.\n")
    (notes / "roof.md").write_text("The roof estimate was 4200.\n")
    lst = tmp_path / "list.txt"
    lst.write_text(f"{notes / 'roof.md'}\n")
    box = tmp_path / "box"
    b = ["--box", str(box), "--now", "2026-11-16T00:00:00Z"]
    got = cli("init", *b, "--pile", str(pile), "--from", f"law={law}",
              "--from", f"notes=@{lst}", "--key", str(tmp_path / "k"))  # fmt: skip
    assert got.returncode == 0, got.stderr
    cfg = k.config(box)
    assert cfg["sources"] == {
        "law": str(law.resolve()),
        "notes": "@" + str(lst.resolve()),
    }
    boot = k.read(box / "record.jsonl")[0][0]
    assert boot["pile_sha256"] == k.h256(str(pile.resolve()))
    assert boot["sources_sha256"] == k.h256(k.canon(cfg["sources"]))
    assert [c["path"] for c in k.pile_of_box(cfg)] == [
        "garden.md",
        "law/charter.md",
        "notes/roof.md",
    ]
    said = json.loads(cli("bite", *b, "when is the shed painted").stdout)
    assert [x["where"] for x in said["served"]] == ["law/charter.md:1"]
    # sources alone, no pile folder
    only = tmp_path / "only"
    got = cli(
        "init", "--box", str(only), "--from", f"law={law}", "--key", str(tmp_path / "k")
    )
    assert got.returncode == 0, got.stderr
    assert "pile" not in k.config(only)
    assert [c["path"] for c in k.pile_of_box(k.config(only))] == ["law/charter.md"]


def test_a_box_of_one_folder_reads_as_it_always_has(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text(
        "Tomatoes want six hours of sun.\n\nWater at the root.\n"
    )
    box = tmp_path / "box"
    assert (
        cli(
            "init", "--box", str(box), "--pile", str(pile), "--key", str(tmp_path / "k")
        ).returncode
        == 0
    )
    cfg = k.config(box)
    assert set(cfg) == {"key", "pile"}
    assert k.pile_of_box(cfg) == k.chunks(pile)
    assert k.folder(cfg) == Path(cfg["pile"])
    assert "sources_sha256" not in k.read(box / "record.jsonl")[0][0]


def test_a_reader_of_one_folder_refuses_a_box_of_sources(tmp_path):
    law = tmp_path / "law"
    law.mkdir()
    with pytest.raises(ValueError, match="CONST-VI-9"):
        k.folder({"key": "k", "pile": str(tmp_path), "sources": {"law": str(law)}})
    with pytest.raises(ValueError, match="CONST-VI-9"):
        k.folder({"key": "k", "sources": {"law": str(law)}})


@pytest.mark.parametrize(
    "froms, why",
    [
        (["law"], "a source is NAME=FOLDER or NAME=@LIST"),
        (["a/b={law}"], "a source's name is plain"),
        ([".x={law}"], "a source's name is plain"),
        (["law={law}", "law={law}"], "a source's name is given once"),
        (["law={tmp}/none"], "is not a folder"),
        (["law=@{tmp}/none.txt"], "a list of files is a file, and isn't there"),
        (["law=@{gone}"], "names 1 file that aren't there"),
        (["garden.md={law}"], "the pile already holds that name at its top"),
    ],
)
def test_a_bad_source_is_refused_and_no_box_is_made(tmp_path, froms, why):
    pile, law = tmp_path / "pile", tmp_path / "law"
    pile.mkdir()
    law.mkdir()
    (pile / "garden.md").write_text("Sun.\n")
    gone = tmp_path / "gone.txt"
    gone.write_text(f"{tmp_path / 'missing.md'}\n")
    box = tmp_path / "box"
    args = [
        x for f in froms for x in ("--from", f.format(law=law, tmp=tmp_path, gone=gone))
    ]
    got = cli(
        "init",
        "--box",
        str(box),
        "--pile",
        str(pile),
        *args,
        "--key",
        str(tmp_path / "k"),
    )
    assert got.returncode == 2 and why in got.stderr, got.stderr
    assert not (box / "k.json").exists()


def test_a_source_is_named_only_when_the_box_is_made(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    box = tmp_path / "box"
    cli("init", "--box", str(box), "--pile", str(pile), "--key", str(tmp_path / "k"))
    got = cli("bite", "--box", str(box), "--from", f"x={pile}", "a question")
    assert got.returncode == 2


def _newest_by_hand(text: str) -> str:
    """`newest` as it was read before it skipped ahead: one character at a
    time, every one asked whether a web address or a digit starts there.
    The reference the faster one must always agree with."""
    best, i = "", 0
    while i < len(text):
        if url := k._web_address(text, i):
            i += url
            continue
        n = k._digits(text, i)
        if n == 0:
            i += 1
            continue
        got = ""
        if n == 8:
            got = k._date(text[i : i + 4], text[i + 4 : i + 6], text[i + 6 : i + 8])
        elif n == 4 and text[i + 4 : i + 5] == "-" and k._digits(text, i + 5) == 2:
            if text[i + 7 : i + 8] == "-" and k._digits(text, i + 8) == 2:
                got = k._date(
                    text[i : i + 4], text[i + 5 : i + 7], text[i + 8 : i + 10]
                )
                if got:
                    n = 10
        elif n <= 2 and (sep := text[i + n : i + n + 1]) in ("/", "."):
            m = k._digits(text, i + n + 1)
            j = i + n + 1 + m
            if 1 <= m <= 2 and text[j : j + 1] == sep and k._digits(text, j + 1) == 4:
                got = k._day_month(
                    text[i : i + n], text[i + n + 1 : j], text[j + 1 : j + 5]
                )
                if got:
                    n = j + 5 - i
        best = max(best, got)
        i += n
    return best


def test_newest_skipping_ahead_reads_every_date_reading_by_hand_does():
    """newest jumps to the next digit or web address; on 40,000 strings of
    the characters dates and addresses are made of, it says what reading
    every character says (checked on cpython's 710,290 passages too)."""
    import random

    rng = random.Random(20261126)
    alpha = "0123456789-/. aZ:\n٣"  # an Arabic-Indic digit is no ASCII digit
    for _ in range(40000):
        s = "".join(rng.choice(alpha) for _ in range(rng.randint(0, 30)))
        if rng.random() < 0.2:
            at = rng.randint(0, len(s))
            s = s[:at] + rng.choice(["http://", "https://", "http:/"]) + s[at:]
        assert k.newest(s) == _newest_by_hand(s), repr(s)
    for s in (
        "see https://x.org/2026-10-14 then 2025-01-02",
        "20261014",
        "1/13/2026",
        "no digits here at all",
        "",
        "http://",
        "2026-10-14https://a 2027-01-01",
    ):
        assert k.newest(s) == _newest_by_hand(s), s


def test_a_words_plain_form_is_the_same_kept_or_worked_out():
    words = ["owes", "owing", "owed", "feed", "running", "planned", "flies",
             "café", "A1B2", "is", "classes", "studied"]  # fmt: skip
    k._STEMS.clear()
    first = [k.stem(w) for w in words]
    assert first == [k._stem(w) for w in words]
    assert [k.stem(w) for w in words] == first  # now from what was kept
    most = k._STEMS_MOST
    try:
        k._STEMS_MOST = 3
        k._STEMS.clear()
        for w in words:
            k.stem(w)
        assert len(k._STEMS) <= 3
    finally:
        k._STEMS_MOST = most


# ── the key pair (docs/design/key-pair.md) ──────────────────────────────────
#: RFC 8032, section 7.1: the private half, the public half, the message, the signature
RFC8032 = [
    ("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
     "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", "",
     "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
     "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
    ("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
     "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", "72",
     "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
     "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
    ("c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
     "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025", "af82",
     "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac"
     "18ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a"),
]  # fmt: skip
#: the eight points of small order, as their canonical 32 bytes
SMALL = [
    "0100000000000000000000000000000000000000000000000000000000000000",
    "ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f",
    "0000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000000000000000000000000000000000000000080",
    "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05",
    "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85",
    "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a",
    "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa",
]


def test_the_key_pair_signs_and_checks_as_rfc_8032_says():
    for seed, pub, msg, sig in RFC8032:
        seed, pub, msg, sig = (bytes.fromhex(x) for x in (seed, pub, msg, sig))
        assert k.ed_public(seed) == pub and k.ed_sign(seed, msg) == sig
        assert k.ed_check(pub, msg, sig)
        assert not k.ed_check(pub, msg + b"x", sig)
        assert not k.ed_check(pub, msg, sig[:63] + bytes([sig[63] ^ 1]))


def test_the_rule_refuses_what_libraries_disagree_on():
    """One rule in every port, so none takes what another refuses: S of L or
    more, a y of p or more, a point of small order for A or R, and a public
    half that is no point of prime order."""
    seed, pub, msg, sig = (bytes.fromhex(x) for x in RFC8032[1])
    s = int.from_bytes(sig[32:], "little")
    assert not k.ed_check(pub, msg, sig[:32] + (s + k.ED_L).to_bytes(32, "little"))
    for small in SMALL:
        small = bytes.fromhex(small)
        assert k.ed_point(small) is None
        assert not k.ed_check(small, msg, sig)  # as A
        assert not k.ed_check(pub, msg, small + sig[32:])  # as R
        assert k.pub_of({"pub": small.hex()}) is None
    # y = p + 1 names the point y = 1 again, written another way
    assert k.ed_point((k.ED_P + 1).to_bytes(32, "little")) is None
    assert k.pub_of({"pub": pub.hex()}) == pub
    for junk in ("", "zz", pub.hex()[:-2], None, 7):
        assert k.pub_of({"pub": junk}) is None
    assert k.pub_of({}) is None


class Paired:
    """A box with an answer sealed and one declined under the HMAC key, as
    every box has been until now."""

    def __init__(self, tmp_path: Path):
        self.tmp = tmp_path
        pile, self.box = tmp_path / "pile", tmp_path / "box"
        self.key, self.new = tmp_path / "keys" / "me.key", tmp_path / "keys" / "me.pair"
        pile.mkdir()
        (pile / "notes.md").write_text("The bus leaves at seven from the square.\n")
        self.b = ["--box", str(self.box), "--now", "2026-11-27T00:00:00Z"]
        cli("init", *self.b, "--pile", str(pile), "--key", str(self.key))
        got = cli("bite", *self.b, "when does the bus leave the square")
        self.cite = json.loads(got.stdout)["served"][0]["id"]
        self.old, no = self.offer("bus.md", "Seven."), self.offer("ferry.md", "Noon.")
        assert cli("seal", *self.b, self.old).returncode == 0
        assert cli("decline", *self.b, no).returncode == 0
        self.no = no

    def offer(self, path: str, data: str) -> str:
        prop = {"path": path, "data": data, "cites": [self.cite], "claim": "notes.md"}
        f = self.tmp / "rows.jsonl"
        f.write_text(json.dumps(prop) + "\n")
        cli("propose", *self.b, "--file", str(f))
        return k.subject_of(prop)

    def rows(self) -> list[dict]:
        return [
            json.loads(x) for x in (self.box / "record.jsonl").read_text().splitlines()
        ]

    def cfg(self) -> dict:
        return json.loads((self.box / "kernel.json").read_text())

    def verify(self) -> tuple[int, str]:
        got = cli("verify", "--box", str(self.box))
        return got.returncode, got.stdout.strip()


def test_a_box_given_a_key_pair_signs_beside_its_old_seals(tmp_path):
    """pair: a private half in a new file of the person's, the public half in
    the box. A seal from here is signed (`sig`) and one from before keeps its
    HMAC (`proof`), each row one or the other, and both hold."""
    p = Paired(tmp_path)
    got = cli("pair", *p.b, "--key", str(p.new))
    assert got.returncode == 0 and "paired" in got.stdout, got.stderr
    cfg = p.cfg()
    seed = bytes.fromhex(p.new.read_text().strip())
    assert cfg["pub"] == k.ed_public(seed).hex() and len(seed) == 32
    assert cfg["key"] == str(p.new) and cfg["old_key"] == str(p.key)
    assert p.new.stat().st_mode & 0o777 == 0o600
    assert p.rows()[-1]["kind"] == "pair" and p.rows()[-1]["pub"] == cfg["pub"]
    new, no = p.offer("tram.md", "Eight."), p.offer("boat.md", "Nine.")
    assert cli("seal", *p.b, new).returncode == 0
    assert cli("decline", *p.b, no).returncode == 0
    by = {r.get("subject"): r for r in p.rows() if r["kind"] in ("seal", "decline")}
    assert "sig" in by[new] and "proof" not in by[new] and "sig" in by[no]
    assert "proof" in by[p.old] and "sig" not in by[p.old]
    assert k.ed_check(bytes.fromhex(cfg["pub"]),
                      k.said(new, "seal", by[new]["bite_key"]),
                      bytes.fromhex(by[new]["sig"]))  # fmt: skip
    assert p.verify() == (0, f"the chain holds: {len(p.rows())} rows, 2 sealed")
    # a second pair, a key already there, a key in the box: each refused
    for key, why in ((tmp_path / "keys" / "x", "already has a key pair"),):
        got = cli("pair", *p.b, "--key", str(key))
        assert got.returncode == 2 and why in got.stderr and not key.exists()


def test_pair_makes_its_own_key_and_never_takes_one(tmp_path):
    p = Paired(tmp_path)
    for key, why in ((p.key, "is already there"), (p.box / "k", "inside the box")):
        got = cli("pair", *p.b, "--key", str(key))
        assert got.returncode == 2 and why in got.stderr
    assert "pub" not in p.cfg() and p.rows()[-1]["kind"] != "pair"


def test_a_signed_seal_is_checked_without_any_secret(tmp_path):
    """What the pair is for: the private half can be where the one who asks
    can't read it. Checking a signed seal reads no key at all."""
    p = Paired(tmp_path)
    cli("pair", *p.b, "--key", str(p.new))
    new = p.offer("tram.md", "Eight.")
    assert cli("seal", *p.b, new).returncode == 0
    assert cli("rekey", *p.b).returncode == 0
    more = p.offer("boat.md", "Nine.")
    p.new.unlink()
    p.key.unlink()
    assert p.verify() == (0, f"the chain holds: {len(p.rows())} rows, 2 sealed")
    got = cli("bite", *p.b, "when does the bus leave the square")
    assert got.returncode == 0 and "Seven." in got.stdout
    # and nothing is sealed without it
    got = cli("seal", *p.b, more)
    assert got.returncode == 2 and "the key could not be read" in got.stderr


def test_a_forged_signature_or_another_key_never_seals(tmp_path):
    p = Paired(tmp_path)
    cli("pair", *p.b, "--key", str(p.new))
    new = p.offer("tram.md", "Eight.")
    # the old secret is no private half: it signs nothing here
    cfg = p.cfg()
    (p.box / "kernel.json").write_text(json.dumps({**cfg, "key": cfg["old_key"]}))
    got = cli("seal", *p.b, new)
    assert got.returncode == 2 and "not the private half" in got.stderr
    (p.box / "kernel.json").write_text(json.dumps(cfg))
    assert cli("seal", *p.b, new).returncode == 0
    rows = p.rows()
    seal = rows[-1]
    good = k.sealed(p.box, rows)
    assert new in good
    for change in (
        {"sig": seal["sig"][:-2] + ("00" if seal["sig"][-2:] != "00" else "01")},
        {"sig": "zz"}, {"sig": None}, {"sig": ""},
        {"proof": "0" * 64},  # a row has one or the other
        {"bite_key": "0" * 64},  # the question is signed too
        {"subject": p.no},
    ):  # fmt: skip
        forged = [*rows[:-1], {**seal, **change}]
        assert seal["subject"] not in k.sealed(p.box, forged) or change.get("subject")
        assert {**seal, **change}["subject"] not in k.sealed(p.box, forged)
    # an HMAC row after the pair still needs the old secret, and a signature
    # made with another pair's private half is not this box's
    other = k.ed_sign(b"\x07" * 32, k.said(new, "seal", seal["bite_key"])).hex()
    assert new not in k.sealed(p.box, [*rows[:-1], {**seal, "sig": other}])


def test_the_crossing_vouches_for_old_seals_and_retires_the_old_key(tmp_path):
    """rekey: one row, signed with the new private half over the chain's tip
    and the numbers of the rows it found proved under the old secret. After
    it they stand on that row, and the box no longer names the old key."""
    p = Paired(tmp_path)
    got = cli("rekey", *p.b)
    assert got.returncode == 2 and "crosses once, after `pair`" in got.stderr
    cli("pair", *p.b, "--key", str(p.new))
    before = p.rows()
    got = cli("rekey", *p.b)
    assert got.returncode == 0, got.stderr
    assert "crossed: 1 seals and 1 declines" in got.stdout and str(p.key) in got.stdout
    row = p.rows()[-1]
    seal_n = next(r["n"] for r in before if r["kind"] == "seal")
    no_n = next(r["n"] for r in before if r["kind"] == "decline")
    assert (row["kind"], row["seal"], row["decline"]) == ("rekey", [seal_n], [no_n])
    assert row["tip"] == before[-1]["hash"] and "old_key" not in p.cfg()
    assert cli("rekey", *p.b).returncode == 2  # once
    rows = p.rows()
    assert p.old in k.sealed(p.box, rows) and p.no in k.declined(p.box, rows)
    # the row vouches by number for what the chain held: change what it
    # names, or sign less than it says, and the old seals fall with it
    for change in ({"seal": []}, {"decline": []}, {"tip": "0" * 64},
                   {"seal": [seal_n, no_n]}, {"sig": "00" * 64}):  # fmt: skip
        forged = [*rows[:-1], {**row, **change}]
        assert p.old not in k.sealed(p.box, forged), change
    # an HMAC seal written after the crossing proves nothing, old secret or not
    secret = bytes.fromhex(p.key.read_text().strip())
    was = next(r for r in before if r["n"] == seal_n)
    late = {**was, "n": row["n"] + 1,
            "proof": k.proof(secret, p.old, "seal", was["bite_key"])}  # fmt: skip
    assert k.proved(p.box, [*rows, late]) == [was]


def test_a_crossing_refuses_to_vouch_for_a_forgery(tmp_path):
    p = Paired(tmp_path)
    cli("pair", *p.b, "--key", str(p.new))
    p.key.write_text("00" * 32 + "\n")  # not the secret the old seals were made with
    p.key.chmod(0o600)
    got = cli("rekey", *p.b)
    assert got.returncode == 2 and "don't prove under your old key" in got.stderr
    assert p.rows()[-1]["kind"] == "pair" and "old_key" in p.cfg()


def test_a_check_is_remembered_within_a_run_and_never_on_disk(tmp_path, monkeypatch):
    p = Paired(tmp_path)
    cli("pair", *p.b, "--key", str(p.new))
    new = p.offer("tram.md", "Eight.")
    cli("seal", *p.b, new)
    files = sorted(x.name for x in p.box.rglob("*"))
    calls = []
    real = k.ed_check
    monkeypatch.setattr(k, "ed_check", lambda *a: calls.append(a) or real(*a))
    k.ED_CHECKED.clear()
    rows = p.rows()
    assert new in k.sealed(p.box, rows) and new in k.sealed(p.box, rows)
    assert len(calls) == 1
    assert sorted(x.name for x in p.box.rglob("*")) == files


def test_a_question_checks_only_the_seals_that_could_answer_it(tmp_path, monkeypatch):
    """A signature check is slow beside an HMAC, and a record gathers seals.
    bite checks the ones that name its question, one or none, whatever the
    record's size; verify still checks every one."""
    p = Paired(tmp_path)
    (tmp_path / "pile" / "more.md").write_text(
        "The ferry sails at noon from the quay.\nThe tram runs at eight to the park.\n")  # fmt: skip
    cli("pair", *p.b, "--key", str(p.new))
    for ask, path, data in (("when does the ferry sail from the quay", "f.md", "Noon."),
                            ("when does the tram run to the park", "t.md", "Eight.")):  # fmt: skip
        got = cli("bite", *p.b, ask)
        p.cite = json.loads(got.stdout)["served"][0]["id"]
        assert cli("seal", *p.b, p.offer(path, data)).returncode == 0
    rows, calls, real = p.rows(), [], k.ed_check
    monkeypatch.setattr(k, "ed_check", lambda *a: calls.append(a) or real(*a))
    k.ED_CHECKED.clear()
    ferry = k.bite_key("when does the ferry sail from the quay")
    assert len(k.sealed(p.box, rows, only=ferry)) == 1 and len(calls) == 1
    assert k.sealed(p.box, rows, only=k.bite_key("no such question")) == {}
    assert len(calls) == 1
    assert len(k.sealed(p.box, rows)) == 3 and len(calls) == 2
    got = cli("bite", *p.b, "When does the ferry sail from the quay?")
    assert json.loads(got.stdout)["answer"] == "Noon."
    got = cli("bite", *p.b, "when does the tram run to the park")
    assert json.loads(got.stdout)["answer"] == "Eight."


def test_the_rule_answers_its_vectors():
    """vectors/ed25519.json: what the rule says of each signature a library
    might take and another refuse, for every port to answer the same."""
    doc = json.loads((HERE.parent / "vectors" / "ed25519.json").read_text())
    cases = doc["cases"]["rule"]
    assert len(cases) > 100 and {c["why"] for c in cases} >= {
        "rfc 8032", "S plus L", "a key of small order", "an R of small order",
        "a key of mixed order", "an R of mixed order", "a key written another way"}  # fmt: skip
    for c in cases:
        pub, msg, sig = (bytes.fromhex(c[x]) for x in ("pub", "msg", "sig"))
        assert k.ed_check(pub, msg, sig) is c["takes"], c["why"]
        assert (k.pub_of({"pub": c["pub"]}) is not None) is c["key"], c["why"]
    # a signature is a seal only when both hold: nothing of mixed order is
    assert all(
        c["why"] in ("rfc 8032", "signed") for c in cases if c["takes"] and c["key"]
    )


def test_a_box_that_names_no_key_is_no_box_to_read_seals_from(tmp_path):
    """As before the pair: settings with no key raise, whatever the record
    holds, so what lists boxes says such a one can't be read (boxes-here)."""
    (tmp_path / "kernel.json").write_text("{}")
    with pytest.raises(KeyError):
        k.sealed(tmp_path, [])
