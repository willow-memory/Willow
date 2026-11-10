"""browse: a page on 127.0.0.1 that asks with the kernel's bite and approves
with its seal, reachable only with this start's secret, from this machine's
own address, and never framed or scripted."""

from __future__ import annotations

import http.client
import importlib.util
import json
import shlex
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import urlencode

import pytest

HERE = Path(__file__).resolve().parent
#: the front page's summary is digest's; without it the page says so
DIGEST = (HERE.parent / "digest").is_dir()
NO_DIGEST = "The digest add-on isn't here, so there's no summary."
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("browse", HERE / "browse.py")
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)
NOW = ["--now", "2026-10-24T00:00:00Z"]


def k(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KERNEL), *argv], capture_output=True, text=True
    )


def make_box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "dentist.txt").write_text(
        "The dentist is on Tuesday at 3pm. <b>Bring</b> the card.\n"
    )
    (pile / "termin.txt").write_text("Der Termin beim Zahnarzt ist am Dienstag.\n")
    b = tmp_path / "box"
    assert k("init", "--box", str(b), "--pile", str(pile), "--key", str(tmp_path / "key"), *NOW).returncode == 0  # fmt: skip
    return b


class Open:
    """A running browse for one box, and a client that holds its cookie."""

    def __init__(self, box: Path, lang: str | None = None):
        self.willow = br.Willow(box, lang)
        self.server = br.serve(self.willow)
        self.port = self.server.server_address[1]
        self.host = f"127.0.0.1:{self.port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.cookie = ""

    def req(self, method, path, form=None, headers=None, cookie=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        hdrs = {"Host": self.host, **(headers or {})}
        if cookie and self.cookie:
            hdrs["Cookie"] = self.cookie
        body = None
        if form is not None:
            body = urlencode(form)
            hdrs["Content-Type"] = "application/x-www-form-urlencoded"
        conn.request(method, path, body=body, headers=hdrs)
        r = conn.getresponse()
        text = r.read().decode()
        conn.close()
        return r, text

    def start(self):
        r, _ = self.req("GET", f"/start?key={self.willow.token}", cookie=False)
        assert r.status == 303 and r.getheader("Location") == "/"
        self.cookie = r.getheader("Set-Cookie").split(";")[0]
        return r

    def post(self, path, **form):
        return self.req("POST", path, {"token": self.willow.token, **form})

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def site(tmp_path):
    s = Open(make_box(tmp_path))
    yield s
    s.close()


def test_the_link_hands_over_a_cookie_no_other_site_can_send(site):
    r = site.start()
    cookie = r.getheader("Set-Cookie")
    assert "HttpOnly" in cookie and "SameSite=Strict" in cookie and "Path=/" in cookie
    r, text = site.req("GET", "/")
    assert r.status == 200 and "Ask your folder" in text
    assert ("Nothing is waiting" in text) == DIGEST and (NO_DIGEST in text) != DIGEST


def test_without_this_starts_secret_nothing_answers(site):
    for path in ("/", "/waiting", "/nope"):
        r, text = site.req("GET", path)
        assert r.status == 403 and "link browse.py printed" in text
    r, _ = site.req("GET", "/start?key=wrong", cookie=False)
    assert r.status == 403 and r.getheader("Set-Cookie") is None
    site.cookie = "willow=" + "x" * 43
    assert site.req("GET", "/")[0].status == 403


def test_a_page_reached_by_another_name_is_refused(site):
    site.start()
    for host in (
        "evil.example:%d" % site.port,
        "127.0.0.1",
        "localhost.evil:%d" % site.port,
    ):
        r, _ = site.req("GET", "/", headers={"Host": host})
        assert r.status == 403
    r, _ = site.req(
        "GET",
        f"/start?key={site.willow.token}",
        headers={"Host": "evil.example"},
        cookie=False,
    )
    assert r.status == 403 and r.getheader("Set-Cookie") is None
    assert (
        site.req("GET", "/", headers={"Host": f"localhost:{site.port}"})[0].status
        == 200
    )


def test_a_form_from_anywhere_else_is_refused(site):
    site.start()
    r, _ = site.req("POST", "/ask", {"q": "dentist"})  # no token in the form
    assert r.status == 403
    for origin in ("https://evil.example", "null"):  # null: a sandboxed frame's
        r, _ = site.req(
            "POST",
            "/ask",
            {"token": site.willow.token, "q": "dentist"},
            headers={"Origin": origin},
        )
        assert r.status == 403
    r, _ = site.req(
        "POST",
        "/ask",
        {"token": site.willow.token, "q": "dentist"},
        headers={"Origin": f"http://127.0.0.1:{site.port}"},
    )
    assert r.status == 200
    site.cookie = ""
    r, _ = site.req("POST", "/ask", {"token": site.willow.token, "q": "dentist"})
    assert r.status == 403  # the form's token alone isn't enough


def test_every_page_forbids_framing_scripts_and_caching(site):
    site.start()
    for r, _ in (
        site.req("GET", "/"),
        site.req("GET", "/nope"),
        site.req("GET", "/", cookie=False),
    ):
        assert "frame-ancestors 'none'" in r.getheader("Content-Security-Policy")
        assert "default-src 'none'" in r.getheader("Content-Security-Policy")
        assert r.getheader("X-Frame-Options") == "DENY"
        assert r.getheader("Cache-Control") == "no-store"
        assert r.getheader("Referrer-Policy") == "same-origin"


def test_asking_shows_each_passage_with_its_file_and_line_escaped(site):
    site.start()
    r, text = site.post("/ask", q="when is the dentist")
    assert r.status == 200 and "Your files say" in text
    assert (
        "dentist.txt:1" in text
        and "&lt;b&gt;Bring&lt;/b&gt;" in text
        and "<b>Bring" not in text
    )
    rows = (site.willow.box / "record.jsonl").read_text().splitlines()
    assert (
        json.loads(rows[-1])["kind"] == "bite"
    )  # the kernel's own bite, on the record


def test_nothing_found_is_said_with_where_to_look(site):
    site.start()
    r, text = site.post("/ask", q="passport renewal office")
    assert "Nothing in your folder holds that" in text
    r, text = site.post("/ask", q="the and of")
    assert "name the thing you mean" in text


def test_a_suggestion_waits_with_its_sources_and_a_click_approves_it(site, tmp_path):
    b = site.willow.box
    served = json.loads(k("bite", "--box", str(b), *NOW, "when is the dentist").stdout)[
        "served"
    ]
    row = {
        "path": "dentist.md",
        "data": "Tuesday at 3pm",
        "cites": [served[0]["id"]],
        "claim": "the dentist note",
    }
    (tmp_path / "s.jsonl").write_text(json.dumps(row) + "\n")
    assert (
        k(
            "propose", "--box", str(b), "--file", str(tmp_path / "s.jsonl"), *NOW
        ).returncode
        == 42
    )
    site.start()
    front = site.req("GET", "/")[1]
    assert ("1 suggestion waiting" in front) == DIGEST and (
        NO_DIGEST in front
    ) != DIGEST
    r, text = site.req("GET", "/waiting")
    assert r.status == 200 and (
        "Tuesday at 3pm" in text
        and "the dentist note" in text
        and "dentist.txt:1" in text
    )
    subject = text.split('name=subject value="')[1].split('"')[0]
    r, text = site.post("/approve", subject=subject)
    assert r.status == 200 and "Approved" in text
    seal = json.loads((b / "record.jsonl").read_text().splitlines()[-1])
    assert (
        seal["kind"] == "seal" and seal["who"] == "human" and seal["subject"] == subject
    )
    assert k("verify", "--box", str(b)).returncode == 0
    r, text = site.post("/ask", q="when is the dentist")
    assert "You approved this answer" in text and "Tuesday at 3pm" in text
    assert "Nothing is waiting" in site.req("GET", "/waiting")[1]
    r, text = site.post("/approve", subject="proposal:" + "0" * 64)
    assert "Not approved" in text and "not a proposal in this box" in text


def test_with_a_language_its_common_words_are_left_out(tmp_path):
    if not (
        HERE.parent / "words-de"
    ).is_dir():  # a copy without German: said, not guessed
        with pytest.raises(ValueError, match="the words-de add-on isn't here"):
            br.Willow(make_box(tmp_path), "de")
        return
    s = Open(make_box(tmp_path), "de")
    try:
        s.start()
        r, text = s.post("/ask", q="Wann ist der Termin beim Zahnarzt?")
        assert "termin.txt:1" in text and "dentist.txt" not in text
    finally:
        s.close()
    with pytest.raises(ValueError):
        br.Willow(s.willow.box, "xx")


def test_the_launcher_starts_browse_over_the_box_on_each_system(tmp_path, capsys):
    (tmp_path / "with space").mkdir()
    b = make_box(tmp_path / "with space")
    files = {system: text for system, _, text in br.launchers(b, "/usr/bin/python3")}
    mac = shlex.split(files["macOS"].splitlines()[1][len("exec ") :])
    assert mac == ["/usr/bin/python3", str(br.HERE), "--box", str(b.resolve())]
    assert files["macOS"].startswith("#!/bin/sh\n")
    assert (
        files["Windows"].startswith("@echo off\r\n")
        and f'"{b.resolve()}"' in files["Windows"]
    )
    assert "Exec=" in files["Linux"] and "Terminal=true" in files["Linux"]
    before = sorted(p.name for p in b.iterdir())
    assert br.main(["launcher", "--box", str(b)]) == 0
    out = capsys.readouterr().out
    assert out.count("save as") == 3 and sorted(p.name for p in b.iterdir()) == before


def test_a_bad_command_line_or_box_is_refused(tmp_path, capsys):
    b = make_box(tmp_path)
    for argv in (
        [],
        ["--box"],
        ["--box", str(b), "--port", "x"],
        ["--box", str(b), "--port", "70000"],
        ["--box", str(b), "--lang", "xx"],
        ["--box", str(b), "more"],
        ["launcher"],
        ["launcher", "--box"],
    ):
        assert br.main(argv) == 2, argv
    assert br.main(["--box", str(tmp_path)]) == 2
    assert br.main(["launcher", "--box", str(tmp_path)]) == 2
    assert "not a kernel box" in capsys.readouterr().err


def test_a_port_already_taken_is_refused(tmp_path, capsys):
    s = Open(make_box(tmp_path))
    try:
        assert (
            br.main(["--box", str(s.willow.box), "--port", str(s.port), "--no-open"])
            == 2
        )
        assert "refused" in capsys.readouterr().err
    finally:
        s.close()


def test_a_suggestion_you_declined_no_longer_waits(site, tmp_path):
    b = site.willow.box
    served = json.loads(k("bite", "--box", str(b), *NOW, "when is the dentist").stdout)[
        "served"
    ]
    row = {
        "path": "dentist.md",
        "data": "Monday",
        "cites": [served[0]["id"]],
        "claim": "a guess",
    }
    (tmp_path / "s.jsonl").write_text(json.dumps(row) + "\n")
    k("propose", "--box", str(b), "--file", str(tmp_path / "s.jsonl"), *NOW)
    subject = next(r["subject"] for r in map(json.loads, (b / "record.jsonl").read_text().splitlines())
                   if r.get("verdict") == "pass")  # fmt: skip
    assert k("decline", "--box", str(b), subject, *NOW).returncode == 0
    site.start()
    assert "Nothing is waiting for your approval." in site.req("GET", "/waiting")[1]


# ── a card a person can read ─────────────────────────────────────────────────
CHOICE = {
    "card": {
        "line": "Commit messages as a dated pile.",
        "name": "git-history",
        "sha256": "d3" * 32,
    },
    "chose": "git-history",
    "decision_type": "willow-repos",
    "over": ["code-comments", "codebase-memory"],
    "why": "it is the only one with dates",
    "word": "repos",
}
STACK = "# read my repos\n\n## for “read my repos”\n- git-history -- mirror --from {box} --to {tmp}/gh\n- export -- --box {box}\n"


def prop(data: str, claim: str = "the claim") -> dict:
    return {"path": "p.md", "data": data, "cites": [], "claim": claim}


def test_rich_escapes_first_then_marks_bold_lists_and_headings():
    got = br.rich(
        "# A <b>title</b>\n**bold** and <i>not</i>\nsame line\n\n- one\n- two & more\nafter"
    )
    assert got == (
        "<p class=said><strong>A &lt;b&gt;title&lt;/b&gt;</strong></p>"
        "<p class=said><strong>bold</strong> and &lt;i&gt;not&lt;/i&gt; same line</p>"
        "<ul><li>one</li><li>two &amp; more</li></ul>"
        "<p class=said>after</p>"
    )
    assert br.rich("") == ""
    assert br.rich("text\n- item") == "<p class=said>text</p><ul><li>item</li></ul>"
    assert br.rich("a ** b") == "<p class=said>a ** b</p>"


def test_names_are_listed_as_a_person_lists_them():
    assert br.listed([]) == ""
    assert br.listed(["a"]) == "a"
    assert br.listed(["a", "b"]) == "a or b"
    assert br.listed(["a", "b", 3]) == "a, b or 3"


def test_a_choice_reads_as_a_sentence_with_its_own_reason():
    kind, head, body, why = br.reading(prop(json.dumps(CHOICE)))
    assert kind == "choice"
    assert head == "For “repos”, use git-history"
    assert body == (
        "<p>Not code-comments or codebase-memory.</p>"
        "<p class=muted>git-history: Commit messages as a dated pile.</p>"
    )
    assert why == "it is the only one with dates"
    bare = {"chose": "<a>", "word": "<w>", "over": []}
    assert br.reading(prop(json.dumps(bare), "its <claim>")) == (
        "choice",
        "For “&lt;w&gt;”, use &lt;a&gt;",
        "",
        "its &lt;claim&gt;",
    )
    assert br.reading(prop(json.dumps({**bare, "why": ""}), "c"))[3] == "c"
    assert br.reading(prop(json.dumps({**bare, "card": {"line": 3}})))[2] == ""


def test_only_the_shape_of_a_choice_is_read_as_one():
    for not_one in (
        ["chose"],
        {"chose": "a", "word": "w"},
        {"chose": "a", "over": []},
        {"word": "w", "over": []},
        {"chose": 1, "word": "w", "over": []},
        {"chose": "a", "word": 2, "over": []},
        {"chose": "a", "word": "w", "over": "b"},
    ):
        kind, head, body, _ = br.reading(prop(json.dumps(not_one)))
        assert (kind, head) == ("answer", "") and body.startswith("<p class=said>")


def test_a_stack_reads_as_its_title_and_steps():
    kind, head, body, why = br.reading(prop("\n" + STACK, "a <stack>"))
    assert (kind, head, why) == ("stack", "read my repos", "a &lt;stack&gt;")
    assert body == (
        "<ul><li>git-history -- mirror --from {box} --to {tmp}/gh</li>"
        "<li>export -- --box {box}</li></ul>"
    )
    assert br.reading(prop("# a title\n- no steps here"))[0] == "answer"
    assert br.reading(prop("- step -- --box {box}"))[0] == "answer"


def test_the_waiting_page_says_each_suggestion_in_words(site, tmp_path):
    b = site.willow.box
    rows = [
        {
            "path": "forge/decisions/willow-repos.json",
            "data": json.dumps(CHOICE),
            "cites": [],
            "claim": "for repos",
        },
        {"path": "forge/stack.md", "data": STACK, "cites": [], "claim": "a stack"},
    ]
    served = json.loads(k("bite", "--box", str(b), *NOW, "when is the dentist").stdout)[
        "served"
    ]
    rows.append(
        {
            "path": "dentist.md",
            "data": "**Tuesday** at 3pm",
            "cites": [served[0]["id"]],
            "claim": "the note",
        }
    )
    (tmp_path / "s.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert (
        k(
            "propose", "--box", str(b), "--file", str(tmp_path / "s.jsonl"), *NOW
        ).returncode
        == 42
    )
    site.start()
    text = site.req("GET", "/waiting")[1]
    assert "<strong>3 waiting.</strong>" in text
    one, two, three = text.split("<div class=card><p class=kick>")[1:]
    assert one.startswith(
        "A suggested choice <span class=pill>forge/decisions/willow-repos.json</span>"
    )
    assert "<h2>For “repos”, use git-history</h2>" in one
    assert "It cites nothing from your folder." in one and "It cites 0" not in one
    assert "<button>Approve this choice</button>" in one
    # what the seal signs is still there to read, escaped and folded away
    assert "Exactly what you'd be approving</summary><pre>{&quot;card&quot;" in one
    assert "proposal:" in one.split("</pre>")[1].split("</details>")[0]
    assert (
        "<h2>read my repos</h2>" in two and "<button>Approve this stack</button>" in two
    )
    assert "<h2>" not in three and "<strong>Tuesday</strong> at 3pm" in three
    assert "<summary>It cites 1 passage of your folder</summary>" in three
    assert "dentist.txt:1" in three and "<button>Approve this answer</button>" in three
    subject = two.split('name=subject value="')[1].split('"')[0]
    assert "Approved" in site.post("/approve", subject=subject)[1]
    assert "<strong>2 waiting.</strong>" in site.req("GET", "/waiting")[1]


def test_an_approved_answer_is_shown_in_words_with_its_name(site, tmp_path):
    b = site.willow.box
    served = json.loads(k("bite", "--box", str(b), *NOW, "when is the dentist").stdout)[
        "served"
    ]
    row = {
        "path": "d.md",
        "data": "**Tuesday** <at> 3pm",
        "cites": [served[0]["id"]],
        "claim": "c",
    }
    (tmp_path / "s.jsonl").write_text(json.dumps(row) + "\n")
    k("propose", "--box", str(b), "--file", str(tmp_path / "s.jsonl"), *NOW)
    site.start()
    waiting = site.req("GET", "/waiting")[1]
    assert "<strong>1 waiting.</strong>" in waiting
    subject = waiting.split('name=subject value="')[1].split('"')[0]
    site.post("/approve", subject=subject)
    text = site.post("/ask", q="when is the dentist")[1]
    assert (
        "<div class=card><p class=said><strong>Tuesday</strong> &lt;at&gt; 3pm</p>"
        f"<p class=where>{subject}</p></div>"
    ) in text


def test_the_page_wears_the_canvas_colours():
    """The canvas is the main page; ui/test_ui.py holds these to its own."""
    for colour in ("#eceee7", "#f8f9f5", "#23251f", "#45652a", "#141712", "#a6c56f"):
        assert colour in br.STYLE


# ── any report, drawn one way ────────────────────────────────────────────────
STACK_HERE = (HERE.parent / "stack").is_dir()
TODO_HERE = (HERE.parent / "todo").is_dir()
DOC = {
    "addon": "pii-audit",
    "state": "populated",
    "said": "3 numbers in 2 of 9 files",
    "groups": [
        {"name": None, "rows": [{"where": "a.txt:1", "what": "loose <row>"}]},
        {"name": "a card & number", "rows": [{"where": "m/o.csv:17", "what": "···· 4242"},
                                              {"where": "m/o.csv:18", "what": "···· 1111"}]},
    ],
}  # fmt: skip


def test_a_report_is_a_card_its_line_then_its_rows_under_their_groups():
    assert br.report_card(DOC) == (
        "<div class=card><p class=kick>pii-audit <span class=pill>found</span></p>"
        "<h2>3 numbers in 2 of 9 files</h2>"
        "<div class=row><span class=where>a.txt:1</span><p class=text>loose &lt;row&gt;</p></div>"
        "<p class=group>a card &amp; number</p>"
        "<div class=row><span class=where>m/o.csv:17</span><p class=text>···· 4242</p></div>"
        "<div class=row><span class=where>m/o.csv:18</span><p class=text>···· 1111</p></div>"
        "</div>"
    )


def test_a_report_says_its_state_in_words_and_when_it_waits_on_you():
    empty = {"addon": "todo", "state": "empty", "said": "nothing to do", "groups": []}
    got = br.report_card(empty)
    assert "<span class=pill>nothing found</span>" in got and "class=row" not in got
    assert "<span class=pill>couldn&#x27;t look</span>" in br.report_card(
        {**empty, "state": "unreachable"}
    )
    assert "<span class=pill>&lt;odd&gt;</span>" in br.report_card(
        {**empty, "state": "<odd>"}
    )
    waits = "<span class='pill wait'>waits on you</span>"
    assert waits in br.report_card(DOC, 42) and waits not in br.report_card(DOC, 0)
    assert waits not in br.report_card(empty, 42), "nothing found is nothing to wait on"
    assert waits not in br.report_card(DOC, 2)


def test_a_long_report_shows_its_first_rows_and_folds_the_rest():
    rows = [{"where": f"f{i}.txt:1", "what": f"line {i}"} for i in range(11)]
    doc = {"addon": "todo", "state": "populated", "said": "11 lines", "groups": [
        {"name": "old", "rows": rows[:7]}, {"name": "new", "rows": rows[7:]}]}  # fmt: skip
    got = br.report_card(doc)
    seen, folded = got.split("<details>")
    assert seen.count("class=row") == 8 == br.SHOWN and folded.count("class=row") == 3
    assert "<summary>All 11 rows</summary>" in folded
    # the group a fold cuts through is named on both sides of it
    assert (
        seen.count("<p class=group>new</p>") == 1
        and folded.count("<p class=group>new</p>") == 1
    )
    assert "<details>" not in br.report_card(
        {**doc, "groups": [{"name": "old", "rows": rows[:8]}]}
    )
    assert br.report_card(doc, shown=2).split("<details>")[0].count("class=row") == 2


def test_a_stacks_report_steps_are_drawn_and_the_rest_are_named(tmp_path):
    b = make_box(tmp_path)
    (tmp_path / "pile" / "list.txt").write_text("TODO: call the <dentist> back\n")
    stack = tmp_path / "mine.md"
    stack.write_text(
        "# mine\n## what's owed\n- todo -- --box {box}\n- nowhere -- --box {box}\n"
        "## the rest\n- browse -- --box {box}\n"
    )
    s = Open.__new__(Open)
    s.willow = br.Willow(b, None, stack=stack)
    s.server = br.serve(s.willow)
    s.port = s.server.server_address[1]
    s.host = f"127.0.0.1:{s.port}"
    threading.Thread(target=s.server.serve_forever, daemon=True).start()
    s.cookie = ""
    try:
        s.start()
        assert '<a href="/steps">What your stack found</a>' in s.req("GET", "/")[1]
        r, text = s.req("GET", "/steps")
        assert r.status == 200
        if not STACK_HERE:
            assert "The stack add-on isn't here." in text
            return
        assert "The nowhere add-on isn't here." in text
        assert "<h2>what&#x27;s owed</h2>" in text and "<h2>the rest</h2>" not in text
        assert (
            "Not drawn here, since they print something other than a report: browse."
            in text
        )
        if TODO_HERE:
            assert "<p class=kick>todo <span class=pill>found</span>" in text
            assert "call the &lt;dentist&gt; back" in text and "list.txt:1" in text
        stack.write_text("no steps here\n")
        assert "Couldn't read your stack" in s.req("GET", "/steps")[1]
        stack.unlink()
        assert (
            "Couldn't read your stack: can&#x27;t read the stack"
            in s.req("GET", "/steps")[1]
        )
    finally:
        s.close()


def test_without_a_stack_there_is_no_third_page_to_go_to(site):
    site.start()
    assert "/steps" not in site.req("GET", "/")[1]
    r, text = site.req("GET", "/steps")
    assert (
        r.status == 200
        and "No stack was named when this was started." in text
        or (not STACK_HERE and "The stack add-on isn't here." in text)
    )


def test_a_stack_that_isnt_there_is_refused_before_anything_listens(tmp_path, capsys):
    b = make_box(tmp_path)
    assert (
        br.main(["--box", str(b), "--stack", str(tmp_path / "absent.md"), "--no-open"])
        == 2
    )
    assert "can't read the stack" in capsys.readouterr().err
    assert br.main(["--box", str(b), "--stack"]) == 2
    assert "browse.py" in capsys.readouterr().err


# ── a run that was kept, shown and not run ───────────────────────────────────
def opened(box, **kw):
    s = Open.__new__(Open)
    s.willow = br.Willow(box, None, **kw)
    s.server = br.serve(s.willow)
    s.port = s.server.server_address[1]
    s.host = f"127.0.0.1:{s.port}"
    threading.Thread(target=s.server.serve_forever, daemon=True).start()
    s.cookie = ""
    s.start()
    return s


LOG = (
    "01 todo: started (aaaaaaaa)\n01 todo: exit 0, 3 lines\n"
    "02 heavy: started (bbbbbbbb)\n02 heavy: exit 2, 1 line, flagged\n"
    "03 slow: started (cccccccc)\n"
)
REPORT = {"addon": "todo", "state": "populated", "said": "2 lines marked to do",
          "groups": [{"name": None, "rows": [{"where": "a.txt:1", "what": "call <them>"}]}]}  # fmt: skip


@pytest.mark.skipif(
    not STACK_HERE, reason="a run is the stack add-on's, and it isn't here"
)
def test_a_runs_log_is_read_as_its_steps_and_whether_it_ended():
    st = br.sibling("stack", "stack")
    steps, done = br.run_steps(LOG, st)
    assert done is None and [s["n"] for s in steps] == ["01", "02", "03"]
    assert steps[0] == {"n": "01", "name": "todo", "ended": True, "code": 0, "flagged": False, "kept": False}  # fmt: skip
    assert steps[1]["code"] == 2 and steps[1]["flagged"] and steps[2] == {"n": "03", "name": "slow", "ended": False}  # fmt: skip
    steps, done = br.run_steps(
        LOG + "03 slow: exit 0, 2 lines\ndone: 1 of 3 steps flagged\n", st
    )
    assert done == "1 of 3 steps flagged" and steps[2]["ended"]
    more = (
        LOG
        + "done: x\nresumed: 2 of 3 steps had finished\n01 todo: kept from before\n09 nope: kept from before\n"
    )
    steps, done = br.run_steps(more, st)
    assert (
        done is None and steps[0]["kept"] and not steps[1]["kept"] and len(steps) == 3
    )
    assert br.run_steps("02 x: exit 0, 1 line\nnonsense\n", st) == ([], None), (
        "an end with no start"
    )


def test_a_run_is_shown_from_what_it_kept_and_nothing_is_run(tmp_path):
    b = make_box(tmp_path)
    run = tmp_path / "run"
    (run / "reports").mkdir(parents=True)
    rows_before = (b / "record.jsonl").read_text()
    s = opened(b, run=run)
    try:
        assert '<a href="/run">The run</a>' in s.req("GET", "/")[1]
        text = s.req("GET", "/run")[1]
        if not STACK_HERE:
            assert "The stack add-on isn't here." in text
            return
        assert "holds no run" in text and "http-equiv" not in text
        (run / "00-stack.txt").write_text(LOG)
        (run / "reports" / "01-todo.json").write_text(json.dumps(REPORT))
        (run / "01-todo.txt").write_text("todo: populated, 2 lines marked to do\n")
        (run / "02-heavy.txt").write_text("refused: <not> a box\n")
        (run / "03-slow.txt").write_text("".join(f"line {i}\n" for i in range(1, 12)))
        text = s.req("GET", "/run")[1]
        assert "<strong>Still running.</strong>" in text
        assert f'<meta http-equiv="refresh" content="{br.AGAIN}">' in text
        assert "looks again every 3 seconds" in text, "three, as the card says"
        one, two, three = text.split("<div class=card>")[1:]
        assert (
            "<p class=kick>todo <span class=pill>found</span> <span class=pill>step 01</span></p>"
            in one
        )
        assert "<h2>2 lines marked to do</h2>" in one and "call &lt;them&gt;" in one
        assert (
            "<span class=pill>exit 2</span> <span class='pill wait'>flagged</span>"
            in two
        )
        assert "<pre>refused: &lt;not&gt; a box</pre>" in two
        assert (
            "<span class='pill wait'>running</span>" in three
            and "exit" not in three.split("</p>")[0]
        )
        assert (
            "<summary>All 11 lines</summary>" in three
            and "line 8\n"
            not in three.split("<details>")[0].replace("line 8</pre>", "")
        )
        with (run / "00-stack.txt").open("a") as f:
            f.write("03 slow: exit 0, 11 lines\ndone: 1 of 3 steps flagged\n")
        text = s.req("GET", "/run")[1]
        assert (
            "<strong>Finished.</strong> 1 of 3 steps flagged." in text
            and "http-equiv" not in text
        )
        assert "running" not in text
        assert (b / "record.jsonl").read_text() == rows_before, (
            "showing a run writes nothing"
        )
        (run / "reports" / "01-todo.json").write_text("{not json")
        assert (
            "<pre>todo: populated, 2 lines marked to do</pre>"
            in s.req("GET", "/run")[1]
        )
    finally:
        s.close()


def test_a_step_that_printed_nothing_says_so_and_no_run_is_no_page(
    site, tmp_path, capsys
):
    assert "It printed nothing." in br.words_card("<p class=kick>x</p>", "")
    assert br.words_card("", "a\nb", shown=1) == (
        "<div class=card><pre>a</pre><details><summary>All 2 lines</summary><pre>b</pre></details></div>"
    )
    site.start()
    assert "/run" not in site.req("GET", "/")[1]
    assert (
        br.main(
            [
                "--box",
                str(site.willow.box),
                "--run",
                str(tmp_path / "absent"),
                "--no-open",
            ]
        )
        == 2
    )
    assert "isn't a folder that's there" in capsys.readouterr().err
    assert br.main(["--box", str(site.willow.box), "--run"]) == 2


# ── a question goes to the steps whose job it is, and a miss says why ───────
LOOK_HERE = (br.STDLIB / "look" / "look.py").is_file()
WHY_NOT_HERE = (br.STDLIB / "why-not" / "why_not.py").is_file()


def a_kept_run(tmp_path: Path, **steps: str) -> Path:
    run = tmp_path / "run"
    run.mkdir()
    (run / "00-stack.txt").write_text("done: 0 of 1 steps flagged\n")
    for n, (name, text) in enumerate(steps.items(), 1):
        (run / f"{n:02d}-{name}.txt").write_text(text)
    return run


@pytest.mark.skipif(not LOOK_HERE, reason="the look add-on isn't here")
def test_a_question_a_step_answers_shows_that_steps_lines_above_your_files(tmp_path):
    run = a_kept_run(
        tmp_path, debts="Dana owes you $40 <soon>\n", invoices="overdue  Theatre\n"
    )
    s = opened(make_box(tmp_path), run=run)
    try:
        r, text = s.post("/ask", q="who owes the dentist")
        assert r.status == 200
        assert "<h2>What your stack already found</h2>" in text
        assert "money owed" in text and "2 lines from debts and invoices" in text
        assert "01-debts.txt:1" in text and "Dana owes you $40 &lt;soon&gt;" in text
        assert "<soon>" not in text
        assert "waits on you" not in text
        # the step's lines come before the kernel's own passages, which stay
        assert text.index("already found") < text.index("Your files say")
        assert "dentist.txt:1" in text
        # look writes nothing: the last row is the page's own bite
        rows = (s.willow.box / "record.jsonl").read_text().splitlines()
        assert json.loads(rows[-1])["kind"] == "bite"
    finally:
        s.close()


@pytest.mark.skipif(not LOOK_HERE, reason="the look add-on isn't here")
def test_a_step_the_run_lacks_is_said_and_a_thing_written_down_gets_no_card(tmp_path):
    run = a_kept_run(tmp_path, debts="Dana owes you $40\n")
    s = opened(make_box(tmp_path), run=run)
    try:
        _, text = s.post("/ask", q="who owes the dentist")
        assert "its job, and not a step of this run" in text
        assert "waits on you" in text
        # the ask is the page's own, so look's note that it left it is dropped
        assert "add --box BOX" not in text
        _, text = s.post("/ask", q="bring the dentist card")
        assert "already found" not in text and "Your files say" in text
    finally:
        s.close()


def test_without_a_run_asking_is_the_kernels_alone(site):
    site.start()
    _, text = site.post("/ask", q="who owes the dentist")
    assert "already found" not in text and "Your files say" in text


@pytest.mark.skipif(not WHY_NOT_HERE, reason="the why-not add-on isn't here")
def test_a_question_that_finds_nothing_is_given_why_nots_reasons(site):
    site.start()
    _, text = site.post("/ask", q="passport renewal office")
    assert "<h2>Nothing in your folder holds that</h2>" in text
    assert "<p class=kick>why-not" in text
    assert "no passage holds it" in text
    assert "<details><summary>Why no passage" not in text


@pytest.mark.skipif(
    not (LOOK_HERE and WHY_NOT_HERE), reason="the look or why-not add-on isn't here"
)
def test_a_sum_no_passage_says_is_not_called_a_miss(tmp_path):
    run = a_kept_run(
        tmp_path, debts="Dana owes you $40\n", invoices="overdue  Theatre\n"
    )
    s = opened(make_box(tmp_path), run=run)
    try:
        _, text = s.post("/ask", q="who still owes me money")
        assert "<h2>No one passage in your folder says that</h2>" in text
        assert "Nothing in your folder holds that" not in text
        assert "<details><summary>Why no passage holds it</summary>" in text
        assert text.index("already found") < text.index("No one passage")
    finally:
        s.close()


def test_report_of_gives_no_report_for_an_add_on_that_isnt_here_or_isnt_one():
    assert br.report_of("no-such-add-on", "nope") == (0, None)
    # the kernel prints no report: asked as one, it is none
    if (br.STDLIB / "starter-words" / "starter_words.py").is_file():
        code, doc = br.report_of("starter-words", "starter_words")
        assert doc is None
