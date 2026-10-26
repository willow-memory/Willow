"""star_system.py: a deterministic star-system simulation, as cited passages.

    pip install -r adapters/deps/star-system/requirements.txt
    python adapters/deps/star-system/star_system.py --repo DIR --to FILE \\
        [--star NAME] [--planet NAME ...] [--orbits N]

An adapter for a friend's project, science_bitch
(https://github.com/AllHailSeizure/science_bitch): it runs that project's own
`star_system` simulation -- full unsoftened Newtonian N-body gravity, a
fixed-step Yoshida fourth-order integrator -- and writes what it computes as a
short markdown document of cited lines a willow box can hold and answer from.
`--repo` is a checkout of science_bitch; its code is imported and run, not
copied here.

It evolves the system for `--orbits` (default 3) orbits of the outermost body
and writes to `--to`: each body's Kepler period and distance, and how well the
run conserves energy, angular momentum and linear momentum -- the same
invariants the project's own tests check, with the tolerances it asserts. The
numbers are the simulation's; the same star, planets and orbit count give the
same bytes every run, because the integrator is fixed-step and deterministic.

It reads the checkout and writes only `--to`; it reads no box, no key, and
reaches no network. Exit codes, the kernel's: 0 the document was written; 42 a
close encounter halted the run (science_bitch's own guard) -- widen the
orbits; 2 refused (a bad command line, a `--repo` that is not a science_bitch
checkout, or an orbit inside a star).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
PROJECT = "https://github.com/AllHailSeizure/science_bitch"


def parse(argv: list[str]) -> dict | None:
    """The command line, or None to refuse. One --repo and --to; a star
    (default sun); planets (default earth, jupiter), no duplicates; orbits a
    positive number (default 3)."""
    opts: dict = {"star": "sun", "planets": [], "orbits": "3"}
    it = iter(argv)
    for a in it:
        if a == "--repo":
            opts["repo"] = next(it, "")
        elif a == "--to":
            opts["to"] = next(it, "")
        elif a == "--star":
            opts["star"] = next(it, "")
        elif a == "--planet":
            opts["planets"].append(next(it, ""))
        elif a == "--orbits":
            opts["orbits"] = next(it, "")
        else:
            return None  # an unknown flag or a stray word
    if not opts.get("repo") or not opts.get("to"):
        return None
    planets = opts["planets"] or ["earth", "jupiter"]
    if "" in planets or len(set(planets)) != len(planets):
        return None
    opts["planets"] = planets
    try:
        opts["orbits"] = float(opts["orbits"])
    except ValueError:
        return None
    if not (opts["orbits"] > 0):
        return None
    return opts


def load(repo: str):
    """science_bitch's own core and catalog, imported from the checkout, or
    None if --repo is not one."""
    sys.path.insert(0, repo)
    try:
        from simulations.star_system import core, data
    except Exception:
        return None
    return core, data


def lines(core, data, star: str, planets: list[str], orbits: float) -> list[str]:
    """The run as cited markdown lines, or a one-line reason this can't run
    (a bad orbit, a close encounter). Raises nothing the caller must map."""
    st = data.STARS[star]
    dist = {p: data.PLANETS[p].distance for p in planets}
    periods = {p: float(core.period(star, p, dist[p])) for p in planets}
    system = core.make_system(star, planets)  # may raise ValueError (bad orbit)
    outer = max(planets, key=lambda p: periods[p])
    span = orbits * periods[outer]
    steps = round(span / system.dt)
    e0, p0, l0 = (float(x) if i != 1 else x for i, x in enumerate(system.invariants()))
    p0 = (p0[0] ** 2 + p0[1] ** 2) ** 0.5
    system.step(steps)  # may raise ValueError (close encounter)
    e1, p1, l1 = (float(x) if i != 1 else x for i, x in enumerate(system.invariants()))
    p1 = (p1[0] ** 2 + p1[1] ** 2) ** 0.5

    body = f"{st.name} ({st.mass:g} solar mass{'' if st.mass == 1 else 'es'})"
    out = [
        f"# star system: {star} with {', '.join(planets)}",
        "",
        f"A deterministic run of the star_system simulation from science_bitch "
        f"({PROJECT}), evolved {orbits:g} orbit"
        f"{'' if orbits == 1 else 's'} of the outermost body ({outer}) with its "
        f"fixed-step Yoshida integrator. Units are AU, solar masses and Julian "
        f"years; the same inputs give the same numbers every run.",
        "",
        "## the system",
        f"- star: {body}",
    ]
    for p in planets:
        pl = data.PLANETS[p]
        out.append(f"- {pl.name} at {dist[p]:g} AU, Kepler period {periods[p]:.6g} yr")
    out += [
        f"- integrator step {system.dt:.6g} yr (shortest period / 600), "
        f"{steps} steps over {span:.6g} yr",
        "",
        f"## conserved over {orbits:g} orbit{'' if orbits == 1 else 's'} of {outer}",
        f"- energy drift |dE/E0| = {abs((e1 - e0) / e0):.3e} "
        f"(science_bitch asserts <= 1e-7)",
        f"- angular momentum drift |dL/L0| = {abs((l1 - l0) / l0):.3e} "
        f"(asserts <= 1e-11)",
        f"- net linear momentum |p| = {p1:.3e} (began {p0:.3e}; barycentric)",
        "",
        "## sources",
        f"- model, integrator and catalog: science_bitch star_system, {PROJECT}",
        "- integrator: Yoshida 1990, doi:10.1016/0375-9601(90)90092-3",
        "- catalog values: NASA NSSDC fact sheets; stars as the project cites",
    ]
    return out


def main(argv: list[str]) -> int:
    opts = parse(argv)
    if opts is None:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    loaded = load(opts["repo"])
    if loaded is None:
        print(f"refused: {opts['repo']} is not a science_bitch checkout "
              f"(no simulations.star_system)", file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    core, data = loaded
    if opts["star"] not in data.STARS:
        print(f"refused: unknown star {opts['star']}", file=sys.stderr)
        return kernel.REFUSED
    for p in opts["planets"]:
        if p not in data.PLANETS:
            print(f"refused: unknown planet {p}", file=sys.stderr)
            return kernel.REFUSED
    to = Path(opts["to"])
    if not to.parent.exists():
        print(f"refused: {to.parent} does not exist; this makes no folder",
              file=sys.stderr)  # fmt: skip
        return kernel.REFUSED
    try:
        page = lines(core, data, opts["star"], opts["planets"], opts["orbits"])
    except ValueError as exc:
        msg = str(exc)
        if "encounter" in msg.lower():
            print(f"halted: {msg}")
            return kernel.ESCALATE
        print(f"refused: {msg}", file=sys.stderr)
        return kernel.REFUSED
    with to.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(page) + "\n")
    print(f"wrote {len(opts['planets']) + 1} bodies to {to}")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
