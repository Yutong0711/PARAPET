# Hardening record — C1 / CONTROL

- **Weakness:** CWE-502 Deserialization of Untrusted Data
- **Case:** Preference tokens restored with Java object serialization
- **Patch:** `CONTROL` (incomplete control patch (hand-written)), source sha256 `07866c87dd51e66ba37a2819385ec7ea7b0ab180e9480874cbf0ae64e848e46c`
- **Mechanism route:** none (incomplete by design) — denylists only the class named in the reported reproducer (GadgetA)
- **Claim level:** L3 (admissible: False)
- **Generator:** hand-written control
- **Repository commit:** `8c8ad50572f6188171600b7899de488b9725ecfc` (branch `mozilla/local-slice`)

## Checks

| Check | Passed | Summary | Command |
| --- | --- | --- | --- |
| compile | yes | compiles | `javac --release 17 -encoding UTF-8 -d /home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/patches/CONTROL/classes/target /home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/patches/CONTROL/src/example/prefs/PrefsCodec.java` |
| reproducer | yes | canary did not fire; input rejected | `java '-Dparapet.fixtures=/mnt/d/2027-Funding/2027 Mozilla Foundation Human-Scale AI Incubator/Mozilla-1117/PARAPET-v1.0/parapet/cases/C1/fixtures' -cp /home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/support-classes:/home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/patches/CONTROL/classes/harness harness.c1.Reproducer` |
| heldout1 | NO | canary fired (GadgetB.hashCode) | `java '-Dparapet.fixtures=/mnt/d/2027-Funding/2027 Mozilla Foundation Human-Scale AI Incubator/Mozilla-1117/PARAPET-v1.0/parapet/cases/C1/fixtures' -cp /home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/support-classes:/home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/patches/CONTROL/classes/harness harness.c1.HeldOut1` |
| heldout2 | NO | canary fired (GadgetC.readResolve) | `java '-Dparapet.fixtures=/mnt/d/2027-Funding/2027 Mozilla Foundation Human-Scale AI Incubator/Mozilla-1117/PARAPET-v1.0/parapet/cases/C1/fixtures' -cp /home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/support-classes:/home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/patches/CONTROL/classes/harness harness.c1.HeldOut2` |
| functional | yes | 11/11 functional tests pass | `java '-Dparapet.fixtures=/mnt/d/2027-Funding/2027 Mozilla Foundation Human-Scale AI Incubator/Mozilla-1117/PARAPET-v1.0/parapet/cases/C1/fixtures' -cp /home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/support-classes:/home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/patches/CONTROL/classes/harness harness.c1.FunctionalTests` |
| probes | yes | probes evaluated (informational) | `java '-Dparapet.fixtures=/mnt/d/2027-Funding/2027 Mozilla Foundation Human-Scale AI Incubator/Mozilla-1117/PARAPET-v1.0/parapet/cases/C1/fixtures' -cp /home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/patches/CONTROL/classes/target:/home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/support-classes:/home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532/patches/CONTROL/classes/harness harness.c1.Probes` |

## Inputs the original accepted that this patch now rejects

- none

## Cost on the workload

- Latency overhead vs unpatched baseline: not measured
- Peak-memory overhead vs unpatched baseline: not measured
- A/A noise floor: latency 3.99%, peak memory 1.75%

## Budget decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}, budget sha256 `208491b8306db37d…`): does not fit — not assessed. Recommended patch under this budget: `R2`.
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}, budget sha256 `fdada931cc9381c8…`): does not fit — not assessed. Recommended patch under this budget: `R2`.

## Diff

```diff
--- a/example/prefs/PrefsCodec.java
+++ b/example/prefs/PrefsCodec.java
@@ -3,7 +3,9 @@
 import java.io.ByteArrayInputStream;
 import java.io.ByteArrayOutputStream;
 import java.io.IOException;
+import java.io.InvalidClassException;
 import java.io.ObjectInputStream;
+import java.io.ObjectStreamClass;
 import java.io.ObjectOutputStream;
 import java.io.Serializable;
 import java.util.ArrayList;
@@ -104,7 +106,16 @@
     /** Restores preferences from a token produced by {@link #encode(UserPrefs)}. */
     public static UserPrefs decode(String token) throws IOException {
         byte[] data = Base64.getDecoder().decode(token);
-        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(data))) {
+        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(data)) {
+            @Override
+            protected Class<?> resolveClass(ObjectStreamClass desc) throws IOException, ClassNotFoundException {
+                // INCOMPLETE CONTROL PATCH: blocks only the class named in the reported reproducer.
+                if ("thirdparty.canary.GadgetA".equals(desc.getName())) {
+                    throw new InvalidClassException(desc.getName(), "blocked class");
+                }
+                return super.resolveClass(desc);
+            }
+        }) {
             return (UserPrefs) in.readObject();
         } catch (ClassNotFoundException e) {
             throw new IOException("unknown class in preferences token", e);
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
python -m parapet run --case C1 --budget parapet/budgets/strict.parapet.budget.yaml --budget parapet/budgets/lenient.parapet.budget.yaml --no-generator
```
