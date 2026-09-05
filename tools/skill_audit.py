"""Audit discoverability and local references without asserting prose wording."""
import re
from pathlib import Path
REQUIRED = {'brand-setup','clean-cut','make-tsx','fake-screencast','vidtsx-2d-generator','clean-audio','suggest-sfx','packaging','thumbnail'}

def audit(root: Path, required: set[str] | None = None) -> list[str]:
    required = REQUIRED if required is None else required
    base = root / '.agents/skills'
    errors = []
    for name in sorted(required):
        if not (base / name / 'SKILL.md').is_file():
            errors.append(f'Missing skill: {name}')
    for file in base.rglob('*.md'):
        text = file.read_text()
        if file.name == 'SKILL.md':
            if not text.startswith('---\n') or not re.search(r'^name: .+', text, re.M) or not re.search(r'^description: .+', text, re.M):
                errors.append(f'Invalid skill metadata: {file}')
        for ref in re.findall(r'\]\(([^)]+)\)', text):
            if ref.startswith(('http:', 'https:', '#', 'mailto:')) or '<' in ref:
                continue
            target = ref.split('#')[0]
            if target and not (file.parent / target).exists() and not (root / target).exists():
                errors.append(f'{file}: missing reference {ref}')
    return errors

if __name__ == '__main__':
    import json
    result = audit(Path(__file__).resolve().parents[1])
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result))
