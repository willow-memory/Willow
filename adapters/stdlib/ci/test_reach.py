"""reach.py: what an add-on's tests can read is drawn from its card and a
scan of its files, wide when the scan sees anything past it."""

from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("willow_reach", HERE / "reach.py")
reach = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reach)


def addon(
    root: Path, name: str, code: str = "", uses: str = "", kind: str = "stdlib"
) -> None:
    here = root / "adapters" / kind / name
    here.mkdir(parents=True)
    extra = f"uses: {uses}\n" if uses else ""
    (here / "README.md").write_text(
        f"<!-- willow-addon\nline: x.\n{extra}-->\n# {name}\n"
    )
    (here / f"{name}.py").write_text(code)


def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "kernel.py").write_text("")
    return root


def test_an_add_on_reaches_its_folder_what_its_card_names_in_turn_and_the_runner(
    tmp_path,
):
    root = repo(tmp_path)
    addon(root, "a", "import b\n", uses="b")
    addon(root, "b", uses="c")
    addon(root, "c", kind="deps")
    got = reach.reach(str(root), "stdlib/a")
    assert got == sorted(["adapters/stdlib/a/", "adapters/stdlib/b/", "adapters/deps/c/",
                          "kernel.py", "adapters/stdlib/ci/", "adapters/stdlib/test-shards/"])  # fmt: skip
    assert reach.within("adapters/stdlib/b/x.json", got) and reach.within(
        "kernel.py", got
    )
    assert not reach.within("adapters/stdlib/bb/x.py", got) and not reach.within(
        "docs/a.md", got
    )


def test_whatever_the_scan_sees_past_the_reach_draws_it_wide(tmp_path):
    root = repo(tmp_path)
    addon(root, "names-a-doc", 'p = ROOT / "docs" / "a.md"\n')
    addon(root, "lists", "for d in STDLIB.iterdir(): pass\n")
    addon(root, "other", "")
    addon(root, "unnamed", 'x = STDLIB / "other"\n')
    addon(root, "ci")  # a repo tool
    for name in ("names-a-doc", "lists", "unnamed", "ci"):
        assert reach.reach(str(root), f"stdlib/{name}") is None, name
    assert reach.wide_because(str(root), "stdlib/unnamed") == (
        "unnamed.py reaches other, which its card doesn't name"
    )
    assert reach.reach(str(root), "stdlib/other") is not None


def test_one_listed_wide_is_wide(tmp_path, monkeypatch):
    root = repo(tmp_path)
    addon(root, "plain")
    monkeypatch.setattr(reach, "WIDE", {"plain"})
    monkeypatch.setattr(reach, "_cache", {})
    assert reach.reach(str(root), "stdlib/plain") is None
