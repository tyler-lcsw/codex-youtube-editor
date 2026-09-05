import pytest


def test_voice_reference_and_short_beats_are_required(tmp_path):
    from tools.providers.tts_qwen import validate_voice_request
    with pytest.raises(ValueError):validate_voice_request('Hello',None,'')
    ref=tmp_path/'voice.wav';ref.write_bytes(b'audio')
    with pytest.raises(ValueError):validate_voice_request('x'*1001,ref,'reference transcript')
    validate_voice_request('Hello <break time="200ms"/> again.',ref,'reference transcript')
