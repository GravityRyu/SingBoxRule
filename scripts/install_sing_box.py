#!/usr/bin/env python3
"""Install the pinned sing-box release used by this GitHub Actions workflow."""
from __future__ import annotations
import argparse
import shutil
import stat
import tarfile
import tempfile
import urllib.request
from pathlib import Path

VERSION = "1.12.12"
URL = "https://github.com/SagerNet/sing-box/releases/download/v{0}/sing-box-{0}-linux-amd64.tar.gz"

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        archive = Path(temporary) / "sing-box.tar.gz"
        request = urllib.request.Request(URL.format(VERSION), headers={"User-Agent": "rule-set-builder"})
        with urllib.request.urlopen(request, timeout=120) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output)
        with tarfile.open(archive, "r:gz") as bundle:
            member = next((item for item in bundle.getmembers() if item.isfile() and item.name.endswith("/sing-box")), None)
            if member is None:
                raise RuntimeError("sing-box binary not found in the release archive")
            source = bundle.extractfile(member)
            if source is None:
                raise RuntimeError("Unable to extract sing-box")
            binary = arguments.destination / "sing-box"
            with source, binary.open("wb") as output:
                shutil.copyfileobj(source, output)
            with binary.open("rb") as output:
                if output.read(4) != b"\x7fELF":
                    raise RuntimeError("Downloaded sing-box is not a Linux ELF executable")
            binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    print(f"Installed sing-box {VERSION}")

if __name__ == "__main__":
    main()
