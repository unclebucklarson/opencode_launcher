"""Setup script for OpenCode Launcher."""
from setuptools import setup, find_packages
from pathlib import Path

README = Path(__file__).parent / "README.md"
long_description = README.read_text() if README.exists() else ""

setup(
    name="opencode-launcher",
    version="1.0.0",
    description="CLI tool for launching and managing OpenCode instances",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "questionary>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "oc=opencode_launcher.cli:main",
        ],
    },
)
