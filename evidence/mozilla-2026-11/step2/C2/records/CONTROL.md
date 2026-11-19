# Hardening record — C2 / CONTROL

- **Weakness:** CWE-611 Improper Restriction of XML External Entity Reference
- **Case:** Tenant configuration documents parsed with a default DOM parser
- **Patch:** `CONTROL` (incomplete control patch (hand-written)), source sha256 `de6ab9a327835f726e8e0cd0fa699499c2d0a1951720b23a9aab6f6310e2d0c0`
- **Mechanism route:** none (incomplete by design) — regex denylist for the reproducer's shape (<!ENTITY name SYSTEM ...) only
- **Claim level:** L3 (admissible: False)
- **Generator:** hand-written control
- **Repository commit:** `08900879fc58faef8b286e802179fef4522f831b` (branch `mozilla/local-slice`)

## Checks

| Check | Passed | Summary | Command |
| --- | --- | --- | --- |
| compile | yes | compiles | `javac --release 17 -encoding UTF-8 -d /home/yzhao/parapet-work/runs/step2-C2-20261118T171144/patches/CONTROL/classes/target /home/yzhao/parapet-work/runs/step2-C2-20261118T171144/patches/CONTROL/src/example/config/ConfigLoader.java` |
| reproducer | yes | canary did not fire; input rejected | `java -cp /home/yzhao/parapet-work/runs/step2-C2-20261118T171144/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step2-C2-20261118T171144/patches/CONTROL/classes/harness harness.c2.Reproducer` |
| heldout1 | NO | canary fired (result:config.name) | `java -cp /home/yzhao/parapet-work/runs/step2-C2-20261118T171144/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step2-C2-20261118T171144/patches/CONTROL/classes/harness harness.c2.HeldOut1` |
| heldout2 | NO | canary fired (result:config.name) | `java -cp /home/yzhao/parapet-work/runs/step2-C2-20261118T171144/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step2-C2-20261118T171144/patches/CONTROL/classes/harness harness.c2.HeldOut2` |
| functional | yes | 11/11 functional tests pass | `java -cp /home/yzhao/parapet-work/runs/step2-C2-20261118T171144/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step2-C2-20261118T171144/patches/CONTROL/classes/harness harness.c2.FunctionalTests` |
| probes | yes | probes evaluated (informational) | `java -cp /home/yzhao/parapet-work/runs/step2-C2-20261118T171144/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step2-C2-20261118T171144/patches/CONTROL/classes/harness harness.c2.Probes` |

## Inputs the original accepted that this patch now rejects

- none

## Cost on the workload

- Latency overhead vs unpatched baseline: not measured
- Peak-memory overhead vs unpatched baseline: not measured
- A/A noise floor: latency 4.93%, peak memory 3.65%

## Budget decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}, budget sha256 `208491b8306db37d…`): does not fit — not assessed. Recommended patch under this budget: `R2`.
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}, budget sha256 `fdada931cc9381c8…`): does not fit — not assessed. Recommended patch under this budget: `R2`.

## Diff

```diff
--- a/example/config/ConfigLoader.java
+++ b/example/config/ConfigLoader.java
@@ -4,6 +4,7 @@
 import java.io.StringReader;
 import java.util.LinkedHashMap;
 import java.util.Map;
+import java.util.regex.Pattern;
 import javax.xml.parsers.DocumentBuilder;
 import javax.xml.parsers.DocumentBuilderFactory;
 import javax.xml.parsers.ParserConfigurationException;
@@ -24,11 +25,18 @@
  */
 public final class ConfigLoader {
 
+    // INCOMPLETE CONTROL PATCH: blocks only the reported payload shape,
+    // an internal-subset entity declared with a SYSTEM identifier.
+    private static final Pattern SYSTEM_ENTITY = Pattern.compile("<!ENTITY\\s+\\S+\\s+SYSTEM");
+
     private ConfigLoader() {
     }
 
     /** Parses a configuration document. */
     public static Map<String, String> load(String xml) throws IOException {
+        if (SYSTEM_ENTITY.matcher(xml).find()) {
+            throw new IOException("external entities are not allowed");
+        }
         try {
             DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
             DocumentBuilder builder = factory.newDocumentBuilder();
```

## Environment

- os: Ubuntu 26.04 LTS
- kernel: 6.6.114.1-microsoft-standard-WSL2
- cpu: Intel(R) Core(TM) i9-14900KF
- logical_cpus: 32
- ram_gib: 31.2
- gpu: NVIDIA GeForce RTX 4090, 24564 MiB, 610.60
- jdk: openjdk version "21.0.13.0.3" 2026-10-24
- python: 3.14.4

## Reproduce

```bash
python -m parapet run --case C2 --budget parapet/budgets/strict.parapet.budget.yaml --budget parapet/budgets/lenient.parapet.budget.yaml --no-generator
```
