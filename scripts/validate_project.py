from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
errors = []

for path in APP.rglob("*.py"):
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        errors.append(f"{path}: {exc}")

# Validate local imports resolve to either module files or package __init__.py files.
for path in APP.rglob("*.py"):
    if path.name == "__init__.py":
        continue
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
            target = path.parent / (node.module.replace('.', '/') + '.py')
            package_target = path.parent / node.module.replace('.', '/') / '__init__.py'
            if not target.exists() and not package_target.exists():
                errors.append(f"{path}: unresolved relative import .{node.module}")

required = [
    ROOT/'.python-version', ROOT/'requirements.txt', ROOT/'render.yaml', ROOT/'alembic.ini',
    ROOT/'migrations/env.py', ROOT/'migrations/versions/0001_initial.py', ROOT/'app/main.py'
]
for p in required:
    if not p.exists():
        errors.append(f"missing: {p}")

if errors:
    print("VALIDATION_FAILED")
    print("\n".join(errors))
    raise SystemExit(1)
print("VALIDATION_OK")
