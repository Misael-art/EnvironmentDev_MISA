import sys
from pathlib import Path
from typing import List

import pytest
from typer.testing import CliRunner

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from cli.main import app  # noqa: E402

runner = CliRunner()


@pytest.fixture()
def temp_env(monkeypatch, tmp_path: Path):
    (tmp_path / "components").mkdir(parents=True, exist_ok=True)
    (tmp_path / "downloads").mkdir(parents=True, exist_ok=True)
    (tmp_path / "logs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "cache").mkdir(parents=True, exist_ok=True)
    (tmp_path / "backups").mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)
    yield tmp_path


def _write_yaml(tmp_components: Path, content: str) -> Path:
    file_path = tmp_components / "runtimes.yaml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_analyze_gaps_with_synonyms_cli_detection(monkeypatch, temp_env: Path):
    # Montar componentes que devem casar com sinônimos/deteção CLI
    yaml_text = (
        "Node.js:\n"
        "  category: Runtimes\n"
        "  description: Node.js runtime\n"
        "  install_method: manual\n"
        "Python:\n"
        "  category: Runtimes\n"
        "  description: Python runtime\n"
        "  install_method: manual\n"
        "CMake:\n"
        "  category: Build Tools\n"
        "  description: CMake\n"
        "  install_method: manual\n"
    )
    _write_yaml(temp_env / "components", yaml_text)

    # Mock da UnifiedDetectionEngine: detect_essential_runtimes e scan_registry_installations
    import detection.unified_engine as ue

    class DummyRuntimeResult:
        def __init__(self, name: str):
            self.runtime_name = name
            self.detected = True
            self.version = "1.0.0"
            self.install_path = ""
            self.environment_variables = {}
            self.validation_commands = []
            self.validation_results = {}
            from detection.interfaces import DetectionMethod, DetectionConfidence
            self.detection_method = DetectionMethod.COMMAND_LINE
            self.confidence = DetectionConfidence.HIGH

    class DummyEngine(ue.UnifiedDetectionEngine):
        def initialize(self) -> None:  # override sem erro
            return None

        def scan_registry_installations(self) -> List:  # type: ignore
            # Vazios para forçar CLI
            return []

        def detect_essential_runtimes(self):  # type: ignore
            return [DummyRuntimeResult("Node.js"), DummyRuntimeResult("Python")]

    monkeypatch.setattr(ue, "UnifiedDetectionEngine", DummyEngine)

    res = runner.invoke(app, ["analyze-gaps", "--no-fail-on-missing"], catch_exceptions=False)
    assert res.exit_code == 0
    out = res.stdout.lower()
    # Deve marcar Node.js e Python como presentes
    assert "presente" in out
    assert "node.js" in out or "node" in out
    assert "python" in out
