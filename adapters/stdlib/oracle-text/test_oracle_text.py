"""oracle-text: a Tracery grammar expanded by willow's seeded stream; the same
seed, grammar and number give the same reading; modifiers and named
expansions work; a bad grammar or an endless one is refused; nothing written."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "oracle_text.py"
spec = importlib.util.spec_from_file_location("oracle_text", SCRIPT)
ot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ot)


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def only(text: str) -> dict:
    """A grammar with one rule per symbol, so nothing is left to the stream."""
    return {"origin": text, "animal": "heron", "box": "owl", "x": "city", "z": "bush"}


def test_the_modifiers():
    m = ot.MODIFIERS
    assert (
        m["a"]("owl") == "an owl"
        and m["a"]("heron") == "a heron"
        and m["a"]("Egg") == "an Egg"
    )
    assert m["a"]("umbrella") == "an umbrella" and m["a"]("stone") == "a stone"
    assert (
        m["s"]("owl") == "owls"
        and m["s"]("bus") == "buses"
        and m["s"]("box") == "boxes"
    )
    assert m["s"]("buzz") == "buzzes" and m["s"]("dish") == "dishes"
    assert (
        m["s"]("city") == "cities" and m["s"]("toy") == "toys" and m["s"]("y") == "ys"
    )
    assert (
        m["ed"]("play") == "played"
        and m["ed"]("bake") == "baked"
        and m["ed"]("carry") == "carried"
    )
    assert m["ed"]("y") == "yed" and m["ed"]("toy") == "toyed"
    assert m["capitalize"]("owl at dusk") == "Owl at dusk" and m["capitalize"]("") == ""
    assert m["capitalizeAll"]("owl at dusk") == "Owl At Dusk"
    assert m["allCaps"]("owl") == "OWL"


def test_symbols_modifiers_chains_and_plain_text_expand():
    rng = ot.tarot.Stream(b"x")
    g = only(
        "#animal.a.capitalize# met #box.s.allCaps#, a #x# and a #z.s#. 100% # kept"
    )
    assert (
        ot.expand("#origin#", g, rng, {})
        == "A heron met OWLS, a city and a bushes. 100% # kept"
    )
    assert ot.expand("no symbols, [] or #", {}, rng, {}) == "no symbols, [] or #"


def test_a_name_set_in_a_reading_says_the_same_thing_again():
    g = {
        "origin": "[who:#animal#]The #who# and the #who#, not the #animal#.",
        "animal": ["owl", "heron", "otter", "fox", "moth", "hare", "vole"],
    }
    for i in range(1, 12):
        out = ot.reading(g, "names", i)
        words = out.removeprefix("The ").split(" and the ")
        assert words[0] == words[1].split(",")[0], out


def test_the_same_seed_grammar_and_number_give_the_same_reading_and_others_differ():
    assert (
        ot.reading(ot.BUILTIN, "demo", 1)
        == "An owl will cross your path today, carrying a letter."
    )
    assert (
        ot.reading(ot.BUILTIN, "demo", 2)
        == "The otter in the garden has seen an apple, and is saying nothing."
    )
    assert ot.reading(ot.BUILTIN, "demo", 1) == ot.reading(ot.BUILTIN, "demo", 1)
    many = {ot.reading(ot.BUILTIN, "demo", i) for i in range(1, 30)}
    assert len(many) > 10
    assert {ot.reading(ot.BUILTIN, "other", i) for i in range(1, 30)} != many
    one = run("--seed", "demo")
    assert (
        one.returncode == 0
        and one.stdout == "An owl will cross your path today, carrying a letter.\n"
    )
    three = run("--seed", "demo", "--count", "3").stdout.splitlines()
    assert (
        three[0] == one.stdout.strip()
        and three[1] == ot.reading(ot.BUILTIN, "demo", 2)
        and len(three) == 3
    )


def test_a_grammar_file_and_an_origin_are_used(tmp_path):
    f = tmp_path / "g.json"
    f.write_text(json.dumps({"origin": "never", "start": ["only this"]}))
    got = run("--seed", "s", "--grammar", str(f), "--origin", "start")
    assert got.returncode == 0 and got.stdout == "only this\n"
    assert run("--seed", "s", "--grammar", str(f)).stdout == "never\n"


def test_a_bad_grammar_a_missing_symbol_or_an_endless_one_is_refused(tmp_path):
    def refused(grammar, *extra):
        f = tmp_path / "bad.json"
        f.write_text(grammar)
        got = run("--seed", "s", "--grammar", str(f), *extra)
        assert (
            got.returncode == 2
            and got.stdout == ""
            and got.stderr.startswith("refused: ")
        ), grammar
        return got.stderr

    assert "no symbol 'nope'" in refused(json.dumps({"origin": "#nope#"}))
    assert "no symbol 'origin'" in refused(json.dumps({"start": "x"}))
    assert "without end" in refused(json.dumps({"origin": "#origin# again"}))
    assert "no modifier 'zap'" in refused(json.dumps({"origin": "#a.zap#", "a": "x"}))
    assert "JSON object of strings" in refused(json.dumps(["origin"]))
    assert "JSON object of strings" in refused(json.dumps({"origin": []}))
    assert "JSON object of strings" in refused(json.dumps({"origin": ["a", 3]}))
    assert "JSON object of strings" in refused(json.dumps({"origin": 3}))
    assert "as JSON" in refused("{not json")
    assert "no symbol" in refused(json.dumps({"a": "x"}), "--origin", "b")
    assert (
        "could not read"
        in run("--seed", "s", "--grammar", str(tmp_path / "none.json")).stderr
    )


def test_nesting_is_allowed_to_a_depth_and_no_further():
    def chain(n):
        g = {f"s{i}": f"#s{i + 1}#" for i in range(n)}
        g["origin"] = "#s0#"
        g[f"s{n}"] = "end"
        return g

    assert ot.reading(chain(35), "n", 1) == "end"
    try:
        ot.reading(chain(45), "n", 1)
    except ot.Refused as e:
        assert "without end" in str(e)
    else:
        raise AssertionError("45 levels should be called endless")


def test_a_bad_command_line_is_refused_and_nothing_is_written(tmp_path):
    before = sorted(tmp_path.rglob("*"))
    for argv in (
        [],
        ["--seed"],
        ["--seed", "s", "stray"],
        ["--seed", "s", "--count", "0"],
        ["--seed", "s", "--count", "many"],
        ["--count", "2"],
    ):
        assert run(*argv).returncode == 2, argv
    assert "oracle_text.py" in run().stderr
    assert sorted(tmp_path.rglob("*")) == before


def test_the_sibling_it_reads_through_is_put_at_the_front():
    """In a process of its own, so another test's imports can't move the path."""
    code = (
        "import importlib.util, json, sys\n"
        f"s = importlib.util.spec_from_file_location('m', {str(HERE / 'oracle_text.py')!r})\n"
        "m = importlib.util.module_from_spec(s)\n"
        "s.loader.exec_module(m)\n"
        "print(json.dumps(sys.path))\n"
    )
    got = json.loads(
        subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        ).stdout
    )
    here = got.index(str(HERE.parent / "tarot"))
    root = str(HERE.parents[2])
    assert got[here - 1] == root and got[here + 1] == root, (
        "the sibling is put at the front, so nothing else answers to its name"
    )
