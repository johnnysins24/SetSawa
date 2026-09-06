"""Verify downloaded release checksums and every ZIP member without extracting."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def manifest(text):
    result = {}
    for line in text.splitlines():
        expected, name = line.split("  ", 1)
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name or name in result:
            raise ValueError("Unsafe or duplicate manifest path")
        if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            raise ValueError("Invalid SHA-256")
        result[name] = expected
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    folder = args.directory.resolve()
    release = manifest((folder / "release-checksums.sha256").read_text(encoding="utf-8"))
    for name, expected in release.items():
        target = (folder / name).resolve()
        if not target.is_relative_to(folder) or digest(target.read_bytes()) != expected:
            raise ValueError("Release checksum mismatch: " + name)
    with zipfile.ZipFile(folder / "setsawa-v1.0.0.zip") as archive:
        members = archive.infolist()
        if sum(m.file_size for m in members) > 200_000_000:
            raise ValueError("Archive exceeds review size limit")
        checks = manifest(archive.read("checksums.sha256").decode("utf-8"))
        if len(members) != len(checks) + 1 or set(archive.namelist()) != set(checks) | {"checksums.sha256"}:
            raise ValueError("Unexpected or duplicate archive members")
        for name, expected in checks.items():
            if digest(archive.read(name)) != expected:
                raise ValueError("Archive checksum mismatch: " + name)
        if archive.read("checksums.sha256") != (folder / "checksums.sha256").read_bytes():
            raise ValueError("Inner and outer manifests differ")
        if sum(name.startswith("data/raw/pdfs/") and name.endswith(".pdf") for name in checks) != 77:
            raise ValueError("Expected 77 source PDFs")
    print(f"Verified {len(release)} release assets and {len(checks)} archive members")


if __name__ == "__main__":
    main()
