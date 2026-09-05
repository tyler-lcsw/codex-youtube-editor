from pathlib import Path


def test_cache_changes_with_language_terms_or_model_revision(tmp_path):
    from tools.transcribe import local_cache_key
    audio=tmp_path/'clip.wav';audio.write_bytes(b'fixture')
    base=local_cache_key(audio,'English',['Codex'],{'asr':'one'})
    assert local_cache_key(audio,'Spanish',['Codex'],{'asr':'one'}) != base
    assert local_cache_key(audio,'English',['Remotion'],{'asr':'one'}) != base
    assert local_cache_key(audio,'English',['Codex'],{'asr':'two'}) != base
