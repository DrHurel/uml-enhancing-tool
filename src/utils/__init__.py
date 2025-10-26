"""Utility functions and helpers."""

import os
from pathlib import Path


def ensure_dir(path: str) -> str:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory

    Returns:
        The path to the directory
    """
    os.makedirs(path, exist_ok=True)
    return path


def read_file(path: str) -> str:
    """
    Read the contents of a file.

    Args:
        path: Path to the file

    Returns:
        File contents as string
    """
    with open(path, "r") as f:
        return f.read()


def write_file(path: str, content: str):
    """
    Write content to a file.

    Args:
        path: Path to the file
        content: Content to write
    """
    ensure_dir(os.path.dirname(path))
    with open(path, "w") as f:
        f.write(content)


def get_timestamp() -> str:
    """
    Get current timestamp as formatted string.

    Returns:
        Timestamp string in format YYYYMMDD_HHMMSS
    """
    from datetime import datetime

    return datetime.now().strftime("%Y%m%d_%H%M%S")
