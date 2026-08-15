# scanDOC 
**Enterprise Document Intelligence Engine**

`scanDOC` is a privacy-first, local document processing engine engineered to parse complex PDFs, extract deep structural layouts (tables, vector figures, complex math formulas), and convert them into clean, structured Markdown and JSON chunks for RAG pipelines.

It uses an **Adaptive Routing Engine** that skips expensive machine learning for native text pages, and escalates to heavy ML vision models (like RT-DETR, TableFormer, and Nemotron) only for complex or scanned layouts. **No VLM fallbacks are used**; this engine is strictly designed for exact document chunking and layout preservation.

---

## 🚀 Quick Start & Installation

### 1. Install the Core Python Engine (Python 3.10+)
```bash
git clone https://github.com/your-org/scandoc.git
cd scandoc
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Build the Native TUI (Go 1.21+)
```bash
go build -o build/scandoc-tui ./cmd/scandoc
```

### 3. Launch the Dashboard
```bash
./build/scandoc-tui
```

---

## 🧠 Model Management 

Because `scanDOC` runs locally, it relies on several specialized ONNX weights (OCR, Layout Analysis, Math parsing, etc.). 

### How to Download Models
1. Open the TUI (`./build/scandoc-tui`).
2. Press `[M]` to navigate to the **Model Manager**.
3. Select the models you need and press `Enter` to download them. 

### Where are Models Stored?
Models are safely downloaded and cached in:
**`~/local/scandoc/models/`**
The TUI seamlessly tracks installations in this directory.

### Do I need a HuggingFace Token?
**No.** All models provided (including heavy enterprise models like Nemotron and TableFormerV2) are openly accessible. You do not need a HuggingFace token to download or use any models in `scanDOC`.

---

## ⚙️ Pipeline Configuration

Press `[P]` in the TUI to open the **Pipeline Configuration**. Here you can:
* **Toggle Routing Path**: Choose between `Adaptive` (smart), `Fast` (pure text extraction), or `Deep` (heavy ML layout extraction).
* **Select Models Per Stage**: Within Adaptive and Deep modes, press `Enter` on any pipeline stage (OCR, Layout, Table, Formula) to cycle through the specific models you downloaded. Models are clearly labeled by their size and speed tradeoffs (e.g. Fast vs Heavy).

---

## 📂 Output Architecture

`scanDOC` outputs are strictly formatted for immediate RAG ingestion. 
By default, outputs are saved to `~/local/scandoc/output/` (or the folder chosen in the TUI).

**Output Structure for `example.pdf`:**
```text
outputs/example.pdf/
├── document.md             # Fully formatted markdown (tables, math, text)
├── document.json           # Raw JSON nodes and bounding box coordinates
└── images/                 # Automatically cropped semantic figures and charts
    ├── fig_ml_0_1.png
    └── table_ml_2_4.png
```
