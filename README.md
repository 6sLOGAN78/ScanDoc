# scanDOC

**Enterprise Document Ingestion & Intelligent Layout Analysis Engine**

`scanDOC` is a high-performance, privacy-first local document processing engine. It is explicitly designed to parse complex PDFs, extract deep structural layouts (tables, vector figures, complex math formulas), and convert them into clean, structured Markdown and JSON chunks suitable for RAG pipelines and offline data warehouses. 

Built with an **Adaptive Routing Engine**, it intelligently triages documents—using ultra-fast native extraction for clean digital files, and escalating to heavy ML vision models (like RT-DETR, TableFormer, and Nemotron) only for complex or scanned layouts.

---

## ⚡ Key Capabilities

* **Zero-Network Air-Gapped Mode**: Processes everything entirely on your local hardware. No data ever leaves your machine.
* **Intelligent Routing**: Skips expensive machine learning for native text pages; scales up to deep vision models for dense layouts.
* **Hardware Accelerated**: Automatically harnesses CUDA (NVIDIA), OpenVINO (Intel), or vectorized CPU backends through our unified `ExecutionManager`.
* **Beautiful Native TUI**: Keyboard-first Go-based Terminal User Interface for managing pipelines, monitoring tasks, and downloading models.
* **Structured Export**: Outputs semantic Markdown, structured JSON nodes, and perfectly cropped PNG figures.

---

## 🚀 Quick Start & Installation

### 1. Install the Core Python Engine
Ensure you have Python 3.10+ installed.
```bash
# Clone the repository
git clone https://github.com/your-org/scandoc.git
cd scandoc

# Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Build the Native TUI
The TUI is built in Go for maximum responsiveness. Ensure you have Go 1.21+ installed.
```bash
# Build the TUI executable
go build -o build/scandoc-tui ./cmd/scandoc
```

### 3. Launch the Application
Start the interactive dashboard:
```bash
scandoc tui
```

---

## 🧠 Model Management & Downloading

Because `scanDOC` runs locally, it relies on several specialized ONNX and PyTorch weights (OCR, Layout Analysis, Math parsing, etc.). 

### Where are models stored?
By default, all models are safely downloaded and cached in:
**`~/local/scandoc/models/`**
*(You can override this by setting the `SCANDOC_MODELS_DIR` environment variable).*

### How do I download models?
1. Open the TUI (`scandoc tui`).
2. Press `[M]` to navigate to the **Model Manager**.
3. Select the models you need (e.g., `RapidOCR`, `RT-DETR`, `TableFormerV2`) and press `Enter` to download them directly to your machine. 

### Do I need a HuggingFace Token?
**No.** 95% of the models (like standard OCR and Layout vision models) are completely open-source and will download automatically without any authentication. 

*Exception: If you choose to use specific gated enterprise models (e.g., certain NVIDIA Nemotron or IBM Docling checkpoints), you can optionally authenticate by exporting your token before running the TUI:*
```bash
export HF_TOKEN="your_hf_token_here"
scandoc tui
```

---

## ⚙️ Configuration & Processing

Press `[S]` in the TUI to open **Settings**. Here you can:
* **Toggle Routing Path**: Choose between `ADAPTIVE` (smart), `FAST` (pure text extraction), or `DEEP` (heavy ML layout extraction).
* **Select Models**: Hot-swap which specific ML models are plugged into the Deep and Fast paths.
* **Hardware Device**: Force execution onto `CUDA`, `OpenVINO`, or `CPU`.

---

## 📂 Output Architecture

When you process a folder of documents, `scanDOC` automatically creates an organized, chunked output directory. 

By default, outputs are saved to the directory defined in the TUI (often `~/local/scandoc/outputs/` or your current working directory). 

**Output Structure for a parsed document (`example.pdf`):**
```text
outputs/example.pdf/
├── document.md             # Fully formatted markdown (tables, math, text)
├── document.json           # Raw JSON nodes and bounding box coordinates
└── images/                 # Automatically cropped semantic figures and charts
    ├── fig_ml_0_1.png
    └── table_ml_2_4.png
```

This strict architectural separation ensures the output is instantly ready to be ingested by vector databases or chunking frameworks.
