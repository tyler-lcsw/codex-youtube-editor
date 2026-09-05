import pytest

def test_local_rejects_every_hosted_kind():
    from tools.providers.policy import ensure_allowed, CloudDisabled
    for kind in ('cloud','codex_builtin','unknown'):
        with pytest.raises(CloudDisabled): ensure_allowed(kind, True)
    ensure_allowed('local', True)

def test_hybrid_scope_cannot_expand():
    from tools.providers.policy import authorize_hybrid_image
    request = {'provider':'codex_builtin','purpose':'thumbnail','references':['abc'],'profile':'hybrid'}
    approval = {**request,'approved':True,'max_generations':3,'used_generations':1}
    assert authorize_hybrid_image(request, approval)
    assert not authorize_hybrid_image(request, None)
    assert not authorize_hybrid_image({**request,'references':['private-new']}, approval)
    assert not authorize_hybrid_image({**request,'purpose':'avatar'}, approval)
    assert not authorize_hybrid_image({**request,'profile':'local'}, approval)
    assert not authorize_hybrid_image(request,{**approval,'used_generations':3})
