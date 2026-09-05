import hashlib
import io
import zipfile
import pytest


def archive(entries):
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w') as z:
        for name,content in entries.items():z.writestr(name,content)
    return output.getvalue()


def test_archive_installs_only_verified_pinned_files(tmp_path):
    from tools.setup_models import install_archive
    content=b'checkpoint';data=archive({'DeepFilterNet3/config.ini':content,'extra.txt':b'ignored'})
    spec={'archive_sha256':hashlib.sha256(data).hexdigest(),'files':{'config.ini':hashlib.sha256(content).hexdigest()}}
    target=tmp_path/'DeepFilterNet3';install_archive(data,spec,target)
    assert (target/'config.ini').read_bytes()==content
    assert not (tmp_path/'extra.txt').exists()


def test_bad_archive_preserves_existing_model(tmp_path):
    from tools.setup_models import install_archive
    target=tmp_path/'DeepFilterNet3';target.mkdir();(target/'config.ini').write_bytes(b'good')
    data=archive({'DeepFilterNet3/config.ini':b'bad'})
    spec={'archive_sha256':hashlib.sha256(data).hexdigest(),'files':{'config.ini':hashlib.sha256(b'good').hexdigest()}}
    with pytest.raises(ValueError,match='hash'):install_archive(data,spec,target)
    assert (target/'config.ini').read_bytes()==b'good'


def test_archive_path_traversal_is_rejected(tmp_path):
    from tools.setup_models import install_archive
    data=archive({'../escape':b'bad'})
    with pytest.raises(ValueError,match='path'):
        install_archive(data,{'archive_sha256':hashlib.sha256(data).hexdigest(),'files':{}},tmp_path/'DeepFilterNet3')
    assert not (tmp_path/'escape').exists()
