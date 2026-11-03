"""reports.py: scaffold gives an add-on the report's parts and --json without
touching how it reads its command line; the report_text it copies is stack's
word for word; it never scaffolds twice; check says a scaffold isn't done."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("reports", HERE / "reports.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)

#: an add-on that counts its flags, as secrets-audit does: a --json among them
#: would have been refused
STRICT = '''"""strict.py: a stand-in.

    python strict.py --box DIR
"""

import sys


def main(argv: list[str]) -> int:
    """Its docstring stays first."""
    opts = dict(zip(argv[::2], argv[1::2]))
    if len(opts) != 1 or "--box" not in opts:
        print("refused", file=sys.stderr)
        return 2
    print("found 1 thing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
'''


def stand_in(tmp_path: Path) -> Path:
    stdlib = tmp_path / "adapters" / "stdlib"
    (stdlib / "strict").mkdir(parents=True)
    (stdlib / "strict" / "strict.py").write_text(STRICT)
    return stdlib


def test_scaffold_takes_json_off_before_the_add_on_reads_its_arguments(tmp_path):
    stdlib = stand_in(tmp_path)
    assert rp.scaffold_one("strict", stdlib) == (
        True,
        "adapters/stdlib/strict/strict.py",
    )
    script = stdlib / "strict" / "strict.py"
    for argv in (["--box", "b"], ["--box", "b", "--json"], ["--json", "--box", "b"]):
        got = subprocess.run(
            [sys.executable, str(script), *argv], capture_output=True, text=True
        )
        assert (got.returncode, got.stdout) == (0, "found 1 thing\n"), argv
    src = script.read_text()
    assert 'NAME = "strict"' in src and "import json" in src and rp.WIRE in src
    assert src.index('"""Its docstring stays first."""') < src.index("as_json =")


def test_the_report_text_it_copies_is_stacks_word_for_word(tmp_path):
    stdlib = stand_in(tmp_path)
    rp.scaffold_one("strict", stdlib)
    assert rp.report_text_source() in (stdlib / "strict" / "strict.py").read_text()
    assert rp.report_text_source() in (rp.STDLIB / "stack" / "stack.py").read_text()


def test_it_never_scaffolds_twice_and_names_what_it_left(tmp_path):
    stdlib = stand_in(tmp_path)
    rp.scaffold_one("strict", stdlib)
    before = (stdlib / "strict" / "strict.py").read_text()
    assert rp.scaffold_one("strict", stdlib) == (
        False,
        "already has report, report_text or say",
    )
    assert (stdlib / "strict" / "strict.py").read_text() == before
    (stdlib / "nomain").mkdir()
    (stdlib / "nomain" / "nomain.py").write_text(
        "if __name__ == '__main__':\n    pass\n"
    )
    assert rp.scaffold_one("nomain", stdlib) == (
        False,
        "no main(argv) to take --json in",
    )


def test_a_bad_command_line_is_refused():
    assert rp.main([]) == rp.REFUSED
    assert rp.main(["scaffold"]) == rp.REFUSED
    assert rp.main(["check", "--stray"]) == rp.REFUSED
    assert rp.main(["survey", "extra"]) == rp.REFUSED
    assert rp.main(["scaffold", "not-an-add-on"]) == rp.REFUSED
