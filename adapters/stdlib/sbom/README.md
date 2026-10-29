<!-- willow-addon
section: Reading more kinds of files
line: SBOMs in SPDX or CycloneDX JSON: each component, its version and licence, as passages.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, file-reader
-->
# sbom

Your software bills of materials, searchable by component, version and licence.

    python adapters/stdlib/sbom/sbom.py mirror --from FOLDER --to MIRROR

Each bill is written as a heading and a line for each component, in name order:

    sbom: garden-app 1.0 (CycloneDX 1.5)
    requests 2.31.0: Apache-2.0 (pkg:pypi/requests@2.31.0)
    legacy-lib: no licence stated

A CycloneDX licence is its id, its name or its expression; an SPDX package's is
the concluded licence, else the declared one, and NOASSERTION or NONE counts as
none stated. The package URL is kept when the component gives one (for SPDX, its
`purl` external reference). Hashes, dependency graphs and vulnerabilities are not
copied. Only JSON that is a CycloneDX or SPDX bill is read; other JSON is skipped
and counted.

Each file is written to MIRROR at the same relative path with .txt added.
FOLDER is only read: hidden folders and files are skipped, and nothing is
written inside it. A file that can't be read is skipped and counted, never a
crash:

    wrote 2 files to MIRROR; skipped 1

Point the kernel at MIRROR to ask questions of it: `kernel.py init --pile MIRROR`.

**Exit codes:** 0 wrote some; 42 nothing readable; 2 refused (FOLDER is not a
folder, or MIRROR and FOLDER are inside one another).

**Uses:** the kernel's exit codes (`ALIVE`, `ESCALATE`, `REFUSED`); Python's
standard library for the format.

**Never:** writes inside FOLDER, modifies an original, writes anything outside
MIRROR, or goes online.
