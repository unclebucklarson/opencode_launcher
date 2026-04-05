# Copyright (c) 2026 csb (unclebucklarson)
# Licensed under the MIT License - see LICENSE file for details

"""Allow running as: python3 -m opencode_launcher"""
from .cli import main
import sys

if __name__ == "__main__":
    sys.exit(main() or 0)
