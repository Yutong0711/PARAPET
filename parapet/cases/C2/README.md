# Case C2 — CWE-611 Improper Restriction of XML External Entity Reference

An authored, self-contained Java case (JDK standard library only). It is a
teaching-sized model of a common pattern, not a real project.

## The weakness

`src/example/config/ConfigLoader.java` loads tenant-uploaded configuration
documents with a default `DocumentBuilderFactory`. On the JDK used here
(OpenJDK 21) the default parser resolves external entities and loads
external DTD subsets, so a document can make the server read a local file and
return its contents in the parsed configuration.

## Harmless canary

Each check writes a marker file (`secret.txt`, content
`PARAPET-CANARY-C2-5b1e`) into a fresh temporary directory, builds the payload
with `file:` URIs pointing into that directory, and deletes the directory
afterwards. "Fires" means the marker text appears in the loader's result or
in its error message. No network URL is ever used.

| Check | Payload |
| --- | --- |
| reproducer | internal DTD subset, general entity with a `SYSTEM` identifier pointing at the marker file |
| held-out 1 | no entity in the document; `<!DOCTYPE config SYSTEM "file:.../ext.dtd">` names an external DTD (written by the check) that declares the entity |
| held-out 2 | internal DTD subset, general entity declared with a `PUBLIC` identifier |

The held-out variants and the harness never appear in the generation prompt.

## Required behavior (functional tests)

`harness/harness/c2/FunctionalTests.java`, 11 tests on documents **without a
DOCTYPE**: nested elements, attributes, comments, CDATA, predefined and
character references, whitespace trimming, Unicode, XML declaration, document
order, the 277-key workload document, malformed input rejected with
`IOException`. DTD features are not part of the required behavior; how a patch
treats them is reported by the probes.

## Inputs now rejected (probes)

`harness/harness/c2/Probes.java` loads six legitimate documents the original
accepts: the workload document, comments/CDATA/character references, a
DOCTYPE with no subset, an internal entity, an internal attribute default, and
a benign local external DTD that declares only element types.

## Workload (`legitimate-path`)

`harness/harness/c2/Workload.java`: load one ~7 KB configuration document
(30 servers, attributes, a comment, CDATA; no DOCTYPE) per operation, 600
operations per round, single thread, single process.

## Hand-written patches (outside `src/`, never read by the prompt builder)

| Patch | Route | Mechanism | Published guidance |
| --- | --- | --- | --- |
| `reference/R1` | narrowed behavior | reject every DOCTYPE (`disallow-doctype-decl`), plus `FEATURE_SECURE_PROCESSING` | OWASP XML External Entity Prevention Cheat Sheet, Java, DocumentBuilderFactory (DOM): "reject DOCTYPE declarations and leave XInclude disabled" (the cheat sheet's snippet sets exactly these two features). |
| `reference/R2` | added work on the call path | `EntityResolver` that throws `SAXException` for every external entity and external DTD subset; internal DTD subsets still processed; plus `FEATURE_SECURE_PROCESSING` | OWASP XXE Prevention Cheat Sheet, Java, "Other providers and required DTDs": "If internal DTDs are required, install an EntityResolver on the DOM builder or SAX reader that throws SAXException for external references", and "enable FEATURE_SECURE_PROCESSING where supported". SEI CERT Oracle Coding Standard for Java, IDS17-J, "Compliant Solution (EntityResolver)". |
| `reference/CONTROL` | — (incomplete by design) | regex denylist for the reproducer's shape `<!ENTITY name SYSTEM` only | — |

R1 and R2 differ in strictness and mechanism: R1 rejects every document with
a DOCTYPE, so all four DTD probes are rejected; R2 keeps internal DTD
processing and rejects only documents that reference an external resource.
Neither was written to be slow.

Sources (retrieved 2026-11-18):
- https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html
- https://wiki.sei.cmu.edu/confluence/display/java/IDS17-J.+Prevent+XML+External+Entity+Attacks

## Mechanism matching for generated candidates

`case.yaml` `mechanism_match`: a candidate that sets `disallow-doctype-decl`
to `true` is compared with R1; otherwise one that calls `setEntityResolver` is
compared with R2; every other candidate is compared with R1.
