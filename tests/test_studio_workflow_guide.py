"""Acceptance contracts for the project-scoped contextual workflow guide.

These tests intentionally describe the next Studio behavior through the public
JSON bridge and small source-level UI contracts.  They must fail before the
guide is implemented.
"""
import json
from pathlib import Path
import wave

import pytest

from tools.studio import dispatch


ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "macos/Sources/Studio"
STUDIO_CORE = ROOT / "macos/Sources/StudioCore"
REAL_TEMPLATE_IDS = {
    "long_form_youtube",
    "solo_podcast",
    "short_form",
    "clean_audio",
    "tighten_silence",
    "thumbnail",
}


def call(project, method, **params):
    return dispatch({"method": method, "project": str(project), "params": params})


def source(folder, name):
    path = folder / name
    return path.read_text() if path.is_file() else ""


@pytest.fixture
def project(tmp_path):
    path = tmp_path / "production"
    call(path, "create", title="Workflow guide fixture")
    return path


@pytest.fixture
def audio(tmp_path):
    path = tmp_path / "source.wav"
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8_000)
        stream.writeframes(b"\0\0" * 8_000)
    return path


def instance(response, workflow_id):
    items = response.get("workflow_instances", response.get("instances", []))
    return next(item for item in items if item["id"] == workflow_id)


def create_workflow(project, template_id, name):
    response = call(project, "create_workflow", template_id=template_id, name=name)
    workflow_id = response["active_workflow_id"]
    assert instance(response, workflow_id)["template_id"] == template_id
    return response, workflow_id


def test_workflow_response_offers_only_real_templates_and_solo_is_opt_in(project):
    initial = call(project, "workflow_instances")
    assert {item["id"] for item in initial["templates"]} == REAL_TEMPLATE_IDS
    assert all(
        item["template_id"] != "solo_podcast"
        for item in initial["instances"]
    )

    created, workflow_id = create_workflow(project, "solo_podcast", "Episode workflow")
    assert instance(created, workflow_id)["name"] == "Episode workflow"
    assert sum(
        item["template_id"] == "solo_podcast"
        for item in created["workflow_instances"]
    ) == 1


def test_legacy_project_migrates_to_long_form_without_losing_reviews(project):
    evidence = project / "work" / "legacy-intake.md"
    evidence.write_text("Existing project intake evidence.")
    call(
        project,
        "record_stage",
        stage="intake",
        evidence=[str(evidence)],
        reason="Existing intake review",
    )
    state_path = project / "work/studio/project.json"
    legacy = json.loads(state_path.read_text())
    expected_reviews = legacy["stage_reviews"]
    legacy.pop("workflow_instances", None)
    legacy.pop("active_workflow_id", None)
    state_path.write_text(json.dumps(legacy))

    reopened = call(project, "open")
    assert reopened["stage_reviews"] == expected_reviews
    assert len(reopened["workflow_instances"]) == 1
    migrated = reopened["workflow_instances"][0]
    assert migrated["template_id"] == "long_form_youtube"
    assert reopened["active_workflow_id"] == migrated["id"]

    persisted = json.loads(state_path.read_text())
    assert persisted["workflow_instances"] == reopened["workflow_instances"]
    assert persisted["active_workflow_id"] == migrated["id"]


def test_unrelated_revision_and_annotation_do_not_stale_another_workflow(project, audio):
    second_audio = audio.with_name("second.wav")
    second_audio.write_bytes(audio.read_bytes())
    asset = call(project, "import_media", path=str(audio), role="source")["assets"][0]
    other_asset = call(project, "import_media", path=str(second_audio), role="source")["assets"][-1]
    first_revision = call(project, "add_revision", path=str(audio), label="First revision")["revisions"][0]
    first_note = call(
        project,
        "add_annotation",
        asset_id=asset["id"],
        time_ms=100,
        text="First workflow note",
    )["annotations"][0]

    _, first_id = create_workflow(project, "long_form_youtube", "Main edit")
    _, second_id = create_workflow(project, "clean_audio", "Audio cleanup")
    call(
        project,
        "update_workflow_inputs",
        workflow_id=first_id,
        inputs={"asset_ids": [asset["id"]], "output_revision_ids": [first_revision["id"]]},
    )
    before = instance(call(project, "workflow_instances"), first_id)

    unrelated_revision = call(project, "add_revision", path=str(second_audio), label="Audio-only revision")["revisions"][-1]
    call(
        project,
        "add_annotation",
        asset_id=other_asset["id"],
        time_ms=700,
        text="Audio cleanup note",
    )
    call(
        project,
        "update_workflow_inputs",
        workflow_id=second_id,
        inputs={"asset_ids": [other_asset["id"]], "output_revision_ids": [unrelated_revision["id"]]},
    )
    after = instance(call(project, "workflow_instances"), first_id)

    assert after["input_binding"] == before["input_binding"]
    assert after["status"] == "current"


def test_stage_evidence_is_workflow_scoped_but_shared_brief_changes_stale_it(project, audio):
    second_audio = audio.with_name("workflow-b.wav")
    second_audio.write_bytes(audio.read_bytes())
    first_asset = call(project, "import_media", path=str(audio), role="source")["assets"][0]
    second_asset = call(project, "import_media", path=str(second_audio), role="source")["assets"][-1]
    _, first_id = create_workflow(project, "long_form_youtube", "Workflow A")
    _, second_id = create_workflow(project, "short_form", "Workflow B")
    call(
        project,
        "update_workflow_inputs",
        workflow_id=first_id,
        inputs={"asset_ids": [first_asset["id"]], "output_revision_ids": []},
    )
    call(
        project,
        "update_workflow_inputs",
        workflow_id=second_id,
        inputs={"asset_ids": [second_asset["id"]], "output_revision_ids": []},
    )
    evidence = project / "work" / "workflow-a-intake.md"
    evidence.write_text("Reviewed Workflow A's bound source and shared brief.")
    call(
        project,
        "record_stage",
        workflow_id=first_id,
        stage="intake",
        evidence=[str(evidence)],
        reason="Workflow A intake reviewed",
    )
    assert call(project, "workflow", workflow_id=first_id)["stages"][0]["status"] == "complete"

    second_revision = call(project, "add_revision", path=str(second_audio), label="Workflow B revision")["revisions"][-1]
    call(
        project,
        "add_annotation",
        asset_id=second_asset["id"],
        time_ms=600,
        text="Workflow B feedback only",
    )
    call(
        project,
        "update_workflow_inputs",
        workflow_id=second_id,
        inputs={
            "asset_ids": [second_asset["id"]],
            "output_revision_ids": [second_revision["id"]],
        },
    )
    assert call(project, "workflow", workflow_id=first_id)["stages"][0]["status"] == "complete"

    call(project, "update_brief", brief={"purpose": "A changed shared objective"})
    assert call(project, "workflow", workflow_id=first_id)["stages"][0]["status"] == "stale"


def test_workflow_mutations_never_complete_qa_or_authorize_publication(project):
    response, workflow_id = create_workflow(project, "thumbnail", "Thumbnail concept")
    call(project, "select_workflow", workflow_id=workflow_id)
    call(
        project,
        "update_workflow_inputs",
        workflow_id=workflow_id,
        inputs={"asset_ids": [], "output_revision_ids": []},
    )

    assert call(project, "quality")["complete"] is False
    assert not (project / "work/quality/completion.json").exists()
    serialized = json.dumps(call(project, "open")).lower()
    assert '"publication_authorized": true' not in serialized
    assert instance(response, workflow_id).get("complete") is not True


def test_sidebar_is_grouped_and_workflows_are_contextual_not_permanent_tabs():
    navigation = source(STUDIO_CORE, "StudioNavigation.swift")
    app = source(STUDIO, "StudioApp.swift")

    permanent_sidebar = navigation.split("public static let sections", 1)[-1]
    assert "public static let sections" in navigation
    assert "StudioNavigationSection" in navigation
    for stable_destination in ("overview", "brief", "sources", "revisions", "feedback", "workflowGuide"):
        assert f"case {stable_destination}" in navigation
    assert "case podcast=" not in navigation
    assert "case understanding=" not in navigation
    assert ".init(destination:.podcast" not in permanent_sidebar
    assert ".init(destination:.understanding" not in permanent_sidebar
    assert "StudioNavigationContract.sections" in app
    assert "Add Workflow" in app


def test_add_workflow_renders_bridge_templates_instead_of_fake_or_hard_coded_cards():
    guide = source(STUDIO, "WorkflowGuideView.swift")
    workspace = source(STUDIO, "Workspace.swift")

    assert "workflow_instances" in guide
    assert "templates" in guide
    assert "ForEach" in guide
    assert "create_workflow" in guide
    assert "Coming soon" not in guide


def test_contextual_codex_action_prefills_prompt_without_sending_it():
    guide = source(STUDIO, "WorkflowGuideView.swift")
    workspace = source(STUDIO, "Workspace.swift")
    codex = source(STUDIO, "CodexView.swift")

    assert "prefill" in guide.lower() and "codex" in guide.lower()
    assert "codexPrompt" in workspace
    assert "$w.codexPrompt" in codex
    assert "select(.codex)" in guide or "destination:.codex" in guide
    assert "client.send" not in guide
    assert ".send(" not in guide


def test_revision_import_is_atomically_bound_and_shows_workflow_ownership():
    guide = source(STUDIO, "WorkflowGuideView.swift")
    workspace = source(STUDIO, "Workspace.swift")

    assert 'params["workflow_id"]=workflowAtImport.id' in workspace
    assert 'request("update_workflow_inputs"' not in workspace.split("func importURLs", 1)[-1].split("func handoff", 1)[0]
    assert "Workflows:" in guide
    assert "workflowNames(for:" in guide


def test_legacy_podcast_deep_links_land_on_contextual_workflow_capabilities():
    navigation = source(STUDIO_CORE, "StudioNavigation.swift")
    app = source(STUDIO, "StudioApp.swift")

    assert 'case "podcast/setup"' in navigation
    assert 'case "review/podcast"' in navigation
    assert 'destination:.sources' in navigation
    assert 'destination:.feedback' in navigation
    assert "case .sources" in app and "case .feedback" in app
    assert ".init(destination:.podcast" not in navigation.split("public static let sections", 1)[-1]
