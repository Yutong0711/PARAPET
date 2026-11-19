# Installs and network access for the mozilla/local-slice work

Every install made for this work, and every network endpoint contacted while
installing or checking sources. Nothing was installed system-wide, no `sudo`
was used, and no existing project, file, or service was modified or
reconfigured. The repository's own `.venv/` (on the Windows drive) was not
touched.

## Pre-existing (not installed by this work)

| Component | Version | Location |
| --- | --- | --- |
| OpenJDK (javac, java) | 21.0.13.0.3 (Ubuntu build 21.0.13.0.3+1-1-26.04.1) | `/usr/lib/jvm/java-21-openjdk-amd64` |
| Python | 3.14.4 | `/usr/bin/python3` |
| uv | 0.11.29 | `~/.local/bin/uv` |
| NVIDIA driver / CUDA UMD | KMD 610.60, nvidia-smi 610.47.03, CUDA UMD 13.3 | Windows host driver exposed to WSL2 |

## Installed

| # | What | Version | Where | How | Source |
| --- | --- | --- | --- | --- | --- |
| 1 | Ollama (local model server, Linux amd64, includes CUDA runners) | v0.40.16 (released 2026-11-09) | `~/opt/ollama-v0.40.16/` (2.4 GB) | release tarball `ollama-linux-amd64.tar.zst`, SHA-256 `87bfafb2acbc89b2e6a1be0a9043de6aa75fb450696f86bc426e65fc448f788d` (matches the digest GitHub publishes for the asset), extracted with Python 3.14's standard-library `tarfile` (zstd) because no `zstd` binary was present | https://github.com/ollama/ollama/releases/tag/v0.40.16 |
| 2 | Model `qwen2.5-coder:7b-instruct-q4_K_M` | see EVIDENCE.md section A for digest | `~/parapet-work/ollama-models/` (dedicated `OLLAMA_MODELS` dir) | `ollama pull` through the local server | registry.ollama.ai |
| 3 | Python virtual environment | Python 3.14.4 | `~/parapet-work/venv/` | `uv venv`, `uv pip install` | pypi.org |

Packages in the virtual environment (`uv pip list`): annotated-types 0.8.0,
anyio 4.16.0, certifi 2026.10.23, distro 1.9.0, h11 0.16.0, httpcore 1.0.9,
httpx 0.28.1, idna 3.20, iniconfig 2.3.1, jiter 0.19.0, numpy 2.5.5,
openai 2.54.0, packaging 26.3, pluggy 1.7.0, pydantic 2.14.3,
pydantic-core 2.50.4, pygments 2.21.0, pytest 8.4.2, pyyaml 6.0.3,
sniffio 1.3.1, tqdm 4.70.1, typing-extensions 4.16.0, typing-inspection 0.4.5.

## How the model server is run

A user process, not a system service, bound to loopback only:

```bash
OLLAMA_HOST=127.0.0.1:11434 \
OLLAMA_MODELS=$HOME/parapet-work/ollama-models \
OLLAMA_CONTEXT_LENGTH=8192 \
OLLAMA_KEEP_ALIVE=30m \
~/opt/ollama-v0.40.16/bin/ollama serve
```

Server log: `~/parapet-work/logs/ollama-serve-gpu.log` (copied into the
evidence directory with the run outputs).

## Network endpoints contacted for installs and citation checks

| Time (PST) | Endpoint | Purpose |
| --- | --- | --- |
| 2026-11-18 16:38:50 | `https://api.github.com/repos/ollama/ollama/releases/latest` | find the Ollama release asset and its digest |
| 2026-11-18 16:38:57 | `https://github.com/ollama/ollama/releases/download/v0.40.16/ollama-linux-amd64.tar.zst` (redirects to GitHub's release CDN) | download Ollama |
| 2026-11-18 16:39:03 | `https://pypi.org` (via uv) | Python packages above |
| 2026-11-18 16:47:08 | `https://registry.ollama.ai` (via the local Ollama server) | model manifest and blobs |
| 2026-11-18 16:52:22 | `https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html` | verify citation wording for C1 R1/R2 |
| 2026-11-18 16:52:27 | `https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html` | verify citation wording for C2 R1/R2 |
| 2026-11-18 16:52:33 | `https://docs.oracle.com/en/java/javase/21/core/serialization-filtering1.html` | verify citation for C1 R1 |
| 2026-11-18 16:52:36 | `https://www.oracle.com/java/technologies/javase/seccodeguide.html` | verify citation for C1 R1/R2 |
| 2026-11-18 16:52:57 | `https://wiki.sei.cmu.edu/confluence/display/java/IDS17-J.+Prevent+XML+External+Entity+Attacks` | verify citation for C2 R2 |
| 2026-11-18 16:52:58 | `https://wiki.sei.cmu.edu/confluence/display/java/SER12-J.+Prevent+deserialization+of+untrusted+data` | checked, not cited |

Model-call endpoints are logged separately, per run, in each run's
`generation/endpoint_log.jsonl`.
