"""
__main__.py entry point for python -m scandoc.cli invocation.
"""

import sys
from scandoc.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
