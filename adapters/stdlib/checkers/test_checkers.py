"""checkers: the rules, one row a move, a draw only on the seal of whoever
holds the key, and check finding a forged row. Positions are made up here."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
spec = importlib.util.spec_from_file_location("checkers", HERE / "checkers.py")
ck = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ck)
kernel = ck.kernel
NOW = ["--now", "2026-11-14T09:00:00Z"]


def moves(board: dict, side: str) -> list[str]:
    return sorted(ck.written(m) for m in ck.legal(board, side))


class Table:
    """A fresh box and the commands against it."""

    def __init__(self, tmp: Path):
        pile = tmp / "pile"
        pile.mkdir(parents=True)
        (pile / "a.txt").write_text("x\n")
        self.box, self.key = tmp / "box", tmp / "k"
        self.k("init", "--pile", str(pile), "--key", str(self.key))

    def k(self, *argv: str):
        return subprocess.run([sys.executable, str(KERNEL), argv[0], "--box", str(self.box), *NOW, *argv[1:]],
                              capture_output=True, text=True)  # fmt: skip

    def run(self, *argv: str):
        return subprocess.run([sys.executable, str(HERE / "checkers.py"), "--box", str(self.box), *argv, *NOW],
                              capture_output=True, text=True)  # fmt: skip

    def rows(self) -> list[dict]:
        return kernel.read(self.box / "record.jsonl")[0]

    def raw(self) -> bytes:
        return (self.box / "record.jsonl").read_bytes()

    def play(self, *ms: str):
        for m in ms:
            got = self.run("move", m)
            assert got.returncode == 0, got.stderr

    def subject(self) -> str:
        return [r for r in self.rows() if r["kind"] == ck.ASK][-1]["subject"]

    def forge(self, kind: str, **fields):
        kernel.append(self.box, NOW[1], kind, who=ck.WHO, **fields)

    def game(self) -> int:
        return [r for r in self.rows() if r["kind"] == ck.OPEN][-1]["n"]


@pytest.fixture
def t(tmp_path):
    return Table(tmp_path)


# ── the rules ────────────────────────────────────────────────────────────────
def test_the_squares_are_numbered_as_checkers_notation_numbers_them():
    assert ck.place(1) == (0, 1) and ck.place(4) == (0, 7)
    assert ck.place(5) == (1, 0) and ck.place(32) == (7, 6)
    assert all(ck.square(*ck.place(s)) == s for s in range(1, 33))
    assert (
        ck.square(0, 0) is None and ck.square(8, 1) is None and ck.square(-1, 0) is None
    )


def test_black_opens_with_the_seven_moves_of_the_game():
    assert moves(ck.start(), "black") == ["10-14", "10-15", "11-15", "11-16", "12-16", "9-13", "9-14"]  # fmt: skip
    assert moves(ck.start(), "white") == ["21-17", "22-17", "22-18", "23-18", "23-19", "24-19", "24-20"]  # fmt: skip


def test_a_jump_is_a_must_and_a_step_is_refused_while_there_is_one():
    board = {15: "b", 19: "w", 9: "b"}
    assert moves(board, "black") == ["15x24"]
    with pytest.raises(ValueError, match="a jump is a must"):
        ck.find(board, "black", "9-13")


def test_a_man_moves_forward_only_and_a_king_both_ways():
    assert moves({14: "b", 32: "w"}, "black") == ["14-17", "14-18"]
    assert moves({14: "w", 1: "b"}, "white") == ["14-10", "14-9"]
    assert moves({14: "B", 32: "w"}, "black") == ["14-10", "14-17", "14-18", "14-9"]


def test_a_jump_of_several_pieces_is_taken_whole_named_either_way():
    board = {1: "b", 6: "w", 15: "w", 32: "w"}
    assert moves(board, "black") == ["1x10x19"]
    for text in ("1x10x19", "1x19"):
        mv = ck.find(board, "black", text)
        assert mv[1] == {6, 15} and ck.apply(board, mv) == {19: "b", 32: "w"}
    with pytest.raises(ValueError, match="1x10x19"):
        ck.find(board, "black", "1x10")  # stopping half way is not a move


def test_a_jump_two_paths_make_must_name_each_landing():
    board = {
        30: "B",
        5: "w",
        9: "w",
        11: "w",
        26: "w",
        10: "w",
        19: "w",
        18: "w",
        29: "w",
    }
    with pytest.raises(ValueError, match="name each landing"):
        ck.find(board, "black", "30x23")
    mv = ck.find(board, "black", "30x23x14x7x16x23")
    assert ck.written(mv) == "30x23x14x7x16x23"


def test_a_man_crowned_mid_jump_stops_there():
    board = {22: "b", 26: "w", 27: "w"}
    assert moves(board, "black") == [
        "22x31"
    ]  # as a king it could go on over 27; it may not
    assert ck.apply(board, ck.find(board, "black", "22x31")) == {31: "B", 27: "w"}
    assert ck.apply({27: "b", 8: "w"}, ck.find({27: "b", 8: "w"}, "black", "27-32"))[32] == "B"  # fmt: skip


def test_the_square_a_piece_leaves_is_empty_while_it_jumps():
    """A king can land again on the square it set out from: four pieces round
    a ring, back to 11. (game-lab's self-play left the square full, so there
    this jump was missing.)"""
    board = {11: "B", 15: "w", 23: "w", 16: "w", 24: "w", 1: "w"}
    assert "11x18x27x20x11" in moves(board, "black")
    after = ck.apply(board, ck.find(board, "black", "11x18x27x20x11"))
    assert after == {11: "B", 1: "w"}


def test_a_side_with_no_piece_or_no_move_has_lost():
    assert ck.ending({19: "b"}, "white") == "black won"
    assert (
        ck.ending({29: "w", 25: "b", 22: "b"}, "white") == "black won"
    )  # 29 is hemmed in
    assert ck.ending(ck.start(), "black") == "on"


def test_what_isnt_a_move_says_what_is():
    for text, says in (("11_15", "isn't a move"), ("0-4", "isn't a move"),
                       ("33-29", "squares are 1 to 32"), ("11-14", "11-15")):  # fmt: skip
        with pytest.raises(ValueError, match=says):
            ck.find(ck.start(), "black", text)


def test_a_side_with_no_move_is_told_none():
    with pytest.raises(ValueError, match="may play none"):
        ck.find({29: "w", 25: "b", 22: "b"}, "white", "29-25")


def test_the_picture_shows_every_piece_and_the_numbers_of_each_row():
    pic = ck.picture({1: "b", 32: "W"}).splitlines()
    assert len(pic) == 8 and pic[0].split()[0] == "b" and pic[0].endswith("1-4")
    assert pic[7].split()[3] == "W" and pic[7].endswith("29-32")


# ── the record ───────────────────────────────────────────────────────────────
def test_new_opens_a_game_and_each_move_is_a_row(t):
    got = t.run("new")
    assert got.returncode == 0 and "black moves first" in got.stdout
    t.play("11-15", "23-19")
    open_, *ms = [r for r in t.rows() if r["kind"] in ck.KINDS]
    assert open_["kind"] == ck.OPEN and open_["first"] == "black"
    assert [(m["side"], m["move"], m["ply"], m["result"], m["game"]) for m in ms] == [
        ("black", "11-15", 0, "on", open_["n"]), ("white", "23-19", 1, "on", open_["n"])]  # fmt: skip
    assert t.run("check").returncode == 0 and t.k("verify").returncode == 0


def test_a_move_the_rules_dont_allow_is_refused_and_writes_nothing(t):
    t.run("new")
    before = t.raw()
    for m in ("11-14", "23-19", "nonsense"):
        got = t.run("move", m)
        assert got.returncode == 2 and "refused" in got.stderr
    assert t.raw() == before


def test_nothing_is_played_before_a_game_is_opened(t):
    for argv in (("move", "11-15"), ("resign",), ("offer",), ("settle",), ("show",)):
        got = t.run(*argv)
        assert got.returncode == 2 and "no game is open" in got.stderr


def test_show_says_whose_turn_and_what_they_may_play(t):
    t.run("new")
    t.play("11-15")
    got = t.run("show")
    assert got.returncode == 0 and "after 1 moves: on" in got.stdout
    assert "white to move: 21-17, 22-17, 22-18" in got.stdout


def test_a_game_won_on_the_board_ends_it(t):
    """The shortest loss there is: black walks into a jump it can't answer."""
    t.run("new")
    ply = 0
    while True:
        rows = t.rows()
        st = ck.state(ck.current(rows))
        if st["result"] != "on":
            break
        mv = ck.legal(st["board"], st["to_move"])[0]
        t.play(ck.written(mv))
        ply += 1
    assert (
        st["result"] in ("black won", "white won")
        and t.rows()[-1]["result"] == st["result"]
    )
    got = t.run("move", "11-15")
    assert got.returncode == 2 and "the game is over" in got.stderr
    assert t.run("check").returncode == 0
    assert t.run("new").returncode == 0  # a second game, once the first is over


def test_a_new_game_while_one_is_on_is_refused(t):
    t.run("new")
    got = t.run("new")
    assert got.returncode == 2 and "isn't over" in got.stderr


def test_the_side_to_move_resigns(t):
    t.run("new")
    t.play("11-15")
    got = t.run("resign")
    assert got.returncode == 0 and "white resigns: black won" in got.stdout
    r = t.rows()[-1]
    assert (r["kind"], r["side"], r["result"]) == (ck.RESIGN, "white", "black won")
    assert t.run("check").returncode == 0
    assert t.run("resign").returncode == 2


# ── a draw is the ruler's ────────────────────────────────────────────────────
def test_offer_hands_the_draw_in_through_the_kernel_and_waits(t):
    t.run("new")
    t.play("11-15", "23-19")
    got = t.run("offer")
    assert got.returncode == 42 and "waits on the table's ruler" in got.stdout
    ask = t.rows()[-1]
    assert ask["kind"] == ck.ASK and ask["ply"] == 2
    assert ask["subject"] == kernel.subject_of(ck.draw_proposal(t.game(), 2))
    assert any(
        r["kind"] == "proposal" and r["subject"] == ask["subject"] for r in t.rows()
    )
    assert t.run("check").returncode == 0


def test_nothing_is_played_while_a_draw_waits(t):
    t.run("new")
    t.run("offer")
    before = t.raw()
    for argv in (("move", "11-15"), ("resign",), ("offer",)):
        assert t.run(*argv).returncode == 2
    got = t.run("settle")
    assert got.returncode == 42 and "nothing moves" in got.stdout
    assert t.raw() == before
    assert "a draw waits on the seal" in t.run("show").stdout


def test_a_seal_ends_the_game_drawn_and_the_row_names_it(t):
    t.run("new")
    t.play("11-15")
    t.run("offer")
    subj = t.subject()
    assert t.k("seal", subj).returncode == 0
    got = t.run("settle")
    assert got.returncode == 0 and "a draw" in got.stdout
    seal, r = [x for x in t.rows() if x["kind"] == "seal"][-1], t.rows()[-1]
    assert (r["kind"], r["verdict"], r["ruling_row"], r["subject"]) == (ck.RULING, "sealed", seal["n"], subj)  # fmt: skip
    assert seal["who"] == "human"
    assert "over (draw)" in t.run("move", "23-19").stderr
    assert t.run("check").returncode == 0


def test_a_decline_plays_on(t):
    t.run("new")
    t.run("offer")
    assert t.k("decline", t.subject()).returncode == 0
    got = t.run("settle")
    assert got.returncode == 0 and "play on" in got.stdout
    assert t.rows()[-1]["verdict"] == "declined"
    t.play("11-15")
    assert t.run("offer").returncode == 42  # offered again, later, as its own draw
    assert t.run("check").returncode == 0


def test_settle_with_no_draw_waiting_is_refused(t):
    t.run("new")
    got = t.run("settle")
    assert got.returncode == 2 and "no draw waits" in got.stderr


def test_a_seal_without_the_keys_proof_moves_nothing(t):
    t.run("new")
    t.run("offer")
    t.forge("seal", subject=t.subject(), bite_key="0" * 64, proof="0" * 64)
    before = t.raw()
    got = t.run("settle")
    assert got.returncode == 42 and t.raw() == before


def test_a_seal_over_another_proposal_moves_nothing(t):
    t.run("new")
    t.play("11-15")
    t.run("offer")
    other = kernel.subject_of(ck.draw_proposal(t.game(), 0))  # not this draw
    t.forge("seal", subject=other, bite_key="0" * 64, proof="0" * 64)
    assert t.run("settle").returncode == 42


def test_the_add_on_never_seals_or_declines(t):
    t.run("new")
    t.run("offer")
    t.run("settle")
    assert not [
        r for r in t.rows() if r["kind"] in ("seal", "decline") or r["who"] == "human"
    ]


# ── check ────────────────────────────────────────────────────────────────────
def test_check_on_a_record_with_no_game_holds(t):
    got = t.run("check")
    assert got.returncode == 0 and "0 games" in got.stdout


def test_check_accepts_the_honest_forgery_so_the_next_ones_mean_something(t):
    t.run("new")
    t.forge(ck.MOVE, game=t.game(), ply=0, side="black", move="11-15", result="on")
    assert t.run("check").returncode == 0


@pytest.mark.parametrize(
    "fields, says",
    [
        ({"side": "white", "move": "23-19"}, "it was black's turn"),
        ({"move": "11-14"}, "isn't a move black may make"),
        ({"move": "11-15", "result": "black won"}, "the board says on"),
        ({"move": "11x15"}, "isn't a move black may make"),
    ],
)
def test_check_finds_a_move_row_the_board_doesnt_give(t, fields, says):
    t.run("new")
    t.forge(ck.MOVE, **{"game": t.game(), "ply": 0, "side": "black", "move": "11-15", "result": "on", **fields})  # fmt: skip
    got = t.run("check")
    assert got.returncode == 2 and says in got.stderr
    assert "don't hold" in t.run("show").stderr  # and nothing is played on it


def test_check_finds_a_move_not_written_as_the_move_it_is(t, monkeypatch):
    """1x19 names the jump 1x10x19; the row must write it whole."""
    monkeypatch.setattr(ck, "start", lambda: {1: "b", 6: "w", 15: "w", 32: "w"})
    rows = [{"n": 0, "kind": ck.OPEN},
            {"n": 1, "kind": ck.MOVE, "game": 0, "ply": 0, "side": "black", "move": "1x19", "result": "on"}]  # fmt: skip
    assert "isn't written as the move it is, 1x10x19" in ck.check(t.box, rows)[1]
    rows[1]["move"] = "1x10x19"
    assert ck.check(t.box, rows) == (1, None)


def test_check_finds_a_row_after_the_game_ended(t):
    t.run("new")
    t.run("resign")
    t.forge(ck.MOVE, game=t.game(), ply=0, side="black", move="11-15", result="on")
    got = t.run("check")
    assert got.returncode == 2 and "already over (white won)" in got.stderr


def test_check_finds_a_resignation_by_the_wrong_side_or_with_the_wrong_result(t):
    t.run("new")
    t.forge(ck.RESIGN, game=t.game(), ply=0, side="white", result="black won")
    assert "only the side to move" in t.run("check").stderr


def test_check_finds_a_resignation_that_reports_the_wrong_winner(t):
    t.run("new")
    t.forge(ck.RESIGN, game=t.game(), ply=0, side="black", result="black won")
    assert "is white won" in t.run("check").stderr


def test_check_finds_a_row_whose_game_was_never_opened(t):
    t.forge(ck.MOVE, game=0, ply=0, side="black", move="11-15", result="on")
    got = t.run("check")
    assert got.returncode == 2 and "isn't a game opened before it" in got.stderr


def test_check_finds_a_draw_ruled_with_no_seal(t):
    t.run("new")
    t.run("offer")
    t.forge(
        ck.RULING, game=t.game(), subject=t.subject(), verdict="sealed", ruling_row=1
    )
    got = t.run("check")
    assert got.returncode == 2 and "nobody sealed or declined it" in got.stderr


def test_check_finds_a_ruling_that_reports_the_wrong_answer(t):
    t.run("new")
    t.run("offer")
    assert t.k("decline", t.subject()).returncode == 0
    no = t.rows()[-1]["n"]
    t.forge(
        ck.RULING, game=t.game(), subject=t.subject(), verdict="sealed", ruling_row=no
    )
    assert "the person's answer is declined" in t.run("check").stderr


def test_check_finds_a_ruling_on_no_draw(t):
    t.run("new")
    t.forge(ck.RULING, game=t.game(), subject="proposal:" + "0" * 64, verdict="sealed", ruling_row=1)  # fmt: skip
    assert "a ruling on no draw" in t.run("check").stderr


def test_check_finds_a_draw_that_never_passed_the_kernels_door(t):
    t.run("new")
    subj = kernel.subject_of(ck.draw_proposal(t.game(), 0))
    t.forge(ck.ASK, game=t.game(), ply=0, subject=subj)
    assert "never passed the kernel's door" in t.run("check").stderr


def test_check_finds_a_draw_that_isnt_the_one_this_game_hands_in(t):
    t.run("new")
    t.forge(ck.ASK, game=t.game(), ply=3, subject="proposal:" + "0" * 64)
    assert "isn't the draw this game handed in after 0 moves" in t.run("check").stderr


def test_check_finds_a_second_draw_while_one_waits_or_a_move_under_it(t):
    t.run("new")
    t.run("offer")
    ask = t.rows()[-1]
    t.forge(ck.ASK, game=t.game(), ply=0, subject=ask["subject"])
    assert "a draw was already waiting" in t.run("check").stderr


def test_check_finds_a_move_played_while_a_draw_waited(t):
    t.run("new")
    t.run("offer")
    t.forge(ck.MOVE, game=t.game(), ply=0, side="black", move="11-15", result="on")
    assert "nothing is played until it's settled" in t.run("check").stderr


def test_a_record_that_doesnt_verify_is_refused(t):
    t.run("new")
    raw = t.raw()
    assert raw.count(b"black") == 1
    (t.box / "record.jsonl").write_bytes(raw.replace(b"black", b"white"))
    got = t.run("show")
    assert got.returncode == 2 and "doesn't verify" in got.stderr


def test_a_command_line_that_isnt_one_is_refused(t, tmp_path):
    for argv in ((), ("move",), ("move", "11-15", "15-19"), ("fly",), ("new", "x")):
        assert t.run(*argv).returncode == 2
    got = subprocess.run([sys.executable, str(HERE / "checkers.py"), "--box", str(tmp_path / "none"), "new"],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    got = subprocess.run([sys.executable, str(HERE / "checkers.py"), "new"], capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 2
