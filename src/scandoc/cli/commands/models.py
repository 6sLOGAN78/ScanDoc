"""
CLI subcommand handlers for scanDOC model management lifecycle.
"""

import json
import sys
from typing import Any, List, Optional

from scandoc.cli.exceptions import CliError
from scandoc.cli.formatter import TerminalFormatter
from scandoc.cli.taxonomy import ExitCode
from scandoc.models_mgmt.manager import default_model_manager
from scandoc.models_mgmt.taxonomy import ModelState, TaskType


def run_models(args: Any) -> int:
    """
    Execute scanDOC models subcommand (list, status, download, verify, clear).
    """
    subcommand = getattr(args, "models_command", None)
    is_json = getattr(args, "json", False)

    if not subcommand:
        print("[scanDOC CLI] Use 'scandoc models --help' to view model management options.")
        return ExitCode.SUCCESS

    try:
        if subcommand == "list":
            return _cmd_list(args, is_json)
        elif subcommand == "status":
            return _cmd_status(args, is_json)
        elif subcommand == "download":
            return _cmd_download(args, is_json)
        elif subcommand == "verify":
            return _cmd_verify(args, is_json)
        elif subcommand == "clear":
            return _cmd_clear(args, is_json)
        else:
            raise CliError(f"Unknown models subcommand '{subcommand}'", exit_code=ExitCode.INVALID_ARGUMENTS)

    except Exception as e:
        TerminalFormatter.print_error("Models Command", subcommand, str(e), is_json=is_json)
        return ExitCode.UNEXPECTED_ERROR


def _cmd_list(args: Any, is_json: bool) -> int:
    mgr = default_model_manager
    models = mgr.list_available_models()

    if is_json:
        out_data = [m.model_dump() for m in models]
        print(json.dumps(out_data, indent=2))
        return ExitCode.SUCCESS

    print("\nscanDOC Managed Model Registry:")
    print("-" * 80)
    print(f"{'MODEL ID':<25} {'TASK':<12} {'VERSION':<10} {'CACHE':<10} {'STATUS'}")
    print("-" * 80)

    for m in models:
        installed = mgr.is_installed(m.model_id)
        status_str = "INSTALLED" if installed else "MISSING"
        cache_str = "LOCAL" if installed else "REMOTE"
        print(f"{m.model_id:<25} {m.task.value:<12} {m.version:<10} {cache_str:<10} {status_str}")

    print("-" * 80)
    return ExitCode.SUCCESS


def _cmd_status(args: Any, is_json: bool) -> int:
    mgr = default_model_manager
    model_id = getattr(args, "model_id", None)
    models = [mgr.registry.lookup(model_id)] if model_id else mgr.list_available_models()

    status_list = []
    for m in models:
        if not m:
            continue
        installed = mgr.is_installed(m.model_id)
        spec = mgr.store.get_model_spec(m.model_id) if installed else m
        path_str = spec.local_path if spec and spec.local_path else "Not Cached"
        size_mb = round(spec.size_bytes / (1024 * 1024), 2) if spec else 0.0

        status_list.append({
            "model_id": m.model_id,
            "name": m.model_name,
            "task": m.task.value,
            "version": m.version,
            "installed": installed,
            "path": path_str,
            "size_mb": size_mb,
            "checksum_expected": m.checksum_sha256 or "None",
            "state": m.state.value,
        })

    if is_json:
        print(json.dumps(status_list, indent=2))
        return ExitCode.SUCCESS

    print("\nscanDOC Model Lifecycle Status:")
    for s in status_list:
        print(f"\nModel: {s['model_id']}")
        print(f"  Task:               {s['task']}")
        print(f"  Version:            {s['version']}")
        print(f"  Installed:          {'YES' if s['installed'] else 'NO'}")
        print(f"  Cache Path:         {s['path']}")
        print(f"  Size:               {s['size_mb']} MB")
        print(f"  Expected SHA-256:   {s['checksum_expected']}")

    return ExitCode.SUCCESS


def _cmd_download(args: Any, is_json: bool) -> int:
    mgr = default_model_manager
    model_id = getattr(args, "model_id", None)
    download_all = getattr(args, "all", False)

    if not model_id and not download_all:
        print("Error: Specify a model_id or --all flag to download.")
        return ExitCode.INVALID_ARGUMENTS

    target_ids = [m.model_id for m in mgr.list_available_models()] if download_all else [model_id]

    results = []
    for mid in target_ids:
        try:
            resolved = mgr.resolve(mid)
            results.append({"model_id": mid, "status": "downloaded", "path": resolved.local_path})
            if not is_json:
                print(f"[scanDOC] Successfully downloaded and verified '{mid}' -> {resolved.local_path}")
        except Exception as e:
            results.append({"model_id": mid, "status": "failed", "error": str(e)})
            if not is_json:
                print(f"[scanDOC] Failed to download '{mid}': {e}", file=sys.stderr)

    if is_json:
        print(json.dumps(results, indent=2))

    return ExitCode.SUCCESS


def _cmd_verify(args: Any, is_json: bool) -> int:
    mgr = default_model_manager
    model_id = getattr(args, "model_id", None)
    verify_all = getattr(args, "all", False)

    if not model_id and not verify_all:
        print("Error: Specify a model_id or --all flag to verify.")
        return ExitCode.INVALID_ARGUMENTS

    target_ids = [m.model_id for m in mgr.list_available_models()] if verify_all else [model_id]

    results = []
    for mid in target_ids:
        installed = mgr.is_installed(mid)
        if not installed:
            results.append({"model_id": mid, "exists": False, "verified": False, "status": "MISSING"})
            if not is_json:
                print(f"Model: {mid:<25} Status: MISSING")
            continue

        spec = mgr.store.get_model_spec(mid)
        weights_file = mgr._downloader._find_weights_file(mgr.store.determine_path(spec), spec) if spec else None
        valid = False
        if weights_file and spec and spec.checksum_sha256:
            valid = mgr.store.verify_checksum(weights_file, spec.checksum_sha256)
        elif weights_file:
            valid = True  # No expected checksum to fail against

        status_str = "VERIFIED" if valid else "CORRUPTED"
        results.append({
            "model_id": mid,
            "exists": True,
            "verified": valid,
            "path": str(weights_file) if weights_file else None,
            "status": status_str,
        })
        if not is_json:
            print(f"Model: {mid:<25} Status: {status_str} Path: {weights_file}")

    if is_json:
        print(json.dumps(results, indent=2))

    return ExitCode.SUCCESS


def _cmd_clear(args: Any, is_json: bool) -> int:
    mgr = default_model_manager
    model_id = getattr(args, "model_id", None)
    clear_all = getattr(args, "all", False)

    if not model_id and not clear_all:
        print("Error: Specify a model_id or --all flag to clear cache.")
        return ExitCode.INVALID_ARGUMENTS

    target_ids = [m.model_id for m in mgr.list_available_models()] if clear_all else [model_id]

    results = []
    for mid in target_ids:
        removed = mgr.remove(mid)
        results.append({"model_id": mid, "removed": removed})
        if not is_json:
            print(f"[scanDOC] Cleared model cache for '{mid}': {'Success' if removed else 'Not Installed'}")

    if is_json:
        print(json.dumps(results, indent=2))

    return ExitCode.SUCCESS
