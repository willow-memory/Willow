"""A minimal stand-in integrator for the star-system adapter's offline tests.

This is NOT science_bitch's integrator. It is a plain textbook velocity-Verlet
(second order), there only to give the adapter the `make_system`/`period`/
`System` interface it drives, so the deps gate can run without a checkout of
the real project. The real project uses a fourth-order Yoshida composition;
point `--repo` at a real science_bitch checkout to run it.

The Newtonian equations, the unit conversions and the circular initial
conditions are standard orbital mechanics (and are spelled out in the
project's own README); only the interface is matched here.
"""

from dataclasses import dataclass

import numpy as np

from .data import PLANETS, STARS

# G in AU^3 / (solar mass * year^2), from SI constants.
G = 6.67430e-11 * 1.98847e30 * (365.25 * 86400) ** 2 / (149597870700.0) ** 3
SOLAR_RADIUS_AU = 695700 / 149597870.7
_ENCOUNTER = 0.05  # AU; below this the stand-in halts, as the real guard would


def kepler_period(semi_major: float, mu: float) -> float:
    return float(2.0 * np.pi * np.sqrt(semi_major**3 / mu))


def period(star, planet, distance):
    return kepler_period(distance, G * (STARS[star].mass + PLANETS[planet].mass))


@dataclass
class System:
    masses: np.ndarray
    r: np.ndarray
    v: np.ndarray
    dt: float
    time: float = 0.0

    def accelerations(self):
        delta = self.r[None, :, :] - self.r[:, None, :]
        d2 = np.sum(delta**2, axis=-1)
        np.fill_diagonal(d2, np.inf)
        return G * np.sum(delta * (self.masses[None, :] / d2**1.5)[:, :, None], axis=1)

    def step(self, count=1):
        for _ in range(count):
            delta = self.r[None, :, :] - self.r[:, None, :]
            dist = np.linalg.norm(delta, axis=-1)
            np.fill_diagonal(dist, np.inf)
            if np.min(dist) < _ENCOUNTER:
                raise ValueError("Close encounter unresolved: widen the orbits.")
            a = self.accelerations()
            self.r += self.v * self.dt + 0.5 * a * self.dt**2
            self.v += 0.5 * (a + self.accelerations()) * self.dt
            self.time += self.dt

    def invariants(self):
        energy = 0.5 * np.sum(self.masses[:, None] * self.v**2)
        for i in range(len(self.masses)):
            for j in range(i):
                energy -= (
                    G
                    * self.masses[i]
                    * self.masses[j]
                    / np.linalg.norm(self.r[i] - self.r[j])
                )
        momentum = np.sum(self.masses[:, None] * self.v, axis=0)
        angular = np.sum(
            self.masses * (self.r[:, 0] * self.v[:, 1] - self.r[:, 1] * self.v[:, 0])
        )
        return energy, momentum, angular


def make_system(star="sun", planets=("earth", "jupiter"), distances=None):
    if not planets or len(set(planets)) != len(planets):
        raise ValueError("Choose at least one planet, without duplicates.")
    distances = np.array(
        distances if distances is not None else [PLANETS[p].distance for p in planets],
        dtype=float,
    )
    if (
        len(distances) != len(planets)
        or not np.all(np.isfinite(distances))
        or np.any(distances <= STARS[star].radius * SOLAR_RADIUS_AU)
    ):
        raise ValueError("Orbital distances must be finite and outside the star.")
    masses = np.array([STARS[star].mass] + [PLANETS[p].mass for p in planets])
    angles = np.arange(len(planets)) * 2.3999632297
    radial = np.column_stack((np.cos(angles), np.sin(angles)))
    r = np.vstack(([0.0, 0.0], distances[:, None] * radial))
    speeds = np.sqrt(G * (masses[0] + masses[1:]) / distances)
    v = np.vstack(([0.0, 0.0], speeds[:, None] * radial[:, ::-1] * [-1, 1]))
    r -= np.average(r, axis=0, weights=masses)
    v -= np.average(v, axis=0, weights=masses)
    dt = min(period(star, p, a) for p, a in zip(planets, distances)) / 600
    return System(masses, r, v, dt)
