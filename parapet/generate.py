# SPDX-License-Identifier: Apache-2.0
"""Generate stage: k candidate fixes from the default local generator.

Every request goes through PerfOrch's ``llm_generator.generate_text``. The
model is registered by adding an entry to PerfOrch's ``API_CONFIG`` at
runtime. Each response is written to disk verbatim, before any processing;
extraction (claim L1) runs afterwards on the saved text and never edits it.

Hosted endpoints are refused unless ``allow_hosted_control=True``.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import yaml

from parapet.extract import extract_java
from parapet.hashing import sha256_file, sha256_text
from parapet.paths import SETTINGS_DIR
from parapet.perforch_bridge import llm_generator, register_model
from parapet.prompt import build_prompt, prompt_record

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


class HostedGeneratorRefused(RuntimeError):
    pass


def load_generation_settings(path: Path | None = None) -> dict:
    p = path or (SETTINGS_DIR / "generation.yaml")
    data = yaml.safe_load(Path(p).read_text(encoding="utf-8"))
    data["_path"] = str(p)
    data["_sha256"] = sha256_file(Path(p))
    return data


def is_local(base_url: str) -> bool:
    return (urlparse(base_url).hostname or "") in LOCAL_HOSTS


def assert_allowed(base_url: str, allow_hosted_control: bool) -> None:
    if not is_local(base_url) and not allow_hosted_control:
        raise HostedGeneratorRefused(
            f"refusing hosted generator at {urlparse(base_url).hostname}: PARAPET's default path uses a "
            "local open-weight model; pass --allow-hosted-control only for an attribution control run")


class EndpointLog:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, **entry):
        entry.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


def ollama_api(base_url: str, path: str, log: EndpointLog, payload: dict | None = None) -> dict:
    """GET/POST to the Ollama native API on the same (local) server; logged."""
    root = base_url.rsplit("/v1", 1)[0]
    url = root + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read().decode())
        log.write(endpoint=url, method="POST" if data else "GET", purpose="model metadata",
                  status="ok", duration_s=round(time.monotonic() - t0, 3))
        return body
    except Exception as e:
        log.write(endpoint=url, method="POST" if data else "GET", purpose="model metadata",
                  status=f"error: {e.__class__.__name__}", duration_s=round(time.monotonic() - t0, 3))
        raise


def model_identity(gen: dict, log: EndpointLog) -> dict:
    base = gen["base_url"]
    version = ollama_api(base, "/api/version", log)
    tags = ollama_api(base, "/api/tags", log)
    show = ollama_api(base, "/api/show", log, {"model": gen["model"]})
    entry = next((m for m in tags.get("models", []) if m.get("name") == gen["model"]
                  or m.get("model") == gen["model"]), {})
    info = show.get("model_info", {})
    return {
        "tag": gen["model"],
        "manifest_digest": entry.get("digest"),
        "size_bytes": entry.get("size"),
        "details": show.get("details"),
        "parameter_count": info.get("general.parameter_count"),
        "architecture": info.get("general.architecture"),
        "context_length_trained": next((v for k, v in info.items() if k.endswith(".context_length")), None),
        "license_head": (show.get("license") or "")[:200],
        "server_version": version.get("version"),
        "serving": f"Ollama {version.get('version')} (OpenAI-compatible /v1/chat/completions)",
    }


class RecordingCreate:
    """Wraps client.chat.completions.create: adds seed/max_tokens, keeps the response."""

    def __init__(self, real, log: EndpointLog, base_url: str, product: str):
        self.real, self.log, self.base_url, self.product = real, log, base_url, product
        self.extra: dict = {}
        self.last = None

    def __call__(self, **kwargs):
        kwargs.update(self.extra)
        self.last = None
        t0 = time.monotonic()
        try:
            completion = self.real(**kwargs)
        except Exception as e:
            self.log.write(endpoint=self.base_url.rstrip("/") + "/chat/completions", method="POST",
                           purpose="candidate generation", product=self.product, model=kwargs.get("model"),
                           seed=kwargs.get("seed"), status=f"error: {e.__class__.__name__}",
                           duration_s=round(time.monotonic() - t0, 3))
            raise
        self.last = completion
        self.log.write(endpoint=self.base_url.rstrip("/") + "/chat/completions", method="POST",
                       purpose="candidate generation", product=self.product, model=kwargs.get("model"),
                       seed=kwargs.get("seed"), status="ok", duration_s=round(time.monotonic() - t0, 3))
        return completion


def install_recording_client(product: str, base_url: str, api_key: str, timeout: int,
                             client_max_retries: int, log: EndpointLog) -> RecordingCreate:
    from openai import OpenAI

    lg = llm_generator()
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=client_max_retries)
    rec = RecordingCreate(client.chat.completions.create, log, base_url, product)
    client.chat.completions.create = rec
    lg._client_cache[f"{product}:{timeout}"] = client
    return rec


class PowerSampler:
    """Optional: samples GPU power draw with nvidia-smi while generation runs."""

    def __init__(self, path: Path, interval_ms: int = 200):
        self.path, self.interval_ms, self.proc = path, interval_ms, None

    def __enter__(self):
        self.f = open(self.path, "w")
        self.f.write("timestamp, power.draw [W], utilization.gpu [%], memory.used [MiB]\n")
        self.f.flush()
        self.proc = subprocess.Popen(
            ["nvidia-smi", "--query-gpu=timestamp,power.draw,utilization.gpu,memory.used",
             "--format=csv,noheader,nounits", f"-lms={self.interval_ms}"], stdout=self.f, stderr=subprocess.DEVNULL)
        return self

    def __exit__(self, *exc):
        if self.proc:
            self.proc.terminate()
            self.proc.wait(timeout=10)
        self.f.close()


def generate(case, out_dir: Path, *, settings: dict | None = None, generator: dict | None = None,
             allow_hosted_control: bool = False, id_prefix: str = "G", power_csv: Path | None = None,
             progress=print) -> dict:
    s = settings or load_generation_settings()
    gen = dict(generator or s["default_generator"])
    assert_allowed(gen["base_url"], allow_hosted_control)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "raw").mkdir(exist_ok=True)
    log = EndpointLog(out_dir / "endpoint_log.jsonl")

    api_key = gen.get("api_key")
    if gen.get("key_env"):
        api_key = os.environ.get(gen["key_env"])
        if not api_key:
            raise RuntimeError(f"{gen['key_env']} is not set")
    register_model(gen["product_name"], model=gen["model"], base_url=gen["base_url"], api_key=api_key)
    rec = install_recording_client(gen["product_name"], gen["base_url"], api_key, s["request_timeout_s"],
                                   s["client_max_retries"], log)
    identity = model_identity(gen, log) if gen.get("serving") == "ollama" else {"tag": gen["model"]}
    (out_dir / "model.json").write_text(json.dumps(identity, indent=2), encoding="utf-8")

    prompt = build_prompt(case)
    (out_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    prec = prompt_record(case)
    (out_dir / "prompt.json").write_text(json.dumps(prec, indent=2), encoding="utf-8")
    public_settings = {k: v for k, v in s.items() if not k.startswith("_")}
    (out_dir / "settings.json").write_text(json.dumps(
        {"settings": public_settings, "settings_path": s["_path"], "settings_sha256": s["_sha256"],
         "generator": {k: v for k, v in gen.items() if k != "api_key"}}, indent=2), encoding="utf-8")

    lg = llm_generator()
    candidates = []
    sampler = PowerSampler(power_csv) if power_csv else None
    if sampler:
        sampler.__enter__()
    try:
        for i in range(s["k"]):
            cid = f"{id_prefix}{i + 1}"
            seed = s["seeds"][i]
            rec.extra = {"seed": seed, "max_tokens": s["max_tokens"]}
            started = time.time()
            t0 = time.monotonic()
            res = lg.generate_text(prompt, gen["product_name"], timeout=s["request_timeout_s"],
                                   max_retries=s["max_retries"], temperature=s["temperature"], top_p=s["top_p"])
            wall = time.monotonic() - t0
            text = res.get("text")
            raw_path = out_dir / "raw" / f"{cid}.txt"
            # Verbatim, before any processing.
            raw_path.write_text(text if text is not None else "", encoding="utf-8")
            completion = rec.last
            resp = completion.model_dump() if completion is not None else None
            (out_dir / "raw" / f"{cid}.response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            usage = (resp or {}).get("usage") or {}
            choice = ((resp or {}).get("choices") or [{}])[0]
            code, how = extract_java(text, case.target_class_simple_name)
            entry = {
                "candidate": cid, "seed": seed, "started_at": started, "wall_s": round(wall, 3),
                "status": res.get("status"), "error": res.get("error"),
                "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                "finish_reason": choice.get("finish_reason"), "response_model": (resp or {}).get("model"),
                "raw_path": f"raw/{cid}.txt", "raw_sha256": sha256_file(raw_path),
                "L0": res.get("status") == "success", "L1": code is not None, "extraction": how,
            }
            if code is not None:
                ep = out_dir / "extracted" / cid / Path(case.target_relpath).name
                ep.parent.mkdir(parents=True, exist_ok=True)
                ep.write_text(code, encoding="utf-8")
                entry["extracted_path"] = str(ep.relative_to(out_dir))
                entry["extracted_sha256"] = sha256_text(code)
            with open(out_dir / "generation_log.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            candidates.append(entry)
            if progress:
                progress(f"  {cid}: status={entry['status']} wall={entry['wall_s']}s "
                         f"tokens={entry['prompt_tokens']}+{entry['completion_tokens']} L1={entry['L1']}")
    finally:
        if sampler:
            sampler.__exit__(None, None, None)
    return {"candidates": candidates, "model": identity, "prompt": prec,
            "generator": {k: v for k, v in gen.items() if k != "api_key"}}
