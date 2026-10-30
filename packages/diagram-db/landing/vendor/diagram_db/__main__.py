"""Permite ejecutar ``python -m diagram_db``."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
