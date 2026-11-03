"""share: a sealed answer packed, received, forwarded and corrected, between
boxes that each keep their own chain; and every way a package can be wrong."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SHARE = HERE / "share.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]
sys.path.insert(0, str(HERE))
import ed25519  # noqa: E402

#: RFC 8032 section 7.1, tests 1 to 3; then three made with an audited
#: library (pyca/cryptography 50.0.1) and frozen: (seed, public, message, signature)
VECTORS = [
    ("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
     "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", "",
     "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
    ("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
     "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", "72",
     "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
    ("c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
     "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025", "af82",
     "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac18ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a"),
    ("a407c2ce7a1ae95d0f5dcd89610b98d31905afe4469d78c310c3030622637310",
     "8c2f9291312c371cb12e3e91cae51f14349ff61568d78e277f50c13c8fb481db",
     "ca0df2c95aa144c1d0ff2ff3c8f967fdc1de9ef0c4120b3726416701b519d619",
     "6162bfebe74cb61fdb6696e13891cad3e3eb19eda87560e43d383a6103089f8ee529b233f5785fa1160813f57d47cadf5a4e53f4c354864cfc7b6ef60263fc09"),
    ("ff19f3276d452bbdd621d9a38ffe3c1079dd72dedf80894e442cf0c1c703ebec",
     "610ac6efc15372e1ad54c9b731112609da1fb653eeaf06c2ae82bcdc15f497f1",
     "29c1b289e7522195b362e44f54e05470b69ad20540ab60a18a05e5bf6951f13d29c1b289e7522195b362e44f54e05470b69ad20540ab60a18a05e5bf6951f13d",
     "540510dfea7b953fcd67a286ca685799f13d5d041861a514b4a98c51e0becc9ab831f0260e2fb6787da7c25bd0060c785a97a7f1c4d1ce9412451598e5263c03"),
    ("ad480cc0506ec9ed768e172ce31de644ec1b2fb0206339f7b812627eabf55613",
     "4d5d8190b1776f3c26910166e1bbc3be86f5fdfafcad860360b641fea7360dfc",
     "153812ae5fea0b73a011bf28bd7cea93644437c3fe3260b7b2d7e1e2f9f46bde" * 3,
     "85994bba7fbee0357756f9de6658e68ef5a060289d96469dc2442684842ae9be7650be59437a0c92b71a78f5b84973589f81578175e959d67b529bfe49180b07"),
]  # fmt: skip


# ── the signatures ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("seed, pub, msg, sig", VECTORS)
def test_ed25519_makes_and_checks_the_known_signatures(seed, pub, msg, sig):
    seed, msg = bytes.fromhex(seed), bytes.fromhex(msg)
    assert ed25519.public(seed).hex() == pub
    assert ed25519.sign(seed, msg).hex() == sig
    assert ed25519.check(bytes.fromhex(pub), msg, bytes.fromhex(sig))


@pytest.mark.parametrize("seed, pub, msg, sig", VECTORS[:3])
def test_ed25519_refuses_any_bit_changed(seed, pub, msg, sig):
    pub, msg, sig = bytes.fromhex(pub), bytes.fromhex(msg), bytes.fromhex(sig)
    for i in range(0, 512, 37):
        bad = bytearray(sig)
        bad[i // 8] ^= 1 << (i % 8)
        assert not ed25519.check(pub, msg, bytes(bad)), i
    assert not ed25519.check(pub, msg + b"x", sig)
    other = bytes.fromhex(VECTORS[3][1])
    assert not ed25519.check(other, msg, sig)


def test_ed25519_refuses_what_isnt_a_key_or_a_signature():
    seed, pub, msg, sig = (bytes.fromhex(x) for x in VECTORS[1])
    assert not ed25519.check(pub[:31], msg, sig)
    assert not ed25519.check(pub, msg, sig[:63])
    assert not ed25519.check(pub.hex(), msg, sig)  # text, not bytes
    big_s = sig[:32] + (int.from_bytes(sig[32:], "little") + ed25519.L).to_bytes(
        32, "little"
    )
    assert not ed25519.check(pub, msg, big_s), "s past the group order is malleable"
    not_on_curve = (2).to_bytes(32, "little")  # y = 2 has no x
    assert not ed25519.check(not_on_curve, msg, sig)
    assert not ed25519.check(pub, msg, not_on_curve + sig[32:])
    with pytest.raises(ValueError):
        ed25519.sign(seed[:31], msg)


# ── boxes ───────────────────────────────────────────────────────────────────
def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *map(str, argv)], capture_output=True,
                          text=True, stdin=subprocess.DEVNULL)  # fmt: skip


def share(*argv) -> subprocess.CompletedProcess:
    return run(SHARE, *argv)


class Person:
    def __init__(self, root: Path, name: str, text: str = "Nothing much.\n"):
        self.dir = root / name
        (self.dir / "pile").mkdir(parents=True)
        (self.dir / "pile" / "notes.md").write_text(text)
        self.box, self.id = self.dir / "box", self.dir / "id"
        got = run(KERNEL, "init", "--box", self.box, "--pile", self.dir / "pile",
                  "--key", self.dir / "key", *NOW)  # fmt: skip
        assert got.returncode == 0, got.stderr
        got = share("id", "--to", self.id)
        assert got.returncode == 0, got.stderr
        self.pub = got.stdout.strip()

    def rows(self) -> list[dict]:
        return [
            json.loads(x) for x in (self.box / "record.jsonl").read_text().splitlines()
        ]

    def seal(self, question: str, data: str) -> str:
        bite = json.loads(run(KERNEL, "bite", "--box", self.box, question, *NOW).stdout)
        cites = [bite["served"][0]["id"]]
        sug = self.dir / "s.jsonl"
        sug.write_text(json.dumps({"path": f"{len(self.rows())}.md", "data": data,
                                   "cites": cites, "claim": "my notes"}) + "\n")  # fmt: skip
        subj = run(
            KERNEL, "propose", "--box", self.box, "--file", sug, *NOW
        ).stdout.split()[1]
        assert run(KERNEL, "seal", "--box", self.box, subj, *NOW).returncode == 0
        return subj

    def send(
        self, subjects, to: "Person", out: Path, *more
    ) -> subprocess.CompletedProcess:
        return share("send", "--box", self.box, "--id", self.id, "--answer", ",".join(subjects),
                     "--for", to.pub, "--to", out, *NOW, *more)  # fmt: skip

    def receive(self, pkg: Path) -> subprocess.CompletedProcess:
        return share(
            "receive", "--box", self.box, "--id", self.id, "--package", pkg, *NOW
        )

    def forward(
        self, pkg: Path, to: "Person", out: Path, *more
    ) -> subprocess.CompletedProcess:
        return share("forward", "--box", self.box, "--id", self.id, "--package", pkg,
                     "--for", to.pub, "--to", out, *NOW, *more)  # fmt: skip

    def verify(self) -> str:
        return run(KERNEL, "verify", "--box", self.box).stdout.strip()


NOTES = "The roof leak started after the storm on 2026-03-03.\n\nThe quote is $2,140.\n"


@pytest.fixture
def three(tmp_path):
    a = Person(tmp_path, "a", NOTES)
    b, c = Person(tmp_path, "b"), Person(tmp_path, "c")
    out = tmp_path / "out"
    out.mkdir()
    s1 = a.seal("when did the roof leak start", "After the storm of 2026-03-03.")
    s2 = a.seal("how much is the quote", "$2,140.")
    return a, b, c, out, [s1, s2]


def load(p: Path) -> dict:
    return json.loads(p.read_text())


def dump(p: Path, pkg: dict) -> Path:
    p.write_text(json.dumps(pkg))
    return p


def resign(layer: dict, idfile: Path) -> dict:
    """The layer signed again by its sender: what a sender lying could do."""
    import share as sh  # noqa: PLC0415

    seed = bytes.fromhex(idfile.read_text().split()[1])
    layer["sig"] = ed25519.sign(seed, sh.signed_part(layer)).hex()
    return layer


# ── what it does ────────────────────────────────────────────────────────────
def test_a_package_sent_is_received_and_on_both_chains(three):
    a, b, _, out, subs = three
    got = a.send(subs, b, out / "p", "--note", "the report")
    assert got.returncode == 0, got.stderr
    pid = got.stdout.split()[1]
    sent = [r for r in a.rows() if r["kind"] == "sent"]
    assert [(r["package"], r["to"], r["subjects"]) for r in sent] == [
        (pid, b.pub, subs)
    ]
    got = b.receive(out / "p")
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.splitlines()[0] == f"{pid}  good"
    assert "After the storm of 2026-03-03." in got.stdout and "$2,140." in got.stdout
    assert '"the report"' in got.stdout and "notes.md:1" in got.stdout
    assert "a key you haven't had a package from before" in got.stdout
    [r] = [r for r in b.rows() if r["kind"] == "received"]
    assert (r["package"], r["from"], r["verdict"], r["layers"]) == (
        pid,
        a.pub,
        "good",
        1,
    )
    assert r["who"] == "share" and r["standing"] == "unattested"
    assert r["from_chain"] == a.rows()[0]["hash"]
    for p in (a, b):
        assert p.verify().startswith("the chain holds")
    assert not [r for r in b.rows() if r["kind"] == "seal"], "receiving seals nothing"


def test_a_package_holds_the_answers_but_never_the_files_text(three):
    a, b, _, out, subs = three
    a.send(subs, b, out / "p")
    text = (out / "p").read_text()
    assert "The roof leak started" not in text and "The quote is" not in text
    pkg = load(out / "p")
    assert [x["data"] for x in pkg["answers"]] == [
        "After the storm of 2026-03-03.",
        "$2,140.",
    ]
    assert pkg["answers"][0]["places"] == {pkg["answers"][0]["cites"][0]: "notes.md:1"}
    rows = a.rows()
    assert pkg["chain"] == {"start": rows[0]["hash"], "rows": len(rows) - 1,
                            "tip": rows[-2]["hash"]}  # fmt: skip
    assert pkg["answers"][1]["rows"][1] == [r for r in rows if r["kind"] == "seal"][1]


def test_a_second_package_from_the_same_key_is_known(three):
    a, b, _, out, subs = three
    a.send(subs[:1], b, out / "p1")
    a.send(subs[1:], b, out / "p2")
    b.receive(out / "p1")
    got = b.receive(out / "p2")
    first = [r for r in b.rows() if r["kind"] == "received"][0]["n"]
    assert f"known since row {first})" in got.stdout


def test_receiving_the_same_package_twice_writes_one_row(three):
    a, b, _, out, subs = three
    a.send(subs, b, out / "p")
    b.receive(out / "p")
    n = len(b.rows())
    got = b.receive(out / "p")
    assert got.returncode == 0 and got.stdout.startswith("already received at row")
    assert len(b.rows()) == n


def test_a_forward_wraps_it_and_the_next_one_sees_every_layer(three):
    a, b, c, out, subs = three
    a.send(subs, b, out / "p", "--note", "the report")
    b.receive(out / "p")
    got = b.forward(out / "p", c, out / "f", "--note", "reviewed")
    assert got.returncode == 0, got.stderr
    fid = got.stdout.split()[1]
    got = c.receive(out / "f")
    assert got.returncode == 0, got.stdout
    lines = got.stdout.splitlines()
    assert lines[0] == f"{fid}  good"
    assert f"from {b.pub[:12]}…" in lines[1] and '"reviewed"' in lines[1]
    assert f"└ from {a.pub[:12]}…" in lines[2] and '"the report"' in lines[2]
    pkg = load(out / "f")
    assert pkg["wraps"] == load(out / "p") and pkg["answers"] == []
    assert pkg["rows"] == [r for r in b.rows() if r["kind"] == "received"]
    [sent] = [r for r in b.rows() if r["kind"] == "sent"]
    assert sent["wraps"] == load_id(out / "p")
    [r] = [r for r in c.rows() if r["kind"] == "received"]
    assert r["layers"] == 2 and r["from"] == b.pub
    for p in (a, b, c):
        assert p.verify().startswith("the chain holds")


def load_id(p: Path) -> str:
    import share as sh  # noqa: PLC0415

    return sh.package_id(load(p))


def test_only_what_you_received_and_held_can_be_forwarded(three):
    a, b, c, out, subs = three
    a.send(subs, b, out / "p")
    got = b.forward(out / "p", c, out / "f")  # not received yet
    assert (
        got.returncode == 2
        and "not a package your record says you received" in got.stderr
    )
    a.send(subs, c, out / "q")  # for c, not b
    b.receive(out / "q")
    got = b.forward(out / "q", c, out / "f")
    assert got.returncode == 2 and not (out / "f").exists()


def test_a_correction_says_where_the_old_one_went(three):
    a, b, c, out, subs = three
    old = a.send(subs, b, out / "p").stdout.split()[1]
    b.receive(out / "p")
    fwd = b.forward(out / "p", c, out / "f").stdout.split()[1]
    fix = a.seal("when did the leak start again", "After the storm, on 2026-03-03.")
    got = a.send([fix], b, out / "p2", "--replaces", old)
    assert got.returncode == 0, got.stderr
    assert load(out / "p2")["replaces"] == old
    got = b.receive(out / "p2")
    assert f"it replaces {old[:20]}…, which you received at row" in got.stdout
    assert f"forward this one with --replaces {fwd}" in got.stdout
    got = b.forward(out / "p2", c, out / "f2", "--replaces", fwd)
    assert got.returncode == 0, got.stderr
    c.receive(out / "f")
    got = c.receive(out / "f2")
    assert f"it replaces {fwd[:20]}…, which you received at row" in got.stdout
    assert "you passed that on" not in got.stdout


def test_a_correction_of_what_you_never_had_says_so(three):
    a, b, _, out, subs = three
    old = a.send(subs[:1], b, out / "p").stdout.split()[1]
    a.send(subs[1:], b, out / "p2", "--replaces", old)
    got = b.receive(out / "p2")
    assert f"it replaces {old[:20]}…, which your record doesn't have" in got.stdout


def test_replaces_names_only_a_package_you_sent(three):
    a, b, _, out, subs = three
    for rep in ("package:" + "0" * 64, "nonsense"):
        got = a.send(subs, b, out / "p", "--replaces", rep)
        assert (
            got.returncode == 2
            and "is not a package your record says you sent" in got.stderr
        )
    assert not (out / "p").exists()


def test_a_package_for_someone_else_is_recorded_and_waits(three):
    a, b, c, out, subs = three
    a.send(subs, b, out / "p")
    got = c.receive(out / "p")
    assert got.returncode == 42
    assert got.stdout.split()[1] == "not-for-you"
    assert f"it is for {b.pub[:12]}…, not you" in got.stdout
    [r] = [r for r in c.rows() if r["kind"] == "received"]
    assert r["verdict"] == "not-for-you" and r["from_chain"] == a.rows()[0]["hash"]


def test_check_reads_a_package_alone_and_log_lists_the_chain(three):
    a, b, _, out, subs = three
    pid = a.send(subs, b, out / "p").stdout.split()[1]
    got = share("check", "--package", out / "p")
    assert got.returncode == 0 and got.stdout.splitlines()[0] == f"{pid}  holds"
    assert "$2,140." in got.stdout
    b.receive(out / "p")
    got = share("log", "--box", a.box)
    assert got.returncode == 0 and f"sent      {pid} to {b.pub[:12]}…" in got.stdout
    got = share("log", "--box", b.box)
    assert f"received  {pid} from {a.pub[:12]}…  good" in got.stdout


# ── every way a package can be wrong ────────────────────────────────────────
def broken(c: "Person", pkg: Path, *why: str) -> None:
    got = c.receive(pkg)
    assert got.returncode == 42, got.stdout + got.stderr
    assert got.stdout.split()[1] == "broken", got.stdout
    for w in why:
        assert w in got.stdout, got.stdout
    assert [r for r in c.rows() if r["kind"] == "received"][-1]["verdict"] == "broken"
    assert c.verify().startswith("the chain holds")


@pytest.mark.parametrize("edit", [
    lambda p: p["answers"][0].update(data="After the storm of 2026-03-09."),
    lambda p: p.update(note="something else"),
    lambda p: p.update(ts="1999-01-01T00:00:00Z"),
    lambda p: p["chain"].update(rows=99),
    lambda p: p["answers"][1]["places"].update({"x": "elsewhere.md:1"}),
])  # fmt: skip
def test_any_edit_to_a_layer_breaks_its_signature(three, edit):
    a, b, _, out, subs = three
    a.send(subs, b, out / "p")
    pkg = load(out / "p")
    edit(pkg)
    broken(b, dump(out / "e", pkg), "layer 0: the signature isn't")


def test_an_edit_inside_a_forward_is_found_in_its_layer(three):
    a, b, c, out, subs = three
    a.send(subs, b, out / "p")
    b.receive(out / "p")
    b.forward(out / "p", c, out / "f")
    pkg = load(out / "f")
    pkg["wraps"]["answers"][1]["data"] = "$21,400."
    broken(c, dump(out / "e", pkg), "layer 1: the signature isn't",
           "layer 0: its row isn't the sender's record of receiving what it wraps")  # fmt: skip


def test_a_layer_signed_again_still_needs_rows_that_hold(three):
    """A sender can sign anything; it can't make a changed row hash right."""
    a, b, _, out, subs = three
    a.send(subs, b, out / "p")
    pkg = load(out / "p")
    pkg["answers"][0]["rows"][1]["who"] = "kernel"
    broken(b, dump(out / "e", resign(pkg, a.id)), "a record row that doesn't hash")


def test_an_answer_whose_rows_are_another_answers_is_found(three):
    a, b, _, out, subs = three
    a.send(subs, b, out / "p")
    pkg = load(out / "p")
    pkg["answers"][0]["rows"] = pkg["answers"][1]["rows"]
    broken(b, dump(out / "e", resign(pkg, a.id)),
           "answer 0: its rows aren't the proposal and the person's seal")  # fmt: skip


def test_an_answer_moved_to_another_question_is_found(three):
    a, b, _, out, subs = three
    a.send(subs, b, out / "p")
    pkg = load(out / "p")
    pkg["answers"][0]["bite_key"] = "0" * 64
    broken(b, dump(out / "e", resign(pkg, a.id)), "the seal was for another question")


def test_rows_past_where_the_record_stood_are_found(three):
    a, b, _, out, subs = three
    a.send(subs, b, out / "p")
    pkg = load(out / "p")
    pkg["chain"]["rows"] = pkg["answers"][1]["rows"][1]["n"]  # the seal is past it
    broken(
        b,
        dump(out / "e", resign(pkg, a.id)),
        "a row past where the sender's record stood",
    )


def test_a_cite_with_no_place_is_found(three):
    a, b, _, out, subs = three
    a.send(subs, b, out / "p")
    pkg = load(out / "p")
    pkg["answers"][0]["places"] = {}
    broken(b, dump(out / "e", resign(pkg, a.id)), "a cite with no place")


def test_a_forward_must_be_by_the_one_it_was_for(three):
    a, b, c, out, subs = three
    a.send(subs, b, out / "p")
    b.receive(out / "p")
    b.forward(out / "p", c, out / "f")
    pkg = load(out / "f")
    pkg["from"] = c.pub  # c claims to have forwarded what was for b
    broken(c, dump(out / "e", resign(pkg, c.id)), "what it wraps was for someone else")


@pytest.mark.parametrize("edit, why", [
    (lambda p: p.update(answers=[]), "holds answers or wraps a package, one of the two"),
    (lambda p: p.update(wraps={"share": 1}), "holds answers or wraps a package, one of the two"),
    (lambda p: p.update(rows="no"), "answers and rows are lists"),
    (lambda p: p.update(replaces="later"), "replaces names a package"),
    (lambda p: p.update(note=7), "ts and note are text"),
    (lambda p: p.update(chain={"start": "x"}), "chain is where the sender's record stood"),
    (lambda p: p["chain"].update(rows=0), "chain is where the sender's record stood"),
    (lambda p: p["chain"].update(rows=True), "chain is where the sender's record stood"),
    (lambda p: p["answers"][0].pop("places"), "answer 0: an answer is"),
    (lambda p: p["answers"][0].update(cites="x"), "cites is a list and places a table"),
    (lambda p: p["answers"][0].update(rows="x"), "an answer's rows are a list"),
    (lambda p: p["answers"][0].update(data=["x"]), "answer 0: its rows aren't the proposal"),
])  # fmt: skip
def test_a_layer_of_the_wrong_shape_is_said_what_it_lacks(three, edit, why):
    a, b, _, out, subs = three
    a.send(subs, b, out / "p")
    pkg = load(out / "p")
    edit(pkg)
    broken(b, dump(out / "e", resign(pkg, a.id)), why)


@pytest.mark.parametrize("pkg, why", [
    ({"share": 2}, "layer 0: not a share package"),
    ([1, 2], None),
])  # fmt: skip
def test_what_isnt_a_package_is_refused_or_broken(three, pkg, why):
    a, b, _, out, subs = three
    if why is None:
        got = b.receive(dump(out / "e", pkg))
        assert got.returncode == 2 and "is not a package" in got.stderr
        return
    broken(b, dump(out / "e", pkg), why)


def test_keys_that_arent_keys_are_said(three):
    a, b, _, out, subs = three
    a.send(subs, b, out / "p")
    pkg = load(out / "p")
    pkg["for"] = "b" * 63
    broken(b, dump(out / "e", pkg), "from and for are public keys")


def test_a_package_too_deep_is_refused_at_its_depth(three):
    import share as sh  # noqa: PLC0415

    a, b, _, out, subs = three
    a.send(subs, b, out / "p")
    pkg = load(out / "p")
    row = pkg["answers"][0]["rows"][0]
    for _ in range(sh.DEEPEST):
        pkg = {**pkg, "answers": [], "rows": [row], "wraps": pkg}
    assert sh.problems(pkg)[-1] == f"layer {sh.DEEPEST}: more than {sh.DEEPEST} layers"
    assert len(sh.layers(pkg)) == sh.DEEPEST


def test_a_broken_package_doesnt_make_its_claimed_sender_known(three):
    a, b, _, out, subs = three
    a.send(subs[:1], b, out / "p1")
    a.send(subs[1:], b, out / "p2")
    pkg = load(out / "p1")
    pkg["note"] = "edited"
    broken(b, dump(out / "e", pkg))
    got = b.receive(out / "p2")
    assert "a key you haven't had a package from before" in got.stdout


def test_a_package_too_big_is_refused(three, monkeypatch):
    import share as sh  # noqa: PLC0415

    a, b, _, out, subs = three
    a.send(subs, b, out / "p")
    monkeypatch.setattr(sh, "BIGGEST", 10)
    pkg, why = sh.read_package(out / "p")
    assert pkg is None and "bigger than a package may be" in why
    monkeypatch.setattr(sh, "BIGGEST", (out / "p").stat().st_size)
    assert sh.read_package(out / "p")[1] is None


# ── what it refuses ─────────────────────────────────────────────────────────
def test_the_seal_key_is_never_an_identity(three):
    a, b, _, out, subs = three
    got = share("send", "--box", a.box, "--id", a.dir / "key", "--answer", subs[0],
                "--for", b.pub, "--to", out / "p")  # fmt: skip
    assert got.returncode == 2 and "IDFILE is your seal key" in got.stderr
    got = share(
        "receive", "--box", b.box, "--id", b.dir / "key", "--package", out / "p"
    )
    assert got.returncode == 2 and "IDFILE is your seal key" in got.stderr


def test_an_identity_file_must_be_one(three, tmp_path):
    a, b, _, out, subs = three
    for text in ("ed25519 xyz\n", "rsa " + "0" * 64 + "\n", ""):
        bad = tmp_path / "bad"
        bad.write_text(text)
        got = share("send", "--box", a.box, "--id", bad, "--answer", subs[0],
                    "--for", b.pub, "--to", out / "p")  # fmt: skip
        assert got.returncode == 2 and "is not an identity" in got.stderr
    got = share("send", "--box", a.box, "--id", tmp_path / "none", "--answer", subs[0],
                "--for", b.pub, "--to", out / "p")  # fmt: skip
    assert got.returncode == 2 and "could not read" in got.stderr


def test_id_writes_one_new_file_readable_only_by_you(tmp_path):
    got = share("id", "--to", tmp_path / "me")
    assert got.returncode == 0 and len(got.stdout.strip()) == 64
    assert (tmp_path / "me").stat().st_mode & 0o777 == 0o600
    seed = bytes.fromhex((tmp_path / "me").read_text().split()[1])
    assert ed25519.public(seed).hex() == got.stdout.strip()
    before = (tmp_path / "me").read_bytes()
    got = share("id", "--to", tmp_path / "me")
    assert got.returncode == 2 and "exists; this never overwrites" in got.stderr
    assert (tmp_path / "me").read_bytes() == before
    got = share("id", "--to", tmp_path / "no" / "me")
    assert got.returncode == 2 and "is not a folder; this never makes one" in got.stderr


def test_a_package_is_never_written_in_the_box_or_its_folder(three):
    a, b, _, out, subs = three
    for to, why in ((a.box / "p", "inside the box"), (a.dir / "pile" / "p", "inside your folder"),
                    (out / "no" / "p", "this never makes one")):  # fmt: skip
        got = a.send(subs, b, to)
        assert got.returncode == 2 and why in got.stderr, got.stderr
    (out / "p").write_text("mine")
    got = a.send(subs, b, out / "p")
    assert got.returncode == 2 and (out / "p").read_text() == "mine"
    assert not [r for r in a.rows() if r["kind"] == "sent"], "a refusal writes no row"


def test_only_answers_you_sealed_are_sent(three):
    a, b, _, out, subs = three
    for bad, why in (("proposal:" + "0" * 64, "is not an answer you sealed"),
                     (f"{subs[0]},{subs[0]}", "an answer named twice")):  # fmt: skip
        got = a.send([bad], b, out / "p")
        assert got.returncode == 2 and why in got.stderr
    got = share("send", "--box", a.box, "--id", a.id, "--answer", subs[0], "--for", "me",
                "--to", out / "p")  # fmt: skip
    assert got.returncode == 2 and "--for is the public key" in got.stderr


def test_an_answer_whose_file_changed_is_not_sent(three):
    a, b, _, out, subs = three
    p = a.box / "proposals" / f"{subs[0][9:]}.json"
    p.write_text(p.read_text().replace("2026-03-03", "2026-03-09"))
    got = a.send(subs, b, out / "p")
    assert got.returncode == 2 and "its proposal file is not the bytes" in got.stderr


def test_a_box_that_doesnt_verify_is_refused(three, tmp_path):
    a, b, _, out, subs = three
    got = share("log", "--box", tmp_path)
    assert got.returncode == 2 and "not a kernel box" in got.stderr
    rec = a.box / "record.jsonl"
    rec.write_text(rec.read_text().replace('"boot"', '"Boot"', 1))
    got = a.send(subs, b, out / "p")
    assert got.returncode == 2 and "the record doesn't verify" in got.stderr
    rec.write_text("")
    got = share("log", "--box", a.box)
    assert got.returncode == 2 and "the record is empty" in got.stderr


def test_check_says_a_broken_package_and_refuses_no_package(three, tmp_path):
    a, b, _, out, subs = three
    a.send(subs, b, out / "p")
    pkg = load(out / "p")
    pkg["note"] = "x"
    got = share("check", "--package", dump(out / "e", pkg))
    assert got.returncode == 42 and "does not hold" in got.stdout
    got = share("check", "--package", tmp_path / "none")
    assert got.returncode == 2 and "could not read" in got.stderr


@pytest.mark.parametrize("argv", [
    [], ["nothing"], ["id"], ["id", "--to"], ["log", "--box", "x", "--box", "y"],
    ["log", "--box", "x", "--to", "y"], ["check"], ["send", "--box", "x"],
])  # fmt: skip
def test_a_bad_command_line_says_how_to_run_it(argv):
    got = share(*argv)
    assert got.returncode == 2 and "share.py id" in got.stderr
