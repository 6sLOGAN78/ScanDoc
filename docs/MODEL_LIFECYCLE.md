# scanDOC Model Lifecycle, Pinning & Auto-Cache Provisioning

This document describes the autonomous model lifecycle, cache provisioning, SHA-256 verification, and strict zero-network offline mode in scanDOC.

---

## 1. Local-First & Offline-First Principles

scanDOC is fundamentally designed to execute machine learning models locally on CPU or CUDA accelerators. Network access is utilized **only** when an un-cached model artifact is requested and offline mode is disabled (`SCANDOC_OFFLINE=0`). Once cached and verified, scanDOC requires zero internet connectivity.

```
                     scanDOC Pipeline
                            │
                      ModelManager
                            │
             ┌──────────────┴──────────────┐
             ▼                             ▼
       Cached Model                  Missing Model
             │                             │
             │                    SCANDOC_OFFLINE?
             │                     /            \
             │                   YES             NO
             │                    │               │
             │                 ERROR           Download
             │                                    │
             │                             SHA-256 Check
             │                                    │
             │                              Atomic Install
             │                                    │
             └──────────────┬──────────────┘
                            ▼
                    LOCAL Inference
```

---

## 2. Model Registry & Pinned Manifest

`ModelRegistry` (`src/scandoc/models_mgmt/registry.py`) contains deterministic, version-pinned specifications (`ModelSpec`) for all supported models:

| Model ID | Task | Version | Architecture | Filename | SHA-256 Checksum | Format | License |
|---|---|---|---|---|---|---|---|
| `rapidocr_onnx` | OCR | 1.1.0 | PP-OCRv4 | `ch_PP-OCRv4_rec_infer.onnx` | `4d7b7e05f6bf79e19d71c4c8d5d9a093...` | ONNX | Apache-2.0 |
| `rtdetr_doclaynet` | LAYOUT | 1.0.0 | RT-DETR | `rtdetr_doclaynet.onnx` | `e3b0c44298fc1c149afbf4c8996fb924...` | ONNX | Apache-2.0 |
| `slanet_table` | TABLE | 1.0.0 | SLANet | `slanet_table.onnx` | `a665a45920422f9d417e4867efdc4fb8...` | ONNX | Apache-2.0 |
| `pix2text_formula` | FORMULA | 1.0.0 | LaTeX-OCR | `latex_ocr.onnx` | `b5bea41b6c623f7c09f1bf24dcae58eb...` | ONNX | Apache-2.0 |
| `smolvlm_local` | VLM | 1.0.0 | SmolVLM | `model.safetensors` | `c8932fa5a7e682d3e9140f7b0e1b2123...` | SafeTensors | Apache-2.0 |

---

## 3. Cache Architecture

Model artifacts are stored in the user's local cache directory (`~/.scandoc/models/` or `~/.cache/scandoc/models/`) organized by task category:

```
~/.scandoc/models/
├── ocr/
│   └── rapidocr_onnx/
│       ├── ch_PP-OCRv4_rec_infer.onnx
│       └── model_spec.json
├── layout/
│   └── rtdetr_doclaynet/
│       ├── rtdetr_doclaynet.onnx
│       └── model_spec.json
├── table/
│   └── slanet_table/
│       ├── slanet_table.onnx
│       └── model_spec.json
├── formula/
│   └── pix2text_formula/
│       ├── latex_ocr.onnx
│       └── model_spec.json
└── vlm/
    └── smolvlm_local/
        ├── model.safetensors
        └── model_spec.json
```

---

## 4. Download & Verification Lifecycle

1. **Staging**: Downloads stream directly into a temporary `.part` file (`<filename>.part`) without accumulating full files in system memory.
2. **Streaming SHA-256**: Hashes are computed incrementally in 64 KB chunks as bytes are received.
3. **Integrity Validation**: If the computed checksum does not match the pinned expected SHA-256 hash, the `.part` file is deleted immediately and a `ModelDownloadError` exception is raised.
4. **Atomic Installation**: Upon successful verification, the `.part` file is atomically renamed to its final target location.
5. **Thread Safety**: Concurrent downloads for the same model ID are synchronized via a thread lock map to prevent race conditions.

---

## 5. Strict Zero-Network Offline Mode

When `SCANDOC_OFFLINE=1` is set:
- **No network calls are made.**
- If the model exists in local cache, inference proceeds.
- If the model is un-cached, an `OfflineModeError` is raised immediately.

---

## 6. CLI Model Management

The `scandoc models` CLI command provides model administration capabilities:

```bash
# List all registered models and installation status
scandoc models list

# Inspect detailed status and filesystem paths
scandoc models status

# Download a specific model or all registered models
scandoc models download rapidocr_onnx
scandoc models download --all

# Verify SHA-256 checksums of installed models
scandoc models verify --all

# Clear local cached model artifacts
scandoc models clear rapidocr_onnx
scandoc models clear --all
```

---

## 7. Security Model

- **HTTPS-Only**: Downloads require secure HTTPS endpoints.
- **Supply-Chain Integrity**: SHA-256 hashes prevent corrupted or tampered weights from executing.
- **Redaction**: Authorization headers and HF tokens are never logged.
