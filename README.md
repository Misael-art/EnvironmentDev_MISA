# Environment Dev Deep Evaluation

Ferramenta CLI/TUI para gerenciar componentes de desenvolvimento com segurança RF005 (hash obrigatório) e detecção unificada do ambiente.

## Requisitos
- Windows 10/11, PowerShell 7+
- Python 3.10+

## Instalação e uso
- CLI: `python mecha.py --help`
- TUI: `python tui/main.py`

## Comandos principais
- `list-components`:
  - Lista componentes com coluna de Confiança (cores/ícones) enriquecida pela UnifiedDetectionEngine (Registry + CLI + sinônimos)
  - Filtros: `--category`, `--installed`, `--available`
- `install <componente>`:
  - Baixa, verifica SHA256 e instala (RF005 estrito)
  - `pip` via wheel previamente baixada e verificada; instalação offline `--no-index`
- `install-many <comp1> <comp2> ...`:
  - Resolve dependências (instala deps antes) e aplica RF005 por item
  - Flags: `--continue/--no-continue`, `--dry-run`
- `uninstall <componente>`: tenta via pip/winget/choco
- `backup`/`restore`: exporta e restaura `components/*.yaml`
- `update --hashes-only`: executa o HashUpdater para atualizar hashes pendentes
- `analyze-gaps`: compara componentes esperados vs ambiente (UnifiedDetectionEngine)
- `doctor`: diagnóstico avançado (rede/DNS/SSL, clock skew, disco, diretórios críticos) com códigos de saída

## Segurança (RF005)
Consulte `SECURITY.md`. Hash é obrigatório para métodos com download e para `pip` (wheel verificada e instalação offline). Placeholders são rejeitados.

## Próximos passos
- Curar URLs em `components/*.yaml` para links oficiais estáveis; preencher `alternative_urls` quando aplicável
- Rodar o atualizador de hashes com limites adequados:
  ```bash
  python scripts/hash_updater.py --components-dir components --max-size-mb 700 --log-level INFO
  ```
- Manter testes “verdes” (`pytest -q`) e commits semânticos

## Testes
- Executar: `pytest -q`

## Estado das Categorias (detecção)

| Categoria | Esperados | Presentes | Ausentes |
|---|---:|---:|---:|

