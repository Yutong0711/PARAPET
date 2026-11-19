# Hardening record — L1 / CONTROL

- **Weakness:** CWE-611 Improper Restriction of XML External Entity Reference
- **Case:** java-xmlbuilder 1.1+ (pinned 5d5caa5) parses documents with external entities enabled
- **Patch:** `CONTROL` (incomplete control patch (hand-written)), source sha256 `17f6bb4f41d12a6ded6e51f4c565bc90d11e5f53c3d17f88c9a9796d12fde9af`
- **Mechanism route:** none (incomplete by design) — regex denylist for the reproducer's shape (<!ENTITY name SYSTEM ...) on character-stream input only
- **Claim level:** L3 (admissible: False)
- **Generator:** hand-written control
- **Repository commit:** `2ac56563e219ecf72c31ee33d8c4dd262d97d0f5` (branch `mozilla/local-slice`)

## Checks

| Check | Passed | Summary | Command |
| --- | --- | --- | --- |
| compile | yes | compiles | `javac --release 17 -encoding UTF-8 -d /home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/classes/target -cp /home/yzhao/parapet-work/jars/base64-2.3.8.jar /home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/src/com/jamesmurty/utils/BaseXMLBuilder.java /home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/src/com/jamesmurty/utils/NamespaceContextImpl.java /home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/src/com/jamesmurty/utils/XMLBuilder.java /home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/src/com/jamesmurty/utils/XMLBuilder2.java /home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/src/com/jamesmurty/utils/XMLBuilderRuntimeException.java` |
| reproducer | yes | canary did not fire; input rejected | `java -cp /home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/classes/harness:/home/yzhao/parapet-work/jars/base64-2.3.8.jar:/home/yzhao/parapet-work/jars/junit-4.11.jar:/home/yzhao/parapet-work/jars/hamcrest-core-1.3.jar harness.l1.Reproducer` |
| heldout1 | NO | canary fired (parsed document) | `java -cp /home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/classes/harness:/home/yzhao/parapet-work/jars/base64-2.3.8.jar:/home/yzhao/parapet-work/jars/junit-4.11.jar:/home/yzhao/parapet-work/jars/hamcrest-core-1.3.jar harness.l1.HeldOut1` |
| heldout2 | NO | canary fired (parsed document) | `java -cp /home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/classes/harness:/home/yzhao/parapet-work/jars/base64-2.3.8.jar:/home/yzhao/parapet-work/jars/junit-4.11.jar:/home/yzhao/parapet-work/jars/hamcrest-core-1.3.jar harness.l1.HeldOut2` |
| functional | yes | 34/34 functional tests pass | `java -cp /home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/classes/harness:/home/yzhao/parapet-work/jars/base64-2.3.8.jar:/home/yzhao/parapet-work/jars/junit-4.11.jar:/home/yzhao/parapet-work/jars/hamcrest-core-1.3.jar harness.l1.FunctionalTests` |
| probes | yes | probes evaluated (informational) | `java -cp /home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019/patches/CONTROL/classes/harness:/home/yzhao/parapet-work/jars/base64-2.3.8.jar:/home/yzhao/parapet-work/jars/junit-4.11.jar:/home/yzhao/parapet-work/jars/hamcrest-core-1.3.jar harness.l1.Probes` |

## Inputs the original accepted that this patch now rejects

- none

## Cost on the workload

- Latency overhead vs unpatched baseline: not measured
- Peak-memory overhead vs unpatched baseline: not measured
- A/A noise floor: latency 2.93%, peak memory 6.22%

## Budget decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}, budget sha256 `208491b8306db37d…`): does not fit — not assessed. Recommended patch under this budget: `None`.
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}, budget sha256 `fdada931cc9381c8…`): does not fit — not assessed. Recommended patch under this budget: `R2`.

## Diff

```diff
--- a/com/jamesmurty/utils/BaseXMLBuilder.java
+++ b/com/jamesmurty/utils/BaseXMLBuilder.java
@@ -160,6 +160,20 @@
     protected static Document parseDocumentImpl(InputSource inputSource)
         throws ParserConfigurationException, SAXException, IOException
     {
+        // INCOMPLETE CONTROL PATCH: blocks only the reported payload shape,
+        // an internal-subset entity declared with a SYSTEM identifier.
+        if (inputSource.getCharacterStream() != null) {
+            StringBuilder text = new StringBuilder();
+            char[] buf = new char[4096];
+            int n;
+            while ((n = inputSource.getCharacterStream().read(buf)) != -1) {
+                text.append(buf, 0, n);
+            }
+            if (java.util.regex.Pattern.compile("<!ENTITY\\s+\\S+\\s+SYSTEM").matcher(text).find()) {
+                throw new SAXException("external entities are not allowed");
+            }
+            inputSource = new InputSource(new java.io.StringReader(text.toString()));
+        }
         DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
         factory.setNamespaceAware(isNamespaceAware);
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
python -m parapet run --case L1 --budget parapet/budgets/strict.parapet.budget.yaml --budget parapet/budgets/lenient.parapet.budget.yaml --no-generator
```
