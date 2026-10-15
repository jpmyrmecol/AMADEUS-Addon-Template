# Copyright (C) 2026 Yusuke Notomi
# SPDX-License-Identifier: 0BSD

"""Build an installable ZIP without importing AMADEUS or executing the add-on."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.parse
import zipfile

# Add your own application files here. Do not package a virtual environment.
PAYLOAD = ("addon.json", "app.py", "reader.py", "LICENSE")


def build(source: Path, output_dir: Path, download_url: str | None = None) -> Path:
    source = Path(source)
    manifest = json.loads((source / "addon.json").read_text(encoding="utf-8"))
    # Validate filenames locally. AMADEUS separately validates the complete package.
    import re
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+", manifest["id"]):
        raise ValueError("Change id to a lowercase qualified name.")
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", manifest["version"]):
        raise ValueError("Use MAJOR.MINOR.PATCH for the version.")
    if download_url:
        parsed = urllib.parse.urlsplit(download_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            raise ValueError("download_url must use HTTPS without credentials or fragments.")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"{manifest['id']}-{manifest['version']}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for name in PAYLOAD:
            path = source / name
            if path.is_symlink():
                raise ValueError(f"Do not package symlinks: {name}")
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            target.writestr(info, path.read_bytes())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output_dir / f"{archive.name}.sha256").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    if download_url:
        update = {"manifest_version": 1, "id": manifest["id"], "version": manifest["version"],
                  "url": download_url, "sha256": digest}
        (output_dir / "update.json").write_text(json.dumps(update, indent=2) + "\n", encoding="utf-8")
    return archive


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    parser.add_argument("--download-url", help="Final HTTPS URL of this ZIP, to generate update.json")
    args = parser.parse_args()
    print(build(Path(__file__).resolve().parent, args.output_dir, args.download_url))


if __name__ == "__main__":
    main()
