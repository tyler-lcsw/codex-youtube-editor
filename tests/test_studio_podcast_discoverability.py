"""Source-level UI contracts for podcast discoverability in the native Studio."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "macos/Sources/Studio"
STUDIO_CORE = ROOT / "macos/Sources/StudioCore"


def source(name: str) -> str:
    path = STUDIO / name
    return path.read_text() if path.is_file() else ""


def test_sidebar_exposes_a_podcast_destination_and_icon():
    app = source("StudioApp.swift")
    assert "StudioNavigationContract.sidebarItems" in app
    assert "PodcastQuickStartView()" in app


def test_podcast_quick_start_exposes_accessible_setup_and_review_routes():
    quick_start = source("PodcastQuickStartView.swift")
    intake = source("IntakeView.swift")
    assert "PodcastQuickStartAction.allCases" in quick_start
    assert ".accessibilityLabel(action.accessibilityLabel)" in quick_start
    assert "w.open(action.route)" in quick_start
    assert '.id("podcast-setup")' in intake
    assert 'proxy.scrollTo("podcast-setup"' in intake


def test_review_area_is_workspace_owned_instead_of_local_picker_state():
    workspace = source("Workspace.swift")
    review = source("ReviewView.swift")
    assert "@Published var navigation=StudioNavigationState()" in workspace
    assert "@State private var reviewArea" not in review
    assert "selection:$w.navigation.reviewArea" in review


def test_podcast_copy_routes_generation_to_codex_and_keeps_review_explicit():
    intake = source("IntakeView.swift")
    quick_start = source("PodcastQuickStartView.swift") + (STUDIO_CORE / "StudioNavigation.swift").read_text()
    assert "waveform rendering and semantic visual proposals are not generated yet" not in intake
    assert "Codex & QA" in quick_start
    assert "render" in quick_start.lower()
    assert "explicit review" in quick_start.lower()


def test_sidebar_displays_version_build_and_revision_identity():
    app = source("StudioApp.swift")
    builder = (ROOT / "tools/build_studio_app.py").read_text()
    assert "StudioBuildIdentity.current.visibleLabel" in app
    assert "StudioEngineRevision" in builder
