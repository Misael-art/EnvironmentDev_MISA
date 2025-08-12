import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / 'logs'
README = ROOT / 'README.md'

rows = []
for p in LOGS.glob('gaps_*.json'):
    if p.name == 'gaps_all.json':
        continue
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
        cat = p.stem.replace('gaps_', '').replace('_', ' ')
        rows.append((cat, data.get('expected', 0), data.get('present', 0), data.get('missing', 0)))
    except Exception:
        continue

rows.sort(key=lambda r: r[0].lower())

table_lines = [
    '| Categoria | Esperados | Presentes | Ausentes |',
    '|---|---:|---:|---:|',
]
for cat, exp, pres, miss in rows:
    table_lines.append(f'| {cat} | {exp} | {pres} | {miss} |')

section = '\n'.join(['\n## Estado das Categorias (detecção)\n', *table_lines, '\n'])

readme = README.read_text(encoding='utf-8') if README.exists() else ''
marker = '\n## Estado das Categorias (detecção)\n'
if marker in readme:
    # substitui seção existente
    head, _, tail = readme.partition(marker)
    # tail começa com a seção, vamos remover até próxima seção '## ' ou fim
    parts = tail.split('\n## ', 1)
    new_tail = (('## ' + parts[1]) if len(parts) > 1 else '')
    new_content = head + section + new_tail
else:
    new_content = readme + section

README.write_text(new_content, encoding='utf-8')
print('README atualizado com tabela de estados por categoria.')
