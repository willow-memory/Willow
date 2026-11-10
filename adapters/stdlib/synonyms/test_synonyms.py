"""synonyms: for a word no file holds, the dictionary's other words that the
files do hold, as words-list lines; nothing installed, nothing written, and
an embedder asked only on this machine."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("synonyms", HERE / "synonyms.py")
sy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sy)
NOW = ["--now", "2026-11-09T00:00:00Z"]

#: a WordNet of six meanings, in its own files' shape: kind, then the words
MEANINGS = [
    ("verb", ["postpone", "table", "shelve", "defer", "put_off"]),
    ("verb", ["table", "tabularize"]),
    ("noun", ["table", "tabular_array"]),
    ("noun", ["gap", "opening", "crack"]),
    ("adj", ["big(a)", "large", "Big"]),
    ("adv", ["later", "afterwards"]),
]


def make_dict(folder: Path, meanings=MEANINGS, licence: bool = True) -> Path:
    """WordNet's eight files for `meanings`, each data line at the byte the
    index says, under the licence lines every real file opens with."""
    folder.mkdir(parents=True, exist_ok=True)
    top = (
        "  1 This software and database is being provided to you\n  2 \n"
        if licence
        else ""
    )
    for kind in sy.KINDS:
        data = top.encode()
        where: dict[str, list[int]] = {}
        for k, words in meanings:
            if k != kind:
                continue
            at = len(data)
            pairs = " ".join(f"{w} 0" for w in words)
            line = f"{at:08d} 29 {kind[0]} {len(words):02x} {pairs} 000 | a gloss\n"
            data += line.encode()
            for w in words:
                where.setdefault(w.split("(")[0].lower(), []).append(at)
        (folder / f"data.{kind}").write_bytes(data)
        index = top + "".join(
            f"{w} {kind[0]} {len(ats)} 2 @ ~ {len(ats)} 0 "
            + " ".join(f"{a:08d}" for a in ats)
            + "  \n"
            for w, ats in sorted(where.items())
        )
        (folder / f"index.{kind}").write_text(index, encoding="utf-8")
    return folder


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HERE / "synonyms.py"), *argv],
        capture_output=True,
        text=True,
    )


@pytest.fixture
def made(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "plan.txt").write_text(
        "We defer the palette.\n\nThe table shows rows.\n\nAnother table of cracks, large.\n"
    )
    (pile / "notes.txt").write_text("A table again, and a crack in it.\n")
    box = tmp_path / "box"
    assert k("init", "--box", str(box), "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW).returncode == 0  # fmt: skip
    return box, make_dict(tmp_path / "dict"), pile


def test_a_bad_command_line_is_refused_and_names_the_script(made):
    box, data, _ = made
    b, d = ["--box", str(box)], ["--data", str(data)]
    for argv in (
        [],
        [*b, "a question"],
        [*d, "a question"],
        [*b, *d],
        [*b, *d, "one", "two"],
        [*b, *d, "--nope"],
        [*b, *d, "q", "--questions", str(data)],
        [*b, *d, "q", "--url", "http://127.0.0.1:1/v1"],
        [*b, *d, "q", "--embed"],
    ):
        got = run(*argv)
        assert (
            got.returncode == 2 and "synonyms.py" in got.stderr and got.stdout == ""
        ), argv


def test_a_word_no_file_holds_is_read_as_the_dictionarys_words_the_files_do(made):
    box, data, _ = made
    got = run(
        "--box", str(box), "--data", str(data), "what was Postponed, and the gaps"
    )
    # table is in three passages, defer in one; shelve and put_off in none;
    # gaps is gap with its ending off, and the files hold crack, twice
    assert got.stdout == "postponed = table, defer\ngaps = crack\n"
    assert got.returncode == 0 and got.stderr == ""
    rows = (box / "record.jsonl").read_text().splitlines()
    assert len(rows) == 1  # read only: not even the record


def test_a_word_the_dictionary_cant_help_is_a_note_and_42(made):
    box, data, _ = made
    got = run(
        "--box",
        str(box),
        "--data",
        str(data),
        "tabularize it afterwards, zzyzx, shelve",
    )
    assert got.stdout == (
        "tabularize = table\n"
        "shelve = table, defer\n"
        "# afterwards: no file holds it, nor any of the dictionary's 1 other word for it\n"
        "# zzyzx: no file holds it, and the dictionary has no other word for it\n"
    )
    assert got.returncode == 42
    two = run("--box", str(box), "--data", str(data), "big")
    assert two.stdout == "big = large\n" and two.returncode == 0


def test_words_the_files_hold_and_common_words_get_nothing(made):
    box, data, _ = made
    got = run("--box", str(box), "--data", str(data), "the table and a crack")
    assert got.stdout == "# your files hold every word of it; nothing to suggest\n"
    assert got.returncode == 0


def test_a_words_list_already_reading_a_word_leaves_it_alone(tmp_path, made):
    _, data, pile = made
    words = tmp_path / "words.txt"
    words.write_text("postponed = defer\n")
    words.chmod(0o600)
    box = tmp_path / "box2"
    assert k("init", "--box", str(box), "--pile", str(pile), "--key", str(tmp_path / "k2"), "--words", str(words), *NOW).returncode == 0  # fmt: skip
    got = run("--box", str(box), "--data", str(data), "postponed gaps")
    assert got.stdout == "gaps = crack\n"
    words.chmod(0o644)
    got = run("--box", str(box), "--data", str(data), "postponed gaps")
    assert got.returncode == 2 and "chmod 600" in got.stderr and got.stdout == ""


def test_a_file_of_questions_is_read_each_word_once(tmp_path, made):
    box, data, _ = made
    q = tmp_path / "q.txt"
    q.write_text(
        "# a note\n\nfirst\twhat was postponed\nwhat was postponed, the gaps\n"
    )
    got = run("--box", str(box), "--data", str(data), "--questions", str(q))
    assert (
        got.stdout == "postponed = table, defer\ngaps = crack\n" and got.returncode == 0
    )
    assert sy.questions(q) == ["what was postponed", "what was postponed, the gaps"]
    # only the first tab parts a name from its question
    q.write_text("n\tpostponed\tgaps\n")
    assert sy.questions(q) == ["postponed\tgaps"]
    q.write_text(
        "# a note\n\nfirst\twhat was postponed\nwhat was postponed, the gaps\n"
    )
    missing = run(
        "--box", str(box), "--data", str(data), "--questions", str(tmp_path / "no")
    )
    assert (
        missing.returncode == 2
        and "could not be read: FileNotFoundError" in missing.stderr
    )
    q.write_text("# only a note\n")
    empty = run("--box", str(box), "--data", str(data), "--questions", str(q))
    assert empty.returncode == 2 and "no words" in empty.stderr


def test_what_isnt_a_box_or_a_dictionary_is_refused_by_name(tmp_path, made):
    box, data, _ = made
    got = run("--box", str(tmp_path), "--data", str(data), "postponed")
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    (data / "data.adv").unlink()
    (data / "index.noun").unlink()
    got = run("--box", str(box), "--data", str(data), "postponed")
    assert got.returncode == 2 and got.stdout == ""
    assert (
        f"{data} isn't WordNet's database; it has no index.noun, data.adv" in got.stderr
    )
    assert sy.Dictionary.missing(tmp_path / "nowhere") == [
        f"{part}.{kind}" for kind in sy.KINDS for part in ("index", "data")
    ]
    with (box / "record.jsonl").open("a") as f:
        f.write("{}\n")
    make_dict(data)
    got = run("--box", str(box), "--data", str(data), "postponed")
    assert got.returncode == 2 and got.stderr.startswith("refused:")


def test_the_dictionary_is_read_as_wordnet_writes_it(tmp_path):
    wn = sy.Dictionary(make_dict(tmp_path / "d"))
    assert wn.index["noun"]["table"] == [wn.index["noun"]["tabular_array"][0]]
    assert len(wn.index["verb"]["table"]) == 2 and "1" not in wn.index["noun"]
    assert wn.bases("gaps", "noun") == ["gap"] and wn.bases("gap", "noun") == ["gap"]
    assert wn.bases("tables", "verb") == ["table"] and wn.bases("s", "noun") == []
    assert wn.bases("postponed", "verb") == ["postpone"]
    assert wn.bases("tabling", "verb") == ["table"] and wn.bases("later", "adv") == [
        "later"
    ]
    assert wn.bases("larger", "adj") == ["large"] and wn.bases("bigs", "adj") == []
    # the most used meaning's words first, phrases left out, the word and its base never
    assert wn.others("postponed") == ["table", "shelve", "defer"]
    assert wn.others("table") == ["postpone", "shelve", "defer", "tabularize"]
    assert wn.others("large") == ["big"] and wn.others("nothing") == []
    assert sy.Dictionary(make_dict(tmp_path / "bare", licence=False)).others("gap") == [
        "opening",
        "crack",
    ]


def test_passages_are_counted_as_the_kernel_holds_words():
    held = sy.passages(
        [
            {"text": "A table. Tables!", "path": "a.txt"},
            {"text": "one table", "path": "b/table.md"},
        ]
    )
    assert (
        held["table"] == 2 and held["a"] == 1 and held["b"] == 1 and "zebra" not in held
    )


class Embedder(BaseHTTPRequestHandler):
    """An embedder on 127.0.0.1 that knows four words, and counts its calls."""

    known = {
        "postponed": [1.0, 0.0],
        "defer": [0.9, 0.1],
        "table": [0.0, 1.0],
        "tabularize": [0, 0],
    }
    calls: list = []
    answer = "ok"

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Embedder.calls.append((self.path, body))
        rows = [{"embedding": self.known.get(t, [0.5, 0.5])} for t in body["input"]]
        doc = {"data": rows} if Embedder.answer == "ok" else {"data": rows[:1]}
        if Embedder.answer == "odd":
            doc = {"error": "no such model"}
        out = json.dumps(doc).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


@pytest.fixture
def embedder():
    server = HTTPServer(("127.0.0.1", 0), Embedder)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    Embedder.calls, Embedder.answer = [], "ok"
    yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    server.shutdown()


def test_an_embedder_on_this_machine_puts_the_nearest_word_first(made, embedder):
    box, data, _ = made
    got = run(
        "--box",
        str(box),
        "--data",
        str(data),
        "--embed",
        "m1",
        "--url",
        embedder + "/",
        "postponed",
    )
    assert got.stdout == (
        "postponed = defer, table\n# each line's words are nearest in meaning first, by m1\n"
    )
    assert got.returncode == 0
    assert Embedder.calls == [
        ("/v1/embeddings", {"model": "m1", "input": ["postponed", "table", "defer"]})
    ]
    # nothing to order, nothing asked, and no line saying it was
    Embedder.calls.clear()
    got = run(
        "--box",
        str(box),
        "--data",
        str(data),
        "--embed",
        "m1",
        "--url",
        embedder,
        "zzyzx",
    )
    assert (
        got.stdout.startswith("# zzyzx")
        and "nearest" not in got.stdout
        and Embedder.calls == []
    )


def test_an_embedder_that_cant_be_asked_is_unreachable_not_a_guess(made, embedder):
    box, data, _ = made
    for answer in ("short", "odd"):
        Embedder.answer = answer
        got = run(
            "--box",
            str(box),
            "--data",
            str(data),
            "--embed",
            "m1",
            "--url",
            embedder,
            "postponed",
        )
        assert got.returncode == 42 and got.stdout == ""
        assert got.stderr.startswith(
            f"unreachable: m1 at {embedder} could not be asked ("
        )
    closed = "http://127.0.0.1:9/v1"
    got = run(
        "--box",
        str(box),
        "--data",
        str(data),
        "--embed",
        "m1",
        "--url",
        closed,
        "postponed",
    )
    assert got.returncode == 42 and got.stdout == "" and "without --embed" in got.stderr


def test_an_embedder_off_this_machine_is_refused_before_a_word_is_sent(made):
    box, data, _ = made
    for url in (
        "http://example.com/v1",
        "https://127.0.0.1/v1",
        "http://127.0.0.1.example.com/v1",
        "ftp://localhost/v1",
    ):
        got = run(
            "--box",
            str(box),
            "--data",
            str(data),
            "--embed",
            "m1",
            "--url",
            url,
            "postponed",
        )
        assert got.returncode == 2 and got.stdout == ""
        assert (
            got.stderr == f"refused: {url} is not on this machine; nothing was sent\n"
        )
    assert sy.here("http://localhost:11434/v1") and sy.here("http://[::1]:8080/v1")


def test_nearness_and_order():
    assert sy.nearness([1.0, 0.0], [2.0, 0.0]) == 1.0
    assert sy.nearness([1.0, 0.0], [0.0, 3.0]) == 0.0
    assert sy.nearness([1.0, 1.0], [-1.0, -1.0]) == pytest.approx(-1.0)
    assert sy.nearness([0.0, 0.0], [1.0, 0.0]) == 0.0
    vec = {"w": [1.0, 0.0], "a": [0.0, 1.0], "b": [1.0, 0.1], "c": [0.0, 1.0]}
    assert sy.nearest_first("w", ["a", "b", "c"], lambda ts: [vec[t] for t in ts]) == [
        "b",
        "a",
        "c",
    ]
