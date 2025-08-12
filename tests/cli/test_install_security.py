import os
import sys
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

# Ajuste de path para importar a CLI
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from cli.main import app  # noqa: E402


runner = CliRunner()


def _write_yaml(tmp_components: Path, name: str, content: str) -> Path:
    tmp_components.mkdir(parents=True, exist_ok=True)
    file_path = tmp_components / f"{name}.yaml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture()
def temp_env(monkeypatch, tmp_path: Path):
    # Criar estrutura mínima de diretórios no diretório temporário
    (tmp_path / "components").mkdir(parents=True, exist_ok=True)
    (tmp_path / "downloads").mkdir(parents=True, exist_ok=True)
    (tmp_path / "logs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "cache").mkdir(parents=True, exist_ok=True)
    (tmp_path / "backups").mkdir(parents=True, exist_ok=True)

    # Chdir para o tmp_path para que a CLI use ./components
    monkeypatch.chdir(tmp_path)

    # Garantir que a CLI trabalhe com esse CWD
    yield tmp_path


def test_install_rejects_placeholder_hash(temp_env: Path):
    # Componente EXE com hash placeholder deve falhar (RF005)
    yaml_text = (
        "test_tool:\n"
        "  category: Runtimes\n"
        "  description: Test tool\n"
        "  download_url: https://example.com/test.exe\n"
        "  install_method: exe\n"
        "  hash: HASH_NEEDS_UPDATE\n"
    )
    _write_yaml(temp_env / "components", "test_tool", yaml_text)

    result = runner.invoke(app, ["install", "test_tool"], catch_exceptions=False)

    assert result.exit_code == 2
    assert "hash obrigatório ausente ou pendente" in result.stdout.lower()


def test_install_exe_success_with_hash_and_mock_download_and_silent_installer(monkeypatch, temp_env: Path):
    # Componente EXE com hash válido; mockar download/verificação e subprocess.run
    valid_hash = "a" * 64
    yaml_text = (
        "mytool:\n"
        "  category: Runtimes\n"
        "  description: My Tool\n"
        "  download_url: https://example.com/mytool.exe\n"
        "  install_method: exe\n"
        f"  hash: {valid_hash}\n"
        "  install_args: /S\n"
    )
    _write_yaml(temp_env / "components", "mytool", yaml_text)

    class DummyResult:
        def __init__(self):
            self.success = True
            self.errors = []
            self.message = "ok"

    # Mock do download/verificação
    from cli import main as cli_main

    def fake_download_with_fallback(**kwargs: Any):
        # Criar arquivo destino vazio, pois a CLI imprime caminho
        dest = Path(kwargs.get("destination"))
        dest.write_bytes(b"dummy")
        return DummyResult()

    monkeypatch.setattr(cli_main.NetworkOperations, "download_with_fallback", staticmethod(lambda **kw: fake_download_with_fallback(**kw)))

    # Mock do subprocess.run para simulador silencioso
    class DummyCompleted:
        def __init__(self, returncode=0, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    monkeypatch.setattr(cli_main.subprocess, "run", lambda *a, **k: DummyCompleted(0, "ok", ""))

    result = runner.invoke(app, ["install", "mytool"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "instalação concluída" in result.stdout.lower()


def test_install_pip_offline_with_provided_wheel_and_hash(monkeypatch, temp_env: Path):
    # pip com wheel fornecida (download_url .whl) e hash válido; mockar download e pip install
    valid_content = b"wheel-bytes"
    import hashlib as _hashlib
    valid_hash = _hashlib.sha256(valid_content).hexdigest()

    yaml_text = (
        "mypkg:\n"
        "  category: AI Tools\n"
        "  description: Package\n"
        "  install_method: pip\n"
        "  install_args: mypkg\n"
        "  pypi_name: mypkg\n"
        "  version: 1.0.0\n"
        f"  hash: {valid_hash}\n"
        "  download_url: https://files.pythonhosted.org/packages/m/mypkg-1.0.0-py3-none-any.whl\n"
    )
    _write_yaml(temp_env / "components", "mypkg", yaml_text)

    from cli import main as cli_main

    class DummyResult:
        def __init__(self):
            self.success = True
            self.errors = []
            self.message = "ok"

    def fake_download_with_fallback(**kwargs: Any):
        dest = Path(kwargs.get("destination"))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(valid_content)
        return DummyResult()

    monkeypatch.setattr(cli_main.NetworkOperations, "download_with_fallback", staticmethod(lambda **kw: fake_download_with_fallback(**kw)))

    class DummyCompleted:
        def __init__(self, returncode=0, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    # pip install offline
    monkeypatch.setattr(cli_main.subprocess, "run", lambda *a, **k: DummyCompleted(0, "ok", ""))

    result = runner.invoke(app, ["install", "mypkg"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "pacote pip instalado offline" in result.stdout.lower()
