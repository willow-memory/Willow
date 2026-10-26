"""A tiny stand-in catalog for the star-system adapter's offline tests.

This is NOT science_bitch's catalog: it is a minimal, clearly distinct set of
bodies that gives the adapter the `STARS`/`PLANETS` interface it reads, so the
deps gate can run without a checkout of the real project. Point `--repo` at a
real science_bitch checkout to run the actual simulation and catalog.
"""

from dataclasses import dataclass

SOLAR_KG = 1.98847e30


@dataclass(frozen=True)
class Star:
    name: str
    mass: float  # solar masses
    radius: float  # solar radii
    temperature: float  # K


STARS = {
    "sun": Star("Sun", 1.0, 1.0, 5772),
    "proxima": Star("Proxima Centauri", 0.120, 0.141, 3050),
}


@dataclass(frozen=True)
class Planet:
    name: str
    mass: float  # solar masses
    radius: float  # km
    distance: float  # AU


# (name, mass in 10^24 kg, radius km, distance AU). "inner" is a deliberately
# close orbit, there only to exercise the close-encounter path.
_ROWS = [
    ("Earth", 5.97, 6371, 1.0),
    ("Jupiter", 1898, 69911, 5.204),
    ("Neptune", 102, 24622, 30.178),
    ("Inner", 0.330, 2439.7, 0.03),
]
PLANETS = {n.lower(): Planet(n, m * 1e24 / SOLAR_KG, r, a) for n, m, r, a in _ROWS}
