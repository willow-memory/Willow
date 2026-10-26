"""The study's tools read Cargo's TOML with tomllib, Python 3.11's. On 3.9
and 3.10, which CI's tests also run, the same parser is pip's own copy of
tomli, the library tomllib was made from, so the tests run there whole."""

import sys

try:
    import tomllib  # noqa: F401
except ModuleNotFoundError:
    from pip._vendor import tomli

    sys.modules["tomllib"] = tomli
