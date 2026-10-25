"""compose.py: one Cargo workspace assembled from the store's pieces, by rule.

    python demo/craft-assembly/compose.py --store STORE --recipe composite.json --to OUT

The recipe names the apps (sources in the store, each a Cargo workspace).
Everything is read from the store (pieces.py apart wrote it), never from a
checkout, and OUT is written as:

    OUT/<app>/...                every file of the app, byte for byte, but its
                                 root Cargo.toml and Cargo.lock; each member's
                                 Cargo.toml is rewritten (below)
    OUT/git/<repo>/<rev>/...     each crate an app takes by git, at the commit
                                 it pinned, with that commit's licence files;
                                 its Cargo.toml rewritten too. Not a member:
                                 the workspace excludes git/
    OUT/Cargo.toml               the one workspace: every member, sorted
    OUT/GLUE.json                every file the rules wrote, with the piece it
                                 came from, and everything they left out, why

The rules, all of them; none looks at what a build does:

    1. inherit    a member's `x.workspace = true` (in [package], a dependency
                  table, or [lints]) is replaced by its own app's workspace
                  value: dependencies keep the member's added features and
                  `optional`; a path in a workspace value is made relative to
                  the member again. Each app keeps its own versions, so apps
                  that pin different versions of a crate need no choosing.
    2. git        a dependency by git becomes a path dependency on that crate,
                  taken from the store at the commit pinned: its `rev`, or
                  for a branch or none, the commit its source's own Cargo.lock
                  holds. So do the crates it depends on by path at that
                  commit. A crate wanted at two commits, or at a commit the
                  store lacks, stops the composite.
    3. clash      a package name in two apps is left out in both, and so is
                  every member that depends on a member left out.
    4. profile    profiles are joined setting by setting: a setting of
                  [profile.X], or of one package's override in it, is kept when
                  every app that has [profile.X] gives it the same value, and
                  dropped (and listed) when they differ or some leave it out.
                  [patch] tables are joined; a clash stops.
    5. drop       each app's root Cargo.toml and Cargo.lock are not copied:
                  the composite has one root and resolves one lockfile.
    6. links      `resolve` asks Cargo for that lockfile. When Cargo says two
                  versions of a crate link one native library, the members
                  that depend on the crate are grouped by the version they
                  ask for; the group fewer apps use (on a tie, the one whose
                  apps come later in the recipe) is left out, with every
                  member that depends on one of them, and Cargo is asked
                  again. Any other failure to resolve is said, not settled.

Same store and recipe, same bytes; with rule 6, the same registry too.
Exit codes: 0 composed; 2 refused, or a rule that stops the composite.
"""

from __future__ import annotations

import fnmatch
import json
import os
import posixpath
import re
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pieces  # noqa: E402

DEP_TABLES = ("dependencies", "dev-dependencies", "build-dependencies")
PACKAGE_PATHS = {"readme", "license-file"}  # [package] keys that hold a path
LICENCE = re.compile(r"(?i)^(licen[cs]e|copying|notice|attribution)")


class Stop(Exception):
    """A rule that stops the composite."""


# ── TOML out ────────────────────────────────────────────────────────────────
BARE = re.compile(r"^[A-Za-z0-9_-]+$")


def key(k: str) -> str:
    return k if BARE.match(k) else json.dumps(k, ensure_ascii=False)


def value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ", ".join(value(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{key(k)} = {value(x)}" for k, x in v.items()) + " }"
    return v.isoformat()  # a TOML date or time


def is_tables(v) -> bool:
    return isinstance(v, list) and bool(v) and all(isinstance(x, dict) for x in v)


def toml(doc: dict) -> str:
    """`doc` as TOML: scalars first, then each table and array of tables, in
    the order they came; a dependency spec stays one inline table."""
    out: list[str] = []

    def emit(table: dict, path: list[str], header: str) -> None:
        plain = {
            k: v
            for k, v in table.items()
            if not (isinstance(v, dict) and not inline(path, k)) and not is_tables(v)
        }
        if header and (plain or not table):
            out.append(f"\n{header}")
        for k, v in plain.items():
            out.append(f"{key(k)} = {value(v)}")
        for k, v in table.items():
            sub = path + [k]
            if isinstance(v, dict) and not inline(path, k):
                emit(v, sub, "[" + ".".join(map(key, sub)) + "]")
            elif is_tables(v):
                for item in v:
                    out.append("\n[[" + ".".join(map(key, sub)) + "]]")
                    emit(item, sub, "")

    emit(doc, [], "")
    return "\n".join(out).lstrip("\n") + "\n"


def inline(path: list[str], k: str) -> bool:
    """A dependency's spec is written inline: `name = { version = "1" }`."""
    return bool(path) and path[-1] in DEP_TABLES


# ── reading the store ───────────────────────────────────────────────────────
def rows_of(store: Path, name: str) -> dict[str, tuple[str, str]]:
    return {p: (m, s) for p, m, s in pieces.recipe(store, name)["files"]}


def manifest(store: Path, rows: dict, path: str) -> dict:
    return tomllib.loads(pieces.get(store, rows[path][1]).decode("utf-8"))


def members(ws: dict, rows: dict) -> list[str]:
    """The member folders a workspace's globs name, that hold a Cargo.toml."""
    dirs = sorted(
        {posixpath.dirname(p) for p in rows if posixpath.basename(p) == "Cargo.toml"}
        - {""}
    )

    def pick(globs: list[str]) -> set[str]:
        return {d for d in dirs for g in globs if matches(d, g.rstrip("/"))}

    return sorted(pick(ws.get("members", [])) - pick(ws.get("exclude", [])))


def matches(path: str, glob: str) -> bool:
    """A workspace glob as Cargo reads it: `*` stays inside one folder name,
    so `crates/*` names crates/core but never crates/core/tests/fixture."""
    parts, pats = path.split("/"), glob.split("/")
    return len(parts) == len(pats) and all(
        fnmatch.fnmatchcase(p, g) for p, g in zip(parts, pats)
    )


def rel(target: str, member: str) -> str:
    return posixpath.relpath(posixpath.normpath(target), member) if target else "."


# ── the rules ───────────────────────────────────────────────────────────────
class App:
    def __init__(self, store: Path, name: str):
        self.name, self.rows = name, rows_of(store, name)
        if "Cargo.toml" not in self.rows:
            raise Stop(f"{name} has no root Cargo.toml")
        self.root = manifest(store, self.rows, "Cargo.toml")
        self.ws = self.root.get("workspace", {})
        if "package" in self.root:
            raise Stop(f"{name}'s root is a package as well as a workspace")
        self.members = members(self.ws, self.rows)


def inherit(doc: dict, ws: dict, member: str, libs, where: str) -> dict:
    """Rule 1 and rule 2 on one manifest; `member` is its folder in its own
    source, `where` that folder in the composite."""
    out = dict(doc)
    pkg = dict(doc.get("package", {}))
    for k, v in doc.get("package", {}).items():
        if isinstance(v, dict) and v.get("workspace") is True:
            got = ws.get("package", {})[k]
            pkg[k] = (
                rel(got, member) if k in PACKAGE_PATHS and isinstance(got, str) else got
            )
    if pkg:
        out["package"] = pkg
    if isinstance(doc.get("lints"), dict) and doc["lints"].get("workspace") is True:
        out["lints"] = ws.get("lints", {})

    def deps(table: dict) -> dict:
        new = {}
        for name, spec in table.items():
            if isinstance(spec, dict) and spec.get("workspace") is True:
                base = ws.get("dependencies", {})[name]
                base = {"version": base} if isinstance(base, str) else dict(base)
                if "path" in base:
                    base["path"] = rel(base["path"], member)
                feats = base.get("features", []) + [
                    f
                    for f in spec.get("features", [])
                    if f not in base.get("features", [])
                ]
                if feats:
                    base["features"] = feats
                for k, v in spec.items():
                    if k not in ("workspace", "features"):
                        base[k] = v
                spec = base
            new[name] = libs(name, spec, where) if isinstance(spec, dict) else spec
        return new

    for t in DEP_TABLES:
        if t in doc:
            out[t] = deps(doc[t])
    if "target" in doc:
        out["target"] = {cfg: {k: (deps(v) if k in DEP_TABLES else v) for k, v in tables.items()}
                         for cfg, tables in doc["target"].items()}  # fmt: skip
    return out


def compose(store: Path, recipe: dict, to: Path) -> dict:
    apps = [App(store, n) for n in recipe["apps"]]
    sources = {
        p.stem: rows_of(store, p.stem) for p in (store / "recipes").glob("*@*.json")
    }
    glue = {
        "rewritten": [],
        "left_out": [],
        "profiles_dropped": [],
        "git": {},
        "local_cargo_config": [],
    }
    needed: dict[str, tuple[str, str]] = {}  # package -> (source, its folder)
    used_by: dict[str, set[str]] = {}

    def git_dep(lock_rows: dict):
        def libs(name: str, spec: dict, where: str) -> dict:
            if "git" not in spec:
                return spec
            url = spec["git"].rstrip("/").removesuffix(".git")
            repo, pkg = url.rsplit("/", 1)[-1], spec.get("package", name)
            commit = spec.get("rev") or locked(store, lock_rows, url, pkg)
            src = next((n for n in sorted(sources) if n.split("@")[0] == repo and len(commit) >= 10
                        and commit.startswith(n.split("@")[1])), None)  # fmt: skip
            if src is None:
                raise Stop(
                    f"{pkg} wants {repo} at {commit or 'no commit'}, which the store doesn't hold"
                )
            want(pkg, src, lib_folder(store, sources[src], pkg))
            if not where.startswith(("git/", ".")):
                used_by.setdefault(pkg, set()).add(where.split("/")[0])
            out = {
                k: v
                for k, v in spec.items()
                if k not in ("git", "rev", "branch", "tag")
            }
            out["path"] = rel(
                posixpath.normpath(f"git/{src.replace('@', '/')}/{needed[pkg][1]}"),
                where,
            )
            return out

        return libs

    def want(pkg: str, src: str, folder: str) -> None:
        if needed.setdefault(pkg, (src, folder)) != (src, folder):
            raise Stop(f"{pkg} is wanted at two commits, {needed[pkg][0]} and {src}")

    # rule 3: names in two apps
    names: dict[str, list[tuple[str, str]]] = {}
    docs: dict[tuple[str, str], dict] = {}
    for app in apps:
        for m in app.members:
            doc = manifest(store, app.rows, f"{m}/Cargo.toml")
            docs[(app.name, m)] = doc
            names.setdefault(doc.get("package", {}).get("name", m), []).append(
                (app.name, m)
            )
    out_of = {am for n, where in names.items() if len(where) > 1 for am in where}
    for n, where in sorted(names.items()):
        if len(where) > 1:
            glue["left_out"] += [
                {"member": f"{a}/{m}", "why": f"the name {n} is in {len(where)} apps"}
                for a, m in where
            ]
    changed = True
    while changed:  # and whatever depends on a member left out
        changed = False
        for (a, m), doc in sorted(docs.items()):
            if (a, m) in out_of:
                continue
            app = next(x for x in apps if x.name == a)
            for dep in path_deps(doc, app.ws, m):
                if (a, dep) in out_of:
                    out_of.add((a, m))
                    glue["left_out"].append(
                        {
                            "member": f"{a}/{m}",
                            "why": f"it depends on {a}/{dep}, left out",
                        }
                    )
                    changed = True
                    break

    # copy the apps, rewriting each member's manifest
    kept = []
    for app in apps:
        manifests = {f"{m}/Cargo.toml" for m in app.members}
        for path, (mode, sha) in sorted(app.rows.items()):
            if path in ("Cargo.toml", "Cargo.lock"):
                continue
            if path.startswith(".cargo/") or "/.cargo/" in path:
                glue["local_cargo_config"].append(f"{app.name}/{path}")
            target = f"{app.name}/{path}"
            if path in manifests and (app.name, posixpath.dirname(path)) not in out_of:
                m = posixpath.dirname(path)
                text = toml(
                    inherit(
                        docs[(app.name, m)],
                        app.ws,
                        m,
                        git_dep(app.rows),
                        f"{app.name}/{m}",
                    )
                )
                write_text(to / target, text)
                glue["rewritten"].append(
                    {"file": target, "from": sha, "rule": "inherit, git"}
                )
                kept.append(f"{app.name}/{m}")
            else:
                pieces.write(store, [[path, mode, sha]], to / app.name)

    # [patch] tables joined, each git entry from the store as rule 2 says
    patch: dict[str, dict] = {}
    for a in apps:
        for src, table in a.root.get("patch", {}).items():
            for k, v in table.items():
                if isinstance(v, dict) and "git" in v:
                    v = git_dep(a.rows)(k, v, ".")
                    used_by.setdefault(v.get("package", k), set()).add(a.name)
                if patch.setdefault(src, {}).setdefault(k, v) != v:
                    raise Stop(f"[patch.{src}] {k} differs between apps")

    # the crates taken by git, each at its commit, with its path deps there
    done: set[str] = set()
    while set(needed) - done:
        pkg = sorted(set(needed) - done)[0]
        done.add(pkg)
        src, folder = needed[pkg]
        rows = sources[src]
        top = tomllib.loads(pieces.get(store, rows["Cargo.toml"][1]).decode("utf-8"))
        base = f"git/{src.replace('@', '/')}"
        manifest_path = "Cargo.toml" if folder == "." else f"{folder}/Cargo.toml"
        doc = tomllib.loads(pieces.get(store, rows[manifest_path][1]).decode("utf-8"))
        for dep in path_deps(doc, top.get("workspace", {}), folder):
            want(package_at(store, rows, dep), src, dep)
        for path, (mode, sha) in sorted(rows.items()):
            top_licence = "/" not in path and LICENCE.match(path)
            if not (top_licence or folder == "." or path.startswith(folder + "/")):
                continue
            if path == manifest_path:
                text = toml(
                    inherit(
                        doc,
                        top.get("workspace", {}),
                        folder,
                        git_dep(rows),
                        posixpath.normpath(f"{base}/{folder}"),
                    )
                )
                write_text(to / base / path, text)
                glue["rewritten"].append(
                    {"file": f"{base}/{path}", "from": sha, "rule": "inherit, git"}
                )
            elif not (to / base / path).exists():
                pieces.write(store, [[path, mode, sha]], to / base)
        glue["git"][pkg] = {"source": src, "folder": posixpath.normpath(f"{base}/{folder}"),
                            "used_by": sorted(used_by.get(pkg, ()))}  # fmt: skip

    # rule 4 and the root
    profiles = join_profiles(
        [a.root.get("profile", {}) for a in apps], glue["profiles_dropped"]
    )
    resolver = max((a.ws.get("resolver", "1") for a in apps), key=lambda r: int(r))
    exclude = sorted(f"{a}/{m}" for a, m in out_of) + (["git"] if needed else [])
    root = {
        "workspace": {"resolver": resolver, "members": sorted(kept), "exclude": exclude}
    }
    if profiles:
        root["profile"] = profiles
    if patch:
        root["patch"] = patch
    write_text(to / "Cargo.toml", toml(root))
    glue["members"] = len(kept)
    glue["left_out"].sort(key=lambda g: g["member"])
    glue["rewritten"].sort(key=lambda g: g["file"])
    write_text(to / "GLUE.json", pieces.dump(glue))
    return glue


def join_profiles(all_profiles: list[dict], dropped: list[str]) -> dict:
    """Rule 4: each profile's settings, and each package override's, kept
    where every app with that profile agrees; `dropped` gets the rest."""
    out = {}
    for name in sorted({n for p in all_profiles for n in p}):
        having = [p[name] for p in all_profiles if name in p]
        kept = {}
        for k in sorted({k for h in having for k in h}):
            if k == "package":
                over = {}
                for pkg in sorted({q for h in having for q in h.get("package", {})}):
                    sets = [
                        h["package"][pkg] for h in having if pkg in h.get("package", {})
                    ]
                    if pkg == "*" and len(sets) < len(having):
                        dropped.append(f"{name}.package.*")
                        continue
                    joined = {s: sets[0][s] for s in sorted({s for x in sets for s in x})
                              if all(x.get(s, object()) == sets[0].get(s, object()) for x in sets)}  # fmt: skip
                    dropped += [
                        f"{name}.package.{pkg}.{s}"
                        for s in sorted({s for x in sets for s in x} - set(joined))
                    ]
                    if joined:
                        over[pkg] = joined
                if over:
                    kept["package"] = over
            elif all(k in h and h[k] == having[0].get(k) for h in having):
                kept[k] = having[0][k]
            else:
                dropped.append(f"{name}.{k}")
        if kept:
            out[name] = kept
    return out


def path_deps(doc: dict, ws: dict, member: str) -> list[str]:
    """The member folders (in its own source) `doc` depends on by path."""
    out = []
    tables = [doc.get(t, {}) for t in DEP_TABLES]
    tables += [v.get(t, {}) for v in doc.get("target", {}).values() for t in DEP_TABLES]
    for table in tables:
        for name, spec in table.items():
            if isinstance(spec, dict) and spec.get("workspace") is True:
                base = ws.get("dependencies", {}).get(name)
                if isinstance(base, dict) and "path" in base:
                    out.append(posixpath.normpath(base["path"]))
            elif isinstance(spec, dict) and "path" in spec:
                out.append(posixpath.normpath(posixpath.join(member, spec["path"])))
    return out


def lib_folder(store: Path, rows: dict, pkg: str) -> str:
    """The folder of package `pkg` in one source, "." when it is the root."""
    for path in sorted(rows):
        if posixpath.basename(path) == "Cargo.toml":
            doc = tomllib.loads(pieces.get(store, rows[path][1]).decode("utf-8"))
            if doc.get("package", {}).get("name") == pkg:
                return posixpath.dirname(path) or "."
    raise Stop(f"no package {pkg} in that source")


def package_at(store: Path, rows: dict, folder: str) -> str:
    path = "Cargo.toml" if folder in ("", ".") else f"{folder}/Cargo.toml"
    if path not in rows:
        raise Stop(f"a path dependency on {folder}, which holds no Cargo.toml")
    return tomllib.loads(pieces.get(store, rows[path][1]).decode("utf-8"))["package"][
        "name"
    ]


def locked(store: Path, rows: dict, url: str, pkg: str) -> str:
    """The commit a source's own Cargo.lock holds for `pkg` from `url`."""
    if "Cargo.lock" not in rows:
        return ""
    lock = tomllib.loads(pieces.get(store, rows["Cargo.lock"][1]).decode("utf-8"))
    for entry in lock.get("package", []):
        source = entry.get("source", "")
        if entry.get("name") == pkg and source.startswith("git+") and "#" in source:
            if (
                source[4:].split("?")[0].split("#")[0].rstrip("/").removesuffix(".git")
                == url
            ):
                return source.rsplit("#", 1)[1]
    return ""


# ── rule 6: resolving ───────────────────────────────────────────────────────
LINKS = re.compile(
    r"failed to select a version for `([^`]+)`.*?links to the native library `([^`]+)`",
    re.S,
)


def resolve(to: Path, order: list[str], cargo) -> dict:
    """Rule 6. `cargo(argv, cwd)` runs Cargo and gives (ok, stderr). Returns
    what was left out, and whether a lockfile was made."""
    glue = json.loads((to / "GLUE.json").read_text(encoding="utf-8"))
    for _ in range(64):
        ok, err = cargo(["generate-lockfile"], to)
        if ok:
            glue["resolved"] = True
            break
        m = LINKS.search(err)
        if not m:
            glue["resolved"], glue["unresolved"] = False, err.strip().splitlines()[-1:]
            break
        crate, native = m.groups()
        root = tomllib.loads((to / "Cargo.toml").read_text(encoding="utf-8"))
        users: dict[str, set[str]] = {}
        for mem in root["workspace"]["members"]:
            for req in wants(
                tomllib.loads((to / mem / "Cargo.toml").read_text(encoding="utf-8")),
                crate,
            ):
                users.setdefault(req, set()).add(mem)
        if len(users) < 2:
            glue["resolved"], glue["unresolved"] = (
                False,
                [f"{crate} links {native}, but no two member groups ask for it"],
            )
            break

        def apps_of(req: str) -> list[str]:
            return sorted({m.split("/")[0] for m in users[req]})

        side = min(
            users,
            key=lambda r: (
                len(apps_of(r)),
                -max(order.index(a) for a in apps_of(r)),
                r,
            ),
        )
        others = sorted(r for r in users if r != side)
        out = set(users[side])
        grew = True
        while grew:  # and every member that depends on one left out
            grew = False
            for mem in root["workspace"]["members"]:
                doc = tomllib.loads(
                    (to / mem / "Cargo.toml").read_text(encoding="utf-8")
                )
                if mem not in out and set(path_deps(doc, {}, mem)) & out:
                    out.add(mem)
                    glue["left_out"].append(
                        {
                            "member": mem,
                            "why": f"it depends on a member left out for {native}",
                        }
                    )
                    grew = True
        for mem in sorted(users[side]):
            glue["left_out"].append({"member": mem, "why": f"it asks for {crate} {side}, which links {native}, "
                                                               f"as {crate} {' and '.join(others)} does in more apps"})  # fmt: skip
        root["workspace"]["members"] = sorted(set(root["workspace"]["members"]) - out)
        root["workspace"]["exclude"] = sorted(set(root["workspace"]["exclude"]) | out)
        write_text(to / "Cargo.toml", toml(root))
    else:
        glue["resolved"] = False
    glue["members"] = len(
        tomllib.loads((to / "Cargo.toml").read_text(encoding="utf-8"))["workspace"][
            "members"
        ]
    )
    glue["left_out"].sort(key=lambda g: g["member"])
    write_text(to / "GLUE.json", pieces.dump(glue))
    return glue


def wants(doc: dict, crate: str) -> list[str]:
    """The versions of `crate` a manifest asks for, in any dependency table."""
    tables = [doc.get(t, {}) for t in DEP_TABLES]
    tables += [v.get(t, {}) for v in doc.get("target", {}).values() for t in DEP_TABLES]
    out = []
    for table in tables:
        for name, spec in table.items():
            if (spec.get("package", name) if isinstance(spec, dict) else name) == crate:
                out.append(spec if isinstance(spec, str) else spec.get("version", "*"))
    return sorted(set(out))


def write_text(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    os.chmod(p, 0o644)


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv)
    for a in it:
        v = next(it, "")
        if a not in ("--store", "--recipe", "--to") or not v or a in opts:
            print(__doc__.split("\n\n")[1], file=sys.stderr)
            return 2
        opts[a] = v
    if len(opts) != 3:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    store, to = Path(opts["--store"]), Path(opts["--to"])
    if to.exists() and any(to.iterdir()):
        print(f"refused: {to} isn't empty; compose into a new folder", file=sys.stderr)
        return 2
    try:
        glue = compose(
            store, json.loads(Path(opts["--recipe"]).read_text(encoding="utf-8")), to
        )
    except Stop as e:
        print(f"stopped: {e}", file=sys.stderr)
        return 2
    print(f"composed {glue['members']} members, {len(glue['git'])} crates by git, "
          f"{len(glue['left_out'])} left out, {len(glue['rewritten'])} manifests rewritten")  # fmt: skip
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
