## A. Environment, default generator, installs

| Item | Value |
| --- | --- |
| OS | Ubuntu 26.04 LTS on WSL2, kernel 6.6.114.1-microsoft-standard-WSL2 |
| CPU | Intel Core i9-14900KF, 32 logical CPUs visible to WSL; forks pinned with `taskset -c 2-5` |
| RAM | 31.2 GiB visible to WSL |
| GPU | NVIDIA GeForce RTX 4090, 24,564 MiB, driver 610.60 (nvidia-smi 610.47.03, CUDA UMD 13.3) |
| JDK | OpenJDK 21.0.13.0.3 (Ubuntu build 21.0.13.0.3+1-1-26.04.1); all Java compiled with `javac --release 17` |
| Python | 3.14.4 (venv under `~/parapet-work/venv`: numpy 2.5.5, openai 2.54.0, PyYAML 6.0.3, pytest 8.4.2) |
| Model server | Ollama 0.40.16, user process on `127.0.0.1:11434` (loopback only), `OLLAMA_CONTEXT_LENGTH=8192`, `OLLAMA_NO_CLOUD=1` from the first model run on (D2) |
| Work directory | compile and measure under `~/parapet-work/runs` (ext4, Linux filesystem); results copied into this directory (see D8 for the JVM working directory) |

**Default generator.** Qwen2.5-Coder-7B-Instruct.

| Property | Value | Source |
| --- | --- | --- |
| Ollama tag | `qwen2.5-coder:7b-instruct-q4_K_M` | `parapet/settings/generation.yaml` |
| Manifest digest | `sha256:dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364` | `step3/C1/generation/model.json` (Ollama `/api/tags`) |
| Weights blob (GGUF) | `sha256:60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463`, 4,683,074,048 bytes; hash re-computed locally and matches | Ollama manifest; `sha256sum` |
| Parameter count | 7,615,616,512 (GGUF `general.parameter_count`); model card: "Number of Parameters: 7.61B" | `model.json`; https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct |
| License | Apache-2.0 (model card `license: apache-2.0`; GGUF `general.license`; Ollama license layer is the Apache License 2.0 text) | same |
| Quantization | Q4_K_M (GGUF `file_type` 15), as distributed by Ollama | `model.json` |
| Context | 32,768 trained (GGUF metadata); served with 8,192 | `model.json`; server log |

Generation settings (pre-registered): k = 5, temperature 0.7, top_p 0.95,
seeds 101–105, max_tokens 4096, request timeout 600 s, no retries. Prompt
template `parapet/prompts/harden_v1.txt` (sha256
`d5b3c33c4650e1a53437ad477bd4031896f35b4b33193efb946968f8ed90edbc`); prompt
sha256 C1 `ca4de091367f148432505594779160045f56343829121931948f4c2bf83c07ea`,
C2 `48823d42342e244db8b00af2bff2c0b45a45f62f67066165c71ce0824710bed9`. The
prompt contains the vulnerable source file and the weakness class only
(checked by `tests/parapet/test_prompt_and_generator.py`).

Installs and every network endpoint used for installs and citation checks:
`evidence/INSTALLS.md`. Hugging Face model card fetched once
(`https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct/raw/main/README.md`,
2026-11-18 17:14:33 PST) for the parameter count and license.

## B. Workflow without a generator (hand-written patches only)

Budgets: strict = 5% latency / 5% peak memory, lenient = 25% / 25%
(`parapet/budgets/`, sha256 `208491b8306d…` and `fdada931cc93…`). A patch fits
only if the upper end of each 95% interval is at or below the cap. "≈ noise"
marks a point estimate smaller in magnitude than that session's A/A noise
floor (indistinguishable).

### B.1 C1 — CWE-502 (validation, v1 Step 2 session; v2 identical)

{{validation:step2/C1}}

### B.2 C2 — CWE-611 (validation, v1 Step 2 session; v2 identical)

{{validation:step2/C2}}

In both cases the unpatched source fails the checks (all three canaries
fire), R1 and R2 are admissible, and the incomplete control patch blocks the
reproducer but is rejected by both held-out variants.

### B.3 Cost of R1 and R2, A/A noise floor, and decisions — every session

Each session: 20 forked JVMs per arm, arms interleaved, 10 warm-up rounds
discarded, 20 measured rounds. Ratio of medians against that session's
unpatched baseline, 95% percentile bootstrap (10,000 resamples). v1 peak-memory
columns are invalid (D6) and shown only for completeness.

C1 (CWE-502):

{{cross:C1}}

C2 (CWE-611):

{{cross:C2}}

Primary Step 2 tables (v2 session, valid memory):

C1:

{{measurement:step2-v2/C1}}

{{decisions:step2-v2/C1}}

C2:

{{measurement:step2-v2/C2}}

{{decisions:step2-v2/C2}}

What the hand-written patches show:

- C1: R1 (serialization filter) adds a small latency cost in every session;
  R2 (data-only format) is faster than the baseline in every session. Both fit
  both budgets in every session; the rule recommends R2 because its latency
  upper bound is lowest. R2 rejects every token written by the original
  implementation (6/6 probes); R1 rejects one legacy token shape (1/6). The
  decision rule does not weigh rejected inputs; the records list them for the
  maintainer.
- C2: R1 (reject DOCTYPE) costs about 10% latency in every session and never
  fits the strict budget; it fits the lenient one. R2 (entity resolver) is
  within the noise floor in every session, and fits the strict budget in three
  of four sessions. In the v2 Step 2 session its latency upper bound is
  5.08% against a 5.0% cap, so in that session nothing fits the strict budget.
  The strict verdict for a patch whose cost sits inside the noise is therefore
  not stable from session to session.

## C. Workflow with the default local generator

Each case was run end to end once (v1, 2026-11-18 17:15–17:26 PST); the saved
candidates were re-validated and re-measured once more without a model call
(v2). Raw outputs are saved verbatim in `step3/<case>/generation/raw/`.

### C.1 Claim levels (per case; levels are not merged)

{{claims:step3-v2/C1}}

{{claims:step3-v2/C2}}

### C.2 Time and tokens per candidate (GPU, v1 generation run)

C1:

{{generation:step3/C1}}

C2:

{{generation:step3/C2}}

C1's G1 time includes loading the model into GPU memory (first request of the
server session). For C2, seeds 102 and 105 returned byte-identical outputs,
as did seeds 103 and 104, so the five samples contain three distinct outputs.

C1 failures, as observed (no candidate was edited):

- G1: the code block is byte-identical to the original file; it compiles and
  all three canaries fire (L2).
- G2: adds a `resolveClass` override but does not import
  `InvalidClassException` or `ObjectStreamClass`; does not compile (L1).
- G3, G4: move the cast into a type check applied to the object `readObject`
  returns, and drop the `java.util.Base64` import; do not compile (L1).
- G5: builds a custom class around `ObjectInputFilter`; unresolved
  `ObjectInputFilter`, `FilterInfo`, `Status` and an incompatible-type error;
  does not compile (L1).

C2: all five candidates set `disallow-doctype-decl` plus the three external
entity/DTD features, `setXIncludeAware(false)` and
`setExpandEntityReferences(false)`; all are admissible (L4) and reject the
same four DTD probes as R1.

### C.3 Cost of admissible candidates (C2) and model-induced cost

The matched reference is assigned by the pre-registered rule in
`parapet/cases/C2/case.yaml` (all five set `disallow-doctype-decl` → R1).
Model-induced cost = candidate against R1, measured in the same session.

v2 (valid memory):

{{model_induced:step3-v2/C2}}

v1 (latency valid, memory invalid):

{{model_induced:step3/C2}}

### C.4 Budget decisions over all admissible patches

C1 (no admissible candidate; the set is R1 and R2), v2:

{{decisions:step3-v2/C1}}

C2 (R1, R2, G1–G5), v2:

{{decisions:step3-v2/C2}}

C2, v1:

{{decisions:step3/C2}}

### C.5 CPU-only generation time (C2, GPU hidden; D5)

{{cpu_only:step3/cpu-only-C2}}

The CPU outputs for seeds 102–105 are byte-identical to the GPU outputs for
the same seeds; seed 101 differs (596 vs 595 completion tokens). These five
outputs were not validated or measured.

### C.6 Endpoint log (model calls)

C1:

{{endpoints:step3/C1}}

C2:

{{endpoints:step3/C2}}

CPU-only run (second local server, port 11435):

{{endpoints:step3/cpu-only-C2}}

v2 runs made no model request. A connection monitor (`ss`, every 2 s,
17:15:39–17:34:33 PST, `logs/ollama_connections_step3.log`) saw only
loopback-to-loopback connections for the Ollama processes. Sampling every 2 s
cannot rule out a shorter-lived connection.

### C.7 GPU board power during generation (Step 6; run concurrently, D3)

C1:

{{power:step3/C1}}

C2:

{{power:step3/C2}}

Whole-board power from `nvidia-smi` every 200 ms; includes anything else
using the GPU (the Windows desktop). Not a per-request energy measurement.

