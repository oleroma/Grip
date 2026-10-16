#!/usr/bin/env python3
"""Reload every STL part of OrcaSlicer 3MF projects from disk, in one run.

Usage:
    python orca_reload.py PROJECT.3mf [MORE.3mf | FOLDER ...] [options]

The code lives in the Orca Reload Blender extension, extensions/orca_reload/reload3mf.py; this runs it without
Blender. Only the Python standard library is needed (Python 3.8+). See README.md next to this file.
"""

import os
import sys

sys.dont_write_bytecode = True  # no __pycache__ inside the extension folder
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir,
                                "extensions", "orca_reload"))

from reload3mf import *  # noqa: E402,F401,F403
from reload3mf import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
