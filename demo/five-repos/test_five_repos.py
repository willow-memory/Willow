"""five-repos: the stacks name add-ons that are here, the words list is one
the kernel reads, and the records' chains hold with nothing sealed."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

STACKS = sorted((HERE / "stacks").glob("*.md"))
RECORDS = sorted((HERE / "results").glob("*/record.jsonl"))


def stack_module():
    spec = importlib.util.spec_from_file_location(
        "stack", ROOT / "adapters/stdlib/stack/stack.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_every_stack_parses_and_names_only_add_ons_that_are_here():
    stack = stack_module()
    assert len(STACKS) == 7
    for path in STACKS:
        pools, err = stack.parse_stack(path.read_text(encoding="utf-8"))
        assert err is None, f"{path.name}: {err}"
        names = {name for _, steps in pools for name, _ in steps}
        assert names, path.name
        missing = sorted(n for n in names if stack.resolve(n) is None)
        assert not missing, f"{path.name} names add-ons that aren't here: {missing}"


def test_the_stacks_name_no_machine_of_their_own():
    for path in STACKS:
        text = path.read_text(encoding="utf-8")
        assert "/tmp/" not in text and "/home/" not in text, path.name
        assert "<scratch>" in text or "{box}" in text, path.name


def test_the_words_list_is_one_the_kernel_reads():
    alias, why = kernel.parse_words((HERE / "words.txt").read_text(encoding="utf-8"))
    assert why is None
    assert alias["vault"] == ["box", "chain", "ledger", "receipts", "record", "store"]
    assert "dataset" not in alias and "record" not in alias, "the broad lines were cut"
    assert len(alias) == 24


def test_each_records_chain_holds_and_nothing_in_it_is_sealed():
    assert len(RECORDS) == 2
    for record in RECORDS:
        rows, breaks = kernel.read(record)
        assert not breaks, f"{record.parent.name}: {breaks}"
        kinds = [r["kind"] for r in rows]
        assert "seal" not in kinds and "decline" not in kinds, record.parent.name
        assert kinds[0] == "boot"


def test_the_proof_record_holds_the_suggestions_that_wait():
    rows, _ = kernel.read(HERE / "results" / "proof-record" / "record.jsonl")
    proposals = [r for r in rows if r["kind"] == "proposal"]
    assert len(proposals) == 10
    files = sorted(
        p.stem for p in (HERE / "results/proof-record/proposals").glob("*.json")
    )
    assert len(files) == 10, "ten suggestion files: nine answers and the session bundle"
    for name in files:
        prop = json.loads(
            (HERE / "results/proof-record/proposals" / f"{name}.json").read_text()
        )
        assert prop["path"] and prop["claim"], name
    kinds = sorted({r["kind"] for r in rows})
    assert kinds == ["bite", "boot", "fixity", "out", "proposal", "session"]


def test_the_play_record_is_the_games_rows():
    rows, _ = kernel.read(HERE / "results" / "play-record" / "record.jsonl")
    kinds = [r["kind"] for r in rows[1:]]
    assert set(kinds) == {"guess", "quiz", "answer", "draw", "roll", "catgrid", "life"}
    assert kinds.count("guess") == 5 and kinds.count("catgrid") == 2
