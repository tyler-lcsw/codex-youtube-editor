"""Recommend an execution route from workflow requirements, not artwork complexity."""
def recommend_image_route(requirements: dict) -> str:
    if requirements.get('profile','local') != 'hybrid' or not requirements.get('native_available'):
        return 'local'
    if any(requirements.get(k) for k in ('unattended','control_maps','pinned_seed_required','integrated_multi_shot')):
        return 'local'
    return 'codex_builtin'
