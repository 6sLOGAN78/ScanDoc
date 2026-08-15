"""
scandoc convert subcommand implementation.
"""

import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

from scandoc.cli.exceptions import (
    ConfigurationError,
    InputError,
    ProcessingError,
)
from scandoc.cli.formatter import TerminalFormatter
from scandoc.cli.taxonomy import BatchErrorPolicy, ExitCode
from scandoc.exporters import default_exporter_registry, ExportOptions
from scandoc.pipelines import DocumentPipeline, PipelineConfig, OrderingMode


def run_convert(args: Any) -> int:
    """
    Execute `scandoc convert` subcommand.
    
    Returns:
        int: Exit code (ExitCode.SUCCESS, etc.)
    """
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        TerminalFormatter.print_error(str(input_path), "Input Validation", "Input path does not exist", is_json=args.json)
        raise InputError(f"Input path '{input_path}' does not exist.")

    fmt_name = args.format.lower()
    try:
        default_exporter_registry.get_exporter(fmt_name)
    except Exception as e:
        valid_fmts = ", ".join([e.format_id for e in default_exporter_registry.list_exporters()])
        raise ConfigurationError(f"Unsupported format '{args.format}'. Supported formats: [{valid_fmts}]") from e

    # Collect files
    files_to_process: List[Path] = []
    if input_path.is_file():
        files_to_process.append(input_path)
    elif input_path.is_dir():
        pattern = "**/*" if getattr(args, "recursive", True) else "*"
        for p in input_path.glob(pattern):
            if p.is_file() and not p.name.startswith("."):
                files_to_process.append(p)
    else:
        raise InputError(f"Input '{input_path}' is neither a file nor a directory.")

    if not files_to_process:
        raise InputError(f"No files found to process in '{input_path}'.")

    # Determine destination directory
    out_dir: Optional[Path] = None
    if args.output_dir:
        out_dir = Path(args.output_dir).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
    elif input_path.is_dir():
        out_dir = input_path.resolve()

    # Determine output extension
    ext_map = {
        "markdown": ".md",
        "html": ".html",
        "json": ".json",
        "text": ".txt",
        "docx": ".docx",
    }
    ext = ext_map.get(fmt_name, f".{fmt_name}")

    # Build Pipeline Configuration
    pipeline_config = PipelineConfig(
        max_workers=getattr(args, "workers", 4),
        ordering_mode=OrderingMode.ORDERED,
    )
    pipeline = DocumentPipeline(config=pipeline_config)

    successful = 0
    failed = 0
    skipped = 0
    results_meta: List[Dict[str, Any]] = []
    start_time = time.perf_counter()

    for idx, f in enumerate(files_to_process, start=1):
        if not args.quiet and not args.json:
            TerminalFormatter.print_progress(idx, len(files_to_process), f.name, stage="Pipeline", quiet=args.quiet)

        # Output path calculation
        if args.output and input_path.is_file():
            target_out = Path(args.output).expanduser().resolve()
        elif out_dir:
            target_out = out_dir / f"{f.stem}{ext}"
        else:
            target_out = f.parent / f"{f.stem}{ext}"

        if target_out.exists() and not getattr(args, "overwrite", False):
            if args.verbose:
                TerminalFormatter.print_verbose_info("File Skipped", {"file": str(f), "reason": "Target file exists and --overwrite not specified"}, quiet=args.quiet)
            skipped += 1
            continue

        try:
            # Process via Pipeline
            p_result = pipeline.process(f)
            if p_result.status != "success" or not p_result.document_ir:
                err_msg = "; ".join(p_result.errors) if p_result.errors else "Pipeline processing failed"
                raise ProcessingError(err_msg)

            if fmt_name == "json":
                try:
                    images_dir = target_out.parent / "images"
                    images_dir.mkdir(parents=True, exist_ok=True)
                    import base64
                    for page in p_result.document_ir.pages:
                        for block in page.blocks:
                            if block.block_type == "figure" and getattr(block, "image_ref", None):
                                img_ref = block.image_ref
                                if getattr(img_ref, "base64_data", None):
                                    img_data = base64.b64decode(img_ref.base64_data)
                                    img_path = images_dir / f"{block.id}.png"
                                    img_path.write_bytes(img_data)
                                    img_ref.path = str(img_path)
                                    img_ref.base64_data = None # do not store binary inside JSON
                except Exception as ex:
                    TerminalFormatter.print_error(str(f), "Image Extraction", str(ex), is_json=args.json)

            # Export via Exporter
            export_res = default_exporter_registry.export(p_result.document_ir, ExportOptions(format_id=fmt_name))
            exported_content = export_res.content

            target_out.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(exported_content, bytes):
                target_out.write_bytes(exported_content)
            else:
                target_out.write_text(str(exported_content), encoding="utf-8")

            if fmt_name == "json":
                try:
                    annotated_pdf_path = target_out.with_suffix('.annotated.pdf')
                    _generate_annotated_pdf(f, p_result.document_ir, annotated_pdf_path)
                except Exception as ex:
                    TerminalFormatter.print_error(str(f), "Annotated PDF", str(ex), is_json=args.json)

            successful += 1
            results_meta.append({
                "source": str(f),
                "target": str(target_out),
                "pages": len(p_result.document_ir.pages),
                "time_sec": round(p_result.metrics.total_processing_time_ms / 1000.0, 3),
            })

            if args.verbose:
                TerminalFormatter.print_verbose_info("File Processed", {
                    "source": str(f),
                    "target": str(target_out),
                    "pages": len(p_result.document_ir.pages),
                    "pipeline_time": f"{p_result.metrics.total_processing_time_ms / 1000.0:.3f}s",
                }, quiet=args.quiet)

        except Exception as e:
            failed += 1
            TerminalFormatter.print_error(str(f), "Conversion", str(e), is_json=args.json)
            if getattr(args, "on_error", "continue-on-error") == BatchErrorPolicy.FAIL_FAST.value:
                raise ProcessingError(f"Batch execution failed on '{f}': {e}") from e

    elapsed = round(time.perf_counter() - start_time, 3)

    if args.json:
        summary = {
            "status": "completed" if failed == 0 else "completed_with_errors",
            "format": fmt_name,
            "total_files": len(files_to_process),
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "elapsed_sec": elapsed,
            "results": results_meta,
        }
        print(json.dumps(summary, indent=2))
    elif not args.quiet:
        sys.stdout.write("\n" + "=" * 50 + "\n")
        sys.stdout.write(f" scanDOC Conversion Completed in {elapsed}s\n")
        sys.stdout.write(f" Successful: {successful} | Failed: {failed} | Skipped: {skipped}\n")
        sys.stdout.write("=" * 50 + "\n")

    return ExitCode.SUCCESS if failed == 0 else ExitCode.PROCESSING_ERROR

def _generate_annotated_pdf(source_path: Path, doc_ir, out_path: Path) -> None:
    try:
        import pypdfium2 as pdfium
        from PIL import ImageDraw
    except ImportError:
        return
        
    pdf = pdfium.PdfDocument(str(source_path))
    images = []
    
    color_map = {
        "text": "blue",
        "table": "green",
        "figure": "red",
        "formula": "purple",
        "heading": "orange",
        "list": "cyan"
    }

    for page_idx in range(len(pdf)):
        page = pdf[page_idx]
        bitmap = page.render(scale=2.0)
        img = bitmap.to_pil()
        draw = ImageDraw.Draw(img)
        w, h = img.size
        
        # Find blocks for this page
        for p in doc_ir.pages:
            if p.page_index == page_idx:
                for block in p.blocks:
                    if block.bbox:
                        x0 = block.bbox.left * w
                        y0 = block.bbox.top * h
                        x1 = block.bbox.right * w
                        y1 = block.bbox.bottom * h
                        c = color_map.get(block.block_type.lower(), "red")
                        draw.rectangle([x0, y0, x1, y1], outline=c, width=3)
        images.append(img)
        
    if images:
        images[0].save(str(out_path), save_all=True, append_images=images[1:])
