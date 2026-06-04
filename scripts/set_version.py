#!/usr/bin/env python3

import re
import sys
from pathlib import Path

VERSION_PATTERN = re.compile(r'(__version__\s*=\s*")([^"]+)(")')
SETUP_VERSION_PATTERN = re.compile(r'(version\s*=\s*")([^"]+)(")')


def replace_version(path, pattern, version):
    text = path.read_text(encoding="utf-8")
    updated, count = pattern.subn(rf"\g<1>{version}\g<3>", text, count=1)
    if count != 1:
        raise RuntimeError(
            f"Expected to update exactly one version in {path}"
        )
    path.write_text(updated, encoding="utf-8")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: scripts/set_version.py <version>")

    version = sys.argv[1]
    replace_version(Path("setup.py"), SETUP_VERSION_PATTERN, version)
    replace_version(
        Path("pylotoncycle/__init__.py"), VERSION_PATTERN, version
    )


if __name__ == "__main__":
    main()
