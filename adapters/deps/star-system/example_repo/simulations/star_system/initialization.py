"""The stand-in's setup: the start `make_system` builds, kept so it can be named.

The real project keeps a full initial setup (bodies, sources, a population)
and builds its system from that. The adapter needs two things of it:
`legacy_setup`, the setup for a star and its planets, and `build_system`,
the system that setup builds. Only that interface is matched here.
"""

from dataclasses import dataclass

import numpy as np

from .core import System, make_system


@dataclass(frozen=True)
class Setup:
    bodies: tuple
    masses: np.ndarray
    r: np.ndarray
    v: np.ndarray
    dt: float


@dataclass(frozen=True)
class Prepared:
    system: System


def legacy_setup(star="sun", planets=("earth", "jupiter")):
    system = make_system(star, planets)
    return Setup(
        (star, *planets),
        system.masses.copy(),
        system.r.copy(),
        system.v.copy(),
        system.dt,
    )


def build_system(setup):
    return Prepared(
        System(setup.masses.copy(), setup.r.copy(), setup.v.copy(), setup.dt)
    )
