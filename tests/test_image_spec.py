import pytest
from PIL import Image


def test_image_trial_profile_rejects_unqualified_resolution_and_large_refs(tmp_path):
    from tools.providers.image_klein import validate_request
    validate_request('robot',768,512,[])
    with pytest.raises(ValueError):validate_request('robot',2048,2048,[])
    p=tmp_path/'reference.png';Image.new('RGB',(2048,2048)).save(p)
    with pytest.raises(ValueError):validate_request('robot',768,512,[p])
