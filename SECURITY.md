# Política de Segurança

Este projeto adota uma postura de segurança proativa e obrigatória para operações de instalação e atualização de artefatos.

## RF005 – Verificação de Integridade Obrigatória (SHA256)

- Toda instalação que envolva download de artefatos (EXE/MSI/ZIP/Wheel) exige hash SHA256 válido e verificado antes da execução.
- Placeholders não são permitidos: `HASH_NEEDS_UPDATE` e `HASH_PENDENTE_VERIFICACAO` são rejeitados pelos schemas e pela CLI.
- Para `pip`, a política é estrita: o pacote deve ser instalado a partir de uma wheel previamente baixada e verificada (instalação offline via `--no-index`). O hash da wheel é obrigatório.

### Exemplo pip (offline, seguro)

```bash
# Baixar wheel previamente (ou use download_url .whl com alternative_urls)
python -m pip download --only-binary=:all: --dest downloads/.dist somepkg==1.2.3

# Validar SHA256 com a CLI (RF005)
python -m cli.main install somepkg

# Internamente: a CLI verificará o SHA256 e instalará com:
# python -m pip install --no-index --find-links downloads/.dist somepkg-1.2.3-*.whl
```

## Rede e Fallbacks

- O download é feito com streaming, timeout configurável e retries com backoff exponencial.
- `HEAD` é best-effort e não falha o fluxo; quando presente, o tamanho é validado antes de baixar.
- URLs alternativas (`alternative_urls`) são suportadas como fallback. Também suportamos `file://` para artefatos locais.
- Limites de tamanho por componente e timeouts consistentes são aplicados para evitar abusos e travamentos.

### Heurística de Content-Type no HashUpdater
- Respostas textuais (text/html, application/json, etc.) são rejeitadas quando a URL não aponta para extensão de artefato conhecida (`.exe`, `.msi`, `.zip`, `.7z`, `.whl`). Evita gerar hashes de páginas HTML.

## Tratamento de Erros e Auditoria

- Todas as operações retornam `OperationResult(success: bool, errors: List[str], data: Any|None)` com mensagens claras: o que falhou, por que falhou e como corrigir.
- Logs usam níveis apropriados: `INFO` (progresso), `WARNING` (recuperáveis), `ERROR` (falhas).

## Como corrigir hashes pendentes

Use o atualizador de hashes com limites de tamanho e nível de log ajustáveis:

```bash
python scripts/hash_updater.py --components-dir components --max-size-mb 700 --log-level INFO
```

Atualize os arquivos em `components/*.yaml` e valide executando a suíte de testes.


