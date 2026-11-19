# Case C1 — CWE-502 Deserialization of Untrusted Data

An authored, self-contained Java case (JDK standard library only). It is a
teaching-sized model of a common pattern, not a real project.

## The weakness

`src/example/prefs/PrefsCodec.java` saves editor preferences as a Base64 token
that is stored in a browser cookie and sent back later. `decode(String)` runs
`ObjectInputStream.readObject()` on whatever bytes arrive. Any serializable
class on the classpath can be instantiated, and its deserialization hooks run
before the cast to `UserPrefs` can fail.

## Harmless canary

`support/thirdparty/canary/` simulates classes from a third-party dependency
that happen to be on the application classpath. Their "side effect" is a
static flag (`Canary.fire`) inside the JVM running the check: no I/O, no
process, no network. "Fires" means attacker-chosen code ran during decoding.

| Check | Payload (built once from the original source by `MakeFixtures`) |
| --- | --- |
| reproducer | `GadgetA` as the whole token (`readObject` side effect) |
| held-out 1 | `GadgetB` as a `HashMap` key (`hashCode` side effect when the map rehashes during `readObject`) |
| held-out 2 | `GadgetC` (`readResolve` side effect) nested inside an otherwise legitimate `UserPrefs.recentFiles` list |

The held-out variants and the harness never appear in the generation prompt.

## Required behavior (functional tests)

`harness/harness/c1/FunctionalTests.java`, 11 tests, public API only:
round trips (typical, empty collections, null theme, Unicode, 500 files,
order preservation, int extremes), the token is Base64 text, decoded
collections are read-only, truncated and non-token input are rejected.
Wire compatibility with tokens written by the original implementation is
**not** required; it is reported separately.

## Inputs now rejected (probes)

`harness/harness/c1/Probes.java` decodes six legitimate tokens written by the
original implementation (typical, empty, large: 2,000 files, Unicode, a
legacy `LinkedList` field, a legacy `HashMap` field) and reports which ones a
patch now rejects or decodes differently. Probes do not gate admissibility.

## Workload (`legitimate-path`)

`harness/harness/c1/Workload.java`: one save/restore round trip
(`encode` then `decode`) of typical preferences per operation, 4,000
operations per round, single thread, single process.

## Hand-written patches (outside `src/`, never read by the prompt builder)

| Patch | Route | Mechanism | Published guidance |
| --- | --- | --- | --- |
| `reference/R1` | added work on the call path | per-stream JEP 290 `ObjectInputFilter`: allowlist of exactly the classes `encode` writes (plus the array component types `ArrayList`/`HashMap` check), graph and byte limits, everything else rejected | OWASP Deserialization Cheat Sheet, Java: "Configure serialization filters with an application-specific class allowlist and resource limits before reading objects." Oracle Secure Coding Guidelines for Java SE, Guideline 8-6 / SERIAL-6 "Filter untrusted serial data". Oracle Java SE 21 Core Libraries, "Serialization Filtering". |
| `reference/R2` | substituted mechanism | explicit data-only token format (`DataOutputStream`/`DataInputStream`, length-checked UTF-8 strings and counts); no object deserialization at all | OWASP Deserialization Cheat Sheet, "Using Alternative Data Formats": "A great reduction of risk is achieved by avoiding native (de)serialization formats." Oracle Secure Coding Guidelines for Java SE, Section 8: "Deserialization of untrusted data is inherently dangerous and should be avoided." |
| `reference/CONTROL` | — (incomplete by design) | `resolveClass` override that rejects only `thirdparty.canary.GadgetA`, the class in the reported reproducer | — |

R1 and R2 differ in mechanism and in strictness: R1 keeps Java
serialization but narrows it to an allowlist (it rejects the legacy
`LinkedList` probe); R2 drops it, so every token written by the original
implementation is rejected and strings travel as UTF-8 (an unpaired UTF-16
surrogate would not round-trip; Java serialization preserves it). Neither was
written to be slow.

Sources (retrieved 2026-11-18):
- https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html
- https://www.oracle.com/java/technologies/javase/seccodeguide.html
- https://docs.oracle.com/en/java/javase/21/core/serialization-filtering1.html

## Mechanism matching for generated candidates

`case.yaml` `mechanism_match`: a candidate whose source no longer constructs
or subclasses `ObjectInputStream` is compared with R2; every other candidate
is compared with R1.
