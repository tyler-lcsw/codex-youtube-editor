"""Pure eligibility checks. Policy decisions happen before credential/model loading."""
from .contracts import CloudDisabled

def ensure_allowed(provider_kind: str, local_only: bool) -> None:
    if provider_kind not in {'local','cloud','codex_builtin'}:
        raise CloudDisabled(f'Unregistered provider kind: {provider_kind}')
    if local_only and provider_kind != 'local':
        raise CloudDisabled('Strict local profile rejects hosted generation')

def authorize_hybrid_image(request: dict, approval: dict | None) -> bool:
    if request.get('profile') != 'hybrid' or request.get('provider') != 'codex_builtin':
        return False
    if not approval or approval.get('approved') is not True:
        return False
    for key in ('provider', 'purpose', 'references'):
        if key not in request or request[key] != approval.get(key):
            return False
    used, limit = approval.get('used_generations'), approval.get('max_generations')
    return type(used) is int and type(limit) is int and 0 <= used < limit
