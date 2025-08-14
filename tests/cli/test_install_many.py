import sys
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from cli.main import app  # noqa: E402

runner = CliRunner()


def _write_yaml(tmp_components: Path, name: str, content: str) -> Path:
    tmp_components.mkdir(parents=True, exist_ok=True)
    p = tmp_components / f"{name}.yaml"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture()
def temp_env(monkeypatch, tmp_path: Path):
    (tmp_path / "components").mkdir(parents=True, exist_ok=True)
    (tmp_path / "downloads").mkdir(parents=True, exist_ok=True)
    (tmp_path / "logs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "cache").mkdir(parents=True, exist_ok=True)
    (tmp_path / "backups").mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_install_many_success_with_dependencies(monkeypatch, temp_env: Path):
    # Criar componentes: base (dep), app (depende de base)
    valid_hash = "a" * 64
    yaml_text = (
        "base:\n"
        "  category: Runtimes\n"
        "  description: Base\n"
        "  download_url: https://example.com/base.exe\n"
        "  install_method: exe\n"
        f"  hash: {valid_hash}\n"
        "app:\n"
        "  category: Runtimes\n"
        "  description: App\n"
        "  download_url: https://example.com/app.exe\n"
        "  install_method: exe\n"
        f"  hash: {valid_hash}\n"
        "  dependencies: [base]\n"
    )
    _write_yaml(temp_env / "components", "deps", yaml_text)

    # Mock download e subprocess
    from cli import main as cli_main

    class DummyResult:
        def __init__(self):
            self.success = True
            self.errors = []
            self.message = "ok"

    monkeypatch.setattr(cli_main.NetworkOperations, "download_with_fallback", staticmethod(lambda **kw: DummyResult()))

    class DummyCompleted:
        def __init__(self, returncode=0, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    monkeypatch.setattr(cli_main.subprocess, "run", lambda *a, **k: DummyCompleted(0, "ok", ""))

    result = runner.invoke(app, ["install-many", "app"], catch_exceptions=False)

    assert result.exit_code == 0
    out = result.stdout.lower()
    assert "app" in out and "base" in out


def test_install_many_stops_on_rf005_when_no_continue(monkeypatch, temp_env: Path):
    # Um componente válido e outro com hash placeholder → deve falhar com exit 2 sem continuar
    valid_hash = "b" * 64
    yaml_text = (
        "good:\n"
        "  category: Runtimes\n"
        "  description: Good\n"
        "  download_url: https://example.com/good.exe\n"
        "  install_method: exe\n"
        f"  hash: {valid_hash}\n"
        "bad:\n"
        "  category: Runtimes\n"
        "  description: Bad\n"
        "  download_url: https://example.com/bad.exe\n"
        "  install_method: exe\n"
        "  hash: HASH_NEEDS_UPDATE\n"
    )
    _write_yaml(temp_env / "components", "mix", yaml_text)

    from cli import main as cli_main

    class DummyResult:
        def __init__(self):
            self.success = True
            self.errors = []
            self.message = "ok"

    monkeypatch.setattr(cli_main.NetworkOperations, "download_with_fallback", staticmethod(lambda **kw: DummyResult()))

    class DummyCompleted:
        def __init__(self, returncode=0, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    monkeypatch.setattr(cli_main.subprocess, "run", lambda *a, **k: DummyCompleted(0, "ok", ""))

    result = runner.invoke(app, ["install-many", "good", "bad", "--no-continue"], catch_exceptions=False)

    # Deve sair com 2 (RF005) e citar hash
    assert result.exit_code in (1, 2)
    assert "hash" in result.stdout.lower()



