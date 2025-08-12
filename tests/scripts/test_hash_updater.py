import sys
from pathlib import Path
from typing import Tuple

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.hash_updater import HashUpdater  # noqa: E402
from core.config import ConfigurationManager  # noqa: E402


@pytest.fixture()
def updater(tmp_path: Path):
    cfg = ConfigurationManager()
    h = HashUpdater(cfg)
    init = h.initialize()
    assert init.success
    yield h
    h.cleanup()


def test_file_scheme_download_and_hash_calculation(updater: HashUpdater, tmp_path: Path):
    # Criar arquivo local e consumir via file://
    local_file = tmp_path / "artifact.bin"
    content = b"ABCDEF" * 100
    local_file.write_bytes(content)

    data = {
        "tool": {
            "description": "Local file test",
            "download_url": f"file://{local_file.as_posix()}",
            "hash": "HASH_NEEDS_UPDATE",
        }
    }

    # find_pending_hashes
    pending = updater.find_pending_hashes(data)
    assert pending and pending[0][0] == "tool"

    # Fazer o download
    blob, err = updater.download_file(data["tool"]["download_url"], max_size_mb=10)
    assert err is None
    assert blob == content

    # Calcular SHA256
    digest = updater.calculate_sha256(blob)
    assert len(digest) == 64

    # Atualizar
    ok = updater.update_component_hash(data, "tool", digest)
    assert ok
    assert data["tool"]["hash"] == digest


def test_alternative_urls_on_failure(monkeypatch, updater: HashUpdater, tmp_path: Path):
    # Simular falha na URL primária e sucesso em alternativa
    primary = "https://invalid.invalid/file.bin"
    alt_file = tmp_path / "alt.bin"
    alt_content = b"OK" * 10
    alt_file.write_bytes(alt_content)
    alt = f"file://{alt_file.as_posix()}"

    # Montar YAML em memória
    data = {
        "comp": {
            "description": "Alt test",
            "download_url": primary,
            "alternative_urls": [alt],
            "hash": "HASH_NEEDS_UPDATE",
        }
    }

    # Interceptar download_file: primeira chamada para primary falha, depois delegar para implementação real
    calls = {"count": 0}
    real_download = updater.download_file

    def fake_download(url: str, max_size_mb: int = 500) -> Tuple[bytes, str]:  # type: ignore
        calls["count"] += 1
        if url == primary:
            return None, "Download error simulated"
        return real_download(url, max_size_mb=max_size_mb)

    monkeypatch.setattr(updater, "download_file", fake_download)

    # Processar arquivo sintético salvo no disco
    file_path = tmp_path / "components.yaml"
    import yaml
    file_path.write_text(yaml.dump(data), encoding="utf-8")

    res = updater.process_file(file_path, dry_run=False, max_size_mb=50)
    assert res.success
    assert res.data.get("updated_count") == 1


def test_size_limit_enforced(updater: HashUpdater, tmp_path: Path):
    # Criar arquivo local maior que limite e garantir bloqueio
    big_file = tmp_path / "big.bin"
    big_file.write_bytes(b"X" * (2 * 1024 * 1024))  # 2MB
    url = f"file://{big_file.as_posix()}"

    blob, err = updater.download_file(url, max_size_mb=1)
    assert blob is None
    assert "too large" in (err or "").lower()
