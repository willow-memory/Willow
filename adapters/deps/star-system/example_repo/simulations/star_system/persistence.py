"""The stand-in's names for itself, and its digest of a setup.

The real project names its model, its numerical method and each setup in
`persistence.py`; the adapter reads those names off the checkout it runs.
This gives the stand-in the same three, so the adapter's document says the
stand-in's method, not the real project's. The digest here is a plain
SHA-256 of the setup's numbers; the real one is over its whole saved
document.
"""

import hashlib
import json

MODEL_VERSION = "planar-newtonian-point-mass-v1"
NUMERICAL_VERSION = "fixed-velocity-verlet-stand-in"


def setup_digest(setup):
    """SHA-256 over the stand-in setup's bodies, start and step, and its names."""
    named = {
        "model": MODEL_VERSION,
        "numerical": NUMERICAL_VERSION,
        "bodies": list(setup.bodies),
        "masses": setup.masses.tolist(),
        "r": setup.r.tolist(),
        "v": setup.v.tolist(),
        "dt": setup.dt,
    }
    encoded = json.dumps(named, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()
