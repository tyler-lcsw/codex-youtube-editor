"""Independent project workflow instances layered over the authoritative stage engine."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import uuid

from .jobs import file_hash


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "config/studio-workflows.json"
STAGE_WORKFLOW = ROOT / "config/studio-workflow.json"
LEGACY_ID = "legacy-main-production"
INPUT_KEYS = {"asset_ids", "revision_ids", "annotation_ids"}


def _digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def templates(path=None):
    data = json.loads(Path(TEMPLATES if path is None else path).read_text())
    if not isinstance(data, dict) or data.get("schema_version") != 1 or set(data) != {"schema_version", "templates"}:
        raise ValueError("Unsupported Studio workflow template schema")
    values = data["templates"]
    if not isinstance(values, list) or not values:
        raise ValueError("Studio workflow templates cannot be empty")
    stage_data = json.loads(STAGE_WORKFLOW.read_text())
    stage_ids = [item["id"] for item in stage_data.get("stages", [])]
    if not stage_ids:
        raise ValueError("Authoritative Studio workflow stages cannot be empty")
    destinations = {"Brief", "Sources", "Workflow Guide", "Revisions", "Feedback", "Codex & QA"}
    seen = set()
    for item in values:
        if not isinstance(item, dict) or set(item) != {"id", "label", "description", "guide_stages"}:
            raise ValueError("Workflow templates require id, label, description, and guide stages")
        identifier = item["id"]
        if not isinstance(identifier, str) or re.fullmatch(r"[a-z][a-z0-9_]*", identifier) is None or identifier in seen:
            raise ValueError("Invalid or duplicate workflow template ID")
        seen.add(identifier)
        for key in ("label", "description"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError(f"Workflow template {key} must be nonempty text")
        guides = item["guide_stages"]
        if not isinstance(guides, list) or [guide.get("stage_id") if isinstance(guide, dict) else None for guide in guides] != stage_ids:
            raise ValueError("Workflow guide stages must exactly match the authoritative stage IDs")
        for guide in guides:
            if not {"stage_id", "label", "detail", "destination"} <= set(guide) <= {"stage_id", "label", "detail", "destination", "prompt"}:
                raise ValueError("Workflow guide stage has invalid fields")
            for key in ("label", "detail"):
                if not isinstance(guide[key], str) or not guide[key].strip():
                    raise ValueError(f"Workflow guide {key} must be nonempty text")
            if guide["destination"] not in destinations:
                raise ValueError("Workflow guide has an unknown destination")
            if "prompt" in guide and (not isinstance(guide["prompt"], str) or not guide["prompt"].strip()):
                raise ValueError("Workflow guide prompt must be nonempty text")
    return data


def _text(value, label, maximum=100):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")
    result = value.strip()
    if len(result) > maximum:
        raise ValueError(f"{label} is too long")
    return result


def request_inputs(params):
    """Accept canonical nested inputs plus the initial bridge's flat aliases."""
    nested = params.get("inputs")
    flat_present = any(key in params for key in ("asset_ids", "revision_ids", "output_revision_ids", "annotation_ids"))
    if nested is not None and flat_present:
        raise ValueError("Provide workflow inputs either nested or flat, not both")
    if nested is not None and not isinstance(nested, dict):
        raise ValueError("Workflow inputs must be an object")
    if nested is not None:
        value = dict(nested)
    else:
        if "revision_ids" in params and "output_revision_ids" in params:
            raise ValueError("Use only one revision input field")
        value = {
            "asset_ids": params.get("asset_ids", []),
            "revision_ids": params.get("revision_ids", params.get("output_revision_ids", [])),
            "annotation_ids": params.get("annotation_ids"),
        }
    if "output_revision_ids" in value:
        if "revision_ids" in value:
            raise ValueError("Use only one revision input field")
        value["revision_ids"] = value.pop("output_revision_ids")
    value.setdefault("asset_ids", [])
    value.setdefault("revision_ids", [])
    value.setdefault("annotation_ids", None)
    return value


def _inputs(data, value):
    if not isinstance(value, dict) or set(value) != INPUT_KEYS:
        raise ValueError("Workflow inputs require asset_ids, revision_ids, and annotation_ids")
    asset_ids, revision_ids = value["asset_ids"], value["revision_ids"]
    if not isinstance(asset_ids, list) or not isinstance(revision_ids, list):
        raise ValueError("Workflow input IDs must be lists")
    if any(not isinstance(item, str) or not item for item in asset_ids + revision_ids):
        raise ValueError("Workflow input IDs must be nonempty strings")
    if len(set(asset_ids)) != len(asset_ids) or len(set(revision_ids)) != len(revision_ids):
        raise ValueError("Workflow input IDs must be unique")
    annotation_ids = value["annotation_ids"]
    if annotation_ids is not None and (not isinstance(annotation_ids, list) or any(not isinstance(item, str) or not item for item in annotation_ids) or len(set(annotation_ids)) != len(annotation_ids)):
        raise ValueError("Workflow annotation IDs must be a unique list or null")
    known_assets = {item["id"] for item in data["assets"]}
    known_revisions = {item["id"] for item in data["revisions"]}
    if not set(asset_ids) <= known_assets or not set(revision_ids) <= known_revisions:
        raise ValueError("Workflow inputs must identify imported assets and output revisions")
    known_annotations = {item.get("id") for item in data["annotations"]}
    if annotation_ids is not None and not set(annotation_ids) <= known_annotations:
        raise ValueError("Workflow inputs must identify existing annotations")
    return {"asset_ids": list(asset_ids), "revision_ids": list(revision_ids), "annotation_ids": None if annotation_ids is None else list(annotation_ids)}


def _relevant_annotations(data, inputs):
    if inputs["annotation_ids"] is not None:
        selected_annotations = set(inputs["annotation_ids"])
        return [annotation for annotation in data["annotations"] if annotation.get("id") in selected_annotations]
    selected = set(inputs["asset_ids"]) | set(inputs["revision_ids"])
    return [
        annotation for annotation in data["annotations"]
        if annotation.get("asset_id") in selected or annotation.get("resolution_revision_id") in selected
    ]


def input_binding(project, data, inputs, template_id):
    project = Path(project).resolve()
    inputs = _inputs(data, inputs)
    selected_assets = set(inputs["asset_ids"])
    selected_revisions = set(inputs["revision_ids"])

    def snapshot(item):
        candidate = Path(item["path"])
        return {
            "id": item["id"],
            "registered": item["sha256"],
            "current": file_hash(candidate) if candidate.is_file() else None,
        }

    return {
        "assets": [snapshot(item) for item in data["assets"] if item["id"] in selected_assets],
        "output_revisions": [snapshot(item) for item in data["revisions"] if item["id"] in selected_revisions],
        "annotations_sha256": _digest(_relevant_annotations(data, inputs)),
        "template_id": template_id,
        "template_catalog_sha256": file_hash(TEMPLATES),
    }


def _instance(project, data, identifier, template_id, name, inputs, *, input_mode="selected", stage_reviews=None):
    normalized = _inputs(data, inputs)
    return {
        "id": identifier,
        "template_id": template_id,
        "name": name,
        "inputs": normalized,
        "input_binding": input_binding(project, data, normalized, template_id),
        "input_mode": input_mode,
        "stage_reviews": deepcopy(stage_reviews or {}),
    }


def migrate(project, data):
    """Apply an additive schema-v1 migration without touching legacy stage reviews."""
    synchronize_legacy_reviews = False
    if "workflow_instances" not in data:
        main_inputs = {
            "asset_ids": [item["id"] for item in data["assets"]],
            "revision_ids": [item["id"] for item in data["revisions"]],
            "annotation_ids": None,
        }
        legacy_reviews = data.get("stage_reviews", {})
        instances = [_instance(project, data, LEGACY_ID, "long_form_youtube", "Main production", main_inputs, input_mode="all_project", stage_reviews=legacy_reviews)]
        active_id = LEGACY_ID
        podcast = data.get("podcast")
        if isinstance(podcast, dict):
            audio_id = podcast.get("primary_audio_asset_id")
            camera_id = podcast.get("camera_asset_id")
            asset_ids = list(dict.fromkeys(item for item in (audio_id, camera_id) if isinstance(item, str)))
            podcast_id = "legacy-solo-podcast"
            instances.append(_instance(project, data, podcast_id, "solo_podcast", "Solo podcast", {"asset_ids": asset_ids, "revision_ids": [], "annotation_ids": None}, input_mode="selected"))
            active_id = podcast_id
        data["workflow_instances"] = instances
        data["active_workflow_id"] = active_id
        synchronize_legacy_reviews = True
    elif "active_workflow_id" not in data:
        instances = data.get("workflow_instances")
        data["active_workflow_id"] = instances[0]["id"] if isinstance(instances, list) and instances else None
        synchronize_legacy_reviews = True
    # Repair the short-lived derived-podcast migration shape. It accidentally
    # inherited the general workflow's evidence and all-project scope. The
    # recognizable derived ID and old input mode make this a bounded one-time
    # compatibility repair without touching user-created podcast workflows.
    instances = data.get("workflow_instances")
    if isinstance(instances, list):
        main = next((item for item in instances if isinstance(item, dict) and item.get("id") == LEGACY_ID), None)
        derived = next((item for item in instances if isinstance(item, dict) and item.get("id") == "legacy-solo-podcast" and item.get("template_id") == "solo_podcast"), None)
        if isinstance(main, dict) and isinstance(derived, dict) and derived.get("input_mode") == "all_project":
            if derived.get("stage_reviews") == main.get("stage_reviews"):
                derived["stage_reviews"] = {}
            derived["input_mode"] = "selected"
            derived["input_binding"] = input_binding(project, data, derived["inputs"], derived["template_id"])
            synchronize_legacy_reviews = True
    validate(project, data)
    if synchronize_legacy_reviews:
        data["stage_reviews"] = deepcopy(active(data)["stage_reviews"])
    return data


def validate(project, data):
    definitions = {item["id"] for item in templates()["templates"]}
    instances = data.get("workflow_instances")
    if not isinstance(instances, list) or not instances:
        raise ValueError("At least one workflow instance is required")
    ids = set()
    for item in instances:
        if not isinstance(item, dict):
            raise ValueError("Workflow instances must be objects")
        identifier = item.get("id")
        if not isinstance(identifier, str) or re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", identifier) is None or identifier in ids:
            raise ValueError("Invalid or duplicate workflow instance ID")
        ids.add(identifier)
        if item.get("template_id") not in definitions:
            raise ValueError("Unknown workflow template")
        _text(item.get("name"), "Workflow name")
        if item.get("input_mode") not in {"selected", "all_project"}:
            raise ValueError("Invalid workflow input mode")
        if not isinstance(item.get("stage_reviews"), dict):
            raise ValueError("Workflow stage reviews must be an object")
        normalized = _inputs(data, item.get("inputs"))
        binding = item.get("input_binding")
        if not isinstance(binding, dict):
            raise ValueError("Workflow instance is missing its input binding")
        # Older schema-v1 bindings did not include template metadata. Accept
        # them so opening a project remains additive; status() reports them as
        # stale until the workflow inputs are explicitly refreshed.
        if not {"assets", "output_revisions", "annotations_sha256"} <= set(binding):
            raise ValueError("Invalid workflow input binding")
        if not isinstance(binding["assets"], list) or not isinstance(binding["output_revisions"], list):
            raise ValueError("Invalid workflow media binding")
        if not isinstance(binding["annotations_sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", binding["annotations_sha256"]) is None:
            raise ValueError("Invalid workflow annotation binding")
        if "template_id" in binding and not isinstance(binding["template_id"], str):
            raise ValueError("Invalid workflow template binding")
        if "template_catalog_sha256" in binding and (not isinstance(binding["template_catalog_sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", binding["template_catalog_sha256"]) is None):
            raise ValueError("Invalid workflow template catalog binding")
        item["inputs"] = normalized
    if data.get("active_workflow_id") not in ids:
        raise ValueError("Active workflow does not exist")


def create(project, data, params):
    template_id = params.get("template_id")
    definition = next((item for item in templates()["templates"] if item["id"] == template_id), None)
    if definition is None:
        raise ValueError("Unknown workflow template")
    name = _text(params.get("name", definition["label"]), "Workflow name")
    identifier = uuid.uuid4().hex
    instance = _instance(project, data, identifier, template_id, name, request_inputs(params))
    data["workflow_instances"].append(instance)
    data["active_workflow_id"] = identifier
    data["stage_reviews"] = {}
    validate(project, data)


def select(project, data, params):
    identifier = params.get("workflow_id")
    if identifier not in {item["id"] for item in data["workflow_instances"]}:
        raise ValueError("Unknown workflow instance")
    data["active_workflow_id"] = identifier
    data["stage_reviews"] = deepcopy(active(data)["stage_reviews"])


def update_inputs(project, data, params):
    identifier = params.get("workflow_id")
    instance = next((item for item in data["workflow_instances"] if item["id"] == identifier), None)
    if instance is None:
        raise ValueError("Unknown workflow instance")
    inputs = _inputs(data, request_inputs(params))
    instance["inputs"] = inputs
    instance["input_mode"] = "selected"
    instance["input_binding"] = input_binding(project, data, inputs, instance["template_id"])
    validate(project, data)


def attach_revision(project, data, workflow_id, revision):
    """Attach a newly registered revision to exactly one workflow instance."""
    instance = by_id(data, workflow_id)
    revision_id = revision.get("id") if isinstance(revision, dict) else None
    if revision_id not in {item["id"] for item in data["revisions"]}:
        raise ValueError("Workflow revision must already be registered")
    if revision_id not in instance["inputs"]["revision_ids"]:
        instance["inputs"]["revision_ids"].append(revision_id)
    instance["input_binding"] = input_binding(
        project, data, effective_inputs(data, instance), instance["template_id"]
    )
    validate(project, data)


def effective_inputs(data, instance):
    if instance.get("input_mode") == "all_project":
        return {
            "asset_ids": [item["id"] for item in data["assets"]],
            "revision_ids": [item["id"] for item in data["revisions"]],
            "annotation_ids": None,
        }
    return instance["inputs"]


def active(data):
    return next(item for item in data["workflow_instances"] if item["id"] == data["active_workflow_id"])


def by_id(data, workflow_id=None):
    identifier = data["active_workflow_id"] if workflow_id is None else workflow_id
    instance = next((item for item in data["workflow_instances"] if item["id"] == identifier), None)
    if instance is None:
        raise ValueError("Unknown workflow instance")
    return instance


def status(project, data):
    migrate(project, data)
    result = []
    for item in data["workflow_instances"]:
        current = input_binding(project, data, effective_inputs(data, item), item["template_id"])
        reasons = []
        stored = item.get("input_binding")
        if not isinstance(stored, dict):
            reasons.append({"code": "invalid_input_binding", "message": "The saved workflow input binding is not readable."})
        else:
            media_keys = ("assets", "output_revisions", "annotations_sha256")
            if any(stored.get(key) != current[key] for key in media_keys):
                reasons.append({"code": "input_binding_changed", "message": "Bound media or relevant annotations changed."})
            if stored.get("template_id") != current["template_id"]:
                reasons.append({"code": "template_binding_changed", "message": "The saved workflow template binding is missing or changed."})
            if stored.get("template_catalog_sha256") != current["template_catalog_sha256"]:
                reasons.append({"code": "template_catalog_changed", "message": "The workflow template catalog changed."})
        result.append({
            **item,
            "status": "stale" if reasons else "current",
            "stale_reason": reasons[0] if reasons else None,
            "stale_reasons": reasons,
            "current_input_binding": current,
        })
    active = next(item for item in result if item["id"] == data["active_workflow_id"])
    return {
        "schema_version": 1,
        "templates": templates()["templates"],
        "active_workflow_id": data["active_workflow_id"],
        "instances": result,
        "workflow_instances": result,
        "active_workflow": active,
    }
