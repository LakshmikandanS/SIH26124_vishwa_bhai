"""
RouteSense Urban AI Fleet Intelligence — Main CLI Entrypoint
============================================================
Delegates to edge.main to run the Edge Transit Multi-Model Node.

Usage:
    python main.py --source test2.mp4 --show-video --verbose
    python main.py --source edge/assets/test_dashcam.mp4 --show-video --verbose
"""

import sys
import os

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from edge.main import main

if __name__ == "__main__":
    main()
