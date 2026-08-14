"""
Terminal progress rendering, structured error diagnostics, and output formatters.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional


class TerminalFormatter:
    """
    Handles progress rendering, diagnostic error formatting, and secret masking.
    """

    @staticmethod
    def mask_secrets(data: Any) -> Any:
        """Recursively redact secrets and token strings from data structures."""
        if isinstance(data, str):
            # Mask potential secret tokens
            if "hf_" in data or "sk-" in data or "token" in data.lower() or "secret" in data.lower():
                return "[REDACTED_SECRET]"
            return data
        elif isinstance(data, dict):
            masked = {}
            for k, v in data.items():
                if any(secret_key in k.lower() for secret_key in ["token", "key", "secret", "auth", "password"]):
                    masked[k] = "[REDACTED_SECRET]"
                else:
                    masked[k] = TerminalFormatter.mask_secrets(v)
            return masked
        elif isinstance(data, list):
            return [TerminalFormatter.mask_secrets(item) for item in data]
        return data

    @staticmethod
    def print_progress(current: int, total: int, filename: str, stage: str = "processing", quiet: bool = False) -> None:
        """Render clean terminal progress bar."""
        if quiet:
            return
        pct = (current / max(1, total)) * 100
        bar_len = 30
        filled = int(bar_len * current // max(1, total))
        bar = "=" * filled + "-" * (bar_len - filled)
        sys.stderr.write(f"\r[{bar}] {pct:5.1f}% ({current}/{total}) | {stage.upper()}: {filename[:30]}")
        sys.stderr.flush()
        if current >= total:
            sys.stderr.write("\n")
            sys.stderr.flush()

    @staticmethod
    def print_error(input_source: str, stage: str, reason: str, is_json: bool = False) -> None:
        """Render structured error diagnostics."""
        clean_input = str(TerminalFormatter.mask_secrets(str(input_source)))
        clean_reason = str(TerminalFormatter.mask_secrets(reason))
        if is_json:
            out = {
                "status": "error",
                "input": clean_input,
                "stage": stage,
                "reason": clean_reason,
            }
            print(json.dumps(out, indent=2))
        else:
            sys.stderr.write("\n==================================================\n")
            sys.stderr.write("                scanDOC ERROR DIAGNOSTIC           \n")
            sys.stderr.write("==================================================\n")
            sys.stderr.write(f"Input : {clean_input}\n")
            sys.stderr.write(f"Stage : {stage}\n")
            sys.stderr.write(f"Reason: {clean_reason}\n")
            sys.stderr.write("==================================================\n")
            sys.stderr.flush()

    @staticmethod
    def print_verbose_info(title: str, details: Dict[str, Any], quiet: bool = False) -> None:
        """Print verbose diagnostic telemetry."""
        if quiet:
            return
        clean_details = TerminalFormatter.mask_secrets(details)
        sys.stderr.write(f"\n[VERBOSE] {title}:\n")
        for k, v in clean_details.items():
            sys.stderr.write(f"  • {k}: {v}\n")
        sys.stderr.flush()
