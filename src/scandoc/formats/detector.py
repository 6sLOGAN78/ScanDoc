"""
Format detector engine using magic bytes, content heuristics, file extensions, and explicit overrides.
"""

import io
from pathlib import Path
from typing import BinaryIO, Optional, Union

from scandoc.formats.exceptions import (
    AmbiguousFormatError,
    InvalidFileError,
    UnsupportedFormatError,
)
from scandoc.formats.models import FormatDetectionResult

FORMAT_EXTENSION_MAP = {
    ".pdf": ("pdf", "application/pdf"),
    ".docx": ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ".pptx": ("pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
    ".html": ("html", "text/html"),
    ".htm": ("html", "text/html"),
    ".png": ("image", "image/png"),
    ".jpg": ("image", "image/jpeg"),
    ".jpeg": ("image", "image/jpeg"),
    ".webp": ("image", "image/webp"),
    ".tiff": ("image", "image/tiff"),
    ".tif": ("image", "image/tiff"),
    ".txt": ("txt", "text/plain"),
    ".md": ("markdown", "text/markdown"),
    ".markdown": ("markdown", "text/markdown"),
}

OVERRIDE_ALIAS_MAP = {
    "pdf": ("pdf", "application/pdf", ".pdf"),
    "docx": ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
    "pptx": ("pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", ".pptx"),
    "html": ("html", "text/html", ".html"),
    "image": ("image", "image/png", ".png"),
    "txt": ("txt", "text/plain", ".txt"),
    "markdown": ("markdown", "text/markdown", ".md"),
    "md": ("markdown", "text/markdown", ".md"),
}


class FormatDetector:
    """
    Format detection subsystem evaluating magic bytes, extensions, and explicit overrides.
    """

    @classmethod
    def detect(
        cls,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        override_format: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> FormatDetectionResult:
        """
        Detect input document format.
        
        Args:
            source: Input document file path, bytes, or stream.
            override_format: Optional explicit user format override string (e.g. 'pdf', 'docx').
            file_path: Optional filename hint.
            
        Returns:
            FormatDetectionResult containing detected format, confidence, MIME type, and method.
        """
        # Step 1: Check Explicit User Override
        if override_format:
            fmt_clean = override_format.strip().lower()
            if fmt_clean in OVERRIDE_ALIAS_MAP:
                fmt_name, mime_type, ext = OVERRIDE_ALIAS_MAP[fmt_clean]
                return FormatDetectionResult(
                    detected_format=fmt_name,
                    confidence=1.0,
                    mime_type=mime_type,
                    extension=ext,
                    detection_method="explicit_override",
                )
            raise UnsupportedFormatError(f"User override format '{override_format}' is not supported")

        # Step 2: Read header bytes and resolve path hint
        header_bytes, target_path = cls._read_header(source, file_path)
        
        if len(header_bytes) == 0:
            raise InvalidFileError("Input document source is empty (0 bytes)")

        # Step 3: Magic Bytes Inspection
        magic_result = cls._detect_by_magic_bytes(header_bytes, target_path)
        if magic_result:
            return magic_result

        # Step 4: File Extension Fallback
        if target_path:
            ext = Path(target_path).suffix.lower()
            if ext in FORMAT_EXTENSION_MAP:
                MANDATORY_MAGIC_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif", ".docx", ".pptx", ".xlsx", ".zip"}
                if ext not in MANDATORY_MAGIC_EXTS:
                    fmt_name, mime_type = FORMAT_EXTENSION_MAP[ext]
                    return FormatDetectionResult(
                        detected_format=fmt_name,
                        confidence=0.85,
                        mime_type=mime_type,
                        extension=ext,
                        detection_method="extension",
                    )

        # Step 5: Content Heuristics (Plain text vs Markdown vs Unknown Binary)
        heur_result = cls._detect_by_content_heuristics(header_bytes)
        if heur_result:
            return heur_result

        raise UnsupportedFormatError("Unable to detect document format from content or file extension")

    @classmethod
    def _read_header(
        cls,
        source: Union[str, Path, bytes, bytearray, BinaryIO],
        file_path: Optional[str],
    ) -> tuple[bytes, Optional[str]]:
        """Read up to 2048 initial header bytes from source."""
        target_path = file_path

        if isinstance(source, (str, Path)):
            path_obj = Path(source)
            if not path_obj.exists():
                raise InvalidFileError(f"File not found: {source}")
            target_path = str(path_obj.resolve())
            with open(path_obj, "rb") as f:
                header = f.read(2048)
            return header, target_path

        elif isinstance(source, (bytes, bytearray)):
            return bytes(source[:2048]), target_path

        elif hasattr(source, "read"):
            pos = getattr(source, "tell", lambda: None)()
            header = source.read(2048)
            if pos is not None and hasattr(source, "seek"):
                source.seek(pos)
            return header, target_path

        raise InvalidFileError(f"Unsupported source type: {type(source)}")

    @classmethod
    def _detect_by_magic_bytes(
        cls, header: bytes, file_path: Optional[str]
    ) -> Optional[FormatDetectionResult]:
        """Inspect binary signatures."""
        # PDF Magic Bytes (%PDF-)
        if header.startswith(b"%PDF-"):
            return FormatDetectionResult(
                detected_format="pdf",
                confidence=1.0,
                mime_type="application/pdf",
                extension=".pdf",
                detection_method="magic_bytes",
            )

        # PNG Magic Bytes (\x89PNG\r\n\x1a\n)
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return FormatDetectionResult(
                detected_format="image",
                confidence=1.0,
                mime_type="image/png",
                extension=".png",
                detection_method="magic_bytes",
            )

        # JPEG Magic Bytes (\xFF\xD8\xFF)
        if header.startswith(b"\xff\xd8\xff"):
            return FormatDetectionResult(
                detected_format="image",
                confidence=1.0,
                mime_type="image/jpeg",
                extension=".jpg",
                detection_method="magic_bytes",
            )

        # WEBP Magic Bytes (RIFF....WEBP)
        if header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WEBP":
            return FormatDetectionResult(
                detected_format="image",
                confidence=1.0,
                mime_type="image/webp",
                extension=".webp",
                detection_method="magic_bytes",
            )

        # TIFF Magic Bytes (II*\x00 or MM\x00*)
        if header.startswith(b"II*\x00") or header.startswith(b"MM\x00*"):
            return FormatDetectionResult(
                detected_format="image",
                confidence=1.0,
                mime_type="image/tiff",
                extension=".tiff",
                detection_method="magic_bytes",
            )

        # ZIP Container (PK\x03\x04) - DOCX or PPTX
        if header.startswith(b"PK\x03\x04"):
            ext = Path(file_path).suffix.lower() if file_path else ""
            if ext == ".docx":
                return FormatDetectionResult(
                    detected_format="docx",
                    confidence=0.95,
                    mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    extension=".docx",
                    detection_method="magic_bytes",
                )
            elif ext == ".pptx":
                return FormatDetectionResult(
                    detected_format="pptx",
                    confidence=0.95,
                    mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    extension=".pptx",
                    detection_method="magic_bytes",
                )
            # Default ZIP fallback if extension ambiguous
            if b"word/" in header or b"word/document.xml" in header:
                return FormatDetectionResult(
                    detected_format="docx",
                    confidence=0.95,
                    mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    extension=".docx",
                    detection_method="magic_bytes",
                )
            if b"ppt/" in header or b"ppt/presentation.xml" in header:
                return FormatDetectionResult(
                    detected_format="pptx",
                    confidence=0.95,
                    mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    extension=".pptx",
                    detection_method="magic_bytes",
                )

        # HTML Magic Tags (<!DOCTYPE html or <html)
        header_lower = header[:256].lower()
        if b"<!doctype html" in header_lower or b"<html" in header_lower:
            return FormatDetectionResult(
                detected_format="html",
                confidence=0.95,
                mime_type="text/html",
                extension=".html",
                detection_method="magic_bytes",
            )

        return None

    @classmethod
    def _detect_by_content_heuristics(cls, header: bytes) -> Optional[FormatDetectionResult]:
        """Evaluate text/markdown heuristics."""
        if b"\x00" in header:
            return None  # Binary data containing null bytes, not text/markdown

        try:
            text_sample = header.decode("utf-8")
        except UnicodeDecodeError:
            return None  # Binary data, not text/markdown

        # Check for Markdown headers or code blocks
        lines = [line.strip() for line in text_sample.splitlines() if line.strip()]
        if any(line.startswith("# ") or line.startswith("## ") or line.startswith("```") for line in lines[:5]):
            return FormatDetectionResult(
                detected_format="markdown",
                confidence=0.75,
                mime_type="text/markdown",
                extension=".md",
                detection_method="content_heuristics",
            )

        # Plain text fallback
        return FormatDetectionResult(
            detected_format="txt",
            confidence=0.50,
            mime_type="text/plain",
            extension=".txt",
            detection_method="content_heuristics",
        )
