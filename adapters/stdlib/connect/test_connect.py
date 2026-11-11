"""connect: a model on this machine is asked one plain question about two
passages of the folder, and the part of its answer that can be checked is:
a number or a name neither passage holds is named, and so is an answer that
speaks of one passage only. Only this machine is asked; nothing is written."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "connect.py"
KERNEL = HERE.parents[2] / "kernel.py"
sys.path.insert(0, str(HERE))
import connect as cn  # noqa: E402

INVOICE = "overdue INV-2026-011 Larkfield Community Theatre $640.00 due 2026-06-27\n"
LOG = (
    "date,client,what,amount,invoice\n\n"
    "2026-05-28,Larkfield Community Theatre,service visit on the Wurlitzer,640.00,INV-2026-011\n"
)
TEXT = "[2021-08-16 14:11] Nell: made the goulash, it was ok, not grandma's\n"
GOOD = (
    "The first is an overdue invoice and the second is the service visit it "
    "bills: the same theatre, invoice INV-2026-011 and the amount, 640.00."
)


@pytest.fixture
def box(tmp_path):
    pile = tmp_path / "pile"
    (pile / "work").mkdir(parents=True)
    (pile / "invoices.txt").write_text(INVOICE)
    (pile / "work" / "log.csv").write_text(LOG)
    (pile / "texts.txt").write_text(TEXT)
    b = tmp_path / "box"
    subprocess.run(
        [sys.executable, str(KERNEL), "init", "--box", str(b), "--pile", str(pile),
         "--key", str(tmp_path / "k"), "--now", "2026-10-24T00:00:00Z"],
        check=True, capture_output=True,
    )  # fmt: skip
    return b


def go(*argv, ask=None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cn.main([str(a) for a in argv], ask)
    return code, out.getvalue(), err.getvalue()


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, argv)], capture_output=True, text=True
    )


def test_a_bad_command_line_is_refused_and_names_the_script(box, tmp_path):
    got = run()
    assert got.returncode == 2 and "connect.py" in got.stderr
    pairs = tmp_path / "p.txt"
    pairs.write_text("invoices.txt:1\twork/log.csv:3\n")
    a, b = "invoices.txt:1", "work/log.csv:3"
    for argv in (
        ["--first", a, "--second", b],  # no box
        ["--box", box],  # nothing to connect
        ["--box", box, "--first", a],  # one end
        ["--box", box, "--second", b],
        ["--box", box, "--first", a, "--second", b, "--pairs", pairs],  # both ways
        ["--box", box, "--first", a, "--second"],
        ["--box", box, "--first", a, "--second", b, "--chars", "many"],
        ["--box", box, "--first", a, "--second", b, "--chars", "10"],
        ["--box", box, "--first", a, "--second", b, "--timeout", "0"],
        ["--box", box, "--first", a, "--second", b, "--nope"],
    ):
        code, out, err = go(*argv)
        assert code == 2 and err.startswith("usage: connect.py") and out == "", argv


def test_what_cant_be_read_is_refused_and_says_what(box, tmp_path):
    a, b = "invoices.txt:1", "work/log.csv:3"
    code, _, err = go("--box", tmp_path, "--first", a, "--second", b)
    assert code == 2 and "not a kernel box" in err
    for bad in ("invoices.txt", "invoices.txt:0", ":3", "invoices.txt:x"):
        code, _, err = go("--box", box, "--first", bad, "--second", b)
        assert code == 2 and "isn't a place: a file, a colon, a line" in err, bad
    pairs = tmp_path / "p.txt"
    code, _, err = go("--box", box, "--pairs", pairs)
    assert code == 2 and "could not be read" in err
    pairs.write_text("# nothing\n\n")
    assert "it holds no pair" in go("--box", box, "--pairs", pairs)[2]
    pairs.write_text(f"{a}\t{b}\n{a} {b}\n")
    assert "line 2 isn't two places with a tab between them" in go("--box", box, "--pairs", pairs)[2]  # fmt: skip


def test_a_connection_is_said_with_both_passages_and_what_was_checked(box):
    asked = []
    code, out, err = go("--box", box, "--first", "invoices.txt:1", "--second", "work/log.csv:3",
                        "--json", ask=lambda p: asked.append(p) or GOOD)  # fmt: skip
    assert code == 0, err
    doc = json.loads(out)
    assert doc["addon"] == "connect" and doc["state"] == "populated"
    assert doc["said"] == (
        "1 pair: 1 connection said, every number and name in it is in the passages"
    )
    assert doc["groups"] == [{
        "name": "invoices.txt:1 and work/log.csv:3, by llama3.2:3b",
        "rows": [
            {"where": "invoices.txt:1", "what": INVOICE.strip()},
            {"where": "work/log.csv:3", "what": LOG.splitlines()[2]},
            {"where": "said", "what": GOOD},
            {"where": "checked", "what": "every number and name it gives is in one "
             "of the two passages, and it speaks of both"},
        ],
    }]  # fmt: skip
    # the model is asked one plain question, and nothing about format
    assert asked == [
        "What's the connection between these two?\n\n"
        f"First: {INVOICE.strip()}\n\nSecond: {LOG.splitlines()[2]}\n\n"
        "Answer in a few plain sentences, under 500 characters."
    ]


def test_chars_sets_how_short_and_a_model_tag_is_said(box):
    asked = []
    code, out, _ = go("--box", box, "--first", "invoices.txt:1", "--second", "work/log.csv:3",
                      "--chars", "250", "--model", "tiny:1b", ask=lambda p: asked.append(p) or GOOD)  # fmt: skip
    assert asked[0].endswith("under 250 characters.")
    assert "## invoices.txt:1 and work/log.csv:3, by tiny:1b" in out


def test_a_number_or_a_name_neither_passage_holds_is_named_and_flagged(box):
    bad = "Both are about the Larkfield Opera House, which owes Hollis $700 on INV-2026-011."
    code, out, _ = go("--box", box, "--first", "invoices.txt:1", "--second", "work/log.csv:3",
                      ask=lambda p: bad)  # fmt: skip
    assert code == 42
    assert "connect: populated, 1 pair: 1 connection said, 1 to look at" in out
    assert "checked         in neither passage: 700, Opera, House, Hollis" in out


def test_what_counts_as_added():
    a, b = INVOICE, LOG
    assert cn.added(GOOD, a, b) == []
    # a sentence's own capital names nothing; a name inside one does
    assert cn.added("Both name the same theatre. Neither says more.", a, b) == []
    assert cn.added("Both name Dunmore, and Marchetti signed it.", a, b) == ["Dunmore", "Marchetti"]  # fmt: skip
    # what it can't tell: a name that opens a sentence looks like any first word
    assert cn.added("Marchetti signed it.", a, b) == []
    # numbers are read without commas, and a year or an id counts as one
    assert cn.added("It was 640 in 2026, not 1,180.", a, b) == ["1180"]
    assert cn.added("Invoice INV-2026-011 and INV-2026-012.", a, b) == [
        "012",
        "INV-2026-012",
    ]
    # a possessive is the name's, and the question's own words are let be
    assert cn.added("The First is Larkfield's; the Second too.", a, b) == []
    assert cn.added("The Wurlitzer's visit, and Nell's.", a, b) == ["Nell"]


def test_an_answer_that_speaks_of_one_passage_only_is_named_and_flagged(box):
    only = "Nell made goulash and thought it was ok, though not like grandma's."
    code, out, _ = go("--box", box, "--first", "texts.txt:1", "--second", "work/log.csv:3",
                      ask=lambda p: only)  # fmt: skip
    assert code == 42
    assert "it speaks of nothing that is only in the second passage" in out
    none = "There is no direct connection between a meal and a service visit."
    assert cn.drawn_from(none, TEXT, LOG) == (False, True)
    assert cn.drawn_from(GOOD, INVOICE, LOG) == (True, True)
    # two passages that say the same have nothing of their own, and that is no fault
    said, extra, missed = cn.connect({"text": INVOICE}, {"text": INVOICE}, lambda p: "They are the same overdue invoice.")  # fmt: skip
    assert missed == "" and extra == []
    assert (
        cn.connect({"text": TEXT}, {"text": LOG}, lambda p: "Nothing much.")[2]
        == "either"
    )


def test_a_place_with_no_passage_is_said_and_not_asked(box):
    code, out, _ = go("--box", box, "--first", "invoices.txt:99", "--second", "gone.txt:1",
                      "--json", ask=lambda p: pytest.fail("nothing to ask about"))  # fmt: skip
    assert code == 42
    doc = json.loads(out)
    assert doc["said"] == "1 pair: 0 connections said, 1 to look at"
    assert doc["groups"][0]["name"] == "invoices.txt:99 and gone.txt:1: not asked"
    assert [r["what"] for r in doc["groups"][0]["rows"]] == [
        "no passage of your folder holds this line"
    ] * 2


def test_only_a_file_inside_your_folder_is_read(box, tmp_path):
    (tmp_path / "secret.txt").write_text("the key to everything\n")
    for bad in (
        "../secret.txt:1",
        f"{tmp_path}/secret.txt:1",
        "/etc/passwd:1",
        "../box/kernel.json:1",
    ):
        code, out, _ = go("--box", box, "--first", bad, "--second", "invoices.txt:1",
                          ask=lambda p: pytest.fail("not asked"))  # fmt: skip
        assert (
            code == 42 and "the key to everything" not in out and "root:" not in out
        ), bad
        assert "no passage of your folder holds this line" in out


def test_many_pairs_are_each_a_group_in_order(box, tmp_path):
    pairs = tmp_path / "p.txt"
    pairs.write_text(
        "# two\ninvoices.txt:1\twork/log.csv:3\n\ntexts.txt:1\twork/log.csv:3\n"
    )
    said = iter([GOOD, "Nell made goulash."])
    code, out, _ = go(
        "--box", box, "--pairs", pairs, "--json", ask=lambda p: next(said)
    )
    doc = json.loads(out)
    assert code == 42
    assert doc["said"] == "2 pairs: 2 connections said, 1 to look at"
    assert [g["name"].split(",")[0] for g in doc["groups"]] == [
        "invoices.txt:1 and work/log.csv:3", "texts.txt:1 and work/log.csv:3"]  # fmt: skip
    ok = iter([GOOD, GOOD.replace("first", "one").replace("second", "other")])
    pairs.write_text("invoices.txt:1\twork/log.csv:3\nwork/log.csv:3\tinvoices.txt:1\n")
    code, out, _ = go("--box", box, "--pairs", pairs, ask=lambda p: next(ok))
    assert code == 0
    assert (
        "2 pairs: 2 connections said, every number and name in them is in the passages"
        in out
    )


def test_a_long_passage_is_cut_on_its_row_and_given_whole_to_the_model(box, tmp_path):
    long = "The roofer came. " * 25
    (tmp_path / "pile" / "long.txt").write_text(long + "\n")
    asked = []
    code, out, _ = go("--box", box, "--first", "long.txt:1", "--second", "invoices.txt:1",
                      "--json", ask=lambda p: asked.append(p) or "The roofer and the overdue invoice.")  # fmt: skip
    row = json.loads(out)["groups"][0]["rows"][0]["what"]
    assert len(row) <= cn.SHOWN + 1 and row.endswith("…")
    assert long.strip() in asked[0]


class Ollama:
    def __init__(self, reply: str, status: int = 200):
        self.asked: list[dict] = []
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):  # noqa: N802
                n = int(self.headers.get("Content-Length") or 0)
                outer.asked.append(json.loads(self.rfile.read(n)))
                self.send_response(status)
                self.end_headers()
                self.wfile.write(json.dumps({"response": reply}).encode())

        self.server = HTTPServer(("127.0.0.1", 0), H)
        self.host = f"127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()


def test_the_model_on_this_machine_is_asked_as_say_asks_it(box):
    o = Ollama(GOOD)
    try:
        got = run("--box", box, "--first", "invoices.txt:1", "--second", "work/log.csv:3",
                  "--host", o.host, "--model", "tiny:1b", "--chars", "300")  # fmt: skip
        assert got.returncode == 0, got.stderr
        assert got.stdout.splitlines()[0] == (
            "connect: populated, 1 pair: 1 connection said, every number and name in it is in the passages"
        )
        (asked,) = o.asked
        assert asked["model"] == "tiny:1b" and asked["stream"] is False
        assert asked["options"] == {"temperature": 0, "num_predict": 140}
        assert asked["prompt"].startswith("What's the connection between these two?")
    finally:
        o.server.shutdown()
        o.server.server_close()


def test_a_model_that_cant_be_asked_is_unreachable_and_another_machine_is_never_asked(
    box,
):
    a, b = "invoices.txt:1", "work/log.csv:3"
    got = run("--box", box, "--first", a, "--second", b, "--host", "127.0.0.1:9")
    assert got.returncode == 42
    assert got.stdout.startswith(
        "connect: unreachable, llama3.2:3b at http://127.0.0.1:9: "
    )
    assert len(got.stdout.splitlines()) == 1
    got = run(
        "--box", box, "--first", a, "--second", b, "--host", "example.com", "--json"
    )
    doc = json.loads(got.stdout)
    assert (
        got.returncode == 42 and doc["state"] == "unreachable" and doc["groups"] == []
    )
    assert "is not this machine; not asked" in doc["said"]
    code, out, _ = go("--box", box, "--first", a, "--second", b, ask=lambda p: "  ")
    assert code == 42 and "connect: unreachable, llama3.2:3b said nothing" in out


def test_nothing_is_written(box, tmp_path):
    def now():
        return {p: p.read_bytes() for p in sorted(tmp_path.rglob("*")) if p.is_file()}

    before = now()
    go(
        "--box",
        box,
        "--first",
        "invoices.txt:1",
        "--second",
        "work/log.csv:3",
        ask=lambda p: GOOD,
    )
    go("--box", box, "--first", "invoices.txt:1", "--second", "gone.txt:1")
    assert now() == before
