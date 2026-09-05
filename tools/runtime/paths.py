"""Paths shared by script and module entry points."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def resolve_project_path(root: Path, value: str) -> Path:
    return (root / value).resolve()
