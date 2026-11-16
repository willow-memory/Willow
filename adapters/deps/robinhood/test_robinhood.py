"""robinhood: only the six read tools are ever called, whatever the server
offers; each answer is written once, under its day, account numbers to their
last four digits, with its SHA-256 on the log; and every refusal comes
before any connection. Run against a stand-in server on 127.0.0.1."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import socket
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "robinhood.py"
spec = importlib.util.spec_from_file_location("robinhood", SCRIPT)
rh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rh)
NOW = ["--now", "2026-11-06T17:00:00Z"]
NEVER = {"place_equity_order", "cancel_equity_order", "add_to_watchlist", "update_watchlist",
         "search", "review_equity_order"}  # fmt: skip


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True, timeout=120)  # fmt: skip


@pytest.fixture
def server():
    pytest.importorskip("mcp")
    sys.path.insert(0, str(HERE))
    import fake_robinhood

    calls: list = []
    url, srv = fake_robinhood.serve(calls)
    yield SimpleNamespace(url=url, calls=calls, fake=fake_robinhood)
    srv.should_exit = True


def test_a_snapshot_calls_the_read_tools_only_and_writes_each_once(
    server, tmp_path: Path
):
    to = tmp_path / "rh"
    got = run(
        "snapshot", "--to", str(to), "--url", server.url, "--quotes", "vti, kr", *NOW
    )
    assert got.returncode == 0, got.stderr
    names = [n for n, _ in server.calls]
    assert not NEVER & set(names)
    assert names == ["get_accounts", "get_portfolio", "get_equity_positions",
                     "get_equity_positions", "get_equity_orders", "get_watchlists",
                     "get_equity_quotes"]  # fmt: skip
    assert ("get_equity_quotes", {"symbols": ["VTI", "KR"]}) in server.calls
    day = to / "2026-11-06"
    assert sorted(p.name for p in day.glob("*.txt")) == sorted(
        f"{n}.txt" for n in rh.READ
    )
    log = [json.loads(x) for x in (to / ".robinhood.jsonl").read_text().splitlines()]
    assert [r["tool"] for r in log] == list(rh.READ)
    for r in log:
        raw = (day / ".raw" / f"{r['tool']}.json").read_bytes()
        assert r["sha256"] == hashlib.sha256(raw).hexdigest() and r["bytes"] == len(raw)
        assert r["at"] == "2026-11-06T17:00:00Z"


def test_an_account_number_is_written_as_its_last_four(server, tmp_path: Path):
    to = tmp_path / "rh"
    assert run("snapshot", "--to", str(to), "--url", server.url, *NOW).returncode == 0
    every = "".join(p.read_text() for p in to.rglob("*") if p.is_file())
    assert "5QR12345678" not in every and "5QR98765432" not in every
    assert "****5678" in (to / "2026-11-06" / "get_accounts.txt").read_text()
    held = (to / "2026-11-06" / "get_equity_positions.txt").read_text()
    assert "VTI" in held and "****5678" in held


def test_quotes_are_skipped_and_said_without_symbols(server, tmp_path: Path):
    got = run("snapshot", "--to", str(tmp_path / "rh"), "--url", server.url, *NOW)
    assert got.returncode == 0
    assert "get_equity_quotes: no --quotes given" in got.stdout
    assert "get_equity_quotes" not in [n for n, _ in server.calls]


def test_a_read_tool_the_server_marks_as_changing_is_skipped(tmp_path: Path):
    pytest.importorskip("mcp")
    sys.path.insert(0, str(HERE))
    import fake_robinhood

    calls: list = []
    url, srv = fake_robinhood.serve(calls, marked_changing=("get_watchlists",))
    try:
        got = run("snapshot", "--to", str(tmp_path / "rh"), "--url", url, *NOW)
    finally:
        srv.should_exit = True
    assert got.returncode == 0
    assert (
        "get_watchlists: skipped, the server marks it as changing something"
        in got.stdout
    )
    assert "get_watchlists" not in [n for n, _ in calls]


def test_tools_lists_what_it_reads_and_what_it_never_calls(server):
    got = run("tools", "--url", server.url)
    assert got.returncode == 0, got.stderr
    marks = dict(reversed(ln.split()) for ln in got.stdout.splitlines() if ln.strip())
    assert {n for n, m in marks.items() if m == "reads"} == set(rh.READ)
    assert {n for n, m in marks.items() if m == "never"} == NEVER
    assert server.calls == []


def test_a_day_already_written_is_refused_before_any_connection(server, tmp_path: Path):
    to = tmp_path / "rh"
    (to / "2026-11-06").mkdir(parents=True)
    got = run("snapshot", "--to", str(to), "--url", server.url, *NOW)
    assert got.returncode == 2 and "already written" in got.stderr
    assert server.calls == []


@pytest.mark.parametrize("url", ["http://agent.robinhood.com/mcp/trading", "ftp://127.0.0.1/x",
                                 "http://evil.example/mcp"])  # fmt: skip
def test_anything_but_https_off_this_machine_is_refused(url, tmp_path: Path):
    got = run("snapshot", "--to", str(tmp_path / "rh"), "--url", url, *NOW)
    assert got.returncode == 2 and "is not https" in got.stderr
    assert not (tmp_path / "rh").exists()


@pytest.mark.parametrize("argv", [[], ["snapshot"], ["tools", "--to", "x"], ["trade", "--to", "x"],
                                  ["snapshot", "--to", "x", "--tool", "place_equity_order"],
                                  ["snapshot", "--to", "x", "--port", "many"],
                                  ["snapshot", "--to", "x", "--now", "today"]])  # fmt: skip
def test_a_bad_command_line_is_refused_and_names_the_script(argv):
    got = run(*argv)
    assert got.returncode == 2 and (
        "robinhood.py" in got.stderr or "--now" in got.stderr
    )


def test_masking_reaches_every_account_number_and_nothing_else():
    data = {"accounts": [{"account_number": "12345678", "acct": 99887766, "type": "cash"}],
            "nested": {"rh_account_no": "ABCD1234WXYZ", "accounts_count": 2}}  # fmt: skip
    assert rh.mask(data) == {
        "accounts": [
            {"account_number": "****5678", "acct": "****7766", "type": "cash"}
        ],
        "nested": {"rh_account_no": "****WXYZ", "accounts_count": 2},
    }
    assert rh.last_four("123") == "****"


def tool(name: str, need: list[str] | None = None, read_only=None, destructive=None):
    ann = None if read_only is None else SimpleNamespace(read_only_hint=read_only,
                                                         destructive_hint=destructive)  # fmt: skip
    return SimpleNamespace(
        name=name, input_schema={"required": need or []}, annotations=ann
    )


def test_a_tool_is_asked_once_per_account_and_never_with_arguments_it_cant_fill():
    accounts = {"account_number": ["A1", "A2", "A1"]}
    assert rh.calls(tool("get_equity_positions", ["account_number"]), accounts, []) == [
        {"account_number": "A1"}, {"account_number": "A2"}]  # fmt: skip
    assert (
        rh.calls(tool("get_portfolio", ["account_id"]), accounts, [])
        == "needs account_id"
    )
    assert rh.calls(tool("get_equity_quotes", ["symbols"]), {}, ["VTI"]) == [
        {"symbols": ["VTI"]}
    ]
    assert (
        rh.calls(tool("get_equity_quotes", ["symbols", "x"]), {}, ["VTI"])
        == "needs symbols, x"
    )
    assert rh.calls(tool("get_watchlists"), {}, []) == [{}]


def test_the_list_is_read_in_its_own_order_and_a_missing_tool_is_said():
    listed = [tool("place_equity_order", read_only=False, destructive=True),
              tool("get_watchlists"), tool("get_accounts", read_only=True),
              tool("get_portfolio", read_only=True, destructive=True)]  # fmt: skip
    use, why = rh.on_list(listed)
    assert [t.name for t in use] == ["get_accounts", "get_watchlists"]
    assert "get_portfolio: skipped, the server marks it as changing something" in why
    assert "get_equity_orders: not offered by this server" in why


def test_an_answer_is_its_structured_content_else_its_text():
    txt = SimpleNamespace(type="text", text='{"a": 1}')
    assert rh.answer(
        SimpleNamespace(is_error=False, structured_content={"b": 2}, content=[])
    ) == {"b": 2}
    assert rh.answer(
        SimpleNamespace(is_error=False, structured_content=None, content=[txt])
    ) == {"a": 1}
    plain = SimpleNamespace(type="text", text="no json")
    assert (
        rh.answer(
            SimpleNamespace(is_error=False, structured_content=None, content=[plain])
        )
        == "no json"
    )
    assert (
        rh.answer(
            SimpleNamespace(is_error=True, structured_content={"b": 2}, content=[])
        )
        is None
    )
    assert (
        rh.answer(SimpleNamespace(is_error=False, structured_content=None, content=[]))
        is None
    )


def test_the_sign_in_returns_to_this_machine_and_is_read_once():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    httpd, thread, got = rh.return_server(port)
    thread.start()
    with urllib.request.urlopen(
        f"http://127.0.0.1:{port}/callback?code=abc&state=xyz"
    ) as r:
        assert b"Signed in" in r.read()
    thread.join(5)
    httpd.server_close()
    assert got == {"code": "abc", "state": "xyz"}
    assert httpd.server_address[0] == "127.0.0.1"


def test_only_https_or_this_machine_is_allowed():
    assert rh.allowed_url(rh.URL)
    assert rh.allowed_url("http://127.0.0.1:9/mcp") and rh.allowed_url(
        "http://localhost:9/mcp"
    )
    assert not rh.allowed_url("http://agent.robinhood.com/mcp/trading")
    assert not rh.allowed_url("ftp://127.0.0.1/x")
    assert threading  # imported for the sign-in test's server


def test_the_sign_ins_return_keeps_its_issuer_for_the_sdk_to_check():
    """Robinhood's sign-in sends `iss` back with the code, and the SDK
    refuses a return without it when the server says it sends one: the
    first real sign-in failed so, with nothing written."""
    pytest.importorskip("mcp")
    from mcp.client.auth.exceptions import OAuthFlowError
    from mcp.client.auth.utils import validate_authorization_response_iss
    from mcp.shared.auth import OAuthMetadata

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    httpd, thread, got = rh.return_server(port)
    thread.start()
    issuer = "https://auth.example.test/"
    q = urllib.parse.urlencode({"code": "the-code", "state": "st", "iss": issuer})
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/callback?{q}") as r:
        assert r.status == 200
    thread.join(5)
    httpd.server_close()
    back = rh.returned(got)
    assert (back.code, back.state, back.iss) == ("the-code", "st", issuer)
    meta = OAuthMetadata(
        issuer=issuer,
        authorization_endpoint=issuer + "authorize",
        token_endpoint=issuer + "token",
        authorization_response_iss_parameter_supported=True,
    )
    validate_authorization_response_iss(back.iss, meta)  # the SDK takes it
    with pytest.raises(OAuthFlowError):
        validate_authorization_response_iss(rh.returned({"code": "c"}).iss, meta)
    with pytest.raises(OAuthFlowError):
        validate_authorization_response_iss(
            rh.returned({"code": "c", "iss": "https://elsewhere.test/"}).iss, meta
        )
