"""Human-facing project naming stays distinct from legacy technical identifiers."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT_ROOTS = (ROOT / "docs", ROOT / "plan", ROOT / "productions")
TEXT_SUFFIXES = {".md", ".html", ".json", ".txt", ".yaml", ".yml", ".toml"}


def documentation_files() -> list[Path]:
    files = [ROOT / "README.md", ROOT / "AGENTS.md"]
    for directory in DOCUMENT_ROOTS:
        files.extend(
            path
            for path in directory.rglob("*")
            if path.is_file()
            and path.suffix.lower() in TEXT_SUFFIXES
            and "docs/upstream" not in path.relative_to(ROOT).as_posix()
        )
    return files


def test_current_product_name_replaces_legacy_human_facing_names():
    forbidden = ("Codex YouTube Editor", "Mac Production Studio")
    for path in documentation_files():
        text = path.read_text(encoding="utf-8")
        for old_name in forbidden:
            assert old_name not in text, f"{old_name!r} remains in {path.relative_to(ROOT)}"


def test_unqualified_codex_studio_only_appears_in_legacy_technical_identifiers():
    unqualified = re.compile(r"(?<!Media )Codex Studio")
    allowed_context = re.compile(
        r"(?:Applications|Movies|Logs|work/apps)/Codex Studio|CodexStudio"
    )
    for path in documentation_files():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if unqualified.search(line):
                assert allowed_context.search(line), (
                    f"Unqualified product name in {path.relative_to(ROOT)}:{line_number}"
                )


def test_decision_artifacts_use_the_product_name():
    required = {
        "Codex Media Studio — Design and Research.md",
        "Codex Media Studio — Editorial Techniques Research and Development Specification.html",
        "Codex Media Studio — Engine Implementation Plan.md",
        "Codex Media Studio — Migration Plan.html",
        "Codex Media Studio — Native App Implementation Plan.html",
        "Codex Media Studio — Native App Implementation Plan.md",
        "Codex Media Studio — Native App Specification.md",
        "Codex Media Studio — Short-Form Vertical Video Research and Specification.html",
        "Codex Media Studio — Visual Identity.html",
    }
    assert required <= {path.name for path in (ROOT / "plan").iterdir()}


def test_local_project_name_is_distinct_from_the_product_name():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "`YT-codex` is the local project and repository name" in readme
    assert "The local project/repository name is `YT-codex`" in agents
