"""
Command-line interface entry points for scanDOC.
"""

from scandoc.cli.main import main
from scandoc.cli.parser import create_parser

__all__ = ["main", "create_parser"]

