"""groups.py: every built add-on has one place, and the UI and the lists
read it from the same grouping."""

from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rd = load("willow_readme_for_groups", HERE / "readme.py")
g = rd.groups
EVERY = rd.addons()


def placed(a: dict) -> dict:
    return g.role({"name": a["name"], "section": a["section"], "line": a["line"],
                   "role": a.get("role", ""), "state": "built" if a["built"] else "idea"})  # fmt: skip


def test_every_built_add_on_lands_in_its_cards_role_and_a_named_group():
    for a in (a for a in EVERY if a["built"]):
        got = placed(a)
        assert got["role"] == a["role"], (a["name"], got)
        assert got["group"] not in (g.OTHER_READERS, "Other ways in"), (
            f"{a['name']} ({got['role']}) is in no group: add it to groups.py"
        )


def test_each_name_in_a_group_is_an_add_on_of_that_role_and_in_one_group_only():
    roles = {a["name"]: a["role"] for a in EVERY}
    seen: dict[str, str] = {}
    for role, table in (("reads", g.READERS), ("ways", g.WAYS)):
        for title, names in table:
            for n in names:
                assert n not in seen, f"{n} is under both {seen[n]} and {title}"
                seen[n] = title
                assert roles.get(n) == role, f"{title} names {n}, which isn't a {role} add-on"  # fmt: skip


def test_an_idea_not_yet_placed_still_has_a_heading():
    got = g.role({"name": "nowhere-yet", "section": "", "line": "", "role": "reads", "state": "idea"})  # fmt: skip
    assert got["group"] == g.OTHER_READERS and got["group_at"] == len(g.READERS)


def test_the_ui_and_the_list_share_the_one_grouping():
    canvas = load("willow_canvas_for_groups", ROOT / "ui" / "canvas.py")
    assert canvas.ROLES is canvas.groups.ROLES and canvas.role is canvas.groups.role
    assert {k for k, _ in canvas.groups.ROLES} == rd.ROLES
    assert canvas.groups.__file__ == g.__file__
