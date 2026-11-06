"""sort-ask: each file sort didn't place is bitten on, a model on this machine
is asked in labelled facts, and only an answer naming a category of yours and
citing a served passage reaches the door; it never places, never asks off this
machine, and doesn't ask twice. The model here is a stand-in server on
127.0.0.1, so nothing needs a real one."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "sort_ask.py"
NOW = ["--now", "2026-11-03T00:00:00Z"]
spec = importlib.util.spec_from_file_location("sort_ask", SCRIPT)
sa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sa)
CATS = "garden: tomatoes, basil\nhealth: doctor, clinic\n"


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


#: every request a stand-in model was sent, in order
SENT: list[dict] = []


def model(replies: dict[str, str]):
    """A stand-in model: the first reply whose key is in the file's place."""
    asked: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            user = body["messages"][-1]["content"]
            assert (body["temperature"], body["seed"]) == (0, 7), "sort-ask's own seed"
            SENT.append(body)
            asked.append(user)
            text = next((r for k, r in replies.items() if f"File: {k}" in user), "NONE")
            out = json.dumps({"choices": [{"message": {"content": text}}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/v1", asked


def box(tmp_path: Path, files: dict[str, str]) -> tuple[Path, Path]:
    pile = tmp_path / "pile"
    pile.mkdir()
    for rel, text in files.items():
        (pile / rel).write_text(text)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(pile), "--key",
        str(tmp_path / "k"), *NOW)  # fmt: skip
    cats = tmp_path / "categories.txt"
    cats.write_text(CATS)
    return b, cats


FILES = {
    "allotment.txt": "Watered the courgettes and picked the first runner beans.\n",
    "note.txt": "Booked the dentist for Tuesday; the refill is due Friday.\n",
    "beds.txt": "The tomatoes went in beside the basil.\n",
    "misc.txt": "A list of train times for the weekend.\n",
}


def test_a_suggestion_cites_a_served_passage_and_waits_for_a_seal(tmp_path):
    b, cats = box(tmp_path, FILES)
    srv, url, asked = model({"allotment.txt": "CATEGORY garden [1]", "note.txt": "Health [1]",
                             "misc.txt": "NONE"})  # fmt: skip
    try:
        got = run(str(SCRIPT), "--box", str(b), "--categories", str(cats), "--model", "m",
                  "--url", url, *NOW)  # fmt: skip
        assert got.returncode == 42, got.stderr
        assert got.stdout.splitlines() == [
            "sort-ask: populated, 2 suggestions of 3 files asked about, by m",
            "## suggested",
            "  allotment.txt  garden  (waits on your seal)",
            "  note.txt       health  (waits on your seal)",
            "## not suggested",
            "  misc.txt       no category of yours, cited: NONE",
        ]
        assert len(asked) == 3, "beds.txt is placed by its phrases: never asked"
        assert (
            "garden: tomatoes, basil" in asked[0] and "File: allotment.txt" in asked[0]
        )
        rows = [
            json.loads(p.read_text()) for p in sorted((b / "proposals").glob("*.json"))
        ]
        assert sorted((r["path"], r["data"]) for r in rows) == [
            ("sort/allotment.txt.txt", "garden\n"),
            ("sort/note.txt.txt", "health\n"),
        ]
        assert all(
            len(r["cites"]) == 1
            and re.fullmatch(
                rf"m at {re.escape(url)} \(temperature 0, seed 7\) read"
                r" \S+ as (garden|health), from the passage it cited",
                r["claim"],
            )  # fmt: skip
            for r in rows
        )
        again = run(str(SCRIPT), "--box", str(b), "--categories", str(cats), "--model", "m",
                    "--url", url, *NOW, "--json")  # fmt: skip
        doc = json.loads(again.stdout)
        assert len(asked) == 4, (
            "only misc.txt, with no suggestion standing, is asked again"
        )
        assert (
            doc["state"] == "populated" and doc["groups"][0]["name"] == "not suggested"
        )
    finally:
        srv.shutdown()


def test_nothing_left_to_ask_about_is_empty(tmp_path):
    b, cats = box(tmp_path, {"beds.txt": FILES["beds.txt"]})
    got = run(str(SCRIPT), "--box", str(b), "--categories", str(cats), "--model", "m",
              "--url", "http://127.0.0.1:9/v1")  # fmt: skip
    assert (got.returncode, got.stdout.split(",")[0]) == (0, "sort-ask: empty")


def test_a_model_that_doesnt_answer_is_unreachable(tmp_path):
    b, cats = box(tmp_path, FILES)
    got = run(str(SCRIPT), "--box", str(b), "--categories", str(cats), "--model", "m",
              "--url", "http://127.0.0.1:9/v1", "--limit", "1")  # fmt: skip
    assert got.returncode == 42 and got.stdout.startswith("sort-ask: unreachable, ")


def test_a_url_off_this_machine_is_refused_before_anything_is_sent(tmp_path):
    b, cats = box(tmp_path, FILES)
    for url in ("https://api.example.com/v1", "http://10.0.0.5:11434/v1"):
        got = run(str(SCRIPT), "--box", str(b), "--categories", str(cats), "--model", "m",
                  "--url", url)  # fmt: skip
        assert got.returncode == 2 and "isn't on this machine" in got.stderr
    assert not (b / "proposals").exists()
    assert sa.on_this_machine("http://localhost:11434/v1")
    assert sa.on_this_machine("http://[::1]:11434/v1")


def test_only_one_of_your_categories_and_a_served_passage_counts():
    cats = sa.sort.categories(CATS)
    served = [
        {"id": "a", "where": "x:1", "text": "t"},
        {"id": "b", "where": "x:2", "text": "t"},
    ]
    assert sa.answer("garden [2]", cats, served) == ("garden", "b")
    assert sa.answer("Category: Health [1]\nbecause", cats, served) == ("health", "a")
    assert sa.answer("`garden` [1]", cats, served) == ("garden", "a")
    assert sa.answer("garden [3]", cats, served) is None  # no third passage served
    assert sa.answer("fruit [1]", cats, served) is None  # not a category of yours
    assert sa.answer("NONE", cats, served) is None


def test_the_example_is_never_one_of_your_categories():
    cats = sa.sort.categories("fruit: apple\nweather: rain\n")
    user = sa.messages(cats, "a.txt", [{"where": "a.txt:1", "text": "x"}])[-1][
        "content"
    ]
    assert "for example `music [1]` if the list had music" in user


def test_refusals(tmp_path):
    b, cats = box(tmp_path, FILES)
    assert run(str(SCRIPT)).returncode == 2
    assert (
        run(str(SCRIPT), "--box", str(b), "--categories", str(cats)).returncode == 2
    )  # no model
    assert run(str(SCRIPT), "--box", str(b), "--categories", str(cats), "--model", "m",
               "--limit", "x").returncode == 2  # fmt: skip


def test_reasoning_goes_in_the_request_and_the_claim_only_when_asked(tmp_path):
    b, cats = box(tmp_path, {"allotment.txt": FILES["allotment.txt"]})
    srv, url, _ = model({"allotment.txt": "garden [1]"})
    SENT.clear()
    try:
        argv = [str(SCRIPT), "--box", str(b), "--categories", str(cats), "--model", "m",
                "--url", url, *NOW]  # fmt: skip
        for bad in ("think", "", "High"):
            assert run(*argv, "--reasoning", bad).returncode == 2, bad
        assert SENT == [], "a refused effort asks nothing"
        assert run(*argv, "--reasoning", "high").returncode == 42
    finally:
        srv.shutdown()
    assert SENT[0]["reasoning_effort"] == "high"
    (prop,) = (b / "proposals").glob("*.json")
    assert (
        "(temperature 0, seed 7, reasoning high) read"
        in json.loads(prop.read_text())["claim"]
    )
    assert all("reasoning_effort" not in s for s in SENT[1:])
