# Contribuindo

Obrigado por contribuir! Siga as diretrizes para manter a qualidade e coerência do projeto.

## Commits
- Use commits semânticos:
  - `feat(<escopo>): <descrição>`
  - `fix(<escopo>): <descrição>`
  - `chore(<escopo>): <descrição>`
  - `docs(<escopo>): <descrição>`
  - `test(<escopo>): <descrição>`

## Código
- Padrões: PEP 8.
- Nomes descritivos; evite abreviações opacas.
- Tratamento de erros explícito com mensagens claras (o que, por quê, como corrigir).
- Não duplique arquivos nem lógicas; edite in-place e preserve a arquitetura.

## Testes
- Rode `pytest -q` e mantenha “verde”.
- Mocke rede/FS nos testes que exigem I/O.

## Segurança
- RF005 é obrigatório para métodos com download e para `pip` (wheel offline com SHA256). Placeholders são rejeitados.
