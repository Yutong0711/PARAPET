Command (repository root, at the final commit):

```bash
PYTHON=~/parapet-work/venv/bin/python ./scripts/run_tests.sh
```

Result (2026-11-18 18:37 PST): **445 passed, 0 failed, 0 skipped**:
component functional and Python runtime smoke tests 242 passed; Java/JVM
end-to-end tests 8 passed; repository and website structural checks 195
passed. ("Deselected" counts are the `jvm` marker split between suites, not
skips.) `tests/parapet/test_prompt_and_generator.py::test_library_case_prompt_reads_only_the_target_file`
ran here because the L1 jars are present; on a runner without them (CI) it
skips by design. At LOCAL-EVIDENCE the same command gave 444 passed, 0
failed, 0 skipped. Raw output: `logs/run_tests_final.log`,
`logs/run_tests_local_evidence.log`.

```text
=== Component functional and Python runtime smoke tests ===
$ /home/yzhao/parapet-work/venv/bin/python -m pytest tests/perforch tests/more_than_just_functional tests/parapet -m not jvm
====================== 242 passed, 8 deselected in 3.97s =======================
=== Java/JVM end-to-end smoke tests ===
$ /home/yzhao/parapet-work/venv/bin/python -m pytest tests/perforch tests/parapet -m jvm
====================== 8 passed, 218 deselected in 25.37s ======================
=== Repository and website structural checks ===
$ /home/yzhao/parapet-work/venv/bin/python -m pytest tests/repository tests/website
============================= 195 passed in 2.34s ==============================
All selected PARAPET checks passed.
```
