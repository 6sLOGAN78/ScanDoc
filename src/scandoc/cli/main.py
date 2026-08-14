"""
Main CLI entry point for scanDOC orchestrating commands, signal handling, and exit code resolution.
"""

import signal
import sys
from typing import Any, List, Optional

from scandoc.cli.commands.benchmark import run_benchmark
from scandoc.cli.commands.convert import run_convert
from scandoc.cli.commands.inspect import run_inspect
from scandoc.cli.commands.models import run_models
from scandoc.cli.commands.serve import run_serve
from scandoc.cli.commands.studio import run_studio
from scandoc.cli.exceptions import CliError
from scandoc.cli.formatter import TerminalFormatter
from scandoc.cli.parser import create_parser
from scandoc.cli.taxonomy import ExitCode

_active_cancelled = False


def _signal_handler(signum: int, frame: Any) -> None:
    global _active_cancelled
    _active_cancelled = True
    sys.stderr.write("\n[scanDOC CLI] Cancellation signal received (SIGINT/SIGTERM). Shutting down...\n")
    sys.stderr.flush()
    sys.exit(ExitCode.SIGINT_CANCELLED)


def main(args: Optional[List[str]] = None) -> int:
    """
    Main CLI entry point function.
    
    Args:
        args: List of command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    # Register signal handlers for clean SIGINT / SIGTERM handling
    try:
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
    except (ValueError, AttributeError):
        pass  # Signal registration might fail if called from a non-main thread

    parser = create_parser()

    if args is None:
        args = sys.argv[1:]

    if not args:
        parser.print_help()
        return ExitCode.SUCCESS

    try:
        parsed_args = parser.parse_args(args)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else ExitCode.INVALID_ARGUMENTS

    if not parsed_args.command:
        parser.print_help()
        return ExitCode.SUCCESS

    try:
        if parsed_args.command == "convert":
            return run_convert(parsed_args)
        elif parsed_args.command == "inspect":
            return run_inspect(parsed_args)
        elif parsed_args.command == "serve":
            return run_serve(parsed_args)
        elif parsed_args.command == "benchmark":
            return run_benchmark(parsed_args)
        elif parsed_args.command == "models":
            return run_models(parsed_args)
        elif parsed_args.command == "studio":
            return run_studio(parsed_args)
        else:
            parser.print_help()
            return ExitCode.INVALID_ARGUMENTS

    except CliError as ce:
        TerminalFormatter.print_error("CLI Command", parsed_args.command, ce.message, is_json=getattr(parsed_args, "json", False))
        return ce.exit_code
    except Exception as exc:
        TerminalFormatter.print_error("CLI Command", parsed_args.command, str(exc), is_json=getattr(parsed_args, "json", False))
        return ExitCode.UNEXPECTED_ERROR


if __name__ == "__main__":
    sys.exit(main())
