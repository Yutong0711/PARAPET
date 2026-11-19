# PARAPET local slice — evidence package (mozilla-2026-11)

Branch `mozilla/local-slice`, built on tag `v1.0` (`c6a9566`). This package
shows the four-stage workflow — Generate, Validate, Measure, Decide — run per
weakness on two authored Java cases (C1, CWE-502; C2, CWE-611) and one real
library case (L1, java-xmlbuilder, CWE-611). It is not a comparison of
models. Every table is generated from files in this directory by
`analysis/build_doc.py` (templates in `analysis/`). Sections A–C repeat the
content frozen at LOCAL-EVIDENCE (`LOCAL-EVIDENCE.md`, unchanged).

**Read first.** (1) Peak-memory figures exist in two versions: **v1**, from
the pre-registered runner, is invalid as a JVM measurement because it
included the runner's own memory; **v2** is correct (DEVIATIONS D6/D7). L1
was measured only with the corrected runner. (2) Every change after a
pre-registration commit is in `evidence/DEVIATIONS.md` (P1–P4, D1–D10),
reproduced in full in section G.

Pre-registration commits: `f9f9e15` (C1, C2, budgets, protocol, prompt,
settings; 2026-11-18 17:05:09 PST) and `083b7b8` (L1; 18:12:18 PST).
Generator-free results were committed before the corresponding model runs
(`5eefe0c` before the first model request at 17:15:45; `2ac5656` before the
first L1 model request at 18:16:06; times from the endpoint logs).

