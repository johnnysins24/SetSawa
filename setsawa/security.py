"""Local release-content scan. Dependency vulnerabilities are checked by pip-audit."""
import re
from pathlib import Path

PATTERNS = [
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{60,}"),
    re.compile(rb"AKIA[A-Z0-9]{16}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{32,}"),
    re.compile(rb"https?://[^\s/:]+:[^\s/@]+@"),
    re.compile(rb"(?i)[a-z]:[\\/]+Users[\\/]+[A-Za-z0-9_~-]+[\\/]"),
]


def scan_files(files):
    checked = 0
    for file in files:
        file = Path(file)
        if file.is_symlink() or file.name.startswith(".env") or file.suffix.lower() in (".pem", ".key", ".pfx"):
            raise ValueError("Forbidden release file: " + file.name)
        data = file.read_bytes()
        if any(p.search(data) for p in PATTERNS):
            # Never print matched secret content.
            raise ValueError("Potential secret in release file: " + file.name)
        checked += 1
    return checked
