#!/usr/bin/env python3
"""
URL Checker for components/*.yaml

Varre download_url e alternative_urls, valida acessibilidade (HEAD/GET),
registra status_code, content-type e URL final (após redirects).
Gera relatório em logs/url_audit.json.
"""

from __future__ import annotations

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml
import requests

ROOT = Path(__file__).resolve().parents[1]
COMP_DIR = ROOT / "components"
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = LOGS_DIR / "url_audit.json"


def check_url(url: str, timeout: int = 10) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "url": url,
        "ok": False,
        "status": None,
        "final_url": None,
        "content_type": None,
        "error": None,
    }
    try:
        # HEAD best-effort
        try:
            rh = requests.head(url, allow_redirects=True, timeout=timeout)
            entry["status"] = rh.status_code
            entry["final_url"] = getattr(rh, "url", url)
            entry["content_type"] = (rh.headers.get("content-type") or "").lower()
            if rh.ok:
                entry["ok"] = True
                return entry
        except Exception as he:
            entry["error"] = f"HEAD: {he}"

        # Fallback GET (stream, sem baixar corpo inteiro)
        with requests.get(url, stream=True, allow_redirects=True, timeout=timeout) as rg:
            entry["status"] = rg.status_code
            entry["final_url"] = getattr(rg, "url", url)
            entry["content_type"] = (rg.headers.get("content-type") or "").lower()
            entry["ok"] = bool(rg.ok)
            return entry
    except Exception as e:
        entry["error"] = str(e)
        return entry


def main() -> int:
    results: Dict[str, Any] = {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "components": {}}

    for yml in sorted(COMP_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(yml.read_text(encoding="utf-8"))
        except Exception as e:
            results["components"][yml.name] = {"error": f"YAML parse error: {e}"}
            continue

        if not isinstance(data, dict):
            continue

        comp_report: Dict[str, Any] = {}
        for name, comp in data.items():
            if not isinstance(comp, dict):
                continue
            urls = []
            if comp.get("download_url"):
                urls.append(comp["download_url"])
            for au in (comp.get("alternative_urls") or []):
                urls.append(au)
            url_checks = [check_url(u) for u in urls]
            comp_report[name] = url_checks

        if comp_report:
            results["components"][yml.name] = comp_report

    OUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"URL audit written to {OUT_PATH}")
    # Return non-zero if any URL clearly failed
    any_fail = False
    for file_report in results.get("components", {}).values():
        if isinstance(file_report, dict):
            for arr in file_report.values():
                if isinstance(arr, list):
                    for e in arr:
                        if not e.get("ok"):
                            any_fail = True
                            break
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())


