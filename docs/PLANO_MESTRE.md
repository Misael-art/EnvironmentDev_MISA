## Plano Mestre — Environment Dev Deep Evaluation

Este documento é a fonte única da verdade para decisões de produto, UX/CX, arquitetura, segurança, qualidade e processo de mudança. Toda alteração funcional deve atualizar este plano no mesmo commit/PR.

## Visão e Objetivos
- Gerenciar um ambiente de desenvolvimento de forma segura (RF005), auditável e automatizável.
- Metas mensuráveis por release (ex.: v2.0: UX/DX; v3.0: plugins assinados, lockfiles de wheels, etc.).
- Escopo: Windows‑first com degradação segura em outras plataformas.

## Regras de Ouro (invioláveis)
1) Zero ambiguidades, zero mocks e zero gambiarras em produção.
2) RF005: download/instalação SEMPRE com hash válido (sem placeholders).
3) Nenhuma implementação parcial entra no main; feature incompleta deve ficar atrás de flag desativada por padrão e testada.
4) Mensagens de erro explícitas: o que falhou, por quê, como corrigir.
5) Portabilidade e segurança têm prioridade sobre atalhos de prazo.

## Princípios de UX/CX
- Linguagem única PT‑BR; ícones + texto; acessibilidade (contraste AA) e `--no-emoji`.
- Saídas humanas e `--json` padronizado para automação.
- Prompts claros, defaults seguros, `--dry-run` em operações destrutivas.
- Progresso real com estimativas honestas; `--quiet` e `--verbose`.
- Erros com ação de correção em 1–2 passos e códigos de saída estáveis/documentados.

## Requisitos Funcionais e Não Funcionais
- Funcionais: CLI/TUI, instalação offline com verificação de hash, backup/restore, análise de lacunas.
- Não-funcionais: desempenho previsível, observabilidade (logging estruturado), portabilidade com degradação segura, segurança de supply chain.

## Arquitetura e Módulos
- CLI (Typer), Core (config/log/erros), Detection (Registro/FS/CLI), Validation (Pydantic), Scripts utilitários.
- Fronteiras e contratos estáveis; dependências externas minimizadas.

## Segurança (RF005) e Supply Chain
- Hash obrigatório e não‑placeholder para `exe/msi/zip` e `pip` (wheel). Limites de tamanho, timeouts, retries exponenciais, mirrors confiáveis.
- `pip` offline via wheel verificada; roadmap: lockfiles de wheels com hashes.
- Atualização de hashes via `scripts/hash_updater.py` com política documentada.

## Especificação de CLI/TUI
- Comandos, flags e exemplos realistas. Todos com `--help` útil e `--json` quando aplicável.
- Tabela de códigos de saída por comando (documentar no README e aqui).

### Códigos de saída por comando (padrão)
- install / install-many:
  - 0: sucesso
  - 1: erro genérico
  - 2: política RF005 violada (hash ausente/placeholder)
  - 3: falha em download/verificação
  - 4: falha de instalação/extração
- analyze-gaps:
  - 0: sucesso sem lacunas (ou `--no-fail-on-missing`)
  - 2: lacunas encontradas e `--fail-on-missing`
- backup/restore/update/uninstall/doctor: 0 sucesso, 1 erro

## Detecção (Unified Detection Engine)
- Métodos: Registro (Windows), FS e CLI; guarda de plataforma e fallback seguro.
- Confiança: HIGH/MEDIUM/LOW; cache com TTL; métricas de acerto.

## Schema de Componentes (YAML)
- Campos obrigatórios por método: `exe/msi/zip` → `download_url` + `hash`; `pip` → `install_args` + `pypi_name` + `version` + `hash`.
- Regras de URL, hash, dependências, pós‑instalação e desinstalação. Exemplos válidos/ inválidos.

## Tratamento de Erros e Logging
- Categorias e severidades; estratégias de recuperação (retry/skip/fallback/intervenção).
- Logging estruturado em arquivo + console; correlation IDs; dados sensíveis redigidos.

## Qualidade: DoD, Gates e Métricas
- DoD: testes (unit/integração), linters, tipos, cobertura mínima, documentação atualizada.
- Gates de CI: bloqueio por falha; retry controlado; versionamento e changelog.

## Processo de Mudança (sem ambiguidade)
- Commits semânticos; versionamento semântico; changelog.
- RFC leve para mudanças de contrato; ADRs curtos quando necessário.
- Atualização deste plano é obrigatória em mudanças comportamentais.

## Roadmap (alto nível)
- v2.x: Correções de UX/CX, `--json` nos comandos, instalação `zip`, guardas de plataforma, integração de comandos auxiliares.
- v3.x: Lockfiles de wheels, assinatura/verificação de plugins, relatórios avançados.

### Itens v3.x detalhados
- Lockfile de wheels: `scripts/lock_wheels.py` gerando arquivo com lista de wheels + hashes.
- Assinatura/verificação de plugins: `core/plugin_system.py` com verificação de assinatura digital e política de confiança.
- Relatórios avançados: export JSON/HTML com métricas de detecção, instalação e conflitos de plugins.

#### Fluxo de lockfile de wheels
- Assinatura de plugins
  - Config: `plugin_signature_verification` (bool) e `plugin_signature_required` (bool)
  - Verificação atual: assinatura == SHA256 do diretório do plugin (placeholder robusto). Evoluir para PKI.
- Comando: `python scripts/lock_wheels.py --requirements req.txt --output wheels.lock.json --dest downloads/.dist`
- Uso no `install`/`update`: verificar se wheel presente em `dest` tem hash igual ao do lockfile antes de instalar.


