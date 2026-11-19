# Case L1 — java-xmlbuilder, CWE-611 (CVE-2014-125087)

A real open-source Java library at a public historical commit, with a
publicly disclosed weakness that upstream has already fixed.

## Library and provenance

| | |
| --- | --- |
| Library | java-xmlbuilder (`com.jamesmurty.utils:java-xmlbuilder`), https://github.com/jmurty/java-xmlbuilder |
| License | Apache License 2.0 (`lib/LICENSE-2.0.txt`, copied from the upstream repository) |
| Pinned vulnerable commit | `5d5caa583b14ade1d6713b8e73b58679de50361f` (2014-07-22, "Update latest version in README following release of 1.1"), the parent of the fix |
| Upstream fix (R1) | `e6fddca201790abab4f2c274341c0bb8835c3e73` (2014-07-22, "Disable external entities by default to prevent XXE injection attacks, re #6"), released in v1.2 |
| Disclosure | upstream issue #6, "XMLBuilder2 is vulnerable to XML External Entity (XXE) injection", opened 2014-07-22 by an external reporter; CVE-2014-125087 (NVD, published 2023-02-19, CWE-611), whose references list the fix commit, issue #6 and the v1.2 release |
| Copied into this case | `lib/src/main/java` (5 files) and `lib/src/test/java` (3 files) at the pinned commit, byte for byte; R1 = the three main-source files at the fix commit |

**Maintainers and dependents (verified 2026-11-18; raw responses in
`evidence/mozilla-2026-11/step4/sources/`).**

- GitHub contributors API: 4 contributors — `jmurty` (53 commits), two
  other people with 2 and 1 commits, and `dependabot[bot]` (1). Last push to
  the repository: 2020-10-13. Effectively one maintainer.
- deps.dev dependents API: version 1.1 (the vulnerable release line) has 731
  dependents (25 direct, 710 indirect); version 1.3 (latest) has 69 (11
  direct, 58 indirect). These are per-version counts as deps.dev reports
  them; no aggregate across versions is claimed.

## Build (offline after one fetch)

No Maven: the five main sources are compiled with `javac --release 17`
against `base64-2.3.8.jar`; the tests need `junit-4.11.jar` and
`hamcrest-core-1.3.jar`. `fetch_jars.sh` downloads the three jars from Maven
Central once and checks the SHA-256 pinned in `case.yaml`; the case loader
re-checks the hashes on every run.

## Checks

Same canary as C2 (a marker file in a fresh temporary directory, `file:`
URIs only, no network). "Fires" = the marker appears in the parsed document
(its serialized form or its text content) or in an error message. The three
payload shapes are C2's pre-registered shapes, chosen before the upstream fix
was run:

| Check | API | Payload |
| --- | --- | --- |
| reproducer | `XMLBuilder2.parse(String)` (the class named in issue #6) | internal DTD subset, SYSTEM external entity |
| held-out 1 | `XMLBuilder.parse(InputSource)` | external DTD subset (named by `DOCTYPE SYSTEM`) declares the external entity |
| held-out 2 | `XMLBuilder.parse(String)` | internal DTD subset, PUBLIC external entity |

Functional tests: the library's own JUnit suite at the pinned commit
(`TestXMLBuilder` and `TestXMLBuilder2`, 34 tests via `BaseXMLBuilderTests`),
run with JUnit 4.11 against the patched library. All 34 pass on the
unpatched library on the JDK used here. Probes: C2's six documents, parsed
with `XMLBuilder.parse(String)`.

Workload (`legitimate-path`): per operation, `XMLBuilder.parse` of C2's
~7 KB configuration document plus `XMLBuilder.create` of a small document
(both go through the code the fix changes), 800 operations per round.

## Patches (outside `lib/`, never read by the prompt builder)

| Patch | Route | Mechanism | Source |
| --- | --- | --- | --- |
| `reference/R1` | narrowed behavior | upstream fix: explicitly disable `external-general-entities` and `external-parameter-entities` on every `DocumentBuilderFactory` (parse and create); new opt-in overloads in `XMLBuilder` and `XMLBuilder2` (three files) | upstream commit `e6fddca` |
| `reference/R2` | narrowed behavior | reject any DOCTYPE (`disallow-doctype-decl`) plus `FEATURE_SECURE_PROCESSING`, parse path only (one file) | OWASP XML External Entity Prevention Cheat Sheet, Java, DocumentBuilderFactory (DOM) |
| `reference/CONTROL` | — (incomplete by design) | regex denylist for `<!ENTITY name SYSTEM` on character-stream input | — |

R1 and R2 differ in strictness: R1 keeps DTD processing and turns off
external entity resolution; R2 rejects every document with a DOCTYPE.

## Generation target

The prompt builder reads only `lib/src/main/java/com/jamesmurty/utils/BaseXMLBuilder.java`
(1,347 lines, 46,255 bytes), the file whose `parseDocumentImpl` builds the
parser. A candidate replaces that one file; the rest of the library is
compiled unchanged around it.
