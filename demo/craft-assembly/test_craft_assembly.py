"""demo/craft-assembly: what was frozen stays frozen, and its tools do what
they say, on sources made here: pieces rebuild a source to git's own tree
hash, and compose assembles apps and a shared library into one workspace
by its rules alone, the same bytes twice, that Cargo builds and tests.

The study's runs fetch the Craft repositories and are not part of CI; this is.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compose  # noqa: E402
import pieces  # noqa: E402

URL = "https://example.org/acme/libs"
REV = "abcdef1234" + "0" * 30
GIT = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.org",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.org",
       "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}  # fmt: skip


def source(root: Path, files: dict[str, str | bytes], exe=(), links=None) -> Path:
    """A git repo holding `files`, in one commit."""
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode() if isinstance(text, str) else text)
    for rel in exe:
        os.chmod(root / rel, 0o755)
    for rel, target in (links or {}).items():
        os.symlink(target, root / rel)
    env = {**os.environ, **GIT}
    for argv in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-qm", "one"]):
        subprocess.run(
            ["git", *argv], cwd=root, env=env, check=True, capture_output=True
        )
    return root


def git_tree(root: Path) -> str:
    return subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD^{tree}"],
                          capture_output=True, text=True, check=True).stdout.strip()  # fmt: skip


def files(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): (os.readlink(p).encode() if p.is_symlink() else p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file() or p.is_symlink()}  # fmt: skip


# ── pieces ──────────────────────────────────────────────────────────────────
def two_sources(tmp_path: Path) -> Path:
    src = tmp_path / "sources"
    shared = "fn shared() -> u32 { 7 }\n"
    source(src / "one", {"README.md": "one\n", "src/lib.rs": shared, "run.sh": "#!/bin/sh\n",
                         "deep/a/b/c.txt": "deep\n"}, exe=["run.sh"], links={"latest": "README.md"})  # fmt: skip
    source(src / "two", {"README.md": "two\n", "src/lib.rs": shared})
    (src / "two" / "empty").mkdir()  # git has no empty folders, and neither does a tree
    return src


@pytest.mark.skipif(
    os.name != "posix", reason="the sources hold a symlink and an executable"
)
def test_a_source_taken_apart_rebuilds_to_git_s_own_tree(tmp_path):
    src = two_sources(tmp_path)
    store = tmp_path / "store"
    counts = pieces.apart(src, store)
    assert counts == {"sources": 2, "files": 7, "pieces": 6, "shared_pieces": 1,
                      "shared_bytes": 25, "piece_bytes": 57}  # fmt: skip
    for name in ("one", "two"):
        assert pieces.recipe(store, name)["tree"] == git_tree(src / name)
    out = tmp_path / "out"
    assert pieces.rebuild(store, out) == ["one", "two"]
    assert pieces.check(store, out) == {"one": True, "two": True}
    assert files(out / "one") == {
        k: v for k, v in files(src / "one").items() if not k.startswith(".git/")
    }
    assert os.stat(out / "one" / "run.sh").st_mode & 0o100
    assert os.readlink(out / "one" / "latest") == "README.md"
    (out / "two" / "README.md").write_text("changed\n")
    assert pieces.check(store, out) == {"one": True, "two": False}, (
        "a changed byte is caught"
    )


def test_taking_apart_twice_gives_the_same_store(tmp_path):
    src = two_sources(tmp_path)
    pieces.apart(src, tmp_path / "a")
    pieces.apart(src, tmp_path / "b")
    assert files(tmp_path / "a") == files(tmp_path / "b")


def test_a_piece_that_doesn_t_hash_to_its_name_is_refused(tmp_path):
    src = two_sources(tmp_path)
    store = tmp_path / "store"
    pieces.apart(src, store)
    sha = hashlib.sha256(b"two\n").hexdigest()
    (store / "objects" / sha[:2] / sha).write_bytes(b"tampered\n")
    with pytest.raises(ValueError, match="doesn't hash"):
        pieces.rebuild(store, tmp_path / "out", "two")


def test_a_recipe_row_that_climbs_out_is_refused(tmp_path):
    store = tmp_path / "store"
    sha = pieces.put(store, b"x")
    for path in ("../escape", "/etc/passwd"):
        with pytest.raises(ValueError, match="can't be written"):
            pieces.write(store, [[path, "100644", sha]], tmp_path / "out")


# ── compose ─────────────────────────────────────────────────────────────────
def lib(name: str) -> str:
    return f'{{ git = "{URL}", rev = "{REV}"{name} }}'


def apps(
    tmp_path: Path, a_profile="lto = true", b_profile="lto = false", patch_b=""
) -> Path:
    src = tmp_path / "sources"
    for app, profile, extra in (("appa", a_profile, ""), ("appb", b_profile, patch_b)):
        source(src / app, {
            "Cargo.toml": f"""[workspace]
resolver = "2"
members = ["crates/*", "xtask"]

[workspace.package]
version = "1.{ord(app[-1]) - 97}.0"
edition = "2021"
license = "MIT"

[workspace.dependencies]
{app}-core = {{ path = "crates/core" }}
lib-ui = {lib(', features = ["serde"]')}

[workspace.lints.rust]
unsafe_code = "forbid"

[profile.release]
{profile}

[profile.dev]
debug = 0
{extra}""",
            "Cargo.lock": "# a lockfile the composite never copies\n",
            "crates/core/Cargo.toml": f"""[package]
name = "{app}-core"
version.workspace = true
edition.workspace = true
license.workspace = true

[lints]
workspace = true
""",
            "crates/core/src/lib.rs": f"pub fn core() -> &'static str {{ \"{app}\" }}\n",
            "crates/app/Cargo.toml": f"""[package]
name = "{app}"
version.workspace = true
edition.workspace = true

[dependencies]
{app}-core.workspace = true
lib-ui = {{ workspace = true, features = ["extra"] }}
""",
            "crates/app/src/lib.rs": f"""pub fn hello() -> String {{ format!("{{}} {{}}", {app}_core::core(), lib_ui::ui()) }}

#[cfg(test)]
mod tests {{
    #[test]
    fn says_its_name() {{ assert_eq!(super::hello(), "{app} ui"); }}
}}
""",
            "xtask/Cargo.toml": '[package]\nname = "xtask"\nversion = "0.1.0"\nedition = "2021"\n',
            "xtask/src/main.rs": "fn main() {}\n",
            "assets/logo.txt": f"{app} logo\n",
            # a test fixture that is a workspace of its own, below a member:
            # `crates/*` must not name it, as Cargo's glob doesn't
            "crates/app/tests/fixture/Cargo.toml": '[workspace]\n\n[package]\nname = "fixture"\n'
                                                   'version = "0.0.0"\nedition = "2021"\n',
            "crates/app/tests/fixture/src/lib.rs": "",
        })  # fmt: skip
    source(src / f"craft-libs@{REV[:10]}", {
        "Cargo.toml": '[workspace]\nmembers = ["crates/*"]\n\n[workspace.package]\nedition = "2021"\n',
        "LICENSE-MIT": "MIT License\n",
        "crates/ui/Cargo.toml": '[package]\nname = "lib-ui"\nversion = "0.1.0"\nedition.workspace = true\n\n'
                                '[features]\nserde = []\nextra = []\n',
        "crates/ui/src/lib.rs": "pub fn ui() -> &'static str { \"ui\" }\n",
        "crates/other/Cargo.toml": '[package]\nname = "lib-other"\nversion = "0.1.0"\nedition = "2021"\n',
        "crates/other/src/lib.rs": "",
        "docs/notes.md": "not a crate anyone needs\n",
    })  # fmt: skip
    return src


RECIPE = {"apps": ["appa", "appb"], "library": URL}


def composed(tmp_path: Path, **kw) -> tuple[Path, Path, dict]:
    src = apps(tmp_path, **kw)
    store = tmp_path / "store"
    pieces.apart(src, store)
    out = tmp_path / "composite"
    return src, out, compose.compose(store, RECIPE, out)


def test_the_composite_holds_both_apps_and_the_library_once(tmp_path):
    src, out, glue = composed(tmp_path)
    root = tomllib.loads((out / "Cargo.toml").read_text())
    assert root["workspace"] == {
        "resolver": "2",
        "members": [
            "appa/crates/app",
            "appa/crates/core",
            "appb/crates/app",
            "appb/crates/core",
        ],
        "exclude": ["appa/xtask", "appb/xtask"],
    }
    assert root["profile"] == {"dev": {"debug": 0}}, (
        "rule 4: only a profile every app agrees on"
    )
    assert glue["profiles_dropped"] == ["release.lto"], (
        "rule 4: what the apps disagree on"
    )
    assert glue["left_out"] == [
        {"member": "appa/xtask", "why": "the name xtask is in 2 apps"},
        {"member": "appb/xtask", "why": "the name xtask is in 2 apps"},
    ]
    assert glue["library"] == {"lib-ui": {"commit": REV[:10], "folder": f"craft-libs/{REV[:10]}/crates/ui",
                                          "used_by": ["appa", "appb"]}}  # fmt: skip
    assert sorted(files(out / "craft-libs")) == [
        f"{REV[:10]}/LICENSE-MIT", f"{REV[:10]}/crates/ui/Cargo.toml", f"{REV[:10]}/crates/ui/src/lib.rs",
    ]  # fmt: skip
    assert (
        not (out / "appa" / "Cargo.lock").exists()
        and not (out / "appa" / "Cargo.toml").exists()
    )


def test_inheritance_is_inlined_from_each_app_s_own_workspace(tmp_path):
    _, out, _ = composed(tmp_path)
    a = tomllib.loads((out / "appa" / "crates" / "app" / "Cargo.toml").read_text())
    b = tomllib.loads((out / "appb" / "crates" / "app" / "Cargo.toml").read_text())
    assert a["package"] == {"name": "appa", "version": "1.0.0", "edition": "2021"}
    assert b["package"]["version"] == "1.1.0", "each app keeps its own versions"
    assert a["dependencies"] == {
        "appa-core": {"path": "../core"},
        "lib-ui": {
            "features": ["serde", "extra"],
            "path": f"../../../craft-libs/{REV[:10]}/crates/ui",
        },
    }
    core = tomllib.loads((out / "appa" / "crates" / "core" / "Cargo.toml").read_text())
    assert core["lints"] == {"rust": {"unsafe_code": "forbid"}}
    assert core["package"]["license"] == "MIT"
    ui = tomllib.loads(
        (out / "craft-libs" / REV[:10] / "crates" / "ui" / "Cargo.toml").read_text()
    )
    assert ui["package"]["edition"] == "2021"


def test_every_other_file_is_its_piece_byte_for_byte(tmp_path):
    src, out, glue = composed(tmp_path)
    rewritten = {g["file"] for g in glue["rewritten"]}
    for app in ("appa", "appb"):
        for rel, data in files(src / app).items():
            if rel.startswith(".git/") or rel in ("Cargo.toml", "Cargo.lock"):
                continue
            if f"{app}/{rel}" in rewritten:
                continue
            assert (out / app / rel).read_bytes() == data, rel
    assert len(rewritten) == 5, (
        "four app members and the library crate; the xtasks left out are copied as they are"
    )


def test_composing_twice_gives_the_same_bytes(tmp_path):
    src = apps(tmp_path)
    store = tmp_path / "store"
    pieces.apart(src, store)
    compose.compose(store, RECIPE, tmp_path / "one")
    compose.compose(store, RECIPE, tmp_path / "two")
    assert files(tmp_path / "one") == files(tmp_path / "two")


def test_cargo_builds_and_tests_the_composite_offline(tmp_path):
    _, out, _ = composed(tmp_path)
    env = {
        **os.environ,
        "CARGO_TARGET_DIR": str(tmp_path / "target"),
        "CARGO_NET_OFFLINE": "true",
    }
    got = subprocess.run(["cargo", "test", "--workspace", "--offline", "-q"], cwd=out, env=env,
                         capture_output=True, text=True)  # fmt: skip
    assert got.returncode == 0, got.stderr
    assert got.stdout.count("1 passed") == 2, got.stdout
    lock = (out / "Cargo.lock").read_text()
    assert lock.count('name = "lib-ui"') == 1, (
        "the library crate both apps use is built once"
    )


def test_a_library_crate_wanted_at_two_commits_stops_it(tmp_path):
    src = apps(tmp_path)
    other = "fedcba9876" + "1" * 30
    source(src / f"craft-libs@{other[:10]}", {
        "Cargo.toml": '[workspace]\nmembers = ["crates/*"]\n',
        "crates/ui/Cargo.toml": '[package]\nname = "lib-ui"\nversion = "0.1.0"\nedition = "2021"\n',
        "crates/ui/src/lib.rs": "",
    })  # fmt: skip
    b = src / "appb" / "Cargo.toml"
    b.write_text(b.read_text().replace(REV, other))
    store = tmp_path / "store"
    pieces.apart(src, store)
    with pytest.raises(compose.Stop, match="lib-ui is wanted at two commits"):
        compose.compose(store, RECIPE, tmp_path / "out")


def test_a_commit_the_store_lacks_stops_it(tmp_path):
    src = apps(tmp_path)
    b = src / "appb" / "Cargo.toml"
    b.write_text(b.read_text().replace(REV, "0" * 40))
    store = tmp_path / "store"
    pieces.apart(src, store)
    with pytest.raises(compose.Stop, match="which the store doesn't hold"):
        compose.compose(store, RECIPE, tmp_path / "out")


def test_profiles_join_setting_by_setting():
    dev = {"opt-level": 1, "package": {"*": {"opt-level": 2}}}
    a = {"dev": {**dev, "package": {**dev["package"], "codec-a": {"opt-level": 3}}},
         "release": {"lto": "thin", "codegen-units": 16}}  # fmt: skip
    b = {"dev": {**dev, "package": {**dev["package"], "codec-b": {"opt-level": 3}}},
         "release": {"lto": "thin", "codegen-units": 1}}  # fmt: skip
    c = {"dev": {"opt-level": 1, "package": {"codec-a": {"opt-level": 2}}}}
    dropped: list[str] = []
    assert compose.join_profiles([a, b], dropped) == {
        "dev": {"opt-level": 1, "package": {"*": {"opt-level": 2}, "codec-a": {"opt-level": 3},
                                            "codec-b": {"opt-level": 3}}},
        "release": {"lto": "thin"},
    }  # fmt: skip
    assert dropped == ["release.codegen-units"]
    dropped = []
    assert compose.join_profiles([a, c], dropped) == {
        "dev": {"opt-level": 1}, "release": {"lto": "thin", "codegen-units": 16},
    }  # fmt: skip
    assert dropped == ["dev.package.*", "dev.package.codec-a.opt-level"], (
        "an override that differs, or one only some apps set for every package"
    )


def test_patches_join_and_a_clash_stops_it(tmp_path):
    patch = '\n[patch.crates-io]\nfoo = { path = "vendor/foo" }\n'
    _, out, _ = composed(tmp_path, patch_b=patch)
    assert tomllib.loads((out / "Cargo.toml").read_text())["patch"] == {
        "crates-io": {"foo": {"path": "vendor/foo"}}
    }
    clash = tmp_path / "clash"
    src = apps(
        clash, a_profile='lto = true\n\n[patch.crates-io]\nfoo = "1"', patch_b=patch
    )
    store = clash / "store"
    pieces.apart(src, store)
    with pytest.raises(compose.Stop, match=r"\[patch.crates-io\] foo differs"):
        compose.compose(store, RECIPE, clash / "out")


def test_the_toml_written_reads_back_as_what_was_given():
    doc = {
        "cargo-features": ["edition2024"],
        "package": {
            "name": "x",
            "version": "1.0.0",
            "metadata": {"docs": {"rs": {"all-features": True}}},
        },
        "dependencies": {"a": {"version": "1", "features": ["b"]}, "c": "2"},
        "target": {
            'cfg(target_os = "linux")': {"dependencies": {"d": {"path": "../d"}}}
        },
        "bin": [{"name": "one", "path": "src/one.rs"}, {"name": "two", "test": False}],
        "features": {"default": [], "full": ["a/b"]},
        "lints": {"rust": {"unsafe_code": {"level": "forbid", "priority": -1}}},
        "badges": {},
        "weird key": 1.5,
    }
    assert tomllib.loads(compose.toml(doc)) == doc


# ── what was frozen ─────────────────────────────────────────────────────────
def test_the_pins_are_whole():
    pins = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))["sources"]
    assert len(pins) == 21
    for name, pin in pins.items():
        assert len(pin["commit"]) == 40 and len(pin["tree"]) == 40, name
        assert pin["url"].startswith("https://github.com/storytold/"), name
        if name.startswith("craft-libs@"):
            assert pin["commit"].startswith(name.split("@")[1])
    recipe = json.loads((HERE / "composite.json").read_text(encoding="utf-8"))
    assert set(recipe["apps"]) <= set(pins)


# ── the pass rules ──────────────────────────────────────────────────────────
import run  # noqa: E402


def outcome(builds: bool, tests: bool) -> dict:
    return {"builds": builds, "tests": tests}


def test_the_rules_count_only_what_held_in_the_app_itself():
    rebuilt = dict.fromkeys(run.sources.PINS, True)
    base = {
        "appa": {
            "a-core": outcome(True, True),
            "a-gui": outcome(True, False),
            "a-broken": outcome(False, False),
        }
    }
    good = {"rebuilt": rebuilt, "same_store": True, "same_composite": True, "baseline": base,
            "composite": {"appa": {"a-core": outcome(True, True), "a-gui": outcome(True, False),
                                   "a-broken": outcome(False, False)}}}  # fmt: skip
    assert run.rules(good) == dict.fromkeys(
        ["rebuilt", "same-store", "same-composite", "builds", "tests"], True
    )
    lost_test = {
        **good,
        "composite": {
            "appa": {**good["composite"]["appa"], "a-core": outcome(True, False)}
        },
    }
    assert (
        run.rules(lost_test)["tests"] is False
        and run.rules(lost_test)["builds"] is True
    )
    lost_build = {
        **good,
        "composite": {
            "appa": {**good["composite"]["appa"], "a-gui": outcome(False, False)}
        },
    }
    assert (
        run.rules(lost_build)["builds"] is False
        and run.rules(lost_build)["tests"] is True
    )
    gone = {**good, "composite": {"appa": {}}}
    assert run.rules(gone)["builds"] is False, (
        "a package missing from the composite didn't build there"
    )


def test_every_source_must_rebuild_and_both_runs_must_match():
    rebuilt = dict.fromkeys(run.sources.PINS, True)
    res = {"rebuilt": rebuilt, "same_store": True, "same_composite": True}
    assert run.rules(res) == {
        "rebuilt": True,
        "same-store": True,
        "same-composite": True,
    }
    one_broken = {**res, "rebuilt": {**rebuilt, "cadcraft": False}}
    assert run.rules(one_broken)["rebuilt"] is False
    one_missing = {
        **res,
        "rebuilt": {k: v for k, v in rebuilt.items() if k != "cadcraft"},
    }
    assert run.rules(one_missing)["rebuilt"] is False, (
        "a source not rebuilt at all doesn't hold"
    )
    assert run.rules({**res, "same_store": False})["same-store"] is False
    assert run.rules({**res, "same_composite": False})["same-composite"] is False


def test_a_digest_changes_with_any_byte_mode_or_name(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "f.txt").write_text("x\n")
    first = run.digest(tmp_path / "a")
    (tmp_path / "a" / "f.txt").write_text("y\n")
    assert run.digest(tmp_path / "a") != first
    (tmp_path / "a" / "f.txt").write_text("x\n")
    assert run.digest(tmp_path / "a") == first
    os.chmod(tmp_path / "a" / "f.txt", 0o755)
    assert run.digest(tmp_path / "a") != first
    os.chmod(tmp_path / "a" / "f.txt", 0o644)
    (tmp_path / "a" / "f.txt").rename(tmp_path / "a" / "g.txt")
    assert run.digest(tmp_path / "a") != first


def test_every_frozen_file_is_as_it_was_frozen():
    frozen = json.loads((HERE / "FROZEN.json").read_text(encoding="utf-8"))
    for rel, sha in frozen["files"].items():
        got = hashlib.sha256((HERE / rel).read_bytes()).hexdigest()
        assert got == sha, (
            f"{rel} changed after it was frozen; a change is a new freeze"
        )
    assert set(frozen["files"]) == {"sources.json", "composite.json", "pieces.py", "compose.py",
                                    "run.py", "sources.py"}  # fmt: skip
