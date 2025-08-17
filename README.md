# Environment Dev Deep Evaluation

Ferramenta CLI/TUI para gerenciar componentes de desenvolvimento com segurança RF005 (hash obrigatório) e detecção unificada do ambiente.

## Requisitos
- Windows 10/11, PowerShell 7+
- Python 3.10+

## Instalação e uso
- CLI: `python -m cli.main --help` (ponto de entrada principal)
- TUI: `python tui/main.py` (requer `pip install textual`)

> Documento diretor: veja `docs/PLANO_MESTRE.md` (fonte única da verdade para requisitos, UX/CX, segurança RF005, arquitetura, qualidade e processo). Qualquer mudança funcional deve atualizar esse plano.

## Comandos principais
**Use `python -m cli.main [comando]` como ponto de entrada:**
- `list-components`:
  - Lista componentes com coluna de Confiança (cores/ícones) enriquecida pela UnifiedDetectionEngine (Registry + CLI + sinônimos)
  - Filtros: `--category`, `--installed`, `--available`, `--json`
- `install <componente>`:
  - Baixa, verifica SHA256 e instala (RF005 estrito)
  - `pip` via wheel previamente baixada e verificada; instalação offline `--no-index`
  - Flags: `--dry-run`
- `install-many <comp1> <comp2> ...`:
  - Resolve dependências (instala deps antes) e aplica RF005 por item
  - Flags: `--continue/--no-continue`, `--dry-run`, `--json`
- `uninstall <componente>`: tenta via pip/winget/choco
- `backup`/`restore`: exporta e restaura `components/*.yaml`
- `update --hashes-only`: executa o HashUpdater para atualizar hashes pendentes
- `analyze-gaps`: compara componentes esperados vs ambiente (UnifiedDetectionEngine)
  - Filtros: `--category`, `--name`, `--json`
- `doctor`: diagnóstico avançado (rede/DNS/SSL, clock skew, disco, diretórios críticos) com códigos de saída
  - Verificações específicas para Retro Games (drivers, runtimes) e Vibe Code/IA (APIs, CUDA, espaço em disco)
- `report`: gera relatório avançado (JSON/HTML) do ambiente e, opcionalmente, plugins
  - JSON: `python -m cli.main report -o report.json`
  - HTML: `python -m cli.main report -o report.html --format html`
  - Com plugins: `--include-plugins --plugins-dir diretorio`
- `profiles`: gerencia perfis de componentes
  - `profiles create`: cria novos perfis
  - `profiles list`: lista perfis disponíveis
  - `profiles show`: mostra detalhes de um perfil
  - `profiles delete`: exclui um perfil
  - `profiles export`/`profiles import`: exporta/importa perfis

### Códigos de saída (resumo)
- install/install-many: 0 sucesso; 2 RF005; 3 download/hash; 4 instalação; demais 1.
- analyze-gaps: 0 sucesso; 2 lacunas com `--fail-on-missing`.
- backup/restore/update/uninstall/doctor: 0 sucesso; 1 erro.

## Segurança (RF005)
Consulte `SECURITY.md` e `docs/PLANO_MESTRE.md`. Hash é obrigatório para métodos com download e para `pip` (wheel verificada e instalação offline). Placeholders são rejeitados.

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

