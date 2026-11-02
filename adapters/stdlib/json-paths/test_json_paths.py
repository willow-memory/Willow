"""json-paths: any JSON or JSON Lines file as `key: value` lines, a record to a
passage the kernel keeps whole; keys beside their values, a key in most records
left out so an absent question finds nothing, numbers digit for digit, bad
files and bad lines skipped and counted, big mirrors in parts, the same bytes
twice, originals unchanged, and MIRROR and FOLDER kept apart."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "json_paths.py"
spec = importlib.util.spec_from_file_location("json_paths", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
kernel = mod.kernel

GOODS = ["leeks", "carrots", "oats", "lentils", "honey", "rye", "figs", "kale"]
GOODS += ["plums", "beans", "cider", "pears", "eggs", "cheese", "mint"]
ORDERS = json.dumps(
    {
        "shop": "Hollow Lane Grocer",
        "orders": [
            {
                "id": 100 + i,
                "date": f"2026-03-{i + 1:02d}",
                "total": f"{i}.50",
                "items": [
                    {"name": GOODS[(i * 3 + j) % len(GOODS)], "qty": j + 1}
                    for j in range(min(i + 1, 3))
                ],
            }
            for i in range(5)
        ],
    }
).encode()


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv], capture_output=True, text=True
    )


def mirror_of(
    tmp_path: Path, files: dict[str, bytes]
) -> tuple[subprocess.CompletedProcess, Path]:
    src = tmp_path / "src"
    for rel, data in files.items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_bytes(data)
    out = tmp_path / "out"
    return run("mirror", "--from", str(src), "--to", str(out)), out


def conv(value: object, name: str = "x.json") -> str:
    return mod.convert(json.dumps(value).encode(), name)


def blocks(text: str) -> list[list[str]]:
    return [b.split("\n") for b in text.rstrip("\n").split("\n\n")]


def test_each_value_is_written_beside_its_key_under_its_records_heading():
    out = conv({"shop": "x", "orders": [{"id": 7, "items": [{"name": "leeks"}]}]})
    assert out == "shop: x\n\norders\n[0].id: 7\n[0].items[0].name: leeks\n"


def test_a_key_with_a_dot_bracket_space_quote_colon_or_nothing_is_written_in_brackets():
    out = conv(
        {
            "a.b": 1,
            "first name": 2,
            "x[0]": 3,
            'say "hi"': 4,
            "time: now": 5,
            "": 6,
            "back\\slash": 7,
            "café": 8,
            "snake_case-key": 9,
        }
    )
    assert out.splitlines() == [
        '["a.b"]: 1',
        '["first name"]: 2',
        '["x[0]"]: 3',
        '["say \\"hi\\""]: 4',
        '["time: now"]: 5',
        '[""]: 6',
        '["back\\\\slash"]: 7',
        "café: 8",
        "snake_case-key: 9",
    ]
    nested = conv({"a": {"b c": {"d.e": [1]}}}).splitlines()
    assert nested == ["a", '["b c"]["d.e"][0]: 1']


def test_numbers_are_kept_digit_for_digit_and_true_false_null_as_json_writes_them():
    raw = b'{"price": 1.50, "big": 1e5, "neg": -0, "n": 12345678901234567890, "t": true, "f": false, "z": null}'
    assert mod.convert(raw).splitlines() == [
        "price: 1.50",
        "big: 1e5",
        "neg: -0",
        "n: 12345678901234567890",
        "t: true",
        "f: false",
        "z: null",
    ]


def test_a_string_is_unquoted_but_an_empty_or_blank_one_keeps_its_quotes():
    out = conv({"s": "leeks", "e": "", "b": "   ", "nil": None, "l": [], "o": {}})
    assert out.splitlines() == [
        "s: leeks",
        'e: ""',
        'b: "   "',
        "nil: null",
        "l: []",
        "o: {}",
    ]


def test_a_key_given_twice_keeps_both_values():
    assert mod.convert(b'{"tag": "a", "tag": "b"}') == "tag: a\ntag: b\n"


def test_a_strings_own_lines_each_keep_the_key_and_never_make_a_blank_line():
    out = conv({"note": {"body": "first line\r\nsecond line\n\n\n  \nthird"}})
    assert out == "note\nbody: first line\nbody: second line\nbody: third\n"


def test_a_long_line_wraps_at_a_space_onto_lines_with_the_same_key():
    words = " ".join(f"word{i}" for i in range(200))
    lines = mod.flat(words, ("k",), 1)
    assert len(lines) > 3 and all(steps == ("k",) for steps, _ in lines)
    assert all(len(v) <= mod.WIDTH for _, v in lines)
    assert " ".join(v for _, v in lines) == words
    unbroken = "x" * (mod.WIDTH * 2 + 5)
    assert [len(v) for _, v in mod.flat(unbroken, ("k",), 1)] == [
        mod.WIDTH,
        mod.WIDTH,
        5,
    ]
    out = conv({"k": " ".join(words.split()[:50])}).splitlines()
    assert len(out) == 2 and all(x.startswith("k: ") for x in out)


def test_control_characters_are_written_as_json_escapes_so_no_line_is_cut():
    out = conv({"k": "a\u0000b c\u0085d\x0ce", "k\u0001": 1})
    assert out == 'k: a\\u0000b\\u2028c\\u0085d\\u000ce\n["k\\u0001"]: 1\n'
    assert len(out.splitlines()) == 2 and "\0" not in out


def test_each_element_of_a_top_level_array_is_a_passage_headed_by_its_index():
    out = conv([{"id": 1, "name": "a"}, {"id": 2, "name": "b"}, "loose", 3])
    assert blocks(out) == [
        ["loose", "3"],
        ["[0]", "id: 1", "name: a"],
        ["[1]", "id: 2", "name: b"],
    ]


def test_a_top_level_objects_plain_values_run_together_and_each_container_is_its_own():
    out = conv({"name": "shop", "tags": ["a", "b"], "open": True, "owner": {"n": 1}})
    assert blocks(out) == [
        ["name: shop", "open: true"],
        ["tags", "a", "b"],
        ["owner", "n: 1"],
    ]


def test_a_key_in_most_records_is_left_out_and_a_key_naming_its_value_stays():
    rows = [
        {
            "date": f"2026-01-{i:02d}",
            "from": f"P{i}",
            "text": ("words %d " % i) * 8 + "end",
        }
        for i in range(30)
    ]
    out = conv({"chat": "Kieran", "messages": rows})
    got = blocks(out)
    assert got[0] == ["chat: Kieran"]
    assert got[1] == ["[0]", "2026-01-00", "P0", "words 0 " * 8 + "end"]
    assert "date" not in out and "from" not in out and "messages" not in out
    times = {f"tests/test_{w}.py": n for n, w in enumerate(["a", "b", "c", "d"])}
    assert conv(times).splitlines()[0] == '["tests/test_a.py"]: 0'
    two = conv([{"date": "2026-01-01"}, {"date": "2026-01-02"}])
    assert "date: 2026-01-01" in two, "a key in two records stays"
    half = conv([{"a": 1}, {"a": 2}, {"a": 3}, {"b": 4}, {"b": 5}, {"b": 6}])
    assert "a: 1" in half and "b: 6" in half, "in half the records, not most"
    most = conv([{"a": 1}, {"a": 2}, {"a": 3}, {"a": 4}, {"b": 5}, {"b": 6}])
    assert "a:" not in most and "b: 6" in most


def test_an_absent_question_finds_nothing_and_real_questions_still_land(tmp_path):
    """The owner's test: each word in most passages of a mirror file, paired
    with a word the folder doesn't hold, is served nothing; the questions a
    person asks of the records still find them."""
    lines = b"".join(
        json.dumps({"day": f"2026-02-{i:02d}", "who": w, "said": s}).encode() + b"\n"
        for i, (w, s) in enumerate(
            [
                ("Ada", "the boiler is fixed"),
                ("Cy", "pick up the parcel"),
                ("Bea", "dentist moved to Friday"),
                ("Dov", "rent goes up in May"),
            ],
            1,
        )
    )
    big = [{"id": 9, "items": [{"name": f"part{j}", "qty": j} for j in range(30)]}]
    files = {
        "a.json": ORDERS,
        "b.jsonl": lines + b"not json\n",
        "c.json": json.dumps(big).encode(),
    }
    got, out = mirror_of(tmp_path, files)
    assert got.returncode == 0, got.stderr
    pile = kernel.chunks(out)
    for path in {c["path"] for c in pile}:
        mine = [c for c in pile if c["path"] == path]
        assert len(mine) >= 3, path
        seen: dict[str, int] = {}
        for c in mine:
            for w in set(kernel.words(c["text"])) - kernel.FUNCTION:
                seen[w] = seen.get(w, 0) + 1
        common = [w for w, n in seen.items() if n * 2 > len(mine) and not w.isdigit()]
        assert "volcano" not in seen
        for w in common:
            assert kernel.rank(mine, f"volcano {w}") == [], (path, w)
    for bite, needle in (
        ("what was order 103", "103"),
        ("when is the dentist", "dentist moved to Friday"),
        ("what did Dov say about rent", "rent goes up in May"),
        ("which is part17", "part17"),
    ):
        hit = kernel.rank(pile, bite)
        assert hit and needle in hit[0]["text"], bite


def test_what_order_3_contained_is_one_passage_with_its_fields_together():
    out = mod.convert(ORDERS)
    order = [b for b in blocks(out) if b[0] == "[3]"]
    assert order == [
        ["[3]", "103", "2026-03-04", "3.50", "beans", "1", "cider", "2", "pears", "3"]
    ]
    assert blocks(out)[0] == ["shop: Hollow Lane Grocer"]


def test_the_kernel_keeps_each_passage_whole_and_finds_the_order(tmp_path):
    got, out = mirror_of(tmp_path, {"a/b.json": ORDERS})
    assert got.returncode == 0, got.stderr
    text = (out / "a/b.json.txt").read_text(encoding="utf-8")
    chunks = kernel.chunks(out)
    assert [c["text"].split("\n") for c in chunks] == blocks(text)
    hit = kernel.rank(chunks, "what was in order 103 on 2026-03-04")[0]
    assert hit["text"].startswith("[3]\n") and "beans" in hit["text"]
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "b.json").write_bytes(ORDERS)
    assert len(kernel.chunks(raw)) == 1, "the raw file is one line, one cut"


def test_records_are_found_in_the_first_array_that_does_not_fit_however_deep():
    data = json.loads(ORDERS)
    nested = conv({"meta": {"v": 2}, "data": {"source": "till", **data}})
    got = blocks(nested)
    assert got[0] == ["meta", "v: 2"]
    assert got[1] == ["source: till", "shop: Hollow Lane Grocer"]
    assert [b[0] for b in got[2:]] == [f"[{i}]" for i in range(5)]
    small = conv({"orders": data["orders"][:2]})
    assert [b[0] for b in blocks(small)] == ["orders"], "a list that fits stays whole"


def test_a_record_bigger_than_a_passage_is_cut_between_lines_under_its_heading():
    record = {
        "id": 9,
        "items": [{"name": f"item number {j}", "qty": j} for j in range(40)],
        "total": "99.00",
    }
    parts = blocks(conv([record]))
    assert len(parts) > 3
    for p in parts:
        assert sum(len(x) + 1 for x in p) <= kernel.MAX_CHUNK
        assert p[0] == "[0]"
    assert parts[0] == ["[0]", "id: 9"]
    assert parts[-1] == ["[0]", "total: 99.00"]
    items = parts[1:-1]
    assert len(items) > 2
    body = [x for p in items for x in p[1:]]
    assert body == [x for j in range(40) for x in (f"item number {j}", str(j))]
    for p in items:  # an item's name and qty are never torn apart
        assert len(p[1:]) % 2 == 0


def test_inside_a_record_an_array_of_objects_fills_passages_rather_than_one_each():
    record = {"id": 1, "items": [{"n": f"thing {j}", "q": j} for j in range(30)]}
    parts = blocks(conv([record]))
    items = parts[1:]
    assert parts[0] == ["[0]", "id: 1"] and 1 < len(items) < 10
    assert sum(len(p) - 1 for p in items) == 60


def test_one_huge_string_is_cut_between_its_lines_under_the_same_heading():
    text = "\n".join(f"line {i} of the diary" for i in range(100))
    parts = blocks(conv([{"diary": text}]))
    assert len(parts) > 3 and all(p[0] == "[0]" for p in parts)
    assert all(sum(len(x) + 1 for x in p) <= kernel.MAX_CHUNK for p in parts)
    assert [x for p in parts for x in p[1:]] == [
        f"line {i} of the diary" for i in range(100)
    ]


def test_nesting_deeper_than_the_cap_is_written_as_compact_json():
    deep: object = {"leaf": "x", "n": [1, 2.50]}
    for _ in range(mod.MAX_DEPTH + 3):
        deep = {"a": deep}
    out = conv(deep).splitlines()
    path = ".".join(["a"] * (mod.MAX_DEPTH - 1))
    assert out[0] == "a"
    assert out[-1] == path + ': {"a":{"a":{"a":{"leaf":"x","n":[1,2.5]}}}}'
    capped = mod.flat(mod.loads('{"a": {"b": 1.50, "b": 2}}'), ("p",), 32)
    assert capped == [(("p",), '{"a":{"b":1.50,"b":2}}')]
    shallow = mod.flat(mod.loads('{"a": {"b": 1}}'), ("p",), 31)
    assert shallow == [(("p", "a"), '{"b":1}')]


def test_a_string_past_the_cap_is_cut_and_says_how_much_was_left_out():
    lines = mod.flat("y" * (mod.MAX_STRING + 1234), ("k",), 1)
    joined = "".join(v for _, v in lines)
    assert joined == "y" * mod.MAX_STRING + " … (1234 more characters)"
    assert "more characters" not in conv({"k": "y" * mod.MAX_STRING})


def test_json_lines_each_line_is_a_record_and_a_bad_line_is_counted_apart():
    data = (
        b'{"id": 1, "who": "ada"}\n\nnot json\n{}\n[]\n{"id": 2, "who": "cy"}\n{"id":\n'
    )
    out = mod.convert(data, "log.jsonl")
    assert blocks(out) == [
        ["#1", "id: 1", "who: ada"],
        ["#6", "id: 2", "who: cy"],
        ["skipped 4: 3, 4, 5, 7"],
    ]
    assert mod.convert(b'"just a string"\n', "a.NDJSON") == "#1\njust a string\n"
    one = mod.convert(b'{"a": 1}\nbad\n', "x.ndjson")
    assert one.endswith("\n\nskipped 1: 2\n")
    many = mod.convert(b'{"a": 1}\n' + b"bad\n" * 25, "x.jsonl")
    assert many.endswith("skipped 25: 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, " +
                         "14, 15, 16, 17, 18, 19, 20, 21, …\n")  # fmt: skip
    assert mod.convert(b"bad\n{}\n\n", "x.jsonl") is None
    crlf = mod.convert(b'{"a": 1}\r\n{"a": 2}\r\n', "x.jsonl")
    assert blocks(crlf) == [["#1", "a: 1"], ["#2", "a: 2"]]
    same = b"".join(b'{"a": %d}\n' % i for i in range(4))
    assert blocks(mod.convert(same, "x.jsonl"))[0] == ["#1", "0"]


def test_a_json_file_holding_json_lines_is_not_json():
    with pytest.raises(ValueError):
        mod.convert(b'{"a": 1}\n{"a": 2}\n', "x.json")


def test_a_bom_is_read_and_an_empty_array_or_object_is_nothing_to_read():
    assert mod.convert(b'\xef\xbb\xbf{"a": 1}') == "a: 1\n"
    assert mod.convert(b"[]") is None and mod.convert(b" { } ") is None
    assert mod.convert(b'"hello"') == "hello\n" and mod.convert(b"3.0") == "3.0\n"


def test_bad_files_are_skipped_and_counted_never_a_crash(tmp_path):
    files = {
        "good.json": b'{"a": 1}',
        "utf16.json": '{"a": 1}'.encode("utf-16"),
        "broken.json": b'{"a": ',
        "empty.json": b"[]",
        "nothing.json": b"",
        "deep.json": b"[" * 200_000 + b"]" * 200_000,
        "allbad.jsonl": b"nope\n",
        "notes.txt": b'{"a": 1}',
    }
    got, out = mirror_of(tmp_path, files)
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip().endswith("wrote 1 files to " + str(out) + "; skipped 6")
    assert sorted(p.name for p in out.rglob("*") if p.is_file()) == ["good.json.txt"]


def test_a_mirror_bigger_than_the_kernel_reads_is_cut_into_parts_and_old_parts_go(
    tmp_path,
):
    rows = [{"id": i, "text": "word " * 40} for i in range(6000)]
    got, out = mirror_of(tmp_path, {"big.json": json.dumps(rows).encode()})
    assert got.returncode == 0, got.stderr
    names = sorted(p.name for p in out.iterdir())
    assert names[0] == "big.json.part2.txt" and "big.json.txt" in names
    files = [out / "big.json.txt"] + [
        out / f"big.json.part{n}.txt" for n in range(2, len(names) + 1)
    ]
    assert all(f.stat().st_size <= kernel.MAX_FILE for f in files)
    text = "".join(f.read_text(encoding="utf-8") for f in files)
    assert all(f"[{i}]\n{i}\n" in text for i in (0, 2999, 5999))
    assert all(f.read_text(encoding="utf-8").startswith("[") for f in files)
    assert len(kernel.chunks(out)) == 6000
    (tmp_path / "src/big.json").write_bytes(b'{"a": 1}')
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(out))
    assert sorted(p.name for p in out.iterdir()) == ["big.json.txt"]


def test_parts_cut_between_passages_and_keep_every_one():
    text = "aa\nbb\n\ncc\n\ndd\nee\n"
    assert mod.parts(text, limit=8) == ["aa\nbb\n", "cc\n", "dd\nee\n"]
    assert mod.parts(text, limit=100) == [text]
    assert mod.parts(text, limit=12) == ["aa\nbb\n\ncc\n", "dd\nee\n"]


def test_a_file_over_the_read_cap_is_skipped_and_counted(tmp_path, monkeypatch):
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    (src / "small.json").write_bytes(b'{"a": 1}')
    (src / "large.json").write_bytes(b'{"a": "' + b"x" * 100 + b'"}')
    monkeypatch.setattr(mod, "MAX_READ", 50)
    argv = ["mirror", "--from", str(src), "--to", str(out)]
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), *argv])
    assert mod.main(argv) == kernel.ALIVE
    assert sorted(p.name for p in out.iterdir()) == ["small.json.txt"]


def test_a_mirror_is_written_at_the_same_path_with_txt_added(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"a/orders.json": ORDERS, "a/log.jsonl": b'{"x": 1}\n', "b.ndjson": b"2\n"},
    )
    assert got.returncode == 0, got.stderr
    assert sorted(p.relative_to(out).as_posix() for p in out.rglob("*.txt")) == [
        "a/log.jsonl.txt",
        "a/orders.json.txt",
        "b.ndjson.txt",
    ]
    assert got.stdout.strip() == f"wrote 3 files to {out}; skipped 0"


def test_hidden_files_and_folders_are_not_read(tmp_path):
    got, out = mirror_of(
        tmp_path,
        {"a.json": b"[1]", ".hid/a.json": b"[1]", ".a.json": b"[1]", "UP.JSON": b"[2]"},
    )
    assert sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    ) == ["UP.JSON.txt", "a.json.txt"]


def test_the_same_folder_gives_the_same_bytes_and_originals_are_unchanged(tmp_path):
    got, out = mirror_of(tmp_path, {"orders.json": ORDERS})
    before = (tmp_path / "src/orders.json").read_bytes()
    again = tmp_path / "again"
    run("mirror", "--from", str(tmp_path / "src"), "--to", str(again))
    assert (again / "orders.json.txt").read_bytes() == (
        out / "orders.json.txt"
    ).read_bytes()
    assert (tmp_path / "src/orders.json").read_bytes() == before
    assert sorted(p.name for p in (tmp_path / "src").iterdir()) == ["orders.json"]


def test_a_folder_with_nothing_to_read_waits_on_you(tmp_path):
    got, _ = mirror_of(tmp_path, {"notes.md": b"nothing here\n", "e.json": b"{}"})
    assert got.returncode == 42 and "wrote 0 files" in got.stdout
    assert got.stdout.strip().endswith("skipped 1")


def test_a_mirror_inside_the_folder_or_the_folder_inside_it_is_refused(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/a.json").write_bytes(b"[1]")
    for to in (tmp_path / "src" / "m", tmp_path):
        got = run("mirror", "--from", str(tmp_path / "src"), "--to", str(to))
        assert got.returncode == 2 and got.stderr.startswith("refused")
    assert not (tmp_path / "src/m").exists()
    got = run(
        "mirror", "--from", str(tmp_path / "missing"), "--to", str(tmp_path / "m")
    )
    assert got.returncode == 2 and got.stderr.startswith("refused: not a folder")


def test_a_bad_command_line_says_how_to_run_it():
    for argv in (
        [],
        ["mirror"],
        ["mirror", "--from", "a"],
        ["nope", "--from", "a", "--to", "b"],
        ["mirror", "--from", "a", "--from", "b"],
    ):
        got = run(*argv)
        assert got.returncode == 2 and "json_paths.py mirror" in got.stderr
