# scanDOC Benchmarking & Production Release Guide

## 1. Installation & Environment Options

### Standard Installation
```bash
pip install scandoc
```

### Installation with Extras
```bash
# Install with local PDF support
pip install scandoc[pdf]

# Install with benchmarking suite & Docling support
pip install scandoc[benchmark]

# Install with GPU ONNX Runtime acceleration
pip install scandoc[gpu]

# Install full development environment
pip install scandoc[dev,pdf,benchmark]
```

---

## 2. CLI Execution & Benchmarking Commands

### Basic Conversion
```bash
scandoc convert input.pdf --output result.md --format markdown
```

### Multi-Core Throughput Benchmarking
```bash
scandoc benchmark --workers 4 --iterations 20
```

### Side-by-Side Comparative Evaluation against Docling
```bash
scandoc benchmark --implementation both --iterations 5 --compare
```

### Benchmark Output in Machine-Readable JSON
```bash
scandoc benchmark --implementation both --json > benchmark_results.json
```

---

## 3. Package Build Verification

To compile the source distribution (`.tar.gz`) and binary wheel (`.whl`):
```bash
python -m build
```

Generated artifacts will be placed in `dist/`.
