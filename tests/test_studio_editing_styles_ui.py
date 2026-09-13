from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_editing_styles_are_a_visible_native_destination():
    navigation = (ROOT / "macos/Sources/StudioCore/StudioNavigation.swift").read_text()
    app = (ROOT / "macos/Sources/Studio/StudioApp.swift").read_text()
    view = (ROOT / "macos/Sources/Studio/EditingStylesView.swift").read_text()

    assert 'case editingStyles="Editing Styles"' in navigation
    assert 'systemImage:"checklist"' in navigation
    assert "case .editingStyles:EditingStylesView()" in app
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
    assert "guard !hasUnsavedStyleDraft || destination == .editingStyles" in workspace
    assert "guard !hasUnsavedStyleDraft else" in workspace
