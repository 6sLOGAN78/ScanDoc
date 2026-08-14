"""
Dataset management and local fixture discovery subsystem.
"""

import json
from pathlib import Path
from typing import List, Optional

from scandoc.benchmarks.manifest import DocumentCorpusManifest, ManifestDocument
from scandoc.benchmarks.models import BenchmarkCase, GroundTruthDocument
from scandoc.benchmarks.taxonomy import DocumentType


class DatasetManager:
    """
    Manages benchmark datasets and local test fixture discovery.
    Provides graceful fallbacks when external datasets are unavailable.
    """

    def __init__(self, manifest_path: Optional[str] = None):
        self.manifest_path = manifest_path
        self.manifest: Optional[DocumentCorpusManifest] = None
        if manifest_path and Path(manifest_path).exists():
            self.load_manifest(manifest_path)

    def load_manifest(self, manifest_path: str) -> DocumentCorpusManifest:
        """Load corpus manifest from JSON file."""
        p = Path(manifest_path)
        if not p.exists():
            raise FileNotFoundError(f"Dataset manifest not found: {manifest_path}")

        data = json.loads(p.read_text(encoding="utf-8"))
        self.manifest = DocumentCorpusManifest.model_validate(data)
        return self.manifest

    def discover_local_fixtures(self, test_dir: str = "tests") -> List[BenchmarkCase]:
        """Discover synthetic and test PDF/image fixtures in test suite."""
        cases: List[BenchmarkCase] = []
        t_path = Path(test_dir)
        if not t_path.exists():
            return cases

        # Search for test pdf / image files
        pdf_files = list(t_path.rglob("*.pdf")) + list(t_path.rglob("*.png")) + list(t_path.rglob("*.jpg"))
        for idx, f in enumerate(pdf_files):
            cid = f"local_fixture_{f.stem}_{idx}"
            doc_type = DocumentType.IMAGE if f.suffix in (".png", ".jpg", ".jpeg") else DocumentType.DIGITAL_PDF
            cases.append(
                BenchmarkCase(
                    case_id=cid,
                    file_path=str(f),
                    doc_type=doc_type.value,
                    description=f"Local test fixture: {f.name}",
                )
            )

        return cases

    def get_benchmark_cases(self) -> List[BenchmarkCase]:
        """Get benchmark cases from manifest or fallback to local fixtures."""
        cases: List[BenchmarkCase] = []
        if self.manifest and self.manifest.documents:
            for doc in self.manifest.documents:
                gt_doc = None
                if doc.ground_truth_path and Path(doc.ground_truth_path).exists():
                    try:
                        gt_data = json.loads(Path(doc.ground_truth_path).read_text(encoding="utf-8"))
                        gt_doc = GroundTruthDocument.model_validate(gt_data)
                    except Exception:
                        pass

                cases.append(
                    BenchmarkCase(
                        case_id=doc.id,
                        file_path=doc.path,
                        doc_type=doc.doc_type.value,
                        description=f"Manifest doc: {doc.id}",
                        ground_truth=gt_doc,
                    )
                )
        else:
            cases = self.discover_local_fixtures()

        return cases
