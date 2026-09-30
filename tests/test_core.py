from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_all_python_files_parse():
    for path in (ROOT / "app").rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"))


def test_no_duplicate_model_index_declarations():
    models = (ROOT / "app/models.py").read_text(encoding="utf-8")
    assert 'index=True' not in models
