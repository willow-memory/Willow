`llm-cli`, `manifests`: off the pins with known advisories. llm's pin is
0.37.1 and its floor 0.28 (llm up to 0.27.1 has PYSEC-2026-400, code run by
`--functions`, which willow never passes); PyYAML's floor is 6.0.1
(PYSEC-2021-142; 5.4 to 6.0 don't build on Python 3.13)
