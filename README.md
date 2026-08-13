# scanDOC: Next-Generation Open-Source Document Intelligence Engine

`scanDOC` is an open-source, high-performance Document Intelligence Engine designed for converting complex PDFs, scanned documents, and images into structured, machine-readable formats (Markdown, HTML, JSON, RAG Chunks).

## Features & Goals
- **High Speed**: Sub-50ms processing per page for digital PDFs via fast native inspection.
- **ONNX-First Runtime**: Multi-provider execution (CPU, CUDA, OpenVINO, TensorRT) without mandatory heavy PyTorch dependencies.
- **Pluggable Architecture**: Modular OCR, Layout Analysis, Table Structure Recognition, and VLM providers.
- **Agentic Pipeline Selection**: Smart document inspection and automated fallback routing.

## Documentation
- [System Architecture](docs/ARCHITECTURE.md)
- [Project Roadmap](docs/ROADMAP.md)
- [Docling Capabilities Analysis](docs/research/docling-capabilities.md)
- [Docling Architecture Deconstruction](docs/research/docling-architecture.md)
- [OCR Engine Landscape](docs/research/ocr-landscape.md)
- [Layout Analysis Landscape](docs/research/layout-landscape.md)
- [Table Recognition Landscape](docs/research/table-landscape.md)
- [VLM Landscape](docs/research/vlm-landscape.md)
- [Inference Acceleration Landscape](docs/research/inference-landscape.md)

## License
Apache License 2.0
