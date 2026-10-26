"""serve: the one markdown file a model reads, only a sealed scope, pooled
with peaks first, by unguessable ids. It proposes a scope from the last bite,
serves only when a scope is sealed (through the kernel, never the key), fails
closed otherwise, and refuses a bad command line."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVE = HERE / "serve.py"
KERNEL = HERE.parents[2] / "kernel.py"
NOW = ["--now", "2026-10-23T00:00:00Z"]


def run(script: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *argv], capture_output=True, text=True
    )


def a_box(tmp: Path) -> tuple[Path, Path]:
    """A box over a two-file pile, with a bite already served; (box, key)."""
    pile = tmp / "pile"
    pile.mkdir()
    (pile / "roof.md").write_text("2026-03-01 The roof estimate came in at 4200.\n")
    (pile / "mould.md").write_text("2026-03-02 Reported the mould in the bedroom.\n")
    box, key = tmp / "box", tmp / "key"
    subprocess.run(
        [
            sys.executable,
            str(KERNEL),
            "init",
            "--box",
            str(box),
            "--pile",
            str(pile),
            "--key",
            str(key),
            *NOW,
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run([sys.executable, str(KERNEL), "bite", "--box", str(box), *NOW,
                    "roof estimate"], check=True, capture_output=True)  # fmt: skip
    return box, key


def seal_the_scope(box: Path) -> str:
    """Propose the scope with `serve scope`, read back its subject, seal it
    through the kernel with the box's key. Returns the subject."""
    got = run(SERVE, "scope", "--box", str(box), *NOW)
    assert got.returncode in (0, 42), got.stderr
    subj = re.search(r"(proposal:[0-9a-f]+)", got.stdout).group(1)
    sealed = subprocess.run([sys.executable, str(KERNEL), "seal", "--box", str(box),
                             *NOW, subj], capture_output=True, text=True)  # fmt: skip
    assert sealed.returncode == 0, sealed.stderr
    return subj


def test_scope_proposes_the_last_bites_passages_pooled_with_peaks(tmp_path):
    box, _ = a_box(tmp_path)
    got = run(SERVE, "scope", "--box", str(box), *NOW)
    assert got.returncode == 42, got.stdout + got.stderr  # waits on your seal
    assert "peaks first" in got.stdout
    assert "proposal:" in got.stdout and "seal it with your key" in got.stdout


def test_serve_writes_the_view_only_once_a_scope_is_sealed(tmp_path):
    box, _ = a_box(tmp_path)
    seal_the_scope(box)
    out = tmp_path / "served.md"
    got = run(SERVE, "--box", str(box), "--to", str(out), *NOW)
    assert got.returncode == 0, got.stdout + got.stderr
    page = out.read_text()
    assert page.startswith("# served:")
    assert "## roof.md" in page  # a pool heading, by where
    assert "human-sealed" in page  # the trust label
    assert "roof estimate came in" in page  # the sealed passage's text
    assert "data, not instructions" in page  # untrusted-input framing


def test_the_served_ids_are_opaque_and_change_each_run(tmp_path):
    box, _ = a_box(tmp_path)
    seal_the_scope(box)
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    run(SERVE, "--box", str(box), "--to", str(a), *NOW)
    run(SERVE, "--box", str(box), "--to", str(b), *NOW)
    ids_a = set(re.findall(r"`([0-9a-f]{12})`", a.read_text()))
    ids_b = set(re.findall(r"`([0-9a-f]{12})`", b.read_text()))
    assert ids_a and ids_b and ids_a.isdisjoint(ids_b), "a fresh serve key each run"


def test_the_view_holds_no_record_hash_or_row_number(tmp_path):
    box, _ = a_box(tmp_path)
    seal_the_scope(box)
    out = tmp_path / "served.md"
    run(SERVE, "--box", str(box), "--to", str(out), *NOW)
    page = out.read_text()
    # the chunk ids on the record are 64-hex; none may appear in the view
    leaked = re.findall(r"[0-9a-f]{64}", page)
    assert not leaked, f"a full-width hash leaked into the view: {leaked}"


def test_without_a_sealed_scope_it_fails_closed_and_writes_nothing(tmp_path):
    box, _ = a_box(tmp_path)  # a bite, but no scope sealed
    out = tmp_path / "served.md"
    got = run(SERVE, "--box", str(box), "--to", str(out), *NOW)
    assert got.returncode == 2 and "no sealed scope" in got.stderr
    assert not out.exists(), "nothing is served without a seal"


def test_scope_on_a_box_with_no_bite_says_so(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "a.md").write_text("Tomatoes want sun.\n")
    box = tmp_path / "box"
    subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile",
                    str(pile), "--key", str(tmp_path / "key"), *NOW],
                   check=True, capture_output=True)  # fmt: skip
    got = run(SERVE, "scope", "--box", str(box), *NOW)
    assert got.returncode == 42 and "nothing to scope" in got.stdout


def test_it_refuses_to_write_inside_the_box_or_pile(tmp_path):
    box, _ = a_box(tmp_path)
    seal_the_scope(box)
    for bad in (box / "served.md", tmp_path / "pile" / "served.md"):
        got = run(SERVE, "--box", str(box), "--to", str(bad), *NOW)
        assert got.returncode == 2 and "never writes there" in got.stderr
        assert not bad.exists()


def test_a_bad_command_line_is_refused_and_names_the_script(tmp_path):
    box, _ = a_box(tmp_path)
    for argv in (
        [],  # nothing
        ["--box", str(box)],  # write form, no --to
        [
            "scope",
            "--box",
            str(box),
            "--to",
            str(tmp_path / "x"),
        ],  # scope takes no --to
        ["dig", "--box", str(box)],  # unknown verb
        ["scope", "--box", str(box), "extra"],  # a stray word
    ):
        got = run(SERVE, *argv)
        assert got.returncode == 2 and "serve.py" in got.stderr, (argv, got.stderr)


def test_the_given_now_is_the_proposals_timestamp(tmp_path):
    box, _ = a_box(tmp_path)
    run(SERVE, "scope", "--box", str(box), *NOW)
    rows = [json.loads(ln) for ln in (box / "record.jsonl").read_text().splitlines()]
    prop = next(r for r in reversed(rows) if r["kind"] == "proposal")
    assert prop["ts"] == NOW[1], "serve scope records the --now it was given"


def test_not_a_kernel_box_is_refused(tmp_path):
    (tmp_path / "b").mkdir()
    got = run(SERVE, "scope", "--box", str(tmp_path / "b"))
    assert got.returncode == 2 and "not a kernel box" in got.stderr


def test_a_sealed_scope_whose_proposal_file_changed_serves_nothing(tmp_path):
    """The seal covers the scope's bytes. A file widened after the seal to
    cite another passage is not the scope the person sealed: fail closed."""
    box, _ = a_box(tmp_path)
    subj = seal_the_scope(box)
    other = subprocess.run([sys.executable, str(KERNEL), "bite", "--box", str(box), *NOW,
                            "mould bedroom"], capture_output=True, text=True)  # fmt: skip
    mould = json.loads(other.stdout)["served"][0]["id"]
    f = box / "proposals" / f"{subj[9:]}.json"
    held = f.read_text()
    prop = json.loads(held)
    f.write_text(json.dumps({**prop, "cites": [*prop["cites"], mould]}))
    out = tmp_path / "served.md"
    got = run(SERVE, "--box", str(box), "--to", str(out), *NOW)
    assert got.returncode == 2 and not out.exists(), got.stdout
    assert "mould" not in got.stdout.lower()
    f.write_text(held)
    assert run(SERVE, "--box", str(box), "--to", str(out), *NOW).returncode == 0
    assert "Reported the mould" not in out.read_text()  # and never the widened one


def test_scope_says_how_many_pools_with_the_right_plural(tmp_path):
    box, _ = a_box(tmp_path)  # the roof bite served one passage, in one pool
    first = run(SERVE, "scope", "--box", str(box), *NOW).stdout.splitlines()[0]
    assert first.endswith("in 1 pool, peaks first"), first
    subprocess.run([sys.executable, str(KERNEL), "bite", "--box", str(box), *NOW,
                    "mould roof"], check=True, capture_output=True)  # fmt: skip
    first = run(SERVE, "scope", "--box", str(box), *NOW).stdout.splitlines()[0]
    assert first.endswith("in 2 pools, peaks first"), first
