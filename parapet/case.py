# SPDX-License-Identifier: Apache-2.0
"""Loading and validating PARAPET case definitions (``cases/<id>/case.yaml``)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from parapet.hashing import sha256_file
from parapet.paths import CASES_DIR

CHECK_NAMES = ("reproducer", "heldout1", "heldout2", "functional", "probes")


class CaseError(ValueError):
    pass


@dataclass(frozen=True)
class Reference:
    id: str
    path: Path            # the patched target file
    route: str
    mechanism: str
    guidance: tuple
    files: tuple = ()     # ((relpath, Path), ...) for a multi-file reference (e.g. an upstream fix)

    def file_map(self, target_relpath: str) -> dict:
        if self.files:
            return {rel: Path(p) for rel, p in self.files}
        return {target_relpath: self.path}


@dataclass(frozen=True)
class Case:
    id: str
    dir: Path
    title: str
    cwe_id: str
    cwe_name: str
    java_release: int
    target_src_root: Path
    target_relpath: str
    harness_sourcepath: Path
    support_root: Path | None
    support_sources: tuple
    fixtures: Path | None
    checks: dict
    workload_name: str
    workload_main: str
    workload_description: str
    ops_per_round: int
    references: dict
    control_path: Path
    control_description: str
    mechanism_match: tuple = field(default_factory=tuple)
    library_sources_root: Path | None = None
    library_test_sources_root: Path | None = None
    jars: tuple = ()          # compile + runtime classpath jars (verified Paths)
    test_jars: tuple = ()     # harness classpath jars (verified Paths)
    provenance: dict = field(default_factory=dict)

    @property
    def is_library(self) -> bool:
        return self.library_sources_root is not None

    def read_original(self, relpath: str) -> str:
        root = self.library_sources_root if self.is_library else self.target_src_root
        return (root / relpath).read_text(encoding="utf-8")

    def library_files(self) -> dict:
        """relpath -> original text for every compiled source file of the case."""
        if not self.is_library:
            return {self.target_relpath: self.read_target()}
        root = self.library_sources_root
        return {str(f.relative_to(root)): f.read_text(encoding="utf-8") for f in sorted(root.rglob("*.java"))}

    @property
    def harness_classpath_jars(self) -> list:
        return list(self.jars) + list(self.test_jars)

    @property
    def target_path(self) -> Path:
        return self.target_src_root / self.target_relpath

    @property
    def target_class_simple_name(self) -> str:
        return Path(self.target_relpath).stem

    def read_target(self) -> str:
        return self.target_path.read_text(encoding="utf-8")

    def match_reference(self, source: str) -> str:
        """Map a patch to the reference fix with the same mechanism.

        Applies the pre-registered ``mechanism_match`` rules in order; the
        first rule whose conditions hold wins. A rule with no conditions is
        the default.
        """
        for rule in self.mechanism_match:
            any_of = rule.get("any_of") or []
            none_of = rule.get("none_of") or []
            if any_of and not any(re.search(p, source) for p in any_of):
                continue
            if none_of and any(re.search(p, source) for p in none_of):
                continue
            return rule["ref"]
        return "R1"


def jars_dir() -> Path:
    """Where dependency jars live (outside the repository; see each case's fetch_jars.sh)."""
    env = os.environ.get("PARAPET_JARS_DIR")
    return Path(env).expanduser() if env else Path.home() / "parapet-work" / "jars"


def _resolve_jar(spec: dict, ctx: str) -> Path:
    p = jars_dir() / spec["file"]
    if not p.is_file():
        raise CaseError(f"{ctx}: dependency jar {p} not found; run the case's fetch_jars.sh "
                        f"({spec.get('coordinate')})")
    digest = sha256_file(p)
    if digest != spec["sha256"]:
        raise CaseError(f"{ctx}: {p} sha256 {digest} != pinned {spec['sha256']}")
    return p


def _req(d: dict, key: str, ctx: str):
    if key not in d:
        raise CaseError(f"{ctx}: missing key {key!r}")
    return d[key]


def load_case(case_id: str, cases_dir: Path = CASES_DIR) -> Case:
    cdir = Path(cases_dir) / case_id
    manifest = cdir / "case.yaml"
    if not manifest.is_file():
        raise CaseError(f"unknown case {case_id!r}: {manifest} not found")
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    ctx = str(manifest)
    if _req(data, "id", ctx) != case_id:
        raise CaseError(f"{ctx}: id {data['id']!r} does not match directory {case_id!r}")
    cwe = _req(data, "cwe", ctx)
    target = _req(data, "target", ctx)
    harness = _req(data, "harness", ctx)
    checks = _req(data, "checks", ctx)
    for name in CHECK_NAMES:
        _req(checks, name, f"{ctx} checks")
    workload = _req(data, "workload", ctx)
    refs = {}
    for rid, r in _req(data, "references", ctx).items():
        files = tuple((rel, cdir / path) for rel, path in (r.get("files") or {}).items())
        refs[rid] = Reference(
            id=rid,
            path=cdir / _req(r, "path", f"{ctx} references.{rid}"),
            route=_req(r, "route", f"{ctx} references.{rid}"),
            mechanism=_req(r, "mechanism", f"{ctx} references.{rid}"),
            guidance=tuple(_req(r, "guidance", f"{ctx} references.{rid}")),
            files=files,
        )
    if set(refs) != {"R1", "R2"}:
        raise CaseError(f"{ctx}: exactly two reference fixes R1 and R2 are required")
    control = _req(data, "control", ctx)
    fixtures = harness.get("fixtures")
    lib = data.get("library") or {}
    jars, test_jars = (), ()
    if lib:
        jars = tuple(_resolve_jar(j, ctx) for j in lib.get("jars") or ())
        test_jars = tuple(_resolve_jar(j, ctx) for j in lib.get("test_jars") or ())
    case = Case(
        id=case_id,
        dir=cdir,
        title=_req(data, "title", ctx),
        cwe_id=_req(cwe, "id", ctx),
        cwe_name=_req(cwe, "name", ctx),
        java_release=int(data.get("java_release", 17)),
        target_src_root=cdir / _req(target, "src_root", ctx),
        target_relpath=_req(target, "path", ctx),
        harness_sourcepath=cdir / _req(harness, "sourcepath", ctx),
        support_root=(cdir / harness["support_root"]) if harness.get("support_root") else None,
        support_sources=tuple(harness.get("support_sources") or ()),
        fixtures=(cdir / fixtures) if fixtures else None,
        checks=dict(checks),
        workload_name=_req(workload, "name", ctx),
        workload_main=_req(workload, "main", ctx),
        workload_description=workload.get("description", ""),
        ops_per_round=int(_req(workload, "ops_per_round", ctx)),
        references=refs,
        control_path=cdir / _req(control, "path", ctx),
        control_description=control.get("description", ""),
        mechanism_match=tuple(data.get("mechanism_match") or ()),
        library_sources_root=(cdir / lib["sources_root"]) if lib.get("sources_root") else None,
        library_test_sources_root=(cdir / lib["test_sources_root"]) if lib.get("test_sources_root") else None,
        jars=jars,
        test_jars=test_jars,
        provenance=dict(data.get("provenance") or {}),
    )
    # Reference and control patches must live outside the directory the
    # prompt builder reads.
    src_root = case.target_src_root.resolve()
    ref_paths = [p for r in refs.values() for p in r.file_map(case.target_relpath).values()]
    for p in ref_paths + [r.path for r in refs.values()] + [case.control_path]:
        if src_root in p.resolve().parents:
            raise CaseError(f"{ctx}: {p} is inside the prompt source root {src_root}")
        if not p.is_file():
            raise CaseError(f"{ctx}: patch file {p} not found")
    if not case.target_path.is_file():
        raise CaseError(f"{ctx}: target {case.target_path} not found")
    return case


def list_cases(cases_dir: Path = CASES_DIR) -> list[str]:
    return sorted(p.name for p in Path(cases_dir).iterdir() if (p / "case.yaml").is_file())
