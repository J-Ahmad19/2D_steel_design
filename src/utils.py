import re

def sanitize_filename(name: str) -> str:
    """Removes illegal characters from filenames."""
    # Replace slashes and other bad chars with underscores
    s = str(name).strip().replace('/', '-').replace('\\', '-')
    return re.sub(r'[^\w\-.]', '_', s)