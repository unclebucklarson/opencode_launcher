"""Allow running as: python3 -m opencode_launcher"""
from .cli import main
import sys

if __name__ == "__main__":
    sys.exit(main() or 0)
