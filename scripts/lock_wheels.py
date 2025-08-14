#!/usr/bin/env python3
"""
Gera um lockfile de wheels Python com seus hashes para instalação offline segura (RF005).

Uso:
  python scripts/lock_wheels.py --requirements requirements.txt --output wheels.lock.json --dest downloads/.dist

Regras:
- Não realiza instalação. Apenas baixa wheels com pip download e computa SHA256.
- Saída inclui nome do arquivo, sha256, tamanho em bytes e timestamp.
"""

import argparse
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from cli.utils import FileOperations


def compute_sha256(path: Path) -> str:
    return FileOperations.calculate_file_hash(path) or ""


def pip_download(requirements: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    cmd = [
        "python",
        "-m",
        "pip",
        "download",
        "--only-binary=:all:",
        "--dest",
        str(dest),
        "-r",
        str(requirements),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0:
        raise RuntimeError(f"pip download failed: {proc.stderr}")


def build_lockfile(dest: Path) -> Dict:
    entries: List[Dict] = []
    for whl in dest.glob("*.whl"):
        entries.append(
            {
                "filename": whl.name,
                "sha256": compute_sha256(whl),
                "bytes": whl.stat().st_size,
            }
        )
    return {
        "generated_at": datetime.now().isoformat(),
        "directory": str(dest),
        "wheels": entries,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate wheels lockfile with hashes")
    parser.add_argument("--requirements", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--dest", default="downloads/.dist")
    args = parser.parse_args()

    req = Path(args.requirements)
    out = Path(args.output)
    dest = Path(args.dest)

    pip_download(req, dest)
    data = build_lockfile(dest)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"✅ Lockfile gerado: {out}")


if __name__ == "__main__":
    main()


