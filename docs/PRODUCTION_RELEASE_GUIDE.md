# scanDOC Production Release & Distribution Guide

## 1. Installation Modes & Optional Extras

scanDOC is packaged with a modular dependency architecture. The base package is lightweight and supports deterministic native extraction out-of-the-box.

### Base Installation (Local-First)
```bash
pip install scandoc
```

### Optional Extras
```bash
# PDF Extraction Extra
pip install scandoc[pdf]

# REST API Server Extra
pip install scandoc[server]

# Benchmarking Suite Extra
pip install scandoc[benchmark]

# GPU Hardware Acceleration Extra
pip install scandoc[gpu]

# Hugging Face VLM Extra
pip install scandoc[huggingface]

# Full Extras Installation
pip install scandoc[all]
```

---

## 2. Single Authoritative Versioning

System versioning is defined in `src/scandoc/__init__.py`:
```python
__version__ = "0.1.0"
```

Verify version in CLI:
```bash
scandoc --version
# Output: scanDOC 0.1.0
```

---

## 3. Building Wheel & Source Distribution

To build production release artifacts:
```bash
python -m build
```

Generated artifacts:
- `dist/scandoc-0.1.0-py3-none-any.whl` (Binary Wheel)
- `dist/scandoc-0.1.0.tar.gz` (Source Distribution)

Verify package metadata with `twine`:
```bash
twine check dist/*
# Output: PASSED
```

---

## 4. Clean Virtual Environment Installation Test

```bash
python -m venv test_env
source test_env/bin/activate
pip install dist/scandoc-0.1.0-py3-none-any.whl

# Test CLI commands
scandoc --help
scandoc convert --help
scandoc inspect --help
scandoc serve --help
scandoc benchmark --help
```

---

## 5. Security & Exclusions Checklist

Release wheels and source distributions MUST NOT bundle:
- Model weights or binary model caches (`.onnx`, `.bin`, `.pt`, `~/.cache`)
- API credentials, tokens, or `.env` files
- Test suites or temporary benchmark outputs

Wheel sizes must remain under **2 MB**.

---

## 6. GitHub Actions & PyPI Release Workflow

The release workflow is defined in `.github/workflows/release.yml`. Releases are triggered automatically upon pushing a git tag matching `v*` (e.g. `git tag v0.1.0 && git push origin v0.1.0`).
