# src/utils.py
import re

def sanitize_filename(name: str) -> str:
    """Sanitizes a string for use as a filename."""
    safe = re.sub(r"[^\w\-.]", "_", str(name))
    return safe[:200]