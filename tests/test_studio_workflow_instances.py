import json
from pathlib import Path

import pytest

from tools.studio import dispatch


def call(project, method, **params):
    return dispatch({"method": method, "project": str(project), "params": params})


@pytest.fixture
def project(tmp_path):
    project = tmp_path / "production"
    call(project, "create", title="Workflow fixture")
    return project


def imported(project, tmp_path, name):
    source = tmp_path / name
    source.write_text(f"document {name}")
    return call(project, "import_media", path=str(source), role="document")["assets"][-1]


def test_templates_expose_six_supported_project_workflows(project):
    result = call(project, "workflow_instances")
    assert [item["id"] for item in result["templates"]] == [
        "long_form_youtube", "solo_podcast", "short_form", "clean_audio",
        "tighten_silence", "thumbnail",
    ]
    assert result["active_workflow_id"] == "legacy-main-production"
    assert result["instances"][0]["template_id"] == "long_form_youtube"
    assert all([stage["stage_id"] for stage in item["guide_stages"]] == ["intake", "source_understanding", "editorial_strategy", "edit", "final_review"] for item in result["templates"])


def test_templates_distinguish_deliverables_from_supporting_actions(project):
    templates = {
        item["id"]: item["kind"]
        for item in call(project, "workflow_instances")["templates"]
    }
    assert templates == {
        "long_form_youtube": "deliverable",
        "solo_podcast": "deliverable",
        "short_form": "deliverable",
        "thumbnail": "deliverable",
        "clean_audio": "supporting_action",
        "tighten_silence": "supporting_action",
    }


def test_unknown_future_template_defaults_to_a_deliverable_without_closing_catalog(tmp_path, monkeypatch):
    from tools import studio_workflows

    catalog = json.loads(studio_workflows.TEMPLATES.read_text())
    future = dict(catalog["templates"][0])
    future.update(id="future_deliverable", label="Future deliverable")
    catalog["templates"].append(future)
    path = tmp_path / "future-templates.json"
    path.write_text(json.dumps(catalog))

    assert studio_workflows.templates(path)["templates"][-1]["id"] == "future_deliverable"
    assert studio_workflows.template_kind("future_deliverable") == "deliverable"


def test_all_project_workflow_exposes_effective_inputs_after_import(project, tmp_path):
    source = imported(project, tmp_path, "new-source.txt")

    workflow = call(project, "workflow_instances")["active_workflow"]

    assert workflow["input_mode"] == "all_project"
    assert workflow["inputs"]["asset_ids"] == []
    assert workflow["effective_inputs"]["asset_ids"] == [source["id"]]


def test_supporting_action_can_be_created_attached_to_a_deliverable(project):
    created = call(
        project,
        "create_workflow",
        template_id="clean_audio",
        name="Clean the main video's audio",
        parent_workflow_id="legacy-main-production",
    )
    action = next(
        item
        for item in created["workflow_instances"]
        if item["id"] == created["active_workflow_id"]
    )

    assert action["template_id"] == "clean_audio"
    assert action["parent_workflow_id"] == "legacy-main-production"


def test_deliverable_cannot_be_created_as_child_work(project):
    before = (project / "work/studio/project.json").read_bytes()

    with pytest.raises(ValueError, match="supporting action"):
        call(
            project,
            "create_workflow",
            template_id="thumbnail",
            name="Invalid child deliverable",
            parent_workflow_id="legacy-main-production",
        )

    assert (project / "work/studio/project.json").read_bytes() == before


def test_supporting_action_rejects_a_missing_parent(project):
    before = (project / "work/studio/project.json").read_bytes()

    with pytest.raises(ValueError, match="parent workflow"):
        call(
            project,
            "create_workflow",
            template_id="clean_audio",
            name="Orphaned action",
            parent_workflow_id="missing-workflow",
        )

    assert (project / "work/studio/project.json").read_bytes() == before


def test_supporting_action_cannot_parent_another_action(project):
    first = call(
        project,
        "create_workflow",
        template_id="clean_audio",
        name="Existing action",
    )
    action_id = first["active_workflow_id"]
    before = (project / "work/studio/project.json").read_bytes()

    with pytest.raises(ValueError, match="deliverable"):
        call(
            project,
            "create_workflow",
            template_id="tighten_silence",
            name="Invalid nested action",
            parent_workflow_id=action_id,
        )

    assert (project / "work/studio/project.json").read_bytes() == before


def test_supporting_action_can_be_linked_and_unlinked_without_recreation(project):
    created = call(
        project,
        "create_workflow",
        template_id="clean_audio",
        name="Movable action",
    )
    action_id = created["active_workflow_id"]

    linked = call(
        project,
        "set_workflow_parent",
        workflow_id=action_id,
        parent_workflow_id="legacy-main-production",
    )
    linked_action = next(
        item for item in linked["workflow_instances"] if item["id"] == action_id
    )
    assert linked_action["parent_workflow_id"] == "legacy-main-production"

    unlinked = call(
        project,
        "set_workflow_parent",
        workflow_id=action_id,
        parent_workflow_id=None,
    )
    unlinked_action = next(
        item for item in unlinked["workflow_instances"] if item["id"] == action_id
    )
    assert unlinked_action["parent_workflow_id"] is None


def test_legacy_instance_without_parent_relationship_remains_valid(project):
    state_path = project / "work/studio/project.json"
    state = json.loads(state_path.read_text())
    state["workflow_instances"][0].pop("parent_workflow_id", None)
    state_path.write_text(json.dumps(state))

    reopened = call(project, "open")
    legacy = next(
        item
        for item in reopened["workflow_instances"]
        if item["id"] == "legacy-main-production"
    )
    assert legacy.get("parent_workflow_id") is None


def test_relinking_supporting_action_does_not_change_evidence_bindings(project):
    created = call(
        project,
        "create_workflow",
        template_id="clean_audio",
        name="Reviewed action",
    )
    action_id = created["active_workflow_id"]
    evidence = project / "work" / "reviewed-action-intake.md"
    evidence.write_text("Reviewed the action's intake and current bound inputs.")
    call(
        project,
        "record_stage",
        workflow_id=action_id,
        stage="intake",
        evidence=[str(evidence)],
        reason="Action intake reviewed",
    )
    before = next(
        item
        for item in call(project, "workflow_instances")["workflow_instances"]
        if item["id"] == action_id
    )

    call(
        project,
        "set_workflow_parent",
        workflow_id=action_id,
        parent_workflow_id="legacy-main-production",
    )
    after = next(
        item
        for item in call(project, "workflow_instances")["workflow_instances"]
        if item["id"] == action_id
    )

    assert after["input_binding"] == before["input_binding"]
    assert after["stage_reviews"] == before["stage_reviews"]


def test_review_annotation_is_atomically_added_to_explicit_workflow_scope(project, tmp_path):
    asset = imported(project, tmp_path, "review.txt")
    # Give the lightweight imported fixture the bounded duration used by annotation validation.
    state_path = project / "work/studio/project.json"
    state = json.loads(state_path.read_text())
    state["assets"][-1]["duration_ms"] = 1_000
    state_path.write_text(json.dumps(state))
    created = call(project, "create_workflow", template_id="long_form_youtube", name="Scoped review")
    workflow_id = created["active_workflow_id"]
    call(
        project,
        "update_workflow_inputs",
        workflow_id=workflow_id,
        inputs={"asset_ids":[asset["id"]],"revision_ids":[],"annotation_ids":[]},
    )

    updated = call(
        project,
        "add_annotation",
        workflow_id=workflow_id,
        asset_id=asset["id"],
        time_ms=100,
        text="Scoped note",
    )
    note_id = updated["annotations"][-1]["id"]
    scoped = next(item for item in updated["workflow_instances"] if item["id"] == workflow_id)

    assert scoped["inputs"]["annotation_ids"] == [note_id]
    assert next(item for item in call(project, "workflow_instances")["workflow_instances"] if item["id"] == workflow_id)["status"] == "stale"


def test_authoritative_stages_receive_template_specific_guide_copy(project):
    created = call(project, "create_workflow", template_id="thumbnail", name="Package")
    workflow = call(project, "workflow", workflow_id=created["active_workflow_id"])
    assert workflow["stages"][0]["label"] == "Define the packaging promise"
    assert workflow["stages"][0]["destination"] == "Brief"
    assert workflow["stages"][0]["requires"] == []
    assert workflow["stages"][-1]["destination"] == "Feedback"
    assert "prompt" in workflow["stages"][-1]


def test_legacy_migration_is_additive_and_preserves_stage_evidence(project):
    state_path = project / "work/studio/project.json"
    state = json.loads(state_path.read_text())
    state.pop("workflow_instances", None)
    state.pop("active_workflow_id", None)
    state["stage_reviews"] = {"intake": {"future": "preserve"}}
    state["unknown_extension"] = {"keep": True}
    state_path.write_text(json.dumps(state))

    reopened = call(project, "open")
    assert reopened["active_workflow_id"] == "legacy-main-production"
    assert reopened["workflow_instances"][0]["id"] == "legacy-main-production"
    assert reopened["stage_reviews"] == {"intake": {"future": "preserve"}}
    assert reopened["unknown_extension"] == {"keep": True}


def test_legacy_configured_podcast_adds_and_selects_solo_workflow(project, tmp_path):
    audio = imported(project, tmp_path, "episode.md")
    state_path = project / "work/studio/project.json"
    state = json.loads(state_path.read_text())
    state.pop("workflow_instances", None)
    state.pop("active_workflow_id", None)
    state["podcast"] = {
        "schema_version": 1,
        "kind": "solo_audio_first",
        "primary_audio_asset_id": audio["id"],
        "camera_asset_id": None,
        "visual_density": "balanced",
    }
    state_path.write_text(json.dumps(state))

    reopened = call(project, "open")
    assert reopened["active_workflow_id"] == "legacy-solo-podcast"
    assert [(item["id"], item["template_id"]) for item in reopened["workflow_instances"]] == [
        ("legacy-main-production", "long_form_youtube"),
        ("legacy-solo-podcast", "solo_podcast"),
    ]
    podcast = reopened["workflow_instances"][1]
    assert podcast["inputs"]["asset_ids"] == [audio["id"]]
    assert podcast["input_mode"] == "selected"
    assert podcast["stage_reviews"] == {}
    assert reopened["stage_reviews"] == {}


def test_legacy_podcast_does_not_inherit_general_production_reviews(project, tmp_path):
    audio = imported(project, tmp_path, "reviewed-episode.md")
    state_path = project / "work/studio/project.json"
    state = json.loads(state_path.read_text())
    state.pop("workflow_instances", None)
    state.pop("active_workflow_id", None)
    state["stage_reviews"] = {"intake": {"opaque_legacy_review": True}}
    state["podcast"] = {
        "schema_version": 1,
        "kind": "solo_audio_first",
        "primary_audio_asset_id": audio["id"],
        "camera_asset_id": None,
        "visual_density": "balanced",
    }
    state_path.write_text(json.dumps(state))

    reopened = call(project, "open")
    main, podcast = reopened["workflow_instances"]
    assert main["stage_reviews"] == state["stage_reviews"]
    assert podcast["stage_reviews"] == {}
    assert podcast["input_mode"] == "selected"


def test_existing_derived_podcast_migration_is_repaired_once(project, tmp_path):
    audio = imported(project, tmp_path, "old-derived.md")
    state_path = project / "work/studio/project.json"
    state = json.loads(state_path.read_text())
    reviews = {"intake": {"opaque": "general evidence"}}
    state["stage_reviews"] = reviews
    main = state["workflow_instances"][0]
    main["stage_reviews"] = reviews
    podcast = dict(main)
    podcast.update(
        id="legacy-solo-podcast",
        template_id="solo_podcast",
        name="Solo podcast",
        inputs={"asset_ids": [audio["id"]], "revision_ids": [], "annotation_ids": None},
        input_mode="all_project",
        stage_reviews=reviews,
    )
    state["workflow_instances"].append(podcast)
    state["active_workflow_id"] = podcast["id"]
    state_path.write_text(json.dumps(state))

    reopened = call(project, "open")
    repaired = next(item for item in reopened["workflow_instances"] if item["id"] == podcast["id"])
    assert repaired["input_mode"] == "selected"
    assert repaired["stage_reviews"] == {}
    assert reopened["stage_reviews"] == {}


def test_create_select_and_update_inputs_round_trip(project, tmp_path):
    source = imported(project, tmp_path, "source.md")
    created = call(
        project, "create_workflow", template_id="clean_audio",
        name="Clean interview", inputs={"asset_ids": [source["id"]], "output_revision_ids": []},
    )
    workflow_id = created["active_workflow_id"]
    assert next(item for item in created["workflow_instances"] if item["id"] == workflow_id)["name"] == "Clean interview"

    call(project, "select_workflow", workflow_id="legacy-main-production")
    selected = call(project, "update_workflow_inputs", workflow_id=workflow_id, inputs={"asset_ids": [], "output_revision_ids": []})
    assert selected["active_workflow_id"] == "legacy-main-production"
    instance = next(item for item in selected["workflow_instances"] if item["id"] == workflow_id)
    assert instance["inputs"] == {"asset_ids": [], "revision_ids": [], "annotation_ids": None}


def test_flat_output_revision_alias_is_accepted(project, tmp_path, monkeypatch):
    media = tmp_path / "flat-output.mov"
    media.write_bytes(b"revision")
    monkeypatch.setattr("tools.studio_project.probe", lambda _path: (1000, ["video", "audio"]))
    revision = call(project, "add_revision", path=str(media))["revisions"][-1]

    created = call(
        project,
        "create_workflow",
        template_id="short_form",
        name="Flat alias",
        asset_ids=[],
        output_revision_ids=[revision["id"]],
    )
    selected = next(item for item in created["workflow_instances"] if item["id"] == created["active_workflow_id"])
    assert selected["inputs"]["revision_ids"] == [revision["id"]]


def test_workflow_input_binding_includes_template_and_catalog(project):
    created = call(project, "create_workflow", template_id="thumbnail", name="Bound template")
    selected = next(item for item in created["workflow_instances"] if item["id"] == created["active_workflow_id"])
    assert selected["input_binding"]["template_id"] == "thumbnail"
    assert len(selected["input_binding"]["template_catalog_sha256"]) == 64


def test_old_binding_without_template_metadata_opens_as_structurally_stale(project):
    state_path = project / "work/studio/project.json"
    state = json.loads(state_path.read_text())
    binding = state["workflow_instances"][0]["input_binding"]
    binding.pop("template_id")
    binding.pop("template_catalog_sha256")
    state_path.write_text(json.dumps(state))

    selected = call(project, "workflow_instances")["active_workflow"]
    assert selected["status"] == "stale"
    assert {reason["code"] for reason in selected["stale_reasons"]} == {
        "template_binding_changed", "template_catalog_changed"
    }


def test_template_catalog_change_stales_instance_and_stage_review(project, tmp_path, monkeypatch):
    catalog = tmp_path / "studio-workflows.json"
    catalog.write_bytes(Path("config/studio-workflows.json").read_bytes())
    monkeypatch.setattr("tools.studio_workflows.TEMPLATES", catalog)
    created = call(project, "create_workflow", template_id="thumbnail", name="Catalog-bound")
    workflow_id = created["active_workflow_id"]
    evidence = project / "work/catalog-intake.md"
    evidence.write_text("Reviewed the catalog-bound intake.")
    call(project, "record_stage", workflow_id=workflow_id, stage="intake", evidence=[str(evidence)], reason="Catalog-bound review")

    changed = json.loads(catalog.read_text())
    changed["templates"][-1]["description"] += " Updated guidance."
    catalog.write_text(json.dumps(changed))

    status = next(item for item in call(project, "workflow_instances")["instances"] if item["id"] == workflow_id)
    assert "template_catalog_changed" in {reason["code"] for reason in status["stale_reasons"]}
    stage = call(project, "workflow", workflow_id=workflow_id)["stages"][0]
    assert stage["status"] == "stale"
    assert "workflow_binding_changed" in {reason["code"] for reason in stage["stale_reasons"]}


def test_workflow_status_is_scoped_to_bound_media_and_annotations(project, tmp_path):
    first = imported(project, tmp_path, "first.md")
    second = imported(project, tmp_path, "second.md")
    one = call(project, "create_workflow", template_id="thumbnail", name="First", inputs={"asset_ids": [first["id"]], "output_revision_ids": []})
    first_id = one["active_workflow_id"]
    two = call(project, "create_workflow", template_id="thumbnail", name="Second", inputs={"asset_ids": [second["id"]], "output_revision_ids": []})
    second_id = two["active_workflow_id"]

    status = call(project, "workflow_instances")
    statuses = {item["id"]: item["status"] for item in status["instances"]}
    assert statuses[first_id] == "current"
    assert statuses[second_id] == "current"

    state_path = project / "work/studio/project.json"
    state = json.loads(state_path.read_text())
    state["annotations"].append({"id": "note-first", "asset_id": first["id"], "text": "Change crop"})
    state_path.write_text(json.dumps(state))
    status = call(project, "workflow_instances")
    statuses = {item["id"]: item["status"] for item in status["instances"]}
    assert statuses[first_id] == "stale"
    assert statuses[second_id] == "current"

    call(project, "update_workflow_inputs", workflow_id=first_id, inputs={"asset_ids": [first["id"]], "output_revision_ids": []})
    state = json.loads(state_path.read_text())
    second_path = Path(second["path"])
    second_path.write_text("changed second document")
    status = call(project, "workflow_instances")
    statuses = {item["id"]: item["status"] for item in status["instances"]}
    assert statuses[first_id] == "current"
    assert statuses[second_id] == "stale"


def test_workflow_status_explains_staleness_structurally(project, tmp_path):
    source = imported(project, tmp_path, "stale-source.md")
    created = call(project, "create_workflow", template_id="thumbnail", name="Stale reason", asset_ids=[source["id"]])
    workflow_id = created["active_workflow_id"]
    Path(source["path"]).write_text("changed bytes")

    selected = next(item for item in call(project, "workflow_instances")["instances"] if item["id"] == workflow_id)
    assert selected["status"] == "stale"
    assert selected["stale_reason"]["code"] == "input_binding_changed"
    assert selected["stale_reasons"] == [selected["stale_reason"]]


def test_output_revision_and_related_resolution_annotation_are_bound(project, tmp_path, monkeypatch):
    media = tmp_path / "revision.mp4"
    media.write_bytes(b"fixture")
    monkeypatch.setattr("tools.studio_project.probe", lambda _path: (1000, ["video", "audio"]))
    revision = call(project, "add_revision", path=str(media), label="Output")["revisions"][0]
    created = call(project, "create_workflow", template_id="short_form", name="Vertical", inputs={"asset_ids": [], "output_revision_ids": [revision["id"]]})
    workflow_id = created["active_workflow_id"]
    assert next(item for item in call(project, "workflow_instances")["instances"] if item["id"] == workflow_id)["status"] == "current"

    state_path = project / "work/studio/project.json"
    state = json.loads(state_path.read_text())
    state["annotations"].append({"id": "revision-note", "asset_id": revision["id"], "text": "Move caption"})
    state_path.write_text(json.dumps(state))
    assert next(item for item in call(project, "workflow_instances")["instances"] if item["id"] == workflow_id)["status"] == "stale"


def test_invalid_template_inputs_and_selection_fail_without_writes(project):
    state_path = project / "work/studio/project.json"
    before = state_path.read_bytes()
    with pytest.raises(ValueError):
        call(project, "create_workflow", template_id="unknown", name="Bad", inputs={"asset_ids": [], "output_revision_ids": []})
    with pytest.raises(ValueError):
        call(project, "create_workflow", template_id="thumbnail", name="Bad", inputs={"asset_ids": ["missing"], "output_revision_ids": []})
    with pytest.raises(ValueError):
        call(project, "create_workflow", template_id="thumbnail", name="Bad", inputs=[])
    with pytest.raises(ValueError):
        call(project, "select_workflow", workflow_id="missing")
    assert state_path.read_bytes() == before


def test_existing_workflow_and_record_stage_methods_remain_compatible(project):
    evidence = project / "work/intake.md"
    evidence.write_text("Reviewed workflow fixture intake.")
    call(project, "record_stage", stage="intake", evidence=[str(evidence)], reason="Current intake")
    legacy = call(project, "workflow")
    assert legacy["stages"][0]["status"] == "complete"
    assert call(project, "workflow_instances")["active_workflow_id"] == "legacy-main-production"


def test_opaque_legacy_stage_review_is_reported_stale_instead_of_crashing(project):
    state_path = project / "work/studio/project.json"
    state = json.loads(state_path.read_text())
    state["workflow_instances"][0]["stage_reviews"]["intake"] = "old opaque evidence"
    state["stage_reviews"]["intake"] = "old opaque evidence"
    state_path.write_text(json.dumps(state))

    intake = call(project, "workflow")["stages"][0]
    assert intake["status"] == "stale"
    assert intake["stale_reason"]["code"] == "invalid_review"
    assert intake["stale_reasons"] == [intake["stale_reason"]]


def test_null_legacy_stage_review_is_present_but_invalid(project):
    state_path = project / "work/studio/project.json"
    state = json.loads(state_path.read_text())
    state["workflow_instances"][0]["stage_reviews"]["intake"] = None
    state["stage_reviews"]["intake"] = None
    state_path.write_text(json.dumps(state))

    intake = call(project, "workflow")["stages"][0]
    assert intake["status"] == "stale"
    assert intake["stale_reason"]["code"] == "invalid_review"


def test_inactive_workflow_cannot_borrow_active_workflow_final_qa(project, monkeypatch):
    first = call(project, "create_workflow", template_id="thumbnail", name="First final")
    first_id = first["active_workflow_id"]
    workflow_root = project / "work" / "workflows" / first_id
    (workflow_root / "analysis").mkdir(parents=True)
    (workflow_root / "analysis" / "source-understanding.md").write_text("Reviewed source.")
    (workflow_root / "analysis" / "content-map.json").write_text("{}")
    (workflow_root / "edit-plan.md").write_text("Reviewed edit plan.")
    (project / "work" / "quality" / "completion.json").write_text("{}")
    evidence = project / "work" / "workflow-review.md"
    evidence.write_text("Current reviewed evidence.")
    monkeypatch.setattr("tools.studio_workflow.quality.require_complete", lambda *_args, **_kwargs: {})

    for stage in ("intake", "source_understanding", "editorial_strategy", "edit", "final_review"):
        call(project, "record_stage", workflow_id=first_id, stage=stage, evidence=[str(evidence)], reason=f"Reviewed {stage}")
    assert call(project, "workflow", workflow_id=first_id)["stages"][-1]["status"] == "complete"

    second = call(project, "create_workflow", template_id="clean_audio", name="Second active")
    assert second["active_workflow_id"] != first_id
    inactive_final = call(project, "workflow", workflow_id=first_id)["stages"][-1]
    assert inactive_final["status"] == "stale"
    assert inactive_final["stale_reason"]["code"] == "workflow_not_active"
    with pytest.raises(ValueError, match="active workflow"):
        call(project, "record_stage", workflow_id=first_id, stage="final_review", evidence=[str(evidence)], reason="Wrong active workflow")


def test_requested_workflow_is_consistent_across_response_envelope(project):
    first = call(project, "create_workflow", template_id="thumbnail", name="First")
    first_id = first["active_workflow_id"]
    second = call(project, "create_workflow", template_id="clean_audio", name="Second")
    second_id = second["active_workflow_id"]

    requested = call(project, "workflow", workflow_id=first_id)
    assert requested["workflow_id"] == first_id
    assert requested["active_workflow_id"] == first_id
    assert requested["active_workflow"]["id"] == first_id
    assert next(item for item in requested["workflow_instances"] if item["id"] == second_id)["id"] == second_id


def test_nonlegacy_planning_artifacts_are_workflow_scoped(project):
    created = call(project, "create_workflow", template_id="short_form", name="Scoped")
    workflow_id = created["active_workflow_id"]
    stages = call(project, "workflow", workflow_id=workflow_id)["stages"]
    assert stages[1]["artifacts"] == [
        f"work/workflows/{workflow_id}/analysis/source-understanding.md",
        f"work/workflows/{workflow_id}/analysis/content-map.json",
    ]
    assert stages[2]["artifacts"] == [f"work/workflows/{workflow_id}/edit-plan.md"]
    assert stages[-1]["artifacts"] == ["work/quality/completion.json"]

    legacy = call(project, "workflow", workflow_id="legacy-main-production")["stages"]
    assert legacy[1]["artifacts"] == ["work/analysis/source-understanding.md", "work/analysis/content-map.json"]
    assert legacy[2]["artifacts"] == ["work/edit-plan.md"]

    handoff = call(project, "export_handoff")["text"]
    assert f"work/workflows/{workflow_id}/analysis/source-understanding.md" in handoff
    assert f"work/workflows/{workflow_id}/edit-plan.md" in handoff
    assert "register every new revision with this workflow_id" in handoff


def test_add_revision_can_attach_atomically_to_one_workflow(project, tmp_path, monkeypatch):
    first = call(project, "create_workflow", template_id="short_form", name="First")
    first_id = first["active_workflow_id"]
    second = call(project, "create_workflow", template_id="clean_audio", name="Second")
    second_id = second["active_workflow_id"]
    media = tmp_path / "attached.mp4"
    media.write_bytes(b"attached revision")
    monkeypatch.setattr("tools.studio_project.probe", lambda _path: (1000, ["video", "audio"]))

    response = call(project, "add_revision", path=str(media), workflow_id=first_id)
    revision_id = response["revisions"][-1]["id"]
    workflows = {item["id"]: item for item in response["workflow_instances"]}
    assert workflows[first_id]["inputs"]["revision_ids"] == [revision_id]
    assert workflows[second_id]["inputs"]["revision_ids"] == []
    attached = next(item for item in call(project, "workflow_instances")["instances"] if item["id"] == first_id)
    assert attached["status"] == "current"

    before = (project / "work/studio/project.json").read_bytes()
    with pytest.raises(ValueError, match="Unknown workflow instance"):
        call(project, "add_revision", path=str(media), workflow_id="missing")
    assert (project / "work/studio/project.json").read_bytes() == before


def test_authoritative_stage_evidence_is_scoped_per_workflow(project, tmp_path, monkeypatch):
    first = imported(project, tmp_path, "first-stage.md")
    second = imported(project, tmp_path, "second-stage.md")
    first_state = call(project, "create_workflow", template_id="thumbnail", name="First stage", asset_ids=[first["id"]], revision_ids=[])
    first_id = first_state["active_workflow_id"]
    evidence = project / "work/first-stage-review.md"
    evidence.write_text("Reviewed only the first workflow input.")
    call(project, "record_stage", stage="intake", evidence=[str(evidence)], reason="First workflow intake")
    assert call(project, "workflow")["stages"][0]["status"] == "complete"

    second_state = call(project, "create_workflow", template_id="short_form", name="Second stage", asset_ids=[second["id"]], revision_ids=[])
    second_id = second_state["active_workflow_id"]
    media = tmp_path / "second-output.mp4"
    media.write_bytes(b"second output")
    monkeypatch.setattr("tools.studio_project.probe", lambda _path: (1000, ["video", "audio"]))
    revision = call(project, "add_revision", path=str(media), label="Second output")["revisions"][-1]
    call(project, "update_workflow_inputs", workflow_id=second_id, asset_ids=[second["id"]], revision_ids=[revision["id"]])
    state_path = project / "work/studio/project.json"
    state = json.loads(state_path.read_text())
    state["annotations"].append({"id": "second-only-note", "asset_id": second["id"], "text": "Second workflow only"})
    state_path.write_text(json.dumps(state))

    call(project, "select_workflow", workflow_id=first_id)
    first_workflow = call(project, "workflow")
    assert first_workflow["active_workflow_id"] == first_id
    assert first_workflow["stages"][0]["status"] == "complete"

    call(project, "update_brief", brief={"purpose": "Shared purpose changed"})
    assert call(project, "workflow")["stages"][0]["status"] == "stale"
