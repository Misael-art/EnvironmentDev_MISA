# Environment Dev Deep Evaluation

Ferramenta CLI/TUI para gerenciar componentes de desenvolvimento com segurança RF005 (hash obrigatório) e detecção unificada do ambiente.

## Requisitos
- Windows 10/11, PowerShell 7+
- Python 3.10+

## Instalação e uso
- CLI: `python mecha.py --help`
- TUI: `python tui/main.py`

## Comandos principais
- `list-components`: lista componentes e mostra coluna de Confiança (cores/ícones) baseada na UnifiedDetectionEngine
- `install <componente>`: baixa, verifica SHA256 e instala; pip via wheel offline verificada (`--no-index`)
- `uninstall <componente>`: tenta via pip/winget/choco
- `backup`/`restore`: exporta e restaura `components/*.yaml`
- `update --hashes-only`: executa o HashUpdater para atualizar hashes pendentes
- `analyze-gaps`: compara componentes esperados vs ambiente (UnifiedDetectionEngine)

## Segurança (RF005)
Consulte `SECURITY.md`. Hash é obrigatório para métodos com download e para `pip` (wheel verificada e instalação offline). Placeholders são rejeitados.

## Próximos passos
- Curar URLs em `components/*.yaml` para links oficiais estáveis; preencher `alternative_urls` quando aplicável
- Rodar o atualizador de hashes com limites adequados: `python scripts/hash_updater.py --components-dir components --max-size-mb 700 --log-level INFO`
- Manter testes “verdes” (`pytest -q`) e commits semânticos

## Testes
- Executar: `pytest -q`
