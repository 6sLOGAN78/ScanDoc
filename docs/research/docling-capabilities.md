# Docling Capabilities Deep Dive & Requirements Analysis

## 1. Executive Summary & Context

Docling (developed by IBM Research) has emerged as a state-of-the-art open-source framework for parsing complex unstructured documents (PDFs, DOCX, PPTX, HTML, Images) into structured, machine-readable formats optimized for GenAI, Large Language Models (LLMs), and Retrieval-Augmented Generation (RAG) pipelines.

Unlike traditional OCR systems (e.g., Tesseract) or raw text extractors (e.g., PyPDF), Docling treats document conversion as a **multimodal document layout and semantic structure reconstruction task**. It parses visual layouts, identifies reading order, extracts complex tables preserving cell spanning, converts formulas, and compiles the entire document into a unified, typed Document Object Model (`DoclingDocument`).

To build an independent, next-generation Document Intelligence Engine (**scanDOC**), we must analyze Docling's capabilities, pinpoint its strengths, identify its performance bottlenecks, and specify the exact functional requirements for our system.

---

## 2. Capability Matrix

| Capability Category | Docling Implementation | Technical Approach | scanDOC Requirement |
| :--- | :--- | :--- | :--- |
| **PDF Inspection & Parsing** | `pypdfium2` / `pdfplumber` | Extracts native text, fonts, vector paths, bounding boxes, embedded bitmap images. | Native fast inspection engine with zero-overhead layout pre-filtering. |
| **Document Layout Analysis** | `docling-ibm-models` (LayoutLMv3 / RT-DETR trained on DocLayNet) | Object detection model segmenting pages into 11+ categories (Header, Paragraph, Table, Picture, etc.). | ONNX/TensorRT multi-model layout engine (YOLOv8/11 layout, RT-DETR, Florence-2). |
| **Reading Order Detection** | Spatial heuristic sorting + Document Graph assembly | Bounding box coordinates sorting with multi-column awareness and reading order graph heuristics. | Topo-spatial reading order algorithm + neural reading order fallback for complex non-linear pages. |
| **Table Structure Recognition** | `TableFormer` (IBM proprietary architecture) | Structure tree prediction + cell bounding box localization + textual mapping. | Modular table engine supporting TATR, SLANet, TableFormer ONNX, and rule-based Lattice/Stream. |
| **OCR Integration** | EasyOCR, Tesseract, RapidOCR, MacOCR, Azure OCR | Crop-based OCR on detected image/text regions or full page fallback when native text is absent. | Pluggable multi-provider OCR framework (RapidOCR, Tesseract, Surya, Paddle, Cloud APIs). |
| **Formula Recognition** | Integrated in layout + LaTeX conversion model | Visual detection of block/inline math and transformation into LaTeX strings. | Dedicated Math OCR / Formula parser (Nougat, GOT-OCR2.0, UniMERNet). |
| **Vision-Language Models (VLM)** | SmolVLM / Qwen2-VL page-to-markdown integration | Passes page images to visual LLMs to directly synthesize Markdown or JSON. | Dynamic Hybrid pipeline: Local VLMs (SmolVLM, Florence-2) + API VLMs (GPT-4o, Claude 3.5). |
| **Document Representation** | `DoclingDocument` (Pydantic v2 data model) | Tree-structured JSON model with strict nodes, references, provenance (`prov`), and furniture separation. | Zero-copy / high-performance Document IR (Pydantic + Msgpack/Arrow serialized graph). |
| **Export Formats** | Markdown, HTML, JSON, Doctags, Chunked Text | Custom serializers with hierarchical heading levels and markdown table formatting. | Markdown, HTML, JSON, Doctags, Arrow/Parquet, and direct LlamaIndex/LangChain objects. |
| **RAG Chunking** | `HybridChunker`, `HierarchicalChunker` | Structure-aware chunking preserving section context, headings, and table integrity. | Semantic & Layout-aware chunking with token-boundary constraint management. |

---

## 3. Detailed Breakdown of Capabilities

### 3.1 PDF Inspection & Parsing
PDFs exist in three primary states:
1. **Digital-Native PDFs**: Contain explicit vector text streams, glyph positions, embedded fonts, and bounding boxes.
2. **Scanned PDFs**: Contain page-sized bitmap images with zero vector text streams.
3. **Hybrid / Programmatic PDFs**: Contain mixed elements—scanned figures embedded beside digital text, vector tables with rasterized logos, or background images behind digital layers.

Docling inspects incoming PDFs page by page, measuring native text coverage (char count, text density, bounding box overlap). If native text quality exceeds a threshold, it bypasses full-page OCR; otherwise, it marks pages for full OCR rasterization.

### 3.2 Layout Detection & Segmentation
Layout analysis identifies visual boundaries and structural roles of document elements. Docling uses models fine-tuned on **DocLayNet** (an IBM-released dataset of 80k annotated pages). Key layout classes include:
- `Caption`: Image/table descriptive labels.
- `Footnote`: Page bottom citations.
- `Formula`: Mathematical notation blocks.
- `List-Item`: Bullet points and numbered sequences.
- `Page-Header` / `Page-Footer`: Document furniture/chrome (usually excluded from body stream).
- `Picture`: Figures, charts, diagrams.
- `Section-Header`: Headings (H1-H6 structural hierarchy).
- `Table`: Tabular data grid.
- `Text`: Regular paragraph blocks.
- `Title`: Document main title.

### 3.3 Reading Order & Document Graph Assembly
Determining correct reading order is critical for multi-column layouts, sidebars, multi-page flow, and embedded text boxes.
- Standard bounding-box sorting (top-to-bottom, left-to-right) fails on multi-column academic papers or news layouts.
- Docling constructs a document hierarchy separating `body` content from `furniture` (headers, footers, page numbers), using geometric layout tree assembly to link text nodes under their parent headers.

### 3.4 Table Structure Recognition (TSR)
Tables represent the highest density of structured information in business documents.
- **Docling's TableFormer**: Takes a cropped table image, predicts the HTML grid tag sequence (`<table>`, `<tr>`, `<td>`, `colspan`, `rowspan`), predicts bounding boxes for each cell, and maps native text/OCR outputs into the target cells.
- **Handling Bordered vs. Borderless Tables**: Bordered tables can be solved via line detection algorithms (Lattice), but borderless tables require visual deep learning to infer implicit spatial alignment.

### 3.5 OCR Engine Integration
When processing scanned documents or un-extractable glyphs:
- Docling supports multiple OCR engines.
- OCR outputs must return bounding boxes and confidence scores aligned with the page coordinate system (usually normalized 0..1 or 72-dpi PDF points).
- Alignment with native elements: Bounding box IoU (Intersection over Union) matching is required to prevent duplicate text extraction when a PDF contains both faint native text and OCR text.

### 3.6 Vision-Language Model (VLM) Pipelines
Modern VLM pipelines (e.g., SmolVLM, Qwen2-VL, Florence-2) allow alternative processing:
- **Direct VLM Conversion**: Page image $\rightarrow$ VLM Prompt $\rightarrow$ Markdown/HTML.
- **Pros**: Handles complex artistic layouts, handwritten notes, and mixed math/text natively without multi-stage pipeline pipeline cascading errors.
- **Cons**: High computational latency, potential model hallucinations, lack of precise bounding-box provenance for RAG citation verification.

### 3.7 Document Export & Downstream Chunking
- **Exporting**: Transforming the document IR into GitHub-Flavored Markdown, semantic HTML5, or raw structured JSON.
- **Structure-Aware RAG Chunking**: Conventional fixed-token chunking (e.g., 512 tokens with 50-token overlap) breaks tables in half and separates headings from paragraph text. Docling's `HybridChunker` ensures chunks break at logical structural boundaries (headings, sub-headings, full tables).

---

## 4. Strengths & Bottlenecks of Docling

### Strengths
1. **Unified Schema**: `DoclingDocument` provides a clean, validated Pydantic model for all document types.
2. **High Table Quality**: `TableFormer` handles multi-span complex business tables with high fidelity.
3. **DocLayNet Pretraining**: Layout model is trained on a massive, diverse dataset.
4. **Rich RAG Chunking**: First-class support for structure-preserving chunking.

### Performance Bottlenecks & Limitations
1. **PyTorch Overhead**: Heavy dependency footprint (~2GB+ dependencies), slow cold-start times.
2. **CPU Execution Latency**: PyTorch model execution (Layout + TableFormer) on CPU takes multiple seconds per page, limiting throughput on standard application servers without GPUs.
3. **Memory Churn**: Python object instantiation for every word/box across hundreds of pages causes high peak memory usage and garbage collection pauses.
4. **Monolithic Framework Dependencies**: Hard-coded PyTorch model invocations make it difficult to run lightweight ONNX Runtime microservices or edge deployments.
5. **Rigid Pipeline Selection**: Fixed pipelines mean simple digital PDFs pay the performance tax of heavy visual inference unless explicitly reconfigured.

---

## 5. Requirements for scanDOC (Our Engine)

Based on this capability analysis, **scanDOC** must satisfy:
1. **Sub-second Digital PDF Processing**: Pure digital PDFs must execute via fast native vector extraction in <50ms per page.
2. **Flexible ML Acceleration**: Models must support native ONNX Runtime (CPU, CUDA, TensorRT, OpenVINO) without mandatory heavy PyTorch dependencies.
3. **Pluggable Architecture**: Modular OCR, Layout, Table, and VLM plugins that can be swapped or cascaded at runtime.
4. **Agentic Control & Dynamic Routing**: Smart inspection to automatically route documents between Light (native), Standard (Layout+OCR), and Deep (VLM/Table) pipelines.
5. **Decoupled Document IR**: High-performance, schema-driven Document IR independent of the execution runtime.
