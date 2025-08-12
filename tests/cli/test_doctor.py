import sys
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from cli.main import app  # noqa: E402

runner = CliRunner()


def test_doctor_runs_and_outputs_tables(monkeypatch, tmp_path: Path):
    # Redirecionar diretórios para tmp para evitar permissões reais
    from core import config as core_config

    original_cm = core_config.ConfigurationManager

    class DummyCM(core_config.ConfigurationManager):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self._config.base_directory = str(tmp_path)
            self._config.downloads_directory = str(tmp_path / "downloads")
            self._config.logs_directory = str(tmp_path / "logs")
            self._config.cache_directory = str(tmp_path / "cache")
            self._config.backups_directory = str(tmp_path / "backups")

    monkeypatch.setattr(core_config, "ConfigurationManager", DummyCM)

    result = runner.invoke(app, ["doctor"], catch_exceptions=False)
    # Pode falhar se rede indisponível; aceitamos 0 ou 1
    assert result.exit_code in (0, 1)
    out = result.stdout.lower()
    assert "informações do sistema" in out or "system information" in out
    assert "diretórios críticos" in out or "directories" in out
    assert "espaço em disco" in out or "disk" in out
