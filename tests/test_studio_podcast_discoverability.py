"""Source-level UI contracts for podcast discoverability in the native Studio."""
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "macos/Sources/Studio"
STUDIO_CORE = ROOT / "macos/Sources/StudioCore"


def source(name: str) -> str:
    path = STUDIO / name
    return path.read_text() if path.is_file() else ""


def test_podcast_is_contextual_instead_of_a_permanent_sidebar_destination():
    app = source("StudioApp.swift")
    navigation = (STUDIO_CORE / "StudioNavigation.swift").read_text()
    intake = source("IntakeView.swift")
    assert "StudioNavigationContract.sections" in app
    assert ".init(destination:.podcast" not in navigation
    assert 'title:"Sources"' not in navigation.split("public static let sections", 1)[-1]
    assert "hasSoloPodcastWorkflow" in intake
    assert "if hasSoloPodcastWorkflow" in intake


def test_review_area_is_workspace_owned_instead_of_local_picker_state():
    workspace = source("Workspace.swift")
    review = source("ReviewView.swift")
    assert "@Published var navigation=StudioNavigationState()" in workspace
    assert "@State private var reviewArea" not in review
    assert "selection:$w.navigation.reviewArea" in review


def test_sidebar_displays_version_build_and_revision_identity():
    app = source("StudioApp.swift")
    builder = (ROOT / "tools/build_studio_app.py").read_text()
    assert "StudioBuildIdentity.current.visibleLabel" in app
    assert "StudioEngineRevision" in builder


def test_podcast_context_help_has_real_articles():
    guide = json.loads((ROOT / "docs/user-guide.json").read_text())
    by_id = {article["id"]: article for article in guide["articles"]}
    assert by_id["podcast-setup"]["section"] == "Current Work"
    assert by_id["review-podcast-visual-score"]["section"] == "Current Work"
    assert by_id["review-podcast-qualification"]["section"] == "Current Work"
    assert "Solo podcast" in by_id["manage-workflows"]["steps"][1]
