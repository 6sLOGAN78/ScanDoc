"""
Benchmark dataset manager for CI fixtures and external benchmark datasets.
"""

from pathlib import Path
import tempfile
from typing import List, Optional

from scandoc.benchmarks.ground_truth import GroundTruthLoader
from scandoc.benchmarks.models import BenchmarkCase, GroundTruthDocument, GroundTruthElement


class BenchmarkDatasetManager:
    """
    Manages loading and generation of benchmark cases and ground truth fixtures.
    """

    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_path = Path(dataset_path).expanduser().resolve() if dataset_path else None
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None

    def get_cases(self) -> List[BenchmarkCase]:
        """
        Load benchmark cases. If dataset_path is set and exists, load from directory.
        Otherwise, construct deterministic built-in synthetic CI test fixtures.
        """
        if self.dataset_path and self.dataset_path.exists() and self.dataset_path.is_dir():
            return self._load_external_cases(self.dataset_path)

        return self._generate_ci_fixtures()

    def _load_external_cases(self, directory: Path) -> List[BenchmarkCase]:
        """Load benchmark documents and associated JSON ground truths from directory."""
        cases: List[BenchmarkCase] = []
        valid_exts = {".pdf", ".docx", ".pptx", ".html", ".png", ".jpg", ".jpeg"}

        for p in directory.glob("**/*"):
            if p.is_file() and p.suffix.lower() in valid_exts and not p.name.startswith("."):
                gt_file = p.with_suffix(".json")
                gt = GroundTruthLoader.load_ground_truth(gt_file) if gt_file.exists() else None
                cases.append(
                    BenchmarkCase(
                        case_id=p.stem,
                        file_path=str(p),
                        doc_type=p.suffix.lstrip(".").lower(),
                        description=f"External case {p.name}",
                        ground_truth=gt,
                    )
                )

        return cases

    def _generate_ci_fixtures(self) -> List[BenchmarkCase]:
        """Generate small, deterministic CI fixtures in temporary storage."""
        if self._temp_dir is None:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="scandoc_bench_ci_")

        tmp_path = Path(self._temp_dir.name)
        cases: List[BenchmarkCase] = []

        # Try to import fixture PDF generator
        try:
            from fixtures.pdf_fixtures import generate_digital_pdf_bytes, generate_scanned_pdf_bytes
            digital_pdf = tmp_path / "ci_digital_doc.pdf"
            digital_pdf.write_bytes(generate_digital_pdf_bytes(text="scanDOC CI Benchmark Digital Document Header\nSample paragraph text for testing accuracy."))
            
            gt_digital = GroundTruthDocument(
                doc_id="ci_digital_doc",
                text_content="scanDOC CI Benchmark Digital Document Header Sample paragraph text for testing accuracy.",
                elements=[
                    GroundTruthElement(type="heading", text="scanDOC CI Benchmark Digital Document Header", bbox=[0.1, 0.1, 0.9, 0.2], page_index=0),
                    GroundTruthElement(type="text", text="Sample paragraph text for testing accuracy.", bbox=[0.1, 0.25, 0.9, 0.5], page_index=0),
                ],
            )
            cases.append(BenchmarkCase(case_id="ci_digital_doc", file_path=str(digital_pdf), doc_type="pdf", description="CI Digital PDF Fixture", ground_truth=gt_digital))

            scanned_pdf = tmp_path / "ci_scanned_doc.pdf"
            scanned_pdf.write_bytes(generate_scanned_pdf_bytes(text="Scanned Page Content"))
            gt_scanned = GroundTruthLoader.create_synthetic_ground_truth("ci_scanned_doc", "Scanned Page Content")
            cases.append(BenchmarkCase(case_id="ci_scanned_doc", file_path=str(scanned_pdf), doc_type="pdf", description="CI Scanned PDF Fixture", ground_truth=gt_scanned))

        except ImportError:
            # Fallback text fixture
            txt_file = tmp_path / "ci_sample.txt"
            txt_file.write_text("scanDOC Baseline Text Content", encoding="utf-8")
            gt_txt = GroundTruthLoader.create_synthetic_ground_truth("ci_sample", "scanDOC Baseline Text Content")
            cases.append(BenchmarkCase(case_id="ci_sample", file_path=str(txt_file), doc_type="text", description="CI Fallback Fixture", ground_truth=gt_txt))

        return cases

    def cleanup(self) -> None:
        """Clean up temporary directory if created."""
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None
