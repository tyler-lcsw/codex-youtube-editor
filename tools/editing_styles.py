"""Selectable project-local editorial guidance cloned from the master QA rules."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import uuid

from . import production_quality as quality
from .run_state import atomic_json


def path(project):
    return Path(project).resolve() / "work/studio/editing-styles.json"


def _master_style(name="Default", identifier=None):
    master = quality.read_rules()
    return {
        "id": identifier or uuid.uuid4().hex,
        "name": name,
        "source_master_sha256": master["sha256"],
        "source_master_rule_ids": [rule["id"] for rule in master["rules"]],
        "rules": [
            {"id": rule["id"], "enabled": True, "text": rule["rule"]}
            for rule in master["rules"]
        ],
    }


def _default_state():
    master = quality.read_rules()
    identifier = hashlib.sha256(("default:" + master["sha256"]).encode()).hexdigest()[:32]
    style = _master_style(identifier=identifier)
    return {
        "schema_version": 1,
        "revision": 0,
        "selected_style_id": style["id"],
        "styles": [style],
    }


def _text(value, label, maximum):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")
    value = value.strip()
    if len(value) > maximum:
        raise ValueError(f"{label} is too long")
    return value


def validate(data):
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Unsupported editing-style schema")
    revision = data.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise ValueError("Invalid editing-style revision")
    styles = data.get("styles")
    if not isinstance(styles, list) or not styles:
        raise ValueError("At least one editing style is required")
    master = quality.read_rules()
    master_ids = [rule["id"] for rule in master["rules"]]
    ids, names = set(), set()
    for style in styles:
        if not isinstance(style, dict):
            raise ValueError("Editing styles must be objects")
        identifier = style.get("id")
        if not isinstance(identifier, str) or re.fullmatch(r"[0-9a-f]{32}", identifier) is None or identifier in ids:
            raise ValueError("Invalid or duplicate editing-style ID")
        ids.add(identifier)
        name = _text(style.get("name"), "Style name", 80)
        if name.casefold() in names:
            raise ValueError("Editing-style names must be unique")
        names.add(name.casefold())
        source = style.get("source_master_sha256")
        if not isinstance(source, str) or re.fullmatch(r"[0-9a-f]{64}", source) is None:
            raise ValueError("Invalid source master hash")
        rules = style.get("rules")
        if not isinstance(rules, list) or not rules:
            raise ValueError("An editing style must contain rules")
        rule_ids = set()
        for rule in rules:
            if not isinstance(rule, dict) or set(rule) != {"id", "enabled", "text"}:
                raise ValueError("Editing-style rules require id, enabled, and text")
            rule_id = rule["id"]
            if not isinstance(rule_id, str) or re.fullmatch(r"R\d+", rule_id) is None or rule_id in rule_ids:
                raise ValueError("Invalid or duplicate editing-style rule ID")
            rule_ids.add(rule_id)
            if type(rule["enabled"]) is not bool:
                raise ValueError("Editing-style enabled values must be true or false")
            rule["text"] = _text(rule["text"], f"Rule {rule_id}", 20_000)
        if style.get("source_master_rule_ids") != [rule["id"] for rule in rules]:
            raise ValueError("Editing-style rules must match their master snapshot")
        if source == master["sha256"] and style["source_master_rule_ids"] != master_ids:
            raise ValueError("Editing style does not match the identified master rule list")
    if data.get("selected_style_id") not in ids:
        raise ValueError("Selected editing style does not exist")
    return data


def read(project):
    styles_path = path(project)
    raw = styles_path.read_bytes() if styles_path.is_file() else None
    data = json.loads(raw) if raw is not None else _default_state()
    validate(data)
    current_master = quality.read_rules()["sha256"]
    result = deepcopy(data)
    result["path"] = str(styles_path)
    result["materialized"] = styles_path.is_file()
    result["master_sha256"] = current_master
    result["master_changed"] = any(style["source_master_sha256"] != current_master for style in data["styles"])
    canonical = raw if raw is not None else json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    result["sha256"] = hashlib.sha256(canonical).hexdigest()
    return result


def ensure(project):
    if not path(project).exists():
        data = _default_state()
        validate(data)
        atomic_json(path(project), data)
    return read(project)


def _stored(project):
    state = read(project)
    for key in ("path", "materialized", "master_sha256", "master_changed", "sha256"):
        state.pop(key, None)
    return deepcopy(state)


def _check_version(project, data, expected_revision, expected_sha256):
    current = read(project)
    if type(expected_revision) is not int or expected_revision != data["revision"] or expected_sha256 != current["sha256"]:
        raise ValueError("Editing styles changed; reload before saving")


def _save(project, data):
    validate(data)
    atomic_json(path(project), data)
    return read(project)


def create_style(project, name, expected_revision, expected_sha256):
    data = _stored(project)
    _check_version(project, data, expected_revision, expected_sha256)
    style = _master_style(_text(name, "Style name", 80))
    data["styles"].append(style)
    data["selected_style_id"] = style["id"]
    data["revision"] += 1
    return _save(project, data)


def update_style(project, style_id, name, rules, expected_revision, expected_sha256):
    data = _stored(project)
    _check_version(project, data, expected_revision, expected_sha256)
    style = next((item for item in data["styles"] if item["id"] == style_id), None)
    if style is None:
        raise ValueError("Unknown editing style")
    if not isinstance(rules, list):
        raise ValueError("Editing-style rules must be a list")
    expected_ids = [rule["id"] for rule in style["rules"]]
    candidate = deepcopy(style)
    candidate["name"] = _text(name, "Style name", 80)
    candidate["rules"] = deepcopy(rules)
    if [rule.get("id") if isinstance(rule, dict) else None for rule in rules] != expected_ids:
        raise ValueError("A style update must preserve every rule ID and its order")
    replacement = deepcopy(data)
    replacement["styles"] = [candidate if item["id"] == style_id else item for item in data["styles"]]
    validate(replacement)
    if replacement["styles"] != data["styles"]:
        replacement["revision"] += 1
    return _save(project, replacement)


def select_style(project, style_id, expected_revision, expected_sha256):
    data = _stored(project)
    _check_version(project, data, expected_revision, expected_sha256)
    if style_id not in {style["id"] for style in data["styles"]}:
        raise ValueError("Unknown editing style")
    if data["selected_style_id"] != style_id:
        data["selected_style_id"] = style_id
        data["revision"] += 1
    return _save(project, data)


def delete_style(project, style_id, expected_revision, expected_sha256):
    data = _stored(project)
    _check_version(project, data, expected_revision, expected_sha256)
    if len(data["styles"]) == 1:
        raise ValueError("The last editing style cannot be deleted")
    if data["selected_style_id"] == style_id:
        raise ValueError("Select another editing style before deleting this one")
    remaining = [style for style in data["styles"] if style["id"] != style_id]
    if len(remaining) == len(data["styles"]):
        raise ValueError("Unknown editing style")
    data["styles"] = remaining
    data["revision"] += 1
    return _save(project, data)


def active_style(project):
    data = read(project)
    style = next(item for item in data["styles"] if item["id"] == data["selected_style_id"])
    return deepcopy(style)


def active_binding(project):
    styles_path = path(project)
    if not styles_path.is_file():
        return None
    style = active_style(project)
    canonical = json.dumps(style, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return {"id": style["id"], "sha256": hashlib.sha256(canonical).hexdigest()}
