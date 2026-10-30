"""code-shape: ast-grep's matches of a pattern with holes, each shown with
the id of the kernel's own passage holding its first line; nothing written;
and a refusal, never a quiet skip, without ast-grep."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "code_shape.py"
NOW = ["--now", "2026-10-30T09:00:00Z"]

FETCH = """import requests


def fetch(url):
    # requests.get is only named here, not called
    return requests.get(
        url,
        timeout=3,
    )


def items(base):
    return requests.get(f"{base}/items").json()
"""


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True)  # fmt: skip


@pytest.fixture
def box(tmp_path: Path) -> Path:
    pile = tmp_path / "pile"
    (pile / "app").mkdir(parents=True)
    (pile / "app" / "fetch.py").write_text(FETCH)
    (pile / "app" / "old.py").write_text("try:\n    go()\nexcept:\n    pass\n")
    (pile / "web.js").write_text("fetch('/x').then(r => r.json())\n")
    (pile / ".venv").mkdir()
    (pile / ".venv" / "lib.py").write_text("requests.get('hidden')\n")
    b = tmp_path / "box"
    got = subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(b), "--pile",
                          str(pile), "--key", str(tmp_path / "key"), *NOW],
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stderr
    return b


def ids(box: Path) -> dict[str, str]:
    sys.path.insert(0, str(HERE.parents[2]))
    import kernel

    pile = Path(kernel.config(box)["pile"])
    return {f"{c['path']}:{c['line']}": c["id"][:12] for c in kernel.chunks(pile)}


def test_every_call_whatever_its_arguments_and_never_a_mention(box):
    got = run("--box", str(box), "--lang", "python", "requests.get($$$)")
    assert got.returncode == 0, got.stderr
    i = ids(box)
    assert got.stdout.splitlines() == [
        f"app/fetch.py:6  {i['app/fetch.py:4']}  return requests.get(",
        f'app/fetch.py:13  {i["app/fetch.py:12"]}  return requests.get(f"{{base}}/items").json()',
        "2 matches in 2 passages",
    ]


def test_a_shape_with_no_words_and_another_language(box):
    bare = run("--box", str(box), "--lang", "python", "try: $$$\nexcept: $$$")
    assert bare.returncode == 0 and bare.stdout.startswith("app/old.py:1  ")
    js = run("--box", str(box), "--lang", "javascript", "fetch($URL)")
    assert js.returncode == 0 and js.stdout.startswith("web.js:1  ")


def test_no_match_is_42(box):
    got = run("--box", str(box), "--lang", "python", "nothing_like_this($$$)")
    assert got.returncode == 42 and got.stdout == "0 matches in 0 passages\n"


def test_nothing_is_written(box, tmp_path):
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run("--box", str(box), "--lang", "python", "requests.get($$$)")
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_refusals(box, tmp_path):
    for argv in ([], ["--box", str(box), "x"], ["--box", str(box), "--lang", "python"],
                 ["--box", str(box), "--lang", "klingon", "x"],
                 ["--box", str(tmp_path), "--lang", "python", "x"]):  # fmt: skip
        assert run(*argv).returncode == 2, argv
    assert "klingon" in run("--box", str(box), "--lang", "klingon", "x").stderr


def test_without_ast_grep_it_refuses_and_names_the_install(box, tmp_path):
    lone = tmp_path / "lone"
    lone.mkdir()
    (lone / "python").symlink_to(sys.executable)
    got = subprocess.run([str(lone / "python"), str(SCRIPT), "--box", str(box),
                          "--lang", "python", "x"], capture_output=True, text=True,
                         env={"PATH": str(lone), "PYTHONPATH": ":".join(sys.path)})  # fmt: skip
    assert got.returncode == 2 and "requirements.txt" in got.stderr
