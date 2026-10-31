"""kernel.py, the smallest script for anyone: its eight beats hold, the whole
loop runs on the command line, and what it serves is what its rules say."""

from __future__ import annotations

import ast
import importlib.util
import json
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


def test_its_eight_beats_hold():
    p = cli("test")
    assert p.returncode == 0 and "eight beats held" in p.stdout, p.stderr


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
    doesn't prove is never counted (LIMITS.md asked for this verb)."""
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
    """Scores are exact (Fraction), so the set's walk order can't move them."""
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


def test_a_date_inside_a_web_address_dates_nothing():
    assert (
        k.newest("Nvidia rose 3% (https://example.com/snap/2026-10-24-nvda.html)") == ""
    )
    assert (
        k.newest("See http://example.com/20261024, then check 2026-10-25.")
        == "20261025"
    )


@pytest.mark.xfail(
    strict=True, reason="bug #96: propose exits 0 when every suggestion is refused"
)
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
    assert got.returncode != 0
