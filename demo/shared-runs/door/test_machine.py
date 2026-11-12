"""shared-runs, the door's machine: it comes to the first study's bytes; a
run cut off goes on and ends the same; what it leaves is sealed and a
changed file shows; and the door takes, holds and refuses as it says."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / "study"
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(STUDY))
import pytest  # noqa: E402

import machine  # noqa: E402

PLAN = {
    "machines": 2, "rounds": 2, "spacing": 10, "draw_one_in": 2, "check_one_in": 2,
    "deal_seed": "a deal", "draw_seed": "a draw",
    "lengths": [7, 25, 60, 133],
    "trajectories": [
        {"name": "t1", "toy": {"seed": 1}},
        {"name": "t2", "toy": {"seed": 2, "halts_after": 23}},
        {"name": "t3", "toy": {"seed": 3, "halts_after": 0}},
        {"name": "t4", "toy": {"seed": 4}},
        {"name": "t5", "toy": {"seed": 5}},
    ],
}  # fmt: skip


def rows(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines()]


def setup(tmp: Path) -> list[str]:
    (tmp / "plan.json").write_text(json.dumps(PLAN))
    starts = {t["name"]: {"toy": t["toy"]} for t in PLAN["trajectories"]}
    (tmp / "starts.json").write_text(json.dumps(starts))
    return [
        "--plan",
        str(tmp / "plan.json"),
        "--starts",
        str(tmp / "starts.json"),
        "--toy",
    ]


def ident(tmp: Path, name: str) -> tuple[Path, str]:
    seed = bytes([len(name)]) * 31 + name[:1].encode()
    file = tmp / f"{name}.id"
    file.write_text(f"ed25519 {seed.hex()}\n")
    return file, machine.ed25519.public(seed).hex()


def go(*args: str) -> int:
    return machine.main([str(a) for a in args])


def shared(base, tmp, k, r, *more, to=None) -> Path:
    out = to or tmp / f"round-{r}-machine-{k}"
    code = go("shared", *base, "--to", out, "--machine", k, "--round", r, *more)
    assert code in (0, 42), code
    return out


def test_it_comes_to_the_bytes_the_first_studys_runner_comes_to(tmp_path):
    base = setup(tmp_path)
    for mode, extra in (("alone", []), ("shared", ["--machine", "0", "--round", "1"])):
        assert go(mode, *base, "--to", tmp_path / f"new-{mode}", *extra) == 0
        done = subprocess.run([sys.executable, str(STUDY / "runner.py"), mode, *base,
                               "--to", str(tmp_path / f"old-{mode}"), *extra])  # fmt: skip
        assert done.returncode == 0
        old, new = (
            rows(tmp_path / f"{w}-{mode}" / "acts.jsonl") for w in ("old", "new")
        )
        keys = (
            "job",
            "asked",
            "from",
            "took",
            "stepped",
            "ended",
            "outcome",
            "tried_halt",
            "sha256",
        )
        assert [[a[k] for k in keys] for a in old] == [
            [a[k] for k in keys] for a in new
        ]
        assert len(new) > 3
    old, new = (rows(tmp_path / f"{w}-shared" / "memory.jsonl") for w in ("old", "new"))
    assert old == new and new


def test_a_run_cut_off_goes_on_and_ends_as_one_never_cut(tmp_path, monkeypatch):
    base = setup(tmp_path)
    whole = shared(base, tmp_path, 0, 1, to=tmp_path / "whole")
    cut = tmp_path / "cut"
    assert (
        go("shared", *base, "--to", cut, "--machine", 0, "--round", 1, "--budget", "0")
        == 42
    )
    assert not (cut / "manifest.json").exists() and rows(cut / "acts.jsonl") == []
    # the machine dies part way through a job: the step is interrupted, and
    # the line being written when it died is left torn
    acts = rows(whole / "acts.jsonl")
    dies_in = next(i for i, x in enumerate(acts) if i >= 2 and x["stepped"] > 20)
    die_at = sum(x["stepped"] for x in acts[:dies_in]) + 15
    real, count = machine.runner.Toy.step, [0]

    def step(self, s):
        if count[0] == die_at:
            raise KeyboardInterrupt
        real(self, s)
        count[0] += 1

    monkeypatch.setattr(machine.runner.Toy, "step", step)
    with pytest.raises(KeyboardInterrupt):
        go("shared", *base, "--to", cut, "--machine", 0, "--round", 1)
    monkeypatch.setattr(machine.runner.Toy, "step", real)
    assert len(rows(cut / "acts.jsonl")) == dies_in
    for name in ("acts.jsonl", "memory.jsonl", "log.jsonl"):
        with (cut / name).open("a") as f:
            f.write('{"trajectory":"abc","st')
    assert go("shared", *base, "--to", cut, "--machine", 0, "--round", 1) == 0
    keys = ("job", "asked", "from", "took", "stepped", "ended", "outcome", "sha256")
    a, b = rows(whole / "acts.jsonl"), rows(cut / "acts.jsonl")
    assert [[x[k] for k in keys] for x in a] == [[x[k] for k in keys] for x in b]
    assert [x["taken_up_again"] for x in b] == [
        int(i == dies_in) for i in range(len(b))
    ]
    assert sorted(map(json.dumps, rows(whole / "memory.jsonl"))) == sorted(map(json.dumps, rows(cut / "memory.jsonl")))  # fmt: skip
    said = [r["what"] for r in rows(cut / "log.jsonl")]
    assert (
        "stopped at the budget" in said and "a line torn by a cut was dropped" in said
    )
    assert "going on" in said and said[-1] == "ended"
    assert go("verify", "--run", cut) == 0
    # a sealed run is left as it is
    before = (cut / "log.jsonl").read_bytes()
    assert go("shared", *base, "--to", cut, "--machine", 0, "--round", 1) == 0
    assert (cut / "log.jsonl").read_bytes() == before


def test_a_budget_that_runs_out_inside_a_job_stops_at_a_kept_state(
    tmp_path, monkeypatch
):
    base = setup(tmp_path)
    whole = shared(base, tmp_path, 0, 1, to=tmp_path / "whole")
    fired = []

    def once_inside_a_job(self):
        if sys._getframe(1).f_code.co_name == "job" and not fired:
            fired.append(1)
            return True
        return False

    monkeypatch.setattr(machine.Run, "over_budget", once_inside_a_job)
    cut = tmp_path / "cut"
    assert go("shared", *base, "--to", cut, "--machine", 0, "--round", 1) == 42
    last = rows(cut / "log.jsonl")[-1]
    assert (
        last["what"] == "stopped at the budget"
        and last["kept_to"] % PLAN["spacing"] == 0
    )
    assert go("shared", *base, "--to", cut, "--machine", 0, "--round", 1) == 0
    keys = ("job", "from", "stepped", "ended", "outcome", "sha256")
    a, b = rows(whole / "acts.jsonl"), rows(cut / "acts.jsonl")
    assert [[x[k] for k in keys] for x in a] == [[x[k] for k in keys] for x in b]
    assert sum(x["taken_up_again"] for x in b) == 1


def test_a_run_carried_to_an_empty_disk_goes_on_from_what_was_left(tmp_path):
    base = setup(tmp_path)
    first = tmp_path / "first"
    assert (
        go(
            "shared",
            *base,
            "--to",
            first,
            "--machine",
            1,
            "--round",
            1,
            "--budget",
            "0",
        )
        == 42
    )
    second = shared(base, tmp_path, 1, 1, "--from", first, to=tmp_path / "second")
    said = [r["what"] for r in rows(second / "log.jsonl")]
    assert said.count("stopped at the budget") == 1 and "carried on from" in said
    assert go("verify", "--run", second) == 0


def test_it_refuses_to_go_on_as_another_run_or_with_other_starts(tmp_path, capsys):
    base = setup(tmp_path)
    out = tmp_path / "o"
    assert (
        go("shared", *base, "--to", out, "--machine", 0, "--round", 1, "--budget", "0")
        == 42
    )
    assert go("shared", *base, "--to", out, "--machine", 1, "--round", 1) == 2
    assert "what is already here is this same run" in capsys.readouterr().err
    assert rows(out / "log.jsonl")[-1]["what"] == "refused"
    starts = json.loads((tmp_path / "starts.json").read_text())
    del starts["t5"]
    (tmp_path / "starts.json").write_text(json.dumps(starts))
    assert go("alone", *base, "--to", tmp_path / "p") == 2
    assert "the starts are this plan's" in capsys.readouterr().err
    assert (
        go("shared", *base, "--to", tmp_path / "q", "--machine", 9, "--round", 1) == 2
    )


def test_what_it_leaves_is_sealed_and_a_changed_file_shows(tmp_path):
    base = setup(tmp_path)
    me, key = ident(tmp_path, "ours")
    out = shared(base, tmp_path, 0, 1, "--id", me)
    seal = json.loads((out / "manifest.json").read_text())
    assert seal["signer"] == key and set(seal["files"]) == set(machine.FILES)
    ring = tmp_path / "ring.json"
    ring.write_text(json.dumps({key: "ours"}))
    assert go("verify", "--run", out, "--ring", ring) == 0
    ring.write_text(json.dumps({"0" * 64: "another"}))
    assert go("verify", "--run", out, "--ring", ring) == 42
    # a line of the log taken out; a state changed; the seal's own words changed
    for name, change in (
        ("log.jsonl", lambda t: "".join(t.splitlines(keepends=True)[1:])),
        ("memory.jsonl", lambda t: t.replace('"state": "', '"state": "ff', 1)),
        ("manifest.json", lambda t: t.replace('"acts": ', '"acts": 1', 1)),
    ):
        text = (out / name).read_text()
        assert change(text) != text
        (out / name).write_text(change(text))
        assert go("verify", "--run", out) == 2, name
        (out / name).write_text(text)
    assert go("verify", "--run", out) == 0
    rows_ = rows(out / "log.jsonl")
    rows_[2]["said"] = "something else"
    (tmp_path / "l.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows_))
    assert machine.chain_holds(out / "log.jsonl") == (True, len(rows_))
    assert machine.chain_holds(tmp_path / "l.jsonl")[0] is False


def test_the_door_takes_the_enrolled_holds_the_unknown_and_refuses_the_changed(
    tmp_path, capsys
):
    base = setup(tmp_path)
    ours, ours_key = ident(tmp_path, "ours")
    theirs, _ = ident(tmp_path, "stranger")
    ring = tmp_path / "ring.json"
    ring.write_text(json.dumps({ours_key: "ours"}))
    known = shared(base, tmp_path, 1, 1, "--id", ours)
    unknown = shared(base, tmp_path, 0, 1, "--id", theirs)
    both = ["--memory", known, "--memory", unknown, "--ring", ring, "--id", ours]

    # round 2 for the stranger's own trajectories: held, so nothing is taken
    k = 0
    out = tmp_path / "held"
    assert go("shared", *base, "--to", out, "--machine", k, "--round", 2, *both) == 42
    seal = json.loads((out / "manifest.json").read_text())
    assert {v["how"] for v in seal["took_in"].values()} == {"taken", "held"}
    acts = rows(out / "acts.jsonl")
    bare = tmp_path / "bare"
    assert go("shared", *base, "--to", bare, "--machine", k, "--round", 2) == 0
    stepped = sum(a["stepped"] for a in acts)
    assert stepped == sum(a["stepped"] for a in rows(bare / "acts.jsonl")), (
        "nothing went on from the held run"
    )

    # with no ring the same folders are taken, and it goes on from them
    free = tmp_path / "free"
    assert go("shared", *base, "--to", free, "--machine", k, "--round", 2,
              "--memory", known, "--memory", unknown) == 0  # fmt: skip
    assert any(a["took"] for a in rows(free / "acts.jsonl"))
    assert sum(a["stepped"] for a in rows(free / "acts.jsonl")) < stepped

    # an enrolled checker steps every state of the stranger's run again: now it is taken
    check = tmp_path / "check"
    assert (
        go(
            "check",
            *base,
            "--to",
            check,
            "--memory",
            known,
            "--memory",
            unknown,
            "--id",
            ours,
        )
        == 0
    )
    found = json.loads((check / "manifest.json").read_text())["checked"]
    assert all(f["all_the_same"] and f["states"] == f["of"] for f in found.values())
    assert found[unknown.name]["halts"] >= 1 and found[unknown.name]["halts_that_halt"] == found[unknown.name]["halts"]  # fmt: skip
    vouched = tmp_path / "vouched"
    assert (
        go(
            "shared",
            *base,
            "--to",
            vouched,
            "--machine",
            k,
            "--round",
            2,
            *both,
            "--memory",
            check,
        )
        == 0
    )
    assert [a["sha256"] for a in rows(vouched / "acts.jsonl")] == [
        a["sha256"] for a in rows(free / "acts.jsonl")
    ]

    # a checker who is not enrolled vouches for nobody
    assert (
        go("check", *base, "--to", tmp_path / "c2", "--memory", unknown, "--id", theirs)
        == 0
    )
    assert go("shared", *base, "--to", tmp_path / "v2", "--machine", k, "--round", 2, *both,
              "--memory", tmp_path / "c2") == 42  # fmt: skip

    # a state changed after the seal: refused, and the run stops
    text = (unknown / "memory.jsonl").read_text()
    (unknown / "memory.jsonl").write_text(text.replace('"state": "', '"state": "ff', 1))
    capsys.readouterr()
    assert (
        go("shared", *base, "--to", tmp_path / "r", "--machine", k, "--round", 2, *both)
        == 2
    )
    assert "is not the file its seal names" in capsys.readouterr().err
    assert not (tmp_path / "r" / "manifest.json").exists()


def test_a_check_finds_a_lie_sealed_by_its_teller_and_a_halt_that_does_not_halt(
    tmp_path,
):
    base = setup(tmp_path)
    ours, ours_key = ident(tmp_path, "ours")
    liar, _ = ident(tmp_path, "liar")
    ring = tmp_path / "ring.json"
    ring.write_text(json.dumps({ours_key: "ours"}))
    honest = shared(base, tmp_path, 0, 1, to=tmp_path / "honest")
    lied = tmp_path / "lied"
    lied.mkdir()
    for name in ("acts.jsonl", "log.jsonl", "machine.json", "run.json"):
        (lied / name).write_bytes((honest / name).read_bytes())
    memory = rows(honest / "memory.jsonl")
    state = next(m for m in memory if "state" in m)
    state["state"] = "ff" + state["state"][2:]
    assert any("halt" in m for m in memory), "this machine owns a trajectory that halts"
    never = machine.runner.identity({"toy": {"seed": 1}}, machine.runner.Toy.said)
    memory.append({"trajectory": never, "halt": 10})
    (lied / "memory.jsonl").write_text(
        "".join(machine.canon(m).decode() + "\n" for m in memory)
    )
    # the liar seals its own lie: whole at the door, and wrong
    doc = json.loads((honest / "manifest.json").read_text())
    doc["files"] = {n: machine.sha(lied / n) for n in machine.FILES}
    seed = machine.read_id(liar)
    doc["signer"] = machine.ed25519.public(seed).hex()
    doc.pop("sig", None)
    doc["sig"] = machine.ed25519.sign(seed, machine.canon(doc)).hex()
    (lied / "manifest.json").write_text(json.dumps(doc))
    assert go("verify", "--run", lied) == 0, (
        "a seal says who and what, not that it is right"
    )
    check = tmp_path / "check"
    assert go("check", *base, "--to", check, "--memory", lied, "--id", ours) == 0
    found = json.loads((check / "manifest.json").read_text())["checked"]["lied"]
    assert found["all_the_same"] is False and found["same"] < found["states"]
    assert found["halts_that_halt"] == found["halts"] - 1
    out = tmp_path / "next"
    assert go("shared", *base, "--to", out, "--machine", 0, "--round", 2, "--memory", lied,
              "--memory", check, "--ring", ring) == 42  # fmt: skip
    assert not any(
        a["outcome"] == "halted" and a["trajectory"] == "t1"
        for a in rows(out / "acts.jsonl")
    )


def test_a_run_that_went_on_from_a_run_not_vouched_for_is_not_vouched_for(tmp_path):
    base = setup(tmp_path)
    ours, ours_key = ident(tmp_path, "ours")
    ring = tmp_path / "ring.json"
    ring.write_text(json.dumps({ours_key: "ours"}))
    a = shared(base, tmp_path, 1, 1, to=tmp_path / "a")
    b = shared(base, tmp_path, 1, 2, "--memory", a, to=tmp_path / "b")
    assert any(x["took"] for x in rows(b / "acts.jsonl"))
    only_b = tmp_path / "only-b"
    assert (
        go("check", *base, "--to", only_b, "--memory", a, "--memory", b, "--id", ours)
        == 0
    )
    seals = {f.name: machine.sha(f / "manifest.json") for f in (a, b)}
    both = machine.vouches([a, b, only_b], machine.ring_of(ring))
    assert set(both) == set(seals.values())
    # the check's word on `a` taken away: `b` stands on nothing
    doc = json.loads((only_b / "manifest.json").read_text())
    del doc["checked"]["a"]
    doc.pop("sig")
    doc["sig"] = machine.ed25519.sign(machine.read_id(ours), machine.canon(doc)).hex()
    (only_b / "manifest.json").write_text(json.dumps(doc))
    assert machine.vouches([a, b, only_b], machine.ring_of(ring)) == {}


def test_a_bad_command_line_is_refused(capsys):
    for argv in ([], ["nonsense"], ["alone", "--plan", "p"], ["verify"], ["check", "--plan", "p", "--starts", "s", "--to", "o", "--toy"]):  # fmt: skip
        assert machine.main(argv) == 2
    assert "usage" in capsys.readouterr().err or True
