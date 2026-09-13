from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_editing_styles_are_contextual_project_settings_not_a_peer_destination():
    navigation = (ROOT / "macos/Sources/StudioCore/StudioNavigation.swift").read_text()
    app = (ROOT / "macos/Sources/Studio/StudioApp.swift").read_text()
    view = (ROOT / "macos/Sources/Studio/EditingStylesView.swift").read_text()

    permanent_sidebar = navigation.split("public static let sections", 1)[-1]
    assert 'title:"Editing Styles"' not in permanent_sidebar
    assert 'title:"Project Settings"' in permanent_sidebar
    assert "EditingStylesView" in app
    assert 'Picker("Editing style"' in view
    assert 'Toggle("Enable rule"' in view
    assert 'TextEditor(text:' in view
    assert 'Button("New from master"' in view
    assert 'Button("Save style"' in view


def test_style_drafts_reload_from_disk_and_block_accidental_navigation():
    view = (ROOT / "macos/Sources/Studio/EditingStylesView.swift").read_text()
    workspace = (ROOT / "macos/Sources/Studio/Workspace.swift").read_text()

    assert "func reloadFromDisk()" in view
    assert "try await w.refresh();load()" in view
    assert "w.hasUnsavedStyleDraft=true" in view
    assert "guard !hasUnsavedStyleDraft || destination == .projectSettings" in workspace
    assert "guard !hasUnsavedStyleDraft else" in workspace


def test_project_settings_consolidates_editorial_resource_and_application_settings():
    app = (ROOT / "macos/Sources/Studio/StudioApp.swift").read_text()
    navigation = (ROOT / "macos/Sources/StudioCore/StudioNavigation.swift").read_text()
    codex = (ROOT / "macos/Sources/Studio/CodexView.swift").read_text()

    assert 'case editing="Editing Style"' in navigation
    assert 'case resources="Resources"' in navigation
    assert 'case application="Application"' in navigation
    assert 'TextField("Engine repository"' in app
    assert 'TextField("Python executable"' in app
    assert 'TextField("Codex executable"' in app
    assert 'DisclosureGroup("Local application paths")' not in codex


def test_project_settings_does_not_discard_an_unsaved_style_when_switching_sections():
    app = (ROOT / "macos/Sources/Studio/StudioApp.swift").read_text()

    assert "StudioProjectSettingsSection.permitsTransition" in app
    assert "Save or reload the editing style before opening another Project Settings section." in app
