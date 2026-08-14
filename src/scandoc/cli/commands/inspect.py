"""
scandoc inspect subcommand implementation.
"""

import json
from pathlib import Path
import sys
from typing import Any, Dict

from scandoc.agent import AgentDocumentInspector
from scandoc.cli.exceptions import InputError
from scandoc.cli.formatter import TerminalFormatter
from scandoc.cli.taxonomy import ExitCode


def run_inspect(args: Any) -> int:
    """
    Execute `scandoc inspect` subcommand.
    
    Returns:
        int: Exit code (ExitCode.SUCCESS, etc.)
    """
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        TerminalFormatter.print_error(str(input_path), "Input Validation", "Input path does not exist", is_json=args.json)
        raise InputError(f"Input file '{input_path}' does not exist.")

    if not input_path.is_file():
        raise InputError(f"Inspect target '{input_path}' is not a file.")

    # Execute fast non-inference inspection
    chars = AgentDocumentInspector.inspect_document(input_path)

    has_native_text = any(p.native_text_ratio > 0.0 for p in chars.pages)
    avg_native_text_ratio = (
        sum(p.native_text_ratio for p in chars.pages) / max(1, len(chars.pages))
    )
    has_images = any(p.image_density > 0.0 or p.has_figures for p in chars.pages)
    image_count = sum(1 for p in chars.pages if p.has_figures or p.image_density > 0.0)
    is_scanned = any(p.scan_probability > 0.5 for p in chars.pages)

    info: Dict[str, Any] = {
        "file_name": input_path.name,
        "file_path": str(input_path),
        "file_size_bytes": input_path.stat().st_size,
        "format": chars.format_name,
        "page_count": chars.num_pages,
        "has_native_text": has_native_text,
        "native_text_ratio": round(avg_native_text_ratio, 3),
        "has_images": has_images,
        "image_count": image_count,
        "is_scanned": is_scanned,
        "recommended_fast_path": has_native_text and not is_scanned,
    }

    if getattr(args, "verbose", False):
        info["page_characteristics"] = [
            {
                "page_index": p.page_index,
                "native_text_ratio": p.native_text_ratio,
                "scan_probability": p.scan_probability,
                "image_density": p.image_density,
                "has_tables": p.has_tables,
                "has_figures": p.has_figures,
            }
            for p in chars.pages
        ]

    if args.json:
        print(json.dumps(TerminalFormatter.mask_secrets(info), indent=2))
    elif not args.quiet:
        sys.stdout.write("==================================================\n")
        sys.stdout.write(f"           scanDOC Document Inspection           \n")
        sys.stdout.write("==================================================\n")
        sys.stdout.write(f"File Name         : {info['file_name']}\n")
        sys.stdout.write(f"Detected Format   : {info['format'].upper()}\n")
        sys.stdout.write(f"Page Count        : {info['page_count']}\n")
        sys.stdout.write(f"Native Text Ratio : {info['native_text_ratio'] * 100:.1f}%\n")
        sys.stdout.write(f"Has Native Text   : {info['has_native_text']}\n")
        sys.stdout.write(f"Is Scanned        : {info['is_scanned']}\n")
        sys.stdout.write(f"Embedded Images   : {info['image_count']}\n")
        sys.stdout.write(f"Recommended Path  : {'Fast Native Extraction' if info['recommended_fast_path'] else 'OCR & Layout Extraction'}\n")
        sys.stdout.write("==================================================\n")

    return ExitCode.SUCCESS
