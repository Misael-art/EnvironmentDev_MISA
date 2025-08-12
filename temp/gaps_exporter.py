import os, sys, glob, yaml, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMP_DIR = ROOT / 'components'
LOGS_DIR = ROOT / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Descobrir categorias únicas
categories = set()
for yml in COMP_DIR.glob('*.yaml'):
    try:
        data = yaml.safe_load(yml.read_text(encoding='utf-8'))
        if isinstance(data, dict):
            for _, comp in data.items():
                if isinstance(comp, dict):
                    c = comp.get('category')
                    if c:
                        categories.add(c)
    except Exception:
        continue

categories = sorted(categories)

# Helper: extrair JSON do output da CLI
json_re = re.compile(r'\{[\s\S]*\}$', re.MULTILINE)

def extract_json(text: str) -> str:
    m = json_re.search(text.strip())
    if m:
        return m.group(0)
    i = text.find('{'); j = text.rfind('}')
    return text[i:j+1] if i != -1 and j != -1 else text

# Export por categoria
py = sys.executable
for cat in categories:
    safe = ''.join(ch if ch.isalnum() else '_' for ch in cat)
    out_file = LOGS_DIR / f'gaps_{safe}.json'
    cmd = [py, '-m', 'cli.main', 'analyze-gaps', '--category', cat, '--json', '--no-fail-on-missing']
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        content = extract_json(res.stdout)
        out_file.write_text(content, encoding='utf-8')
        print(f'Wrote {out_file}')
    except Exception as e:
        print(f'Error on {cat}: {e}', file=sys.stderr)

# Export geral
all_out = LOGS_DIR / 'gaps_all.json'
res = subprocess.run([py, '-m', 'cli.main', 'analyze-gaps', '--json', '--no-fail-on-missing'], capture_output=True, text=True, timeout=240)
all_out.write_text(extract_json(res.stdout), encoding='utf-8')
print(f'Wrote {all_out}')
